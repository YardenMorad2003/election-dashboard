# -*- coding: utf-8 -*-
"""
build_statarea_1995era.py — vote-only stat-area layers for K16 (2003) and
K17 (2006) on the CBS 1995 SA geometry.

Unlike the 2008/2022-era builds, this does NOT use Cain's back-propagated
venue data (it collapses before 2009 — SESSION_CHALLENGES.md §8). Instead:

  K17: the CSV's own contemporaneous כתובת (address) column, geocoded once by
       geocode_k17_addresses.py (Nominatim, PIP-validated against the
       locality's 1995 polygons). 99.8% of votes carry an address.
  K16: coordinates carried back from K17 by (semel, ballot-number) join —
       96.6% of votes match exactly one step back (2003←2006), vs 6% against
       the modern venue master. K16 predates the Nov-2003 municipal mergers,
       so its semels natively match the 1995 geometry's CITY codes.

Both: single-SA localities assigned directly (no coordinate needed);
neighbor imputation (nearest ballot number ΔN≤2, same locality) for the rest;
PIP constrained to the locality's own polygon set (0 spillover by design).
The 1995 layer is boundaries-only — no census — so areas carry votes/blocs
only (census: null). Key: stat95 = CITY_STA = semel*1000 + N_STAT.

Outputs: data/statarea_k16.json, data/statarea_k17.json,
data/statarea_1995_geo.json (slimmed), and per-ballot / per-SA snapshots in
analysis/statarea_inputs/ for validation and the mis-geocode cross-check.

Run: python -X utf8 analysis/build_statarea_1995era.py
"""
import csv
import json
import os
import re
import sys
from collections import defaultdict

from shapely.geometry import Point, shape, mapping
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAP = os.path.join(HERE, "statarea_inputs")
EM = r"C:\Users\yarde\elections-merge\data"
GEO95 = r"C:\Users\yarde\Downloads\statistical_areas_1995.geojson"
CACHE = os.path.join(SNAP, "k17_address_geocodes.json")
GERESH = "'׳״‘’“”\"`"
DOUBLE = "מעטפות כפולות"

# K17 merged-municipality names (Nov-2003) -> constituent 1995 semels.
# Must match geocode_k17_addresses.py.
MERGED = {
    "מודיעין מכבים רעו": [1200, 1273],
    "יהוד נוה אפרים": [9400, 1062],
    "שגור": [516, 490, 483],
    "באקה גת": [6000, 628],
    "עיר כרמל": [494, 534],
    "צורן קדימה": [195, 1308],
    "בנימינה גבעת עדה": [9800, 50],
    # 1996 mergers — merged in BOTH K16 and K17 (K16 predates only the 2003 mergers)
    "בסמה": [639, 643, 657],
    "מעלה עירון": [640, 645, 644, 934],
}


def norm(s):
    if not s:
        return ""
    for ch in GERESH:
        s = s.replace(ch, "")
    s = re.sub(r"[()\-,./\\:;+]", " ", s)
    return " ".join(s.replace("יי", "י").replace("וו", "ו").split())


def iv(x):
    try:
        return int(float(x))
    except (ValueError, TypeError):
        return 0


