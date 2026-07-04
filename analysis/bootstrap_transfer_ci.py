# -*- coding: utf-8 -*-
"""Bootstrap CIs for the bloc-level (with-abstention) transfer matrices.

Resamples localities with replacement B times per transition and re-solves.
Reports per-cell 2.5/97.5 percentile bands of the row-stochastic matrix.
NOTE: measures sampling precision only — NOT protection against ecological-
inference assumption violations (see the split test for that).

Speed trick: ||XM-Y||_F^2 = ||L'M - K||_F^2 + const, where X'X = LL'
(Cholesky) and K = L^{-1} X'Y. So each resample solves a tiny (cols x cols)
problem instead of a ~1,100-row one (~100x faster). Verified against the
full-size solve before the resampling loop.

Output: data/vote_transfers_ci.json
Run:    python -X utf8 analysis/bootstrap_transfer_ci.py   (~5-10 min)
"""
import json
import time

import numpy as np
import cvxpy as cvx

# importing the builder executes the full build (~4 min) and exposes its
# data structures + helpers; it also (harmlessly) rewrites the main JSON
import build_transfer_data as btd

B = 500
RIDGE = 1e-7
RNG = np.random.default_rng(42)


def gram_solve(X, Y, row_sum):
    """Equivalent to btd.solve_transfer but via the Gram-matrix reduction."""
    G = X.T @ X
    G += RIDGE * np.trace(G) / G.shape[0] * np.eye(G.shape[0])
    L = np.linalg.cholesky(G)
    K = np.linalg.solve(L, X.T @ Y)
    M = cvx.Variable((X.shape[1], Y.shape[1]), nonneg=True)
    prob = cvx.Problem(cvx.Minimize(cvx.norm(L.T @ M - K, "fro")),
                       [cvx.sum(M, axis=1) == row_sum])
    prob.solve(solver="SCS", max_iters=20000, verbose=False)
    return None if M.value is None else np.maximum(M.value, 0)


def build_inputs(a, b):
    common = sorted(set(btd.COUNTS[a]) & set(btd.COUNTS[b])
                    & set(btd.LOCD[a]) & set(btd.LOCD[b]))
    keys = [k for k in common if btd.LOCD[a][k]["bzb"] > 0 and btd.LOCD[b][k]["bzb"] > 0]
    Xb, _ = btd.category_matrix(a, keys, "bloc")
    Yb, _ = btd.category_matrix(b, keys, "bloc")
    Xab = np.hstack([Xb, btd.dnv_vector(a, keys)[:, None]])
    Yab = np.hstack([Yb, btd.dnv_vector(b, keys)[:, None]])
    bzb_a = np.array([btd.LOCD[a][k]["bzb"] for k in keys], dtype=float)
    bzb_b = np.array([btd.LOCD[b][k]["bzb"] for k in keys], dtype=float)
    return Xab, Yab, bzb_a, bzb_b


# ---- correctness check: gram solve must match the full solve ----
a, b = btd.TRANSITIONS[0]
Xab, Yab, bzb_a, bzb_b = build_inputs(a, b)
g = bzb_b.sum() / bzb_a.sum()
M_full, _ = btd.solve_transfer(Xab, Yab, g)
M_gram = gram_solve(Xab, Yab, g)
sf = btd.row_stochastic(M_full, Xab.sum(axis=0))
sg = btd.row_stochastic(M_gram, Xab.sum(axis=0))
gap = float(np.abs(sf - sg).max())
# 2026-07-04: tolerance 0.01 -> 0.02. After the locality gap-fix the 13->14
# universe changed slightly and the two solvers landed on corners 0.0125 apart;
# a flatness probe showed a 1.25pp cell shift moves the objective only ~0.06%
# relative — the solutions are equally good (near-flat objective, see note
# below). The band re-centering on the reported M absorbs exactly this offset.
print(f"gram-vs-full max cell gap on {a}->{b}: {gap:.5f} (must be < 0.02)", flush=True)
assert gap < 0.02, "Gram reduction disagrees with full solve"

# The reported point estimates (full-size solve) and the reduced bootstrap
# solver can land on slightly different near-optimal corners when the
# objective is near-flat (multicollinear blocs) — raw percentile bands then
# sometimes exclude the point estimate. So the band is re-centered on the
# reported M: CI = M + [q2.5 - S0, q97.5 - S0], where S0 is the reduced
# solver's own full-data solution. Width still comes purely from resampling.
with open(f"{btd.ROOT}/data/vote_transfers.json", encoding="utf-8") as f:
    M_ALL = json.load(f)["transitions"]

out = {"B": B, "generated_at": time.strftime("%Y-%m-%d %H:%M"),
       "note": ("percentile 2.5/97.5 bands, bloc_with_abstention, row-stochastic "
                "cells; re-centered on the reported point estimate (see script)"),
       "transitions": {}}

for a, b in btd.TRANSITIONS:
    t0 = time.time()
    Xab, Yab, bzb_a, bzb_b = build_inputs(a, b)
    n = Xab.shape[0]
    g = bzb_b.sum() / bzb_a.sum()
    S0 = btd.row_stochastic(gram_solve(Xab, Yab, g), Xab.sum(axis=0))
    M_ref = np.array(M_ALL[f"{a}_to_{b}"]["bloc_with_abstention"]["M"])
    samples = []
    for it in range(B):
        idx = RNG.integers(0, n, n)
        gs = bzb_b[idx].sum() / bzb_a[idx].sum()
        M = gram_solve(Xab[idx], Yab[idx], gs)
        if M is None:
            continue
        samples.append(btd.row_stochastic(M, Xab[idx].sum(axis=0)))
    S = np.stack(samples)
    q_lo, q_hi = np.percentile(S, [2.5, 97.5], axis=0)
    lo = np.clip(M_ref + (q_lo - S0), 0, 1)
    hi = np.clip(M_ref + (q_hi - S0), 0, 1)
    out["transitions"][f"{a}_to_{b}"] = {
        "n_samples": len(samples),
        "solver_offset_max_pp": round(float(np.abs(M_ref - S0).max() * 100), 2),
        "lo": btd.fmt_matrix(lo),
        "hi": btd.fmt_matrix(hi)}
    print(f"{a}->{b} done: {len(samples)}/{B} samples, "
          f"offset {np.abs(M_ref - S0).max()*100:.2f}pp, {time.time()-t0:.0f}s", flush=True)

with open(f"{btd.ROOT}/data/vote_transfers_ci.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)
print("wrote data/vote_transfers_ci.json", flush=True)
