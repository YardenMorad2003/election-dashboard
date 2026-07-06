# -*- coding: utf-8 -*-
"""
spotcheck_residence_estimate.py — §4 validation of the residence-estimate files:
named spot checks + apples-to-apples coherence (actual vs estimate on the SAME
voted-SA set). Read-only; run after build_residence_estimate.py.

Run: python -X utf8 analysis/spotcheck_residence_estimate.py
"""
import json, os, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

LAYERS = {"18": "statarea_2009.json", "19": "statarea_k19.json", "20": "statarea_k20.json",
          "21": "statarea_k21.json", "22": "statarea_k22.json", "23": "statarea_k23.json",
          "24": "statarea_k24.json", "25": "statarea_2022.json"}
DATIYUT_ORD = {"חילוני": 0, "מסורתי": 1, "דתי/ דתי מאוד": 2, "חרדי": 3}


def pearson(pairs):
    n = len(pairs)
    if n < 3: return None
    mx = sum(p[0] for p in pairs) / n; my = sum(p[1] for p in pairs) / n
    cov = sum((x - mx) * (y - my) for x, y in pairs)
    vx = sum((x - mx) ** 2 for x, _ in pairs); vy = sum((y - my) ** 2 for _, y in pairs)
    return cov / math.sqrt(vx * vy) if vx and vy else None


def city_stats(est, semel):
    """(n, min rh, max rh, winners) over estimate SAs of the given city semel"""
    rhs, winners = [], set()
    for sid, e in est.items():
        if int(sid) // 10000 == semel:
            rhs.append(e["blocs"]["rh"]); winners.add(e["winner"])
    return len(rhs), (min(rhs) if rhs else None), (max(rhs) if rhs else None), winners


for yr, lname in LAYERS.items():
    layer = json.load(open(os.path.join(DATA, lname), encoding="utf-8"))["areas"]
    est = json.load(open(os.path.join(DATA, f"statarea_estimate_k{yr}.json"), encoding="utf-8"))["areas"]

    # fair coherence: both corrs on the SAME voted∩estimated SA set
    pa, pe = [], []
    for sid, rec in layer.items():
        if not (rec.get("valid") and rec.get("blocs") and sid in est):
            continue
        c = rec.get("census") or {}
        if yr in ("18", "19", "20"):
            x = (c.get("religion") or {}).get("arab")
            if x is None: continue
            x = -x
        else:
            if c.get("religion") != "יהודים": continue
            x = DATIYUT_ORD.get(c.get("datiyut"))
            if x is None: continue
        pa.append((x, rec["blocs"]["rh"]))
        pe.append((x, est[sid]["blocs"]["rh"]))
    print(f"\n== K{yr}: fair coherence on n={len(pa)} voted SAs: "
          f"actual {pearson(pa):.3f} -> est {pearson(pe):.3f}")

    # named spot checks
    for label, semel in [("Bnei Brak (6100)", 6100), ("Umm al-Fahm (2710)", 2710)]:
        n, lo, hi, winners = city_stats(est, semel)
        print(f"  {label}: n={n} rh {lo}..{hi} winners={sorted(winners)}")
    for label, sid in [("TA coast 50000511", "50000511"),
                       ("Herzliya 122", "64000122"), ("Herzliya 133", "64000133"),
                       ("Kfar Saba 424", "69000424")]:
        e = est.get(sid)
        a = layer.get(sid) or {}
        act = f"actual rh {a['blocs']['rh']}" if a.get("blocs") else "actual: no ballots"
        if e:
            print(f"  {label}: est rh {e['blocs']['rh']} winner {e['winner']} "
                  f"(donors {e['n_donors']}, {e['valid_est']:,} votes) | {act}")
        else:
            print(f"  {label}: NOT in estimate | {act}")
