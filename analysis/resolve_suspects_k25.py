# -*- coding: utf-8 -*-
"""
resolve_suspects_k25.py — settle the crosscheck manual pile with the OFFICIAL
K25 kalpi-locations file (user-provided, CEC 27-10-2022):
  C:/Users/yarde/Downloads/kalpiplaces_kalpieslist_27-10.xlsx
  (סמל ישוב, סמל קלפי, כתובת קלפי, מקום קלפי — 11,707 ballots)

Per manual suspect (from crosscheck_audit.json):
  1. official 2022 address for its K25 ballots;
  2. same street as the official 2006 address → the venue never moved →
     CONFIRM at the 2006 cluster (two official sources 16 years apart agree);
  3. different/missing → Nominatim-geocode the 2022 address (resumable cache,
     PIP-validated into the city's SA polygons, ≤1.5 km else rejected):
     geocode ≈ alt → CONFIRM; geocode ≈ current → CLEARED (venue moved / map
     right); geocode elsewhere in-city → CONFIRM_NEW at the geocode (official
     2022 address wins for the modern map); invalid → stays manual.

Writes statarea_inputs/k25_resolution.json; does NOT touch the fixes file —
review the printout, then merge.

Run: python -X utf8 analysis/resolve_suspects_k25.py
"""
import json, os, sys, time, math, re, collections, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAP = os.path.join(HERE, "statarea_inputs")
EM = r"C:\Users\yarde\elections-merge\data"
XLSX = r"C:\Users\yarde\Downloads\kalpiplaces_kalpieslist_27-10.xlsx"
GEOCACHE = os.path.join(SNAP, "k25_address_geocodes.json")
sys.path.insert(0, HERE)
from build_venue_dots import norm, canon_ballot  # noqa: E402
from audit_crosscheck_suspects import city_polys, in_city, dist_km  # noqa: E402


def street_of(addr):
    """normalized street tokens, numbers stripped"""
    s = norm(re.sub(r"[\d,]+", " ", addr or ""))
    return set(s.split()) - {"רח", "רחוב", "שד", "שדרות", "דרך"}


def streets_match(a, b):
    ta, tb = street_of(a), street_of(b)
    if not ta or not tb:
        return False
    inter = ta & tb
    return len(inter) >= min(len(ta), len(tb)) * 0.99 or len(inter) / len(ta | tb) >= 0.6


def geocode(addr, city, cache):
    key = f"{city}|{addr}"
    if key in cache:
        return cache[key] and tuple(cache[key])
    street = " ".join((addr or "").replace(",", " ").split())
    q = f"{street}, {city}, ישראל"
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": q, "format": "json", "limit": 1})   # NO countrycodes filter (West-Bank trap)
    req = urllib.request.Request(url, headers={"User-Agent": "election-dashboard-audit/1.0"})
    try:
        res = json.load(urllib.request.urlopen(req, timeout=30))
    except Exception:
        res = []
    time.sleep(1.1)
    ll = (float(res[0]["lat"]), float(res[0]["lon"])) if res else None
    cache[key] = list(ll) if ll else None
    json.dump(cache, open(GEOCACHE, "w", encoding="utf-8"), ensure_ascii=False)
    return ll


