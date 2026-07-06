# -*- coding: utf-8 -*-
"""
build_statarea_2008era.py — stat-area layer for the 2008-census-era elections
(K18-K20 = 2009/2013/2015) on the 2008 SA shapefile + mesukam 2008 census.

Same method as the K18 build, generalized: venue-name match into the geocoded
station index (+ coord fixes + settlement-name fixes) with neighbour imputation,
PIP into the 2008 layer (ITM->WGS84), aggregate with parties_national[e] blocs
(5-bloc, no opposition_right), then the mesukam/tab02/localities-religion census
join (reused from build_census_18).

Outputs per election e: data/statarea_k{e}.json + analysis/statarea_inputs/
statarea_counts_{e}.csv

Run: python -X utf8 analysis/build_statarea_2008era.py 19 20
"""
import csv
import glob
import json
import os
import re
import sys
from collections import defaultdict

import shapefile
from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform as shp_transform
from shapely.strtree import STRtree

import build_census_18 as bc18   # collect_mesukam / collect_tab02 / load_religion / shape_census

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAP = os.path.join(HERE, "statarea_inputs")
EM = r"C:\Users\yarde\elections-merge\data"
SHP = glob.glob(r"C:\Users\yarde\Downloads\statistical_areas_2008\*\*_1335.shp")[0]
GERESH = "'׳״‘’“”\"`"
PRECISE = ("venue", "google_venue", "manual", "manual_correction")


def norm(s):
    if not s:
        return ""
    for ch in GERESH:
        s = s.replace(ch, "")
    s = re.sub(r"[()\-,./\\:;+]", " ", s)
    return " ".join(s.replace("יי", "י").replace("וו", "ו").split())


def canon(x):
    try:
        f = float(x)
        return str(int(f)) if f == int(f) else x
    except ValueError:
        return x


