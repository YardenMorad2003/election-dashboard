# -*- coding: utf-8 -*-
"""
build_census_1995.py — extract the 1995 census stat-area demographics from the
CBS tables (user-provided 2026-07-06, Downloads) and join them into the
K16/K17 layers. THE missing census for the 1995 geometry — incl. the gold:
post-1990 aliyah per stat-area.

Inputs (Downloads):
  t1p168.xls  לוח 1  (full pop): religion counts, households, avg hh size
  t1 (2).xls  לוח ג1 (Jews+others): born-Israel/abroad, immigration waves
              (עד 1964 / 1965-89 / 1990+ as % of foreign-born), origin continents
  t2 (2).xls  לוח ג2 (Jews+others): country of birth (incl. former USSR)
  t2p352.xls  לוח א2 (full pop): age bands, median age, hh composition
Row structure: locality (c0) -> רובע (c1) -> תת-רובע (c2) -> א"ס NNN (c3),
with sex/religion sub-rows carrying a label in c4 (skipped). Locality main
rows serve single-SA towns (geo convention: their only SA is sa=1).
Name->semel: the 'אזורים סטטיסטיים' key sheet ("name    semel") + the 1995
slim geo names. 1995 key = semel*1000 + SA.

Writes: data/census_1995_statarea.json  (+ joins census{} into
        data/statarea_k16.json / statarea_k17.json)
Run: python -X utf8 analysis/build_census_1995.py
"""
import json, os, re, sys, collections
import xlrd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DL = r"C:\Users\yarde\Downloads"
sys.path.insert(0, HERE)
from build_venue_dots import norm  # noqa: E402

SA_RE = re.compile(r'א[\'"׳״]?\s*ס\s+(\d+)')


def fv(x):
    if isinstance(x, float):
        return x
    s = str(x).strip()
    if not s or s in "-..":
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def name2sem_map():
    m = {}
    # geo names (all 1,112 localities, CBS-1995 vintage)
    geo = json.load(open(os.path.join(ROOT, "data", "statarea_1995_geo.json"), encoding="utf-8"))
    single = collections.Counter(f["properties"]["semel"] for f in geo["features"])
    for f in geo["features"]:
        p = f["properties"]
        m.setdefault(norm(p["name"]), p["semel"])
    # key sheet: multi-SA localities carry "name    semel" (authoritative)
    wb = xlrd.open_workbook(os.path.join(DL, "t1 (2).xls"))
    sh = wb.sheet_by_name("אזורים סטטיסטיים")
    for i in range(sh.nrows):
        v = str(sh.cell_value(i, 0)).strip()
        mm = re.match(r"^(.*?)\s+(\d{3,4})$", v)
        if mm:
            m[norm(mm.group(1))] = int(mm.group(2))
    single_sa = {sem: 1 for sem, n in single.items() if n == 1}
    return m, single_sa


def iter_rows(path, sheet_idx=0):
    """yield (kind, semname, sa, rowvals): kind in {'loc','sa'} for MAIN rows only."""
    wb = xlrd.open_workbook(os.path.join(DL, path))
    sh = wb.sheet_by_index(sheet_idx)
    cur_name = None
    for i in range(sh.nrows):
        vals = sh.row_values(i)
        c0 = str(vals[0]).strip()
        c3 = str(vals[3]).strip()
        c4 = str(vals[4]).strip()
        if c4:                       # sex/religion sub-row
            continue
        if c0 and not any(w in c0 for w in ("לוח", "מפתח", "סך כולל", "הערה")):
            cur_name = c0
            yield "loc", cur_name, None, vals
            continue
        mm = SA_RE.search(c3)
        if mm and cur_name:
            yield "sa", cur_name, int(mm.group(1)), vals


def collect(path, cols, out, n2s, single_sa, denom_pop=None):
    """cols: {field: col or callable(vals)->value}; writes into out[key][field]."""
    unresolved = collections.Counter()
    for kind, name, sa, vals in iter_rows(path):
        sem = n2s.get(norm(name))
        if not sem:
            if kind == "loc":
                unresolved[name] += 1
            continue
        if kind == "loc":
            sa = single_sa.get(sem)
            if sa is None:
                continue            # multi-SA locality: wait for its א"ס rows
        key = sem * 1000 + sa
        rec = out.setdefault(key, {})
        for field, col in cols.items():
            rec[field] = col(vals) if callable(col) else fv(vals[col])
    return unresolved


