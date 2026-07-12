# -*- coding: utf-8 -*-
"""
measure_k18_crosswalk.py — Step 0 (MEASUREMENT ONLY) for the K18→K19/K20
kalpi-number crosswalk (CONTINUE.md §3). Writes nothing; prints a report.

Question: can 2013/2015 kalpiot inherit the K18 official-address coordinate
by (semel, kalpi#) identity — the same move K16 already does off K17?

Per election e in (19, 20):
  1. Match rate (semel, canon(ballot#)): K18 xlsx → knesset{e}_ballots.csv,
     weighted by kosher votes; overall + multi-SA-only (single-SA localities
     need no coordinate, so multi-SA is the decision-relevant slice).
  2. Venue-name agreement among matches: k18_ballot_venues.json vs
     ballot_locations_{e}.json (norm + token-Jaccard, build_coords_18 helpers).
  3. Roster agreement among matches: xlsx eligible voters vs the year's בזב
     (exact / ±20 / ratio quartiles) — split by name class to validate the
     name guard.
  4. Coordinate benefit: K18 coord_src (ballot_coords_18.csv) of the matched
     multi-SA votes — 'address' is the slice the crosswalk actually upgrades;
     also how many matched ballots have NO venue name in the year's own
     ballot_locations (today those lean on the K25-aligned fallback).

Gates (CONTINUE §3): K18→K19 expect ~90%+ match w/ high name agreement → wire.
K18→K20 (6 years, 2 steps) lower — likely restrict to the name-agreeing
subset. If name agreement is poor overall, stop and report.

Run: python -X utf8 analysis/measure_k18_crosswalk.py
"""
import csv
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(HERE, "statarea_inputs")
EM = r"C:\Users\yarde\elections-merge\data"
XLSX = r"C:\Users\yarde\Downloads\knesset18_polling_places.xlsx"
PSEUDO = ("0", "875", "9999", "99999")   # external/double envelopes (875 collides with כפר עבודה)
sys.path.insert(0, HERE)
from build_coords_18 import norm, jacc  # noqa: E402


def canon(x):
    """Float-normalize a kalpi number. Sub-number leading zeros folded
    ('24.01' == '24.1' — CEC files disagree on the sub-number format)."""
    try:
        f = float(x)
        if f == int(f):
            return str(int(f))
        frac = str(f).split(".")[1].lstrip("0") or "0"
        return f"{int(f)}.{frac}"
    except ValueError:
        return str(x).strip()


def pct(a, b):
    return f"{100 * a / b:.1f}%" if b else "n/a"


def quartiles(xs):
    xs = sorted(xs)
    if not xs:
        return None
    q = lambda p: xs[min(len(xs) - 1, int(p * len(xs)))]
    return q(0.25), q(0.50), q(0.75)


def load_k18():
    """(semel, ballot) -> (venue_name, eligible) from the official CEC xlsx."""
    import openpyxl
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    k18 = {}
    hdr = None
    for row in wb["Polling Places"].iter_rows(values_only=True):
        if hdr is None:
            if row and row[0] == "Committee code":
                hdr = list(row)
            continue
        if not row or row[3] is None:
            continue
        sem = str(int(str(row[3]).strip()))
        b = canon(row[5])
        vname = str(row[9]).strip() if row[9] is not None else ""
        elig = int(row[11]) if isinstance(row[11], (int, float)) else None
        k18[(sem, b)] = (vname, elig)
    return k18


def load_k18_coords():
    """(semel, ballot) -> coord_src; semel -> single_sa flag."""
    csrc, single = {}, {}
    for r in csv.DictReader(open(os.path.join(SNAP, "ballot_coords_18.csv"), encoding="utf-8-sig")):
        csrc[(r["semel"], canon(r["ballot"]))] = r["coord_src"]
        single[r["semel"]] = r["single_sa"] == "1"
    return csrc, single


