# -*- coding: utf-8 -*-
"""Party-system metrics per election K13-K25, from data already in the repo:

  - ENP (effective number of parties, Laakso-Taagepera 1/sum(s^2)):
      votes  — over the Knesset-represented lists in parties_national.json,
               shares renormalized (sub-threshold lists absent: 0.3-5.9%/yr,
               biases ENP_votes slightly DOWN; documented)
      seats  — exact (seats/120)
  - Pedersen volatility (0.5 * sum |share_t - share_{t-1}|):
      party  — over the 38 canonical party lines of party_analysis.json
               (verified 1:1 with the national lists per election; mergers/
               splits count as exit+entry per the standard Pedersen convention)
      bloc   — over the 6 dashboard blocs + residual, from core.json
  - PSNS (party-system nationalization score, Jones-Mainwaring):
      per party, 1 - weighted Gini of its locality vote shares (weights =
      locality kosher votes), aggregated across parties weighted by national
      share. Locality-aggregate, not kalpi - absolute level reads high;
      the TREND is the meaningful part.

Output: data/party_system.json (~8 KB). Run: python -X utf8 analysis/build_party_system.py (~5s)

Trap handled: parties_by_locality has raw-COUNT rows (19 in K15 + 3 documented
in K23-25) where share-sum > 150 — converted to shares of their own sum, same
rule as build_transfer_data.py.
"""
import json
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:/Users/yarde/Downloads/election-dashboard-extracted/election-dashboard-main"

def load(f): return json.load(open(f"{ROOT}/data/{f}", encoding="utf-8"))

PN = load("parties_national.json")
PA = load("party_analysis.json")
PBL = load("parties_by_locality.json")
CORE = load("core.json")
LOC = load("localities.json")

KS = [str(k) for k in range(13, 26)]
YEAR_OF = PA["meta"]["year_of"]
BLOCS = ["right", "haredi", "center", "left", "arab", "opposition_right"]

kosher = {}          # k -> locality name -> kosher votes
for x in LOC:
    for k, d in x["data"].items():
        kv = d.get("kosher_votes")
        if kv:
            kosher.setdefault(k, {})[x["name"]] = kv


def weighted_gini(x, w):
    x, w = np.asarray(x, float), np.asarray(w, float)
    o = np.argsort(x)
    x, w = x[o], w[o]
    cw = np.cumsum(w)
    # G = sum_i f_i * (S_{i-1} + S_i) trick
    s = np.cumsum(w * x)
    if s[-1] <= 0: return None
    f = w / cw[-1]
    S = s / s[-1]
    S_prev = np.concatenate([[0.0], S[:-1]])
    return float(1 - np.sum(f * (S_prev + S)))


series = []
for k in KS:
    e = PN[k]
    nat = e["national"]                       # party code -> % of valid votes
    seats = e["seats"]
    listed = sum(nat.values())

    # --- ENP ---
    sh = np.array(list(nat.values())) / listed
    enp_votes = float(1 / np.sum(sh ** 2))
    ss = np.array([v for v in seats.values() if v]) / 120
    enp_seats = float(1 / np.sum(ss ** 2))

    # --- PSNS ---
    pbl = PBL.get(k, {})
    kv = kosher.get(k, {})
    pns_rows = []
    for code, share_nat in nat.items():
        xs, ws = [], []
        for loc_name, row in pbl.items():
            w = kv.get(loc_name)
            if not w or code not in row: continue
            vals = row
            tot = sum(v for v in vals.values() if v)
            v = vals[code] or 0
            if tot > 150:                      # raw-count row -> convert to share
                v = 100 * v / tot if tot else 0
            xs.append(v); ws.append(w)
        if len(xs) < 100: continue
        g = weighted_gini(xs, ws)
        if g is None: continue
        pns_rows.append({"code": code, "name": next((p["name"] for p in e["party_list"] if p["code"] == code), code),
                         "share": share_nat, "pns": round(1 - g, 4)})
    psns = round(sum(r["share"] * r["pns"] for r in pns_rows) /
                 sum(r["share"] for r in pns_rows), 4) if pns_rows else None
    pns_rows.sort(key=lambda r: -r["pns"])

    # full per-party snapshot for the by-election drill-down
    bloc_of = {p["code"]: p["bloc"] for p in e["party_list"]}
    pns_of = {r["code"]: r["pns"] for r in pns_rows}
    parties = sorted(({"code": c, "name": next((p["name"] for p in e["party_list"] if p["code"] == c), c),
                       "bloc": bloc_of.get(c, "other"), "share": round(v, 2),
                       "seats": seats.get(c, 0), "pns": pns_of.get(c)}
                      for c, v in nat.items()), key=lambda r: -r["share"])

    largest = max(nat.items(), key=lambda t: t[1])
    series.append({
        "k": k, "year": YEAR_OF[k],
        "n_lists": len(nat), "listed_share": round(listed, 1),
        "enp_votes": round(enp_votes, 2), "enp_seats": round(enp_seats, 2),
        "psns": psns,
        "pns_top": [{"name": r["name"], "pns": r["pns"]} for r in pns_rows[:3]],
        "pns_bottom": [{"name": r["name"], "pns": r["pns"]} for r in pns_rows[-3:]],
        "parties": parties,
        "largest_party": {"name": next((p["name"] for p in e["party_list"] if p["code"] == largest[0]), largest[0]),
                          "share": largest[1]},
    })

