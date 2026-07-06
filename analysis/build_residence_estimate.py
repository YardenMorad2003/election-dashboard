# -*- coding: utf-8 -*-
"""
build_residence_estimate.py — the residence-estimate layer ("אומדן מגורים"):
a modeled answer to "how did each stat-area's RESIDENTS vote," vs the actual
layer's "which votes were CAST inside the SA".

Model (RESIDENCE_ESTIMATE_HANDOFF.md §3): assume each resident votes at the
nearest polling venue of their own city; distribute every venue's actual votes
back over the SAs it serves, in proportion to the population it serves there.
City totals stay exact by construction (closure asserted per city).

  data/statarea_estimate_k{18..25}.json
  {"meta": {...holdout_mae_rh...}, "areas": {sid: {valid_est, winner, blocs,
   parties, n_donors}}}

K16/K17 are skipped in v1: no census population exists on the 1995 geometry.

Run: python -X utf8 analysis/build_residence_estimate.py [18 19 ...]
"""
import json, os, sys, math, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_venue_dots as bvd   # venue aggregation + coordinate resolution

ROOT = bvd.ROOT
DATA = os.path.join(ROOT, "data")

# geometry / distance constants (same convention as the page + interp mode)
KX = 0.845                 # lng -> lat-equivalent degrees at Israel's latitude
DEG_KM = 111.32            # km per degree latitude
PITCH0 = 0.100 / DEG_KM    # ~100 m grid pitch, in lat-degrees
MIN_SAMPLES = 30           # refine pitch until an SA has at least this many
MIN_PITCH = 0.013 / DEG_KM # ...but never finer than ~13 m
MAX_CAND = 4000            # coarsen huge (rural) SAs to ~this many candidates
MAX_KEEP = 800             # thin accepted samples beyond this (memory hygiene)
MAXD2 = (3.0 / DEG_KM) ** 2  # samples >3 km from every venue stay unassigned

ERAS = {
    "18": ("statarea_2009.json", "statarea_2009_geo.json"),
    "19": ("statarea_k19.json",  "statarea_2009_geo.json"),
    "20": ("statarea_k20.json",  "statarea_2009_geo.json"),
    "21": ("statarea_k21.json",  "statarea_2022_geo.json"),
    "22": ("statarea_k22.json",  "statarea_2022_geo.json"),
    "23": ("statarea_k23.json",  "statarea_2022_geo.json"),
    "24": ("statarea_k24.json",  "statarea_2022_geo.json"),
    "25": ("statarea_2022.json", "statarea_2022_geo.json"),
}

DATIYUT_ORD = {"חילוני": 0, "מסורתי": 1, "דתי/ דתי מאוד": 2, "חרדי": 3}


# ---- geometry ------------------------------------------------------------
def polys_of(geom):
    """GeoJSON geometry -> list of polygons, each a list of rings [outer, holes...]."""
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    if geom["type"] == "MultiPolygon":
        return list(geom["coordinates"])
    return []


def pip(lng, lat, ring):
    """ray-casting point-in-ring; ring = [[lng,lat], ...]"""
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > lat) != (yj > lat) and lng < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def point_in_polys(lng, lat, polys):
    for rings in polys:
        if pip(lng, lat, rings[0]) and not any(pip(lng, lat, h) for h in rings[1:]):
            return True
    return False


