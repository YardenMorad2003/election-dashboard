# -*- coding: utf-8 -*-
"""
audit_k26_locations.py — second look at the K26 polling-site coordinates
(k26_ballot_coords.csv), using the Ministry of Education school registry
(statarea_inputs/moe_registry_cache.json: name + coordinate + accuracy) as an
independent reference, plus the vote-coherence test of sweep_venue_anomalies.py.

Per site (semel + venue + address):
  reg    nearest in-city registry school whose name contains the venue's core name
         (accuracy 'גבוהה*' only, generic names skipped), distance d0 from our point
  hood   vote-weighted right-Haredi share of the 6 nearest other sites <= 1.5 km

Verdicts
  OK       registry school <= 0.35 km from our point
  CONFIRM  nearest registry school >= 0.5 km away, the venue name is specific
           (exactly one in-city registry cluster), and EITHER the site is in a weak
           coordinate tier (geocode*/k25_rikuz/k25_fuzzy/k25_addr_amb) OR moving it
           improves vote coherence by >= 15 pt with residual <= 20 pt
  REVIEW   registry disagrees but evidence is ambiguous (several same-name schools, or
           a verified K25 point with no coherence gain)  -> listed, NOT changed
  -        no registry match (not a school / generic name)

Output: analysis/k26_location_audit.txt, statarea_inputs/k26_audit_confirms.json
Run: python -X utf8 analysis/audit_k26_locations.py
"""
import collections
import csv
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAP = os.path.join(HERE, "statarea_inputs")
EM = r"C:\Users\yarde\elections-merge\data"
sys.path.insert(0, HERE)
from build_venue_dots import norm, canon_ballot  # noqa: E402

KX = 0.845
WEAK = ("geocode", "geocode_street", "geocode_venue", "k25_rikuz", "k25_fuzzy", "k25_addr_amb")
STOP = set("""בי ס ביה בית ספר יסודי תיכון חט ב חטיבת ביניים ממ ד ממלכתי דתי ע ש עש ביס בנין בניין
אולפנת אולפנא אולפנה גן ילדים גני מקיף עירוני מרכז קהילתי מתנ מתנס מועדון אשכול פיס חדש חדשה חינוך
ישיבת ישיבה תלמוד תורה ת בנות בנים לבנות לבנים כללי אזורי על שם החדש הישן אגף מבנה שלוחה קריית קרית
כניסה ראשית צפונית דרומית אולם ספורט סניף שכ שכונת רח רחוב הספר לשעבר מזרחית מערבית""".split())
# norm() collapses יי->י and וו->ו, so the stop words must be collapsed the same way
# (otherwise 'ביניים' never matches and stays in the core name)
STOP |= {norm(w) for w in STOP}

def dkm(a, b):
    return math.hypot((a[1] - b[1]) * 111 * KX, (a[0] - b[0]) * 111)


def name_key(v):
    """(core name, sibling letter). Sibling schools differ only by a trailing letter
    ('רוגוזין א' / 'רוגוזין ב', 'מקיף ג'): dropping it merges different campuses
    (the Kiryat Ata miss, 2026-11-21), so it is kept as a separate key part."""
    toks = norm(v).split()
    suf = ""
    if len(toks) >= 2 and len(toks[-1]) == 1 and "א" <= toks[-1] <= "ת":
        suf = toks[-1]
        toks = toks[:-1]
    extra = {"חטב", "חטיבה", "חטיבת", "מקיף", "הביניים"}
    core = " ".join(t for t in toks if t not in STOP and t not in extra and len(t) >= 2 and not t.isdigit())
    return core, suf


def core_name(v):
    return " ".join(t for t in norm(v).split() if t not in STOP and len(t) >= 2 and not t.isdigit())


