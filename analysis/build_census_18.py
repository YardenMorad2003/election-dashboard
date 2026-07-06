# -*- coding: utf-8 -*-
"""
build_census_18.py — STATAREA 2009 build step 7: join the 2008 census to the
vote layer and write the final data/statarea_2009.json.

Sources
- mesukam1.xls  (CBS 2008 census PROFILES): rich per-unit demography+SES.
  * band גיליון_3א/3ב  = STAT-AREA level rows (1,708 SAs; incl. big cities).
  * bands 1/2/4/5/6    = LOCALITY level by size (band-1 = >=100k).
  Columns detected by English header (row 4) because band layouts differ.
  Religion (jew/mosl/chris/druze) + age-bands exist only at LOCALITY level
  -> inherited onto each SA of the locality (rel_src / age_src = 'locality').
  Combined SAs use the "3+1" StatAreaCmb convention (like 2022) -> census_src
  'combo'.
- tab02_01.xls  (2008 socio-economic INDEX): SA-level cluster/rank/index +
  income per capita -> attached as a bonus where available.

Output: data/statarea_2009.json  (votes from statarea_2009_votes.json + census)
Run: python -X utf8 analysis/build_census_18.py
"""
import json
import os
import warnings
from collections import defaultdict

import pandas as pd

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAP = os.path.join(HERE, "statarea_inputs")
MES = r"C:\Users\yarde\Downloads\mesukam1.xls"
TAB02 = r"C:\Users\yarde\Downloads\socio_index_zip2\2\tab02_01.xls"
VOTES = os.path.join(SNAP, "statarea_2009_votes.json")
OUT = os.path.join(ROOT, "data", "statarea_2009.json")

# raw mesukam header -> we pull these; derived keys computed afterward
RAW = ["pop_thou", "pop_density", "jew_pcnt", "mosl_pcnt", "chris_pcnt", "druze_pcnt",
       "age_median", "age0_4_pcnt", "age5_9_pcnt", "age10_14_pcnt", "age15_19_pcnt",
       "age65m_pcnt", "israel_pcnt", "europe_pcnt", "asia_pcnt", "africa_pcnt",
       "america_pcnt", "aliya2002_pcnt", "Acadm1Cert_pcnt", "Acadm2Cert_pcnt",
       "MatricCert_pcnt", "Wrk2008Y_pcnt", "ChldBorn_avg", "size_avg",
       "own_pcnt", "rent_pcnt", "Vehicle1up_pcnt", "ComputerY_pcnt"]
REL = ["jew_pcnt", "mosl_pcnt", "chris_pcnt", "druze_pcnt"]
AGEB = ["age0_4_pcnt", "age5_9_pcnt", "age10_14_pcnt", "age15_19_pcnt"]


