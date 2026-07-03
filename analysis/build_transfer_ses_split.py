# -*- coding: utf-8 -*-
"""SES-stratified vote-transfer matrices (Phase 3 companion to build_transfer_data.py).

Jewish-sector localities (arab_pct < 50 in election A, same rule as the Phase 1
split test) are cut into LOW / MID / HIGH education terciles — %academics from
the census panel (demographics_panel.json), interpolated to the year of election
B, with tercile cut-points weighted by election-A registered voters so each
stratum holds roughly a third of the Jewish electorate. A transfer matrix (bloc
level, with abstention, rows sum to per-stratum electorate growth) is solved per
stratum per transition.

Answers "WHO transfers": e.g. did the 24->25 opposition_right collapse to the
right come from low- or high-education localities.

Same caveats as Phase 1 (ecological, constancy assumption); tercile membership
is time-varying by design (current SES at each transition).

Run: python -X utf8 analysis/build_transfer_ses_split.py  (~2-4 min)
Output: data/vote_transfers_ses.json
"""
import json
import re
import sys
import time

import numpy as np
import cvxpy as cvx

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:/Users/yarde/Downloads/election-dashboard-extracted/election-dashboard-main"

TRANSITIONS = [(str(a), str(a + 1)) for a in range(13, 25)]
BLOCS = ["right", "haredi", "center", "left", "arab", "opposition_right"]
ARAB_SPLIT_PCT = 50.0
MIN_SHARE_SUM, MAX_SHARE_SUM = 50.0, 150.0
COUNT_ROW_TOL = 0.25
STRATA = ["low", "mid", "high"]
STRATA_HE = {"low": "שליש תחתון (השכלה)", "mid": "שליש אמצעי", "high": "שליש עליון (השכלה)"}


def load(name):
    with open(f"{ROOT}/data/{name}", encoding="utf-8") as f:
        return json.load(f)


FIN = {"ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ"}


def norm(s):
    s = re.sub(r"\([^)]*\)", "", str(s).strip())
    for ch in ['"', "״", "'", "׳"]:
        s = s.replace(ch, "")
    s = re.sub(r"[\s\-–־]+", "", s)
    s = "".join(FIN.get(c, c) for c in s)
    return s.replace("יי", "י").replace("וו", "ו")


# ---------- load (same prep as build_transfer_data.py) ----------
pnat = load("parties_national.json")
pbl = load("parties_by_locality.json")
loc = load("localities.json")
demo = load("demographics_panel.json")

YEARS = sorted(set(pnat) & set(pbl), key=int)
YEAR_OF = {k: pnat[k]["year"] for k in pnat}
CODE_BLOC = {k: {it["code"]: it["bloc"] for it in pnat[k]["party_list"]} for k in YEARS}

LOCD = {k: {} for k in YEARS}
for x in loc:
    key = norm(x["name"])
    for k, d in x.get("data", {}).items():
        if k not in LOCD:
            continue
        kv = d.get("kosher_votes") or 0
        if kv <= 0:
            continue
        cur = LOCD[k].get(key)
        if cur is None or kv > cur["kosher"]:
            LOCD[k][key] = {"kosher": kv, "bzb": d.get("bzb") or 0,
                            "voters": d.get("voters") or 0,
                            "arab_pct": d.get("arab_pct")}

K17_INTERP = 0
for key, d in LOCD.get("17", {}).items():
    if d["bzb"]:
        continue
    b16 = LOCD.get("16", {}).get(key, {}).get("bzb") or 0
    b18 = LOCD.get("18", {}).get(key, {}).get("bzb") or 0
    if b16 and b18:
        d["bzb"] = (b16 + b18) / 2
    elif b16 or b18:
        d["bzb"] = b16 or b18
    if d["bzb"]:
        K17_INTERP += 1
        d["bzb"] = max(d["bzb"], d["voters"])

