# -*- coding: utf-8 -*-
"""
build_ines_micro.py — individual-level INES cross-reference for the ecological
findings: weighted bloc shares BY education / religiosity / age group, per
election K13-K25, from the 14 INES waves.

Motivation: every research page carries the "ecological — locality aggregates"
caveat. This produces the survey-side (individual-level) education gradient to
put NEXT TO the ecological one in demographics.html: if the RH-share gap
between academics and non-academics widens 1992->2022 like the locality-level
slope does, the sorting finding gets its micro confirmation.

Reuses the label->bloc machinery of build_survey_transfers.py (imported as a
module — R rules, COMMON tail rules, map_series, read_wave, pick_weight,
CODE_2013 maps), so bloc assignment per election matches the transfer study
and parties_national.json exactly.

Design decisions:
- Vote variable: POST-election report where the wave has one (2006 d6, 2009 q3,
  2022 F2), else intent/current — same preference as the transfer study's
  voters-only variant. Shares are computed among VOTERS (dnv/undecided/refuse
  excluded).
- Education harmonized to BINARY academic-degree: direct question where asked
  (1999 c29, 2003 b84, 2006 c77, 2009 v182), 'highest level of education'
  labels 2013+ (academic keywords), years-of-schooling >= 16 as proxy for
  1992/1996 (flagged in output).
- Religiosity harmonized to 4 tiers (haredi/dati/masorti/hiloni) from the
  self-definition question where asked; waves with only the observance scale
  (1992, 1996, 2009, 2013, 2015) are mapped approximately and flagged
  scale='observance' (no haredi tier there).
- Education/age splits are scoped to JEWISH respondents where the wave allows
  identification (religion var / sample design) — matching the ecological
  gradient's Jewish-localities universe. Scope recorded per election.
- Weights: same per-wave preference lists as the transfer study; unweighted
  before 2009 (the files ship no weights).

Output: data/ines_micro.json
Report: analysis/ines_micro_report.txt (incl. per-election national-RH
        triangulation vs core.json and the unmapped-label log)
Run:    python -X utf8 analysis/build_ines_micro.py   (~2 min)
"""
import importlib.util
import json
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import os
import re

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INES = r"C:/Users/yarde/Downloads/INES"

spec = importlib.util.spec_from_file_location("bst", os.path.join(HERE, "build_survey_transfers.py"))
bst = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bst)

BLOCS = ["right", "haredi", "center", "left", "arab", "opposition_right", "other"]
RH = ("right", "haredi")

report = []


def rep(s=""):
    report.append(s)
    print(s)


# ---------------- harmonizers ----------------
ACAD_YES = re.compile(r"\byes\b|academic degree|has an academic", re.I)
ACAD_NO = re.compile(r"\bno\b|does not|doesn't|non-academic", re.I)
ACAD_LEVEL = re.compile(r"\bb\.?a\b|\bm\.?a\b|ph\.?d|doctor|academic|university degree|first degree|second degree|third degree", re.I)
NONACAD_LEVEL = re.compile(r"elementary|primary|high school|secondary|matriculation|vocational|yeshiva|no formal|partial|post-secondary non|non academic|technician|practical", re.I)

REL_RULES = [
    (re.compile(r"haredi|ultra", re.I), "haredi"),
    (re.compile(r"tradition", re.I), "masorti"),          # incl. traditional-religious
    # secular BEFORE religious: v144 labels read "Secular, anti-religious" /
    # "Secular, not anti-religious" — the religious pattern must not claim them
    (re.compile(r"secular|hiloni|not religious|non-religious|not at all|do(es)? not observe|don't observe", re.I), "hiloni"),
    (re.compile(r"religious|dati|orthodox|observe (all|meticulously|strictly)|to a great extent|great deal", re.I), "dati"),
    (re.compile(r"somewhat|partial|to some extent|little", re.I), "masorti"),
    (re.compile(r"mixed|other|refus|know|answer", re.I), None),
]

JEW_PAT = re.compile(r"jew", re.I)


