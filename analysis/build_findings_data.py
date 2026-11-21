# -*- coding: utf-8 -*-
"""Build findings_data.json (repo root): the polarization / sorting / nationalization
panel read by findings.html, the dashboard polarization tab and demographics.html.

No builder existed before 2026-11-20 — the June-30 file was a one-off session
artifact. This script re-implements the method documented in CONTINUE.md §3.1,
cross-checked against that file (see VALIDATION below).

Method (locality level, ecological):
  * Balanced panel  = localities.json rows with right_haredi_pct present in EVERY
    election of the span; names containing 'מעטפות' (double envelopes) excluded.
  * Weight          = kosher_votes of that locality in that election (--weights
    kosher, the CONTINUE §3.1 convention). The June-30 file actually used
    bzb-with-kosher-fallback (bzb is empty at K17); --weights bzb_or_kosher
    reproduces that file.
  * Measure         = raw right_haredi_pct (share of valid votes; NOT two-bloc).
  * sorting.*       = per election: weighted SD (wsd_rh), weighted mean, weighted
    p10/median/p90 (inverse-CDF: first value whose cumulative weight >= q*W),
    p90_p10, bimodality coefficient (g1^2+1)/kurtosis (weighted moments, no
    small-sample correction), dissimilarity 0.5*sum|r_i/R - c_i/C| on two-bloc
    VOTES (r_i = rh% x kosher, c_i = cla% x kosher; always kosher-based).
  * nationalization = per consecutive pair: weighted SD (wsd_swing) and weighted
    mean (natl_swing) of the locality swing d_rh, weights = election-B weight;
    midyear = mean of the two years.
  * hists           = per election, weight share of localities in 5-pt rh bins
    (edges 0..95, last bin closed at 100).
  * ci              = bootstrap over panel localities, B=2000, fixed seed:
    slopes/change = [point, 2.5%, 97.5%] for the OLS slope per year (swing: per
    midyear) and for last-minus-first; *_band = per-election 2.5/97.5 percentiles.
  * movers          = cities with bzb >= 30,000 at the LAST election and arab_pct
    < 50 there: top 6 by change (last - first) each way; traj for the six featured
    cities (curated list, unchanged).
  * mechanism       = same size/arab rule, joined to socioeconomic.json by name with
    whitespace removed (the June-30 join; it misses yod-spelling variants such as
    הרצלייה / קריית — kept for faithfulness, flagged in the report); dRH = last -
    first, acad/fert = socioeconomic pct_academic_degree / pct_families_4plus,
    har/arab = haredi_pct / arab_pct at the last election; corr = unweighted
    Pearson r of dRH with acad, fert, har. featured/profiles = curated lists.

Run:  python -X utf8 analysis/build_findings_data.py              (K13..latest, writes)
      python -X utf8 analysis/build_findings_data.py --kmax 25 --dry-run
      python -X utf8 analysis/build_findings_data.py --validate    (method checks only)
Report: analysis/findings_data_report.txt (UTF-8)
"""
import argparse
import json
import os
import re
import shutil

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_PATH = os.path.join(ROOT, "findings_data.json")
REPORT_PATH = os.path.join(HERE, "findings_data_report.txt")

B_BOOT = 2000
SEED = 20261120
BINS = np.arange(0, 105, 5)
CITY_MIN_BZB = 30000
ARAB_MAX = 50.0
TOP_N = 6
# curated lists carried over verbatim from the June-30 file (page colour maps key on them)
FEATURED_LEFT = ["תל אביב - יפו", "גבעתיים", "הרצליה"]
FEATURED_RIGHT = ["בית שמש", "בני ברק", "ירושלים"]
MECH_FEATURED = ["תל אביב - יפו", "רמת השרון", "גבעתיים", "הרצליה", "ירושלים", "בית שמש", "בני ברק"]
MECH_PROFILES = [("תל אביב - יפו", "secular"), ("רמת השרון", "secular"), ("גבעתיים", "secular"),
                 ("ירושלים", "haredi"), ("בית שמש", "haredi"), ("בני ברק", "haredi")]

report = []


def rep(s=""):
    report.append(str(s))


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------- weighted helpers ----------------
def wmean(v, w):
    return float(np.average(v, weights=w))


