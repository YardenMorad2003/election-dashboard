# -*- coding: utf-8 -*-
"""Project the pre-2019 elections (K16-K20) onto the 2022 stat-area geometry.

Why: the neighbourhood map's swing modes compare elections record-to-record, which only
works inside one census geometry (1995 / 2008 / 2022 SA ids differ). Long-run change
(2003 -> 2026, e.g. gentrification) needs the old vote on today's boundaries. Each old
kalpi already has a resolved coordinate from its own era's builder, so the projection is
just a second point-in-polygon of the same points into the 2022 polygons - no areal
interpolation, no crosswalk table.

Inputs  (all produced by the era builders):
  statarea_inputs/ballot_stat95_{16,17}.csv   semel,ballot,lat,lng,coord_src,stat95,valid
  statarea_inputs/ballot_coords_{18,19,20}.csv semel,ballot,kosher,single_sa,coord_src,lat,lng
  elections-merge/data/knesset{e}_ballots.csv  raw per-kalpi party votes
Outputs:
  data/statarea_k{e}_on22.json   {meta, areas:{sid:{valid, blocs:{rh,cla,...}, parties}}}
  analysis/statarea_on22_report.txt

Kalpis without a coordinate (single-SA localities in their own era) are placed only if
the locality is still a single SA in 2022; otherwise they stay unplaced (reported).
Areas with fewer than MIN_VALID projected votes are dropped: no baseline is better than
a baseline made of one stray kalpi.

Run: python -X utf8 analysis/build_statarea_on22.py [16 17 18 19 20]
"""
import csv
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_statarea_modern import load_geometry, canon, EM, SNAP  # noqa: E402

ROOT = os.path.dirname(HERE)
MIN_VALID = 100
NEAR_DEG = 0.003          # ~300 m: a point just outside every polygon snaps to the nearest one
YEAR = {"16": 2003, "17": 2006, "18": 2009, "19": 2013, "20": 2015}
DOUBLE = "מעטפות כפולות"


def iv(x):
    try:
        return int(float(x or 0))
    except ValueError:
        return 0


