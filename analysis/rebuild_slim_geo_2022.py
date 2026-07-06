# -*- coding: utf-8 -*-
"""
rebuild_slim_geo_2022.py — regenerate data/statarea_2022_geo.json with the
keep-set as the UNION of all modern-era layers (K21-K25). The original slim
geo was written from the pre-rebuild K25 snapshot and misses ~170 SAs that the
modern pipeline places votes into.

Run: python -X utf8 analysis/rebuild_slim_geo_2022.py
"""
import json
import os
import sys

from shapely.geometry import shape, mapping

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GEOJSON = r"C:\Users\yarde\Downloads\statistical_areas_2022.geojson"
OUT = os.path.join(ROOT, "data", "statarea_2022_geo.json")


def rnd(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], 5), round(c[1], 5)]
    return [rnd(x) for x in c]


def main():
    keep = set()
    for e in ("21", "22", "23", "24", "25"):
        p = os.path.join(ROOT, "data", f"statarea_k{e}.json")
        keep |= set(int(k) for k in json.load(open(p, encoding="utf-8"))["areas"])
    print(f"union keep-set: {len(keep)} SAs")
    print("loading 2022 geojson (126MB)...")
    g = json.load(open(GEOJSON, encoding="utf-8"))
    feats = []
    for f in g["features"]:
        p = f["properties"]
        sid = p.get("YISHUV_STAT_2022")
        if sid is None or int(sid) not in keep:
            continue
        try:
            geom = shape(f["geometry"]).simplify(0.0003, preserve_topology=True)
        except Exception:
            continue
        if not geom.is_valid:
            geom = geom.buffer(0)
        gj = mapping(geom)
        feats.append({"type": "Feature",
                      "properties": {"id": int(sid), "semel": int(p["SEMEL_YISHUV"]),
                                     "sa": int(sid) % 10000,
                                     "name": p.get("SHEM_YISHUV"), "name_en": p.get("SHEM_YISHUV_ENGLISH")},
                      "geometry": {"type": gj["type"], "coordinates": rnd(gj["coordinates"])}})
    got = {f["properties"]["id"] for f in feats}
    json.dump({"type": "FeatureCollection", "features": feats},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"kept {len(feats)} features; data SAs without geometry: {len(keep - got)}")
    print(f"wrote {OUT} ({os.path.getsize(OUT):,} bytes)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
