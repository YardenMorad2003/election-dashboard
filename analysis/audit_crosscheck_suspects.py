# -*- coding: utf-8 -*-
"""
audit_crosscheck_suspects.py — MOE-registry audit of the K17-crosscheck
suspects (the profile-SILENT mis-geocode class; see SESSION_CHALLENGES §18).

Scope: suspects whose venue string is still alive in K21–K25 (user call
2026-07-06: "ok to miss 2015 and prior — I just want to miss less").

Verdict cascade per suspect (evidence bar = the Magen case):
  CONFIRM  — an in-city MOE registry candidate (accuracy גבוהה+) sits ≤0.6 km
             from the 2006-address alt cluster AND the current map coordinate
             is ≥1.5 km away → two independent period-true sources agree the
             venue is at the alt. Fix = the registry coordinate.
  CLEARED  — a registry candidate sits ≤0.3 km from the CURRENT coordinate →
             the flag is 2006→2009 renumbering noise (Goldstein-Goren class).
  MANUAL   — no registry name match in-city / registry agrees with neither.

Prints the audit + writes analysis/statarea_inputs/crosscheck_audit.json with
the CONFIRM list ready to merge into station_coord_fixes.json.

Run AFTER crosscheck_cain_vs_k17.py (needs crosscheck_suspects.json):
    python -X utf8 analysis/audit_crosscheck_suspects.py
"""
import json, os, sys, math, urllib.request, urllib.parse, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAP = os.path.join(HERE, "statarea_inputs")
EM = r"C:\Users\yarde\elections-merge\data"
sys.path.insert(0, HERE)
from build_venue_dots import norm  # noqa: E402

UA = {"User-Agent": "datagov-external-client"}
MOE_RESOURCE = "5c5d6bb0-755d-470d-84b6-d7dd3135ba9c"
MOE_CACHE = os.path.join(SNAP, "moe_registry_cache.json")
GOOD_ACC = ("גבוהה מאוד", "גבוהה")
# tokens that carry no identity — never require them to match
GENERIC = {"בית", "ספר", "ביס", "ביהס", "בי", "ס", "יסודי", "תיכון", "ממלכתי",
           "ממד", "עש", "מקיף", "חדש", "ישן", "לשעבר", "כניסה", "ראשית", "אולם", "ספורט"}


def dist_km(a, b):
    dy = (a[0] - b[0]) * 111.32
    dx = (a[1] - b[1]) * 111.32 * 0.845
    return math.hypot(dx, dy)


