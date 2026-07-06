# -*- coding: utf-8 -*-
"""
build_geo_18.py — STATAREA 2009 build step 8a: slim 2008 SA geometry.

Reprojects the 2008 shapefile (ITM 2039 -> WGS84 4326), simplifies polygons,
rounds coords to 5 decimals, keeps only SAs present in data/statarea_2009.json,
and writes data/statarea_2009_geo.json with properties {id, semel, sa, name,
name_en} — mirroring statarea_2022_geo.json so the page can share the renderer.

Run: python -X utf8 analysis/build_geo_18.py
"""
import glob
import json
import os

import shapefile
from pyproj import Transformer
from shapely.geometry import shape, mapping
from shapely.ops import transform as shp_transform

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SHP = glob.glob(r"C:\Users\yarde\Downloads\statistical_areas_2008\*\*_1335.shp")[0]
OUT = os.path.join(ROOT, "data", "statarea_2009_geo.json")


def rnd(coords):
    if isinstance(coords[0], (int, float)):
        return [round(coords[0], 5), round(coords[1], 5)]
    return [rnd(c) for c in coords]


def main():
    # union across every election served by the 2008 geometry (K18 + K19 + K20)
    keep = set()
    for fn in ("statarea_2009.json", "statarea_k19.json", "statarea_k20.json"):
        p = os.path.join(ROOT, "data", fn)
        if os.path.exists(p):
            keep |= set(int(k) for k in json.load(open(p, encoding="utf-8"))["areas"])
    tr = Transformer.from_crs(2039, 4326, always_xy=True).transform
    sf = shapefile.Reader(SHP, encoding="cp1255")
    flds = [f[0] for f in sf.fields[1:]]
    i_sem, i_ys = flds.index("SEMEL_YISH"), flds.index("YISHUV_STA")
    i_he, i_en = flds.index("Shem_Yishu"), flds.index("Shem_Yis_1")

    feats = []
    n_in = miss = 0
    for rec, shp in zip(sf.records(), sf.shapes()):
        sem = rec[i_sem]
        if not sem or sem <= 0:
            continue
        n_in += 1
        ys = int(rec[i_ys])
        if ys not in keep:
            continue
        g = shp_transform(tr, shape(shp.__geo_interface__)).simplify(0.0003, preserve_topology=True)
        if not g.is_valid:
            g = g.buffer(0)
        gj = mapping(g)
        feats.append({"type": "Feature",
                      "properties": {"id": ys, "semel": int(sem), "sa": ys % 10000,
                                     "name": (rec[i_he] or "").strip() or None,
                                     "name_en": (rec[i_en] or "").strip() or None},
                      "geometry": {"type": gj["type"], "coordinates": rnd(gj["coordinates"])}})
    got = {f["properties"]["id"] for f in feats}
    miss = len(keep - got)
    json.dump({"type": "FeatureCollection", "features": feats},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"polygons in layer (SEMEL>0): {n_in}; kept features: {len(feats)}")
    print(f"data-layer SAs without geometry: {miss} (census/vote areas absent from 2008 shapefile)")
    print(f"wrote {OUT} ({os.path.getsize(OUT):,} bytes)")


if __name__ == "__main__":
    main()
