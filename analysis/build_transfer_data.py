# -*- coding: utf-8 -*-
"""Build vote-transfer matrices between consecutive Knesset elections (K13-K25).

Method: constrained least squares (ecological inference, Goodman-lineage).
For each transition solve  min ||X @ M - Y||_F  s.t.  M >= 0, rows sum to g,
where X/Y are locality x category vote-count matrices and g is electorate
growth (registered-voter ratio) so a growing roll doesn't force fake flows.

Method credit: Harel Cain (kolot-nodedim / elections-vote-transfer) and
Itamar Mushkin. Clean-room reimplementation (his repo is CC BY-NC-SA).

Solved per transition:
  * bloc level (6 dashboard blocs + other + didn't-vote), with & without abstention
  * party level (party_list codes + other + didn't-vote), with abstention
  * split test: Arab-sector vs Jewish-sector localities solved separately
  * validation vs Cain's ballot-box-level matrices (K16+ where available)

Data notes (verified 2026-07-01):
  * parties_by_locality.json rows are usually shares (sum ~100); some rows
    carry RAW COUNTS instead (sum > 150, e.g. Tel Aviv-Yafo K15 = 217,641).
    Count rows are recovered as counts, not dropped.
  * counts = share/100 x kosher_votes via the conservative name normalizer
    (same as build_party_analysis.py) - fixes ~96 unmatched localities/yr
    (Bedouin tribes, K23+ CEC renaming) that undercounted Arab parties.
  * didn't-vote = bzb - voters (both in localities.json).

Output: data/vote_transfers.json (all transitions, matrices row-stochastic).
Run:    python -X utf8 analysis/build_transfer_data.py
"""
import json
import re
import sys
import time

import numpy as np
import cvxpy as cvx

ROOT = r"C:/Users/yarde/Downloads/election-dashboard-extracted/election-dashboard-main"
CAIN_DIR = (r"C:\Users\yarde\AppData\Local\Temp\claude\C--Users-yarde"
            r"\cf0d69de-f48d-44c0-84e4-9c7905f35404\scratchpad"
            r"\elections-vote-transfer\elections-vote-transfer-master\data")

TRANSITIONS = [(str(a), str(a + 1)) for a in range(13, 25)]
BLOCS = ["right", "haredi", "center", "left", "arab", "opposition_right"]
BLOC_HE = {"right": "ימין", "haredi": "חרדים", "center": "מרכז", "left": "שמאל",
           "arab": "ערבים", "opposition_right": "ימין אופוזיציוני",
           "other": "אחר", "dnv": "לא הצביעו"}
ARAB_SPLIT_PCT = 50.0   # arab bloc share in election A that defines the Arab sector
MIN_SHARE_SUM, MAX_SHARE_SUM = 50.0, 150.0  # outside => raw-count row (>) or drop (<)
COUNT_ROW_TOL = 0.25    # count rows must be within 25% of kosher_votes when known


def load(name):
    with open(f"{ROOT}/data/{name}", encoding="utf-8") as f:
        return json.load(f)


# ---------- conservative Hebrew name normalizer (same as build_party_analysis.py) ----------
FIN = {"ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ"}


def norm(s):
    s = re.sub(r"\([^)]*\)", "", str(s).strip())
    for ch in ['"', "״", "'", "׳"]:
        s = s.replace(ch, "")
    s = re.sub(r"[\s\-–־]+", "", s)
    s = "".join(FIN.get(c, c) for c in s)
    return s.replace("יי", "י").replace("וו", "ו")


# ---------- load ----------
pnat = load("parties_national.json")
pbl = load("parties_by_locality.json")
loc = load("localities.json")

YEARS = sorted(set(pnat) & set(pbl), key=int)
YEAR_OF = {k: pnat[k]["year"] for k in pnat}
CODE_BLOC = {k: {it["code"]: it["bloc"] for it in pnat[k]["party_list"]} for k in YEARS}
CODE_NAME = {k: {it["code"]: it["name"] for it in pnat[k]["party_list"]} for k in YEARS}

