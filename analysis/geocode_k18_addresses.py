# -*- coding: utf-8 -*-
"""
geocode_k18_addresses.py — geocode the K18 (2009) official polling-place
addresses (statarea_inputs/k18_ballot_addresses.json, from the CEC 2008-12-28
list) for every multi-SA-2008 locality, via Nominatim.

Adapted from geocode_k17_addresses.py with two simplifications: the source
carries official locality CODES (no name->semel bridge, no merged-municipality
table — 2009 is post-Nov-2003 mergers), and hit validation uses the in-repo
2008 geometry (data/statarea_2009_geo.json, WGS84).

Method per address (lesson #5: geocode addresses, not venue names):
  raw query -> abbreviation-expanded (שד->שדרות …) -> street-only (no number).
  Every hit is validated by distance to the locality's own 2008 polygons
  (<= ~1.5 km) — a hit elsewhere is rejected (Haifa lesson: bad points are
  worse than no points). A 'retry' arg adds looser passes for the misses
  (neighborhood-strip, no-countrycode, bare-city for unnumbered addresses).

Cache: statarea_inputs/k18_address_geocodes.json, written incrementally —
re-running skips resolved keys, so the job is resumable.

Run: python -X utf8 analysis/geocode_k18_addresses.py [retry]
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict

from shapely.geometry import Point, shape
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAP = os.path.join(HERE, "statarea_inputs")
GEO08 = os.path.join(ROOT, "data", "statarea_2009_geo.json")
ADDRS = os.path.join(SNAP, "k18_ballot_addresses.json")
CACHE = os.path.join(SNAP, "k18_address_geocodes.json")
UA = "election-dashboard-research/1.0 (academic; ym2705@nyu.edu)"
MAX_KM = 1.5
DEG = MAX_KM / 111.0  # ~deg per km (lat); fine at Israel's latitude for a sanity radius


def clean_addr(a):
    return " ".join((a or "").split())


def expand(a):
    """Common CEC abbreviations that break OSM lookup."""
    a = re.sub(r"^שד'? ", "שדרות ", a)
    a = re.sub(r"^רח'? ", "", a)
    a = re.sub(r"^רחוב ", "", a)
    a = re.sub(r"^ככר ", "כיכר ", a)
    a = re.sub(r"^ק\.? ?", "קרית ", a) if a.startswith("ק.") else a
    # this list writes 'street,num' with no space — normalize for OSM
    a = re.sub(r",(\S)", r", \1", a)
    return a


def street_only(a):
    s = re.sub(r"\s*,?\s*\d+[א-ת]?\s*$", "", a).strip().rstrip(",")
    return s if s and s != a else None


def hood_strip(a):
    """'שכ אלמלסא' / 'שכונת עין איברהים' -> bare neighborhood name (common in
    Arab-town address fields, where the 'address' is the neighborhood)."""
    s = re.sub(r"^שכ(ונת)?'? ", "", a).strip()
    return s if s and s != a else None


def query_nominatim(q, cc=True):
    params = {"q": q, "format": "json", "limit": 3}
    if cc:
        # NB: countrycodes=il drops West Bank hits (tagged ps) — the retry
        # pass queries without it; polygon-distance validation is the guard.
        params["countrycodes"] = "il"
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)
        except Exception:
            if attempt == 2:
                return None
            time.sleep(5 * (attempt + 1))
    return None


def main():
    # --- 2008 locality polygons (dissolved per semel) for hit validation ---
    print("loading 2008 geometry...", flush=True)
    g = json.load(open(GEO08, encoding="utf-8"))
    polys = defaultdict(list)
    sa_count = defaultdict(int)
    name_of = {}
    for f in g["features"]:
        p = f["properties"]
        sm = p.get("semel")
        if sm is None:
            continue
        sm = int(sm)
        geom = shape(f["geometry"])
        if not geom.is_valid:
            geom = geom.buffer(0)
        polys[sm].append(geom)
        sa_count[sm] += 1
        name_of.setdefault(sm, " ".join(str(p.get("name") or "").replace(" -", "-").split()))
    union = {sm: unary_union(gs) for sm, gs in polys.items()}

    # --- worklist: unique (semel, address) in multi-SA-2008 localities ---
    addrs = json.load(open(ADDRS, encoding="utf-8"))
    work = {}   # key "semel|addr" -> {"targets": [(semel, query_city)], "addr": str}
    no_poly = defaultdict(int)
    for sem, bmap in addrs.items():
        smi = int(sem)
        if smi not in union:
            no_poly[sem] += len(bmap)
            continue
        if sa_count.get(smi, 0) <= 1:
            continue  # single-SA locality: no coordinate needed
        city = name_of.get(smi) or ""
        for addr in set(clean_addr(a) for a in bmap.values() if clean_addr(a)):
            work.setdefault(f"{smi}|{addr}", {"targets": [(smi, city)], "addr": addr})
    if no_poly:
        print(f"localities absent from the 2008 layer (skipped): {len(no_poly)} "
              f"({sum(no_poly.values())} kalpiot)")
    print(f"worklist: {len(work)} unique (semel, address) pairs", flush=True)

    cache = {}
    if os.path.exists(CACHE):
        cache = json.load(open(CACHE, encoding="utf-8"))
    retry = "retry" in sys.argv[1:]
    if retry:
        todo = [k for k in work if cache.get(k, {}).get("src") == "none"]
    else:
        todo = [k for k in work if k not in cache]
    print(f"cached: {len(cache)}, to geocode: {len(todo)}{' (retry misses)' if retry else ''}", flush=True)

    def try_q(addr_variant, city, targets, cc=True):
        """Query; accept a hit if it sits within DEG of the semel's polygons.
        Returns (lat, lng, matched_semel) or None."""
        q = f"{addr_variant}, {city}, ישראל" if addr_variant else f"{city}, ישראל"
        d = query_nominatim(q, cc=cc)
        time.sleep(1.05)
        if not d:
            return None
        for hit in d:
            lat, lng = float(hit["lat"]), float(hit["lon"])
            pt = Point(lng, lat)
            for sm, _ in targets:
                u = union.get(sm)
                if u is not None and u.distance(pt) <= DEG:
                    return lat, lng, sm
        return None

    n_hit = n_miss = 0
    for i, key in enumerate(todo):
        w = work[key]
        addr = w["addr"]
        res = None
        for _, city in w["targets"]:
            ladder = [(addr, "raw", True), (expand(addr), "expanded", True),
                      (street_only(addr), "street", True)]
            if retry:
                ladder += [(hood_strip(addr), "hood", True),
                           (addr, "raw_nocc", False),
                           (street_only(addr) or hood_strip(addr), "soft_nocc", False)]
                if not re.search(r"\d", addr):
                    ladder.append((None, "city", True))
            seen = set()
            for variant, src, cc in ladder:
                vkey = (variant, cc)
                if (src != "raw" and variant == addr and cc) or vkey in seen:
                    continue
                if variant is None and src != "city":
                    continue
                seen.add(vkey)
                ll = try_q(variant, city, w["targets"], cc=cc)
                if ll:
                    res = {"lat": ll[0], "lng": ll[1], "semel": ll[2], "src": src}
                    break
            if res:
                break
        # failed retries are marked distinctly so an interrupted retry pass
        # never re-burns the full ladder on the same address when resumed
        cache[key] = res or {"src": "none_retried" if retry else "none"}
        n_hit += bool(res)
        n_miss += not res
        if (i + 1) % 25 == 0 or i == len(todo) - 1:
            json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
            print(f"  {i+1}/{len(todo)}  hits {n_hit}  misses {n_miss}", flush=True)

    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    hits = sum(1 for v in cache.values() if v.get("src") != "none")
    print(f"done: {hits}/{len(cache)} geocoded ({100*hits/len(cache):.1f}%) -> {os.path.basename(CACHE)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