COUNTS = {}
for k in YEARS:
    rows = {}
    for locname, d in pbl[k].items():
        if "מעטפות" in locname:
            continue
        vals = {c: v for c, v in d.items() if isinstance(v, (int, float)) and v > 0}
        s = sum(vals.values())
        if s <= 0:
            continue
        key = norm(locname)
        ld = LOCD[k].get(key)
        if s > MAX_SHARE_SUM:
            if ld and abs(s - ld["kosher"]) / max(ld["kosher"], 1) > COUNT_ROW_TOL:
                continue
            counts = dict(vals)
        elif s >= MIN_SHARE_SUM:
            if ld is None:
                continue
            counts = {c: v / 100.0 * ld["kosher"] for c, v in vals.items()}
        else:
            continue
        if key in rows and sum(rows[key].values()) >= sum(counts.values()):
            continue
        rows[key] = counts
    COUNTS[k] = rows


def category_matrix(k, keys):
    cb = CODE_BLOC[k]
    cols = BLOCS + ["other"]
    idx = {b: i for i, b in enumerate(cols)}
    out = np.zeros((len(keys), len(cols)))
    for r, key in enumerate(keys):
        for c, v in COUNTS[k][key].items():
            out[r, idx.get(cb.get(c, "other"), idx["other"])] += v
    return out, cols


def dnv_vector(k, keys):
    return np.array([max((LOCD[k][key]["bzb"] or 0) - (LOCD[k][key]["voters"] or 0), 0.0)
                     for key in keys])


def solve_transfer(X, Y, row_sum):
    M = cvx.Variable((X.shape[1], Y.shape[1]), nonneg=True)
    prob = cvx.Problem(cvx.Minimize(cvx.norm(X @ M - Y, "fro")),
                       [cvx.sum(M, axis=1) == row_sum])
    prob.solve(solver="SCS", max_iters=20000, verbose=False)
    if M.value is None:
        return None, None
    Mv = np.maximum(M.value, 0)
    resid = ((Y - X @ Mv) ** 2).sum()
    tot = ((Y - Y.mean(axis=0)) ** 2).sum()
    return Mv, 1 - resid / tot


def row_stochastic(M, source_votes=None):
    s = M.sum(axis=1, keepdims=True)
    out = M / np.where(s > 0, s, 1)
    if source_votes is not None:
        out[np.asarray(source_votes) <= 0] = 0.0
    return out


def fmt_matrix(M, digits=4):
    return [[round(float(v), digits) for v in row] for row in M]


# ---------- census %academics, interpolated (norm-name keyed) ----------
CPTS = [("1972", 1972), ("1983", 1983), ("1995", 1995), ("2008", 2008), ("2022", 2022)]
ACAD = {}                       # norm(name) -> list[(year, acad)]
for dname, rec in demo["census"].items():
    pts = [(y, rec[k]["acad"]) for k, y in CPTS if k in rec and "acad" in rec[k]]
    if len(pts) >= 2:
        ACAD[norm(dname)] = pts


def acad_at(key, year):
    pts = ACAD.get(key)
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return float(np.interp(min(max(year, xs[0]), xs[-1]), xs, ys))


def wquantile(vals, wts, q):
    idx = np.argsort(vals)
    v, w = np.asarray(vals, float)[idx], np.asarray(wts, float)[idx]
    cw = np.cumsum(w) - 0.5 * w
    return float(np.interp(q * w.sum(), cw, v))


# ---------- main ----------
out = {"generated_at": time.strftime("%Y-%m-%d %H:%M"), "blocs": BLOCS,
       "strata": STRATA, "strata_labels_he": STRATA_HE, "transitions": {}}
BIDX = {b: i for i, b in enumerate(BLOCS + ["other", "dnv"])}
print(f"{'trans':>8} {'nJ':>4} {'cens%':>6} {'cut1':>5} {'cut2':>5} "
      f"{'R2 low':>7} {'R2 mid':>7} {'R2 high':>8}   headline flows")

