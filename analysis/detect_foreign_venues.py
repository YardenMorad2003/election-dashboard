# -*- coding: utf-8 -*-
"""
detect_foreign_venues.py — the Hashmonaim class (user-found 2026-07-06): a
venue whose dot physically sits inside ANOTHER city's statistical-area polygon
while its own city's polygons are kilometers away. Catches settlement-name /
street-name cross-city geocode collisions with pure geometry — no APIs.

Flags (K24∪K25 dots, 2022 geometry): host-semel != own-semel AND the venue is
>3 km from the nearest polygon of its own semel. Venues whose semel has no
polygons at all are skipped (nothing to compare).

Run: python -X utf8 analysis/detect_foreign_venues.py
"""
import json, os, sys, math, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from build_residence_estimate import polys_of, point_in_polys  # noqa: E402

KX, DEG_KM = 0.845, 111.32


def main():
    geo = json.load(open(os.path.join(ROOT, "data", "statarea_2022_geo.json"), encoding="utf-8"))
    feats = []
    by_sem = collections.defaultdict(list)
    for f in geo["features"]:
        pr = f["properties"]
        polys = polys_of(f["geometry"])
        xs = [x for rings in polys for x, _ in rings[0]]
        ys = [y for rings in polys for _, y in rings[0]]
        rec = (pr["semel"], pr["id"], polys, (min(xs), min(ys), max(xs), max(ys)), pr["name"])
        feats.append(rec)
        by_sem[pr["semel"]].append(rec)

    def dist_to_sem(lat, lng, sem):
        best = 9e9
        for _, _, polys, bb, _ in by_sem.get(sem, []):
            for rings in polys:
                for x, y in rings[0][::3]:
                    d = math.hypot((lat - y) * DEG_KM, (lng - x) * DEG_KM * KX)
                    if d < best:
                        best = d
        return best

    def host_of(lat, lng):
        for sem, sid, polys, bb, name in feats:
            if bb[0] <= lng <= bb[2] and bb[1] <= lat <= bb[3] and point_in_polys(lng, lat, polys):
                return sem, sid, name
        return None

    seen = set()
    flags = []
    for yr in ("25", "24"):
        vd = json.load(open(os.path.join(ROOT, "data", f"venue_dots_k{yr}.json"), encoding="utf-8"))["venues"]
        for v in vd:
            lat, lng, valid, name, sem = v[0], v[1], v[2], v[7], v[8]
            key = (sem, name)
            if key in seen or sem not in by_sem:
                continue
            seen.add(key)
            host = host_of(lat, lng)
            if not host or host[0] == sem:
                continue
            d_own = dist_to_sem(lat, lng, sem)
            if d_own > 3.0:
                flags.append((valid, yr, sem, name, host, round(d_own, 1)))

    flags.sort(reverse=True)
    print(f"foreign-venue flags: {len(flags)}")
    for valid, yr, sem, name, host, d in flags:
        print(f"  K{yr} semel={sem:<5} {name[:34]!r:36} k={valid:>5} sits in {host[2]} "
              f"(SA {host[1]}), own city {d}km away")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
