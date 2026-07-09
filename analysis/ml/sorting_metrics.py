# -*- coding: utf-8 -*-
"""ML project 1b: sorting/polarization metrics in the common electoral space
+ CLR robustness check for the PCA.

Everything runs on BALANCED PANELS so cross-era comparisons are apples to
apples (era coverage differs; an unbalanced series would confound sorting
with mapping coverage):
  P08: 2022-geo SAs whose 2009 ancestor has K18/19/20 rows and which have
       all of K21-25 (headline series, 8 elections)
  P95: additionally chained to a 1995 ancestor with K16/17 (10 elections,
       smaller + lower placement quality - secondary evidence only)

Metrics per election, valid-weighted, on common-space PC scores:
  - dispersion: weighted std + p90-p10 per PC (between-neighborhood spread)
  - nationalization: between-locality share of total variance (and its
    complement = WITHIN-city neighborhood sorting)
  - trajectories: per-SA path length and net displacement (PC1-4)
CLR check: PCA re-run on centered-log-ratio shares; loading congruence +
score correlations vs the raw-share space.

Run from repo root: python -X utf8 analysis/ml/sorting_metrics.py
Outputs: analysis/ml/out/sorting_{report.txt,series.csv}
"""
import csv
import json
import os
from collections import defaultdict

import numpy as np

OUT = os.path.join('analysis', 'ml', 'out')
KS = ['16', '17', '18', '19', '20', '21', '22', '23', '24', '25']
ERA = {'16': '1995', '17': '1995', '18': '2009', '19': '2009', '20': '2009',
       '21': '2022', '22': '2022', '23': '2022', '24': '2022', '25': '2022'}
NPC = 4


def load_votes(k):
    out = {}
    with open(os.path.join(OUT, 'votes_k%s.csv' % k), encoding='utf-8') as f:
        rd = csv.DictReader(f)
        lineages = [c for c in rd.fieldnames
                    if c not in ('semel', 'sa', 'valid', 'turnout')]
        for r in rd:
            out['%s|%s' % (r['semel'], r['sa'])] = (
                float(r['valid']), np.array([float(r[l]) for l in lineages]))
    return out, lineages


def wstd(x, w):
    m = np.average(x, weights=w)
    return float(np.sqrt(np.average((x - m) ** 2, weights=w)))


def wq(x, w, q):
    i = np.argsort(x)
    cw = np.cumsum(w[i])
    return float(x[i][np.searchsorted(cw, q * cw[-1])])


