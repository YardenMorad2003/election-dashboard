# -*- coding: utf-8 -*-
"""
build_census_delta.py — project the 2008 census onto 2022 stat-area geometry so the
map can show census-vs-census change (currently: acad = academic-degree share).

Method: population-weighted areal interpolation. For every 2022 SA polygon, intersect
with the 2008 SA polygons that carry the dimension; each piece is weighted by
intersection area x the 2008 SA's population density (pop assumed uniform within the
2008 SA; density falls back to the national median where 2008 pop is missing).
The projected value is the weighted mean. A 2022 SA gets a value only when >=50% of
its area is covered by contributing 2008 SAs.

Geometry note: both inputs are the tracked WGS84 display files (simplified). Areas are
computed in raw degrees^2 — anisotropic globally but locally uniform, and only ratios
within one neighborhood matter here. Definitional caveat carried to the page: 2008
acad = Acadm1Cert+Acadm2Cert summed, 2022 = AcadmCert; close but not identical.

Output: data/census_delta_2022.json  {"semel|sa": [acad2008, coverage_pct]} + meta
Report: analysis/census_delta_report.txt (coverage stats + top movers for sanity)
Run: python -X utf8 analysis/build_census_delta.py
"""
import json
import os

from shapely.geometry import shape
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "data", "census_delta_2022.json")
REPORT = os.path.join(HERE, "census_delta_report.txt")

MIN_COVER = 0.5


def load(name):
    return json.load(open(os.path.join(ROOT, "data", name), encoding="utf-8"))


def clean(geom_dict):
    """shape() + buffer(0) validity repair; None for degenerate/unfixable geometries."""
    try:
        g = shape(geom_dict)
        if not g.is_valid:
            g = g.buffer(0)
        return g if (not g.is_empty and g.area > 0) else None
    except Exception:
        return None


def main():
    g08, g22 = load("statarea_2009_geo.json"), load("statarea_2022_geo.json")
    d08, d22 = load("statarea_2009.json"), load("statarea_2022.json")
    a08, a22 = d08["areas"], d22["areas"]

    # 2008 contributors: geometry + acad; density from pop where available
    geoms, acads, dens = [], [], []
    densities = []
    for f in g08["features"]:
        rec = a08.get(str(f["properties"]["id"]))
        c = (rec or {}).get("census") or {}
        if c.get("acad") is None:
            continue
        g = clean(f["geometry"])
        if g is None:
            continue
        geoms.append(g)
        acads.append(c["acad"])
        d = (c.get("pop") / g.area) if c.get("pop") else None
        dens.append(d)
        if d:
            densities.append(d)
    densities.sort()
    med_dens = densities[len(densities) // 2]
    dens = [d if d else med_dens for d in dens]
    tree = STRtree(geoms)
    print(f"2008 contributors: {len(geoms)} SAs with acad")

    out, rows = {}, []
    n_null = 0
    for f in g22["features"]:
        p = f["properties"]
        tgt = clean(f["geometry"])
        if tgt is None:
            n_null += 1
            continue
        wsum = vsum = cover = 0.0
        for i in tree.query(tgt):
            try:
                inter = tgt.intersection(geoms[i])
            except Exception:
                continue
            if inter.is_empty:
                continue
            a = inter.area
            cover += a
            w = a * dens[i]
            wsum += w
            vsum += w * acads[i]
        cov = cover / tgt.area
        if cov < MIN_COVER or wsum <= 0:
            n_null += 1
            continue
        acad08 = round(vsum / wsum, 1)
        key = f"{p['semel']}|{p['sa']}"
        out[key] = [acad08, round(100 * min(cov, 1.0))]
        rec = a22.get(str(p["id"]))
        acad22 = ((rec or {}).get("census") or {}).get("acad")
        if acad22 is not None:
            rows.append((round(acad22 - acad08, 1), p["name"], p["sa"], acad08, acad22))

    json.dump({"meta": {"dim": "acad", "src": "census2008->2022 areal interp, pop-weighted",
                        "min_cover": MIN_COVER, "n": len(out)}, "areas": out},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {OUT}: {len(out)} SAs ({n_null} below cover/geometry gate)")

    rows.sort(reverse=True)
    with open(REPORT, "w", encoding="utf-8") as r:
        r.write(f"census delta 2008->2022 (acad): {len(out)} projected, {len(rows)} with 2022 acad\n")
        deltas = sorted(x[0] for x in rows)
        r.write(f"delta pctiles: p5={deltas[len(deltas)//20]} p50={deltas[len(deltas)//2]} "
                f"p95={deltas[-len(deltas)//20]}\n\nTOP GROWTH\n")
        for d, name, sa, a0, a1 in rows[:15]:
            r.write(f"  {name} sa{sa}: {a0} -> {a1}  (+{d})\n")
        r.write("\nTOP DECLINE\n")
        for d, name, sa, a0, a1 in rows[-15:]:
            r.write(f"  {name} sa{sa}: {a0} -> {a1}  ({d})\n")
    print(f"report -> {REPORT}")
    print("sample pctiles:", deltas[len(deltas)//20], deltas[len(deltas)//2], deltas[-len(deltas)//20])


if __name__ == "__main__":
    main()