def sample_polygon(geom):
    """Deterministic grid sample of an SA polygon -> [(lat, lng), ...].
    ~100 m pitch, refined ×2 for tiny SAs, coarsened for huge rural ones."""
    polys = polys_of(geom)
    if not polys:
        return []
    xs, ys = [], []
    for rings in polys:
        for x, y in rings[0]:
            xs.append(x); ys.append(y)
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)

    pitch = PITCH0
    est = ((maxy - miny) / pitch + 1) * ((maxx - minx) / (pitch / KX) + 1)
    if est > MAX_CAND:
        pitch *= math.sqrt(est / MAX_CAND)

    pts = []
    while True:
        pts = []
        step_x = pitch / KX
        lat = miny + pitch / 2
        while lat < maxy:
            lng = minx + step_x / 2
            while lng < maxx:
                if point_in_polys(lng, lat, polys):
                    pts.append((lat, lng))
                lng += step_x
            lat += pitch
        if len(pts) >= MIN_SAMPLES or pitch <= MIN_PITCH:
            break
        pitch /= 2.0

    if not pts:
        # degenerate sliver: fall back to the outer ring's vertex mean, else a vertex
        ring = max((r[0] for r in polys), key=len)
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)
        if not point_in_polys(cx, cy, polys):
            cx, cy = ring[0][0], ring[0][1]
        pts = [(cy, cx)]
    if len(pts) > MAX_KEEP:
        stride = -(-len(pts) // MAX_KEEP)
        pts = pts[::stride]
    return pts


def sample_geometry(geo_name, cache):
    """cache[geo_name] = {sid_str: {"pts": [(lat,lng)...], "sem": str, "polys": polys}}"""
    if geo_name in cache:
        return cache[geo_name]
    geo = json.load(open(os.path.join(DATA, geo_name), encoding="utf-8"))
    out = {}
    for f in geo["features"]:
        pr = f["properties"]
        polys = polys_of(f["geometry"])
        xs = [x for rings in polys for x, _ in rings[0]]
        ys = [y for rings in polys for _, y in rings[0]]
        out[str(pr["id"])] = {"pts": sample_polygon(f["geometry"]),
                              "sem": str(pr["semel"]),
                              "polys": polys,
                              "bbox": (min(xs), min(ys), max(xs), max(ys)) if xs else None}
    cache[geo_name] = out
    print(f"  sampled {geo_name}: {len(out)} SAs, "
          f"{sum(len(v['pts']) for v in out.values()):,} sample points")
    return out


# ---- math helpers ----------------------------------------------------------
def nearest_venue(lat, lng, venues, skip=None):
    """index of nearest venue (equirectangular, KX lng scaling), None if >3 km."""
    best, bd = None, MAXD2
    for k, v in enumerate(venues):
        if skip and k in skip:
            continue
        dx = (lng - v["lng"]) * KX
        dy = lat - v["lat"]
        d2 = dx * dx + dy * dy
        if d2 < bd:
            best, bd = k, d2
    return best


def pearson(pairs):
    n = len(pairs)
    if n < 3:
        return None
    sx = sum(p[0] for p in pairs); sy = sum(p[1] for p in pairs)
    mx, my = sx / n, sy / n
    cov = sum((x - mx) * (y - my) for x, y in pairs)
    vx = sum((x - mx) ** 2 for x, _ in pairs)
    vy = sum((y - my) ** 2 for _, y in pairs)
    if vx == 0 or vy == 0:
        return None
    return cov / math.sqrt(vx * vy)


# ---- per-era build ---------------------------------------------------------
def build_year(yr, geo_cache):
    layer_name, geo_name = ERAS[yr]
    layer = json.load(open(os.path.join(DATA, layer_name), encoding="utf-8"))["areas"]
    sas = sample_geometry(geo_name, geo_cache)

    pn = bvd.PN[yr]
    bloc_of = {p["code"]: p.get("bloc") for p in pn["party_list"]}
    bloc_names = sorted({b for b in bloc_of.values() if b})
    rh_blocs = ("right", "haredi")

    vlist, tot_votes, dropped = bvd.collect_venues(yr)
    placed = sum(v["valid"] for v in vlist)
    ven_by_sem = collections.defaultdict(list)
    for v in vlist:
        rh_share = sum(c for p, c in v["pv"].items() if bloc_of.get(p) in rh_blocs) / v["valid"]
        ven_by_sem[v["sem"]].append({"lat": v["lat"], "lng": v["lng"], "valid": v["valid"],
                                     "pv": v["pv"], "rh": rh_share, "name": v["name"]})

    # populated, sampled SAs per city
    city_sas = collections.defaultdict(list)   # sem -> [sid]
    pop = {}
    for sid, s in sas.items():
        rec = layer.get(sid)
        p = ((rec or {}).get("census") or {}).get("pop") or 0
        if p > 0 and s["pts"]:
            pop[sid] = p
            city_sas[s["sem"]].append(sid)

    areas_out = {}
    distributed = 0.0
    undistributed_novenuepop = 0.0   # venues serving no population, no containing SA
    holdout_deltas = []
    cities_done = 0

    for sem, venues in ven_by_sem.items():
        sids = city_sas.get(sem)
        if not sids:
            continue
        cities_done += 1

        # assignment: every sample -> nearest venue of its own city
        assign = {}   # sid -> {venue_idx: n_samples}; also keep per-sid sample count
        P = collections.defaultdict(dict)   # P[sid][k] = pop-persons of sid served by venue k
        D = [0.0] * len(venues)             # D[k] = total persons served by venue k
        for sid in sids:
            cnt = collections.Counter()
            pts = sas[sid]["pts"]
            for (lat, lng) in pts:
                k = nearest_venue(lat, lng, venues)
                if k is not None:
                    cnt[k] += 1
            assign[sid] = cnt
            for k, n in cnt.items():
                pik = pop[sid] * n / len(pts)
                P[sid][k] = pik
                D[k] += pik

        # interior venue(s) per SA — for the D==0 fallback and the hold-out
        interior = collections.defaultdict(list)   # sid -> [venue_idx]
        for k, v in enumerate(venues):
            for sid in sids:
                bb = sas[sid]["bbox"]
                if not bb or not (bb[0] <= v["lng"] <= bb[2] and bb[1] <= v["lat"] <= bb[3]):
                    continue
                if point_in_polys(v["lng"], v["lat"], sas[sid]["polys"]):
                    interior[sid].append(k)
                    break

        # closure-exact distribution
        est = {sid: {"votes": 0.0, "pv": collections.defaultdict(float), "donors": []}
               for sid in sids}
        city_valid = 0.0
        for k, v in enumerate(venues):
            if D[k] > 0:
                city_valid += v["valid"]
                continue
            # venue serves no sampled population: attach to its containing populated SA
            host = next((sid for sid in sids if k in interior[sid]), None)
            if host is None:
                undistributed_novenuepop += v["valid"]
            else:
                e = est[host]
                e["votes"] += v["valid"]
                for p, c in v["pv"].items():
                    e["pv"][p] += c
                e["donors"].append(k)
                city_valid += v["valid"]
        for sid in sids:
            e = est[sid]
            for k, pik in P[sid].items():
                if D[k] <= 0:
                    continue
                r = venues[k]["valid"] * pik / D[k]
                e["votes"] += r
                for p, c in venues[k]["pv"].items():
                    e["pv"][p] += r * c / venues[k]["valid"]
                if r >= 1.0:
                    e["donors"].append(k)

        city_est = sum(e["votes"] for e in est.values())
        assert abs(city_est - city_valid) < 1.0, \
            f"closure broke: semel {sem} est {city_est:.2f} vs valid {city_valid:.2f}"
        distributed += city_est

        # hold-one-out: SAs with ground truth (voted) and an interior venue
        for sid in sids:
            exc = set(interior[sid])
            if not exc or len(exc) >= len(venues):
                continue
            truth = layer.get(sid) or {}
            if not truth.get("valid") or not truth.get("blocs"):
                continue
            pts = sas[sid]["pts"]
            cnt = collections.Counter()
            for (lat, lng) in pts:
                k = nearest_venue(lat, lng, venues, skip=exc)
                if k is not None:
                    cnt[k] += 1
            num = den = 0.0
            for k, n in cnt.items():
                pik = pop[sid] * n / len(pts)
                dk = D[k] - P[sid].get(k, 0.0) + pik
                if dk <= 0:
                    continue
                r = venues[k]["valid"] * pik / dk
                num += r * venues[k]["rh"]
                den += r
            if den > 0:
                holdout_deltas.append(abs(100 * num / den - truth["blocs"]["rh"]))

        # emit records
        for sid in sids:
            e = est[sid]
            if e["votes"] < 0.5:
                continue
            tot = e["votes"]
            pcts = {p: 100 * c / tot for p, c in e["pv"].items()}
            blocs = {b: 0.0 for b in bloc_names}
            other = 0.0
            for p, pc in pcts.items():
                b = bloc_of.get(p)
                if b:
                    blocs[b] += pc
                else:
                    other += pc
            rh = blocs.get("right", 0) + blocs.get("haredi", 0)
            cla = sum(v for b, v in blocs.items() if b not in rh_blocs)
            out_blocs = {b: round(v, 1) for b, v in blocs.items()}
            out_blocs["rh"] = round(rh, 1)
            out_blocs["cla"] = round(cla, 1)
            out_blocs["other"] = round(other, 1)
            top = sorted(pcts.items(), key=lambda kv: -kv[1])[:8]
            areas_out[sid] = {
                "valid_est": int(round(tot)),
                "winner": top[0][0],
                "blocs": out_blocs,
                "parties": {p: round(pc, 1) for p, pc in top if pc >= 0.1},
                "n_donors": len(set(e["donors"])),
            }

    # coherence: est-rh should track the census religiosity BETTER than actual-rh
    # — compared on the SAME voted∩estimated SA set (different sets mislead)
    pairs_act, pairs_est = [], []
    for sid, rec in layer.items():
        if not (rec.get("valid") and rec.get("blocs") and sid in areas_out):
            continue
        c = rec.get("census") or {}
        if yr in ("18", "19", "20"):
            x = (c.get("religion") or {}).get("arab")
            if x is None:
                continue
            x = -x   # flip so both eras expect a POSITIVE corr with rh
        else:
            if c.get("religion") != "יהודים":
                continue
            x = DATIYUT_ORD.get(c.get("datiyut"))
            if x is None:
                continue
        pairs_act.append((x, rec["blocs"]["rh"]))
        pairs_est.append((x, areas_out[sid]["blocs"]["rh"]))
    corr_act, corr_est = pearson(pairs_act), pearson(pairs_est)

    holdout_deltas.sort()
    n_h = len(holdout_deltas)
    med = holdout_deltas[n_h // 2] if n_h else None
    mae = sum(holdout_deltas) / n_h if n_h else None

    meta = {"knesset": int(yr),
            "votes_total": tot_votes,
            "votes_placed": placed,
            "votes_distributed": int(round(distributed)),
            "coverage_pct": round(100 * distributed / tot_votes, 1),
            "cities": cities_done,
            "areas": len(areas_out),
            "holdout_mae_rh": round(mae, 1) if mae is not None else None,
            "holdout_median_rh": round(med, 1) if med is not None else None,
            "holdout_n": n_h,
            "built": "2026-07-06"}
    path = os.path.join(DATA, f"statarea_estimate_k{yr}.json")
    json.dump({"meta": meta, "areas": areas_out}, open(path, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))

    print(f"K{yr}: {len(areas_out):,} SAs estimated in {cities_done} cities | "
          f"distributed {distributed:,.0f}/{tot_votes:,} ({meta['coverage_pct']}%), "
          f"undistributable-venue votes {undistributed_novenuepop:,.0f} | "
          f"hold-out |Δrh| median {med:.1f} mean {mae:.1f} (n={n_h}) | "
          f"coherence corr(rh, religiosity) actual {corr_act:.3f} -> est {corr_est:.3f} | "
          f"{os.path.basename(path)} ({os.path.getsize(path)//1024} KB)")


if __name__ == "__main__":
    years = sys.argv[1:] or list(ERAS.keys())
    cache = {}
    for yr in years:
        build_year(yr, cache)
