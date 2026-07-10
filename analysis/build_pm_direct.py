# -*- coding: utf-8 -*-
"""
build_pm_direct.py — locality results for the three DIRECT PM elections (1996/1999/2001)
→ data/pm_direct.json, consumed by election_map.html's "בחירה ישירה" mode.

Sources: analysis/pm_source/localities_<year>.csv — locality-level candidate counts
OCR'd from the official CEC result volumes and arithmetically repaired (candidate sums
reconcile to `valid` exactly in all three years; national two-way shares reproduce the
official results to <0.2pp; the ~5% national shortfall vs official totals is the
non-geographic envelope vote: soldiers, hospitals, embassies).

Join (mirrors how the Knesset layers behave):
  1. CSV settlement_code == geo feature semel  (election_map_geo.json)
  2. normalized-name match against geo feature names
  Unresolved rows are NOT force-merged into modern polygons — pre-merger reporting
  units (גבעת עדה, מכבים-רעות, צורן…), Negev tribes (שבט), and settlements evacuated
  in 2005 have no polygon of their own and stay unrendered, exactly like their K14/K15
  Knesset rows. Full list in analysis/pm_direct_report.txt; coverage is ~99% of votes.

Output shape (loc keys are EXACT geo feature names — runtime lookup is exact-match,
and the EN fetch shim translates these keys together with geo props.name, so the
name join survives the English build):
  { "contests": {"1996": {"knesset":"14","right_votes":<official>,"left_votes":<official>}, ...},
    "loc": {"<geo name>": {"1996":[right,left,voted,registered], ...}} }
(valid = right+left; invalid = voted-valid — both derivable, not stored.)

Run: python -X utf8 analysis/build_pm_direct.py
Also prints the split-ticket (PM vs concurrent Knesset) distribution used to
calibrate the map's split submode color cap.
"""
import csv
import json
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GEO_PATH = os.path.join(ROOT, "data", "election_map_geo.json")
LOC_PATH = os.path.join(ROOT, "data", "localities.json")
OUT_PATH = os.path.join(ROOT, "data", "pm_direct.json")
REPORT_PATH = os.path.join(HERE, "pm_direct_report.txt")

# right/left candidate official national totals (CEC): Netanyahu-Peres, Barak-Netanyahu, Sharon-Barak
CONTESTS = {
    "1996": {"knesset": "14", "csv": "localities_1996.csv",
             "right_col": "netanyahu", "left_col": "peres",
             "right_votes": 1501023, "left_votes": 1471566},
    "1999": {"knesset": "15", "csv": "localities_1999.csv",
             "right_col": "netanyahu", "left_col": "barak",
             "right_votes": 1402474, "left_votes": 1791020},
    "2001": {"knesset": "15", "csv": "localities_2001.csv",   # PM-only election; K15 was the sitting Knesset
             "right_col": "sharon", "left_col": "barak",
             "right_votes": 1698077, "left_votes": 1023944},
}


def norm_name(n):
    n = re.sub(r"[\"'׳״]", "", n.replace("-", " "))
    return " ".join(n.split())