def wsd(v, w):
    m = np.average(v, weights=w)
    return float(np.sqrt(np.average((v - m) ** 2, weights=w)))


def wq(v, w, q):
    o = np.argsort(v, kind="stable")
    v, w = v[o], w[o]
    cw = np.cumsum(w)
    return float(v[np.searchsorted(cw, q * cw[-1])])


def bimod(v, w):
    m = np.average(v, weights=w)
    s = np.sqrt(np.average((v - m) ** 2, weights=w))
    z = (v - m) / s
    g1 = np.average(z ** 3, weights=w)
    k4 = np.average(z ** 4, weights=w)
    return float((g1 ** 2 + 1) / k4)


def dissim(rh, cla, kv):
    r, c = rh * kv / 100.0, cla * kv / 100.0
    return float(0.5 * np.abs(r / r.sum() - c / c.sum()).sum())


def slope(x, y):
    return float(np.polyfit(np.asarray(x, float), np.asarray(y, float), 1)[0])


def nows(s):
    return re.sub(r"\s+", "", s or "")


# ---------------- core ----------------
def build(loc, core, soc, ks, weights="kosher", boot=True):
    years = {k: core["metadata"]["knesset_years"][k] for k in ks}
    panel = [x for x in loc if "מעטפות" not in x["name"]
             and all((x.get("data") or {}).get(k, {}).get("right_haredi_pct") is not None for k in ks)]
    n = len(panel)
    D = lambda f: np.array([[x["data"][k].get(f) or 0 for k in ks] for x in panel], float)
    rh, cla, kv, bz = D("right_haredi_pct"), D("center_left_arab_pct"), D("kosher_votes"), D("bzb")
    if (kv <= 0).any():
        raise SystemExit("panel locality with kosher_votes <= 0 — inspect before building")
    W = kv if weights == "kosher" else np.where(bz > 0, bz, kv)
    yrs = np.array([years[k] for k in ks], float)
    mids = (yrs[:-1] + yrs[1:]) / 2

    def metrics(idx):
        r, c, w, k_ = rh[idx], cla[idx], W[idx], kv[idx]
        out = {"wsd": [], "p9010": [], "dis": [], "swing": []}
        for j in range(len(ks)):
            out["wsd"].append(wsd(r[:, j], w[:, j]))
            out["p9010"].append(wq(r[:, j], w[:, j], .9) - wq(r[:, j], w[:, j], .1))
            out["dis"].append(dissim(r[:, j], c[:, j], k_[:, j]))
        for j in range(len(ks) - 1):
            out["swing"].append(wsd(r[:, j + 1] - r[:, j], w[:, j + 1]))
        return out

    sorting = {"election": ks, "year": [years[k] for k in ks],
               "wsd_rh": [], "p90_p10": [], "bimod": [], "dissim": [], "wmean_rh": [],
               "p10": [], "p90": [], "median": []}
    hists = {"edges": [int(e) for e in BINS[:-1]]}
    for j, k in enumerate(ks):
        v, w = rh[:, j], W[:, j]
        p10, p90 = wq(v, w, .1), wq(v, w, .9)
        sorting["wsd_rh"].append(round(wsd(v, w), 2))
        sorting["p90_p10"].append(round(p90 - p10, 2))
        sorting["bimod"].append(round(bimod(v, w), 4))
        sorting["dissim"].append(round(dissim(v, cla[:, j], kv[:, j]), 4))
        sorting["wmean_rh"].append(round(wmean(v, w), 2))
        sorting["p10"].append(round(p10, 2))
        sorting["p90"].append(round(p90, 2))
        sorting["median"].append(round(wq(v, w, .5), 2))
        h, _ = np.histogram(v, bins=BINS, weights=w)
        hists[k] = [round(float(x), 4) for x in h / h.sum()]

    nat = {"pair": [f"{a}→{b}" for a, b in zip(ks[:-1], ks[1:])],
           "midyear": [float(m) for m in mids], "wsd_swing": [], "natl_swing": []}
    for j in range(len(ks) - 1):
        d, w = rh[:, j + 1] - rh[:, j], W[:, j + 1]
        nat["wsd_swing"].append(round(wsd(d, w), 2))
        nat["natl_swing"].append(round(wmean(d, w), 2))

    # ---- bootstrap ----
    # point estimates for slopes/change come from the PUBLISHED (rounded) series, as in
    # the June-30 file (its slope = polyfit on the rounded series, change = last-first of it)
    pt = {"wsd": sorting["wsd_rh"], "p9010": sorting["p90_p10"], "dis": sorting["dissim"],
          "swing": nat["wsd_swing"]}
    ci = None
    if boot:
        rng = np.random.default_rng(SEED)
        reps = {m: [] for m in pt}
        for _ in range(B_BOOT):
            r_ = metrics(rng.integers(0, n, n))
            for m in reps:
                reps[m].append(r_[m])
        reps = {m: np.array(v) for m, v in reps.items()}
        keymap = [("wsd_rh", "wsd", yrs, 4), ("p90_p10", "p9010", yrs, 4),
                  ("dissim", "dis", yrs, 4), ("swing", "swing", mids, 4)]
        ci = {"B": B_BOOT, "seed": SEED, "slopes": {}, "change": {}}
        for name, m, x, d in keymap:
            sl_b = np.array([slope(x, row) for row in reps[m]])
            ch_b = reps[m][:, -1] - reps[m][:, 0]
            ci["slopes"][name] = [round(slope(x, pt[m]), d), round(float(np.percentile(sl_b, 2.5)), d),
                                  round(float(np.percentile(sl_b, 97.5)), d)]
            ci["change"][name] = [round(pt[m][-1] - pt[m][0], d), round(float(np.percentile(ch_b, 2.5)), d),
                                  round(float(np.percentile(ch_b, 97.5)), d)]
        for name, m in [("wsd_rh", "wsd"), ("p90_p10", "p9010"), ("dissim", "dis"), ("swing", "swing")]:
            ci[f"{name}_band"] = {"lo": [round(float(v), 4) for v in np.percentile(reps[m], 2.5, axis=0)],
                                  "hi": [round(float(v), 4) for v in np.percentile(reps[m], 97.5, axis=0)]}

    # ---- movers ----
    k0, k1 = ks[0], ks[-1]
    cities = [x for x in panel if (x["data"][k1].get("bzb") or 0) >= CITY_MIN_BZB
              and (x["data"][k1].get("arab_pct") or 0) < ARAB_MAX]
    ch = sorted(((x["data"][k1]["right_haredi_pct"] - x["data"][k0]["right_haredi_pct"], x) for x in cities),
                key=lambda t: t[0])
    item = lambda c, x: {"name": x["name"], "change": round(c, 1),
                         "from": round(x["data"][k0]["right_haredi_pct"], 1),
                         "to": round(x["data"][k1]["right_haredi_pct"], 1)}
    byname = {x["name"]: x for x in panel}
    movers = {"years": [years[k] for k in ks],
              "featured_left": FEATURED_LEFT, "featured_right": FEATURED_RIGHT,
              "traj": {nm: [round(byname[nm]["data"][k]["right_haredi_pct"], 1) for k in ks]
                       for nm in FEATURED_LEFT + FEATURED_RIGHT if nm in byname},
              "left_list": [item(c, x) for c, x in ch[:TOP_N]],
              "right_list": [item(c, x) for c, x in reversed(ch[-TOP_N:])]}
    missing_feat = [nm for nm in FEATURED_LEFT + FEATURED_RIGHT if nm not in byname]

    # ---- mechanism ----
    soc_by = {nows(s["name"]): s for s in soc}
    mc = []
    unmatched = []
    for x in sorted(cities, key=lambda x: x["name"]):
        s = soc_by.get(nows(x["name"]))
        if not s or s.get("pct_academic_degree") is None or s.get("pct_families_4plus_children") is None:
            unmatched.append(x["name"])
            continue
        d1 = x["data"][k1]
        mc.append({"name": x["name"],
                   "dRH": round(d1["right_haredi_pct"] - x["data"][k0]["right_haredi_pct"], 1),
                   "acad": round(s["pct_academic_degree"], 1),
                   "fert": round(s["pct_families_4plus_children"], 1),
                   "har": round(d1.get("haredi_pct") or 0, 1),
                   "_arab": round(d1.get("arab_pct") or 0, 1)})
    y = np.array([c["dRH"] for c in mc])
    corr = {f: round(float(np.corrcoef(np.array([c[f] for c in mc]), y)[0, 1]), 2) for f in ("acad", "fert", "har")}
    corr["n"] = len(mc)
    mcd = {c["name"]: c for c in mc}
    profiles = [{"name": nm, "dRH": mcd[nm]["dRH"], "acad": mcd[nm]["acad"], "fert": mcd[nm]["fert"],
                 "har": mcd[nm]["har"], "arab": mcd[nm]["_arab"], "type": t}
                for nm, t in MECH_PROFILES if nm in mcd]
    for c in mc:
        c.pop("_arab")
    mechanism = {"corr": corr, "cities": mc, "featured": MECH_FEATURED, "profiles": profiles}

    out = {"sorting": sorting, "nationalization": nat, "hists": hists,
           "year": {k: years[k] for k in ks}, "n": n, "ci": ci,
           "movers": movers, "mechanism": mechanism}
    diag = {"mech_unmatched": unmatched, "missing_featured": missing_feat,
            "missing_profiles": [nm for nm, _ in MECH_PROFILES if nm not in mcd],
            "panel_names": [x["name"] for x in panel]}
    return out, diag


