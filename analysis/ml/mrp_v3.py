# -*- coding: utf-8 -*-
"""ML project 6, v3: v2 + tier-level TURNOUT differentials.

The frame gives POPULATION composition; the target (rh share) is among
VOTERS. v3 adds a turnout-propensity layer estimated from INES F1 ("did you
vote"), applied as cell weights: w'_c = w_c * t_c. Survey turnout is
overreported (92% vs actual 70.6%) — only the RELATIVE tier/education/age
gradient is used (weights are renormalized per SA), which is the defensible
part. Everything else is identical to v2.

v1's diagnosis: deterministic datiyut labels force mixed SAs into pure cells
(hiloni-labeled middle underpredicts by 10-30pp). CBS publishes no SA-level
religiosity shares (and the census portal's profile API is down), so v2
estimates each Jewish SA's religiosity MIXTURE from vote-free demographics:

  1. anchor profiles: covariate signature of each tier (fertility, median
     age, academic %, married-18-34 %, household size, %0-19) from label-
     homogeneous SAs (haredi/hiloni anchors sharpened by fertility split);
  2. per-SA tier weights: NNLS fit of the SA's covariates to a convex
     combination of anchors (sum-to-1, non-negative);
  3. per-SA joint (tier x acad x age65) via IPF: seed = INES-2022 national
     weighted joint, margins = (NNLS tier mix, SA acad share, SA age share);
  4. SAME v1 logistic cell model + Arab cell -> poststratify -> validate.

The vote model is UNCHANGED from v1, so any validation gain is attributable
purely to the frame. No vote data enters the frame construction (no leakage).

Run from repo root: python -X utf8 analysis/ml/mrp_v2.py   (~2 min)
Outputs: analysis/ml/out/mrp_v2_{report.txt,sa.csv}
"""
import importlib.util
import os

import numpy as np
import pandas as pd
from scipy.optimize import nnls
from sklearn.linear_model import LogisticRegression

HERE = os.path.dirname(os.path.abspath(__file__))
AN = os.path.dirname(HERE)
OUT = os.path.join(HERE, 'out')
BLOC_RH = ['likud', 'shas', 'utj', 'natrel', 'far_right']

spec = importlib.util.spec_from_file_location(
    'bim', os.path.join(AN, 'build_ines_micro.py'))
bim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bim)

DAT_MAP = {'חילוני': 'hiloni', 'מסורתי': 'masorti',
           'דתי/ דתי מאוד': 'dati', 'חרדי': 'haredi'}
ARAB_REL = {'מוסלמים', 'נוצרים', 'דרוזים'}
MIX_COVS = ['ChldBorn_avg', 'age_median', 'AcadmCert_pcnt',
            'married18_34_pcnt', 'size_avg', 'age0_19_pcnt']


def ipf(seed, m_tier, m_acad, m_age, iters=200):
    """seed[t,a,g] -> joint matching the three margins."""
    J = seed.copy()
    for _ in range(iters):
        s = J.sum(axis=(1, 2))
        J *= (m_tier / np.where(s > 0, s, 1))[:, None, None]
        s = J.sum(axis=(0, 2))
        J *= (m_acad / np.where(s > 0, s, 1))[None, :, None]
        s = J.sum(axis=(0, 1))
        J *= (m_age / np.where(s > 0, s, 1))[None, None, :]
    return J / J.sum()


