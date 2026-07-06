# -*- coding: utf-8 -*-
"""
validate_statarea_18.py — validation for the 2009 stat-area layer.

Mirrors validate_statarea_2022.py, plus a DRIFT PROBE specific to this layer
(K18 venues are back-propagated from 2019+ CEC scrapes, and some coords are
neighbor-imputed — so per-locality we report the share of votes riding on
soft coords and on renumbered/fallback ballots, to flag scrambled geography).

Inputs:
- data/statarea_2009.json                     (final layer)
- analysis/statarea_inputs/statarea_2009_counts.csv   (per-stat08 raw counts)
- analysis/statarea_inputs/ballot_stat08_18.csv       (per-ballot coord_src/place)
- data/localities.json ['18']                 (closure target)
- data/parties_national.json ['18']           (national party totals)
- elections-merge ballot_locations_18/19/25 + knesset18_ballots.csv (venue tiers)

Run: python -X utf8 analysis/validate_statarea_18.py
Report: analysis/statarea_2009_validation_report.txt
"""
import csv
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAP = os.path.join(HERE, "statarea_inputs")
EM = r"C:\Users\yarde\elections-merge\data"

out = []


def rep(s=""):
    out.append(s); print(s)


def canon(b):
    try:
        f = float(b)
        return str(int(f)) if f == int(f) else b
    except ValueError:
        return b


sa = json.load(open(os.path.join(ROOT, "data", "statarea_2009.json"), encoding="utf-8"))["areas"]
loc = json.load(open(os.path.join(ROOT, "data", "localities.json"), encoding="utf-8"))
pn = json.load(open(os.path.join(ROOT, "data", "parties_national.json"), encoding="utf-8"))["18"]
nat = pn.get("national_votes") or {}
name_of = {r.get("semel"): r["name"] for r in loc if r.get("semel")}

# rebuild per-party counts from the snapshot
with open(os.path.join(SNAP, "statarea_2009_counts.csv"), encoding="utf-8-sig") as f:
    rdr = csv.DictReader(f)
    party_cols = rdr.fieldnames[8:]
    crows = list(rdr)

# ---- 1. national coverage ----
rep("=== 1. NATIONAL COVERAGE ===")
in_valid = sum(int(r["valid"]) for r in crows)
off_total = sum(nat.values()) if nat else None
rep(f"valid votes in layer: {in_valid:,}"
    + (f" | official K18 kosher: {off_total:,} -> {100*in_valid/off_total:.2f}%" if off_total else ""))
psum = defaultdict(int)
for r in crows:
    for c in party_cols:
        psum[c] += int(r[c] or 0)
rep(f"{'party':>6} {'in layer':>10} {'official':>10} {'coverage':>9}")
skew = []
for code, offv in sorted(nat.items(), key=lambda x: -x[1])[:12]:
    got = psum.get(code, 0)
    cov = 100 * got / offv if offv else 0
    skew.append(cov)
    rep(f"{code:>6} {got:>10,} {offv:>10,} {cov:>8.1f}%")
if skew:
    rep(f"per-party coverage spread (top-12): {min(skew):.1f}%–{max(skew):.1f}% "
        f"(tight = no partisan skew in what's unmapped)")

# ---- 2. per-locality closure ----
rep("\n=== 2. PER-LOCALITY CLOSURE (SA sums vs localities.json K18) ===")
by_semel = defaultdict(int)
for v in sa.values():
    if "valid" in v:
        by_semel[v["semel"]] += v["valid"]
covs = []; over = []
for r in loc:
    e = (r.get("data") or {}).get("18"); s = r.get("semel")
    if not e or not s or s not in by_semel or not e.get("kosher_votes"):
        continue
    ratio = by_semel[s] / e["kosher_votes"]
    covs.append((ratio, r["name"], by_semel[s], e["kosher_votes"]))
    if ratio > 1.001:
        over.append((ratio, r["name"], by_semel[s], e["kosher_votes"]))
covs.sort()
tot_cap = sum(min(g, o) for _, _, g, o in covs)
tot_off = sum(o for _, _, _, o in covs)
rep(f"localities checked: {len(covs)}; overall coverage (capped): {100*tot_cap/tot_off:.2f}%")
rep(f"localities with >=99.9% mapped: {sum(1 for c in covs if c[0]>=0.999)}/{len(covs)}")
rep(f"localities OVER official (spillover in): {len(over)}")
rep(f"localities < 85%: {sum(1 for c in covs if c[0] < 0.85)}")
for ratio, name, g, o in covs[:6]:
    rep(f"   low: {100*ratio:5.1f}%  {name} ({g:,}/{o:,})")

# ---- 3. bloc math ----
rep("\n=== 3. BLOC MATH ===")
bad = sum(1 for v in sa.values() if "blocs" in v and
          abs(v["blocs"]["rh"] + v["blocs"]["cla"] + v["blocs"].get("other", 0) - 100) > 0.1)
rep(f"SAs with inconsistent rh+cla+other: {bad}/{sum(1 for v in sa.values() if 'blocs' in v)}")

# ---- 4. spot checks (resolved semels) ----
rep("\n=== 4. SPOT CHECKS (resolved semels) ===")
from collections import Counter
import statistics as st


