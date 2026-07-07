# -*- coding: utf-8 -*-
"""
resolve_sa_mismatch.py — the sub-1.5km placement class (user report 2026-07-06:
Or-Yehuda גן דקל sits on רחוב דקל instead of official כצנלסון 18 — 0.96 km off,
different stat-area, invisible to the 1.5 km sweep threshold).

For every K25 venue with an official street address (majority over its ballots)
and a cached geocode: PIP the CURRENT map coordinate and the OFFICIAL-address
geocode into the 2022 SA polygons. Where they land in different SAs of the same
city, escalate exactly like the sweep ladder:

  tier-2 (house): re-geocode with addressdetails; if Nominatim returns the
     EXACT requested house number (and the road shares a token with the
     official street), the address alone suffices → CONFIRM, fix = geocode.
  tier-3 (street): no house number / imprecise result → fetch the street
     geometry; if >=80% of its vertices PIP into exactly ONE SA:
       == current SA → SAME_SA (point imprecise, SA right — cleared);
       != current SA → CONFIRM, fix = median in-SA street vertex.
  else → manual.

Exclusions: venues with an existing name-keyed fix (evidence-verified by hand —
never auto-overridden; listed for review) and multi-address venue names (the
merge class — handled by station_coord_fixes_k25_addr.json).

Writes statarea_inputs/sa_mismatch_resolve.json. Does NOT modify fixes.
Run: python -X utf8 analysis/resolve_sa_mismatch.py
"""
import json, os, re, sys, time, math, collections, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAP = os.path.join(HERE, "statarea_inputs")
EM = r"C:\Users\yarde\elections-merge\data"
GEOJSON = r"C:\Users\yarde\Downloads\statistical_areas_2022.geojson"
sys.path.insert(0, HERE)
from build_venue_dots import norm, canon_ballot  # noqa: E402
from resolve_sweep_tier3 import street_vertices  # noqa: E402

UA = {"User-Agent": "election-dashboard-audit/1.0"}
CTOKS = {"רח", "רחוב", "שד", "שדרות", "דרך"}


def dist_km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 2*6371*math.asin(math.sqrt(h))


def street_tokens(addr):
    s = norm(re.sub(r"[\d,]+", " ", addr or ""))
    return set(s.split()) - CTOKS


def geocode_precise(addr, city):
    street = " ".join((addr or "").replace(",", " ").split())
    street = re.sub(r"^שד['׳]?\s+", "שדרות ", street)
    street = re.sub(r"^רח['׳]?\s+", "", street)
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": f"{street}, {city}, ישראל", "format": "json", "limit": 1, "addressdetails": 1})
    req = urllib.request.Request(url, headers=UA)
    try:
        res = json.load(urllib.request.urlopen(req, timeout=30))
    except Exception:
        res = []
    time.sleep(1.1)
    if not res:
        return None
    r = res[0]
    a = r.get("address") or {}
    return float(r["lat"]), float(r["lon"]), a.get("house_number", ""), a.get("road", "")