def por_get(por_labels, var):
    """POR variable names are UPPERCASE and truncated to 8 chars."""
    if not por_labels:
        return None
    for key in (var, var.upper(), var.upper()[:8]):
        if key in por_labels:
            return por_labels[key]
    return None


def labels_of(df, vl, var, categoricals):
    """Return a Series of LABEL STRINGS for var (or raw values if unlabeled)."""
    s = df[var]
    if categoricals:
        return s.astype(str)
    if vl and var in vl:
        m = {k: str(lab) for k, lab in vl[var].items()}
        return s.map(lambda v: m.get(v, m.get(int(v)) if pd.notna(v) and float(v) == int(v) else None) if pd.notna(v) else None)
    return s


def edu_binary(df, vl, cfg, categoricals, por_labels=None):
    kind, var = cfg
    if var not in df.columns:
        return None, kind
    if kind == "years":
        y = pd.to_numeric(df[var], errors="coerce")
        y = y.where((y >= 0) & (y <= 30))
        return y.map(lambda v: None if pd.isna(v) else bool(v >= 16)), "years>=16 (proxy)"
    lab = labels_of(df, vl, var, categoricals)
    pl = por_get(por_labels, var)
    if pl:
        m = {float(k): str(v) for k, v in pl.items()}
        lab = df[var].map(lambda v: m.get(float(v)) if pd.notna(v) else None)

    def cls(s):
        if s is None or (isinstance(s, float) and pd.isna(s)) or s == "nan":
            return None
        s = str(s)
        if kind == "binary":
            if ACAD_YES.search(s):
                return True
            if ACAD_NO.search(s):
                return False
            return None
        if ACAD_LEVEL.search(s):
            return True
        if NONACAD_LEVEL.search(s):
            return False
        return None
    return lab.map(cls), ("direct question" if kind == "binary" else "education-level labels")


def rel_tier(df, vl, cfg, categoricals, por_labels=None):
    kind, var = cfg
    if var is None or var not in df.columns:
        return None, kind
    lab = labels_of(df, vl, var, categoricals)
    pl = por_get(por_labels, var)
    if pl:
        m = {float(k): str(v) for k, v in pl.items()}
        lab = df[var].map(lambda v: m.get(float(v)) if pd.notna(v) else None)

    def cls(s):
        if s is None or (isinstance(s, float) and pd.isna(s)) or s == "nan":
            return None
        for pat, tier in REL_RULES:
            if pat.search(str(s)):
                return tier
        return None
    return lab.map(cls), kind


def age_group(df, vl, cfg, categoricals):
    kind, var = cfg
    if var is None or var not in df.columns:
        return None

    def from_num(v):
        if pd.isna(v) or v < 18 or v > 110:
            return None
        return "55+" if v >= 55 else ("35-54" if v >= 35 else "18-34")
    if kind == "num":
        return pd.to_numeric(df[var], errors="coerce").map(from_num)
    lab = labels_of(df, vl, var, categoricals)

    def from_label(s):
        if s is None or (isinstance(s, float) and pd.isna(s)):
            return None
        m = re.search(r"\d+", str(s))
        return from_num(float(m.group(0))) if m else None
    return lab.map(from_label)


def jewish_mask(df, vl, cfg, categoricals, por_labels=None):
    kind, var = cfg
    if kind == "assume_jewish":
        return pd.Series(True, index=df.index), "single-sample wave (assumed Jewish sample)"
    if var not in df.columns:
        return pd.Series(True, index=df.index), f"sector var {var} missing — unscoped"
    if kind == "religion":
        lab = labels_of(df, vl, var, categoricals)
        pl = por_get(por_labels, var)
        if pl:
            m = {float(k): str(v) for k, v in pl.items()}
            lab = df[var].map(lambda v: m.get(float(v)) if pd.notna(v) else None)
        return lab.map(lambda s: bool(JEW_PAT.search(str(s))) if s is not None else False), f"religion var {var}"
    if kind == "relvar_notna":
        return df[var].notna(), f"{var} answered (asked of Jews)"
    if kind == "arabvar_isna":
        return df[var].isna(), f"{var} (Arab-sample var) empty"
    return pd.Series(True, index=df.index), "unscoped"


