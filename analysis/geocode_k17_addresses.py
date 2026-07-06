# -*- coding: utf-8 -*-
"""
geocode_k17_addresses.py — geocode the K17 (2006) ballot CSV's contemporaneous
כתובת (address) column for every multi-SA-1995 locality, via Nominatim.

Why: ballot_locations_16/17 are back-propagated from the modern venue master and
collapse this far back (SESSION_CHALLENGES.md §8). The K17 CSV itself carries a
period-true street address for 99.8% of votes — geocoding ~2k unique addresses
once gives coordinates for BOTH K17 (directly) and K16 (via the 96.6%-exact
ballot-number join, since K16 predates the Nov-2003 municipal mergers).

Method per address (lesson #5: geocode addresses, not venue names):
  raw query -> abbreviation-expanded (שד->שדרות …) -> street-only (no number).
  Every hit is validated by distance to the locality's own 1995 polygons
  (<= ~1.5 km) — a hit elsewhere is rejected (Haifa lesson: bad points are
  worse than no points).

Cache: statarea_inputs/k17_address_geocodes.json, written incrementally —
re-running skips resolved keys, so the job is resumable.

Run: python -X utf8 analysis/geocode_k17_addresses.py
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
SNAP = os.path.join(HERE, "statarea_inputs")
EM = r"C:\Users\yarde\elections-merge\data"
GEO95 = r"C:\Users\yarde\Downloads\statistical_areas_1995.geojson"
CACHE = os.path.join(SNAP, "k17_address_geocodes.json")
UA = "election-dashboard-research/1.0 (academic; ym2705@nyu.edu)"
GERESH = "'׳״‘’“”\"`"
MAX_KM = 1.5
DEG = MAX_KM / 111.0  # ~deg per km (lat); fine at Israel's latitude for a sanity radius

# K17 merged-municipality names (Nov-2003 mergers) -> constituent 1995 semels
# with modern query spellings. Resolved against the 1995 geojson's own names.
MERGED = {
    "מודיעין מכבים רעו": [(1200, "מודיעין"), (1273, "מכבים רעות")],
    "יהוד נוה אפרים": [(9400, "יהוד"), (1062, "נווה מונוסון")],
    "שגור": [(516, "מג'ד אל-כרום"), (490, "דיר אל-אסד"), (483, "בענה")],
    "באקה גת": [(6000, "באקה אל-גרביה"), (628, "ג'ת")],
    "עיר כרמל": [(494, "דלית אל-כרמל"), (534, "עספיא")],
    "צורן קדימה": [(195, "קדימה"), (1308, "צורן")],
    "בנימינה גבעת עדה": [(9800, "בנימינה"), (50, "גבעת עדה")],
    # 1996 mergers (already merged in BOTH K16 and K17, unlike the 2003 ones):
    "בסמה": [(639, "ברטעה"), (643, "מועאוויה"), (657, "עין א-סהלה")],
    "מעלה עירון": [(640, "זלפה"), (645, "מושיירפה"), (644, "סאלם"), (934, "ביאדה")],
    # קצר א-סר: not in the 1995 layer (recognized later) — unmappable, reported.
}


def norm(s):
    if not s:
        return ""
    for ch in GERESH:
        s = s.replace(ch, "")
    s = re.sub(r"[()\-,./\\:;+]", " ", s)
    return " ".join(s.replace("יי", "י").replace("וו", "ו").split())


def clean_addr(a):
    return " ".join((a or "").split())


def expand(a):
    """Common CEC abbreviations that break OSM lookup."""
    a = re.sub(r"^שד'? ", "שדרות ", a)
    a = re.sub(r"^רח'? ", "", a)
    a = re.sub(r"^רחוב ", "", a)
    a = re.sub(r"^ככר ", "כיכר ", a)
    a = re.sub(r"^ק\.? ?", "קרית ", a) if a.startswith("ק.") else a
    return a


def street_only(a):
    s = re.sub(r"\s*\d+[א-ת]?\s*$", "", a).strip()
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
    # --- locality polygons (dissolved per semel) for hit validation ---
    print("loading 1995 geometry...", flush=True)
    g = json.load(open(GEO95, encoding="utf-8"))
    polys = defaultdict(list)
    sa_count = defaultdict(int)
    for f in g["features"]:
        p = f["properties"]
        try:
            sm = int(p["CITY"])
        except (ValueError, TypeError, KeyError):
            continue
        geom = shape(f["geometry"])
        if not geom.is_valid:
            geom = geom.buffer(0)
        polys[sm].append(geom)
        sa_count[sm] += 1
    union = {sm: unary_union(gs) for sm, gs in polys.items()}

    # --- name -> semel bridge (era-true K16 first, K25 fallback) ---
    name2sem = {}
    for r in csv.DictReader(open(rf"{EM}\knesset25_ballots.csv", encoding="utf-8-sig")):
        name2sem.setdefault(norm(r["שם ישוב"]), r["סמל ישוב"].strip())
    for r in csv.DictReader(open(rf"{EM}\knesset16_ballots.csv", encoding="utf-8-sig")):
        try:
            sm = str(int(float(r["סמל ישוב"])))
        except (ValueError, TypeError):
            continue
        if sm != "0":
            name2sem[norm(r["שם ישוב"])] = sm
    sfix = os.path.join(SNAP, "settlement_name_fixes_18.json")
    if os.path.exists(sfix):
        for nm, sm in json.load(open(sfix, encoding="utf-8")).items():
            name2sem[norm(nm)] = str(sm)

    # --- worklist: unique (semel-or-mergedset, address) needing coords ---
    rows = [r for r in csv.DictReader(open(rf"{EM}\knesset17_ballots.csv", encoding="utf-8-sig"))
            if r["שם ישוב"].strip() != "מעטפות כפולות"]
    work = {}   # key "semel|addr" -> {"targets": [(semel, query_city)], "addr": str}
    unmapped = defaultdict(int)
    for r in rows:
        nm = norm(r["שם ישוב"])
        addr = clean_addr(r["כתובת"])
        if not addr:
            continue
        if nm in MERGED:
            targets = MERGED[nm]
            if sum(sa_count.get(sm, 0) for sm, _ in targets) <= 1:
                continue
        else:
            sm = name2sem.get(nm)
            if not sm:
                unmapped[r["שם ישוב"].strip()] += 1
                continue
            smi = int(sm)
            if sa_count.get(smi, 0) <= 1:
                continue  # single-SA locality: no coordinate needed
            targets = [(smi, r["שם ישוב"].strip())]
        key = f"{targets[0][0]}|{addr}"
        work.setdefault(key, {"targets": targets, "addr": addr})
    if unmapped:
        print(f"unmapped locality names (skipped): {dict(unmapped)}")
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
        """Query; accept a hit if it sits within DEG of ANY target semel's
        polygons (merged constituents are adjacent — a hit may correctly land
        in a sibling's polygon). Returns (lat, lng, matched_semel) or None."""
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
                if not re.search(r"\d", addr) or norm(addr) == norm(city):
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
        cache[key] = res or {"src": "none"}
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