def measure(e, k18, csrc, single):
    bl = json.load(open(rf"{EM}\ballot_locations_{e}.json", encoding="utf-8"))["ballot_to_location"]
    with open(rf"{EM}\knesset{e}_ballots.csv", encoding="utf-8-sig") as f:
        rdr = csv.DictReader(f)
        hdr = rdr.fieldnames
        bcol = next(c for c in ("מספר קלפי", "סמל קלפי", "קלפי") if c in hdr)
        ecol = next((c for c in hdr if "בז" in c), "בזב")
        rows = list(rdr)

    tot = Counter()            # votes: all / multi / unknown-locality
    m = Counter()              # matched votes: all / multi / multi_no_year_name
    nameclass = Counter()      # matched votes by name class
    src_multi = Counter()      # matched multi-SA votes by K18 coord_src
    gate = Counter()           # matched multi votes: name-agree × coord_src=address
    roster = defaultdict(lambda: [0, 0, 0, []])   # name class -> [n, exact, ±20, ratios]

    for r in rows:
        semel = r["סמל ישוב"].strip()
        if semel in PSEUDO:
            continue
        b = canon(r[bcol].strip())
        votes = int(r["כשרים"] or 0)
        sng = single.get(semel)          # None = locality unknown to K18 file
        multi = sng is False
        tot["all"] += votes
        if multi:
            tot["multi"] += votes
        elif sng is None:
            tot["unk"] += votes

        hit = k18.get((semel, b))
        if hit is None:
            continue
        v18, e18 = hit
        m["all"] += votes
        if multi:
            m["multi"] += votes

        # venue-name class (vote-weighted)
        vy = bl.get(f"{semel}:{b}") or ""
        n18, ny = norm(v18), norm(vy)
        if not ny and multi:
            m["multi_noname"] += votes
        if not n18 or not ny:
            cls = "missing"
        elif n18 == ny:
            cls = "exact"
        elif jacc(set(n18.split()), set(ny.split())) >= 0.5:
            cls = "jaccard"
        else:
            cls = "disagree"
        nameclass[cls] += votes

        # roster agreement (ballot-weighted; ratios for quartiles)
        ey = int(r[ecol] or 0)
        if e18 and ey:
            rec = roster[cls]
            rec[0] += 1
            rec[1] += (e18 == ey)
            rec[2] += (abs(e18 - ey) <= 20)
            rec[3].append(ey / e18)

        if multi:
            src = csrc.get((semel, b), "?")
            src_multi[src] += votes
            if cls in ("exact", "jaccard") and src == "address":
                gate["agree_address"] += votes
            if cls in ("exact", "jaccard"):
                gate["agree_any"] += votes

    print(f"\n=== K18 → K{e} ===")
    print(f"K{e} geographic votes: {tot['all']:,} "
          f"(multi-SA {pct(tot['multi'], tot['all'])}, unknown-locality {pct(tot['unk'], tot['all'])})")
    print(f"key match:  all {pct(m['all'], tot['all'])} of votes | "
          f"multi-SA {pct(m['multi'], tot['multi'])}")
    tw = sum(nameclass.values())
    print("venue-name among matches (vote-weighted): "
          + " | ".join(f"{c} {pct(nameclass[c], tw)}" for c in ("exact", "jaccard", "disagree", "missing")))
    print(f"matched multi-SA votes with NO K{e} venue name (K25-fallback territory today): "
          f"{pct(m['multi_noname'], m['multi'])}")
    print("roster (xlsx eligible vs בזב) by name class [n ballots | exact | ±20 | ratio Q1/med/Q3]:")
    for cls in ("exact", "jaccard", "disagree", "missing"):
        n, ex, w20, ratios = roster[cls]
        if not n:
            continue
        qs = quartiles(ratios)
        print(f"  {cls:8s} n={n:5d}  exact {pct(ex, n):>6s}  ±20 {pct(w20, n):>6s}  "
              f"ratio {qs[0]:.2f}/{qs[1]:.2f}/{qs[2]:.2f}")
    print("K18 coord_src of matched multi-SA votes: "
          + " | ".join(f"{s} {pct(v, m['multi'])}" for s, v in src_multi.most_common()))
    print(f"GATE VIEW (share of ALL multi-SA votes): matched+name-agree "
          f"{pct(gate['agree_any'], tot['multi'])} ; of which K18-address-sourced "
          f"{pct(gate['agree_address'], tot['multi'])}")


def main():
    k18 = load_k18()
    csrc, single = load_k18_coords()
    print(f"K18 xlsx: {len(k18):,} kalpi rows loaded; "
          f"coords file: {len(csrc):,} ballots, {sum(not v for v in single.values()):,} multi-SA localities")
    for e in ("19", "20"):
        measure(e, k18, csrc, single)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