# ---------------- per-election config ----------------
CFG = {
    "13": dict(wave="1992", path="1992/1992.dta", vote="i41", src="intent", weights=[],
               edu=("years", "i62"), rel=("observance", "i50"), age=("num", "i61"),
               sector=("assume_jewish", None)),
    # K14 handled specially (1996 two-sample pooling)
    "15": dict(wave="1999", path="1999/1999-1.dta", vote="c12", src="intent", weights=[],
               edu=("binary", "c29"), rel=("selfdef", "c38"), age=("num", "c20"),
               sector=("relvar_notna", "c38")),
    "16": dict(wave="2003", path="2003/2003.dta", vote="b63", src="intent", weights=[],
               edu=("binary", "b84"), rel=("selfdef", "b91"), age=("group", "b74"),
               sector=("arabvar_isna", "b90")),
    "17": dict(wave="2006", path="2006/2006.dta", vote="d6", src="post", weights=[], categoricals=False,
               edu=("binary", "c77"), rel=("selfdef", "c88"), age=("num", "c54"),
               sector=("religion", "c87")),
    "18": dict(wave="2009", path="2009/2009.dta", vote="q3", src="post", weights=["w_arabs"],
               edu=("binary", "v182"), rel=("observance", "v175"), age=("group", "agegroup_1"),
               sector=("religion", "v189_1")),
    "19": dict(wave="2013", path="2013/2013.dta", vote="a_v2", src="post", weights=[], categoricals=False,
               code_map=bst.CODE_2013_AV2, por="2013/2013.por",
               edu=("years", "a_educ"), rel=("observance", "v132"), age=("num", "a_age"),
               sector=("religion", "v149")),
    "20": dict(wave="2015", path="2015/2015.dta", vote="after_v2", src="post", weights=[], categoricals=False,
               edu=("level", "v128"), rel=("observance", "v114"), age=("num", "age"),
               sector=("religion", "v138")),
    "21": dict(wave="2019", path="2019/Apr-Sep_2019_update_STATA.dta", vote="v2_after", src="post",
               weights=["weights_panel_2", "weights_panel_1", "weights_panel_3", "weights_panel_4"],
               edu=("level", "educ"), rel=("selfdef", "v144"), age=("num", "age"),
               sector=("religion", "v143_code")),
    "22": dict(wave="2019", path="2019/Apr-Sep_2019_update_STATA.dta", vote="D2", src="post(panel)",
               weights=["weights_panel_4", "weights_panel_3", "weights_panel_2", "weights_panel_1"],
               edu=("level", "educ"), rel=("selfdef", "v144"), age=("num", "age"),
               sector=("religion", "v143_code")),
    "23": dict(wave="2020", path="2020/March_2020_update_STATA.dta", vote="E2_after", src="post",
               weights=["weights_panel_2", "weights_panel_1"],
               edu=("level", "educ"), rel=("selfdef", "v144"), age=("num", "age"),
               sector=("relvar_notna", "v144")),
    "24": dict(wave="2021", path="2021/March_2021_update_STATA.dta", vote="F2", src="post",
               weights=["weights_panel_2", "weights_panel_1"],
               edu=("level", "educ"), rel=("selfdef", "v144"), age=("num", "age"),
               sector=("relvar_notna", "v144")),
    "25": dict(wave="2022", path="2022/2022_STATA.dta", vote="F2", src="post",
               weights=["w_panel2", "w_panel1"],
               edu=("level", "educ"), rel=("selfdef", "v144"), age=("num", "age"),
               sector=("religion", "v143_code")),
}


