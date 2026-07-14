# -*- coding: utf-8 -*-
"""
build_ipp_transfers.py — third evidence layer for the vote-transfers page: bloc-level
transition matrices from the Israel Polarization Panel (IPP; Gidron, Sheffer & Mor,
Harvard Dataverse). TRUE PANEL: the same respondents report their vote after each
election — no recall bias anywhere (the INES layer is recall-based except 21->22).

Covers the four adjacent transitions the panel spans: 21_to_22, 22_to_23, 23_to_24,
24_to_25. Jewish voting-age sample only (the panel's design) — the arab row exists but
is tiny and gets the UI's thin-row warning. Unweighted (the file ships no weights);
row-normalization absorbs most of the panel's level skew. Blocs follow the site
convention per election (K24: Yamina, New Hope and Yisrael Beiteinu are
opposition_right).

Abstention: rows/cols include dnv from the wave voted-flags. For the 2020 election the
flag lives in wave 7 (asked ~2.5 months later) while the vote lives in wave 6 — noted.
Output schema mirrors data/survey_transfers.json so transfers.html renders it with the
same machinery.

Writes: data/ipp_transfers.json
Run:    python -X utf8 analysis/build_ipp_transfers.py   (~1 min, bootstrap B=1000)
"""
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IPP = r"C:\Users\yarde\Downloads\dataverse_files (12)_extracted"
CSV_CANDIDATES = [
    os.path.join(IPP, "IPP_wide_19_3_23.csv"),
    r"C:\Users\yarde\AppData\Local\Temp\claude\C--Users-yarde\c591bfac-d4d5-4811-9184-0ca81596f7ab\scratchpad\dataverse12\IPP_wide_19_3_23.csv",
]
CSV = next(p for p in CSV_CANDIDATES if os.path.exists(p))

CATS = ["right", "haredi", "center", "left", "arab", "opposition_right", "other", "dnv"]
B = 1000
rng = np.random.default_rng(25)

DROP = {"Blank vote", "Other/Don't Know"}
BLOC = {
    # K21 April 2019 (w3). Kulanu = right (K21 official-results bloc).
    "w3": {"Likud": "right", "Habayit Hayehudi": "right", "Hayamin Hahadash": "right",
           "Zehut": "right", "Kulanu": "right", "Shas": "haredi", "Yahadut Hatorah": "haredi",
           "Kahol Lavan": "center", "Gesher": "center", "Haavoda": "left", "Meretz": "left",
           "Balad-Raam": "arab", "Hadash-Taal": "arab", "Israel Beitenu": "opposition_right",
           "Other party": "other"},
    # K22 September 2019 (w5)
    "w5": {"Likud": "right", "Yemina": "right", "Otzma Yehudit": "right", "Shas": "haredi",
           "Yahadut Hatorah": "haredi", "Kahol Lavan": "center", "Haavoda-Gesher": "left",
           "Hamahane Hademokrati": "left", "Joint List": "arab",
           "Israel Beitenu": "opposition_right", "Other party": "other"},
    # K23 March 2020 (w6)
    "w6": {"Likud": "right", "Yemina": "right", "Otzma Yehudit": "right", "Shas": "haredi",
           "Yahadut Hatorah": "haredi", "Kahol Lavan": "center",
           "Haavoda-Gesher-Meretz": "left", "Joint List": "arab",
           "Israel Beitenu": "opposition_right", "Other party": "other"},
    # K24 March 2021 (w9). Site convention: Yamina, New Hope, YB = opposition_right.
    "w9": {"Likud": "right", "Hazionut Hadatit": "right", "Shas": "haredi",
           "Yahadut Hatorah": "haredi", "Yesh Atid": "center", "Kahol Lavan": "center",
           "Hacalcalit Hahadasha": "center", "Haavoda": "left", "Meretz": "left",
           "Joint List": "arab", "Yemina": "opposition_right",
           "Tikvah Hadasha": "opposition_right", "Israel Beitenu": "opposition_right"},
    # K25 November 2022 (w11)
    "w11": {"Likud": "right", "Hazionut Hadatit": "right", "Habayit Hayehudi": "right",
            "Shas": "haredi", "Yahadut Hatorah": "haredi", "Yesh Atid": "center",
            "Hamahane Hamamlahti": "center", "Haavoda": "left", "Meretz": "left",
            "Hadash-Taal": "arab", "Raam": "arab", "Balad-Raam": "arab",
            "Israel Beitenu": "opposition_right"},
}
TRANS = [  # key, (row vote var, row voted-flag), (col vote var, col voted-flag), label
    ("21_to_22", ("w3", "w3_voted_2019_apr"), ("w5", "w5_voted_2019_sep"), "w3->w5"),
    ("22_to_23", ("w5", "w5_voted_2019_sep"), ("w6", "w7_voted_2020"), "w5->w6"),
    ("23_to_24", ("w6", "w7_voted_2020"), ("w9", "w9_voted_2021"), "w6->w9"),
    ("24_to_25", ("w9", "w9_voted_2021"), ("w11", "w11_voted_2022"), "w9->w11"),
]

df = pd.read_csv(CSV, low_memory=False)


def assign(w, flag):
    """Per respondent: bloc string, 'dnv', or None (unknown/ineligible/blank)."""
    vote = df[f"{w}_vote_choice"]
    fl = df[flag].astype(str)
    out = []
    unmapped = set()
    for v, f in zip(vote, fl):
        if isinstance(v, str) and v not in DROP:
            b = BLOC[w].get(v)
            if b is None:
                unmapped.add(v)
            out.append(b)
        elif f.startswith("No"):
            out.append("dnv")
        else:
            out.append(None)          # missing wave, ineligible, blank, DK
    if unmapped:
        raise SystemExit(f"{w}: unmapped party values {unmapped}")
    return pd.Series(out, index=df.index)