def main():
    dots = json.load(open(os.path.join(ROOT, "data", "venue_dots_k25.json"), encoding="utf-8"))["venues"]
    cache = json.load(open(os.path.join(SNAP, "k25_address_geocodes.json"), encoding="utf-8"))
    addr25 = json.load(open(os.path.join(SNAP, "k25_ballot_addresses.json"), encoding="utf-8"))
    bl25 = json.load(open(os.path.join(EM, "ballot_locations_25.json"), encoding="utf-8"))["ballot_to_location"]
    cityname = {}
    for r in json.load(open(os.path.join(ROOT, "data", "localities.json"), encoding="utf-8")):
        if r.get("semel"):
            cityname[str(r["semel"])] = r.get("name", "")
    fixed_keys = set()
    for sem, vmap in json.load(open(os.path.join(SNAP, "station_coord_fixes.json"), encoding="utf-8")).items():
        if sem.startswith("_"):
            continue
        for ven in vmap:
            fixed_keys.add((str(sem), norm(ven)))

    ven_ballots = collections.defaultdict(list)
    for key, ven in bl25.items():
        sm, b = key.split(":", 1)
        if ven:
            ven_ballots[(sm, norm(ven))].append(canon_ballot(b))

    # ---- full-country PIP
    from shapely.geometry import shape, Point
    from shapely.strtree import STRtree
    print("loading 2022 geojson (126MB)...", flush=True)
    g = json.load(open(GEOJSON, encoding="utf-8"))
    geoms, sids = [], []
    for f in g["features"]:
        p = f["properties"]
        if p.get("YISHUV_STAT_2022") is None:
            continue
        geom = shape(f["geometry"])
        if not geom.is_valid:
            geom = geom.buffer(0)
        geoms.append(geom)
        sids.append(int(p["YISHUV_STAT_2022"]))
    tree = STRtree(geoms)
    print(f"  polygons: {len(geoms)}", flush=True)

    def pip(lat, lng):
        if lat is None:
            return None
        for i in tree.query(Point(lng, lat), predicate="intersects"):
            return sids[int(i)]
        return None

    # ---- candidates
    cands, skip_fix, skip_merged = [], [], 0
    for v in sorted(dots, key=lambda x: -x[2]):
        sm, name_, cur, valid = str(v[8]), v[7] or "", (v[0], v[1]), v[2]
        nkey = (sm, norm(name_))
        balls = ven_ballots.get(nkey, [])
        baddrs = [addr25.get(sm, {}).get(b) for b in balls]
        baddrs = [a for a in baddrs if a]
        if not baddrs:
            continue
        if len(set(baddrs)) > 1:
            skip_merged += 1
            continue
        addr = baddrs[0]
        ctoks = set(norm(cityname.get(sm, "")).split())
        st = street_tokens(addr)
        if not st or st <= ctoks:
            continue
        gc = cache.get(f"{cityname.get(sm, '')}|{addr}")
        if not gc:
            continue
        sa_cur, sa_geo = pip(*cur), pip(gc[0], gc[1])
        if sa_cur is None or sa_geo is None or sa_cur == sa_geo:
            continue
        if sa_cur // 10000 != sa_geo // 10000:
            continue          # cross-city geocode: tier-1 sweep territory
        if nkey in fixed_keys:
            skip_fix.append({"semel": sm, "city": cityname.get(sm, sm), "venue": name_,
                             "addr": addr, "valid": valid, "sa_cur": sa_cur, "sa_geo": sa_geo,
                             "d_km": round(dist_km(cur, tuple(gc)), 2)})
            continue
        cands.append((sm, name_, addr, cur, valid, sa_cur, sa_geo, tuple(gc)))
    print(f"SA-mismatch candidates: {len(cands)} | skipped: {len(skip_fix)} has-fix, "
          f"{skip_merged} multi-address (merge class)", flush=True)

    # ---- escalate
    confirms, same_sa, manual = [], [], []
    for i, (sm, name_, addr, cur, valid, sa_cur, sa_geo, gc) in enumerate(cands, 1):
        city = cityname.get(sm, "")
        rec = {"semel": sm, "city": city, "venue": name_, "addr": addr, "valid": valid,
               "cur": [round(cur[0], 6), round(cur[1], 6)], "sa_cur": sa_cur}
        if i % 25 == 0:
            print(f"  ...{i}/{len(cands)} (confirms {len(confirms)}, same-SA {len(same_sa)}, "
                  f"manual {len(manual)})", flush=True)
        mm = re.search(r"[,\s](\d+)\s*[א-ת]?\s*$", addr)
        want = mm.group(1) if mm else None
        done = False
        if want:                                   # tier-2: exact house number
            pg = geocode_precise(addr, city)
            if pg:
                la, ln, house, road = pg
                road_ok = (not road) or (street_tokens(addr) & set(norm(road).split()))
                sa_p = pip(la, ln)
                if house and re.sub(r"\D", "", house) == want and road_ok and sa_p is not None \
                        and sa_p // 10000 == sa_cur // 10000:
                    if sa_p != sa_cur:
                        confirms.append(dict(rec, fix=[round(la, 6), round(ln, 6)], sa=sa_p,
                                             how="house", d_km=round(dist_km(cur, (la, ln)), 2)))
                    else:
                        same_sa.append(dict(rec, sa=sa_p, how="house-agrees"))
                    done = True
        if not done:                               # tier-3: single-SA street
            street, verts = street_vertices(addr, city)
            if verts:
                assigns = [pip(y, x) for x, y in verts]
                inside = [a for a in assigns if a is not None and a // 10000 == sa_cur // 10000]
                if inside and len(inside) >= 0.8 * len([a for a in assigns if a is not None]) \
                        and len(set(inside)) == 1:
                    sid = inside[0]
                    if sid == sa_cur:
                        same_sa.append(dict(rec, sa=sid, how="street-agrees"))
                    else:
                        in_verts = [v for v, a in zip(verts, assigns) if a == sid]
                        vx, vy = in_verts[len(in_verts) // 2]
                        confirms.append(dict(rec, fix=[round(vy, 6), round(vx, 6)], sa=sid,
                                             how="street", d_km=round(dist_km(cur, (vy, vx)), 2)))
                    done = True
        if not done:
            manual.append(dict(rec, sa_geo=sa_geo))

    print(f"\nRESOLVE: confirms {len(confirms)} | same-SA cleared {len(same_sa)} | "
          f"manual {len(manual)} | has-fix skipped {len(skip_fix)}")
    for c in confirms:
        print(f"CONFIRM[{c['how']:6}] {c['city'][:14]:<14} {c['venue'][:32]!r:34} k={c['valid']:>5} "
              f"d={c['d_km']:>5}km SA {c['sa_cur']} -> {c['sa']} addr={c['addr'][:24]!r}")
    json.dump({"confirms": confirms, "same_sa": same_sa, "manual": manual, "has_fix": skip_fix},
              open(os.path.join(SNAP, "sa_mismatch_resolve.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"wrote {os.path.join(SNAP, 'sa_mismatch_resolve.json')}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
