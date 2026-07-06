# -*- coding: utf-8 -*-
"""Feasibility v2: K18 coordinate inheritance with bridge fix + split recovery.

Adds over v1: collapse יי/וו in normalization (station file uses collapsed
spellings), bridge via Cain's b25 settlement names too, recover missing K18
venues via K19/K25 same-key or N->N.1 split lookup, and classify
centroid-quality matches by the locality's SA count in the 2008 layer.
"""
import csv
import glob
import json
import re
from collections import defaultdict

DATA = r"C:\Users\yarde\elections-merge\data"
SHP = glob.glob(r"C:\Users\yarde\Downloads\statistical_areas_2008\*\*_1335.shp")[0]

GERESH = "'׳״‘’“”\"`"

def norm(s):
    if not s:
        return ""
    for ch in GERESH:
        s = s.replace(ch, "")
    s = re.sub(r"[()\-,./\\:;+]", " ", s)
    s = s.replace("יי", "י").replace("וו", "ו")
    return " ".join(s.split())

def jacc(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

def canon_ballot(bal):
    try:
        f = float(bal)
        return str(int(f)) if f == int(f) else bal
    except ValueError:
        return bal

# ---- load ----
b18 = json.load(open(rf"{DATA}\ballot_locations_18.json", encoding="utf-8"))
b19 = json.load(open(rf"{DATA}\ballot_locations_19.json", encoding="utf-8"))
b25 = json.load(open(rf"{DATA}\ballot_locations_25.json", encoding="utf-8"))
sc = json.load(open(rf"{DATA}\station_coordinates.json", encoding="utf-8"))
stations = sc["stations"]

l18, l19 = b18["ballot_to_location"], b19["ballot_to_location"]
l25 = {}
for semel, s in b25["settlements"].items():
    for b in s["ballots"]:
        l25[f"{semel}:{b['ballot']}"] = b["location"]

with open(rf"{DATA}\knesset18_ballots.csv", encoding="utf-8-sig") as fh:
    r18 = list(csv.DictReader(fh))
with open(rf"{DATA}\knesset25_ballots.csv", encoding="utf-8-sig") as fh:
    r25 = list(csv.DictReader(fh))

# ---- SA counts per semel from the 2008 layer ----
import shapefile
sf = shapefile.Reader(SHP, encoding="cp1255")
sa_count = defaultdict(int)
for rec in sf.iterRecords(fields=["SEMEL_YISH", "STAT08"]):
    if rec["SEMEL_YISH"] and rec["SEMEL_YISH"] > 0:
        sa_count[str(rec["SEMEL_YISH"])] += 1

# ---- bridge: normalized settlement name -> semel (csv + Cain b25 names) ----
name_to_semel = {}
for row in r25:
    name_to_semel[norm(row["שם ישוב"])] = row["סמל ישוב"].strip()
for semel, s in b25["settlements"].items():
    name_to_semel.setdefault(norm(s["name"]), semel)

venues_by_semel = defaultdict(dict)  # semel -> {norm_venue: precise_bool}
unmapped = set()
for st in stations.values():
    semel = name_to_semel.get(norm(st["settlement"]))
    if semel is None:
        unmapped.add(st["settlement"])
        continue
    v = norm(st.get("location") or "")
    if not v:
        continue
    precise = st.get("source") in ("venue", "google_venue", "manual", "manual_correction") \
        and st.get("lat") is not None
    if precise or v not in venues_by_semel[semel]:
        venues_by_semel[semel][v] = precise or venues_by_semel[semel].get(v, False)

print(f"station settlements still unmapped: {len(unmapped)}")
if unmapped:
    print("  ", " | ".join(sorted(unmapped)[:12]))

# ---- classify every geographic K18 ballot ----
counts, votes = defaultdict(int), defaultdict(int)
mopup = defaultdict(int)  # semel -> votes needing geocoding
total_votes = geo_votes = 0

for row in r18:
    semel = row["סמל ישוב"].strip()
    kosher = int(row["כשרים"] or 0)
    total_votes += kosher
    if semel == "0":
        votes["double_envelope"] += kosher
        counts["double_envelope"] += 1
        continue
    geo_votes += kosher
    b = canon_ballot(row["סמל קלפי"].strip())
    k = f"{semel}:{b}"
    venue = l18.get(k) or l19.get(k) or l25.get(k) or l25.get(k + ".1") or l19.get(k + ".1")
    single_sa = sa_count.get(semel, 0) <= 1
    if not venue:
        cat = "noname_single_sa" if single_sa else "noname_multi_sa"
        counts[cat] += 1
        votes[cat] += kosher
        if not single_sa:
            mopup[semel] += kosher
        continue
    vv = venues_by_semel.get(semel)
    nv = norm(venue)
    hit = vv.get(nv) if vv else None
    if hit is None and vv:
        tv = set(nv.split())
        best, best_j = None, 0.0
        for cand in vv:
            j = jacc(tv, set(cand.split()))
            if j > best_j:
                best, best_j = cand, j
        if best_j >= 0.5:
            hit = vv[best]
    if hit is True:
        counts["precise"] += 1
        votes["precise"] += kosher
    elif hit is False or vv is None:
        cat = "centroid_single_sa" if single_sa else "centroid_multi_sa"
        counts[cat] += 1
        votes[cat] += kosher
        if not single_sa:
            mopup[semel] += kosher
    else:
        cat = "nomatch_single_sa" if single_sa else "nomatch_multi_sa"
        counts[cat] += 1
        votes[cat] += kosher
        if not single_sa:
            mopup[semel] += kosher

print(f"\ntotal valid votes {total_votes:,}; geographic {geo_votes:,} "
      f"(double envelopes {votes['double_envelope']:,} excluded by design)")
print(f"{'category':20s} {'ballots':>8s} {'votes':>10s} {'%geo':>7s}")
order = ["precise", "centroid_single_sa", "noname_single_sa", "nomatch_single_sa",
         "centroid_multi_sa", "noname_multi_sa", "nomatch_multi_sa"]
ok = 0
for cat in order:
    pct = votes[cat] / geo_votes
    print(f"{cat:20s} {counts[cat]:8d} {votes[cat]:10,d} {pct:7.1%}")
    if cat in ("precise", "centroid_single_sa", "noname_single_sa", "nomatch_single_sa"):
        ok += votes[cat]
print(f"\nusable without any geocoding (precise or single-SA locality): {ok:,} = {ok/geo_votes:.1%} of geo votes")

sett18 = b18["settlements"]
print("\nTop-15 mop-up localities (multi-SA, needs geocoding):")
for semel, v in sorted(mopup.items(), key=lambda kv: -kv[1])[:15]:
    print(f"  {semel:6s} {sett18.get(semel, '?'):26s} {v:8,d}  SAs={sa_count.get(semel, 0)}")
print(f"mop-up total: {sum(mopup.values()):,} votes in {len(mopup)} localities")
