# -*- coding: utf-8 -*-
"""
resolve_sweep_tier2.py — tier-2 pass over the official-sweep MANUAL flags:
trust the official CEC address alone when its geocode is HOUSE-NUMBER-PRECISE.

Rationale (user question 2026-07-06: "aren't the addresses in the file?"):
the official address is authoritative; the risk in tier-1 was geocoder error.
If Nominatim resolves the EXACT house number requested (result carries a
matching house_number), the geocode is building-level and the address alone
suffices — no registry needed. Street/suburb-level results stay manual.

Verdict per manual flag:
  CONFIRM — geocode (addressdetails) returns matching house_number, in-city
            PIP, and the current coordinate is >=1.5 km away → fix = geocode.
  else    — stays manual (no house number in the address, imprecise geocode,
            or geocode agrees with current after all).

Writes statarea_inputs/k25_tier2.json; prints the verdicts. Does not modify
the fixes file — merge after review of the printout.
Run: python -X utf8 analysis/resolve_sweep_tier2.py
"""
import json, os, re, sys, time, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAP = os.path.join(HERE, "statarea_inputs")
sys.path.insert(0, HERE)
from audit_crosscheck_suspects import city_polys, in_city, dist_km  # noqa: E402


def geocode_precise(addr, city):
    """returns (lat, lng, matched_house) or None; queries with addressdetails."""
    street = " ".join((addr or "").replace(",", " ").split())
    q = f"{street}, {city}, ישראל"
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": q, "format": "json", "limit": 1, "addressdetails": 1})
    req = urllib.request.Request(url, headers={"User-Agent": "election-dashboard-audit/1.0"})
    try:
        res = json.load(urllib.request.urlopen(req, timeout=30))
    except Exception:
        res = []
    time.sleep(1.1)
    if not res:
        return None
    r = res[0]
    house = (r.get("address") or {}).get("house_number", "")
    return float(r["lat"]), float(r["lon"]), house


def main():
    sw = json.load(open(os.path.join(SNAP, "k25_official_sweep.json"), encoding="utf-8"))
    manual = [f for f in sw["flags"] if f["verdict"] == "manual"]
    polys = city_polys()
    confirms, stay = [], []
    for i, f in enumerate(manual, 1):
        addr = f["addr22"]
        mm = re.search(r"[,\s](\d+)\s*[א-ת]?\s*$", addr)
        want = mm.group(1) if mm else None
        if not want:
            stay.append(dict(f, why="no house number in address"))
            continue
        g = geocode_precise(addr, f["city"])
        if i % 25 == 0:
            print(f"  ...{i}/{len(manual)}", flush=True)
        if not g:
            stay.append(dict(f, why="geocode failed"))
            continue
        lat, lng, house = g
        if not house or re.sub(r"\D", "", house) != want:
            stay.append(dict(f, why=f"geocode imprecise (house={house!r} want {want})"))
            continue
        if not in_city(lat, lng, polys.get(str(f["semel"]), [])):
            stay.append(dict(f, why="precise geocode out of city"))
            continue
        d_cur = dist_km((lat, lng), tuple(f["cur"]))
        if d_cur < 1.5:
            stay.append(dict(f, why=f"precise geocode only {d_cur:.2f}km from current"))
            continue
        confirms.append(dict(f, fix=[round(lat, 6), round(lng, 6)], house=house,
                             d_cur=round(d_cur, 2)))

    print(f"\nTIER-2: house-precise CONFIRMS: {len(confirms)} | stay manual: {len(stay)}\n")
    for c in confirms:
        print(f"CONFIRM  {c['city'][:12]:<12} {c['venue'][:32]!r:34} k={c['valid']:>5} "
              f"addr={c['addr22'][:24]!r} house={c['house']} d={c['d_cur']}km")
    reasons = {}
    for s in stay:
        key = s["why"].split(" (")[0]
        reasons[key] = reasons.get(key, 0) + 1
    print("\nstay-manual reasons:", reasons)
    json.dump({"confirms": confirms, "stay": stay},
              open(os.path.join(SNAP, "k25_tier2.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"wrote {os.path.join(SNAP, 'k25_tier2.json')}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