def main():
    # ---------- 1995 geometry ----------
    print("loading 1995 geometry...", flush=True)
    g = json.load(open(GEO95, encoding="utf-8"))
    geoms, ids, sems = [], [], []
    per_semel = defaultdict(list)
    sa_count = defaultdict(int)
    info = {}
    for f in g["features"]:
        p = f["properties"]
        try:
            semel = int(p["CITY"]); sid = int(p["CITY_STA"]); sac = int(p["N_STAT"])
        except (ValueError, TypeError, KeyError):
            continue
        geom = shape(f["geometry"])
        if not geom.is_valid:
            geom = geom.buffer(0)
        idx = len(geoms)
        geoms.append(geom); ids.append(sid); sems.append(semel)
        per_semel[semel].append(idx)
        sa_count[semel] += 1
        info[sid] = (semel, sac)
    print(f"  polygons: {len(geoms)}, localities: {len(per_semel)}")

    def pip(semel_set, lat, lng, pref=None):
        """Assign stat95 within the locality's own polygons (0 spillover).
        pref = geocode-validated semel, tried first."""
        order = ([pref] if pref in semel_set else []) + [s for s in semel_set if s != pref]
        idxs = [j for s in order for j in per_semel.get(s, [])]
        if not idxs:
            return None
        if lat is not None and lng is not None:
            pt = Point(float(lng), float(lat))
            for j in idxs:
                if geoms[j].covers(pt):
                    return ids[j]
            best, bd = None, 1e18
            for j in idxs:
                d = geoms[j].distance(pt)
                if d < bd:
                    best, bd = j, d
            return ids[best]
        return ids[idxs[0]] if len(idxs) == 1 else None

    # ---------- bridges & geocode cache ----------
    name2sem = {}
    for r in csv.DictReader(open(rf"{EM}\knesset25_ballots.csv", encoding="utf-8-sig")):
        name2sem.setdefault(norm(r["שם ישוב"]), r["סמל ישוב"].strip())
    k16rows = list(csv.DictReader(open(rf"{EM}\knesset16_ballots.csv", encoding="utf-8-sig")))
    for r in k16rows:
        sm = str(iv(r["סמל ישוב"]))
        if sm != "0":
            name2sem[norm(r["שם ישוב"])] = sm
    sfix = os.path.join(SNAP, "settlement_name_fixes_18.json")
    if os.path.exists(sfix):
        for nm, sm in json.load(open(sfix, encoding="utf-8")).items():
            name2sem[norm(nm)] = str(sm)
    cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
    print(f"  geocode cache: {len(cache)} entries, "
          f"{sum(1 for v in cache.values() if v.get('src') != 'none')} resolved")

    pn_all = json.load(open(os.path.join(ROOT, "data", "parties_national.json"), encoding="utf-8"))

    def impute(ballots):
        """Fill missing coords from nearest ballot number (ΔN≤2) in the group."""
        donors = [x for x in ballots if x["lat"] is not None and x["num"] is not None]
        for x in ballots:
            if x["lat"] is not None or x["num"] is None or x["single"]:
                continue
            best, bd = None, 99
            for d in donors:
                dd = abs(x["num"] - d["num"])
                if 0 < dd < bd:
                    best, bd = d, dd
            if best and bd <= 2:
                x["lat"], x["lng"], x["pref"] = best["lat"], best["lng"], best["pref"]
                x["src"] = "impute"

    def aggregate_and_write(e, ballots, party_cols, has_eligible):
        bloc_of = {p["code"]: p["bloc"] for p in pn_all[e]["party_list"]}
        agg = defaultdict(lambda: {"el": 0, "vo": 0, "va": 0, "nb": 0, "p": defaultdict(int)})
        placed = total = 0
        snap = []
        for x in ballots:
            r = x["r"]
            valid = iv(r["כשרים"])
            total += valid
            sid = pip(x["set"], x["lat"], x["lng"], x.get("pref"))
            snap.append((x["set"][0], x["b"], x["lat"], x["lng"], x["src"], sid or "", valid))
            if sid is None:
                continue
            placed += valid
            a = agg[sid]
            if has_eligible:
                a["el"] += iv(r["בוחרים"])
            a["vo"] += iv(r["מצביעים"]); a["va"] += valid; a["nb"] += 1
            for c in party_cols:
                v = iv(r[c])
                if v:
                    a["p"][c] += v
        areas = {}
        counts = []
        for sid, a in agg.items():
            valid = a["va"]
            if valid <= 0:
                continue
            semel, sa = info[sid]
            bv = defaultdict(int); other = 0
            for c, v in a["p"].items():
                b = bloc_of.get(c)
                if b:
                    bv[b] += v
                else:
                    other += v
                counts.append((sid, c, v))
            blocs = {k: round(100 * bv[k] / valid, 2) for k in set(bloc_of.values())}
            blocs["rh"] = round(100 * (bv["right"] + bv["haredi"]) / valid, 2)
            blocs["cla"] = round(100 * sum(v for k, v in bv.items() if k not in ("right", "haredi")) / valid, 2)
            blocs["other"] = round(100 * other / valid, 2)
            areas[sid] = {"semel": semel, "sa": sa,
                          "eligible": a["el"] if has_eligible else None,
                          "voted": a["vo"], "valid": valid, "n_ballots": a["nb"],
                          "turnout": round(100 * a["vo"] / a["el"], 1) if has_eligible and a["el"] else None,
                          "winner": max(a["p"], key=a["p"].get) if a["p"] else None,
                          "blocs": blocs,
                          "parties": {c: round(100 * v / valid, 2) for c, v in a["p"].items() if v / valid >= 0.005}}
        obj = {"meta": {"election": e, "census": None, "geometry": "cbs_1995",
                        "blocs": sorted(set(bloc_of.values())),
                        "source": ("K17 CSV contemporaneous addresses × Nominatim (PIP-validated) × CBS 1995 SAs"
                                   if e == "17" else
                                   "K16 ballots × K17 address coords (ballot-number join) × CBS 1995 SAs")},
               "areas": {str(k): v for k, v in areas.items()}}
        json.dump(obj, open(os.path.join(ROOT, "data", f"statarea_k{e}.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))
        with open(os.path.join(SNAP, f"ballot_stat95_{e}.csv"), "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["semel", "ballot", "lat", "lng", "coord_src", "stat95", "valid"])
            w.writerows(snap)
        with open(os.path.join(SNAP, f"statarea_counts_{e}.csv"), "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["stat95", "code", "votes"])
            w.writerows(counts)
        srcs = defaultdict(int)
        for x in ballots:
            srcs[x["src"]] += iv(x["r"]["כשרים"])
        print(f"K{e}: placed {placed:,}/{total:,} = {100*placed/total:.1f}% | SAs {len(areas)} | "
              f"src votes: {dict(sorted(srcs.items(), key=lambda t: -t[1]))}")
        return areas

    # ---------- K17: addresses ----------
    print("\nbuilding K17 (2006) from contemporaneous addresses...", flush=True)
    k17rows = [r for r in csv.DictReader(open(rf"{EM}\knesset17_ballots.csv", encoding="utf-8-sig"))
               if r["שם ישוב"].strip() != DOUBLE]
    hdr17 = list(k17rows[0].keys())
    party17 = hdr17[hdr17.index("כשרים") + 1:]
    groups17 = defaultdict(list)   # group key -> ballots (for imputation + K16 join)
    unbridged = defaultdict(int)
    for r in k17rows:
        nm = norm(r["שם ישוב"])
        if nm in MERGED:
            sset = MERGED[nm]
        else:
            sm = name2sem.get(nm)
            if not sm:
                unbridged[r["שם ישוב"].strip()] += iv(r["כשרים"])
                continue
            sset = [int(sm)]
        addr = " ".join((r["כתובת"] or "").split())
        total_sa = sum(sa_count.get(s, 0) for s in sset)
        single = total_sa <= 1
        lat = lng = pref = None
        src = "none"
        if single:
            src = "single"
        elif addr:
            c = cache.get(f"{sset[0]}|{addr}")
            if c and c.get("src") != "none":
                lat, lng, pref = c["lat"], c["lng"], c.get("semel")
                src = "addr_" + c["src"]
        b = r["מספר קלפי"].strip()
        # ballot numbers are x10-encoded (ballot 1 = "10", sub-ballot in units
        # digit) -> /10 puts neighbor imputation's dN<=2 on the true scale
        groups17[nm].append({"r": r, "b": b, "set": sset, "single": single,
                             "lat": lat, "lng": lng, "pref": pref, "src": src,
                             "num": float(b) / 10 if re.match(r"^\d+(\.\d+)?$", b) else None})
    if unbridged:
        print(f"  unbridged (dropped): {dict(unbridged)}")
    for nm, bs in groups17.items():
        impute(bs)
    all17 = [x for bs in groups17.values() for x in bs]
    aggregate_and_write("17", all17, party17, has_eligible=False)

    # ---------- K16: ballot-number join back to K17 coords ----------
    print("\nbuilding K16 (2003) via K17 ballot-number join...", flush=True)
    # constituent semel -> K17 group key
    sem2group = {}
    for nm, sset in MERGED.items():
        for s in sset:
            sem2group[s] = nm
    for nm, bs in groups17.items():
        if nm not in MERGED and bs:
            sem2group.setdefault(bs[0]["set"][0], nm)
    k17coord = defaultdict(dict)   # group -> raw ballot int -> (lat, lng, pref)
    for nm, bs in groups17.items():
        for x in bs:
            if x["lat"] is not None:
                k17coord[nm][iv(x["b"])] = (x["lat"], x["lng"], x["pref"])
    hdr16 = list(k16rows[0].keys())
    party16 = hdr16[hdr16.index("שם ישוב") + 1:]
    # pre-2003 mergers (e.g. 1996: Basma, Ma'ale Iron) are merged in K16 too —
    # route their merged semel to the constituent 1995 semels
    merged_sem16 = {}
    for nm in MERGED:
        sm = name2sem.get(nm)
        if sm and sa_count.get(int(sm), 0) == 0:
            merged_sem16[int(sm)] = nm
    groups16 = defaultdict(list)
    nogeom = defaultdict(int)
    for r in k16rows:
        sm = iv(r["סמל ישוב"])
        if sm <= 0:
            continue
        if sm in merged_sem16:
            grp = merged_sem16[sm]
            sset = MERGED[grp]
        else:
            if sa_count.get(sm, 0) == 0:
                nogeom[sm] += iv(r["כשרים"])
                continue
            grp = sem2group.get(sm)
            sset = [sm]
        b = str(iv(r["סמל קלפי"]))
        single = sum(sa_count.get(s, 0) for s in sset) <= 1
        lat = lng = pref = None
        src = "single" if single else "none"
        if not single:
            hit = k17coord.get(grp, {}).get(iv(b))
            if hit:
                lat, lng, pref = hit
                src = "k17_join"
        groups16[sm].append({"r": r, "b": b, "set": sset, "single": single,
                             "lat": lat, "lng": lng, "pref": pref, "src": src,
                             "num": float(b) / 10})
    if nogeom:
        v = sum(nogeom.values())
        print(f"  semels absent from 1995 geometry: {len(nogeom)} localities, {v:,} votes dropped")
    for sm, bs in groups16.items():
        impute(bs)
    all16 = [x for bs in groups16.values() for x in bs]
    aggregate_and_write("16", all16, party16, has_eligible=True)

    # ---------- slim geometry for the page ----------
    keep = set()
    for e in ("16", "17"):
        keep |= set(int(k) for k in json.load(
            open(os.path.join(ROOT, "data", f"statarea_k{e}.json"), encoding="utf-8"))["areas"])
    # SAs with census data but no polling venue inside (voters walk to a neighboring SA):
    # keep their polygons too, so the demographic modes can paint them (2026-07-07 —
    # before the census join existed, venue-less SAs were dropped, leaving urban holes)
    cpath = os.path.join(ROOT, "data", "census_1995_statarea.json")
    if os.path.exists(cpath):
        keep |= set(int(k) for k in json.load(open(cpath, encoding="utf-8")))
    feats = []
    for f in g["features"]:
        p = f["properties"]
        try:
            sid = int(p["CITY_STA"])
        except (ValueError, TypeError, KeyError):
            continue
        if sid not in keep:
            continue
        geom = shape(f["geometry"]).simplify(0.0003, preserve_topology=True)
        gj = mapping(geom)

        def rnd(c):
            return [round(c[0], 5), round(c[1], 5)] if isinstance(c[0], (int, float)) else [rnd(x) for x in c]
        feats.append({"type": "Feature",
                      "properties": {"id": sid, "semel": int(p["CITY"]), "sa": int(p["N_STAT"]),
                                     "name": p.get("SHEM_IVRIT"), "name_en": p.get("NAME")},
                      "geometry": {"type": gj["type"], "coordinates": rnd(gj["coordinates"])}})
    gp = os.path.join(ROOT, "data", "statarea_1995_geo.json")
    json.dump({"type": "FeatureCollection", "features": feats}, open(gp, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"\ngeo: {len(feats)} features -> {os.path.basename(gp)} ({os.path.getsize(gp):,} bytes)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
