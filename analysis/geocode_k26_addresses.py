# -*- coding: utf-8 -*-
"""
geocode_k26_addresses.py — geocode the K26 polling sites that make_k26_ballot_coords.py
could not inherit from the K25 layer (new sites / new addresses), multi-SA settlements only.

Nominatim (OSM), 1 request/sec, generic client name. A hit is accepted only if it
falls inside the settlement's own 2022 stat-area polygons (or within MAX_KM of them).
Variants tried in order: full address -> street only -> venue name.

Cache: statarea_inputs/k26_address_geocodes.json
  {"semel|addr|venue": {"lat":..,"lng":..,"src":"addr|street|venue"} | {"src":"none"}}
Re-run is incremental; `retry` re-queries the misses.

Run: python -X utf8 analysis/geocode_k26_addresses.py
"""
import csv
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
CACHE = os.path.join(SNAP, "k26_address_geocodes.json")
UA = "election-map-research/1.0"
MAX_KM = 0.3
DEG = MAX_KM / 111.0


def expand(a):
    a = " ".join((a or "").split())
    a = re.sub(r"^שד'? ", "שדרות ", a)
    a = re.sub(r"^רח'? ", "", a)
    a = re.sub(r"^רחוב ", "", a)
    a = re.sub(r"^ככר ", "כיכר ", a)
    a = re.sub(r",(\S)", r" \1", a)          # 'street,num' -> 'street num'
    return a.strip(" ,")


def street_only(a):
    s = re.sub(r"\s*,?\s*\d+[א-ת]?\s*$", "", a).strip().rstrip(",")
    return s if s and s != a else None


def query(q):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": q, "format": "json", "limit": 40})
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
    g = json.load(open(os.path.join(ROOT, "data", "statarea_2022_geo.json"), encoding="utf-8"))
    polys, name_of = defaultdict(list), {}
    for f in g["features"]:
        sm = int(f["properties"]["semel"])
        geom = shape(f["geometry"])
        polys[sm].append(geom if geom.is_valid else geom.buffer(0))
        name_of.setdefault(sm, f["properties"].get("name") or "")
    union = {sm: unary_union(gs) for sm, gs in polys.items() if len(gs) > 1}

    _p = os.path.join(SNAP, "k26_geocode_extra.json")
    EXTRA = set(json.load(open(_p, encoding="utf-8"))) if os.path.exists(_p) else set()
    work = {}
    with open(os.path.join(SNAP, "k26_ballot_coords.csv"), encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            # weak inherited tiers are geocoded too, so the official address can be
            # triangulated against the inherited point (audit 2026-11-21); extra suspects
            # (semel|addr|venue keys) come from k26_geocode_extra.json
            if r["coord_src"] not in ("none", "geocode", "geocode_street", "geocode_venue",
                                      "geocode_street_mid", "k25_rikuz", "k25_fuzzy", "k25_addr_amb", "moe", "addr_geocode")                     and f"{r['semel']}|{r['addr']}|{r['venue']}" not in EXTRA:
                continue
            sm = int(r["semel"])
            if sm not in union:
                continue
            work[f"{sm}|{r['addr']}|{r['venue']}"] = (sm, r["sett"], r["addr"], r["venue"])
    cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
    retry = "retry" in sys.argv[1:]
    # refresh: re-query hits recorded before precision (kind/spread) was stored
    refresh = "refresh" in sys.argv[1:]
    todo = [k for k in work if (k not in cache) or (retry and cache[k].get("src") == "none")
            or (refresh and cache[k].get("src") != "none" and "spread" not in cache[k])]
    print(f"worklist {len(work)}, cached {len(cache)}, to geocode {len(todo)}", flush=True)

    def attempt(q, sm):
        d = query(q)
        time.sleep(1.05)
        # LESSON (Kiryat Ata, רוגוזין ב on דרך יצחק רבין, 2026-11-21): OSM rarely has Israeli house
        # numbers, so "street 16, city" usually returns ONE SEGMENT of the street (class highway),
        # anywhere along it. A long road can put the site kilometres off. So: collect every
        # in-city segment, record how far apart they are (spread_km) and return the middle one;
        # the consumer treats a large spread as "not located".
        ok = []
        for hit in d or []:
            lat, lng = float(hit["lat"]), float(hit["lon"])
            if union[sm].distance(Point(lng, lat)) <= DEG:
                ok.append((lat, lng, f"{hit.get('class','')}/{hit.get('type','')}/{hit.get('addresstype','')}"))
        if not ok:
            return None
        if not ok[0][2].startswith("highway"):
            return ok[0][0], ok[0][1], ok[0][2], 0.0
        seg = [h for h in ok if h[2].startswith("highway")]
        la = [h[0] for h in seg]; ln = [h[1] for h in seg]
        spread = ((max(la) - min(la)) * 111.0) ** 2 + ((max(ln) - min(ln)) * 94.0) ** 2
        cla, cln = sum(la) / len(la), sum(ln) / len(ln)
        mid = min(seg, key=lambda h: (h[0] - cla) ** 2 + (h[1] - cln) ** 2)
        return mid[0], mid[1], mid[2], round(spread ** 0.5, 2)

    for i, k in enumerate(todo, 1):
        sm, sett, addr, venue = work[k]
        city = sett or name_of.get(sm, "")
        a = expand(addr)
        res = None
        if a and a != expand(city):
            hit = attempt(f"{a}, {city}", sm)
            if hit:
                res = {"lat": hit[0], "lng": hit[1], "src": "addr" if re.search(r"\d", a) else "street", "kind": hit[2], "spread": hit[3]}
            else:
                so = street_only(a)
                if so:
                    hit = attempt(f"{so}, {city}", sm)
                    if hit:
                        res = {"lat": hit[0], "lng": hit[1], "src": "street", "kind": hit[2], "spread": hit[3]}
        if res is None and venue:
            hit = attempt(f"{venue}, {city}", sm)
            if hit:
                res = {"lat": hit[0], "lng": hit[1], "src": "venue", "kind": hit[2], "spread": hit[3]}
        cache[k] = res or {"src": "none"}
        if i % 20 == 0 or i == len(todo):
            json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
            c = defaultdict(int)
            for kk in work:
                c[cache.get(kk, {}).get("src", "todo")] += 1
            print(f"{i}/{len(todo)} {dict(c)}", flush=True)


if __name__ == "__main__":
    main()