def matrices(rows, cols, cats):
    idx = {c: i for i, c in enumerate(cats)}
    k = len(cats)
    C = np.zeros((k, k))
    for a, b in zip(rows, cols):
        C[idx[a], idx[b]] += 1
    rn = C.sum(axis=1)
    M = np.divide(C, rn[:, None], out=np.zeros_like(C), where=rn[:, None] > 0)
    return C, M, rn


def boot_ci(pairs, cats):
    k = len(cats)
    arr = np.array([( {c: i for i, c in enumerate(cats)}[a], {c: i for i, c in enumerate(cats)}[b]) for a, b in pairs])
    n = len(arr)
    sims = np.zeros((B, k, k))
    for t in range(B):
        pick = arr[rng.integers(0, n, n)]
        C = np.zeros((k, k))
        np.add.at(C, (pick[:, 0], pick[:, 1]), 1)
        rn = C.sum(axis=1)
        sims[t] = np.divide(C, rn[:, None], out=np.zeros_like(C), where=rn[:, None] > 0)
    lo = np.percentile(sims, 2.5, axis=0)
    hi = np.percentile(sims, 97.5, axis=0)
    return lo, hi


ECO = json.load(open(os.path.join(ROOT, "data", "vote_transfers.json"), encoding="utf-8"))


def vs_eco(key, M, rn, cats, abst):
    t = ECO["transitions"].get(key)
    if not t:
        return None
    eset = t["bloc_with_abstention"] if abst else t["bloc_no_abstention"]
    elabs = t["bloc_labels"] if abst else t["bloc_labels"][:-1]
    Me = np.array(eset["M"])
    rows = [c for c in cats if c in elabs and c != "other" and rn[cats.index(c)] >= 30]
    a, b, w, per = [], [], [], {}
    for c in rows:
        i, ie = cats.index(c), elabs.index(c)
        cols = [(j, elabs.index(cc)) for j, cc in enumerate(cats) if cc in elabs and cc != "other"]
        mi = np.array([M[i][j] for j, _ in cols])
        me = np.array([Me[ie][je] for _, je in cols])
        a += list(mi); b += list(me); w += [rn[i]] * len(cols)
        per[c] = {"n": int(rn[i]), "tv_pp": round(50 * float(np.abs(mi - me).sum()), 1)}
    if not a:
        return None
    a, b, w = np.array(a), np.array(b), np.array(w)
    r = float(np.corrcoef(a, b)[0, 1])
    mad = float(np.average(np.abs(a - b), weights=w) * 100)
    return {"pearson_r": round(r, 4), "weighted_mean_abs_diff_pp": round(mad, 2),
            "rows_compared": rows, "per_row": per}


out = {"generated_at": "2026-07-13", "B": B, "blocs": CATS[:-1], "categories": CATS,
       "note": ("Israel Polarization Panel (IPP): the SAME respondents report their vote after "
                "each election — true panel, no recall bias in any transition. Jewish voting-age "
                "sample only, unweighted (the panel ships no weights; row-normalization absorbs "
                "most of the level skew, and its gradients match INES 2022 closely). dnv from the "
                "wave voted-flags; for the 2020 election the flag was asked in the following wave. "
                "Blank/DK excluded. Treat as a third triangulation layer."),
       "transitions": {}}

for key, (wa, fa), (wb, fb), lbl in TRANS:
    ra, rb = assign(wa, fa), assign(wb, fb)
    both = ra.notna() & rb.notna()
    pa, pb = ra[both], rb[both]
    C, M, rn = matrices(pa, pb, CATS)
    lo, hi = boot_ci(list(zip(pa, pb)), CATS)
    vmask = (pa != "dnv") & (pb != "dnv")
    C7, M7, rn7 = matrices(pa[vmask], pb[vmask], CATS[:-1])
    lo7, hi7 = boot_ci(list(zip(pa[vmask], pb[vmask])), CATS[:-1])
    ent = {
        "wave": f"IPP {lbl}", "row_source": "post", "col_source": "post",
        "n": int(both.sum()), "weight": "none", "panel": True,
        "row_n": [int(x) for x in rn],
        "with_abstention": {"M": np.round(M, 4).tolist(), "lo": np.round(lo, 4).tolist(),
                            "hi": np.round(hi, 4).tolist()},
        "voters_only": {"M": np.round(M7, 4).tolist(), "lo": np.round(lo7, 4).tolist(),
                        "hi": np.round(hi7, 4).tolist()},
        "vs_ecological": {"with_abstention": vs_eco(key, M, rn, CATS, True),
                          "voters_only": vs_eco(key, M7, rn7, CATS[:-1], False)},
        "voters_only_n": int(vmask.sum()), "voters_only_col_source": "post",
    }
    out["transitions"][key] = ent
    ve = ent["vs_ecological"]["with_abstention"]
    print(f"{key}: n={ent['n']} voters-only n={ent['voters_only_n']} row_n={ent['row_n']}"
          f" | vs eco r={ve['pearson_r'] if ve else None} mad={ve['weighted_mean_abs_diff_pp'] if ve else None}pp")

path = os.path.join(ROOT, "data", "ipp_transfers.json")
json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False)
print("wrote", path, os.path.getsize(path), "bytes")
