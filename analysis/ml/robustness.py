# -*- coding: utf-8 -*-
"""ML arc rigor add-ons:
(a) split-conformal prediction intervals for project 2's rh model —
    city-blocked calibration so coverage is honest for unseen places;
(b) GMM robustness — do the frozen-pole findings (Arab/Haredi stay rates,
    Labor-segment extinction) survive k=8/9/10?

Run from repo root: python -X utf8 analysis/ml/robustness.py
Appends results to analysis/ml/out/robustness_report.txt
"""
import csv
import json
import os
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.mixture import GaussianMixture
from sklearn.model_selection import GroupShuffleSplit

OUT = os.path.join('analysis', 'ml', 'out')
BLOC_RH = ['likud', 'shas', 'utj', 'natrel', 'far_right']
SHARED = ['pop', 'density', 'age_med', 'age0_19', 'age65', 'acad', 'work',
          'orig_il', 'orig_eur', 'orig_asia', 'orig_afr', 'orig_am',
          'aliya02', 'chld', 'hh_size', 'own', 'rent', 'no_car']
KS = ['16', '17', '18', '19', '20', '21', '22', '23', '24', '25']
ERA = {'16': '1995', '17': '1995', '18': '2009', '19': '2009', '20': '2009',
       '21': '2022', '22': '2022', '23': '2022', '24': '2022', '25': '2022'}


def conformal(k, era, rep):
    cen = pd.read_csv(os.path.join(OUT, 'census_%s.csv' % era))
    cen['key'] = cen.semel.astype(str) + '|' + cen.sa.astype(str)
    v = pd.read_csv(os.path.join(OUT, 'votes_k%s.csv' % k))
    v['key'] = v.semel.astype(str) + '|' + v.sa.astype(str)
    df = v.merge(cen.drop(columns=['semel', 'sa']), on='key')
    X = df[[c for c in SHARED if c in df.columns]].astype(float).to_numpy()
    y = df[BLOC_RH].sum(axis=1).to_numpy()
    g = df['semel'].to_numpy()
    w = df['valid'].to_numpy()
    # city-blocked 3-way split: train / calibrate / test
    gss = GroupShuffleSplit(n_splits=1, test_size=0.4, random_state=0)
    tr, rest = next(gss.split(X, y, g))
    gss2 = GroupShuffleSplit(n_splits=1, test_size=0.5, random_state=1)
    cal_i, te_i = next(gss2.split(X[rest], y[rest], g[rest]))
    cal, te = rest[cal_i], rest[te_i]
    m = HistGradientBoostingRegressor(max_iter=300, random_state=0)
    m.fit(X[tr], y[tr], sample_weight=w[tr])
    q = np.quantile(np.abs(y[cal] - m.predict(X[cal])), 0.9)
    resid = np.abs(y[te] - m.predict(X[te]))
    cover = float(np.average(resid <= q, weights=w[te]))
    rep.append('K%s conformal (90%% nominal, city-blocked): half-width '
               '%.1fpp, achieved coverage %.1f%% (n_test=%d cities-held-out)'
               % (k, q, 100 * cover, len(te)))


def load_scores():
    pca = json.load(open(os.path.join(OUT, 'pca_loadings.json'),
                         encoding='utf-8'))
    mu, V = np.array(pca['mu']), np.array(pca['components'])
    rows, meta = [], []
    for k in KS:
        with open(os.path.join(OUT, 'votes_k%s.csv' % k),
                  encoding='utf-8') as f:
            rd = csv.DictReader(f)
            lin = [c for c in rd.fieldnames
                   if c not in ('semel', 'sa', 'valid', 'turnout')]
            for r in rd:
                x = np.array([float(r[l]) for l in lin])
                rows.append((x - mu) @ V.T)
                meta.append((k, '%s|%s' % (r['semel'], r['sa']),
                             float(r['valid'])))
    return np.vstack(rows), meta, lin, mu, V


def gmm_stability(rep):
    S, meta, lin, mu, V = load_scores()
    l09 = json.load(open(os.path.join(OUT, 'links_2009_to_2022.json'),
                         encoding='utf-8'))
    for kk in (8, 9, 10):
        gm = GaussianMixture(kk, covariance_type='full', random_state=1,
                             n_init=3).fit(S)
        hard = gm.predict(S)
        prof = gm.means_ @ V + mu
        arab_c = int(np.argmax(prof[:, lin.index('arab')]))
        har_c = int(np.argmax(prof[:, lin.index('utj')]))
        lab_c = int(np.argmax(prof[:, lin.index('labor')]))
        seg_of = {(m[0], m[1]): h for m, h in zip(meta, hard)}
        v25 = {m[1]: m[2] for m in meta if m[0] == '25'}

        def seg(key, k):
            kkey = key if ERA[k] == '2022' else l09.get(key, [None])[0]
            return seg_of.get((k, kkey)) if kkey else None
        stay = defaultdict(lambda: [0.0, 0.0])
        lab_share = {k: [0.0, 0.0] for k in KS}
        # labor-segment vote share per election
        for i, (k, key, w) in enumerate(meta):
            lab_share[k][1] += w
            if hard[i] == lab_c:
                lab_share[k][0] += w
        for key, w in v25.items():
            a, b = seg(key, '18'), seg(key, '25')
            if a is None or b is None:
                continue
            for c, tag in ((arab_c, 'arab'), (har_c, 'haredi')):
                if a == c:
                    stay[tag][1] += w
                    if b == c:
                        stay[tag][0] += w
        ls = {k: 100 * a / b for k, (a, b) in lab_share.items()}
        rep.append('k=%d: arab stay %.1f%%, haredi stay %.1f%%; '
                   'labor-segment share K20 %.1f%% -> K21 %.1f%% -> K25 %.1f%%'
                   % (kk, 100 * stay['arab'][0] / stay['arab'][1],
                      100 * stay['haredi'][0] / stay['haredi'][1],
                      ls['20'], ls['21'], ls['25']))


def main():
    rep = ['ROBUSTNESS ADD-ONS', '=' * 50,
           '-- conformal intervals (project 2, rh, shared features) --']
    conformal('18', '2008', rep)
    conformal('25', '2022', rep)
    rep.append('')
    rep.append('-- GMM stability of headline findings across k --')
    gmm_stability(rep)
    with open(os.path.join(OUT, 'robustness_report.txt'), 'w',
              encoding='utf-8') as f:
        f.write('\n'.join(rep) + '\n')
    print('\n'.join(rep))


if __name__ == '__main__':
    main()
