# -*- coding: utf-8 -*-
"""Survey-side vote-transfer matrices from INES waves (Phase 2 of the
transfer project) — triangulates the ecological matrices in
data/vote_transfers.json against individual-level survey crosstabs.

For each K(a)->K(b) transition: weighted crosstab of recalled-vote-at-a x
current-vote-at-b from the INES wave fielded around election b, mapped to
the dashboard bloc taxonomy (right, haredi, center, left, arab,
opposition_right, other) + didn't-vote. Bloc assignment per election
matches parties_national.json exactly (e.g. Yisrael Beiteinu = right
through K20, opposition_right from K21; Kulanu = center at K20, right at
K21). Bootstrap CIs resample respondents (stratified for the two-sample
1996 wave).

K21->K22 is special: the 2019 INES file is a true April->September panel
(post-vote reported in both waves, no recall) — the anchor estimate. The
2020 wave adds a recall-chain estimate of the same transition
(recall-of-K21 x recall-of-K22), so panel-vs-recall quantifies recall bias
directly.

Codes 94-99 are mapped per wave-and-variable from the value labels, never
globally (the assignment varies): "didn't vote despite being eligible" ->
dnv; "wasn't eligible" -> excluded (new voters are not switchers);
undecided / refuse / DK / don't-remember / blank -> excluded.

Where the post-election vote variable has no didn't-vote code (2006 d6,
2009 q3, 2022 F2 were asked of voters only), the with-abstention variant
falls back to the intent variable (which has a "doesn't intend to vote"
code) and the voters-only variant uses the post variable; col_source in
the output says which was used.

Output: data/survey_transfers.json
Run:    python -X utf8 analysis/build_survey_transfers.py   (~1 min)
"""
import io
import json
import sys
import time

import numpy as np
import pandas as pd

ROOT = r"C:/Users/yarde/Downloads/election-dashboard-extracted/election-dashboard-main"
INES = r"C:/Users/yarde/Downloads/INES"

CATS = ["right", "haredi", "center", "left", "arab", "opposition_right", "other", "dnv"]
CIDX = {c: i for i, c in enumerate(CATS)}
DNV, OTHER, EX = "dnv", "other", None
B = 1000
RNG = np.random.default_rng(42)
ARAB_ELECTORATE_SHARE_1996 = 0.12   # pooling weight for the separate 1996 Arab sample

WARN = {}   # (wave, var, label) -> count, for unmapped labels

# Yisrael Beiteinu spelling varies by wave (beitenu/beiteinu/beytenu/beyteinu/
# beteinu) and its bloc changes at K21 — always splice IB() into per-var rules.
def IB(bloc):
    return [(p, bloc) for p in ("beitenu", "beiteinu", "beytenu", "beyteinu", "beteinu")]


def norm_label(v):
    s = str(v)
    for ch in "‎‏‪‫‬":
        s = s.replace(ch, "")
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.strip().lower()
    # strip a leading "12." / "12 " code prefix
    i = 0
    while i < len(s) and s[i].isdigit():
        i += 1
    if i and i < len(s) and s[i] in ". ":
        s = s[i + 1:].strip()
    elif i == len(s):
        return "__numeric__"
    try:                       # pure numerics like "31.0" -> stray unlabeled code
        float(s)
        return "__numeric__"
    except ValueError:
        pass
    return " ".join(s.split())