def main(elections):
    stations = json.load(open(rf"{EM}\station_coordinates.json", encoding="utf-8"))["stations"]
    l25 = {}
    b25 = json.load(open(rf"{EM}\ballot_locations_25.json", encoding="utf-8"))
    for s, v in b25["settlements"].items():
        for b in v["ballots"]:
            l25[f"{s}:{b['ballot']}"] = b["location"]
    # settlement bridge + venue index (+ fixes)
    name_to_semel = {}
    for row in csv.DictReader(open(rf"{EM}\knesset25_ballots.csv", encoding="utf-8-sig")):
        name_to_semel[norm(row["שם ישוב"])] = row["סמל ישוב"].strip()
    sfix = os.path.join(SNAP, "settlement_name_fixes_18.json")
    if os.path.exists(sfix):
        for nm, sm in json.load(open(sfix, encoding="utf-8")).items():
            name_to_semel[norm(nm)] = str(sm)
    coord_fixes = {}
    cf = os.path.join(SNAP, "station_coord_fixes.json")
    if os.path.exists(cf):
        for sm, vm in json.load(open(cf, encoding="utf-8")).items():
            if not sm.startswith("_"):
                for ven, ll in vm.items():
                    coord_fixes[(str(sm), norm(ven))] = (ll[0], ll[1])
    venues = defaultdict(dict)
    for st in stations.values():
        sm = name_to_semel.get(norm(st["settlement"]))
        if not sm or st.get("lat") is None:
            continue
        v = norm(st.get("location") or "")
        if not v:
            continue
        prec = st.get("source") in PRECISE
        cur = venues[sm].get(v)
        if cur is None or (prec and not cur[2]):
            venues[sm][v] = (st["lat"], st["lng"], prec)

    def match(sm, venue):
        vv = venues.get(sm)
        if not vv:
            return None, None
        nv = norm(venue)
        hit = vv.get(nv)
        if hit is None:
            tv = set(nv.split()); best, bj = None, 0.0
            for cand, e in vv.items():
                cs = set(cand.split())
                j = len(tv & cs) / len(tv | cs) if tv and cs else 0
                if j > bj:
                    best, bj = e, j
            if bj >= 0.5:
                hit = best
        return (hit[0], hit[1]) if hit else (None, None)

    # 2008 geometry (ITM -> WGS84), single-SA counts
    tr = Transformer.from_crs(2039, 4326, always_xy=True).transform
    sf = shapefile.Reader(SHP, encoding="cp1255")
    flds = [f[0] for f in sf.fields[1:]]
    i_sem, i_ys = flds.index("SEMEL_YISH"), flds.index("YISHUV_STA")
    geoms, ids, sems = [], [], []
    per_semel = defaultdict(list); sa_count = defaultdict(int)
    for rec, shp in zip(sf.records(), sf.shapes()):
        s = rec[i_sem]
        if not s or s <= 0:
            continue
        g = shp_transform(tr, shape(shp.__geo_interface__))
        if not g.is_valid:
            g = g.buffer(0)
        idx = len(geoms)
        geoms.append(g); ids.append(int(rec[i_ys])); sems.append(int(s))
        per_semel[int(s)].append(idx); sa_count[str(s)] += 1
    tree = STRtree(geoms)

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

    # census (built once, election-independent)
    print("building 2008 census indices (mesukam + tab02 + religion)...")
    mes_sa, combo, mes_loc = bc18.collect_mesukam()
    ses = bc18.collect_tab02()
    rel_loc = bc18.load_religion()
    pn_all = json.load(open(os.path.join(ROOT, "data", "parties_national.json"), encoding="utf-8"))

    for e in elections:
        bl = json.load(open(rf"{EM}\ballot_locations_{e}.json", encoding="utf-8"))["ballot_to_location"]
        bloc_of = {p["code"]: p["bloc"] for p in pn_all[e]["party_list"]}
        with open(rf"{EM}\knesset{e}_ballots.csv", encoding="utf-8-sig") as f:
            rdr = csv.DictReader(f)
            hdr = rdr.fieldnames
            bcol = next(c for c in ("מספר קלפי", "סמל קלפי", "קלפי") if c in hdr)
            ecol = next((c for c in hdr if "בז" in c), "בזב")
            party_cols = [c for c in hdr[hdr.index("כשרים") + 1:] if c != "ת. עדכון"]
            rows = list(rdr)
        # coords per ballot
        per_semel_ballots = defaultdict(list)
        for r in rows:
            semel = r["סמל ישוב"].strip()
            if semel == "0":
                continue
            b = canon(r[bcol].strip())
            venue = bl.get(f"{semel}:{b}") or l25.get(f"{semel}:{b}") or l25.get(f"{semel}:{b}.1")
            single = sa_count.get(semel, 0) <= 1
            cfix = coord_fixes.get((semel, norm(venue))) if venue else None
            lat = lng = None
            if cfix:
                lat, lng = cfix
            elif single:
                pass
            elif venue:
                lat, lng = match(semel, venue)
            per_semel_ballots[semel].append({"r": r, "b": b, "single": single, "lat": lat, "lng": lng,
                                             "num": float(b) if re.match(r"^\d+(\.\d+)?$", b) else None})
        # neighbour imputation within multi-SA localities
        for semel, bs in per_semel_ballots.items():
            donors = [x for x in bs if x["lat"] is not None and x["num"] is not None]
            for x in bs:
                if x["single"] or x["lat"] is not None or x["num"] is None:
                    continue
                best, bd = None, 99
                for d in donors:
                    dd = abs(x["num"] - d["num"])
                    if 0 < dd < bd:
                        best, bd = d, dd
                if best and bd <= 2:
                    x["lat"], x["lng"] = best["lat"], best["lng"]
        # PIP + aggregate
        agg = defaultdict(lambda: {"el": 0, "vo": 0, "va": 0, "nb": 0, "p": defaultdict(int)})
        placed = geo = 0
        for semel, bs in per_semel_ballots.items():
            for x in bs:
                r = x["r"]; valid = int(r["כשרים"] or 0); geo += valid
                sid = pip(int(semel), x["lat"], x["lng"])
                if sid is None:
                    continue
                placed += valid
                a = agg[sid]
                a["el"] += int(r[ecol] or 0); a["vo"] += int(r["מצביעים"] or 0)
                a["va"] += valid; a["nb"] += 1
                for c in party_cols:
                    v = int(r[c] or 0)
                    if v:
                        a["p"][c] += v
        # records
        areas = {}
        counts = []
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
            blocs = {k: round(100 * bv[k] / valid, 2) for k in set(bloc_of.values())}
            blocs["rh"] = round(100 * (bv["right"] + bv["haredi"]) / valid, 2)
            blocs["cla"] = round(100 * sum(v for k, v in bv.items() if k not in ("right", "haredi")) / valid, 2)
            blocs["other"] = round(100 * other / valid, 2)
            areas[sid] = {"semel": semel, "sa": sa, "eligible": a["el"], "voted": a["vo"], "valid": valid,
                          "n_ballots": a["nb"], "turnout": round(100 * a["vo"] / a["el"], 1) if a["el"] else None,
                          "winner": max(a["p"], key=a["p"].get) if a["p"] else None, "blocs": blocs,
                          "parties": {c: round(100 * v / valid, 2) for c, v in a["p"].items() if v / valid >= 0.005}}
            counts.append([sid, semel, sa, a["el"], a["vo"], valid, a["nb"]] + [a["p"].get(c, 0) for c in party_cols])
        # census join (mesukam SA/combo, else locality; + tab02 ses + localities religion)
        for sid, rec in areas.items():
            semel = rec["semel"]
            if sid in mes_sa:
                cen = bc18.shape_census(mes_sa[sid], rel_from=mes_loc.get(semel), age_from=mes_loc.get(semel))
                rec["census_src"] = "combo" if sid in combo else "sa"
            elif semel in mes_loc:
                cen = bc18.shape_census(mes_loc[semel]); rec["census_src"] = "locality"
            else:
                cen = None; rec["census_src"] = None
            if cen is not None:
                if sid in ses:
                    cen.update({k: v for k, v in ses[sid].items() if v is not None})
                rl = rel_loc.get(semel)
                if rl:
                    cen["religion"] = {k: rl[k] for k in ("jew", "mosl", "druze", "arab")}
                    cen["rel_dom"] = rl["rel_dom"]; cen["rel_src"] = "loc2019"
                rec["census"] = cen
        for sid, raw in mes_sa.items():
            if sid in areas:
                continue
            semel, sa = divmod(sid, 10000)
            cen = bc18.shape_census(raw, rel_from=mes_loc.get(semel), age_from=mes_loc.get(semel))
            if sid in ses:
                cen.update({k: v for k, v in ses[sid].items() if v is not None})
            rl = rel_loc.get(semel)
            if rl:
                cen["religion"] = {k: rl[k] for k in ("jew", "mosl", "druze", "arab")}
                cen["rel_dom"] = rl["rel_dom"]; cen["rel_src"] = "loc2019"
            areas[sid] = {"semel": semel, "sa": sa, "census": cen, "census_src": "combo" if sid in combo else "sa"}
        obj = {"meta": {"election": e, "census": "2008", "blocs": sorted(set(bloc_of.values())),
                        "source": "raw ballots × station venues (+fixes) × 2008 SA shapefile × mesukam census"},
               "areas": {str(k): v for k, v in areas.items()}}
        json.dump(obj, open(os.path.join(ROOT, "data", f"statarea_k{e}.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))
        with open(os.path.join(SNAP, f"statarea_counts_{e}.csv"), "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f); w.writerow(["stat08", "semel", "sa", "eligible", "voted", "valid", "n_ballots"] + party_cols)
            w.writerows(counts)
        nv = sum(1 for v in areas.values() if "valid" in v)
        print(f"K{e}: placed {placed:,}/{geo:,} = {100*placed/geo:.1f}% | SAs w/ votes {nv} | wrote statarea_k{e}.json")


if __name__ == "__main__":
    main(sys.argv[1:] or ["19", "20"])
