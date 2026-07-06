# -*- coding: utf-8 -*-
"""
validate_statarea_2022.py — validation for the 2022 stat-area layer.

Checks:
1. National coverage: SA-summed valid votes & per-party totals vs official K25.
2. Per-locality closure: sum of a locality's SA votes vs its localities.json row
   (must be <= official; ratio = geocoded-station coverage in that locality).
3. Bloc math: rh + cla + other == 100 per SA.
4. Census sanity spot-checks: Bnei Brak = haredi/ג; north Tel Aviv = secular,
   high-education, פה/מרצ strong; Kseife = Muslim, עם strong.

Run: python -X utf8 analysis/validate_statarea_2022.py
Report: analysis/statarea_validation_report.txt
"""
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

rep_lines = []


def rep(s=""):
    rep_lines.append(s)
    print(s)


sa = json.load(open(os.path.join(ROOT, "data", "statarea_2022.json"), encoding="utf-8"))["areas"]
loc = json.load(open(os.path.join(ROOT, "data", "localities.json"), encoding="utf-8"))
pn = json.load(open(os.path.join(ROOT, "data", "parties_national.json"), encoding="utf-8"))["25"]

# rebuild party counts per SA from snapshot (data JSON stores pcts only)
import csv
snap = os.path.join(HERE, "statarea_inputs", "k25_demo_join_v11.csv")
with open(snap, encoding="utf-8-sig") as f:
    rdr = csv.DictReader(f)
    hdr = rdr.fieldnames
    party_codes = hdr[hdr.index("valid") + 1:hdr.index("n_ballots")]
    rows = [r for r in rdr]

# ---- 1. national coverage ----
rep("=== 1. NATIONAL COVERAGE ===")
tot_valid = sum(int(float(r["valid"])) for r in rows if r["stat22"] in
                {str(k) for k in sa})
nat_votes = pn.get("national_votes") or {}
official_total = sum(nat_votes.values()) if nat_votes else 4764742
rep(f"valid votes in layer: {tot_valid:,} | official K25 kosher: 4,764,742 "
    f"| geographic (excl. envelopes 458,714): 4,306,028 -> coverage {100*tot_valid/4306028:.2f}%")
psum = defaultdict(int)
for r in rows:
    if r["stat22"] not in {str(k) for k in sa}:
        continue
    for c in party_codes:
        psum[c] += int(float(r[c] or 0))
rep(f"{'party':>6} {'in layer':>10} {'official':>10} {'coverage':>9}")
skew = []
for code, off in sorted(nat_votes.items(), key=lambda x: -x[1])[:12]:
    got = psum.get(code, 0)
    cov = 100 * got / off if off else 0
    skew.append(cov)
    rep(f"{code:>6} {got:>10,} {off:>10,} {cov:>8.1f}%")
rep(f"per-party coverage spread (top-12): {min(skew):.1f}%–{max(skew):.1f}% "
    f"(tight spread = no partisan skew in what's unmapped)")

# ---- 2. per-locality closure ----
rep("")
rep("=== 2. PER-LOCALITY CLOSURE (SA sums vs localities.json K25) ===")
by_semel = defaultdict(int)
for k, v in sa.items():
    if "valid" in v:
        by_semel[v["semel"]] += v["valid"]
over = []
checked = 0
covs = []
for r in loc:
    e = (r.get("data") or {}).get("25")
    s = r.get("semel")
    if not e or not s or s not in by_semel:
        continue
    checked += 1
    ratio = by_semel[s] / e["kosher_votes"]
    covs.append((ratio, r["name"], by_semel[s], e["kosher_votes"]))
    if ratio > 1.001:
        over.append((ratio, r["name"], by_semel[s], e["kosher_votes"]))
covs.sort()
rep(f"localities checked: {checked}; SA-sum EXCEEDS official row: {len(over)}")
for x in over[:10]:
    rep(f"   OVER: {x[1]} ratio={x[0]:.3f} ({x[2]:,} vs {x[3]:,})")
full = sum(1 for c in covs if c[0] > 0.999)
rep(f"localities with 100% of votes mapped: {full}/{checked}")
rep("lowest-coverage localities (geocoding gaps):")
for ratio, name, got, off in covs[:8]:
    rep(f"   {100*ratio:5.1f}%  {name} ({got:,}/{off:,})")

# ---- 3. bloc math ----
rep("")
rep("=== 3. BLOC MATH ===")
bad = 0
for k, v in sa.items():
    b = v["blocs"]
    if not (abs((b["rh"] + b["cla"]) - (b["right"] + b["haredi"] + b["center"] + b["left"] + b["arab"] + b["opposition_right"])) < 0.05):
        bad += 1
    if b["rh"] + b["cla"] > 100.05:
        bad += 1
rep(f"SAs with inconsistent bloc sums: {bad}/{len(sa)}")

# ---- 4. spot checks ----
rep("")
rep("=== 4. SPOT CHECKS ===")


def spot(semel, label, expect):
    recs = [v for v in sa.values() if v["semel"] == semel]
    if not recs:
        rep(f"   {label}: NO SAs FOUND ✗")
        return
    n = len(recs)
    from collections import Counter
    winners = Counter(r["winner"] for r in recs).most_common(3)
    dat = Counter((r.get("census") or {}).get("datiyut") for r in recs).most_common(2)
    acads = [c for r in recs if (c := (r.get("census") or {}).get("acad")) is not None]
    acad = sum(acads) / len(acads) if acads else None
    rep(f"   {label}: {n} SAs | winners {winners} | datiyut {dat} | mean acad "
        f"{acad:.1f}%" if acad is not None else f"   {label}: {n} SAs | winners {winners} | datiyut {dat}")
    rep(f"      expectation: {expect}")


semel_of = {r["name"]: r.get("semel") for r in loc}
for name, expect in [
    ("בני ברק", "winner ג/שס everywhere, datiyut=חרדי"),
    ("תל אביב - יפו", "mostly פה, datiyut=חילוני, high acad"),
    ("ירושלים", "mixed: ג in Haredi SAs, מחל elsewhere"),
    ("מודיעין עילית", "winner ג, haredi"),
    ("כסיפה", "Muslim, winner עם"),
    ("רמת השרון", "פה dominant, secular, very high acad"),
]:
    s = semel_of.get(name)
    if s:
        spot(s, f"{name} (semel {s})", expect)
    else:
        rep(f"   {name}: no semel in localities.json ✗")

# quantify station-spillover (votes landing in a neighboring locality's SAs)
excess = sum(got - off for ratio, name, got, off in covs if ratio > 1.001)
rep("")
rep(f"station-spillover: {len(over)} localities show SA-sums above their official total; "
    f"total excess votes {excess:,} ({100*excess/4306028:.2f}% of geographic votes) — "
    f"inherent to assigning votes to the STATION's polygon (people sometimes vote "
    f"outside their home stat-area; geocoded station may sit across a boundary)")

open(os.path.join(HERE, "statarea_validation_report.txt"), "w", encoding="utf-8").write("\n".join(rep_lines))