def load_registry():
    if os.path.exists(MOE_CACHE):
        return json.load(open(MOE_CACHE, encoding="utf-8"))
    rows, offset = [], 0
    while True:
        q = urllib.parse.urlencode({"resource_id": MOE_RESOURCE, "limit": 32000, "offset": offset})
        req = urllib.request.Request(f"https://data.gov.il/api/3/action/datastore_search?{q}", headers=UA)
        res = json.load(urllib.request.urlopen(req, timeout=120))["result"]
        rows.extend(res["records"])
        offset += len(res["records"])
        if offset >= res.get("total", 0) or not res["records"]:
            break
    slim = [{"name": str(r.get("SHEM_MOSAD") or ""), "sem_mosad": r.get("SEMEL_MOSAD"),
             "lat": r.get("UTM_Y"), "lng": r.get("UTM_X"),   # misnamed: WGS84
             "acc": str(r.get("RAMAT_DIYUK_MIKUM") or "")}
            for r in rows]
    json.dump(slim, open(MOE_CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    return slim


def pip(lng, lat, ring):
    ins = False; j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]; xj, yj = ring[j][0], ring[j][1]
        if (yi > lat) != (yj > lat) and lng < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            ins = not ins
        j = i
    return ins


def city_polys():
    """semel(str) -> list of outer rings from both slim geos."""
    out = collections.defaultdict(list)
    for gname in ("statarea_2022_geo.json", "statarea_2009_geo.json"):
        geo = json.load(open(os.path.join(ROOT, "data", gname), encoding="utf-8"))
        for f in geo["features"]:
            g = f["geometry"]
            polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
            for rings in polys:
                out[str(f["properties"]["semel"])].append(rings[0])
    return out


def in_city(lat, lng, rings):
    return any(pip(lng, lat, r) for r in rings)


def main():
    suspects = json.load(open(os.path.join(SNAP, "crosscheck_suspects.json"), encoding="utf-8"))
    registry = load_registry()
    print(f"suspects: {len(suspects)}; registry rows: {len(registry):,}")

    # modern-alive venue strings + their current (fixes-applied) coordinates
    alive = {}     # (semel, norm_venue) -> [eras]
    for yr in ("21", "22", "23", "24", "25"):
        bl = json.load(open(os.path.join(EM, f"ballot_locations_{yr}.json"), encoding="utf-8"))
        for key, ven in (bl.get("ballot_to_location") or {}).items():
            sm = key.split(":")[0]
            if not ven:
                continue
            lst = alive.setdefault((sm, norm(ven)), [])
            if yr not in lst:
                lst.append(yr)
    cur = {}       # (semel, norm_venue) -> (lat, lng) from the newest dots file that has it
    for yr in ("25", "24", "23", "22", "21"):
        vd = json.load(open(os.path.join(ROOT, "data", f"venue_dots_k{yr}.json"), encoding="utf-8"))["venues"]
        for v in vd:
            cur.setdefault((str(v[8]), norm(v[7] or "")), (v[0], v[1]))

    polys = city_polys()

    # registry index by normed tokens
    reg_normed = [(r, norm(r["name"]).split()) for r in registry
                  if r["lat"] and r["lng"] and r["acc"] in GOOD_ACC]

    confirms, cleared, manual, dead = [], [], [], []
    for s in suspects:
        sm, ven, alt = str(s["semel"]), s["venue"], tuple(s["alt"])
        key = (sm, norm(ven))
        eras = alive.get(key)
        if not eras:
            dead.append(s)
            continue
        cur_ll = cur.get(key)
        toks = [t for t in norm(ven).split() if t not in GENERIC]
        cands = []
        if toks:
            rings = polys.get(sm, [])
            for r, rtoks in reg_normed:
                if all(t in rtoks for t in toks) and in_city(float(r["lat"]), float(r["lng"]), rings):
                    ll = (float(r["lat"]), float(r["lng"]))
                    cands.append((dist_km(ll, alt), dist_km(ll, cur_ll) if cur_ll else 99, r, ll))
        cands.sort(key=lambda c: c[0])
        s2 = dict(s, eras=eras, cur=cur_ll, n_cands=len(cands))
        if cands and cands[0][0] <= 0.6 and (not cur_ll or dist_km(cands[0][3], cur_ll) >= 1.5):
            r, ll = cands[0][2], cands[0][3]
            confirms.append(dict(s2, fix=[round(ll[0], 6), round(ll[1], 6)],
                                 reg_name=r["name"], sem_mosad=r["sem_mosad"], acc=r["acc"],
                                 d_alt=round(cands[0][0], 2)))
        elif cands and cur_ll and min(dist_km(c[3], cur_ll) for c in cands) <= 0.3:
            confirming = min(cands, key=lambda c: dist_km(c[3], cur_ll))
            cleared.append(dict(s2, reg_name=confirming[2]["name"],
                                d_cur=round(dist_km(confirming[3], cur_ll), 2)))
        else:
            manual.append(s2)

    print(f"\nalive in K21-25: {len(suspects)-len(dead)} | dead strings (skipped per scope): {len(dead)}")
    print(f"CONFIRMED: {len(confirms)} | CLEARED (renumbering FP): {len(cleared)} | MANUAL: {len(manual)}\n")
    for c in confirms:
        print(f"CONFIRM  {c['semel']:>5} {c['venue'][:34]!r:36} -> ({c['fix'][0]:.5f},{c['fix'][1]:.5f}) "
              f"reg={c['reg_name'][:22]!r} acc={c['acc']} d_alt={c['d_alt']}km "
              f"med={c['med_km']}km k={c['kosher']} eras={','.join(c['eras'])}")
    for c in cleared:
        print(f"cleared  {c['semel']:>5} {c['venue'][:34]!r:36} reg {c['reg_name'][:22]!r} "
              f"{c['d_cur']}km from current")
    for c in manual:
        print(f"manual   {c['semel']:>5} {c['venue'][:34]!r:36} cands={c['n_cands']} "
              f"med={c['med_km']}km k={c['kosher']} alt=({c['alt'][0]:.4f},{c['alt'][1]:.4f})")

    json.dump({"confirms": confirms, "cleared": cleared, "manual": manual,
               "dead_skipped": len(dead)},
              open(os.path.join(SNAP, "crosscheck_audit.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\nwrote {os.path.join(SNAP, 'crosscheck_audit.json')}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