def coords_for(e):
    """-> list of (semel, ballot, lat, lng, valid) in file order."""
    out = []
    if e in ("16", "17"):
        with open(os.path.join(SNAP, f"ballot_stat95_{e}.csv"), encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                out.append((r["semel"], r["ballot"], r["lat"], r["lng"], iv(r["valid"])))
    else:
        with open(os.path.join(SNAP, f"ballot_coords_{e}.csv"), encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                out.append((r["semel"], r["ballot"], r["lat"], r["lng"], iv(r["kosher"])))
    return out


def raw_rows(e):
    with open(rf"{EM}\knesset{e}_ballots.csv", encoding="utf-8-sig") as f:
        rdr = csv.DictReader(f)
        hdr = rdr.fieldnames
        party_cols = hdr[hdr.index("כשרים") + 1:]
        if "שם ישוב" in party_cols:            # K16 keeps the name after the counts
            party_cols = [c for c in party_cols if c != "שם ישוב"]
        bcol = next(c for c in ("מספר קלפי", "סמל קלפי", "קלפי") if c in hdr)
        rows = [r for r in rdr if (r.get("שם ישוב") or "").strip() != DOUBLE]
    return rows, party_cols, bcol


def join(e, coords, rows, party_cols, bcol):
    """Attach raw party votes to each coordinate row. Returns list of (semel, lat, lng, valid, votes)."""
    have_semel = "סמל ישוב" in rows[0]
    out, miss = [], 0
    if have_semel:
        idx = defaultdict(list)
        for r in rows:
            sm = str(iv(r["סמל ישוב"]))
            if sm == "0":
                continue
            b = r[bcol].strip()
            for k in {b, canon(b)}:
                idx[(sm, k)].append(r)
        for sm, b, lat, lng, valid in coords:
            cands = idx.get((sm, b)) or idx.get((sm, canon(b))) or []
            cands = [r for r in cands if iv(r["כשרים"]) == valid] or cands
            if len(cands) != 1 or iv(cands[0]["כשרים"]) != valid:
                miss += valid
                continue
            out.append((sm, lat, lng, valid, cands[0]))
    else:
        # K17 has no locality code: the era builder wrote its snapshot grouped by locality in
        # first-appearance order, each group in file order. Rebuild that order and zip,
        # checking kalpi number and valid votes row by row.
        groups = defaultdict(list)
        for r in rows:
            groups[" ".join(r["שם ישוב"].split())].append(r)
        by_key = defaultdict(list)
        for r in rows:
            by_key[(r[bcol].strip(), iv(r["כשרים"]))].append(r)
        used = set()
        # sequential cursor inside the candidates of each (ballot, valid) key keeps file order
        for sm, b, lat, lng, valid in coords:
            cands = [r for r in by_key.get((b, valid), []) if id(r) not in used]
            if not cands:
                miss += valid
                continue
            used.add(id(cands[0]))
            out.append((sm, lat, lng, valid, cands[0]))
    return out, miss


def main(elections):
    pn_all = json.load(open(os.path.join(ROOT, "data", "parties_national.json"), encoding="utf-8"))
    tree, geoms, ids, sems, per_semel = load_geometry()
    from shapely.geometry import Point

    def pip(semel, lat, lng):
        if lat and lng:
            pt = Point(float(lng), float(lat))
            cont = [j for j in tree.query(pt) if geoms[j].covers(pt)]
            if cont:
                same = [j for j in cont if sems[j] == semel]
                return ids[(same or cont)[0]]
            near = [(geoms[j].distance(pt), j) for j in tree.query(pt.buffer(NEAR_DEG))]
            near = [t for t in near if t[0] <= NEAR_DEG]
            return ids[min(near)[1]] if near else None
        idxs = per_semel.get(semel) or []
        return ids[idxs[0]] if len(idxs) == 1 else None

    rep = []
    for e in elections:
        coords = coords_for(e)
        rows, party_cols, bcol = raw_rows(e)
        joined, miss = join(e, coords, rows, party_cols, bcol)
        bloc_of = {p["code"]: p["bloc"] for p in pn_all[e]["party_list"]}
        agg = defaultdict(lambda: {"va": 0, "p": defaultdict(int)})
        total = sum(c[4] for c in coords)
        placed = 0
        for sm, lat, lng, valid, r in joined:
            sid = pip(int(sm), lat, lng)
            if sid is None:
                continue
            placed += valid
            a = agg[sid]
            a["va"] += valid
            for c in party_cols:
                v = iv(r[c])
                if v:
                    a["p"][c] += v
        out, dropped = {}, 0
        for sid, a in agg.items():
            valid = a["va"]
            if valid < MIN_VALID:
                dropped += valid
                continue
            bv = defaultdict(int)
            for c, v in a["p"].items():
                if bloc_of.get(c):
                    bv[bloc_of[c]] += v
            rh = bv["right"] + bv["haredi"]
            cla = sum(v for k, v in bv.items() if k not in ("right", "haredi", "third"))
            blocs = {k: round(100 * bv[k] / valid, 2) for k in set(bloc_of.values())}
            blocs["rh"] = round(100 * rh / valid, 2)
            blocs["cla"] = round(100 * cla / valid, 2)
            out[str(sid)] = {"valid": valid, "blocs": blocs,
                             "parties": {c: round(100 * v / valid, 2) for c, v in a["p"].items() if v / valid >= 0.01}}
        obj = {"meta": {"election": e, "year": YEAR[e], "geometry": "cbs_2022 (projected)", "min_valid": MIN_VALID,
                        "source": f"K{e} kalpi coordinates (own-era builder) re-placed into CBS 2022 stat areas"},
               "areas": out}
        path = os.path.join(ROOT, "data", f"statarea_k{e}_on22.json")
        json.dump(obj, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        line = (f"K{e} ({YEAR[e]}): kalpis {len(coords):,} | joined to raw votes {100*(total-miss)/total:.1f}% of valid | "
                f"placed {placed:,}/{total:,} = {100*placed/total:.1f}% | areas {len(out)} "
                f"(dropped <{MIN_VALID}: {dropped:,} votes) | {os.path.getsize(path)//1024} KB")
        print(line)
        rep.append(line)
    with open(os.path.join(HERE, "statarea_on22_report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(rep) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:] or ["16", "17", "18", "19", "20"])
