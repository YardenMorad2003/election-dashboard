# -*- coding: utf-8 -*-
"""
build_landing_points.py — data/landing_points.json for the landing-page dot map.

One compact fetch for index.html: locality centroids + per-election bloc shares
+ national bloc totals. Sources (all repo-local):
  - data/election_map_geo.json   polygons -> shoelace centroid (primary, tracked)
  - cities_points_demo.geojson   point fallback for localities without polygons
                                 (gitignored demo artifact; used only if present)
  - data/localities.json         per-election right_haredi/center_left_arab/turnout
  - data/core.json               national bloc totals per election

Run from repo root:  python -X utf8 analysis/build_landing_points.py
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KS = [str(k) for k in range(13, 26)]


def ring_centroid(ring):
    """Shoelace-weighted centroid of one linear ring [[x,y],...]."""
    a = cx = cy = 0.0
    for i in range(len(ring) - 1):
        x0, y0 = ring[i][0], ring[i][1]
        x1, y1 = ring[i + 1][0], ring[i + 1][1]
        w = x0 * y1 - x1 * y0
        a += w
        cx += (x0 + x1) * w
        cy += (y0 + y1) * w
    if abs(a) < 1e-12:  # degenerate: average the vertices
        xs = [p[0] for p in ring]; ys = [p[1] for p in ring]
        return sum(xs) / len(xs), sum(ys) / len(ys), 0.0
    return cx / (3 * a), cy / (3 * a), abs(a)


def feature_centroid(geom):
    """Centroid of the largest ring (Polygon or MultiPolygon)."""
    if geom["type"] == "Polygon":
        polys = [geom["coordinates"]]
    elif geom["type"] == "MultiPolygon":
        polys = geom["coordinates"]
    else:
        return None
    best = None
    for poly in polys:
        x, y, a = ring_centroid(poly[0])
        if best is None or a > best[2]:
            best = (x, y, a)
    return (best[0], best[1]) if best else None


def main():
    coords = {}

    geo = json.load(open(os.path.join(ROOT, "data", "election_map_geo.json"), encoding="utf-8"))
    for ft in geo["features"]:
        n = ft["properties"].get("name")
        if n and n not in coords and ft.get("geometry"):
            c = feature_centroid(ft["geometry"])
            if c:
                coords[n] = c

    demo = os.path.join(ROOT, "cities_points_demo.geojson")
    n_fallback = 0
    if os.path.exists(demo):
        pts = json.load(open(demo, encoding="utf-8"))
        for ft in pts["features"]:
            n = ft["properties"].get("name")
            if n and n not in coords and ft.get("geometry"):
                coords[n] = tuple(ft["geometry"]["coordinates"][:2])
                n_fallback += 1

    locs = json.load(open(os.path.join(ROOT, "data", "localities.json"), encoding="utf-8"))
    core = json.load(open(os.path.join(ROOT, "data", "core.json"), encoding="utf-8"))

    out_pts, missing = [], 0
    for loc in locs:
        c = coords.get(loc["name"])
        if not c:
            missing += 1
            continue
        e = {}
        for k in KS:
            d = (loc.get("data") or {}).get(k)
            if not d or d.get("right_haredi_pct") is None:
                continue
            e[k] = [round(d["right_haredi_pct"], 1),
                    round(d["center_left_arab_pct"], 1),
                    round(d["turnout_pct"], 1) if d.get("turnout_pct") is not None else None,
                    int(d.get("eligible") or 0)]
        if e:
            out_pts.append({"n": loc["name"], "x": round(c[0], 4), "y": round(c[1], 4), "e": e})

    national = {}
    for k, nb in (core.get("national_blocs") or {}).items():
        national[k] = {"rh": round(nb["right"] + nb["haredi"], 1),
                       "cla": round(nb["center_left_arab"], 1)}

    out = {"years": core["metadata"]["knesset_years"], "national": national, "pts": out_pts}
    path = os.path.join(ROOT, "data", "landing_points.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    kb = os.path.getsize(path) / 1024
    print(f"landing_points.json: {len(out_pts)} localities "
          f"({n_fallback} via demo-point fallback, {missing} without coords), {kb:.0f} KB")


if __name__ == "__main__":
    main()
