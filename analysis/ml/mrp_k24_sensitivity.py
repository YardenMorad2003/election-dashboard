# -*- coding: utf-8 -*-
"""ML project 6: K24 bloc-definition sensitivity — where do Bennett/Saar
voters "belong" demographically?

K24 is the MRP's worst election (v4 MAE 15.8pp) — the Bennett/Saar lists
(ימינה + תקווה חדשה, the opp_right lineage) sit outside the right-haredi
column in the site's bloc definition. This script refits a K24-ONLY model
(same spec as v4: rel + acad + age65 + abroad + rel x acad) under two
outcome definitions, moving BOTH sides of the validation together:

  A. Bennett/Saar as RIGHT      — survey: Yamina/Tikva-Hadasha voters
     count as rh; actual: rh + opp_right lineage share.
  B. Bennett/Saar as CENTER-LEFT — the site's definition (v4 baseline),
     refit K24-only for apples-to-apples.

If A validates better, the 2021 electorate of these lists still lived in
demographically-right neighborhoods (a temporary elite defection); if B,
the voters themselves had crossed. Liberman (beiteinu lineage) stays
outside rh in both versions.

Run from repo root: python -X utf8 analysis/ml/mrp_k24_sensitivity.py
Output: analysis/ml/out/mrp_k24_sensitivity_report.txt
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


def ipf4(seed, margins, iters=200):
    J = seed.copy()
    for _ in range(iters):
        for ax, m in enumerate(margins):
            axes = tuple(i for i in range(4) if i != ax)
            s = J.sum(axis=axes)
            shape = [1, 1, 1, 1]
            shape[ax] = -1
            J *= (m / np.where(s > 0, s, 1)).reshape(shape)
    return J / J.sum()


def main():
    rep = ['K24 SENSITIVITY — Bennett/Saar as right vs center-left',
           '=' * 60]

    # ---- K24 individuals ----
    cfg = bim.CFG['24']
    df, vl = bim.bst.read_wave(f"{bim.INES}/{cfg['path']}",
                               categoricals=True)
    raw = df[cfg['vote']].astype(str)
    bs_mask = raw.str.contains('Yamina') | raw.str.contains('Tikva Hadasha')
    votes = bim.bst.map_series(df[cfg['vote']],
                               f"{cfg['wave']}:{cfg['vote']}", cfg['wave'],
                               value_labels=None)
    voters = votes.isin(bim.BLOCS)
    wvar = bim.bst.pick_weight(df, voters, cfg['weights'])
    w = pd.to_numeric(df[wvar], errors='coerce').fillna(0) if wvar \
        else pd.Series(1.0, index=df.index)
    jm, _ = bim.jewish_mask(df, vl, cfg['sector'], True)
    rel, _ = bim.rel_tier(df, vl, cfg['rel'], True)
    acad, _ = bim.edu_binary(df, vl, cfg['edu'], True)
    age = pd.to_numeric(df[cfg['age'][1]], errors='coerce')
    age65 = age.map(lambda v: None if pd.isna(v) or v < 18
                    else bool(v >= 65))
    abroad = pd.to_numeric(df['v134'], errors='coerce').between(1900, 2023)
    J = voters & jm & rel.notna() & acad.notna() & age65.notna()
    tiers = sorted(rel[J].unique().tolist())
    rh_B = votes.isin(bim.RH)
    rh_A = rh_B | bs_mask
    rep.append('K24 modeled Jewish n=%d; Bennett/Saar voters among them: %d'
               % (int(J.sum()), int((J & bs_mask).sum())))
    rep.append('\nsurvey rh by tier under each definition (weighted):')
    for t in tiers:
        m = J & (rel == t)
        a = 100 * float(w[m & rh_A].sum()) / float(w[m].sum())
        b = 100 * float(w[m & rh_B].sum()) / float(w[m].sum())
        rep.append('  %-8s B(site) %5.1f%%   A(+Bennett/Saar) %5.1f%%  (n=%d)'
                   % (t, b, a, int(m.sum())))

    def design(rel_s, acad_s, age_s, ab_s):
        return np.column_stack([
            *[(rel_s == t).astype(float) for t in tiers[1:]],
            acad_s.astype(float), age_s.astype(float), ab_s.astype(float),
            *[((rel_s == t) & acad_s).astype(float) for t in tiers[1:]]])
    X = design(rel[J], acad[J].astype(bool), age65[J].astype(bool),
               abroad[J])

    def cell_fn(y):
        m = LogisticRegression(C=1.0, max_iter=3000)
        m.fit(X, y[J].astype(int), sample_weight=w[J])

        def cp(tier, ac, a65, ab):
            r = pd.Series([tier])
            return float(m.predict_proba(design(
                r, pd.Series([bool(ac)]), pd.Series([bool(a65)]),
                pd.Series([bool(ab)])))[0, 1])
        return np.array([[[[cp(t, a, g, b) for b in (0, 1)]
                           for g in (0, 1)] for a in (0, 1)] for t in tiers])
    P = {'A': cell_fn(rh_A), 'B': cell_fn(rh_B)}
    A_ = voters & ~jm
    p_arab = (float(w[A_ & rh_B].sum()) / float(w[A_].sum())
              if float(w[A_].sum()) > 0 else 0.025)

    seed = np.full((len(tiers), 2, 2, 2), 0.5)
    for i, t in enumerate(tiers):
        for a in (0, 1):
            for g in (0, 1):
                for b in (0, 1):
                    m = (J & (rel == t) & (acad == bool(a)) &
                         (age65 == bool(g)) & (abroad == bool(b)))
                    seed[i, a, g, b] += float(w[m].sum())
    seed /= seed.sum()

    # ---- frame (v2/v4 NNLS mixtures) ----
    cen = pd.read_csv(os.path.join(AN, 'statarea_inputs',
                                   'cbs_census_2022_statarea.csv'))
    cen = cen[cen.StatArea.notna() & cen.LocalityCode.notna()].copy()
    cen['key'] = (cen.LocalityCode.astype(int).astype(str) + '|' +
                  cen.StatArea.astype(int).astype(str))
    jc = cen[cen.ReligionHeb == 'יהודים'].copy()
    jc['tier'] = jc.hh_MidatDatiyut.map(DAT_MAP)
    Z = jc[MIX_COVS].astype(float)
    Z = Z.fillna(Z.median())
    Zs = (Z - Z.mean()) / Z.std().replace(0, 1)
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
    order = [t for t in ('haredi', 'dati', 'masorti', 'hiloni')
             if t in tiers]
    Aaug = np.vstack([np.column_stack([anchors[t] for t in order]),
                      10 * np.ones(len(order))])
    mixes = []
    for zrow in Zs.to_numpy():
        w_, _ = nnls(Aaug, np.concatenate([zrow, [10.0]]))
        s = w_.sum()
        mixes.append(w_ / s if s > 0 else np.full(len(order), .25))
    jc[['mix_' + t for t in order]] = np.vstack(mixes)
    abr_med = float(jc.j_abr_pcnt.median())

    # ---- actual K24 outcomes under both definitions ----
    v = pd.read_csv(os.path.join(OUT, 'votes_k24.csv'))
    v['key'] = v.semel.astype(str) + '|' + v.sa.astype(str)
    v['rh_B'] = v[BLOC_RH].sum(axis=1)
    v['rh_A'] = v['rh_B'] + v['opp_right']
    jc_i = jc.set_index('key')
    cen_i = cen.set_index('key')

    for ver, ycol in (('B  (site: Bennett/Saar = center-left)', 'rh_B'),
                      ('A  (Bennett/Saar = right)', 'rh_A')):
        Pv = P[ycol[-1]]
        rows = []
        for r in v.itertuples():
            if r.key in jc_i.index:
                c = jc_i.loc[r.key]
                if pd.isna(c.AcadmCert_pcnt):
                    continue
                pa = float(c.AcadmCert_pcnt) / 100
                at = (c.age20_64_pcnt or 0) + (c.age65_pcnt or 0)
                w65 = float(c.age65_pcnt) / at if at and at > 0 else 0.12
                pab = (float(c.j_abr_pcnt) if pd.notna(c.j_abr_pcnt)
                       else abr_med) / 100
                m_tier = np.array([c['mix_' + t] if t in order else 0.0
                                   for t in tiers])
                Jn = ipf4(seed, [m_tier, np.array([1 - pa, pa]),
                                 np.array([1 - w65, w65]),
                                 np.array([1 - pab, pab])])
                rows.append(('jewish', 100 * float((Jn * Pv).sum()),
                             getattr(r, ycol), r.valid))
            elif r.key in cen_i.index and \
                    str(cen_i.loc[r.key, 'ReligionHeb']) in ARAB_REL:
                rows.append(('arab', 100 * p_arab, getattr(r, ycol),
                             r.valid))
        d = pd.DataFrame(rows, columns=['kind', 'rh_hat', 'rh', 'valid'])
        rep.append('\n--- version %s ---' % ver)
        for tag, dd in (('all', d), ('jewish', d[d.kind == 'jewish'])):
            wv = dd['valid'].to_numpy()
            y, yh = dd['rh'].to_numpy(), dd['rh_hat'].to_numpy()
            mae = np.average(np.abs(y - yh), weights=wv)
            ybar = np.average(y, weights=wv)
            r2 = 1 - np.average((y - yh)**2, weights=wv) / \
                np.average((y - ybar)**2, weights=wv)
            rep.append('%-8s n=%4d  r=%.3f  R2=%.3f  MAE=%.1fpp'
                       % (tag, len(dd), np.corrcoef(y, yh)[0, 1], r2, mae))

    rep.append('\n(v4 pooled-model K24 baseline, definition B: all '
               'r=0.755 MAE=15.8; jewish r=0.681 MAE=16.9)')
    with open(os.path.join(OUT, 'mrp_k24_sensitivity_report.txt'), 'w',
              encoding='utf-8') as f:
        f.write('\n'.join(rep) + '\n')
    print('\n'.join(rep))


if __name__ == '__main__':
    main()
