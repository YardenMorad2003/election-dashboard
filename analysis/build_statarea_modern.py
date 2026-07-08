# -*- coding: utf-8 -*-
"""
build_statarea_modern.py — stat-area layer for the 2022-census-era elections
(K21-K25), reusing station_coordinates.json + our mis-geocode fixes and the
2022 CBS stat-area geometry/census. One consistent pipeline; applying
station_coord_fixes.json here is how the corrections propagate to K25/2022.

Per election e in argv (default: 25 22):
  coords: direct station_coordinates[settlement|ballot] (+ coord fixes by venue),
          fallback to ballot_locations_e venue-name match, else single-SA/none
  PIP into statistical_areas_2022.geojson (WGS84) -> stat22, prefer same semel
  aggregate per stat22, blocs from parties_national[e] (rh=right+haredi,
  cla=everything else incl opposition_right where present)
  census join from cbs_census_2022_statarea.csv (SA/combo/locality)

Outputs per election: data/statarea_k{e}.json (+ K25 also written to the
canonical data/statarea_2022.json), analysis/statarea_inputs/ballot_stat22_{e}.csv

Run: python -X utf8 analysis/build_statarea_modern.py 25 22
"""
import csv
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAP = os.path.join(HERE, "statarea_inputs")
EM = r"C:\Users\yarde\elections-merge\data"
GEOJSON = r"C:\Users\yarde\Downloads\statistical_areas_2022.geojson"
CENSUS = os.path.join(EM, "cbs_census_2022_statarea.csv")
GERESH = "'׳״‘’“”\"`"

CENSUS_KEEP = [("pop_approx", "pop"), ("pop_density", "density"), ("ReligionHeb", "religion"),
               ("hh_MidatDatiyut", "datiyut"), ("age_median", "age_med"), ("age0_19_pcnt", "age0_19"),
               ("age65_pcnt", "age65"), ("AcadmCert_pcnt", "acad"), ("employeesAnnual_medWage", "med_wage"),
               ("EmployeesWage_decile9Up", "top2dec"), ("WrkY_pcnt", "work"), ("israel_pcnt", "orig_il"),
               ("europe_pcnt", "orig_eur"), ("asia_pcnt", "orig_asia"), ("africa_pcnt", "orig_afr"),
               ("america_pcnt", "orig_am"), ("aliya2002_pcnt", "aliya02"), ("ChldBorn_avg", "chld"),
               ("size_avg", "hh_size"), ("own_pcnt", "own"), ("rent_pcnt", "rent"), ("Vehicle0_pcnt", "no_car")]


def norm(s):
    if not s:
        return ""
    for ch in GERESH:
        s = s.replace(ch, "")
    s = re.sub(r"[()\-,./\\:;+]", " ", s)
    s = s.replace("יי", "י").replace("וו", "ו")
    return " ".join(s.split())


def canon(x):
    try:
        f = float(x)
        return str(int(f)) if f == int(f) else x
    except ValueError:
        return x


def num(x):
    if x is None or x == "":
        return None
    try:
        f = float(x)
        return int(f) if f == int(f) and abs(f) < 1e9 else round(f, 2)
    except ValueError:
        return None


def load_geometry():
    from shapely.geometry import shape
    from shapely.strtree import STRtree
    print("loading 2022 geojson (126MB)...")
    g = json.load(open(GEOJSON, encoding="utf-8"))
    geoms, ids, sems = [], [], []
    per_semel = defaultdict(list)
    for f in g["features"]:
        p = f["properties"]
        sid = p.get("YISHUV_STAT_2022")
        if sid is None:
            continue
        try:
            geom = shape(f["geometry"])
        except Exception:
            continue
        if not geom.is_valid:
            geom = geom.buffer(0)
        idx = len(geoms)
        geoms.append(geom); ids.append(int(sid)); sems.append(int(p["SEMEL_YISHUV"]))
        per_semel[int(p["SEMEL_YISHUV"])].append(idx)
    print(f"  polygons: {len(geoms)}")
    return STRtree(geoms), geoms, ids, sems, per_semel