# --- shared tail rules: parties whose bloc never changes, then dnv/exclusions ---
COMMON = [
    ("likud", "right"), ("shas", "haredi"),
    ("yahadut", "haredi"), ("yahaduth", "haredi"), ("agudat", "haredi"), ("degel", "haredi"),
    ("meretz", "left"), ("labor", "left"), ("avoda", "left"), ("one israel", "left"),
    ("zionist union", "left"), ("democratic union", "left"), ("hademocrati", "left"),
    ("kahol", "center"), ("blue and white", "center"), ("blue & white", "center"),
    ("yesh atid", "center"), ("kadima", "center"),
    ("hadash", "arab"), ("balad", "arab"), ("joint list", "arab"), ("joint arab", "arab"),
    ("meshutefet", "arab"),
    ("ra'am", "arab"), ("raam", "arab"), ("ta'al", "arab"), ("taal", "arab"),
    ("united arab", "arab"), ("arab movement", "arab"), ("arab democratic", "arab"),
    ("progressive list", "arab"), ("progressive peace", "arab"), ("progressive alliance", "arab"),
    ("the arab list", "arab"), ("ma'an", "arab"),
    ("national religious", "right"), ("mafdal", "right"), ("moledet", "right"),
    ("tzomet", "right"), ("tehiya", "right"), ("habayit", "right"), ("bayit", "right"),
    ("otzma", "right"), ("herut", "right"), ("hazit leumit", "right"),
    ("tzionut hadatit", "right"), ("zionut hadatit", "right"), ("smotrich", "right"),
    ("left-wing party", "left"), ("party from the left", "left"),
    ("right-wing party", "right"), ("party from the right", "right"),
    ("center party", "center"), ("arab party", "arab"),
    ("center or", EX), ("right-wing or", EX),
    ("green", OTHER), ("ale yarok", OTHER), ("pirate", OTHER), ("na nach", OTHER),
    ("economi", OTHER),
    ("pensioner", "center"), ("gil (", "center"),
    ("other", OTHER), ("another", OTHER), ("acher", OTHER),
    # eligibility exclusions BEFORE the generic didn't-vote rule:
    ("ineligible", EX), ("wasn't eligible", EX), ("was not eligible", EX),
    ("did not have the right", EX), ("didn't have the right", EX), ("didn't had the right", EX),
    ("not eligible", EX),
    ("did not vote", DNV), ("didn't vote", DNV), ("will not vote", DNV),
    ("would not vote", DNV), ("not intend", DNV), ("doesn't intend", DNV),
    ("do not intend", DNV), ("not intending", DNV),
    ("refus", EX), ("undecided", EX), ("not decided", EX), ("no decision", EX),
    ("debating", EX), ("don't know", EX), ("do not know", EX), ("doesn't know", EX),
    ("dont know", EX), ("no answer", EX), ("no response", EX),
    ("remember", EX), ("blank", EX), ("empty", EX), ("__numeric__", EX),
]

