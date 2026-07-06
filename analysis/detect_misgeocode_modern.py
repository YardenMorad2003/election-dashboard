# -*- coding: utf-8 -*-
"""
detect_misgeocode_modern.py — generalize detect_misgeocode_18.py to the modern
era (K21–K25 on the 2022 census): flag venues whose votes contradict the
demographics of the stat-area they were geocoded into (same-name collisions in
Cain's station_coordinates.json — SESSION_CHALLENGES.md §6).

Better signal than 2008: the 2022 census carries an explicit per-SA `datiyut`
(religiosity) class, so "Haredi votes inside a חילוני SA" is direct, not an
SES-cluster proxy.

Per venue (aggregating its ballots that landed in an SA):
  - SA is secular/upscale (datiyut == חילוני, or Jewish & acad >= 48) BUT the
    venue's voters are Haredi (haredi-bloc >= 30% or שס >= 18%) AND an outlier
    vs the SA's other ballots;
  - or an Arab-majority venue (>= 55%) in a secular Jewish SA (outlier-guarded
    to spare real mixed-city pockets, e.g. Jaffa).

Confirmed fixes go to analysis/statarea_inputs/station_coord_fixes.json
(verify each via web search -> street address -> geocode -> PIP first).

Run: python -X utf8 analysis/detect_misgeocode_modern.py [25 24 ...]
"""
import csv
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAP = os.path.join(HERE, "statarea_inputs")
EM = r"C:\Users\yarde\elections-merge\data"


def main(elections):
    cen = json.load(open(os.path.join(ROOT, "data", "statarea_2022.json"), encoding="utf-8"))["areas"]
    name = {r.get("semel"): r["name"]
            for r in json.load(open(os.path.join(ROOT, "data", "localities.json"), encoding="utf-8"))
            if r.get("semel")}
    pn = json.load(open(os.path.join(ROOT, "data", "parties_national.json"), encoding="utf-8"))

    for e in elections:
        bl = json.load(open(rf"{EM}\ballot_locations_{e}.json", encoding="utf-8"))["ballot_to_location"]
        har_codes = {p["code"] for p in pn[e]["party_list"] if p["bloc"] == "haredi"}
        arab_codes = {p["code"] for p in pn[e]["party_list"] if p["bloc"] == "arab"}
        s22 = {}
        for r in csv.DictReader(open(os.path.join(SNAP, f"ballot_stat22_{e}.csv"), encoding="utf-8-sig")):
            if r["stat22"]:
                s22[(r["semel"], r["ballot"])] = r["stat22"]

        SAk = defaultdict(lambda: [0, 0, 0])           # sa -> [valid, haredi, arab]
        V = defaultdict(lambda: {"k": 0, "har": 0, "shas": 0, "arab": 0, "sas": Counter()})
        with open(rf"{EM}\knesset{e}_ballots.csv", encoding="utf-8-sig") as f:
            rdr = csv.DictReader(f)
            hdr = rdr.fieldnames
            bcol = next(c for c in ("קלפי", "סמל קלפי", "מספר קלפי") if c in hdr)
            for r in rdr:
                sem = (r["סמל ישוב"] or "").strip()
                if sem in ("0", ""):
                    continue
                b = r[bcol].strip()
                sa = s22.get((sem, b))
                if not sa:
                    continue
                ven = bl.get(f"{sem}:{b}") or bl.get(f"{sem}:{b}.1")
                if not ven:
                    continue
                k = int(r["כשרים"] or 0)
                har = sum(int(r[p] or 0) for p in har_codes if p in r)
                arab = sum(int(r[p] or 0) for p in arab_codes if p in r)
                SAk[sa][0] += k; SAk[sa][1] += har; SAk[sa][2] += arab
                d = V[(sem, ven)]
                d["k"] += k; d["har"] += har; d["arab"] += arab
                d["shas"] += int(r.get("שס") or 0)
                d["sas"][sa] += k

        flags = []
        for (sem, ven), d in V.items():
            if d["k"] < 120:
                continue
            sa = d["sas"].most_common(1)[0][0]
            c = (cen.get(sa) or {}).get("census") or {}
            dat, rel, ac = c.get("datiyut"), c.get("religion"), c.get("acad")
            har, shas, arab = d["har"] / d["k"], d["shas"] / d["k"], d["arab"] / d["k"]
            ok = SAk[sa][0] - d["sas"][sa]
            oth_har = (SAk[sa][1] - d["har"]) / ok if ok > 0 else 0
            oth_arab = (SAk[sa][2] - d["arab"]) / ok if ok > 0 else 0
            secular = (dat == "חילוני") or (rel == "יהודים" and ac is not None and ac >= 48)
            if secular and (har >= 0.30 or shas >= 0.18) and (har - oth_har >= 0.25 or ok < d["k"] * 0.4):
                flags.append((har, sem, name.get(int(sem), sem), ven, sa, d["k"],
                              f"HAREDI har={har:.0%} shas={shas:.0%} | SA datiyut={dat} acad={ac} others_har={oth_har:.0%}"))
            elif secular and rel == "יהודים" and arab >= 0.55 and (arab - oth_arab >= 0.30):
                flags.append((arab, sem, name.get(int(sem), sem), ven, sa, d["k"],
                              f"ARAB arab={arab:.0%} | SA datiyut={dat} acad={ac} others_arab={oth_arab:.0%}"))
        flags.sort(reverse=True)
        print(f"\n=== K{e}: {len(flags)} mis-geocode suspects ===")
        for _, sem, nm, ven, sa, k, reason in flags:
            print(f"  {str(nm)[:16]:16s} semel={sem} k={k:>4} SA {sa} | {ven[:40]!r}\n        {reason}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1:] or ["25"])
