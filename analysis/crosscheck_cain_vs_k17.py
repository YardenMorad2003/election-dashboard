# -*- coding: utf-8 -*-
"""
crosscheck_cain_vs_k17.py — systematic, API-free cross-validation of Cain's
back-propagated K18 (2009) venue coordinates against the period-true K17
(2006) address geocodes.

Join: K18 venue-precise ballots -> K17 ballots by (semel, ballot number)
(one-step back-propagation, ~96% stable). For each K18 VENUE (aggregating its
ballots), compare Cain's coordinate to the median K17 address coordinate.

A venue is suspect only if >= 2 of its joined ballots agree on a distance
> 1.5 km (single-ballot mismatches are usually 2006->2009 renumbering noise,
not geocode errors). Output is a report for human verification — fixes still
go through the web-search -> address -> PIP loop into station_coord_fixes.json.

Run: python -X utf8 analysis/crosscheck_cain_vs_k17.py
"""
import csv
import json
import math
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAP = os.path.join(HERE, "statarea_inputs")
EM = r"C:\Users\yarde\elections-merge\data"
CACHE = os.path.join(SNAP, "k17_address_geocodes.json")
GERESH = "'׳״‘’“”\"`"
KM = 1.5


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


def dist_km(a, b):
    dy = (a[0] - b[0]) * 111.0
    dx = (a[1] - b[1]) * 111.0 * math.cos(math.radians(a[0]))
    return math.hypot(dx, dy)