# --- per-variable rules (run before COMMON; first match wins) ---
R = {
    # 1996 wave (K13 -> K14), Jewish + Arab files
    "1996:ccc23:j": [("religious leader", "haredi"), *IB("right"),
                     ("aliya", "right"), ("haderech", "center"), ("third way", "center")],
    "1996:ccc23:a": [("religious leader", "arab"), ("aliya", "right"),
                     ("haderech", "center"), ("third way", "center")],
    "1996:ccc37": [("a religious party", EX), ("aliya", "right"),
                   ("haderech", "center"), ("third way", "center")],
    # 1999 wave (K14 -> K15)
    "1999:c12": [("party of center", "center"), ("shinui", "center"), ("national unit", "right"),
                 *IB("right"), ("aliya", "right"),
                 ("one nation", "left"), ("haderech", "center"), ("third way", "center"),
                 ("pnina", OTHER), ("women", OTHER), ("veterans", OTHER)],
    "1999:c17": [("haderech", "center"), ("third way", "center"), ("aliya", "right"),
                 *IB("right")],
    # 2003 wave (K15 -> K16)
    "2003:b63": [("shinui", "center"), ("national union", "right"), ("am ehad", "left"),
                 ("aliya", "right"), ("israel acheret", OTHER), ("ahavat", OTHER)],
    "2003:b70": [("shinui", "center"), ("national union", "right"), ("am ehad", "left"),
                 ("aliya", "right"), *IB("right"),
                 ("center", "center"), ("third way", "center")],
    # 2006 wave (K16 -> K17), raw codes + value labels
    "2006:b73": [*IB("right"), ("ihud leumi", "right"), ("shinui", "center"),
                 ("hetz", "center"), ("tafnit", OTHER), ("zionut hadasha", OTHER),
                 ("daam", OTHER), ("lehem", OTHER)],
    "2006:d6": [*IB("right"), ("ihud leumi", "right"), ("shinui", "center"),
                ("hetz", "center"), ("tafnit", OTHER), ("war on banks", OTHER), ("lehem", OTHER)],
    "2006:c40": [("ihud leumi", "right"), ("shinui", "center"), ("am ehad", "left"),
                 ("aliya", "right"), ("bealiya", "right"), ("daam", OTHER)],
    # 2009 wave (K17 -> K18)
    "2009:v154": [*IB("right"), ("hayihud haleumi", "right"), ("memad", "left"),
                  ("new movement", "left")],
    "2009:q3": [*IB("right"), ("haihud haleumi", "right"), ("memad", "left"),
                ("new movement", "left")],
    "2009:v162": [*IB("right"), ("ihud leumi", "right"), ("yachad", "left"),
                  ("shinui", "center"), ("hetz", "center"), ("tafnit", OTHER)],
    # 2015 wave (K19 -> K20), raw codes + value labels
    "2015:v92": [("yachad", "haredi"), ("kulanu", "center"), *IB("right"),
                 ("hope for change", OTHER), ("u'bizchutan", OTHER)],
    "2015:after_v2": [("yachad", "haredi"), ("kulanu", "center"), *IB("right"),
                      ("hope for change", OTHER), ("u'bizchutan", OTHER)],
    "2015:v101": [("hatenuah", "left"), ("dor bonei", OTHER), ("am shalem", OTHER),
                  ("da'am", OTHER), ("eretz hadasha", OTHER), ("hayisraelim", OTHER),
                  ("hope for change", OTHER), ("power to influence", OTHER),
                  ("progressive liberal", OTHER)],
    # 2019 wave (K20 -> K21 + the K21 -> K22 panel)
    "2019:v108": [*IB("right"), ("kulanu", "center"), ("yachad", "haredi")],
    "2019:v2_after": [*IB("opposition_right"),
                      ("kulanu", "right"), ("union of right", "right"), ("new right", "right"),
                      ("zehut", "right"), ("gesher", "center")],
    "2019:D2": [*IB("opposition_right"),
                ("yamina", "right"), ("hayamin hameuchad", "right")],
    # 2020 wave (K22 -> K23 + recall chain for K21 -> K22)
    "2020:v508": [*IB("opposition_right"),
                  ("kulanu", "right"), ("union of right", "right"), ("new right", "right"),
                  ("zehut", "right"), ("gesher", "center")],
    "2020:v507": [*IB("opposition_right"),
                  ("yamina", "right"), ("hayamin hameuchad", "right")],
    "2020:E2_after": [*IB("opposition_right"), ("yamina", "right")],
    # 2021 wave (K23 -> K24)
    "2021:v610": [*IB("opposition_right"), ("yamina", "right")],
    "2021:F2": [*IB("opposition_right"), ("yamina", "opposition_right"),
                ("tikva hadasha", "opposition_right"), ("calcalit", OTHER)],
    # 2022 wave (K24 -> K25)
    "2022:v706": [*IB("opposition_right"), ("yamina", "opposition_right"),
                  ("tikva hadasha", "opposition_right"), ("national unity", "center"),
                  ("mamlakhti", "center")],
    "2022:F2": [*IB("opposition_right"), ("national unity", "center"),
                ("mamlakhti", "center")],
    "2022:v104": [*IB("opposition_right"), ("national unity", "center"),
                  ("mamlakhti", "center")],
}

# 2013 shipped its .dta without value labels; codes verified against the .por
# (scratchpad labels_2013.txt) and the actual K18/K19 results.
CODE_2013_V102 = {1: "center", 2: "right", 3: "left", 4: "right", 5: "right", 6: "haredi",
                  7: "haredi", 8: "left", 9: "right", 10: "left", 11: OTHER, 12: OTHER,
                  13: "center", 14: "right", 15: OTHER, 16: OTHER, 17: "arab", 18: "arab",
                  19: "arab", 20: OTHER, 21: OTHER, 81: "left", 82: "center", 83: "right",
                  84: EX, 85: EX, 86: EX, 87: "arab", 94: EX, 95: OTHER, 96: EX,
                  97: DNV, 98: EX, 99: EX}
CODE_2013_AV2 = {1: "right", 2: "left", 3: "left", 4: "center", 5: "right", 6: "haredi",
                 7: "haredi", 8: "left", 9: "center", 10: "right", 11: OTHER, 12: OTHER,
                 13: OTHER, 14: OTHER, 15: OTHER, 16: OTHER, 17: "arab", 18: "arab",
                 19: "arab", 81: "left", 82: "center", 83: "right", 87: "arab",
                 91: EX, 95: OTHER, 96: EX, 97: DNV, 98: DNV, 99: EX}
CODE_2013_AV2.update({c: OTHER for c in range(20, 34)})


