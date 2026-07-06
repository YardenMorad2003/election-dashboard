# -*- coding: utf-8 -*-
"""
sweep_k25_official.py — FULL modern-era sweep: every K25 venue's current map
coordinate vs the Nominatim geocode of its OFFICIAL CEC address
(kalpiplaces_kalpieslist_27-10.xlsx). The only systematic check that reaches
post-2006 venues.

Per venue (semel × norm(name), coords from venue_dots_k25):
  - official address = majority over its ballots in the xlsx;
  - city-only addresses are exempt (a town name anchors nothing — §20);
  - geocode via resumable cache statarea_inputs/k25_address_geocodes.json,
    rejected unless it PIPs into the venue's own city;
  - |current − geocode| > 1.5 km → FLAG, annotated with any in-city MOE
    registry name-match: registry ≤0.3 km from the geocode = two independent
    sources agree → auto-confirmable; registry ≤0.3 km from CURRENT = the
    geocode is probably the bad guy (street-name collision) → cleared.

Writes statarea_inputs/k25_official_sweep.json. Does NOT modify fixes.
Queue is sorted by venue votes (big venues geocode first; safe to interrupt).

Run: python -X utf8 analysis/sweep_k25_official.py
"""
import json, os, sys, re, time, collections, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAP = os.path.join(HERE, "statarea_inputs")
EM = r"C:\Users\yarde\elections-merge\data"
XLSX = r"C:\Users\yarde\Downloads\kalpiplaces_kalpieslist_27-10.xlsx"
GEOCACHE = os.path.join(SNAP, "k25_address_geocodes.json")
sys.path.insert(0, HERE)
from build_venue_dots import norm, canon_ballot  # noqa: E402
from audit_crosscheck_suspects import city_polys, in_city, dist_km, GENERIC  # noqa: E402

MOE_CACHE = os.path.join(SNAP, "moe_registry_cache.json")
GOOD_ACC = ("גבוהה מאוד", "גבוהה")


def street_tokens(addr):
    s = norm(re.sub(r"[\d,]+", " ", addr or ""))
    return set(s.split()) - {"רח", "רחוב", "שד", "שדרות", "דרך"}


