# -*- coding: utf-8 -*-
"""
detect_misgeocode_18.py — flag polling-station venues whose votes contradict the
demographics of the stat-area they were geocoded into (i.e. likely mis-geocoded
in Cain's station_coordinates.json due to same-name collisions).

Signal (per venue, aggregating its venue-precise K18 ballots):
  - venue lands in a WEALTHY/secular SA (2008 socio cluster >= 14 on the 1-20
    scale, or Jewish & acad >= 48%) BUT its voters are traditional/Haredi
    (ג+שס >= 30%, or שס >= 18%) and it is an OUTLIER vs the SA's other ballots;
  - or an Arab-majority venue (>=55%) sitting in a wealthy Jewish SA.

Confirmed fixes go to analysis/statarea_inputs/station_coord_fixes.json (verify
each via its official CEC venue address / web search before adding).

Run: python -X utf8 analysis/detect_misgeocode_18.py
"""
import csv
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAP = os.path.join(HERE, "statarea_inputs")
DATA = r"C:\Users\yarde\elections-merge\data"
HAR = ("ג", "שס")
ARABP = ("ו", "עם", "ד", "רק")


def canon(x):
    try:
        f = float(x)
        return str(int(f)) if f == int(f) else x
    except ValueError:
        return x


def main():
    b18 = json.load(open(rf"{DATA}\ballot_locations_18.json", encoding="utf-8"))["ballot_to_location"]
    b19 = json.load(open(rf"{DATA}\ballot_locations_19.json", encoding="utf-8"))["ballot_to_location"]
    b25 = json.load(open(rf"{DATA}\ballot_locations_25.json", encoding="utf-8"))
    l25 = {f"{s}:{bb['ballot']}": bb["location"] for s, v in b25["settlements"].items() for bb in v["ballots"]}
    name = {r.get("semel"): r["name"] for r in json.load(open(os.path.join(ROOT, "data", "localities.json"), encoding="utf-8")) if r.get("semel")}
    cen = json.load(open(os.path.join(ROOT, "data", "statarea_2009.json"), encoding="utf-8"))["areas"]
    s08 = {}
    for r in csv.DictReader(open(os.path.join(SNAP, "ballot_stat08_18.csv"), encoding="utf-8-sig")):
        s08[(r["semel"], r["ballot"])] = (r["stat08"], r["coord_src"])

    def venue_of(sem, b):
        return b18.get(f"{sem}:{b}") or b19.get(f"{sem}:{b}") or l25.get(f"{sem}:{b}") or l25.get(f"{sem}:{b}.1")

    SAk = defaultdict(lambda: [0, 0, 0])
    V = defaultdict(lambda: {"k": 0, "har": 0, "shas": 0, "arab": 0, "sa": None})
    for r in csv.DictReader(open(rf"{DATA}\knesset18_ballots.csv", encoding="utf-8-sig")):
        sem = r["סמל ישוב"].strip()
        if sem == "0":
            continue
        b = canon(r["סמל קלפי"].strip())
        st = s08.get((sem, b))
        if not st or not st[0] or st[1] != "venue":
            continue
        ven = venue_of(sem, b)
        if not ven:
            continue
        k = int(r["כשרים"] or 0)
        har = sum(int(r[p] or 0) for p in HAR)
        arab = sum(int(r[p] or 0) for p in ARABP)
        SAk[st[0]][0] += k; SAk[st[0]][1] += har; SAk[st[0]][2] += arab
        d = V[(sem, ven)]; d["k"] += k; d["har"] += har; d["shas"] += int(r["שס"] or 0); d["arab"] += arab; d["sa"] = st[0]

    flags = []
    for (sem, ven), d in V.items():
        if d["k"] < 120:
            continue
        sa = d["sa"]; c = cen.get(sa, {}).get("census", {})
        cl, ac, rel = c.get("ses_cluster"), c.get("acad"), c.get("rel_dom")
        har, shas, arab = d["har"] / d["k"], d["shas"] / d["k"], d["arab"] / d["k"]
        ok, oh, oa = (SAk[sa][i] - [d["k"], d["har"], d["arab"]][i] for i in range(3))
        oth_har = oh / ok if ok > 0 else 0
        oth_arab = oa / ok if ok > 0 else 0
        rich = (cl is not None and cl >= 14) or (rel == "יהודי" and ac is not None and ac >= 48)
        if rich and (har >= 0.30 or shas >= 0.18) and (har - oth_har >= 0.25 or ok < d["k"] * 0.4):
            flags.append((har, sem, name.get(int(sem), sem), ven, sa, d["k"],
                          f"HAREDI har={har:.0%} shas={shas:.0%} | SA cluster={cl} acad={ac} others_har={oth_har:.0%}"))
        elif rich and arab >= 0.55 and (arab - oth_arab >= 0.3):
            flags.append((arab, sem, name.get(int(sem), sem), ven, sa, d["k"],
                          f"ARAB arab={arab:.0%} | SA cluster={cl} acad={ac} others_arab={oth_arab:.0%}"))
    flags.sort(reverse=True)
    print(f"FLAGGED mis-geocode suspects: {len(flags)}\n")
    for _, sem, nm, ven, sa, k, reason in flags:
        print(f"  {nm[:14]:14s} k={k:>4} SA {sa} | {ven[:34]!r}\n        {reason}")


if __name__ == "__main__":
    main()