def apply_rules(label, rules):
    s = norm_label(label)
    for pat, cat in rules:
        if pat in s:
            return cat
    for pat, cat in COMMON:
        if pat in s:
            return cat
    return "__UNMAPPED__"


def map_series(ser, rule_key, wave, code_map=None, value_labels=None):
    """Map a raw column to CATS / None(excluded). Returns object Series."""
    out = pd.Series(index=ser.index, dtype=object)
    if code_map is not None:
        for i, v in ser.items():
            if pd.isna(v):
                out[i] = EX
            else:
                out[i] = code_map.get(int(v), "__UNMAPPED__")
                if out[i] == "__UNMAPPED__":
                    WARN[(wave, rule_key, int(v))] = WARN.get((wave, rule_key, int(v)), 0) + 1
                    out[i] = EX
        return out
    rules = R.get(rule_key, [])
    cache = {}
    for i, v in ser.items():
        if pd.isna(v):
            out[i] = EX
            continue
        if value_labels is not None:
            v = value_labels.get(int(v), v)
        v = str(v)
        if v not in cache:
            cat = apply_rules(v, rules)
            if cat == "__UNMAPPED__":
                WARN[(wave, rule_key, v)] = 0
                cat = EX
            cache[v] = cat
        if cache[v] is EX and (wave, rule_key, v) in WARN:
            WARN[(wave, rule_key, v)] += 1
        out[i] = cache[v]
    return out


def read_wave(path, categoricals=True):
    if categoricals:
        return pd.read_stata(path), None
    df = pd.read_stata(path, convert_categoricals=False)
    with pd.io.stata.StataReader(path) as rd:
        vl = rd.value_labels()
    return df, vl


def pick_weight(df, mask, prefs):
    for w in prefs:
        if w in df.columns:
            cov = df.loc[mask, w].notna().mean()
            if cov >= 0.90:
                return w
    return None


def crosstab(ri, ci, w, ncat=8):
    T = np.zeros((ncat, ncat))
    np.add.at(T, (ri, ci), w)
    return T


def row_stochastic(T):
    s = T.sum(axis=1, keepdims=True)
    return T / np.where(s > 0, s, 1)


def fmt(M, d=4):
    return [[round(float(v), d) for v in row] for row in M]


def boot_cis(ri, ci, w, strata=None):
    """Percentile CIs for both variants from B respondent resamples."""
    n = len(ri)
    groups = [np.arange(n)] if strata is None else [np.where(strata == s)[0] for s in np.unique(strata)]
    S_ab, S_vo = [], []
    for _ in range(B):
        idx = np.concatenate([g[RNG.integers(0, len(g), len(g))] for g in groups])
        T = crosstab(ri[idx], ci[idx], w[idx])
        S_ab.append(row_stochastic(T))
        S_vo.append(row_stochastic(T[:7, :7]))
    lo_ab, hi_ab = np.percentile(S_ab, [2.5, 97.5], axis=0)
    lo_vo, hi_vo = np.percentile(S_vo, [2.5, 97.5], axis=0)
    return (lo_ab, hi_ab), (lo_vo, hi_vo)


def build_pair(df, row_var, col_var, wave, w_prefs, code_maps=None, vlabels=None,
               strata_col=None, strata_w=None, rule_suffix=""):
    """Returns dict with matrices for one (row_var x col_var) crosstab."""
    rk = f"{wave}:{row_var}{rule_suffix}"
    ck = f"{wave}:{col_var}{rule_suffix}"
    rmap = map_series(df[row_var], rk, wave,
                      code_map=(code_maps or {}).get(row_var),
                      value_labels=(vlabels or {}).get(row_var))
    cmap = map_series(df[col_var], ck, wave,
                      code_map=(code_maps or {}).get(col_var),
                      value_labels=(vlabels or {}).get(col_var))
    mask = rmap.notna() & cmap.notna()
    wname = pick_weight(df, mask, w_prefs or [])
    if wname:
        wt = df.loc[mask, wname].to_numpy(dtype=float)
        keep = ~np.isnan(wt)
    else:
        wt = np.ones(mask.sum())
        keep = np.ones(mask.sum(), bool)
    ri = rmap[mask].map(CIDX).to_numpy(dtype=int)[keep]
    ci = cmap[mask].map(CIDX).to_numpy(dtype=int)[keep]
    wt = wt[keep]
    strata = None
    if strata_col is not None:
        strata = df.loc[mask, strata_col].to_numpy()[keep]
        for s, share in strata_w.items():          # pool the separate samples
            m = strata == s
            if m.sum():
                wt[m] = wt[m] * share / wt[m].sum()
    T = crosstab(ri, ci, wt)
    (lo_ab, hi_ab), (lo_vo, hi_vo) = boot_cis(ri, ci, wt, strata)
    row_n = np.bincount(ri, minlength=8)
    return {"n": int(len(ri)), "weight": wname or "none",
            "row_n": [int(v) for v in row_n],
            "T": T,
            "with_abstention": {"M": row_stochastic(T), "lo": lo_ab, "hi": hi_ab},
            "voters_only": {"M": row_stochastic(T[:7, :7]), "lo": lo_vo, "hi": hi_vo}}