def main():
    votes = {}
    for k in KS:
        votes[k], lineages = load_votes(k)
    pca = json.load(open(os.path.join(OUT, 'pca_loadings.json'),
                         encoding='utf-8'))
    assert pca['lineages'] == lineages
    mu = np.array(pca['mu'])
    V = np.array(pca['components'])          # NPC x L

    l09 = json.load(open(os.path.join(OUT, 'links_2009_to_2022.json'),
                         encoding='utf-8'))
    l95 = json.load(open(os.path.join(OUT, 'links_1995_to_2022.json'),
                         encoding='utf-8'))

    # ---- balanced panels (keys are 2022 SAs) ----
    def chain_ok(key, ks):
        for k in ks:
            kk = key if ERA[k] == '2022' else (
                l09.get(key, [None])[0] if ERA[k] == '2009'
                else l95.get(key, [None])[0])
            if kk is None or kk not in votes[k]:
                return False
        return True

    P08 = [key for key in votes['25'] if chain_ok(key, KS[2:])]
    P95 = [key for key in P08 if chain_ok(key, KS[:2])]
    rep = ['SORTING METRICS — common electoral space', '=' * 60,
           'balanced panels: P08 %d SAs (K18-25), P95 %d SAs (K16-25)'
           % (len(P08), len(P95)), '']

    def unit_row(key, k):
        kk = key if ERA[k] == '2022' else (
            l09[key][0] if ERA[k] == '2009' else l95[key][0])
        v, x = votes[k][kk]
        return v, (x - mu) @ V.T          # score vector, NPC

    series = []
    for panel, name, ks in ((P08, 'P08', KS[2:]), (P95, 'P95', KS)):
        rep.append('--- panel %s ---' % name)
        rep.append('%-4s' % 'K' +
                   ''.join('%8s' % ('sd%d' % (i + 1)) for i in range(NPC)) +
                   ''.join('%8s' % ('gap%d' % (i + 1)) for i in range(2)) +
                   '%9s%9s' % ('betw%', 'with_sd'))
        semel_of = {key: key.split('|')[0] for key in panel}
        for k in ks:
            rows = [unit_row(key, k) for key in panel]
            w = np.array([r[0] for r in rows])
            S = np.vstack([r[1] for r in rows])
            sds = [wstd(S[:, i], w) for i in range(NPC)]
            gaps = [wq(S[:, i], w, .9) - wq(S[:, i], w, .1) for i in range(2)]
            # between-locality variance share on PC1+PC2 (2D) —
            # weighted decomposition
            grp = defaultdict(list)
            for j, key in enumerate(panel):
                grp[semel_of[key]].append(j)
            tot_m = np.average(S[:, :2], weights=w, axis=0)
            tot_var = float(np.average(
                ((S[:, :2] - tot_m) ** 2).sum(1), weights=w))
            betw = 0.0
            wsum = w.sum()
            for g, js in grp.items():
                wg = w[js]
                mg = np.average(S[js, :2], weights=wg, axis=0)
                betw += wg.sum() / wsum * float(((mg - tot_m) ** 2).sum())
            within_sd = np.sqrt(max(tot_var - betw, 0))
            series.append({'panel': name, 'k': k,
                           **{'sd%d' % (i + 1): round(sds[i], 2)
                              for i in range(NPC)},
                           'gap1': round(gaps[0], 1), 'gap2': round(gaps[1], 1),
                           'between_share': round(betw / tot_var, 4),
                           'within_sd': round(float(within_sd), 2)})
            rep.append('%-4s' % ('K' + k) +
                       ''.join('%8.2f' % s for s in sds) +
                       ''.join('%8.1f' % g for g in gaps) +
                       '%9.1f%9.2f' % (100 * betw / tot_var, within_sd))
        rep.append('')

    # ---- trajectories on P08 ----
    geo = json.load(open('data/statarea_2022_geo.json', encoding='utf-8'))
    name_of = {'%d|%d' % (f['properties']['semel'], f['properties']['sa']):
               f['properties']['name'] for f in geo['features']}
    traj = []
    for key in P08:
        pts = np.vstack([unit_row(key, k)[1] for k in KS[2:]])
        steps = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        net = float(np.linalg.norm(pts[-1] - pts[0]))
        traj.append((key, float(steps.sum()), net))
    path = np.array([t[1] for t in traj])
    net = np.array([t[2] for t in traj])
    rep.append('--- trajectories K18->K25 (P08, PC1-4 space) ---')
    rep.append('path length: median %.1f  p90 %.1f;  net displacement: '
               'median %.1f  p90 %.1f;  directedness(net/path) median %.2f'
               % (np.median(path), np.percentile(path, 90), np.median(net),
                  np.percentile(net, 90),
                  float(np.median(net / np.maximum(path, 1e-9)))))
    byv = sorted(traj, key=lambda t: -t[2])
    rep.append('biggest net movers:')
    for key, p, n in byv[:8]:
        rep.append('  %-24s path %5.1f  net %5.1f'
                   % ((name_of.get(key, '?') + ' ' + key)[:24], p, n))
    rep.append('most frozen (of big SAs, path):')
    big = [t for t in traj if votes['25'][t[0]][0] > 3000]
    for key, p, n in sorted(big, key=lambda t: t[1])[:8]:
        rep.append('  %-24s path %5.1f  net %5.1f'
                   % ((name_of.get(key, '?') + ' ' + key)[:24], p, n))

    # ---- CLR robustness ----
    rows_x, rows_w = [], []
    for k in KS:
        for v, x in votes[k].values():
            rows_x.append(x)
            rows_w.append(v)
    X = np.vstack(rows_x)
    w = np.array(rows_w)
    wn = w / w.sum()
    L = np.log(X + 0.5)
    C = L - L.mean(1, keepdims=True)
    muc = wn @ C
    Uc, Sc, Vtc = np.linalg.svd((C - muc) * np.sqrt(wn)[:, None],
                                full_matrices=False)
    evrc = Sc**2 / (Sc**2).sum()
    raw_scores = (X - mu) @ V.T
    clr_scores = (C - muc) @ Vtc[:NPC].T
    rep.append('\n--- CLR robustness check ---')
    rep.append('CLR explained variance: ' + '  '.join(
        'PC%d %.1f%%' % (i + 1, 100 * evrc[i]) for i in range(4)))
    for i in range(NPC):
        cors = [abs(np.corrcoef(raw_scores[:, i], clr_scores[:, j])[0, 1])
                for j in range(NPC)]
        rep.append('raw PC%d best matches CLR PC%d (|r|=%.3f)'
                   % (i + 1, int(np.argmax(cors)) + 1, max(cors)))

    with open(os.path.join(OUT, 'sorting_report.txt'), 'w',
              encoding='utf-8') as f:
        f.write('\n'.join(rep) + '\n')
    with open(os.path.join(OUT, 'sorting_series.csv'), 'w', newline='',
              encoding='utf-8') as f:
        wr = csv.DictWriter(f, list(series[0].keys()))
        wr.writeheader()
        wr.writerows(series)
    print('\n'.join(rep))


if __name__ == '__main__':
    main()
