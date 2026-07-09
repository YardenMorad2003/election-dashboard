# -*- coding: utf-8 -*-
"""Methodological check: is the POOLED common space faithful to each
election's own structure?

For every election, run a per-election weighted PCA (centered within the
election) and compare its leading axes to the pooled space's PC1/PC2:
  - loading congruence: max |cosine| between the pooled axis and any of the
    election's top-4 axes (allows sign flips and axis reordering);
  - score fidelity: within-election correlation between pooled-space scores
    and the election's own best-matching axis scores.
High values (>0.9) mean pooling imposes nothing — it just aligns signs and
scales; low values flag an era whose structure the common space distorts.

Run from repo root: python -X utf8 analysis/ml/congruence_check.py
Output: analysis/ml/out/congruence_report.txt
"""
import csv
import json
import os

import numpy as np

OUT = os.path.join('analysis', 'ml', 'out')
KS = ['16', '17', '18', '19', '20', '21', '22', '23', '24', '25']


def main():
    pca = json.load(open(os.path.join(OUT, 'pca_loadings.json'),
                         encoding='utf-8'))
    mu = np.array(pca['mu'])
    V = np.array(pca['components'])          # pooled axes (rows)
    lineages = pca['lineages']

    rep = ['POOLED vs PER-ELECTION PCA — congruence check', '=' * 58,
           '%-5s %28s %28s' % ('K', 'PC1 (Arab-Jewish)', 'PC2 (Haredi-secular)'),
           '%-5s %14s %13s %14s %13s' % ('', '|cos| load', 'r scores',
                                         '|cos| load', 'r scores')]
    for k in KS:
        rows, w = [], []
        with open(os.path.join(OUT, 'votes_k%s.csv' % k),
                  encoding='utf-8') as f:
            for r in csv.DictReader(f):
                rows.append([float(r[l]) for l in lineages])
                w.append(float(r['valid']))
        X = np.array(rows)
        wn = np.array(w) / np.sum(w)
        mu_k = wn @ X
        Xc = X - mu_k
        U, S, Vk = np.linalg.svd(Xc * np.sqrt(wn)[:, None],
                                 full_matrices=False)
        own_scores = Xc @ Vk[:4].T
        pooled_scores = (X - mu) @ V[:2].T
        line = '%-5s' % ('K' + k)
        for pc in (0, 1):
            cos = np.abs(Vk[:4] @ V[pc])
            j = int(np.argmax(cos))
            r = np.corrcoef(pooled_scores[:, pc], own_scores[:, j])[0, 1]
            line += '%10.3f (own PC%d)%10.3f   ' % (cos[j], j + 1, abs(r))
        rep.append(line)
    rep.append('')
    rep.append('reading: |cos| = loading-vector agreement (1 = identical '
               'axis); r = per-SA score agreement within the election. '
               '"own PCj" = which of the election\'s own axes matches.')
    with open(os.path.join(OUT, 'congruence_report.txt'), 'w',
              encoding='utf-8') as f:
        f.write('\n'.join(rep) + '\n')
    print('\n'.join(rep))


if __name__ == '__main__':
    main()