def census_index():
    census_sa, census_src, census_loc = {}, {}, {}
    with open(CENSUS, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            lc, sa = r["LocalityCode"], r["StatArea"]
            if lc and not sa:
                census_loc[int(float(lc))] = r
            elif lc and sa:
                semel = int(float(lc))
                members = r["StatAreaCmb"].split("+") if r["StatAreaCmb"] else [sa]
                for m in members:
                    try:
                        sid = semel * 10000 + int(float(m))
                    except ValueError:
                        continue
                    census_sa[sid] = r
                    census_src[sid] = "sa" if len(members) == 1 else "combo"
    return census_sa, census_src, census_loc


def main(elections):
    stations = json.load(open(rf"{EM}\station_coordinates.json", encoding="utf-8"))["stations"]
    # normalized Cain-direct index (like build_venue_dots' cain_direct): the raw
    # settlement|ballot lookup below misses whenever the CSV settlement string differs
    # from Cain's (e.g. 'תל אביב - יפו' vs 'תל אביב יפו'); if the venue was ALSO renamed
    # between elections (K25 'בי"ס ארנון' = Cain's 'בי"ס מוזיר'), the venue-name fallback
    # fails too and the ballots drop. K25-only: Cain's ballot numbering is K25-aligned.
    cain_norm = {}
    for k, stn in stations.items():
        sett, _, bal = k.rpartition("|")
        if stn.get("lat") is not None:
            cain_norm[(norm(sett), canon(bal))] = (stn["lat"], stn["lng"])
    # coord fixes by (semel, norm venue)
    coord_fixes = {}
    cf = os.path.join(SNAP, "station_coord_fixes.json")
    if os.path.exists(cf):
        for sem, vmap in json.load(open(cf, encoding="utf-8")).items():
            if sem.startswith("_"):
                continue
            for ven, ll in vmap.items():
                coord_fixes[(str(sem), norm(ven))] = (ll[0], ll[1])
    # K25 only: official per-kalpi addresses + address-scoped fixes
    # ("venue@@addr") — same-name venues at different buildings must not share
    # one coordinate (kashish class, 2026-07-06). Takes precedence over the
    # name-keyed fix, which cannot distinguish the buildings.
    addr25 = {}
    _p = os.path.join(SNAP, "k25_ballot_addresses.json")
    if os.path.exists(_p):
        addr25 = json.load(open(_p, encoding="utf-8"))
    addr_fixes = {}
    _p = os.path.join(SNAP, "station_coord_fixes_k25_addr.json")
    if os.path.exists(_p):
        for sem, vmap in json.load(open(_p, encoding="utf-8")).items():
            if sem.startswith("_"):
                continue
            for k, ll in vmap.items():
                ven, _, adr = k.partition("@@")
                addr_fixes[(str(sem), norm(ven), norm(adr))] = (ll[0], ll[1])
    # settlement-name -> semel bridge + venue index (fallback for elections whose
    # ballot numbers don't hit station_coordinates directly, e.g. K21-24)
    name_to_semel = {}
    for row in csv.DictReader(open(rf"{EM}\knesset25_ballots.csv", encoding="utf-8-sig")):
        name_to_semel[norm(row["שם ישוב"])] = row["סמל ישוב"].strip()
    sfix = os.path.join(SNAP, "settlement_name_fixes_18.json")
    if os.path.exists(sfix):
        for nm, sm in json.load(open(sfix, encoding="utf-8")).items():
            name_to_semel[norm(nm)] = str(sm)
    venues_by_semel = defaultdict(dict)
    for stn in stations.values():
        sm = name_to_semel.get(norm(stn["settlement"]))
        if not sm or stn.get("lat") is None:
            continue
        v = norm(stn.get("location") or "")
        if not v:
            continue
        prec = stn.get("source") in ("venue", "google_venue", "manual", "manual_correction")
        cur = venues_by_semel[sm].get(v)
        if cur is None or (prec and not cur[2]):
            venues_by_semel[sm][v] = (stn["lat"], stn["lng"], prec)

    def match_venue(semel, venue):
        vv = venues_by_semel.get(semel)
        if not vv:
            return None, None
        nv = norm(venue)
        hit = vv.get(nv)
        if hit is None:
            tv = set(nv.split())
            best, bj = None, 0.0
            for cand, e in vv.items():
                cs = set(cand.split())
                j = len(tv & cs) / len(tv | cs) if tv and cs else 0
                if j > bj:
                    best, bj = e, j
            if bj >= 0.5:
                hit = best
        return (hit[0], hit[1]) if hit else (None, None)

    pn_all = json.load(open(os.path.join(ROOT, "data", "parties_national.json"), encoding="utf-8"))
    census_sa, census_src, census_loc = census_index()
    tree, geoms, ids, sems, per_semel = load_geometry()
    from shapely.geometry import Point

    def pip(semel, lat, lng):
        idxs = per_semel.get(semel)
        if not idxs:
            return None
        if lat and lng:
            pt = Point(float(lng), float(lat))
            cont = [j for j in tree.query(pt) if geoms[j].covers(pt)]
            same = [j for j in cont if sems[j] == semel]
            if same:
                return ids[same[0]]
            best, bd = None, 1e18
            for j in idxs:
                d = geoms[j].distance(pt)
                if d < bd:
                    best, bd = j, d
            return ids[best]
        return ids[idxs[0]] if len(idxs) == 1 else None

    for e in elections:
        bl = json.load(open(rf"{EM}\ballot_locations_{e}.json", encoding="utf-8"))["ballot_to_location"]
        pn = pn_all[e]
        bloc_of = {p["code"]: p["bloc"] for p in pn["party_list"]}
        with open(rf"{EM}\knesset{e}_ballots.csv", encoding="utf-8-sig") as f:
            rdr = csv.DictReader(f)
            hdr = rdr.fieldnames
            bcol = next(c for c in ("קלפי", "מספר קלפי", "סמל קלפי") if c in hdr)
            party_cols = [c for c in hdr[hdr.index("כשרים") + 1:] if c != "ת. עדכון"]
            agg = defaultdict(lambda: {"el": 0, "vo": 0, "va": 0, "nb": 0, "p": defaultdict(int)})
            b2sa = []
            placed = geo = 0
            for r in rdr:
                semel = r["סמל ישוב"].strip()
                if semel == "0":
                    continue
                valid = int(r["כשרים"] or 0)
                geo += valid
                bal = canon(r[bcol].strip())
                skey = f"{r['שם ישוב'].strip()}|{r[bcol].strip()}"
                st = stations.get(skey) or {}
                venue = st.get("location") or bl.get(f"{semel}:{bal}") or bl.get(f"{semel}:{bal}.1")
                oaddr = addr25.get(semel, {}).get(bal, "") if e == "25" else ""
                cafix = addr_fixes.get((semel, norm(venue), norm(oaddr))) if (venue and oaddr) else None
                cfix = coord_fixes.get((semel, norm(venue))) if venue else None
                if cafix:
                    lat, lng = cafix
                elif cfix:
                    lat, lng = cfix
                elif st.get("lat") is not None:
                    lat, lng = st["lat"], st["lng"]
                elif e == "25" and (norm(r["שם ישוב"]), bal) in cain_norm:
                    # per-ballot Cain coordinate beats the venue-NAME fallback (which one
                    # coordinate per name can't survive a venue rename)
                    lat, lng = cain_norm[(norm(r["שם ישוב"]), bal)]
                elif venue:
                    lat, lng = match_venue(semel, venue)
                else:
                    lat, lng = None, None
                sid = pip(int(semel), lat, lng)
                b2sa.append((semel, bal, valid, sid or ""))
                if sid is None:
                    continue
                placed += valid
                a = agg[sid]
                a["el"] += int(r["בזב"] or 0); a["vo"] += int(r["מצביעים"] or 0)
                a["va"] += valid; a["nb"] += 1
                for c in party_cols:
                    v = int(r[c] or 0)
                    if v:
                        a["p"][c] += v

        # build records
        out = {}
        for sid, a in agg.items():
            valid = a["va"]
            if valid <= 0:
                continue
            semel, sa = divmod(sid, 10000)
            bv = defaultdict(int); other = 0
            for c, v in a["p"].items():
                b = bloc_of.get(c)
                if b:
                    bv[b] += v
                else:
                    other += v
            rh = bv["right"] + bv["haredi"]
            cla = sum(v for k, v in bv.items() if k not in ("right", "haredi"))
            blocs = {k: round(100 * bv[k] / valid, 2) for k in set(bloc_of.values())}
            blocs["rh"] = round(100 * rh / valid, 2)
            blocs["cla"] = round(100 * cla / valid, 2)
            blocs["other"] = round(100 * other / valid, 2)
            rec = {"semel": semel, "sa": sa, "eligible": a["el"], "voted": a["vo"], "valid": valid,
                   "n_ballots": a["nb"], "turnout": round(100 * a["vo"] / a["el"], 1) if a["el"] else None,
                   "winner": max(a["p"], key=a["p"].get) if a["p"] else None, "blocs": blocs,
                   "parties": {c: round(100 * v / valid, 2) for c, v in a["p"].items() if v / valid >= 0.005}}
            crow = census_sa.get(sid); src = census_src.get(sid)
            if crow is None:
                crow = census_loc.get(semel); src = "locality" if crow else None
            if crow:
                rec["census"] = {sh: (crow[col] if col in ("ReligionHeb", "hh_MidatDatiyut") else num(crow[col]))
                                 for col, sh in CENSUS_KEEP if col in crow}
                rec["census_src"] = src
            out[sid] = rec
        # census-only areas
        for sid, crow in census_sa.items():
            if sid in out:
                continue
            semel, sa = divmod(sid, 10000)
            out[sid] = {"semel": semel, "sa": sa, "census_src": census_src.get(sid),
                        "census": {sh: (crow[col] if col in ("ReligionHeb", "hh_MidatDatiyut") else num(crow[col]))
                                   for col, sh in CENSUS_KEEP if col in crow}}

        obj = {"meta": {"election": e, "census": "2022", "source": "raw ballots × station_coordinates (+coord fixes) × CBS 2022 SA"},
               "areas": {str(k): v for k, v in out.items()}}
        outpath = os.path.join(ROOT, "data", f"statarea_k{e}.json")
        json.dump(obj, open(outpath, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        with open(os.path.join(SNAP, f"ballot_stat22_{e}.csv"), "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f); w.writerow(["semel", "ballot", "valid", "stat22"]); w.writerows(b2sa)
        nv = sum(1 for v in out.values() if "valid" in v)
        print(f"K{e}: placed {placed:,}/{geo:,} = {100*placed/geo:.1f}% | SAs with votes {nv} | wrote {os.path.basename(outpath)}")
        if e == "25":
            json.dump(obj, open(os.path.join(ROOT, "data", "statarea_2022.json"), "w", encoding="utf-8"),
                      ensure_ascii=False, separators=(",", ":"))
            print("   also wrote canonical data/statarea_2022.json (fixes propagated)")


if __name__ == "__main__":
    main(sys.argv[1:] or ["25", "22"])