# --- Pedersen volatility ---
traj = {}                                     # k -> canonical code -> vote_pct
for p in PA["parties"]:
    for t in p["trajectory"]:
        if t.get("vote_pct") is not None:
            traj.setdefault(t["k"], {})[p["code"]] = t["vote_pct"]

nb = CORE["national_blocs"]
for i, k in enumerate(KS):
    entry = series[i]
    if i == 0:
        entry["volatility_party"] = entry["volatility_bloc"] = None
        continue
    kp = KS[i - 1]
    # party level (canonical lines; absent = 0)
    codes = set(traj.get(k, {})) | set(traj.get(kp, {}))
    vp = 0.5 * sum(abs(traj.get(k, {}).get(c, 0) - traj.get(kp, {}).get(c, 0)) for c in codes)
    entry["volatility_party"] = round(vp, 1)
    # bloc level (+ residual so micro-party churn counts once)
    b1, b0 = nb.get(k, {}), nb.get(kp, {})
    if b1 and b0:
        vb = 0.5 * sum(abs((b1.get(b) or 0) - (b0.get(b) or 0)) for b in BLOCS)
        r1 = 100 - sum(b1.get(b) or 0 for b in BLOCS)
        r0 = 100 - sum(b0.get(b) or 0 for b in BLOCS)
        vb += 0.5 * abs(r1 - r0)
        entry["volatility_bloc"] = round(vb, 1)
    else:
        entry["volatility_bloc"] = None

OUT = {
    "meta": {
        "built": "2026-07-02",
        "notes": [
            "ENP_votes over Knesset-represented lists only, shares renormalized (sub-threshold lists 0.3-5.9%/election missing -> slight downward bias); ENP_seats exact",
            "Pedersen party volatility over the canonical party lines of party_analysis.json - joint lists / splits count as exit+entry (standard convention, inflates merger years)",
            "PSNS = Jones-Mainwaring: share-weighted mean over parties of (1 - vote-weighted Gini of locality shares); locality-aggregate so levels read high vs kalpi-based scores - compare over time, not across studies",
            "K15/K23-25 raw-count locality rows converted to shares (share-sum>150 rule)",
        ],
    },
    "series": series,
}
with open(f"{ROOT}/data/party_system.json", "w", encoding="utf-8") as fh:
    json.dump(OUT, fh, ensure_ascii=False, separators=(",", ":"))

print(f"{'k':>3} {'year':>5} {'ENPv':>5} {'ENPs':>5} {'volP':>5} {'volB':>5} {'PSNS':>6}  largest")
for s in series:
    print(f"{s['k']:>3} {s['year']:>5} {s['enp_votes']:>5} {s['enp_seats']:>5} "
          f"{str(s['volatility_party']):>5} {str(s['volatility_bloc']):>5} {str(s['psns']):>6}  "
          f"{s['largest_party']['name']} {s['largest_party']['share']}%")
print("wrote data/party_system.json")
