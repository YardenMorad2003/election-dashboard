# -*- coding: utf-8 -*-
"""ML project 1: the common electoral space (weighted PCA over the tensor).

Pools all 10 elections' SA x lineage share rows (K16-K25, ~24k rows), centers
with valid-vote weights, and takes the SVD -> one fixed low-dimensional space
every election projects into. Reports axis loadings + per-election national
drift + example neighborhood trajectories via the cross-era ancestor links.

Notes for the write-up:
- rows are weighted by valid votes, so the space reflects voters, not areas;
- shares are compositional (sum ~100) -> one direction is degenerate by
  construction; we report PCs of the centered simplex as-is (v1; CLR later);
- lineage buckets that exist in few elections (baaliyah K16 only within this
  window, opp_right K24 only) contribute era-specific variance — documented.

Run from repo root: python -X utf8 analysis/ml/pca_space.py
Outputs: analysis/ml/out/pca_{loadings.json,report.txt,scores_k*.csv}
"""
import csv
import json
import os

import numpy as np

OUT = os.path.join('analysis', 'ml', 'out')
KS = ['16', '17', '18', '19', '20', '21', '22', '23', '24', '25']
GEO_ERA = {'16': '1995', '17': '1995', '18': '2009', '19': '2009',
           '20': '2009', '21': '2022', '22': '2022', '23': '2022',
           '24': '2022', '25': '2022'}
NPC = 4


def load_votes(k):
    rows = []
    with open(os.path.join(OUT, 'votes_k%s.csv' % k), encoding='utf-8') as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def main():
    lineages = None
    all_rows = []           # (k, semel|sa, weight, share vector)
    for k in KS:
        for r in load_votes(k):
            if lineages is None:
                lineages = [c for c in r if c not in
                            ('semel', 'sa', 'valid', 'turnout')]
            v = float(r['valid'])
            x = np.array([float(r[l]) for l in lineages])
            all_rows.append((k, '%s|%s' % (r['semel'], r['sa']), v, x))

    X = np.vstack([x for _, _, _, x in all_rows])
    w = np.array([v for _, _, v, _ in all_rows])
    wn = w / w.sum()
    mu = wn @ X
    Xc = X - mu
    U, S, Vt = np.linalg.svd(Xc * np.sqrt(wn)[:, None], full_matrices=False)
    evr = S**2 / (S**2).sum()
    # sign convention: PC1 positive toward the Arab pole? flip so that
    # 'likud' loads NEGATIVE on PC1 and 'arab' positive if needed -> instead
    # fix each PC's sign by its largest-|loading| lineage being positive
    for i in range(NPC):
        j = np.argmax(np.abs(Vt[i]))
        if Vt[i, j] < 0:
            Vt[i] = -Vt[i]
    scores = Xc @ Vt[:NPC].T

    rep = ['COMMON ELECTORAL SPACE — weighted PCA over %d SA-election rows'
           % len(all_rows), '=' * 66]
    rep.append('explained variance: ' + '  '.join(
        'PC%d %.1f%%' % (i + 1, 100 * evr[i]) for i in range(6)))
    rep.append('\nloadings (share-points per unit score):')
    hdr = '%-11s' % '' + ''.join('%8s' % ('PC%d' % (i + 1))
                                 for i in range(NPC))
    rep.append(hdr)
    for li, l in enumerate(lineages):
        rep.append('%-11s' % l + ''.join('%8.2f' % Vt[i, li]
                                         for i in range(NPC)))

    # per-election national position (weighted mean score)
    rep.append('\nnational drift through the space (weighted mean score):')
    rep.append('%-5s' % 'K' + ''.join('%8s' % ('PC%d' % (i + 1))
                                      for i in range(NPC)))
    idx = 0
    slices = {}
    for k in KS:
        n = sum(1 for kk, _, _, _ in all_rows if kk == k)
        slices[k] = (idx, idx + n)
        idx += n
    for k in KS:
        a, b = slices[k]
        wk = w[a:b] / w[a:b].sum()
        m = wk @ scores[a:b]
        rep.append('%-5s' % ('K' + k) + ''.join('%8.2f' % m[i]
                                                for i in range(NPC)))

    # example trajectories (2022-keyed, ancestors via links for K18-20)
    links09 = json.load(open(os.path.join(OUT, 'links_2009_to_2022.json'),
                             encoding='utf-8'))
    geo = json.load(open('data/statarea_2022_geo.json', encoding='utf-8'))
    name_of = {'%d|%d' % (f['properties']['semel'], f['properties']['sa']):
               f['properties']['name'] for f in geo['features']}
    by_key = {}
    for i, (k, key, v, x) in enumerate(all_rows):
        by_key[(k, key)] = i
    # archetype examples: per lineage, the highest-K25-share SA that has a
    # full K18-K25 chain (2009 ancestor exists in the K18 rows)
    k18_keys = {key for (k, key) in by_key if k == '18'}
    examples = []
    a25, b25 = slices['25']
    for l in ('utj', 'arab', 'likud', 'center', 'natrel', 'labor', 'shas',
              'beiteinu'):
        li = lineages.index(l)
        best, bs = None, -1
        for i in range(a25, b25):
            key = all_rows[i][1]
            if X[i, li] > bs and links09.get(key, [None])[0] in k18_keys:
                bs, best = X[i, li], key
        if best:
            examples.append(best)
    rep.append('\narchetype trajectories (PC1/PC2 per election; . = no data):')
    for key in examples:
        parts = []
        anc = links09.get(key, [None])[0]
        for k in KS:
            kk = key if GEO_ERA[k] == '2022' else anc
            i = by_key.get((k, kk)) if kk else None
            parts.append('.' if i is None else
                         '%.0f/%.0f' % (scores[i, 0], scores[i, 1]))
        rep.append('%-22s %s' % ((name_of.get(key, '?') + ' ' + key)[:22],
                                 '  '.join('%9s' % p for p in parts)))

    with open(os.path.join(OUT, 'pca_report.txt'), 'w',
              encoding='utf-8') as f:
        f.write('\n'.join(rep) + '\n')
    json.dump({'lineages': lineages, 'mu': mu.round(4).tolist(),
               'explained_variance_ratio': evr[:8].round(4).tolist(),
               'components': Vt[:NPC].round(4).tolist()},
              open(os.path.join(OUT, 'pca_loadings.json'), 'w',
                   encoding='utf-8'), ensure_ascii=False, indent=1)
    for k in KS:
        a, b = slices[k]
        with open(os.path.join(OUT, 'pca_scores_k%s.csv' % k), 'w',
                  newline='', encoding='utf-8') as f:
            wcsv = csv.writer(f)
            wcsv.writerow(['semel', 'sa'] +
                          ['pc%d' % (i + 1) for i in range(NPC)])
            for i in range(a, b):
                key = all_rows[i][1].split('|')
                wcsv.writerow(key + [round(float(scores[i, j]), 3)
                                     for j in range(NPC)])
    print('\n'.join(rep))


if __name__ == '__main__':
    main()
