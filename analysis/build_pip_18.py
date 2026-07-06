# -*- coding: utf-8 -*-
"""
build_pip_18.py — STATAREA 2009 build step 5: point-in-polygon into the 2008
stat-area layer.

Input : analysis/statarea_inputs/ballot_coords_18.csv  (from build_coords_18.py)
Layer : 2008 SA shapefile, reprojected ITM(EPSG:2039) -> WGS84(EPSG:4326).
Output: analysis/statarea_inputs/ballot_stat08_18.csv
          semel, ballot, kosher, coord_src, stat08, place

Assignment (FIX #2: only SEMEL_YISH > 0 polygons):
  - single-SA locality (1 polygon for the semel): assign that stat08 directly.
  - has coords: PIP; keep the SAME-semel containing polygon; if the point is
    contained only by a different semel's polygon (or none), snap to the nearest
    SAME-semel polygon (keeps votes inside their own locality -> maximizes
    closure vs localities.json, zero cross-semel spillover by construction).
  - no same-semel polygon at all (e.g. semel absent from 2008 layer): uncovered.

Run: python -X utf8 analysis/build_pip_18.py
"""
import csv
import glob
import os
from collections import defaultdict

import shapefile
from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform as shp_transform
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(HERE, "statarea_inputs")
SHP = glob.glob(r"C:\Users\yarde\Downloads\statistical_areas_2008\*\*_1335.shp")[0]
COORDS = os.path.join(SNAP, "ballot_coords_18.csv")
OUT = os.path.join(SNAP, "ballot_stat08_18.csv")


def main():
    tr = Transformer.from_crs(2039, 4326, always_xy=True).transform
    sf = shapefile.Reader(SHP, encoding="cp1255")
    flds = [f[0] for f in sf.fields[1:]]
    i_sem, i_ys, i_st = flds.index("SEMEL_YISH"), flds.index("YISHUV_STA"), flds.index("STAT08")

    geoms, stat08s, semels = [], [], []
    per_semel = defaultdict(list)          # semel(str) -> list of idx
    key_mismatch = 0
    for rec, shp in zip(sf.records(), sf.shapes()):
        sem = rec[i_sem]
        if not sem or sem <= 0:            # FIX #2
            continue
        ys = rec[i_ys]
        if ys != sem * 10000 + rec[i_st]:  # key-convention sanity
            key_mismatch += 1
        g = shp_transform(tr, shape(shp.__geo_interface__))
        if not g.is_valid:
            g = g.buffer(0)
        idx = len(geoms)
        geoms.append(g); stat08s.append(int(ys)); semels.append(str(sem))
        per_semel[str(sem)].append(idx)
    print(f"polygons kept (SEMEL_YISH>0): {len(geoms)}; key mismatches: {key_mismatch}; "
          f"semels: {len(per_semel)}")
    tree = STRtree(geoms)

    def assign(semel, lat, lng):
        idxs = per_semel.get(semel)
        if not idxs:
            return None, "no_poly"
        if lat and lng:
            pt = Point(float(lng), float(lat))
            cand = tree.query(pt)                       # bbox prefilter (indices)
            contained = [j for j in cand if geoms[j].covers(pt)]
            same = [j for j in contained if semels[j] == semel]
            if same:
                return stat08s[same[0]], "pip"
            # not contained by own semel -> snap to nearest same-semel polygon
            best, bd = None, 1e18
            for j in idxs:
                d = geoms[j].distance(pt)
                if d < bd:
                    best, bd = j, d
            return stat08s[best], ("snap" if not contained else "snap_from_other")
        # no coords: only valid for single-SA semel
        if len(idxs) == 1:
            return stat08s[idxs[0]], "single_direct"
        return None, "no_coord_multi"

    rows_out = []
    stat = defaultdict(int); vstat = defaultdict(int); geo = 0
    with open(COORDS, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            semel = r["semel"]; kosher = int(r["kosher"]); geo += kosher
            s08, place = assign(semel, r["lat"], r["lng"])
            stat[place] += 1; vstat[place] += kosher
            rows_out.append([semel, r["ballot"], kosher, r["coord_src"], s08 if s08 else "", place])

    print(f"\ngeographic votes: {geo:,}")
    print(f"{'place':16s} {'ballots':>8s} {'votes':>11s} {'%geo':>7s}")
    placed = 0
    for p in ("pip", "single_direct", "snap", "snap_from_other", "no_poly", "no_coord_multi"):
        if stat[p] or vstat[p]:
            print(f"{p:16s} {stat[p]:8d} {vstat[p]:11,d} {vstat[p]/geo:7.1%}")
        if p in ("pip", "single_direct", "snap", "snap_from_other"):
            placed += vstat[p]
    print(f"placed into a stat08: {placed:,} = {placed/geo:.1%} of geo votes")

    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["semel", "ballot", "kosher", "coord_src", "stat08", "place"])
        w.writerows(rows_out)
    print(f"wrote {OUT}")

    # spot checks: dominant semel-composition of a few known stat08 sets
    print("\nspot check — SAs per known semel:")
    for name, sem in [("Bnei Brak", "6100"), ("Umm al-Fahm", "2710"), ("Tel Aviv", "5000")]:
        sas = sorted({stat08s[j] for j in per_semel.get(sem, [])})
        print(f"  {name} (semel {sem}): {len(sas)} SAs, e.g. {sas[:4]}")


if __name__ == "__main__":
    main()