def main():
    n2s, single_sa = name2sem_map()
    print(f"name->semel entries: {len(n2s)}; single-SA localities: {len(single_sa)}")
    out = {}

    # לוח 1 — full population: religion, households
    un1 = collect("t1p168.xls", {
        "pop": 7, "jew_n": 8, "mosl_n": 9, "chris_n": 10, "druze_n": 11,
        "hh": 12, "hh_size": lambda v: round(fv(v[22]), 2),
    }, out, n2s, single_sa)

    # לוח ג1 — Jews+others: born abroad, immigration waves, origin continents
    collect("t1 (2).xls", {
        "jo_pop": 5, "born_il": 6, "abroad": 8, "pct90": 11,
        "orig_asia_n": 12, "orig_afr_n": 18, "orig_euram_n": 24,
    }, out, n2s, single_sa)

    # לוח ג2 — Jews+others: origin by SELECTED COUNTRY (col layout per TAB_C2 header,
    # continent totals at 7/13/20 skipped — ג1 already supplies them)
    collect("t2 (2).xls", {
        "ussr_n": 25, "g2_tot": 5, "g2_il": 6,
        "oc_tr": 8, "oc_iq": 9, "oc_ye": 10, "oc_ir": 11, "oc_as": 12,
        "oc_ma": 14, "oc_dz": 15, "oc_ly": 16, "oc_eg": 17, "oc_et": 18, "oc_af": 19,
        "oc_pl": 21, "oc_ro": 22, "oc_bg": 23, "oc_de": 24, "oc_su": 25, "oc_eu": 26,
        "oc_na": 27, "oc_la": 28,
    }, out, n2s, single_sa)

    # לוח א2 — full population: age structure + hh composition
    collect("t2p352.xls", {
        "age0_14": 9, "a6574": 14, "a75": 15, "age_med": 17,
        "hh_child": 23, "hh_65": 26, "hh_olim": 29,
    }, out, n2s, single_sa)

    # derive shares
    final = {}
    for key, r in out.items():
        pop = r.get("pop", 0)
        if pop <= 0:
            continue
        jo = r.get("jo_pop", 0)
        olim90 = r.get("abroad", 0) * r.get("pct90", 0) / 100.0
        rel = {"יהודי": r.get("jew_n", 0), "מוסלמי": r.get("mosl_n", 0),
               "נוצרי": r.get("chris_n", 0), "דרוזי": r.get("druze_n", 0)}
        dom, domn = max(rel.items(), key=lambda kv: kv[1])
        c = {"pop": int(pop),
             "rel_dom": dom if domn > 0.5 * pop else "מעורב",
             "religion": {"jew": round(100 * r.get("jew_n", 0) / pop, 1),
                          "mosl": round(100 * r.get("mosl_n", 0) / pop, 1),
                          "chris": round(100 * r.get("chris_n", 0) / pop, 1),
                          "druze": round(100 * r.get("druze_n", 0) / pop, 1)},
             "aliya90": round(100 * olim90 / pop, 1),
             "hh_size": r.get("hh_size"),
             "age0_19": None,   # 1995 bands differ; keep page-compatible key absent
             "age0_14": r.get("age0_14") or None,
             "age65": round((r.get("a6574", 0) or 0) + (r.get("a75", 0) or 0), 1) or None,
             "age_med": r.get("age_med") or None,
             "hh_child": r.get("hh_child") or None,
             "hh_olim": r.get("hh_olim") or None}
        if jo > 0:
            c["born_il"] = round(100 * r.get("born_il", 0) / jo, 1)
            c["ussr"] = round(100 * r.get("ussr_n", 0) / jo, 1)
            c["orig_asia"] = round(100 * r.get("orig_asia_n", 0) / jo, 1)
            c["orig_afr"] = round(100 * r.get("orig_afr_n", 0) / jo, 1)
            c["orig_euram"] = round(100 * r.get("orig_euram_n", 0) / jo, 1)
        # origin by selected country (ג2): shares of that table's own Jews+others total
        g2t = r.get("g2_tot", 0)
        if g2t > 0:
            c["orig_il"] = round(100 * r.get("g2_il", 0) / g2t, 1)
            oc = {}
            for k in ("tr", "iq", "ye", "ir", "as", "ma", "dz", "ly", "eg", "et",
                      "af", "pl", "ro", "bg", "de", "su", "eu", "na", "la"):
                v = round(100 * r.get("oc_" + k, 0) / g2t, 1)
                if v >= 0.1:
                    oc[k] = v
            if oc:
                c["oc"] = oc
        final[str(key)] = c

    path = os.path.join(ROOT, "data", "census_1995_statarea.json")
    json.dump(final, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"census SAs extracted: {len(final):,} -> {os.path.basename(path)}")
    if un1:
        print(f"unresolved locality names ({len(un1)}):",
              [n for n, _ in un1.most_common(12)])

    # join into the two 1995-era layers
    for lname in ("statarea_k16.json", "statarea_k17.json"):
        lp = os.path.join(ROOT, "data", lname)
        layer = json.load(open(lp, encoding="utf-8"))
        hit = added = 0
        for sid, rec in layer["areas"].items():
            c = final.get(sid)
            if c:
                rec["census"] = c
                rec["census_src"] = "sa1995"
                hit += 1
        # census-only SAs (no polling venue inside — voters vote in a neighboring SA):
        # voteless records let the demographic modes paint their polygons
        for sid, c in final.items():
            if sid not in layer["areas"]:
                layer["areas"][sid] = {"semel": int(sid) // 1000, "sa": int(sid) % 1000,
                                       "census": c, "census_src": "sa1995"}
                added += 1
        layer["meta"]["census"] = "1995"
        json.dump(layer, open(lp, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        tot = len(layer["areas"])
        pop_cov = sum(1 for r in layer["areas"].values() if r.get("census"))
        print(f"{lname}: {hit}/{tot} voted SAs joined, +{added} census-only SAs added, "
              f"with-census now {pop_cov}")

    # spot checks
    for label, key in [("J-m 111", "3000111"), ("TA 112", "5000112"),
                       ("Bnei Brak first", None), ("Umm al-Fahm 1", "2710001")]:
        if key is None:
            key = next((k for k in final if k.startswith("6100")), None)
        c = final.get(key) or {}
        print(f"  {label} [{key}]: pop={c.get('pop')} rel_dom={c.get('rel_dom')} "
              f"aliya90={c.get('aliya90')} ussr={c.get('ussr')} age_med={c.get('age_med')}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