# ---------------- transition specs ----------------
def spec_1996():
    dj, _ = read_wave(f"{INES}/1996/1996j.dta")
    da, _ = read_wave(f"{INES}/1996/1996a.dta")
    dj["_s"], da["_s"] = "j", "a"
    df = pd.concat([dj[["ccc23", "ccc37", "_s"]], da[["ccc23", "ccc37", "_s"]]],
                   ignore_index=True)
    # per-sample rules for the current-vote var (the "religious leader" answer)
    rmap = map_series(df["ccc37"], "1996:ccc37", "1996")
    cj = map_series(df.loc[df._s == "j", "ccc23"], "1996:ccc23:j", "1996")
    ca = map_series(df.loc[df._s == "a", "ccc23"], "1996:ccc23:a", "1996")
    cmap = pd.concat([cj, ca]).sort_index()
    mask = rmap.notna() & cmap.notna()
    ri = rmap[mask].map(CIDX).to_numpy(dtype=int)
    ci = cmap[mask].map(CIDX).to_numpy(dtype=int)
    strata = df.loc[mask, "_s"].to_numpy()
    wt = np.ones(len(ri))
    shares = {"j": 1 - ARAB_ELECTORATE_SHARE_1996, "a": ARAB_ELECTORATE_SHARE_1996}
    for s, share in shares.items():
        m = strata == s
        wt[m] = share / m.sum()
    T = crosstab(ri, ci, wt)
    (lo_ab, hi_ab), (lo_vo, hi_vo) = boot_cis(ri, ci, wt, strata)
    return {"n": int(len(ri)), "weight": f"pooled j/a at {1-ARAB_ELECTORATE_SHARE_1996:.2f}/{ARAB_ELECTORATE_SHARE_1996:.2f}",
            "row_n": [int(v) for v in np.bincount(ri, minlength=8)],
            "T": T,
            "with_abstention": {"M": row_stochastic(T), "lo": lo_ab, "hi": hi_ab},
            "voters_only": {"M": row_stochastic(T[:7, :7]), "lo": lo_vo, "hi": hi_vo}}


def out_variant(pair, key):
    v = pair[key]
    n = 8 if key == "with_abstention" else 7
    return {"M": fmt(v["M"][:n, :n]), "lo": fmt(v["lo"][:n, :n]), "hi": fmt(v["hi"][:n, :n])}


def compare(surv_M, surv_row_n, eco, key, ncat):
    """r + weighted mean |diff| (pp) + per-row total-variation, vs ecological."""
    if not eco or not eco.get(key):
        return None
    E = np.array(eco[key]["M"], dtype=float)[:ncat, :ncat]
    sv = np.array(eco[key]["source_votes"], dtype=float)[:ncat]
    S = np.asarray(surv_M)[:ncat, :ncat]
    rows = [i for i in range(ncat) if surv_row_n[i] >= 30 and sv[i] > 0]
    if not rows:
        return None
    e, s = E[rows].ravel(), S[rows].ravel()
    r = float(np.corrcoef(e, s)[0, 1]) if e.std() > 0 and s.std() > 0 else None
    wr = sv[rows] / sv[rows].sum()
    ww = np.repeat(wr, ncat) / ncat
    wmad = float((np.abs(e - s) * ww).sum() * 100)
    per_row = {CATS[i]: {"n": int(surv_row_n[i]),
                         "tv_pp": round(float(np.abs(E[i] - S[i]).sum() / 2 * 100), 1)}
               for i in rows}
    return {"pearson_r": round(r, 4) if r is not None else None,
            "weighted_mean_abs_diff_pp": round(wmad, 2),
            "rows_compared": [CATS[i] for i in rows], "per_row": per_row}