# locality-level electorate data keyed by normalized name (dedupe by max kosher)
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

# K17 (2006) ships with no bzb (registered voters) — same CEC gap Cain hit.
# Locality identity is stable here (unlike ballot numbers), so estimate each
# locality's 2006 roll as the mean of its K16 (2003) and K18 (2009) rolls,
# which bracket 2006 symmetrically. Transitions touching K17 are flagged
# "k17_bzb_interpolated" in the output; their abstention numbers are estimates.
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
        # roll can't be smaller than actual voters
        d["bzb"] = max(d["bzb"], d["voters"])


# ---------- build per-election count tables: normalized name -> {code: votes} ----------
COUNTS = {}
DIAG = {}
for k in YEARS:
    rows, n_share, n_count, n_drop, n_nokosher = {}, 0, 0, 0, 0
    for locname, d in pbl[k].items():
        if "מעטפות" in locname:
            continue
        vals = {c: v for c, v in d.items() if isinstance(v, (int, float)) and v > 0}
        s = sum(vals.values())
        if s <= 0:
            continue
        key = norm(locname)
        ld = LOCD[k].get(key)
        if s > MAX_SHARE_SUM:                      # raw-count row
            if ld and abs(s - ld["kosher"]) / max(ld["kosher"], 1) > COUNT_ROW_TOL:
                n_drop += 1
                continue                            # counts contradict known total
            counts = dict(vals)
            n_count += 1
        elif s >= MIN_SHARE_SUM:                    # share row
            if ld is None:
                n_nokosher += 1
                continue
            counts = {c: v / 100.0 * ld["kosher"] for c, v in vals.items()}
            n_share += 1
        else:
            n_drop += 1
            continue
        # collision: keep the row with more total votes (spelling-variant dups)
        if key in rows and sum(rows[key].values()) >= sum(counts.values()):
            continue
        rows[key] = counts
    COUNTS[k] = rows
    DIAG[k] = dict(share=n_share, count=n_count, dropped=n_drop, no_kosher=n_nokosher)


def category_matrix(k, keys, mode, party_cols=None):
    """Build count matrix for localities `keys` in election k.

    mode 'bloc' -> columns BLOCS + other (+dnv appended by caller)
    mode 'party'-> columns party_cols + other
    """
    cb = CODE_BLOC[k]
    if mode == "bloc":
        cols = BLOCS + ["other"]
        idx = {b: i for i, b in enumerate(cols)}
        out = np.zeros((len(keys), len(cols)))
        for r, key in enumerate(keys):
            for c, v in COUNTS[k][key].items():
                out[r, idx.get(cb.get(c, "other"), idx["other"])] += v
        return out, cols
    cols = list(party_cols) + ["other"]
    idx = {c: i for i, c in enumerate(cols)}
    out = np.zeros((len(keys), len(cols)))
    for r, key in enumerate(keys):
        for c, v in COUNTS[k][key].items():
            out[r, idx[c] if c in idx else idx["other"]] += v
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
    """Normalize rows to sum 1; zero out rows with no source votes (the solver
    returns arbitrary values for empty rows — they carry zero actual votes)."""
    s = M.sum(axis=1, keepdims=True)
    out = M / np.where(s > 0, s, 1)
    if source_votes is not None:
        out[np.asarray(source_votes) <= 0] = 0.0
    return out


def fmt_matrix(M, digits=4):
    return [[round(float(v), digits) for v in row] for row in M]


# ---------- Cain validation helper ----------
def cain_bloc_matrix(a, b):
    """Bloc-aggregated row-stochastic matrix from Cain's ballot-level output."""
    try:
        with open(f"{CAIN_DIR}/transfer_{a}_to_{b}.json", encoding="utf-8") as f:
            T = json.load(f)
    except OSError:
        return None
    cba, cbb = CODE_BLOC[a], CODE_BLOC[b]
    n = len(BLOCS)
    F = np.zeros((n, n))
    bidx = {bl: i for i, bl in enumerate(BLOCS)}
    for t in T["transfers"]:
        sb = cba.get(t["source_symbol"])
        tb = cbb.get(t["target_symbol"])
        if sb in bidx and tb in bidx:
            F[bidx[sb], bidx[tb]] += t["votes"]
    return row_stochastic(F), F


