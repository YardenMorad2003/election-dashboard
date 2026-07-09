# -*- coding: utf-8 -*-
"""ML project 2: how predictable is a neighborhood's vote from demographics —
and is predictability rising (= sorting)?

Per election: census features -> targets (right-haredi share; PC1; PC2),
Ridge (linear baseline) + HistGradientBoosting (nonlinear, NaN-native),
**spatially blocked CV** (GroupKFold on locality semel — held-out CITIES, so
scores measure generalization to unseen places, not spatial leakage), sample-
and score-weighted by valid votes.

Era caveats (disclose with results): census 2022 POSTdates K21/K22 by up to
3 years; census 2008 predates K19/K20 by up to 6. Feature sets differ across
eras (2008 has ses_cluster 1-20 + income; 2022 has wage/top2dec/datiyut) —
the headline series therefore compares eras on the SHARED feature subset,
with full-feature numbers reported alongside.

Run from repo root: python -X utf8 analysis/ml/predictability.py  (~2 min)
Outputs: analysis/ml/out/predictability_{report.txt,series.csv}
"""
import csv
import json
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold

OUT = os.path.join('analysis', 'ml', 'out')
ERAS = {'2008': ['18', '19', '20'], '2022': ['21', '22', '23', '24', '25']}
SHARED = ['pop', 'density', 'age_med', 'age0_19', 'age65', 'acad', 'work',
          'orig_il', 'orig_eur', 'orig_asia', 'orig_afr', 'orig_am',
          'aliya02', 'chld', 'hh_size', 'own', 'rent', 'no_car']
EXTRA = {'2008': ['ses_cluster', 'income', 'matric', 'pc'],
         '2022': ['med_wage', 'top2dec', 'ses2019_value', 'ses2021_value']}
CAT = {'2008': ['rel_dom'], '2022': ['religion', 'datiyut']}
BLOC_RH = ['likud', 'shas', 'utj', 'natrel', 'far_right']   # right-haredi
NPC = 2


def weighted_r2(y, yhat, w):
    ybar = np.average(y, weights=w)
    ss_res = np.average((y - yhat) ** 2, weights=w)
    ss_tot = np.average((y - ybar) ** 2, weights=w)
    return 1 - ss_res / ss_tot


def main():
    pca = json.load(open(os.path.join(OUT, 'pca_loadings.json'),
                         encoding='utf-8'))
    mu = np.array(pca['mu'])
    V = np.array(pca['components'])
    lineages = pca['lineages']

    rep = ['DEMOGRAPHIC PREDICTABILITY OF THE VOTE (held-out cities)',
           '=' * 64,
           'weighted OOS R^2, GroupKFold(5) by locality; w = valid votes', '']
    series = []
    imp_notes = []
    for era, ks in ERAS.items():
        cen = pd.read_csv(os.path.join(OUT, 'census_%s.csv' % era))
        cen['key'] = cen.semel.astype(str) + '|' + cen.sa.astype(str)
        cat_cols = [c for c in CAT[era] if c in cen.columns]
        cen = pd.get_dummies(cen, columns=cat_cols, dummy_na=True)
        dummies = [c for c in cen.columns
                   if any(c.startswith(cc + '_') for cc in cat_cols)]
        for k in ks:
            v = pd.read_csv(os.path.join(OUT, 'votes_k%s.csv' % k))
            v['key'] = v.semel.astype(str) + '|' + v.sa.astype(str)
            df = v.merge(cen.drop(columns=['semel', 'sa']), on='key')
            X_shared = df[[c for c in SHARED if c in df.columns]]
            full_cols = ([c for c in SHARED if c in df.columns] +
                         [c for c in EXTRA[era] if c in df.columns] + dummies)
            X_full = df[full_cols].astype(float)
            w = df['valid'].to_numpy()
            groups = df['semel'].to_numpy()
            S = (df[lineages].to_numpy() - mu) @ V.T
            targets = {'rh': df[BLOC_RH].sum(axis=1).to_numpy(),
                       'pc1': S[:, 0], 'pc2': S[:, 1]}
            for tname, y in targets.items():
                for mname, feats in (('shared', X_shared), ('full', X_full)):
                    Xn = feats.astype(float).to_numpy()
                    res = {}
                    for algo in ('ridge', 'hgb'):
                        yh = np.full(len(y), np.nan)
                        gkf = GroupKFold(n_splits=5)
                        for tr, te in gkf.split(Xn, y, groups):
                            if algo == 'ridge':
                                med = np.nanmedian(Xn[tr], axis=0)
                                Xtr = np.where(np.isnan(Xn[tr]), med, Xn[tr])
                                Xte = np.where(np.isnan(Xn[te]), med, Xn[te])
                                sd = Xtr.std(0)
                                sd[sd == 0] = 1
                                m = Ridge(alpha=10.0).fit(
                                    (Xtr - Xtr.mean(0)) / sd, y[tr],
                                    sample_weight=w[tr])
                                yh[te] = m.predict((Xte - Xtr.mean(0)) / sd)
                            else:
                                m = HistGradientBoostingRegressor(
                                    max_iter=300, learning_rate=0.1,
                                    max_depth=None, random_state=0)
                                m.fit(Xn[tr], y[tr], sample_weight=w[tr])
                                yh[te] = m.predict(Xn[te])
                        res[algo] = weighted_r2(y, yh, w)
                    series.append({'era': era, 'k': k, 'target': tname,
                                   'features': mname,
                                   'r2_ridge': round(res['ridge'], 4),
                                   'r2_hgb': round(res['hgb'], 4),
                                   'n': len(y)})
            # permutation importance snapshot on era endpoints (rh, full, HGB)
            if k in ('18', '25'):
                m = HistGradientBoostingRegressor(max_iter=300,
                                                  random_state=0)
                m.fit(X_full.to_numpy(), targets['rh'], sample_weight=w)
                pi = permutation_importance(m, X_full.to_numpy(),
                                            targets['rh'], n_repeats=5,
                                            random_state=0)
                top = sorted(zip(full_cols, pi.importances_mean),
                             key=lambda t: -t[1])[:8]
                imp_notes.append('K%s top rh predictors: %s' % (k, ', '.join(
                    '%s %.2f' % (c, v) for c, v in top)))

    rep.append('%-4s %-6s %-5s %-7s %8s %8s %6s'
               % ('K', 'era', 'tgt', 'feats', 'ridge', 'hgb', 'n'))
    for s in series:
        rep.append('%-4s %-6s %-5s %-7s %8.3f %8.3f %6d'
                   % ('K' + s['k'], s['era'], s['target'], s['features'],
                      s['r2_ridge'], s['r2_hgb'], s['n']))
    rep.append('')
    rep.extend(imp_notes)

    with open(os.path.join(OUT, 'predictability_report.txt'), 'w',
              encoding='utf-8') as f:
        f.write('\n'.join(rep) + '\n')
    with open(os.path.join(OUT, 'predictability_series.csv'), 'w',
              newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, list(series[0].keys()))
        wr.writeheader()
        wr.writerows(series)
    print('\n'.join(rep))


if __name__ == '__main__':
    main()