def main():
    import openpyxl
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    official = {}
    for row in wb["DataSheet"].iter_rows(min_row=2, values_only=True):
        official[(str(row[2]), canon_ballot(row[4]))] = ((row[6] or "").strip(), (row[7] or "").strip())

    bl25 = json.load(open(os.path.join(EM, "ballot_locations_25.json"), encoding="utf-8"))["ballot_to_location"]
    ven_ballots = collections.defaultdict(list)
    for key, ven in bl25.items():
        sm, b = key.split(":", 1)
        if ven:
            ven_ballots[(sm, norm(ven))].append(canon_ballot(b))

    dots = json.load(open(os.path.join(ROOT, "data", "venue_dots_k25.json"), encoding="utf-8"))["venues"]
    cityname = {}
    for r in json.load(open(os.path.join(ROOT, "data", "localities.json"), encoding="utf-8")):
        if r.get("semel"):
            cityname[str(r["semel"])] = r.get("name", "")
    polys = city_polys()
    registry = json.load(open(MOE_CACHE, encoding="utf-8"))
    reg_normed = [(r, norm(r["name"]).split()) for r in registry
                  if r["lat"] and r["lng"] and r["acc"] in GOOD_ACC]
    cache = json.load(open(GEOCACHE, encoding="utf-8")) if os.path.exists(GEOCACHE) else {}

    # build the work queue: venue -> official majority address
    queue = []
    n_cityonly = n_noaddr = 0
    for v in sorted(dots, key=lambda x: -x[2]):
        sm, name_, cur, valid = str(v[8]), v[7] or "", (v[0], v[1]), v[2]
        addrs = [official.get((sm, b)) for b in ven_ballots.get((sm, norm(name_)), [])]
        addrs = [a for a in addrs if a]
        if not addrs:
            n_noaddr += 1
            continue
        addr = collections.Counter(a[0] for a in addrs).most_common(1)[0][0]
        place = collections.Counter(a[1] for a in addrs).most_common(1)[0][0]
        ctoks = set(norm(cityname.get(sm, "")).split())
        st = street_tokens(addr)
        if not st or st <= ctoks:
            n_cityonly += 1
            continue
        queue.append((sm, name_, place, addr, cur, valid))
    uniq = {(sm, addr) for sm, _, _, addr, _, _ in queue}
    todo = [k for k in ({f"{cityname.get(sm,'')}|{addr}" for sm, addr in uniq}) if k not in cache]
    print(f"venues: {len(dots):,} | with official street address: {len(queue):,} "
          f"(city-only exempt: {n_cityonly:,}, no-xlsx-entry: {n_noaddr:,}) | "
          f"unique addresses: {len(uniq):,} | to geocode: {len(todo):,}", flush=True)

    def geocode(addr, city):
        key = f"{city}|{addr}"
        if key in cache:
            return cache[key] and tuple(cache[key])
        street = " ".join((addr or "").replace(",", " ").split())
        url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
            {"q": f"{street}, {city}, ישראל", "format": "json", "limit": 1})
        req = urllib.request.Request(url, headers={"User-Agent": "election-dashboard-audit/1.0"})
        try:
            res = json.load(urllib.request.urlopen(req, timeout=30))
        except Exception:
            res = []
        time.sleep(1.05)
        ll = (float(res[0]["lat"]), float(res[0]["lon"])) if res else None
        cache[key] = list(ll) if ll else None
        geocode.n += 1
        if geocode.n % 25 == 0:
            json.dump(cache, open(GEOCACHE, "w", encoding="utf-8"), ensure_ascii=False)
            print(f"  geocoded {geocode.n:,}/{len(todo):,}...", flush=True)
        return ll
    geocode.n = 0

    flags, agree, rejected, failed = [], 0, 0, 0
    for sm, name_, place, addr, cur, valid in queue:
        ll = geocode(addr, cityname.get(sm, ""))
        if not ll:
            failed += 1
            continue
        if not in_city(ll[0], ll[1], polys.get(sm, [])):
            rejected += 1
            continue
        d = dist_km(cur, ll)
        if d <= 1.5:
            agree += 1
            continue
        # registry cross-ref (name tokens of the OFFICIAL place name)
        toks = [t for t in norm(place).split() if t not in GENERIC]
        verdict, reg_name = "manual", ""
        if toks:
            best_d = 9e9
            for r, rtoks in reg_normed:
                if all(t in rtoks for t in toks):
                    rll = (float(r["lat"]), float(r["lng"]))
                    if not in_city(rll[0], rll[1], polys.get(sm, [])):
                        continue
                    dg, dc = dist_km(rll, ll), dist_km(rll, cur)
                    if dg < best_d:
                        best_d, reg_name = dg, r["name"]
                        verdict = ("confirm" if dg <= 0.3 else
                                   "cleared" if dc <= 0.3 else "manual")
        flags.append({"semel": sm, "city": cityname.get(sm, sm), "venue": name_,
                      "place22": place, "addr22": addr, "valid": valid,
                      "cur": [round(cur[0], 6), round(cur[1], 6)],
                      "geo": [round(ll[0], 6), round(ll[1], 6)],
                      "d_km": round(d, 2), "verdict": verdict, "reg": reg_name})

    json.dump(cache, open(GEOCACHE, "w", encoding="utf-8"), ensure_ascii=False)
    flags.sort(key=lambda f: -f["valid"])
    vcount = collections.Counter(f["verdict"] for f in flags)
    print(f"\nagree<=1.5km: {agree:,} | flags: {len(flags):,} ({dict(vcount)}) | "
          f"geocode failed: {failed:,} | out-of-city rejected: {rejected:,}")
    for f in flags[:60]:
        print(f"  {f['verdict']:<8} {f['city'][:12]:<12} {f['venue'][:30]!r:32} k={f['valid']:>5} "
              f"d={f['d_km']:>5}km addr={f['addr22'][:22]!r} reg={f['reg'][:18]!r}")
    json.dump({"flags": flags, "agree": agree, "failed": failed, "rejected": rejected,
               "city_only_exempt": n_cityonly},
              open(os.path.join(SNAP, "k25_official_sweep.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\nwrote {os.path.join(SNAP, 'k25_official_sweep.json')}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