# ---------- main loop ----------
all_out = {"generated_at": time.strftime("%Y-%m-%d %H:%M"), "blocs": BLOCS,
           "bloc_labels_he": BLOC_HE, "transitions": {}}
print(f"{'trans':>8} {'nloc':>5} {'grow':>6} {'R2 abst':>8} {'R2 noab':>8} "
      f"{'R2 party':>8} {'nA/nJ':>9} {'R2 A':>6} {'R2 J':>6} {'cain r':>7} {'cainΔpp':>8}")

for a, b in TRANSITIONS:
    common = sorted(set(COUNTS[a]) & set(COUNTS[b])
                    & set(LOCD[a]) & set(LOCD[b]))
    keys = [key for key in common
            if LOCD[a][key]["bzb"] > 0 and LOCD[b][key]["bzb"] > 0]
    bzb_a = sum(LOCD[a][key]["bzb"] for key in keys)
    bzb_b = sum(LOCD[b][key]["bzb"] for key in keys)
    growth = bzb_b / bzb_a

    Xb, cols_a = category_matrix(a, keys, "bloc")
    Yb, cols_b = category_matrix(b, keys, "bloc")
    dnv_a, dnv_b = dnv_vector(a, keys), dnv_vector(b, keys)

    # --- bloc level, with abstention ---
    Xab = np.hstack([Xb, dnv_a[:, None]])
    Yab = np.hstack([Yb, dnv_b[:, None]])
    M_abst, r2_abst = solve_transfer(Xab, Yab, growth)
    src_tot_abst = Xab.sum(axis=0)

    # --- bloc level, no abstention (valid-vote growth as row sum) ---
    g_valid = Yb.sum() / Xb.sum()
    M_noab, r2_noab = solve_transfer(Xb, Yb, g_valid)

    # --- party level, with abstention ---
    pa = [c for c in CODE_BLOC[a]]
    pb_ = [c for c in CODE_BLOC[b]]
    Xp, pcols_a = category_matrix(a, keys, "party", pa)
    Yp, pcols_b = category_matrix(b, keys, "party", pb_)
    Xpa = np.hstack([Xp, dnv_a[:, None]])
    Ypa = np.hstack([Yp, dnv_b[:, None]])
    M_party, r2_party = solve_transfer(Xpa, Ypa, growth)
    src_tot_party = Xpa.sum(axis=0)

    # --- split test: Arab vs Jewish sector (bloc level, with abstention) ---
    arab_keys = [i for i, key in enumerate(keys)
                 if (LOCD[a][key]["arab_pct"] or 0) >= ARAB_SPLIT_PCT]
    jew_keys = [i for i, key in enumerate(keys) if i not in set(arab_keys)]
    split = {}
    for label, rows_idx in [("arab", arab_keys), ("jewish", jew_keys)]:
        if len(rows_idx) < 30:
            split[label] = None
            continue
        Xs, Ys = Xab[rows_idx], Yab[rows_idx]
        gs = (sum(LOCD[b][keys[i]]["bzb"] for i in rows_idx)
              / sum(LOCD[a][keys[i]]["bzb"] for i in rows_idx))
        Ms, r2s = solve_transfer(Xs, Ys, gs)
        split[label] = None if Ms is None else {
            "n": len(rows_idx), "r2": round(float(r2s), 4),
            "M": fmt_matrix(row_stochastic(Ms, Xs.sum(axis=0))),
            "source_votes": [round(float(v)) for v in Xs.sum(axis=0)]}

    # --- Cain validation (bloc, no abstention, row-stochastic) ---
    cain_r = cain_diff = None
    cain = cain_bloc_matrix(a, b)
    if cain is not None and M_noab is not None:
        Mc, Fc = cain
        ours = row_stochastic(M_noab[:len(BLOCS), :len(BLOCS)])
        w = Fc.sum(axis=1)                      # weight rows by Cain source votes
        mask = w > 0
        oc, cc = ours[mask].ravel(), Mc[mask].ravel()
        if len(oc) > 3 and oc.std() > 0 and cc.std() > 0:
            cain_r = float(np.corrcoef(oc, cc)[0, 1])
            # weighted mean |diff| per CELL (weights = Cain source votes per row,
            # spread evenly over the row's cells, normalized to sum to 1)
            ww = np.repeat(w[mask] / w[mask].sum(), ours.shape[1]) / ours.shape[1]
            cain_diff = float((np.abs(oc - cc) * ww).sum() * 100)

    key_t = f"{a}_to_{b}"
    all_out["transitions"][key_t] = {
        "from": {"k": a, "year": YEAR_OF[a]}, "to": {"k": b, "year": YEAR_OF[b]},
        "n_localities": len(keys), "electorate_growth": round(growth, 4),
        "bloc_labels": cols_a + ["dnv"],
        "bloc_with_abstention": None if M_abst is None else {
            "r2": round(float(r2_abst), 4),
            "M": fmt_matrix(row_stochastic(M_abst, src_tot_abst)),
            "source_votes": [round(float(v)) for v in src_tot_abst]},
        "bloc_no_abstention": None if M_noab is None else {
            "r2": round(float(r2_noab), 4),
            "M": fmt_matrix(row_stochastic(M_noab, Xb.sum(axis=0))),
            "source_votes": [round(float(v)) for v in Xb.sum(axis=0)]},
        "party_with_abstention": None if M_party is None else {
            "from_labels": [CODE_NAME[a].get(c, c) for c in pcols_a] + ["לא הצביעו"],
            "to_labels": [CODE_NAME[b].get(c, c) for c in pcols_b] + ["לא הצביעו"],
            "from_blocs": [CODE_BLOC[a].get(c, "other") for c in pcols_a] + ["dnv"],
            "to_blocs": [CODE_BLOC[b].get(c, "other") for c in pcols_b] + ["dnv"],
            "r2": round(float(r2_party), 4),
            "M": fmt_matrix(row_stochastic(M_party, src_tot_party)),
            "source_votes": [round(float(v)) for v in src_tot_party]},
        "split_test": split,
        "cain_validation": None if cain_r is None else {
            "pearson_r": round(cain_r, 4), "weighted_mean_abs_diff_pp": round(cain_diff, 2)},
        "k17_bzb_interpolated": "17" in (a, b),
    }

    nA = len(arab_keys)
    print(f"{a}->{b:>3} {len(keys):>5} {growth:>6.3f} "
          f"{(r2_abst or 0):>8.4f} {(r2_noab or 0):>8.4f} {(r2_party or 0):>8.4f} "
          f"{nA:>4}/{len(jew_keys):<4} "
          f"{(split['arab']['r2'] if split['arab'] else float('nan')):>6.3f} "
          f"{(split['jewish']['r2'] if split['jewish'] else float('nan')):>6.3f} "
          f"{(cain_r if cain_r is not None else float('nan')):>7.3f} "
          f"{(cain_diff if cain_diff is not None else float('nan')):>8.2f}")

with open(f"{ROOT}/data/vote_transfers.json", "w", encoding="utf-8") as f:
    json.dump(all_out, f, ensure_ascii=False)

print("\nrow-recovery diagnostics per election "
      "(share rows / count rows recovered / dropped / share-no-kosher):")
for k in YEARS:
    d = DIAG[k]
    print(f"  K{k}: {d['share']:>5} / {d['count']:>3} / {d['dropped']:>3} / {d['no_kosher']:>3}")
print("\nwrote data/vote_transfers.json")