for a, b in TRANSITIONS:
    common = sorted(set(COUNTS[a]) & set(COUNTS[b]) & set(LOCD[a]) & set(LOCD[b]))
    keys = [k for k in common if LOCD[a][k]["bzb"] > 0 and LOCD[b][k]["bzb"] > 0]
    jew = [k for k in keys if (LOCD[a][k]["arab_pct"] or 0) < ARAB_SPLIT_PCT]

    yr_b = YEAR_OF[b]
    xac = {k: acad_at(k, yr_b) for k in jew}
    covered = [k for k in jew if xac[k] is not None]
    cov_bzb = sum(LOCD[a][k]["bzb"] for k in covered)
    jew_bzb = sum(LOCD[a][k]["bzb"] for k in jew)

    vals = [xac[k] for k in covered]
    wts = [LOCD[a][k]["bzb"] for k in covered]
    c1, c2 = wquantile(vals, wts, 1/3), wquantile(vals, wts, 2/3)
    strata_keys = {
        "low":  [k for k in covered if xac[k] <= c1],
        "mid":  [k for k in covered if c1 < xac[k] <= c2],
        "high": [k for k in covered if xac[k] > c2],
    }

    Xb_all, _ = category_matrix(a, keys)
    Yb_all, _ = category_matrix(b, keys)
    dnv_a, dnv_b = dnv_vector(a, keys), dnv_vector(b, keys)
    Xab = np.hstack([Xb_all, dnv_a[:, None]])
    Yab = np.hstack([Yb_all, dnv_b[:, None]])
    kidx = {k: i for i, k in enumerate(keys)}

    tout = {"from": {"k": a, "year": YEAR_OF[a]}, "to": {"k": b, "year": yr_b},
            "bloc_labels": BLOCS + ["other", "dnv"],
            "acad_cutpoints": [round(c1, 2), round(c2, 2)],
            "census_coverage_of_jewish_bzb": round(cov_bzb / jew_bzb, 4),
            "k17_bzb_interpolated": "17" in (a, b),
            "strata": {}}
    r2s = {}
    for s in STRATA:
        idxs = [kidx[k] for k in strata_keys[s]]
        Xs, Ys = Xab[idxs], Yab[idxs]
        gs = (sum(LOCD[b][k]["bzb"] for k in strata_keys[s])
              / sum(LOCD[a][k]["bzb"] for k in strata_keys[s]))
        Ms, r2 = solve_transfer(Xs, Ys, gs)
        r2s[s] = r2
        src = Xs.sum(axis=0)
        tout["strata"][s] = None if Ms is None else {
            "n": len(idxs), "r2": round(float(r2), 4),
            "electorate_growth": round(gs, 4),
            "M": fmt_matrix(row_stochastic(Ms, src)),
            "source_votes": [round(float(v)) for v in src],
            "acad_range": [round(min(xac[k] for k in strata_keys[s]), 1),
                           round(max(xac[k] for k in strata_keys[s]), 1)]}
    out["transitions"][f"{a}_to_{b}"] = tout

    # headline: biggest low-vs-high divergence among meaningful flows
    heads = []
    if all(tout["strata"][s] for s in STRATA):
        Ml = np.array(tout["strata"]["low"]["M"])
        Mh = np.array(tout["strata"]["high"]["M"])
        srcl = np.array(tout["strata"]["low"]["source_votes"], float)
        for i in range(len(BIDX)):
            if srcl[i] < 5000:
                continue
            for j in range(len(BIDX)):
                dl, dh = Ml[i, j], Mh[i, j]
                if max(dl, dh) > 0.10 and abs(dl - dh) > 0.10:
                    heads.append((abs(dl - dh), i, j, dl, dh))
        heads.sort(reverse=True)
    lbl = list(BIDX)
    htxt = "; ".join(f"{lbl[i]}->{lbl[j]} L{dl*100:.0f}/H{dh*100:.0f}"
                     for _, i, j, dl, dh in heads[:3])
    print(f"{a}->{b:>3} {len(jew):>4} {cov_bzb/jew_bzb*100:>5.1f}% {c1:>5.1f} {c2:>5.1f} "
          f"{(r2s['low'] or 0):>7.4f} {(r2s['mid'] or 0):>7.4f} {(r2s['high'] or 0):>8.4f}   {htxt}")

with open(f"{ROOT}/data/vote_transfers_ses.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)
print("\nwrote data/vote_transfers_ses.json")
