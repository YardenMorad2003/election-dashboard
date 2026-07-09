# -*- coding: utf-8 -*-
"""ML project 6, v4: pooled waves (K21-K25) + born-abroad cell dimension.

Two lifts over v2 (which stays the single-wave baseline):
  POOLING  one weighted logistic on all five INES waves (2019 apr+sep panel,
           2020, 2021, 2022; ~5x the cell sample) with per-election
           intercepts — and validation against FIVE elections' actual SA
           results instead of one.
  ORIGIN   a 4th cell dimension: born abroad vs Israel-born. INES v134
           (immigration year; blank = Israel-born, refusals fold in) matches
           the census margin j_abr_pcnt (foreign-born share of Jews&others)
           — a clean construct pair. Cells: tier(4) x acad(2) x age65(2) x
           abroad(2) = 32, IPF over four margins seeded by the pooled joint.

Frame method (NNLS tier mixtures) identical to v2. Arab cell per election.

Run from repo root: python -X utf8 analysis/ml/mrp_v4.py   (~3 min)
Outputs: analysis/ml/out/mrp_v4_{report.txt,sa.csv}
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
KS = ['21', '22', '23', '24', '25']

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
    rep = ['MRP v4 — pooled K21-K25 waves + born-abroad dimension', '=' * 62]

    # ---- pooled individuals ----
    frames = []
    arab_p = {}
    file_cache = {}
    for k in KS:
        cfg = bim.CFG[k]
        path = f"{bim.INES}/{cfg['path']}"
        if path not in file_cache:
            file_cache[path] = bim.bst.read_wave(path, categoricals=True)
        df, vl = file_cache[path]
        votes = bim.bst.map_series(df[cfg['vote']],
                                   f"{cfg['wave']}:{cfg['vote']}",
                                   cfg['wave'], value_labels=None)
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
        yr = pd.to_numeric(df['v134'], errors='coerce')
        abroad = yr.between(1900, 2023)
        rh = votes.isin(bim.RH)
        if k == '24':
            # USER RULING (after the K24 sensitivity): Bennett's Yamina counts
            # as right; Saar's Tikva Hadasha stays opposition-right. Matches
            # the tensor side, where ימינה K24 sits in the natrel lineage.
            rh = rh | df[cfg['vote']].astype(str).str.contains('Yamina')
        J = voters & jm & rel.notna() & acad.notna() & age65.notna()
        sub = pd.DataFrame({
            'k': k, 'rel': rel[J], 'acad': acad[J].astype(bool),
            'age65': age65[J].astype(bool), 'abroad': abroad[J],
            'rh': rh[J].astype(int), 'w': w[J]})
        sub['w'] = sub.w / sub.w.mean()
        frames.append(sub)
        A = voters & ~jm
        if float(w[A].sum()) > 0:
            arab_p[k] = float(w[A & rh].sum()) / float(w[A].sum())
        elif int(A.sum()) > 0:      # weights zero out the Arab sample -> unweighted
            arab_p[k] = float((A & rh).sum()) / float(A.sum())
        else:                        # no Arab voters in this wave's subset
            arab_p[k] = arab_p.get(KS[KS.index(k) - 1], 0.05)
        rep.append('K%s: modeled Jewish n=%d (abroad %.0f%%), arab cell '
                   'rh=%.1f%% (n=%d)'
                   % (k, len(sub), 100 * sub.abroad.mean(),
                      100 * arab_p[k], int(A.sum())))
    pool = pd.concat(frames, ignore_index=True)
    tiers = sorted(pool.rel.unique().tolist())
    rep.append('pooled modeled n=%d across %d waves' % (len(pool), len(KS)))

    def design(df_):
        cols = [
            *[(df_.rel == t).astype(float) for t in tiers[1:]],
            df_.acad.astype(float), df_.age65.astype(float),
            df_.abroad.astype(float),
            *[((df_.rel == t) & df_.acad).astype(float) for t in tiers[1:]],
            *[(df_.k == k).astype(float) for k in KS[:-1]],  # base = K25
        ]
        return np.column_stack(cols)
    X = design(pool)
    model = LogisticRegression(C=1.0, max_iter=3000)
    model.fit(X, pool.rh, sample_weight=pool.w)
    ab_coef = model.coef_[0][2 * (len(tiers) - 1) + 2]
    rep.append('born-abroad coefficient: %+.2f (log-odds toward rh)' % ab_coef)

    def cell_p(k, tier, ac, a65, ab):
        row = pd.DataFrame({'k': [k], 'rel': [tier], 'acad': [bool(ac)],
                            'age65': [bool(a65)], 'abroad': [bool(ab)]})
        return float(model.predict_proba(design(row))[0, 1])
    P = {k: np.array([[[[cell_p(k, t, a, g, b) for b in (0, 1)]
                        for g in (0, 1)] for a in (0, 1)] for t in tiers])
         for k in KS}

    # pooled joint seed (tier x acad x age65 x abroad)
    seed = np.full((len(tiers), 2, 2, 2), 0.5)
    for i, t in enumerate(tiers):
        for a in (0, 1):
            for g in (0, 1):
                for b in (0, 1):
                    m = ((pool.rel == t) & (pool.acad == bool(a)) &
                         (pool.age65 == bool(g)) & (pool.abroad == bool(b)))
                    seed[i, a, g, b] += float(pool.w[m].sum())
    seed /= seed.sum()

    # ---- frames (v2 NNLS mixtures) ----
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
    order = [t for t in ('haredi', 'dati', 'masorti', 'hiloni') if t in tiers]
    Aaug = np.vstack([np.column_stack([anchors[t] for t in order]),
                      10 * np.ones(len(order))])
    mixes = []
    for zrow in Zs.to_numpy():
        w_, _ = nnls(Aaug, np.concatenate([zrow, [10.0]]))
        s = w_.sum()
        mixes.append(w_ / s if s > 0 else np.full(len(order), .25))
    jc[['mix_' + t for t in order]] = np.vstack(mixes)
    abr_med = float(jc.j_abr_pcnt.median())

    # ---- poststratify + validate per election ----
    jc_i = jc.set_index('key')
    cen_i = cen.set_index('key')
    all_rows = []
    rep.append('\nvalidation vs actual results (valid-vote weighted):')
    rep.append('%-5s %-22s %6s %7s %8s' % ('K', 'slice', 'n', 'r', 'MAE'))
    for k in KS:
        v = pd.read_csv(os.path.join(OUT, 'votes_k%s.csv' % k))
        v['key'] = v.semel.astype(str) + '|' + v.sa.astype(str)
        v['rh'] = v[BLOC_RH].sum(axis=1)
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
                rh_hat = 100 * float((Jn * P[k]).sum())
                rows.append({'k': k, 'key': r.key, 'kind': 'jewish',
                             'rh_hat': round(rh_hat, 2), 'rh': r.rh,
                             'valid': r.valid})
            elif r.key in cen_i.index and \
                    str(cen_i.loc[r.key, 'ReligionHeb']) in ARAB_REL:
                rows.append({'k': k, 'key': r.key, 'kind': 'arab',
                             'rh_hat': round(100 * arab_p[k], 2),
                             'rh': r.rh, 'valid': r.valid})
        d = pd.DataFrame(rows)
        all_rows.append(d)

        def stats(dd, tag):
            wv = dd['valid'].to_numpy()
            y, yh = dd['rh'].to_numpy(), dd['rh_hat'].to_numpy()
            mae = np.average(np.abs(y - yh), weights=wv)
            r_ = np.corrcoef(y, yh)[0, 1] if y.std() > 0 and yh.std() > 0 \
                else float('nan')
            rep.append('%-5s %-22s %6d %7.3f %7.1fpp'
                       % ('K' + k, tag, len(dd), r_, mae))
        stats(d, 'all')
        stats(d[d.kind == 'jewish'], 'jewish')

    res = pd.concat(all_rows, ignore_index=True)
    rep.append('\n(v2 baseline, K25 only: all r=0.821 MAE=12.6; jewish '
               'r=0.738 MAE=13.2)')
    rep.append('\ncalibration K25 (Jewish SAs, deciles of prediction):')
    jd = res[(res.k == '25') & (res.kind == 'jewish')].copy()
    jd['dec'] = pd.qcut(jd.rh_hat, 10, labels=False, duplicates='drop')
    for d_, g in jd.groupby('dec'):
        rep.append('  d%d: pred %5.1f  actual %5.1f  (n=%d)'
                   % (d_, np.average(g.rh_hat, weights=g.valid),
                      np.average(g.rh, weights=g.valid), len(g)))

    res.to_csv(os.path.join(OUT, 'mrp_v4_sa.csv'), index=False)
    with open(os.path.join(OUT, 'mrp_v4_report.txt'), 'w',
              encoding='utf-8') as f:
        f.write('\n'.join(rep) + '\n')
    print('\n'.join(rep))


if __name__ == '__main__':
    main()