def group_shares(votes, weights, groups, voters_mask):
    """weighted bloc shares among voters per group value."""
    out = {}
    for g in sorted(set(groups.dropna().unique()), key=str):
        m = voters_mask & (groups == g)
        w = weights[m]
        tot = w.sum()
        if tot <= 0 or m.sum() < 30:
            continue
        shares = {}
        for b in BLOCS:
            shares[b] = round(100 * float(w[votes[m] == b].sum()) / float(tot), 1)
        shares["rh"] = round(shares["right"] + shares["haredi"], 1)
        out[str(g)] = {"n": int(m.sum()), **shares}
    return out


def process(k, df, vl, cfg, categoricals, por_labels=None):
    wave, vote_var = cfg["wave"], cfg["vote"]
    rule_key = f"{wave}:{vote_var}"
    vlab = None
    if vl and vote_var in vl:
        vlab = {int(kk): lab for kk, lab in vl[vote_var].items()}
    votes = bst.map_series(df[vote_var], rule_key, wave,
                           code_map=cfg.get("code_map"), value_labels=vlab)
    voters = votes.isin(BLOCS)
    wvar = bst.pick_weight(df, voters, cfg.get("weights", []))
    w = pd.to_numeric(df[wvar], errors="coerce").fillna(0) if wvar else pd.Series(1.0, index=df.index)

    jm, sector_note = jewish_mask(df, vl, cfg["sector"], categoricals, por_labels)
    edu, edu_def = edu_binary(df, vl, cfg["edu"], categoricals, por_labels)
    rel, rel_scale = rel_tier(df, vl, cfg["rel"], categoricals, por_labels)
    ag = age_group(df, vl, cfg["age"], categoricals)

    tot_w = w[voters].sum()
    rh_all = round(100 * float(w[voters & votes.isin(RH)].sum()) / float(tot_w), 1) if tot_w > 0 else None

    entry = {"wave": wave, "vote_source": cfg["src"], "weight": wvar or "unweighted",
             "n_voters": int(voters.sum()), "rh_overall": rh_all,
             "sector_scope": sector_note}
    if edu is not None:
        eg = edu.map(lambda v: None if v is None or pd.isna(v) else ("acad" if v else "non_acad"))
        entry["education"] = {"def": edu_def, "scope": "jewish",
                              "groups": group_shares(votes[jm], w[jm], eg[jm], voters[jm])}
        g = entry["education"]["groups"]
        if "acad" in g and "non_acad" in g:
            entry["education"]["rh_gap"] = round(g["non_acad"]["rh"] - g["acad"]["rh"], 1)
    if rel is not None:
        entry["religiosity"] = {"scale": rel_scale,
                                "groups": group_shares(votes, w, rel, voters)}
    if ag is not None:
        entry["age"] = {"scope": "jewish",
                        "groups": group_shares(votes[jm], w[jm], ag[jm], voters[jm])}
    return entry


def k14_1996():
    dj, _ = bst.read_wave(f"{INES}/1996/1996j.dta")
    da, _ = bst.read_wave(f"{INES}/1996/1996a.dta")
    dj = dj.copy(); da = da.copy()
    dj["_s"] = "j"; da["_s"] = "a"
    parts = []
    for d, samp, key in ((dj, "j", "1996:ccc23:j"), (da, "a", "1996:ccc23:a")):
        votes = bst.map_series(d["ccc23"], key, "1996")
        share = (1 - bst.ARAB_ELECTORATE_SHARE_1996) if samp == "j" else bst.ARAB_ELECTORATE_SHARE_1996
        d["_votes"] = votes
        d["_w"] = share / len(d)
        parts.append(d)
    df = pd.concat(parts, ignore_index=True)
    votes = df["_votes"]; w = df["_w"]
    voters = votes.isin(BLOCS)
    jm = df["_s"] == "j"
    edu = pd.to_numeric(df["ccc63"], errors="coerce").where(lambda y: (y >= 0) & (y <= 30)) \
        .map(lambda v: None if pd.isna(v) else ("acad" if v >= 16 else "non_acad"))
    rel, _ = rel_tier(df, None, ("observance", "ccc70"), True)
    ag = age_group(df, None, ("num", "ccc57"), True)
    tot_w = w[voters].sum()
    rh_all = round(100 * float(w[voters & votes.isin(RH)].sum()) / float(tot_w), 1)
    entry = {"wave": "1996", "vote_source": "intent", "weight": "pooled j/a 0.88/0.12",
             "n_voters": int(voters.sum()), "rh_overall": rh_all,
             "sector_scope": "two-sample design (j file = Jews)"}
    entry["education"] = {"def": "years>=16 (proxy)", "scope": "jewish",
                          "groups": group_shares(votes[jm], w[jm], edu[jm], voters[jm])}
    g = entry["education"]["groups"]
    if "acad" in g and "non_acad" in g:
        entry["education"]["rh_gap"] = round(g["non_acad"]["rh"] - g["acad"]["rh"], 1)
    entry["religiosity"] = {"scale": "observance", "groups": group_shares(votes[jm], w[jm], rel[jm], voters[jm])}
    entry["age"] = {"scope": "jewish", "groups": group_shares(votes[jm], w[jm], ag[jm], voters[jm])}
    return entry