def numf(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def sa_members(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return []
    s = str(v).strip()
    if not s or s in ("0", "0.0"):
        return []
    out = []
    for part in s.replace("–", "-").split("+"):
        try:
            out.append(int(float(part.strip())))
        except ValueError:
            pass
    return out


def hdrmap(d):
    m = {}
    for c in range(d.shape[1]):
        v = d.iloc[4, c]
        if not pd.isna(v):
            m.setdefault(str(v).strip(), c)
    return m


def collect_mesukam():
    xl = pd.ExcelFile(MES)
    sa = {}      # stat08 -> {raw dims}; also tracks combo
    combo = set()
    loc = {}     # semel  -> {raw dims}
    for band in range(1, 7):
        for suf in ("א", "ב"):
            sheet = f"גיליון_{band}{suf}"
            if sheet not in xl.sheet_names:
                continue
            d = pd.read_excel(MES, sheet_name=sheet, header=None)
            hm = hdrmap(d)
            lc = hm.get("LocalityCode")
            if lc is None:
                continue
            sacol = hm.get("StatAreaCmb") or hm.get("StatArea")
            qc = hm.get("Quarter"); sq = hm.get("SubQuarter")
            present = {k: hm[k] for k in RAW if k in hm}
            for i in range(5, d.shape[0]):
                code = d.iloc[i, lc]
                if pd.isna(code) or not isinstance(code, (int, float)) or code <= 0:
                    continue
                code = int(code)
                mem = sa_members(d.iloc[i, sacol]) if sacol is not None else []
                if mem:
                    tgt_keys = [code * 10000 + m for m in mem]
                    if len(mem) > 1:
                        combo.update(tgt_keys)
                    store = sa
                else:
                    q = d.iloc[i, qc] if qc is not None else None
                    s = d.iloc[i, sq] if sq is not None else None
                    if (qc is not None and not pd.isna(q)) or (sq is not None and not pd.isna(s)):
                        continue   # quarter / sub-quarter intermediate row
                    tgt_keys = [code]
                    store = loc
                vals = {k: numf(d.iloc[i, c]) for k, c in present.items()}
                vals = {k: v for k, v in vals.items() if v is not None}
                for tk in tgt_keys:
                    store.setdefault(tk, {}).update(vals)
    return sa, combo, loc


def collect_tab02():
    d = pd.read_excel(TAB02, sheet_name=0, header=None)
    ses = {}
    for i in range(9, d.shape[0]):
        s, sac = d.iloc[i, 1], d.iloc[i, 3]
        if not isinstance(s, (int, float)) or pd.isna(s) or s <= 0:
            continue
        if not isinstance(sac, (int, float)) or pd.isna(sac):
            continue
        sid = int(s) * 10000 + int(sac)
        ses[sid] = {"ses_index": numf(d.iloc[i, 6]), "ses_rank": numf(d.iloc[i, 7]),
                    "ses_cluster": numf(d.iloc[i, 8]), "income": numf(d.iloc[i, 42])}
    return ses


def shape_census(raw, rel_from=None, age_from=None):
    """raw dims dict -> output census dict; religion/age0_19 optionally inherited."""
    c = {}
    def r(v, nd=1):
        return None if v is None else round(v, nd)
    if "pop_thou" in raw:
        c["pop"] = int(round(raw["pop_thou"] * 1000))
    c["density"] = r(raw.get("pop_density"))
    c["age_med"] = r(raw.get("age_median"))
    for src, dst in [("israel_pcnt", "orig_il"), ("europe_pcnt", "orig_eur"),
                     ("asia_pcnt", "orig_asia"), ("africa_pcnt", "orig_afr"),
                     ("america_pcnt", "orig_am")]:
        if src in raw:
            c[dst] = r(raw[src])
    if "aliya2002_pcnt" in raw:
        c["aliya02"] = r(raw["aliya2002_pcnt"])
    ac = (raw.get("Acadm1Cert_pcnt") or 0) + (raw.get("Acadm2Cert_pcnt") or 0)
    if "Acadm1Cert_pcnt" in raw or "Acadm2Cert_pcnt" in raw:
        c["acad"] = round(ac, 1)
    for src, dst in [("MatricCert_pcnt", "matric"), ("Wrk2008Y_pcnt", "work"),
                     ("ChldBorn_avg", "chld"), ("size_avg", "hh_size"),
                     ("own_pcnt", "own"), ("rent_pcnt", "rent"), ("ComputerY_pcnt", "pc"),
                     ("age65m_pcnt", "age65")]:
        if src in raw:
            c[dst] = r(raw[src], 2 if dst in ("chld", "hh_size") else 1)
    if "Vehicle1up_pcnt" in raw:
        c["no_car"] = round(100 - raw["Vehicle1up_pcnt"], 1)
    # religion is attached separately in main() from localities.json (2019, uniform
    # vintage — mesukam carries it only for >=100k cities, same locality granularity).
    # age0_19 from locality age-bands if available
    ab = age_from if age_from and all(k in age_from for k in AGEB) else (raw if all(k in raw for k in AGEB) else None)
    if ab:
        c["age0_19"] = round(sum(ab[k] for k in AGEB), 1)
    return c


def load_religion():
    """semel -> {jew,mosl,druze,arab, rel_dom} from localities.json (2019)."""
    loc = json.load(open(os.path.join(ROOT, "data", "localities.json"), encoding="utf-8"))
    out = {}
    for r in loc:
        rel = r.get("religion")
        s = r.get("semel")
        if not isinstance(rel, dict) or not s:
            continue
        jew = rel.get("pct_jews"); mosl = rel.get("pct_muslims")
        druze = rel.get("pct_druze"); arab = rel.get("pct_arabs")
        if jew is None and arab is None:
            continue
        jew = jew or 0; mosl = mosl or 0; druze = druze or 0; arab = arab or 0
        if jew >= 60:
            dom = "יהודי"
        elif druze >= 50:
            dom = "דרוזי"
        elif mosl >= 50:
            dom = "מוסלמי"
        elif arab >= 60:
            dom = "ערבי"
        else:
            dom = "מעורב"
        out[int(s)] = {"jew": round(jew, 1), "mosl": round(mosl, 1),
                       "druze": round(druze, 1), "arab": round(arab, 1), "rel_dom": dom}
    return out


def main():
    print("reading mesukam1 (11 profile sheets)...")
    mes_sa, combo, mes_loc = collect_mesukam()
    print(f"  mesukam SA rows: {len(mes_sa)} ({len(combo)} combo members); locality rows: {len(mes_loc)}")
    ses = collect_tab02()
    print(f"  tab02 SES rows: {len(ses)}")
    rel_loc = load_religion()
    print(f"  religion (localities.json 2019): {len(rel_loc)} localities")

    data = json.load(open(VOTES, encoding="utf-8"))
    areas = {int(k): v for k, v in data["areas"].items()}

    src_ct = defaultdict(int)
    for sid, rec in areas.items():
        semel = rec["semel"]
        if sid in mes_sa:
            cen = shape_census(mes_sa[sid], rel_from=mes_loc.get(semel), age_from=mes_loc.get(semel))
            rec["census_src"] = "combo" if sid in combo else "sa"
        elif semel in mes_loc:
            cen = shape_census(mes_loc[semel])
            rec["census_src"] = "locality"
        else:
            cen = None
            rec["census_src"] = None
        if cen is not None:
            if sid in ses:
                cen.update({k: v for k, v in ses[sid].items() if v is not None})
            r = rel_loc.get(semel)
            if r:
                cen["religion"] = {k: r[k] for k in ("jew", "mosl", "druze", "arab")}
                cen["rel_dom"] = r["rel_dom"]; cen["rel_src"] = "loc2019"
            rec["census"] = cen
        src_ct[rec["census_src"]] += 1

    # census-only SAs (mesukam SA rows without votes) so demographic modes color them
    n_conly = 0
    for sid, raw in mes_sa.items():
        if sid in areas:
            continue
        semel, sa = divmod(sid, 10000)
        cen = shape_census(raw, rel_from=mes_loc.get(semel), age_from=mes_loc.get(semel))
        if sid in ses:
            cen.update({k: v for k, v in ses[sid].items() if v is not None})
        r = rel_loc.get(semel)
        if r:
            cen["religion"] = {k: r[k] for k in ("jew", "mosl", "druze", "arab")}
            cen["rel_dom"] = r["rel_dom"]; cen["rel_src"] = "loc2019"
        areas[sid] = {"semel": semel, "sa": sa, "census": cen,
                      "census_src": "combo" if sid in combo else "sa"}
        n_conly += 1

    n_cen = sum(1 for v in areas.values() if "census" in v)
    print(f"\nvote-area census src: {dict(src_ct)}")
    print(f"census-only SAs added: {n_conly}")
    print(f"total areas: {len(areas)}; with census: {n_cen}; with votes: {sum(1 for v in areas.values() if 'valid' in v)}")

    out = {"meta": {"election": "18", "census": "2008", "blocs": data["meta"]["blocs"],
                    "source": "K18 ballots × 2008 SA shapefile (PIP) × mesukam1 census + tab02 socio-index",
                    "built": "2026-07-05"},
           "areas": {str(k): v for k, v in areas.items()}}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {OUT} ({os.path.getsize(OUT):,} bytes)")

    # spot-check census sanity
    print("\ncensus spot checks:")
    def show(sid):
        r = areas.get(sid)
        if not r or "census" not in r:
            print(f"  {sid}: no census"); return
        c = r["census"]
        print(f"  {sid} (src={r['census_src']}): age_med={c.get('age_med')} acad={c.get('acad')} "
              f"hh_size={c.get('hh_size')} rel_dom={c.get('rel_dom')} ses_cluster={c.get('ses_cluster')} "
              f"orig_eur={c.get('orig_eur')} orig_asia={c.get('orig_asia')}")
    for sem in (6100, 3000, 5000, 2710):
        sids = sorted(k for k in areas if k // 10000 == sem and "census" in areas[k])[:1]
        for s in sids:
            show(s)


if __name__ == "__main__":
    main()