def cmp_lists(label, a, b, tol=0.0):
    if len(a) != len(b):
        return f"{label}: LENGTH {len(a)} vs {len(b)}"
    bad = [(i, x, y) for i, (x, y) in enumerate(zip(a, b)) if abs(x - y) > tol + 1e-12]
    return f"{label}: {'OK' if not bad else 'DIFF ' + str(bad)}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kmin", type=int, default=13)
    ap.add_argument("--kmax", type=int, default=None, help="default: latest election in core.json")
    ap.add_argument("--loc", default=os.path.join(ROOT, "data", "localities.json"))
    ap.add_argument("--weights", choices=["kosher", "bzb_or_kosher"], default="kosher")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--validate", action="store_true",
                    help="method checks only (June-30 file on pre-gapfix data; CONTINUE §3.1 values)")
    a = ap.parse_args()

    core = load(os.path.join(ROOT, "data", "core.json"))
    soc = load(os.path.join(ROOT, "data", "socioeconomic.json"))
    allks = sorted(core["metadata"]["knesset_years"], key=int)
    kmax = a.kmax or int(allks[-1])

    if a.validate:
        rep("== VALIDATION A0: June-30 file reproduced from localities.json.bak_pregapfix, "
            "K13-K25, weights=bzb_or_kosher ==")
        june = load(OUT_PATH + ".bak_prek26") if os.path.exists(OUT_PATH + ".bak_prek26") else load(OUT_PATH)
        old_loc = load(os.path.join(ROOT, "data", "localities.json.bak_pregapfix"))
        ks = [str(k) for k in range(13, 26)]
        o, dg = build(old_loc, core, soc, ks, "bzb_or_kosher", boot=False)
        rep(f"n: {o['n']} vs file {june['n']}")
        for f in ["wsd_rh", "p90_p10", "bimod", "dissim", "wmean_rh", "p10", "p90", "median"]:
            rep("  " + cmp_lists(f"sorting.{f}", o["sorting"][f], june["sorting"][f]))
        for f in ["wsd_swing", "natl_swing", "midyear"]:
            rep("  " + cmp_lists(f"nationalization.{f}", o["nationalization"][f], june["nationalization"][f]))
        for k in ks:
            r = cmp_lists(f"hists.{k}", o["hists"][k], june["hists"][k])
            if not r.endswith("OK"):
                rep("  " + r)
        rep("  hists: other elections OK" )
        rep(f"  movers.left_list identical: {o['movers']['left_list'] == june['movers']['left_list']}")
        rep(f"  movers.right_list identical: {o['movers']['right_list'] == june['movers']['right_list']}")
        rep(f"  movers.traj identical: {o['movers']['traj'] == june['movers']['traj']}")
        if o['movers']['traj'] != june['movers']['traj']:
            for nm in o['movers']['traj']:
                rep("    " + cmp_lists(f"traj {nm}", o['movers']['traj'][nm], june['movers']['traj'][nm]))
        rep(f"  mechanism.corr: {o['mechanism']['corr']} vs file {june['mechanism']['corr']}")
        rep(f"  mechanism.cities identical: {o['mechanism']['cities'] == june['mechanism']['cities']}")
        if o['mechanism']['cities'] != june['mechanism']['cities']:
            A = {c['name']: c for c in o['mechanism']['cities']}
            Bm = {c['name']: c for c in june['mechanism']['cities']}
            rep(f"    only rebuilt: {sorted(set(A) - set(Bm))} | only file: {sorted(set(Bm) - set(A))}")
            for nm in A:
                if nm in Bm and A[nm] != Bm[nm]:
                    rep(f"    {nm}: {A[nm]} vs {Bm[nm]}")
        rep(f"  mechanism.profiles identical: {o['mechanism']['profiles'] == june['mechanism']['profiles']}")
        rep(f"  mechanism unmatched by the name join (excluded): {dg['mech_unmatched']}")
        rep("")
        rep("== VALIDATION A: current localities.json, K13-K25, weights=kosher (CONTINUE §3.1 values) ==")
        cur = load(a.loc)
        o2, dg2 = build(cur, core, soc, ks, "kosher", boot=False)
        S, N = o2["sorting"], o2["nationalization"]
        rep(f"  panel n = {o2['n']}   (documented 917)")
        rep(f"  wsd_rh K13/K25 = {S['wsd_rh'][0]} / {S['wsd_rh'][-1]}   (documented 17.48 / 26.06)")
        rep(f"  p90_p10 K13/K25 = {S['p90_p10'][0]} / {S['p90_p10'][-1]}   (documented 39.69 / 74.04)")
        rep(f"  dissim K13/K25 = {S['dissim'][0]} / {S['dissim'][-1]}   (documented 0.2675 / 0.4388)")
        rep(f"  swing first / min = {N['wsd_swing'][0]} / {min(N['wsd_swing'])}   (documented 7.45 / 2.39)")
        o3, _ = build(cur, core, soc, ks, "bzb_or_kosher", boot=False)
        rep(f"  [same data, June weights bzb_or_kosher]: n {o3['n']} wsd {o3['sorting']['wsd_rh'][0]}/"
            f"{o3['sorting']['wsd_rh'][-1]} p90p10 {o3['sorting']['p90_p10'][0]}/{o3['sorting']['p90_p10'][-1]} "
            f"dissim {o3['sorting']['dissim'][0]}/{o3['sorting']['dissim'][-1]} swing "
            f"{o3['nationalization']['wsd_swing'][0]}/{min(o3['nationalization']['wsd_swing'])}")
        with open(REPORT_PATH.replace(".txt", "_validation.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(report) + "\n")
        print("validation report -> " + REPORT_PATH.replace(".txt", "_validation.txt"))
        return

    ks = [str(k) for k in range(a.kmin, kmax + 1)]
    out, dg = build(load(a.loc), core, soc, ks, a.weights, boot=True)
    S, N, CI = out["sorting"], out["nationalization"], out["ci"]
    rep(f"== findings_data K{ks[0]}-K{ks[-1]}  weights={a.weights}  B={B_BOOT} seed={SEED} ==")
    rep(f"panel n = {out['n']}")
    for f in ["wsd_rh", "p90_p10", "dissim", "bimod", "wmean_rh", "p10", "median", "p90"]:
        rep(f"sorting.{f}: {S[f]}")
    rep(f"nationalization.wsd_swing: {N['wsd_swing']}")
    rep(f"nationalization.natl_swing: {N['natl_swing']}")
    rep(f"ci.slopes: {CI['slopes']}")
    rep(f"ci.change: {CI['change']}")
    rep(f"movers.left_list: {out['movers']['left_list']}")
    rep(f"movers.right_list: {out['movers']['right_list']}")
    rep(f"mechanism.corr: {out['mechanism']['corr']}")
    rep(f"mechanism.profiles: {out['mechanism']['profiles']}")
    rep(f"mechanism unmatched by the name join (excluded): {dg['mech_unmatched']}")
    rep(f"missing featured: {dg['missing_featured']} | missing profiles: {dg['missing_profiles']}")
    if not a.dry_run:
        bak = OUT_PATH + ".bak_prek26"
        if not os.path.exists(bak):
            shutil.copyfile(OUT_PATH, bak)
            rep(f"backup written: {bak}")
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False)
        rep(f"written: {OUT_PATH}")
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n")
    print(f"done (n={out['n']}, K{ks[0]}-K{ks[-1]}, dry_run={a.dry_run}); report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
