# -*- coding: utf-8 -*-
"""
check_dots_vs_sa.py — consistency probe: per stat-area, compare the layer's
vote total against the sum of venue dots physically inside its polygon.

Born from the 2026-07-11 user report ("2015 and prior: SA totals don't match
the kalpiot located in them"). NOT a correctness gate — a *visual-agreement*
metric: containment is checked against the (simplified) display geometry, and
legitimate design choices break equality (same-municipality snapping, dots on
boundary streets, dropped-coordinate ballots). Reference values (2026-07-12):

  K17 2006 (address-based, shipped) : 33% exact | 31.9% of votes in |diff|
  K20 2015 OLD (venue-name method)  : 66% exact | 21.8%
  K18 2009 OLD (venue-name)         : 87% exact |  6.4%   <- self-referential
  K18 2009 NEW (official addresses) : 83% exact | 13.8%   (accuracy >> old)
  K19 2013 NEW (K18 crosswalk)      : 83% exact | 11.1%   (coordinate-keyed dots)
  K20 2015 NEW (K18 crosswalk)      : 83% exact | 11.2%   (coordinate-keyed dots)
  K24 2021 (modern shared-index)    : 81% exact |  9.9%

Run: python -X utf8 analysis/check_dots_vs_sa.py <sa.json> <geo.json> <dots.json>
e.g. python -X utf8 analysis/check_dots_vs_sa.py statarea_2009.json statarea_2009_geo.json venue_dots_k18.json
     (bare filenames resolve inside data/)
"""
import json
import os
import sys

from shapely.geometry import Point, shape
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def respath(p):
    return p if os.path.exists(p) else os.path.join(ROOT, "data", p)


def main(safile, geofile, dotsfile):
    sa = json.load(open(respath(safile), encoding="utf-8"))["areas"]
    dots = json.load(open(respath(dotsfile), encoding="utf-8"))["venues"]
    geo = json.load(open(respath(geofile), encoding="utf-8"))

    geoms, props = [], []
    for f in geo["features"]:
        gm = shape(f["geometry"])
        if not gm.is_valid:
            gm = gm.buffer(0)
        geoms.append(gm)
        props.append(f["properties"])
    tree = STRtree(geoms)

    per_poly = {}
    outside = 0
    for d in dots:
        pt = Point(d[1], d[0])
        hit = next((j for j in tree.query(pt) if geoms[j].covers(pt)), None)
        if hit is None:
            outside += d[2]
            continue
        pid = str(props[hit].get("id"))
        per_poly[pid] = per_poly.get(pid, 0) + d[2]

    rendered = {str(p.get("id")) for p in props}
    diffs = []
    for pid in rendered:
        sv = sa.get(pid, {}).get("valid", 0) or 0
        dv = per_poly.get(pid, 0)
        if sv or dv:
            diffs.append((abs(sv - dv), pid, sv, dv))
    diffs.sort(reverse=True)
    exact = sum(1 for d, *_ in diffs if d == 0)
    close = sum(1 for d, *_ in diffs if d <= 50)
    tot = sum(sv for _, _, sv, _ in diffs)
    tad = sum(d for d, *_ in diffs)
    print(f"{safile} vs {dotsfile} on {geofile}")
    print(f"  SAs compared: {len(diffs)} | exact: {exact} ({100*exact/len(diffs):.0f}%) | "
          f"within 50: {close} ({100*close/len(diffs):.0f}%)")
    print(f"  sum|diff| = {tad:,} votes = {100*tad/tot:.1f}% of {tot:,} | dots outside any polygon: {outside:,}")
    print("  worst 5:", [(pid, sv, dv) for _, pid, sv, dv in diffs[:5]])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    main(*sys.argv[1:])
