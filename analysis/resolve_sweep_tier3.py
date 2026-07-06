# -*- coding: utf-8 -*-
"""
resolve_sweep_tier3.py — street-geometry pass over what tier-2 left manual
(user insight 2026-07-06: "even a street-only address — most likely that
street lies inside a single statistical area").

For each remaining flag: fetch the street's GEOMETRY from Nominatim
(polygon_geojson=1, all highway-class results of that name in-city), drop its
vertices into the city's 2022-geo SA polygons, and:
  CONFIRM   — >=80% of vertices land in SAs and ALL in exactly ONE SA, which
              differs from the current coordinate's SA → the street pins the
              SA uniquely; fix = the median street vertex inside that SA.
  SAME_SA   — the street's single SA == the current coordinate's SA → the
              placement is imprecise but the SA (all that matters for the
              layers) is right; flag cleared for map purposes.
  manual    — street spans multiple SAs / no street geometry found.

Reads statarea_inputs/k25_tier2.json; writes k25_tier3.json. No fixes-file
changes here — merge after review.
Run: python -X utf8 analysis/resolve_sweep_tier3.py
"""
import json, os, re, sys, time, urllib.request, urllib.parse, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAP = os.path.join(HERE, "statarea_inputs")
sys.path.insert(0, HERE)
from build_residence_estimate import polys_of, point_in_polys  # noqa: E402


def sa_polys_by_semel():
    """semel(str) -> [(sid, polys, bbox)] from the 2022 slim geo (K25 flags)."""
    geo = json.load(open(os.path.join(ROOT, "data", "statarea_2022_geo.json"), encoding="utf-8"))
    out = collections.defaultdict(list)
    for f in geo["features"]:
        pr = f["properties"]
        polys = polys_of(f["geometry"])
        xs = [x for rings in polys for x, _ in rings[0]]
        ys = [y for rings in polys for _, y in rings[0]]
        out[str(pr["semel"])].append((pr["id"], polys, (min(xs), min(ys), max(xs), max(ys))))
    return out


def sa_at(lng, lat, city_sas):
    for sid, polys, bb in city_sas:
        if bb[0] <= lng <= bb[2] and bb[1] <= lat <= bb[3] and point_in_polys(lng, lat, polys):
            return sid
    return None


def street_vertices(addr, city):
    street = re.sub(r"[,\s]*\d+\s*[א-ת]?\s*$", "", (addr or "").replace(",", " ")).strip()
    if not street:
        return None, []
    q = f"{street}, {city}, ישראל"
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": q, "format": "json", "limit": 5, "polygon_geojson": 1})
    req = urllib.request.Request(url, headers={"User-Agent": "election-dashboard-audit/1.0"})
    try:
        res = json.load(urllib.request.urlopen(req, timeout=30))
    except Exception:
        res = []
    time.sleep(1.1)
    verts = []
    for r in res:
        if r.get("class") != "highway":
            continue
        g = r.get("geojson") or {}
        if g.get("type") == "LineString":
            verts.extend(g["coordinates"])
        elif g.get("type") == "MultiLineString":
            for seg in g["coordinates"]:
                verts.extend(seg)
    return street, verts


def main():
    t2 = json.load(open(os.path.join(SNAP, "k25_tier2.json"), encoding="utf-8"))
    stay = t2["stay"]
    city_polys = sa_polys_by_semel()
    confirms, same_sa, manual = [], [], []
    for i, f in enumerate(stay, 1):
        sem = str(f["semel"])
        cs = city_polys.get(sem, [])
        street, verts = street_vertices(f["addr22"], f["city"])
        if i % 20 == 0:
            print(f"  ...{i}/{len(stay)}", flush=True)
        if not verts:
            manual.append(dict(f, why3="no street geometry"))
            continue
        assigns = [sa_at(x, y, cs) for x, y in verts]
        inside = [a for a in assigns if a]
        if not inside or len(inside) < 0.8 * len(assigns):
            manual.append(dict(f, why3=f"street mostly outside SA coverage ({len(inside)}/{len(assigns)})"))
            continue
        sids = set(inside)
        if len(sids) != 1:
            manual.append(dict(f, why3=f"street spans {len(sids)} SAs"))
            continue
        sid = inside[0]
        cur_sid = sa_at(f["cur"][1], f["cur"][0], cs)
        if cur_sid == sid:
            same_sa.append(dict(f, sa=sid, why3="street's single SA == current SA"))
            continue
        # fix = median in-SA vertex
        in_verts = [v for v, a in zip(verts, assigns) if a == sid]
        vx, vy = in_verts[len(in_verts) // 2]
        confirms.append(dict(f, fix=[round(vy, 6), round(vx, 6)], sa=sid,
                             cur_sa=cur_sid, street=street))

    print(f"\nTIER-3: single-SA-street CONFIRMS: {len(confirms)} | "
          f"same-SA cleared: {len(same_sa)} | manual: {len(manual)}\n")
    for c in confirms:
        print(f"CONFIRM  {c['city'][:12]:<12} {c['venue'][:30]!r:32} k={c['valid']:>5} "
              f"street={c['street'][:18]!r} SA {c['cur_sa']} -> {c['sa']}")
    for c in same_sa:
        print(f"same-SA  {c['city'][:12]:<12} {c['venue'][:30]!r:32} SA {c['sa']} (point imprecise, SA right)")
    reasons = collections.Counter(m["why3"].split(" (")[0] for m in manual)
    print("\nmanual reasons:", dict(reasons))
    json.dump({"confirms": confirms, "same_sa": same_sa, "manual": manual},
              open(os.path.join(SNAP, "k25_tier3.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"wrote {os.path.join(SNAP, 'k25_tier3.json')}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