def main():
    pn = json.load(open(os.path.join(ROOT, "data", "parties_national.json"), encoding="utf-8"))["26"]
    rh_codes = {p["code"] for p in pn["party_list"] if p["bloc"] in ("right", "haredi")}
    votes = {}
    with open(os.path.join(EM, "knesset26_ballots.csv"), encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            valid = int(r["כשרים"] or 0)
            votes[(r["סמל ישוב"].strip(), canon_ballot(r["קלפי"].strip()))] = (
                valid, sum(int(r[c] or 0) for c in rh_codes if c in r))
    sites = {}
    for r in csv.DictReader(open(os.path.join(SNAP, "k26_ballot_coords.csv"), encoding="utf-8-sig")):
        if not r["lat"]:
            continue
        k = (r["semel"], r["venue"], r["addr"])
        s = sites.setdefault(k, {"sem": r["semel"], "venue": r["venue"], "addr": r["addr"], "sett": r["sett"],
                                 "pt": (float(r["lat"]), float(r["lng"])), "src": r["coord_src"],
                                 "valid": 0, "rhv": 0, "ballots": []})
        v, rv = votes.get((r["semel"], r["ballot"]), (0, 0))
        s["valid"] += v; s["rhv"] += rv; s["ballots"].append(r["ballot"])
    by_city = collections.defaultdict(list)
    for s in sites.values():
        s["rh"] = 100 * s["rhv"] / s["valid"] if s["valid"] else None
        by_city[s["sem"]].append(s)

    def hood(sem, pt, me):
        near = sorted(((dkm(pt, o["pt"]), i, o) for i, o in enumerate(by_city[sem])
                       if o is not me and o["rh"] is not None and dkm(o["pt"], me["pt"]) > 0.02),
                      key=lambda t: t[:2])
        sel = [o for d, _, o in near[:6] if d <= 1.5]
        if len(sel) < 3:
            return None
        return sum(o["rh"] * o["valid"] for o in sel) / sum(o["valid"] for o in sel)

    # city extent from the 2022 SA geometry (bbox + margin)
    bbox = {}
    for f in json.load(open(os.path.join(ROOT, "data", "statarea_2022_geo.json"), encoding="utf-8"))["features"]:
        sem = str(f["properties"]["semel"])
        g = f["geometry"]
        rings = g["coordinates"] if g["type"] == "Polygon" else [r for p in g["coordinates"] for r in p]
        xs = [x for r in rings for x, _ in r]; ys = [y for r in rings for _, y in r]
        b = bbox.get(sem)
        nb = (min(ys), max(ys), min(xs), max(xs))
        bbox[sem] = nb if not b else (min(b[0], nb[0]), max(b[1], nb[1]), min(b[2], nb[2]), max(b[3], nb[3]))
    reg = []
    for r in json.load(open(os.path.join(SNAP, "moe_registry_cache.json"), encoding="utf-8")):
        if "גבוהה" not in str(r.get("acc", "")):
            continue
        try:
            reg.append((norm(r["name"]), r["name"], float(r["lat"]), float(r["lng"])))
        except (TypeError, ValueError):
            pass

    def candidates(sem, core):
        b = bbox.get(sem)
        if not b or len(core) < 3:
            return []
        m = 0.005
        return [(nm, la, ln) for nn, nm, la, ln in reg
                if b[0] - m <= la <= b[1] + m and b[2] - m <= ln <= b[3] + m and core in nn]

    rows, confirms = [], {}
    stat = collections.Counter()
    for s in sites.values():
        core = core_name(s["venue"])
        cands = candidates(s["sem"], core)
        tier = "weak" if s["src"] in WEAK else "inherited"
        if not cands:
            stat[(tier, "no-registry")] += 1
            continue
        d = sorted((dkm(s["pt"], (la, ln)), nm, la, ln) for nm, la, ln in cands)
        d0 = d[0][0]
        if d0 <= 0.35:
            stat[(tier, "OK")] += 1
            continue
        if d0 < 0.5:
            stat[(tier, "near")] += 1
            continue
        # cluster candidates: do they all point at one place?
        one_place = all(dkm((d[0][2], d[0][3]), (la, ln)) <= 0.3 for _, _, la, ln in d)
        cur_h = hood(s["sem"], s["pt"], s)
        dest_h = hood(s["sem"], (d[0][2], d[0][3]), s)
        cur_res = abs(s["rh"] - cur_h) if (cur_h is not None and s["rh"] is not None) else None
        dest_res = abs(s["rh"] - dest_h) if (dest_h is not None and s["rh"] is not None) else None
        gain = (cur_res - dest_res) if (cur_res is not None and dest_res is not None) else None
        coherent = gain is not None and gain >= 15 and dest_res <= 20
        worse = gain is not None and gain <= -15
        if one_place and ((tier == "weak" and not worse) or coherent):
            verdict = "CONFIRM"
            confirms.setdefault(s["sem"], {})[f"{s['venue']}@@{s['addr']}"] = [round(d[0][2], 6), round(d[0][3], 6)]
        else:
            verdict = "REVIEW"
        stat[(tier, verdict)] += 1
        rows.append((verdict, tier, s, d0, d[0][1], len(d), one_place, cur_res, dest_res))

    rows.sort(key=lambda t: (t[0], t[1], -t[2]["valid"]))
    L = [f"K26 location audit vs MOE school registry: {len(sites)} located sites", ""]
    for k in sorted(stat):
        L.append(f"  {k[0]:<10} {k[1]:<12} {stat[k]:>5}")
    L.append("")
    for verdict, tier, s, d0, nm, n, one, cr, dr in rows:
        f = lambda x: "-" if x is None else f"{x:.0f}"
        L.append(f"{verdict:<7} {tier:<9} {s['src']:<14} sem {s['sem']:<5} {s['sett']} | {s['venue']} | {s['addr']} | "
                 f"v={s['valid']} rh={f(s['rh'])} | registry '{nm}' {d0:.2f} km away (cands {n}, one place {one}) | "
                 f"resid now {f(cr)} -> there {f(dr)}")
    open(os.path.join(HERE, "k26_location_audit.txt"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    json.dump(confirms, open(os.path.join(SNAP, "k26_audit_confirms.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n".join(L[:14]))
    print("rows", len(rows))


if __name__ == "__main__":
    main()
