# -*- coding: utf-8 -*-
"""Sanity inspection of data/vote_transfers.json:
1. Print the 24->25 bloc matrix (abstention variant) for a political smell test.
2. Split-test divergence: per transition, per source bloc, L1 distance between
   the sector matrix row and the pooled row (only rows the sector actually
   owns: sector source votes >= 5,000).
3. Arab-bloc K25 reconstructed total vs official (undercount check).
"""
import json

ROOT = r"C:/Users/yarde/Downloads/election-dashboard-extracted/election-dashboard-main"
T = json.load(open(f"{ROOT}/data/vote_transfers.json", encoding="utf-8"))
BLOCS = T["blocs"] + ["other", "dnv"]

# ---- 1. the 24->25 matrix ----
tr = T["transitions"]["24_to_25"]
lab = tr["bloc_labels"]
M = tr["bloc_with_abstention"]["M"]
sv = tr["bloc_with_abstention"]["source_votes"]
print("=== 24->25 bloc matrix (with abstention, rows = K24 source, row-stochastic) ===")
print(f"{'':>18}" + "".join(f"{c[:9]:>10}" for c in lab))
for i, row in enumerate(M):
    print(f"{lab[i][:16]:>16} |" + "".join(f"{v*100:>9.1f}%" for v in row) + f"   ({sv[i]:,})")

# ---- 2. split-test divergence ----
print("\n=== split test: sector-vs-pooled row L1 distance (pp), rows with sector votes>=5k ===")
print(f"{'trans':>8}  {'sector':>7}  {'bloc':>18} {'L1(pp)':>8} {'sector_votes':>13}")
worst = []
for key in sorted(T["transitions"], key=lambda s: int(s.split("_")[0])):
    tr = T["transitions"][key]
    pooled = tr["bloc_with_abstention"]
    if not pooled or not tr.get("split_test"):
        continue
    for sector in ("arab", "jewish"):
        st = tr["split_test"].get(sector)
        if not st:
            continue
        for i, bloc in enumerate(tr["bloc_labels"]):
            if st["source_votes"][i] < 5000:
                continue
            l1 = sum(abs(a - b) for a, b in zip(st["M"][i], pooled["M"][i])) * 100
            worst.append((l1, key, sector, bloc, st["source_votes"][i]))
worst.sort(reverse=True)
for l1, key, sector, bloc, votes in worst[:15]:
    print(f"{key:>8}  {sector:>7}  {bloc:>18} {l1:>8.1f} {votes:>13,}")
import statistics
print(f"\nmedian row L1 across all sector-rows: {statistics.median(w[0] for w in worst):.1f}pp  (n={len(worst)})")

# ---- 3. Arab bloc K25 total check ----
# target Y totals aren't stored; recompute destination-side bloc totals for 24->25
import re
FIN = {"ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ"}
def norm(s):
    s = re.sub(r"\([^)]*\)", "", str(s).strip())
    for ch in ['"', "״", "'", "׳"]:
        s = s.replace(ch, "")
    s = re.sub(r"[\s\-–־]+", "", s)
    s = "".join(FIN.get(c, c) for c in s)
    return s.replace("יי", "י").replace("וו", "ו")

pnat = json.load(open(f"{ROOT}/data/parties_national.json", encoding="utf-8"))
pbl = json.load(open(f"{ROOT}/data/parties_by_locality.json", encoding="utf-8"))
loc = json.load(open(f"{ROOT}/data/localities.json", encoding="utf-8"))
cb25 = {it["code"]: it["bloc"] for it in pnat["25"]["party_list"]}
kosher = {}
for x in loc:
    d = x.get("data", {}).get("25")
    if d and (d.get("kosher_votes") or 0) > 0:
        key = norm(x["name"])
        if key not in kosher or d["kosher_votes"] > kosher[key]:
            kosher[key] = d["kosher_votes"]
arab_total = total = 0.0
for name, d in pbl["25"].items():
    if "מעטפות" in name:
        continue
    vals = {c: v for c, v in d.items() if isinstance(v, (int, float)) and v > 0}
    s = sum(vals.values())
    kv = kosher.get(norm(name))
    if s > 150:
        counts = vals
    elif s >= 50 and kv:
        counts = {c: v / 100 * kv for c, v in vals.items()}
    else:
        continue
    for c, v in counts.items():
        total += v
        if cb25.get(c) == "arab":
            arab_total += v
print(f"\nK25 arab bloc reconstructed: {arab_total/total*100:.2f}% of valid "
      f"(official: 10.73% = Ra'am 4.07 + Hadash-Ta'al 3.75 + Balad 2.91)")