def main():
    t0 = time.time()
    with open(f"{ROOT}/data/vote_transfers.json", encoding="utf-8") as f:
        ECO = json.load(f)

    out = {"generated_at": time.strftime("%Y-%m-%d %H:%M"), "B": B, "blocs": CATS[:6],
           "categories": CATS,
           "note": ("INES recalled-vote x current-vote weighted crosstabs, row-stochastic. "
                    "Rows/cols exclude undecided/refuse/DK/blank and not-eligible-at-a. "
                    "21_to_22 is a true panel (no recall). Survey estimates carry recall "
                    "bias + sampling error; treat as triangulation vs the ecological "
                    "matrices, not ground truth."),
           "transitions": {}}

    def emit(key, pair, wave, row_src, col_src, extra=None):
        eco_t = ECO["transitions"].get(key)
        entry = {"wave": wave, "row_source": row_src, "col_source": col_src,
                 "n": pair["n"], "weight": pair["weight"], "row_n": pair["row_n"],
                 "with_abstention": out_variant(pair, "with_abstention"),
                 "voters_only": out_variant(pair, "voters_only"),
                 "vs_ecological": {
                     "with_abstention": compare(pair["with_abstention"]["M"], pair["row_n"],
                                                eco_t, "bloc_with_abstention", 8),
                     "voters_only": compare(pair["voters_only"]["M"], pair["row_n"],
                                            eco_t, "bloc_no_abstention", 7)}}
        if extra:
            entry.update(extra)
        return entry

    # --- K13 -> K14 (1996, two samples, intent) ---
    pair = spec_1996()
    out["transitions"]["13_to_14"] = emit("13_to_14", pair, "1996",
                                          "recall", "intent",
                                          {"two_sample_pooled": True})
    print(f"13->14  n={pair['n']:>5}  w={pair['weight']}")

    # --- straightforward single-file waves ---
    def run(key, wave, path, row_var, col_var, w_prefs, row_src="recall", col_src="post",
            categoricals=True, code_maps=None, post_pair=None, extra=None):
        df, vl = read_wave(f"{INES}/{path}", categoricals)
        vlabels = None
        if vl is not None and code_maps is None:
            vlabels = {v: {int(k): lab for k, lab in vl[v].items()} for v in (row_var, col_var)
                       if v in vl}
        pair = build_pair(df, row_var, col_var, wave, w_prefs,
                          code_maps=code_maps, vlabels=vlabels)
        entry = emit(key, pair, wave, row_src, col_src, extra)
        # separate post-based voters_only when the main col var is intent
        if post_pair:
            pv, psrc = post_pair
            vlab2 = None
            if vl is not None and code_maps is None:
                vlab2 = {v: {int(k): lab for k, lab in vl[v].items()} for v in (row_var, pv)
                         if v in vl}
            p2 = build_pair(df, row_var, pv, wave, w_prefs, code_maps=code_maps, vlabels=vlab2)
            entry["voters_only"] = out_variant(p2, "voters_only")
            entry["voters_only_n"] = p2["n"]
            entry["voters_only_col_source"] = psrc
            entry["vs_ecological"]["voters_only"] = compare(
                p2["voters_only"]["M"], p2["row_n"], ECO["transitions"].get(key),
                "bloc_no_abstention", 7)
        out["transitions"][key] = entry
        print(f"{key.replace('_to_','->'):>7}  n={pair['n']:>5}  w={pair['weight']}")
        return entry

    run("14_to_15", "1999", "1999/1999-1.dta", "c17", "c12", [], col_src="intent")
    run("15_to_16", "2003", "2003/2003.dta", "b70", "b63", [], col_src="intent")
    run("16_to_17", "2006", "2006/2006.dta", "c40", "b73", [], col_src="intent",
        categoricals=False, post_pair=("d6", "post"))
    run("17_to_18", "2009", "2009/2009.dta", "v162", "v154", ["w_arabs"], col_src="intent",
        post_pair=("q3", "post"))
    run("18_to_19", "2013", "2013/2013.dta", "v102", "a_v2", [], categoricals=False,
        code_maps={"v102": CODE_2013_V102, "a_v2": CODE_2013_AV2})
    run("19_to_20", "2015", "2015/2015.dta", "v101", "after_v2", [], categoricals=False)
    run("20_to_21", "2019", "2019/Apr-Sep_2019_update_STATA.dta", "v108", "v2_after",
        ["weights_panel_2", "weights_panel_1", "weights_panel_3", "weights_panel_4"])
    run("21_to_22", "2019", "2019/Apr-Sep_2019_update_STATA.dta", "v2_after", "D2",
        ["weights_panel_4", "weights_panel_3", "weights_panel_2", "weights_panel_1"],
        row_src="post(panel)", col_src="post(panel)", extra={"panel": True})
    run("22_to_23", "2020", "2020/March_2020_update_STATA.dta", "v507", "E2_after",
        ["weights_panel_2", "weights_panel_1"])
    run("23_to_24", "2021", "2021/March_2021_update_STATA.dta", "v610", "F2",
        ["weights_panel_2", "weights_panel_1"])
    run("24_to_25", "2022", "2022/2022_STATA.dta", "v706", "v104",
        ["w_panel1", "w_panel2"], col_src="intent", post_pair=("F2", "post"))

    # --- recall-chain second estimate of 21->22 (2020 wave) for recall-bias check ---
    df20, _ = read_wave(f"{INES}/2020/March_2020_update_STATA.dta")
    pair = build_pair(df20, "v508", "v507", "2020",
                      ["weights_panel_1", "weights_panel_2"])
    eco_t = ECO["transitions"].get("21_to_22")
    out["extra"] = {"21_to_22_recall_chain": {
        "wave": "2020", "row_source": "recall", "col_source": "recall",
        "n": pair["n"], "weight": pair["weight"], "row_n": pair["row_n"],
        "with_abstention": out_variant(pair, "with_abstention"),
        "voters_only": out_variant(pair, "voters_only"),
        "vs_ecological": {
            "with_abstention": compare(pair["with_abstention"]["M"], pair["row_n"],
                                       eco_t, "bloc_with_abstention", 8),
            "voters_only": compare(pair["voters_only"]["M"], pair["row_n"],
                                   eco_t, "bloc_no_abstention", 7)}}}
    # panel vs recall-chain distance (recall-bias yardstick)
    P = np.array(out["transitions"]["21_to_22"]["with_abstention"]["M"])
    C = np.array(out["extra"]["21_to_22_recall_chain"]["with_abstention"]["M"])
    rn_p = out["transitions"]["21_to_22"]["row_n"]
    rn_c = out["extra"]["21_to_22_recall_chain"]["row_n"]
    rows = [i for i in range(8) if rn_p[i] >= 30 and rn_c[i] >= 30]
    out["extra"]["panel_vs_recall_chain_tv_pp"] = {
        CATS[i]: round(float(np.abs(P[i] - C[i]).sum() / 2 * 100), 1) for i in rows}
    print(f"21->22 recall-chain  n={pair['n']:>5}  w={pair['weight']}")

    with open(f"{ROOT}/data/survey_transfers.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)

    # --- console report (ASCII) ---
    print("\nunmapped labels (excluded, count):")
    for (wave, var, lab), c in sorted(WARN.items()):
        print(f"  [{wave} {var}] {c:>4}  {lab!r}")
    if not WARN:
        print("  none")

    print(f"\n{'trans':>7} {'n':>5} {'r(abst)':>8} {'wmad pp':>8} {'r(vot)':>7} {'wmad':>6}  rows compared")
    for k, t in out["transitions"].items():
        ca = t["vs_ecological"]["with_abstention"]
        cv = t["vs_ecological"]["voters_only"]
        print(f"{k.replace('_to_','->'):>7} {t['n']:>5} "
              f"{(ca['pearson_r'] if ca else float('nan')):>8.3f} "
              f"{(ca['weighted_mean_abs_diff_pp'] if ca else float('nan')):>8.2f} "
              f"{(cv['pearson_r'] if cv else float('nan')):>7.3f} "
              f"{(cv['weighted_mean_abs_diff_pp'] if cv else float('nan')):>6.2f}  "
              f"{','.join(ca['rows_compared']) if ca else '-'}")
    print(f"\npanel vs recall-chain TV (pp) per row: "
          f"{out['extra']['panel_vs_recall_chain_tv_pp']}")
    print(f"\nwrote data/survey_transfers.json  ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
