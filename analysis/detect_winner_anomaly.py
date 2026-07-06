# -*- coding: utf-8 -*-
"""National sweep: SAs whose bloc profile contradicts their same-city neighborhood.
Channel #4 (winner/bloc-vs-neighbors), which the religious-contradiction detectors miss."""
import json, io, sys, csv, math, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = r"C:\Users\yarde\Downloads\election-dashboard-extracted\election-dashboard-main"
EM = r"C:\Users\yarde\elections-merge\data"
OUT = r"C:\Users\yarde\AppData\Local\Temp\claude\C--Users-yarde\cac22b10-e30f-4c26-8097-a59c76e120c8\scratchpad\national_flags.json"

KX = 0.845
def dkm(a, b):
    return math.hypot((a[1]-b[1])*111*KX, (a[0]-b[0])*111)

# centroids from 2022 geo
g = json.load(open(BASE + r"\data\statarea_2022_geo.json", encoding="utf-8"))
cent = {}
sem_of = {}
for f in g["features"]:
    pts = []
    def collect(c):
        if isinstance(c[0], (int, float)): pts.append(c)
        else:
            for x in c: collect(x)
    collect(f["geometry"]["coordinates"])
    sid = str(f["properties"]["id"])
    cent[sid] = (sum(p[1] for p in pts)/len(pts), sum(p[0] for p in pts)/len(pts))
    sem_of[sid] = str(f["properties"]["semel"])

flags = {}   # (sid) -> flag record (keep worst year)
for yr, lf in (("25", "statarea_2022.json"), ("24", "statarea_k24.json")):
    d = json.load(open(BASE + "\\data\\" + lf, encoding="utf-8"))["areas"]
    by_sem = collections.defaultdict(list)
    for sid, a in d.items():
        if a.get("valid") and sid in cent:
            by_sem[sem_of[sid]].append(sid)
    for sem, sids in by_sem.items():
        if len(sids) < 4:
            continue
        for sid in sids:
            me = d[sid]
            c = cent[sid]
            neigh = [(dkm(c, cent[o]), o) for o in sids if o != sid]
            close = [o for dist, o in neigh if dist <= 1.2]
            if len(close) < 2:
                close = [o for dist, o in sorted(neigh)[:3] if dist <= 2.5]
            if len(close) < 2:
                continue
            wsum = sum(d[o]["valid"] for o in close)
            hood_rh = sum(d[o]["blocs"]["rh"] * d[o]["valid"] for o in close) / wsum
            delta = me["blocs"]["rh"] - hood_rh
            if abs(delta) >= 25:
                key = sid
                rec = flags.get(key)
                score = abs(delta) * me["valid"]
                if not rec or score > rec["score"]:
                    flags[key] = {"sid": sid, "semel": sem, "yr": yr, "valid": me["valid"],
                                  "nb": me.get("n_ballots"), "rh": me["blocs"]["rh"],
                                  "hood_rh": round(hood_rh, 1), "delta": round(delta, 1),
                                  "winner": me.get("winner"),
                                  "datiyut": (me.get("census") or {}).get("datiyut"),
                                  "loc": me.get("loc"), "score": round(score)}

out = sorted(flags.values(), key=lambda r: -r["score"])
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(out)} flagged SAs (K25∪K24, |Δrh vs ≤1.2km same-city hood| ≥ 25)")
for r in out[:40]:
    print(f"  {r['sid']} {r['loc'] or r['semel']:<14} K{r['yr']} v={r['valid']:>5} nb={r['nb']} "
          f"rh={r['rh']:>5} hood={r['hood_rh']:>5} Δ={r['delta']:>6} win={r['winner']} dat={r['datiyut']}")
print("... (full list in national_flags.json)" if len(out) > 40 else "")