def main():
    import openpyxl
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    ws = wb["DataSheet"]
    official = {}    # (semel, canon ballot) -> (addr, place)
    for row in ws.iter_rows(min_row=2, values_only=True):
        sem, bal, addr, place = str(row[2]), canon_ballot(row[4]), (row[6] or "").strip(), (row[7] or "").strip()
        official[(sem, bal)] = (addr, place)
    print(f"official K25 ballots: {len(official):,}")

    audit = json.load(open(os.path.join(SNAP, "crosscheck_audit.json"), encoding="utf-8"))
    cache = json.load(open(GEOCACHE, encoding="utf-8")) if os.path.exists(GEOCACHE) else {}
    polys = city_polys()
    name = {}
    for r in json.load(open(os.path.join(ROOT, "data", "localities.json"), encoding="utf-8")):
        if r.get("semel"):
            name[str(r["semel"])] = r.get("name", str(r["semel"]))

    # K25 ballots per venue string
    bl25 = json.load(open(os.path.join(EM, "ballot_locations_25.json"), encoding="utf-8"))["ballot_to_location"]
    ven_ballots = collections.defaultdict(list)
    for key, ven in bl25.items():
        sm, b = key.split(":", 1)
        if ven:
            ven_ballots[(sm, norm(ven))].append(canon_ballot(b))

    # 2006 addresses (for the same-street shortcut)
    import csv
    def iv(x):
        try: return int(float(x))
        except (ValueError, TypeError): return 0
    name2sem = {}
    for r in csv.DictReader(open(rf"{EM}\knesset16_ballots.csv", encoding="utf-8-sig")):
        sm = str(iv(r["סמל ישוב"]))
        if sm != "0":
            name2sem[norm(r["שם ישוב"])] = sm
    addr17 = {}
    for r in csv.DictReader(open(rf"{EM}\knesset17_ballots.csv", encoding="utf-8-sig")):
        sm = name2sem.get(norm(r["שם ישוב"]))
        if sm:
            addr17[(sm, iv(r["מספר קלפי"]))] = " ".join((r["כתובת"] or "").split())
    bl18 = json.load(open(rf"{EM}\ballot_locations_18.json", encoding="utf-8"))["ballot_to_location"]
    ven18 = collections.defaultdict(list)
    for key, ven in bl18.items():
        sm, b = key.split(":", 1)
        if ven:
            ven18[(sm, norm(ven))].append(b)

    def addr06(sm, ven):
        cnt = collections.Counter()
        for b in ven18.get((sm, norm(ven)), []):
            try: b10 = int(round(float(b) * 10))
            except ValueError: continue
            a = addr17.get((sm, b10))
            if a: cnt[a] += 1
        return cnt.most_common(1)[0][0] if cnt else ""

    out = {"confirm_2006": [], "confirm_new": [], "cleared": [], "still_manual": []}
    for s in audit["manual"]:
        sm, ven, alt, cur = str(s["semel"]), s["venue"], tuple(s["alt"]), s.get("cur")
        ballots = ven_ballots.get((sm, norm(ven)), [])
        offs = [official.get((sm, b)) for b in ballots]
        offs = [o for o in offs if o]
        if not offs:
            out["still_manual"].append(dict(s, why="not in K25 official file"))
            continue
        addr22 = collections.Counter(o[0] for o in offs).most_common(1)[0][0]
        place22 = collections.Counter(o[1] for o in offs).most_common(1)[0][0]
        a06 = addr06(sm, ven)
        rec = dict(s, addr22=addr22, place22=place22, addr06=a06)
        if a06 and streets_match(addr22, a06):
            out["confirm_2006"].append(dict(rec, fix=[alt[0], alt[1]],
                                            why="2022 official address == 2006 official address"))
            continue
        ll = geocode(addr22, name.get(sm, ""), cache)
        if ll and not in_city(ll[0], ll[1], polys.get(sm, [])):
            ll = None   # reject out-of-city geocodes (bad points worse than none)
        if ll and dist_km(ll, alt) <= 0.5:
            out["confirm_2006"].append(dict(rec, fix=[alt[0], alt[1]],
                                            why=f"2022-address geocode {dist_km(ll, alt):.2f}km from 2006 cluster"))
        elif ll and cur and dist_km(ll, tuple(cur)) <= 0.5:
            out["cleared"].append(dict(rec, why=f"2022-address geocode {dist_km(ll, tuple(cur)):.2f}km from current"))
        elif ll:
            out["confirm_new"].append(dict(rec, fix=[round(ll[0], 6), round(ll[1], 6)],
                                           why="official 2022 address geocodes to a third location (in-city)"))
        else:
            out["still_manual"].append(dict(rec, why="2022 address failed geocoding"))

    print(f"\nconfirm@2006-cluster: {len(out['confirm_2006'])} | confirm@new-geocode: {len(out['confirm_new'])} "
          f"| cleared: {len(out['cleared'])} | still manual: {len(out['still_manual'])}\n")
    for tag, lst in (("C06", out["confirm_2006"]), ("NEW", out["confirm_new"]),
                     ("CLR", out["cleared"]), ("MAN", out["still_manual"])):
        for r in lst:
            print(f"{tag}  {r['semel']:>5} {r['venue'][:32]!r:34} k={r['kosher']:>5} "
                  f"22addr={r.get('addr22','')[:24]!r:26} 06addr={r.get('addr06','')[:22]!r:24} {r.get('why','')[:52]}")
    json.dump(out, open(os.path.join(SNAP, "k25_resolution.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\nwrote {os.path.join(SNAP, 'k25_resolution.json')}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