def spot(semel, label, expect):
    recs = [v for v in sa.values() if v["semel"] == semel and "blocs" in v]
    if not recs:
        rep(f"   {label}: NO SAs ✗"); return
    win = Counter(v["winner"] for v in recs).most_common(3)
    m = {b: round(st.mean(v["blocs"][b] for v in recs), 1) for b in ("rh", "cla", "haredi", "arab")}
    rd = Counter((v.get("census") or {}).get("rel_dom") for v in recs).most_common(1)
    rep(f"   {label} (semel {semel}, {len(recs)} SAs): winners {win} | "
        f"rh={m['rh']} cla={m['cla']} haredi={m['haredi']} arab={m['arab']} | rel {rd}")
    rep(f"        expect: {expect}")


spot(6100, "Bnei Brak", "ג/שס, haredi high")
spot(3797, "Modiin Illit", "ג, haredi ~100")
spot(2710, "Umm al-Fahm", "Arab bloc ~pure, מוסלמי")
spot(5000, "Tel Aviv", "כן/Kadima lead, cla>rh, יהודי")
# a kibbutz-heavy signal: top-3 localities by 'left' among single-SA localities
left = sorted(((st.mean(v["blocs"]["left"] for v in sa.values()
              if v["semel"] == s and "blocs" in v), name_of.get(s, s), s)
              for s in by_semel if any(v["semel"] == s and "blocs" in v for v in sa.values())),
              reverse=True)[:3]
rep(f"   top-3 left-bloc localities (kibbutz sanity): "
    + "; ".join(f"{n}={v:.0f}%" for v, n, s in left))

# ---- 5. DRIFT PROBE ----
rep("\n=== 5. DRIFT PROBE (soft coords + renumbered ballots per locality) ===")
# 5a. coord_src share from ballot_stat08_18.csv
placed = defaultdict(int); soft = defaultdict(int); nsa = defaultdict(set)
tot_soft = tot_placed = 0
for r in csv.DictReader(open(os.path.join(SNAP, "ballot_stat08_18.csv"), encoding="utf-8-sig")):
    if not r["stat08"]:
        continue
    k = int(r["kosher"]); semel = r["semel"]
    placed[semel] += k; tot_placed += k
    nsa[semel].add(r["stat08"])
    if r["coord_src"] in ("centroid", "neighbor_impute"):
        soft[semel] += k; tot_soft += k
rep(f"national soft-coord share (centroid+neighbor_impute): {100*tot_soft/tot_placed:.1f}% of placed votes")
# 5b. venue-tier: recompute how each ballot's venue was resolved
b18 = json.load(open(rf"{EM}\ballot_locations_18.json", encoding="utf-8"))["ballot_to_location"]
b19 = json.load(open(rf"{EM}\ballot_locations_19.json", encoding="utf-8"))["ballot_to_location"]
b25j = json.load(open(rf"{EM}\ballot_locations_25.json", encoding="utf-8"))
l25 = {f"{s}:{b['ballot']}": b["location"] for s, v in b25j["settlements"].items() for b in v["ballots"]}
renum = defaultdict(int); tot_renum = tot_geo = 0
with open(rf"{EM}\knesset18_ballots.csv", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        semel = r["סמל ישוב"].strip()
        if semel == "0":
            continue
        kosher = int(r["כשרים"] or 0); tot_geo += kosher
        k = f"{semel}:{canon(r['סמל קלפי'].strip())}"
        if b18.get(k):
            tier = "l18"
        elif b19.get(k):
            tier = "l19"
        elif l25.get(k) or l25.get(k + ".1") or b19.get(k + ".1"):
            tier = "renum"   # needed split/other-election recovery -> ballot renumbered
        else:
            tier = "noname"
        if tier in ("renum",):
            renum[semel] += kosher; tot_renum += kosher
rep(f"national renumber/back-prop share (venue needed split/other-election): "
    f"{100*tot_renum/tot_geo:.1f}% of geographic votes")
# flag multi-SA localities where within-city geography is least trustworthy
flags = []
for s in placed:
    if len(nsa[s]) < 2:
        continue
    share = (soft[s] + renum.get(s, 0)) / placed[s] if placed[s] else 0
    if share >= 0.25 and placed[s] >= 3000:
        flags.append((share, name_of.get(int(s), s), len(nsa[s]), placed[s]))
flags.sort(reverse=True)
rep(f"multi-SA localities (>=3k votes) with >=25% soft+renumber vote share: {len(flags)}")
for share, name, n, v in flags[:12]:
    rep(f"   {100*share:4.0f}%  {name}  ({n} SAs, {v:,} votes) — within-city map may be noisy")

# ---- 6. census sanity ----
rep("\n=== 6. CENSUS SANITY ===")
cen = [v for v in sa.values() if "census" in v]
rep(f"areas with census: {len(cen)}/{len(sa)}")
rd = Counter(v["census"].get("rel_dom") for v in cen)
rep(f"rel_dom distribution: {dict(rd)}")
for key in ("age_med", "acad", "hh_size", "ses_cluster", "orig_eur", "aliya02"):
    n = sum(1 for v in cen if key in v["census"])
    rep(f"   {key:12s} coverage: {n}/{len(cen)} ({100*n/len(cen):.0f}%)")

open(os.path.join(HERE, "statarea_2009_validation_report.txt"), "w", encoding="utf-8").write("\n".join(out))
print("\nwrote analysis/statarea_2009_validation_report.txt")