def main():
    cache = json.load(open(CACHE, encoding="utf-8"))
    name2sem = {}
    for r in csv.DictReader(open(rf"{EM}\knesset16_ballots.csv", encoding="utf-8-sig")):
        sm = str(iv(r["סמל ישוב"]))
        if sm != "0":
            name2sem[norm(r["שם ישוב"])] = sm
    for r in csv.DictReader(open(rf"{EM}\knesset25_ballots.csv", encoding="utf-8-sig")):
        name2sem.setdefault(norm(r["שם ישוב"]), r["סמל ישוב"].strip())

    pn = json.load(open(os.path.join(ROOT, "data", "parties_national.json"), encoding="utf-8"))
    bloc17 = {p["code"]: p["bloc"] for p in pn["17"]["party_list"]}
    bloc18 = {p["code"]: p["bloc"] for p in pn["18"]["party_list"]}

    def profile(row, bloc_of):
        k = iv(row["כשרים"])
        if k <= 0:
            return None
        agg = defaultdict(int)
        for code, b in bloc_of.items():
            if code in row:
                agg[b] += iv(row[code])
        return {b: agg[b] / k for b in ("haredi", "arab", "right", "left", "center")}

    # K17: (semel, ballot int) -> (address coord, vote profile)
    k17 = {}
    for r in csv.DictReader(open(rf"{EM}\knesset17_ballots.csv", encoding="utf-8-sig")):
        if r["שם ישוב"].strip() == "מעטפות כפולות":
            continue
        sm = name2sem.get(norm(r["שם ישוב"]))
        if not sm:
            continue
        addr = " ".join((r["כתובת"] or "").split())
        c = cache.get(f"{sm}|{addr}")
        if c and c.get("src") != "none":
            k17[(sm, iv(r["מספר קלפי"]))] = ((c["lat"], c["lng"]), profile(r, bloc17))

    # K18 per-ballot vote profiles
    prof18 = {}
    for r in csv.DictReader(open(rf"{EM}\knesset18_ballots.csv", encoding="utf-8-sig")):
        sm = r["סמל ישוב"].strip()
        if sm == "0":
            continue
        try:
            b10 = int(round(float(r["סמל קלפי"]) * 10))
        except (ValueError, TypeError):
            continue
        prof18[(sm, b10)] = profile(r, bloc18)

    # K18 venue-precise ballots + venue names
    b18 = json.load(open(rf"{EM}\ballot_locations_18.json", encoding="utf-8"))["ballot_to_location"]
    name = {r.get("semel"): r["name"]
            for r in json.load(open(os.path.join(ROOT, "data", "localities.json"), encoding="utf-8"))
            if r.get("semel")}
    def prof_match(p18, p17):
        """Same electorate? Haredi/Arab shares are the sharpest fingerprints."""
        if not p18 or not p17:
            return None
        return (abs(p18["haredi"] - p17["haredi"]) < 0.15
                and abs(p18["arab"] - p17["arab"]) < 0.15
                and abs((p18["right"] + p18["haredi"]) - (p17["right"] + p17["haredi"])) < 0.20)

    V = defaultdict(lambda: {"cain": None, "d": [], "k": 0, "match_far": 0, "mismatch_far": 0})
    joined = comp = 0
    for r in csv.DictReader(open(os.path.join(SNAP, "ballot_coords_18.csv"), encoding="utf-8-sig")):
        if r["coord_src"] != "venue" or not r["lat"]:
            continue
        sm = r["semel"]
        try:
            b10 = int(round(float(r["ballot"]) * 10))  # K17 numbers are K18's x10
        except ValueError:
            continue
        comp += 1
        hit17 = k17.get((sm, b10))
        if not hit17:
            continue
        joined += 1
        ll17, p17 = hit17
        ven = b18.get(f"{sm}:{r['ballot']}")
        if not ven:
            continue
        d = V[(sm, ven)]
        d["cain"] = (float(r["lat"]), float(r["lng"]))
        dd = dist_km(d["cain"], ll17)
        d["d"].append(dd)
        d["k"] += iv(r["kosher"])
        if dd > KM:
            m = prof_match(prof18.get((sm, b10)), p17)
            if m is True:
                d["match_far"] += 1
                d.setdefault("alt", []).append(ll17)
            elif m is False:
                d["mismatch_far"] += 1

    print(f"K18 venue-precise ballots: {comp:,}; joined to a K17 address coord: {joined:,} ({100*joined/comp:.0f}%)")
    sus, noise, scattered = [], 0, 0
    agree = 0
    for (sm, ven), d in V.items():
        far = [x for x in d["d"] if x > KM]
        if len(d["d"]) >= 2 and len(far) >= 2 and len(far) >= 0.6 * len(d["d"]):
            # profile check separates real mis-geocodes from 2006->2009 renumbering
            if d["match_far"] >= 2 and d["match_far"] > d["mismatch_far"]:
                # coherence: a real mis-geocode's 2006 addresses cluster at ONE
                # alternative location; renumbering noise scatters
                alt = d.get("alt", [])
                spread = max((dist_km(a, b) for i, a in enumerate(alt) for b in alt[i + 1:]),
                             default=0.0)
                if spread <= 1.0:
                    sus.append((sorted(d["d"])[len(d["d"]) // 2], sm, ven, d["k"],
                                len(d["d"]), len(far), d["match_far"], alt[0]))
                else:
                    scattered += 1
            else:
                noise += 1
        elif d["d"] and max(d["d"]) <= KM:
            agree += 1
    print(f"venues compared: {len(V):,}; fully agreeing (<= {KM} km): {agree:,} "
          f"({100*agree/len(V):.1f}%)")
    print(f"far-disagreeing venues: {len(sus) + noise + scattered} -> "
          f"COHERENT same-electorate suspects (likely real mis-geocodes): {len(sus)}; "
          f"scattered-alternative (join noise): {scattered}; profile-mismatched (renumbering): {noise}")
    sus.sort(reverse=True)
    for med, sm, ven, k, n, nf, mf, alt in sus[:40]:
        print(f"  {str(name.get(iv(sm), sm))[:14]:14s} semel={sm} k={k:>5} med={med:5.1f}km "
              f"({nf}/{n} far, {mf} same-elec) alt=({alt[0]:.5f},{alt[1]:.5f}) | {ven[:36]!r}")
    out_path = os.path.join(SNAP, "crosscheck_suspects.json")
    json.dump([{"semel": sm, "venue": ven, "kosher": k, "med_km": round(med, 2),
                "n_joined": n, "n_far": nf, "n_same_elec": mf,
                "alt": [round(alt[0], 6), round(alt[1], 6)]}
               for med, sm, ven, k, n, nf, mf, alt in sus],
              open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"wrote {out_path} ({len(sus)} suspects)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
