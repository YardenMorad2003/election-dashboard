# -*- coding: utf-8 -*-
"""
validate_statarea_1995era.py — validation for the K16/K17 layers on the 1995
geometry (built by build_statarea_1995era.py).

Checks:
  1. Closure: layer per-locality valid-vote totals vs the era CSV's own totals
     (merged municipalities compared as constituent groups). Overall % + any
     locality < 85%.
  2. Coord-source drift probe: votes by coord_src (address-precise vs
     street-only vs imputed vs single-SA vs none), overall + the worst cities.
  3. Known-locality sanity: Bnei Brak -> Haredi bloc, Umm al-Fahm -> Arab bloc,
     Tel Aviv -> center/left lean.

Run: python -X utf8 analysis/validate_statarea_1995era.py
"""
import csv
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAP = os.path.join(HERE, "statarea_inputs")
EM = r"C:\Users\yarde\elections-merge\data"
GERESH = "'׳״‘’“”\"`"
DOUBLE = "מעטפות כפולות"

MERGED = {
    "מודיעין מכבים רעו": [1200, 1273],
    "יהוד נוה אפרים": [9400, 1062],
    "שגור": [516, 490, 483],
    "באקה גת": [6000, 628],
    "עיר כרמל": [494, 534],
    "צורן קדימה": [195, 1308],
    "בנימינה גבעת עדה": [9800, 50],
    "בסמה": [639, 643, 657],
    "מעלה עירון": [640, 645, 644, 934],
}


def norm(s):
    if not s:
        return ""
    for ch in GERESH:
        s = s.replace(ch, "")
    s = re.sub(r"[()\-,./\\:;+]", " ", s)
    return " ".join(s.replace("יי", "י").replace("וו", "ו").split())


def iv(x):
    try:
        return int(float(x))
    except (ValueError, TypeError):
        return 0


def main():
    name2sem = {}
    k16rows = list(csv.DictReader(open(rf"{EM}\knesset16_ballots.csv", encoding="utf-8-sig")))
    for r in k16rows:
        sm = str(iv(r["סמל ישוב"]))
        if sm != "0":
            name2sem[norm(r["שם ישוב"])] = sm
    for r in csv.DictReader(open(rf"{EM}\knesset25_ballots.csv", encoding="utf-8-sig")):
        name2sem.setdefault(norm(r["שם ישוב"]), r["סמל ישוב"].strip())
    sem2grp = {}
    for nm, sset in MERGED.items():
        for s in sset:
            sem2grp[s] = nm

    for e in ("17", "16"):
        print(f"\n================ K{e} ================")
        layer = json.load(open(os.path.join(ROOT, "data", f"statarea_k{e}.json"), encoding="utf-8"))["areas"]

        # ---- 1. closure per locality group ----
        csv_tot = defaultdict(int)       # group -> csv valid votes
        names = {}
        if e == "17":
            for r in csv.DictReader(open(rf"{EM}\knesset17_ballots.csv", encoding="utf-8-sig")):
                nm_raw = r["שם ישוב"].strip()
                if nm_raw == DOUBLE:
                    continue
                nm = norm(nm_raw)
                grp = nm if nm in MERGED else name2sem.get(nm)
                if grp is None:
                    grp = f"?{nm_raw}"
                csv_tot[grp] += iv(r["כשרים"])
                names[grp] = nm_raw
        else:
            for r in k16rows:
                sm = iv(r["סמל ישוב"])
                if sm <= 0:
                    continue
                nm = norm(r["שם ישוב"])
                grp = nm if nm in MERGED else sem2grp.get(sm, str(sm))
                csv_tot[grp] += iv(r["כשרים"])
                names.setdefault(grp, r["שם ישוב"].strip())
        lay_tot = defaultdict(int)
        for a in layer.values():
            grp = sem2grp.get(a["semel"], str(a["semel"]))
            lay_tot[grp] += a["valid"]
        allc = sum(csv_tot.values()); alll = sum(lay_tot.values())
        print(f"closure: layer {alll:,} / csv {allc:,} = {100*alll/allc:.2f}%")
        bad = []
        for grp, cv in csv_tot.items():
            lv = lay_tot.get(grp, 0)
            if cv >= 400 and lv / cv < 0.85:
                bad.append((lv / cv, names.get(grp, grp), cv - lv))
        bad.sort()
        print(f"localities (>=400 votes) below 85% closure: {len(bad)}")
        for f, nm, missing in bad[:12]:
            print(f"   {nm[:20]:20s} {f:6.1%} placed (missing {missing:,})")
        over = [(lv / csv_tot[g], names.get(g, g)) for g, lv in lay_tot.items()
                if g in csv_tot and csv_tot[g] >= 400 and lv / csv_tot[g] > 1.005]
        if over:
            print(f"over-closure (>100.5%, spillover suspects): {len(over)}: "
                  + ", ".join(f"{nm}({f:.1%})" for f, nm in sorted(over, reverse=True)[:6]))

        # ---- 2. coord-source drift ----
        src_votes = defaultdict(int)
        city_soft = defaultdict(lambda: [0, 0])   # semel -> [soft, total] placed votes
        snap_p = os.path.join(SNAP, f"ballot_stat95_{e}.csv")
        for r in csv.DictReader(open(snap_p, encoding="utf-8-sig")):
            v = iv(r["valid"])
            src_votes[r["coord_src"]] += v
            if r["stat95"]:
                soft = r["coord_src"] in ("impute", "addr_street", "addr_soft_nocc", "addr_city")
                cs = city_soft[r["semel"]]
                cs[0] += v * soft; cs[1] += v
        tot = sum(src_votes.values())
        print("votes by coord source: " + ", ".join(
            f"{k}={100*v/tot:.1f}%" for k, v in sorted(src_votes.items(), key=lambda t: -t[1])))
        worst = [(s[0] / s[1], sm, s[1]) for sm, s in city_soft.items() if s[1] >= 20000 and s[0] / s[1] > 0.15]
        worst.sort(reverse=True)
        if worst:
            print("cities >=20k votes with >15% soft coords:")
            for f, sm, t in worst[:8]:
                print(f"   semel {sm}: {f:.0%} of {t:,}")

        # ---- 3. known-locality sanity ----
        checks = [("6100", "Bnei Brak", "haredi"), ("2710", "Umm al-Fahm", "arab"), ("5000", "Tel Aviv", None)]
        for sm, label, expect in checks:
            recs = [a for a in layer.values() if str(a["semel"]) == sm]
            if not recs:
                print(f"   {label}: NO AREAS")
                continue
            n = len(recs)
            mean = lambda k: sum(a["blocs"].get(k, 0) for a in recs) / n
            wins = defaultdict(int)
            for a in recs:
                wins[a["winner"]] += 1
            top = sorted(wins.items(), key=lambda t: -t[1])[:3]
            print(f"   {label}: {n} SAs, winners {top}, "
                  f"haredi={mean('haredi'):.1f} arab={mean('arab'):.1f} right={mean('right'):.1f} "
                  f"center={mean('center'):.1f} left={mean('left'):.1f}"
                  + (f"  [expect {expect} dominant]" if expect else ""))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