def main():
    core = json.load(open(os.path.join(ROOT, "data", "core.json"), encoding="utf-8"))
    nb = core.get("national_blocs", {})
    out = {"meta": {
        "built": "2026-07-04",
        "what": "Individual-level (INES survey) bloc shares by education/religiosity/age per election; voters only, weighted where the wave ships weights",
        "citation_note": "Israel National Election Studies (INES), Tel Aviv University — full per-study citations in transfers.html credits",
        "caveats": [
            "education = academic degree; 1992/1996/2013 proxied by years of schooling >= 16",
            "religiosity 4-tier from self-definition; waves flagged scale=observance have no haredi tier",
            "education/age scoped to Jewish respondents (see sector_scope); religiosity groups are effectively Jewish (question asked of Jews)",
            "pre-2009 waves ship no weights (unweighted); shares among voters (dnv/undecided excluded)",
            "survey n per group 300-900 -> +-3-6pp sampling error; trends matter, not single points",
        ],
    }, "elections": {}}

    for k in sorted(list(CFG) + ["14"], key=int):
        if k == "14":
            entry = k14_1996()
        else:
            cfg = CFG[k]
            categoricals = cfg.get("categoricals", True) is not False
            df, vl = bst.read_wave(f"{INES}/{cfg['path']}", categoricals=categoricals)
            por_labels = None
            if cfg.get("por"):
                try:
                    import pyreadstat
                    _, pmeta = pyreadstat.read_por(f"{INES}/{cfg['por']}", metadataonly=True)
                    por_labels = pmeta.variable_value_labels
                except Exception as e:
                    rep(f"K{k}: por labels unavailable ({e}) — label-based dims may drop")
            entry = process(k, df, vl, cfg, categoricals, por_labels)
        out["elections"][k] = entry
        nbk = nb.get(k) or {}
        official_rh = round(nbk["right"] + nbk["haredi"], 1) if "right" in nbk and "haredi" in nbk else None
        gap = entry.get("education", {}).get("rh_gap")
        rep(f"K{k}: wave {entry['wave']:>5} src={entry['vote_source']:<11} n_voters={entry['n_voters']:>5} "
            f"w={entry['weight']:<22} rh_survey={entry['rh_overall']}% official={official_rh} "
            f"edu_gap={gap}")

    # unmapped-label log (safety net, same convention as the transfer study)
    if bst.WARN:
        rep("")
        rep("unmapped vote labels (excluded):")
        for (wave, key, lab), cnt in sorted(bst.WARN.items()):
            rep(f"   {wave} {key}: {lab!r} x{cnt}")

    path = os.path.join(ROOT, "data", "ines_micro.json")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    rep(f"wrote {path} ({os.path.getsize(path):,} bytes)")
    open(os.path.join(HERE, "ines_micro_report.txt"), "w", encoding="utf-8").write("\n".join(report))


if __name__ == "__main__":
    main()