def main():
    rep = ['MRP v3 — v2 frame + INES turnout differentials',
           '=' * 60]

    # ---- INES individuals + v1 model (identical to mrp_v1) ----
    cfg = bim.CFG['25']
    df, vl = bim.bst.read_wave(f"{bim.INES}/{cfg['path']}", categoricals=True)
    votes = bim.bst.map_series(df[cfg['vote']], f"2022:{cfg['vote']}", '2022',
                               value_labels=None)
    voters = votes.isin(bim.BLOCS)
    wvar = bim.bst.pick_weight(df, voters, cfg['weights'])
    w = pd.to_numeric(df[wvar], errors='coerce').fillna(0) if wvar \
        else pd.Series(1.0, index=df.index)
    jm, _ = bim.jewish_mask(df, vl, cfg['sector'], True)
    rel, _ = bim.rel_tier(df, vl, cfg['rel'], True)
    acad, _ = bim.edu_binary(df, vl, cfg['edu'], True)
    age = pd.to_numeric(df[cfg['age'][1]], errors='coerce')
    age65 = age.map(lambda v: None if pd.isna(v) or v < 18 else bool(v >= 65))
    rh = votes.isin(bim.RH)
    J = voters & jm & rel.notna() & acad.notna() & age65.notna()
    tiers = sorted(rel[J].unique().tolist())
    X = np.column_stack([
        *[(rel[J] == t).astype(float) for t in tiers[1:]],
        acad[J].astype(float), age65[J].astype(float),
        *[((rel[J] == t) & acad[J].astype(bool)).astype(float)
          for t in tiers[1:]]])
    model = LogisticRegression(C=1.0, max_iter=2000)
    model.fit(X, rh[J].astype(int), sample_weight=w[J])

    def cell_p(tier, ac, a65):
        x = np.zeros(X.shape[1])
        nt = len(tiers) - 1
        if tier != tiers[0]:
            x[tiers[1:].index(tier)] = 1
        x[nt] = ac
        x[nt + 1] = a65
        if tier != tiers[0] and ac:
            x[nt + 2 + tiers[1:].index(tier)] = 1
        return float(model.predict_proba([x])[0, 1])
    P = np.array([[[cell_p(t, a, g) for g in (0, 1)] for a in (0, 1)]
                  for t in tiers])          # [tier, acad, age65]
    A = voters & ~jm
    p_arab = float(w[A & rh].sum()) / float(w[A].sum())

    # ---- turnout propensity (F1), Jewish respondents incl. nonvoters ----
    f1 = df['F1'].astype(str)
    voted = f1.str.contains('Yes')
    answered = voted | f1.str.contains('No')
    T = answered & jm & rel.notna() & acad.notna() & age65.notna()
    Xt = np.column_stack([
        *[(rel[T] == t).astype(float) for t in tiers[1:]],
        acad[T].astype(float), age65[T].astype(float)])
    tm = LogisticRegression(C=1.0, max_iter=2000)
    tm.fit(Xt, voted[T].astype(int), sample_weight=w[T])

    def cell_t(tier, ac, a65):
        x = np.zeros(Xt.shape[1])
        nt = len(tiers) - 1
        if tier != tiers[0]:
            x[tiers[1:].index(tier)] = 1
        x[nt] = ac
        x[nt + 1] = a65
        return float(tm.predict_proba([x])[0, 1])
    Tmat = np.array([[[cell_t(t, a, g) for g in (0, 1)] for a in (0, 1)]
                     for t in tiers])
    rep.append('reported turnout by tier (survey-inflated; only the gradient'
               ' is used):')
    for i, t in enumerate(tiers):
        m = T & (rel == t)
        rep.append('  %-8s %.1f%% (n=%d)' % (
            t, 100 * float(w[m & voted].sum()) / float(w[m].sum()),
            int(m.sum())))

    # INES national joint as IPF seed (weighted; +0.5 smoothing)
    seed = np.full((len(tiers), 2, 2), 0.5)
    for i, t in enumerate(tiers):
        for a in (0, 1):
            for g in (0, 1):
                m = J & (rel == t) & (acad == bool(a)) & (age65 == bool(g))
                seed[i, a, g] += float(w[m].sum())
    seed /= seed.sum()

    # ---- mixture frames ----
    cen = pd.read_csv(os.path.join(AN, 'statarea_inputs',
                                   'cbs_census_2022_statarea.csv'))
    cen = cen[cen.StatArea.notna() & cen.LocalityCode.notna()].copy()
    cen['key'] = (cen.LocalityCode.astype(int).astype(str) + '|' +
                  cen.StatArea.astype(int).astype(str))
    jc = cen[(cen.ReligionHeb == 'יהודים')].copy()
    jc['tier'] = jc.hh_MidatDatiyut.map(DAT_MAP)   # NB: columns swapped in CSV
    Z = jc[MIX_COVS].astype(float)
    n_imp = int(Z.isna().any(axis=1).sum())
    Z = Z.fillna(Z.median())
    mu, sd = Z.mean(), Z.std().replace(0, 1)
    Zs = (Z - mu) / sd

    anchors = {}
    for t, lbl in (('haredi', 'חרדי'), ('dati', 'דתי/ דתי מאוד'),
                   ('masorti', 'מסורתי'), ('hiloni', 'חילוני')):
        sub = Zs[jc.tier == DAT_MAP[lbl]]
        fert = Z.loc[sub.index, 'ChldBorn_avg']
        if t == 'haredi':
            sub = sub[fert >= fert.median()]
        if t == 'hiloni':
            sub = sub[fert <= fert.median()]
        anchors[t] = sub.mean().to_numpy()
    order = [t for t in ('haredi', 'dati', 'masorti', 'hiloni') if t in tiers]
    Amat = np.column_stack([anchors[t] for t in order])
    # augmented sum-to-1 row (weight 10) keeps NNLS weights on the simplex
    Aaug = np.vstack([Amat, 10 * np.ones(len(order))])

    def mix_of(zrow):
        b = np.concatenate([zrow, [10.0]])
        w_, _ = nnls(Aaug, b)
        s = w_.sum()
        return w_ / s if s > 0 else np.full(len(order), 1 / len(order))

    mixes = np.vstack([mix_of(z) for z in Zs.to_numpy()])
    jc[['mix_' + t for t in order]] = mixes
    rep.append('mixture sanity — mean estimated tier weights by census label:')
    for lbl, t in DAT_MAP.items():
        sub = jc[jc.tier == t]
        ms = sub[['mix_' + o for o in order]].mean()
        rep.append('  label %-14s n=%4d  ' % (lbl, len(sub)) + '  '.join(
            '%s %.2f' % (o, ms['mix_' + o]) for o in order))

    # ---- poststratify ----
    v25 = pd.read_csv(os.path.join(OUT, 'votes_k25.csv'))
    v25['key'] = v25.semel.astype(str) + '|' + v25.sa.astype(str)
    v25['rh'] = v25[BLOC_RH].sum(axis=1)
    tier_idx = [tiers.index(t) for t in order]
    rows = []
    jset = set(jc.key)
    jc_i = jc.set_index('key')
    cen_i = cen.set_index('key')
    for r in v25.itertuples():
        if r.key in jset:
            c = jc_i.loc[r.key]
            if pd.isna(c.AcadmCert_pcnt):
                continue
            pa = float(c.AcadmCert_pcnt) / 100
            at = (c.age20_64_pcnt or 0) + (c.age65_pcnt or 0)
            w65 = float(c.age65_pcnt) / at if at and at > 0 else 0.12
            m_tier = np.zeros(len(tiers))
            for oi, t in enumerate(order):
                m_tier[tiers.index(t)] = c['mix_' + t]
            Jn = ipf(seed, m_tier, np.array([1 - pa, pa]),
                     np.array([1 - w65, w65]))
            Jv = Jn * Tmat
            Jv /= Jv.sum()
            rh_hat = 100 * float((Jv * P).sum())
            rows.append({'key': r.key, 'kind': 'jewish',
                         'rh_hat': round(rh_hat, 2), 'rh': r.rh,
                         'valid': r.valid,
                         'relig': 'יהודים'})
        elif r.key in cen_i.index:
            relig = str(cen_i.loc[r.key, 'ReligionHeb'])
            if relig in ARAB_REL:
                rows.append({'key': r.key, 'kind': 'arab',
                             'rh_hat': round(100 * p_arab, 2), 'rh': r.rh,
                             'valid': r.valid, 'relig': relig})
    res = pd.DataFrame(rows)
    rep.append('\nscored %d SAs (%d jewish, %d arab)'
               % (len(res), (res.kind == 'jewish').sum(),
                  (res.kind == 'arab').sum()))

    def stats(d, tag):
        wv = d['valid'].to_numpy()
        y, yh = d['rh'].to_numpy(), d['rh_hat'].to_numpy()
        ybar = np.average(y, weights=wv)
        r2 = 1 - np.average((y - yh)**2, weights=wv) / \
            np.average((y - ybar)**2, weights=wv)
        mae = np.average(np.abs(y - yh), weights=wv)
        r = np.corrcoef(y, yh)[0, 1] if y.std() > 0 and yh.std() > 0 else \
            float('nan')
        rep.append('%-24s n=%4d  r=%.3f  R2=%.3f  MAE=%.1fpp'
                   % (tag, len(d), r, r2, mae))
    rep.append('\nvalidation vs ACTUAL K25 (valid-vote weighted) — '
               'v2 in parens:')
    stats(res, 'all scored SAs')
    rep.append('   (v2 all: r=0.821  R2=0.645  MAE=12.6pp)')
    stats(res[res.kind == 'jewish'], 'Jewish SAs')
    rep.append('   (v2 jewish: r=0.738  R2=0.468  MAE=13.2pp)')

    rep.append('\ncalibration (Jewish SAs, deciles of prediction):')
    jd = res[res.kind == 'jewish'].copy()
    jd['dec'] = pd.qcut(jd.rh_hat, 10, labels=False, duplicates='drop')
    for d_, g in jd.groupby('dec'):
        rep.append('  d%d: pred %5.1f  actual %5.1f  (n=%d)'
                   % (d_, np.average(g.rh_hat, weights=g.valid),
                      np.average(g.rh, weights=g.valid), len(g)))

    rep.append('\nframe method: NNLS tier mixtures from vote-free census '
               'covariates %s;' % MIX_COVS)
    rep.append('anchors from label-homogeneous SAs (haredi/hiloni sharpened '
               'by fertility split); IPF joint seeded by the INES national '
               'tier x acad x age association. Vote model identical to v1; turnout layer new in v3.')
    res.to_csv(os.path.join(OUT, 'mrp_v3_sa.csv'), index=False)
    with open(os.path.join(OUT, 'mrp_v3_report.txt'), 'w',
              encoding='utf-8') as f:
        f.write('\n'.join(rep) + '\n')
    print('\n'.join(rep))


if __name__ == '__main__':
    main()