def main():
    rep_lines = []

    def rep(s=""):
        print(s)
        rep_lines.append(s)

    geo = json.load(open(GEO_PATH, encoding="utf-8"))
    sem2name, norm2name = {}, {}
    for f in geo["features"]:
        p = f["properties"]
        s = p.get("semel")
        if s not in (None, ""):
            sem2name.setdefault(int(s), p["name"])
        norm2name.setdefault(norm_name(p["name"]), p["name"])

    loc_rows = {}          # geo name -> {contest: [r, l, voted, registered]}
    for year, c in CONTESTS.items():
        rows = list(csv.DictReader(open(os.path.join(HERE, "pm_source", c["csv"]),
                                        encoding="utf-8-sig")))
        total_valid = sum(int(r["valid"]) for r in rows)
        matched_valid, unmatched = 0, []
        collisions = defaultdict(list)
        for r in rows:
            sem = int(r["settlement_code"])
            name = sem2name.get(sem) or norm2name.get(norm_name(r["settlement_name"]))
            right, left = int(r[c["right_col"]]), int(r[c["left_col"]])
            if name is None:
                unmatched.append((right + left, r["settlement_code"], r["settlement_name"]))
                continue
            entry = loc_rows.setdefault(name, {})
            if year in entry:   # two era rows landing on one polygon — sum, and log it
                collisions[name].append(r["settlement_name"])
                prev = entry[year]
                entry[year] = [prev[0] + right, prev[1] + left,
                               prev[2] + int(r["voted"]), prev[3] + int(r["registered"])]
            else:
                entry[year] = [right, left, int(r["voted"]), int(r["registered"])]
            matched_valid += right + left
        unmatched.sort(reverse=True)
        rep(f"=== {year}: {len(rows)} rows, matched {len(rows)-len(unmatched)} "
            f"({matched_valid:,}/{total_valid:,} valid votes = {matched_valid/total_valid*100:.2f}%)")
        for nm, srcs in collisions.items():
            rep(f"  SUMMED onto {nm}: {srcs}")
        rep(f"  unmatched ({len(unmatched)} rows — era units / tribes / evacuated, no polygon):")
        for v, code, nm in unmatched:
            rep(f"    {code:>6} {nm} ({v:,})")

    out = {
        "contests": {y: {"knesset": c["knesset"],
                         "right_votes": c["right_votes"], "left_votes": c["left_votes"]}
                     for y, c in CONTESTS.items()},
        "loc": loc_rows,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    rep(f"\nwrote {OUT_PATH} — {len(loc_rows)} localities, "
        f"{os.path.getsize(OUT_PATH)/1024:.0f} KB")

    # --- split-ticket analysis (PM two-way vs concurrent Knesset two-bloc) ---
    # joined against localities.json (includes era units). Feeds three things:
    # the map submode's color-cap calibration, data/pm_split.json (the findings-page
    # scatter), and the weighted stats quoted in the findings.html panel text.
    locs = json.load(open(LOC_PATH, encoding="utf-8"))
    byname = {}
    for l in locs:
        byname.setdefault(norm_name(l["name"]), l)
    split_out = {}
    for year in ("1996", "1999"):
        c = CONTESTS[year]
        k = c["knesset"]
        rows = list(csv.DictReader(open(os.path.join(HERE, "pm_source", c["csv"]),
                                        encoding="utf-8-sig")))
        vals, pts = [], []
        for r in rows:
            row = byname.get(norm_name(r["settlement_name"]))
            ed = row and row["data"].get(k)
            if not ed:
                continue
            rh, cla = ed.get("right_haredi_pct") or 0, ed.get("center_left_arab_pct") or 0
            right, left = int(r[c["right_col"]]), int(r[c["left_col"]])
            if rh + cla <= 0 or right + left <= 0:
                continue
            rh2 = rh / (rh + cla) * 100
            pm2 = right / (right + left) * 100
            split = pm2 - rh2
            vals.append((split, right + left, r["settlement_name"]))
            pts.append([row["name"], round(rh2, 1), round(pm2, 1), right + left])
        split_out[year] = pts
        vals.sort()
        n = len(vals)
        pct = lambda q: vals[int(q * (n - 1))][0]
        rep(f"\n--- split-ticket {year} (PM right two-way % minus K{k} right-haredi two-bloc %) ---")
        rep(f"  n={n}  p1={pct(.01):+.1f}  p10={pct(.10):+.1f}  p50={pct(.50):+.1f}  "
            f"p90={pct(.90):+.1f}  p99={pct(.99):+.1f}")
        rep("  most PM-right-leaning splits: " +
            "; ".join(f"{nm} {v:+.1f}" for v, _, nm in vals[-5:][::-1]))
        rep("  most PM-left-leaning splits: " +
            "; ".join(f"{nm} {v:+.1f}" for v, _, nm in vals[:5]))
        # vote-weighted stats for the findings panel text
        W = sum(w for _, w, _ in vals)
        wmean_abs = sum(abs(v) * w for v, w, _ in vals) / W
        within3 = sum(w for v, w, _ in vals if abs(v) <= 3) / W * 100
        within5 = sum(w for v, w, _ in vals if abs(v) <= 5) / W * 100
        mx = sum(v * w for v, w, _ in vals) / W
        my = 0  # weighted correlation between rh2 and pm2
        xs = [(p[1], p[2], p[3]) for p in pts]
        sw = sum(w for _, _, w in xs)
        mrx = sum(x * w for x, _, w in xs) / sw
        mry = sum(y * w for _, y, w in xs) / sw
        cov = sum(w * (x - mrx) * (y - mry) for x, y, w in xs) / sw
        vx = sum(w * (x - mrx) ** 2 for x, _, w in xs) / sw
        vy = sum(w * (y - mry) ** 2 for _, y, w in xs) / sw
        rep(f"  weighted: r={cov/(vx*vy)**0.5:.3f}  mean(split)={mx:+.2f}  mean|split|={wmean_abs:.2f}  "
            f"within±3pp={within3:.1f}%  within±5pp={within5:.1f}%")
    SPLIT_PATH = os.path.join(ROOT, "data", "pm_split.json")
    with open(SPLIT_PATH, "w", encoding="utf-8") as f:
        json.dump(split_out, f, ensure_ascii=False, separators=(",", ":"))
    rep(f"\nwrote {SPLIT_PATH} — {len(split_out['1996'])}+{len(split_out['1999'])} points, "
        f"{os.path.getsize(SPLIT_PATH)/1024:.0f} KB")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(rep_lines) + "\n")
    print(f"\nreport: {REPORT_PATH}")


if __name__ == "__main__":
    main()
