# -*- coding: utf-8 -*-
"""
build_locality_fill.py — data for the statarea map's poster-mode municipal
underlay ("municipal boundaries added to reduce empty space", as the classic
precinct posters put it).

From parties_by_locality.json (per-party % per locality, K13-K25) derive each
locality's winning party + its share per election -> data/locality_results.json
{election: {locality_name: [code, share]}}. From election_map_geo.json keep a
slimmed name-only copy -> data/locality_fill_geo.json (drawn beneath the SA
layer; localities without SA coverage get their locality-level color).

Run: python -X utf8 analysis/build_locality_fill.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")


def main():
    pbl = json.load(open(os.path.join(DATA, "parties_by_locality.json"), encoding="utf-8"))
    res = {}
    for e, locs in pbl.items():
        out = {}
        for nm, parties in locs.items():
            best, bp = None, 0.0
            for code, pct in parties.items():
                try:
                    p = float(pct or 0)
                except (TypeError, ValueError):
                    continue
                if p > bp:
                    best, bp = code, p
            if best:
                out[nm] = [best, round(bp, 1)]
        res[e] = out
        print(f"K{e}: {len(out)} localities with a winner")
    rp = os.path.join(DATA, "locality_results.json")
    json.dump(res, open(rp, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {os.path.basename(rp)} ({os.path.getsize(rp):,} bytes)")

    g = json.load(open(os.path.join(DATA, "election_map_geo.json"), encoding="utf-8"))
    names_with_results = set()
    for locs in res.values():
        names_with_results |= set(locs)
    feats = []
    unmatched = 0
    for f in g["features"]:
        nm = f["properties"].get("name")
        if not nm:
            continue
        if nm not in names_with_results:
            unmatched += 1
            continue
        feats.append({"type": "Feature", "properties": {"name": nm},
                      "geometry": f["geometry"]})
    gp = os.path.join(DATA, "locality_fill_geo.json")
    json.dump({"type": "FeatureCollection", "features": feats},
              open(gp, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"geo: kept {len(feats)}/{len(g['features'])} localities "
          f"(no-result: {unmatched}) -> {os.path.basename(gp)} ({os.path.getsize(gp):,} bytes)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
