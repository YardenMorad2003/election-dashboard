# -*- coding: utf-8 -*-
"""ML project 3: electoral segments (GMM in the common space) + transitions.

One GaussianMixture fit on the POOLED SA-election rows' common-space scores
(PC1-4), so a segment means the same thing in every election; k chosen by BIC
scan tempered by interpretability. Each SA-election then carries a hard
segment + soft-membership entropy (mixedness). Cross-era transition matrices
run on the balanced P08 panel via ancestor links (valid-vote weighted).

GMM is fit unweighted (sklearn GMs take no sample weights): each SA counts
once — segments describe kinds of PLACES; the transition matrices are
vote-weighted. Segments are named from their mean lineage profile.

Run from repo root: python -X utf8 analysis/ml/segments.py   (~1 min)
Outputs: analysis/ml/out/segments_{report.txt,k*.csv}
"""
import csv
import json
import os
from collections import defaultdict

import numpy as np
from sklearn.mixture import GaussianMixture

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


def main():
    pca = json.load(open(os.path.join(OUT, 'pca_loadings.json'),
                         encoding='utf-8'))
    mu = np.array(pca['mu'])
    V = np.array(pca['components'])
    votes = {}
    for k in KS:
        votes[k], lineages = load_votes(k)

    rows, meta = [], []
    for k in KS:
        for key, (v, x) in votes[k].items():
            rows.append((x - mu) @ V.T)
            meta.append((k, key, v))
    S = np.vstack(rows)

    # BIC scan
    bics = {}
    for kk in range(4, 11):
        gm = GaussianMixture(kk, covariance_type='full', random_state=0,
                             n_init=3).fit(S)
        bics[kk] = gm.bic(S)
    ksel = min(bics, key=bics.get)
    # prefer parsimony: smallest k within 1% of best BIC
    best = bics[ksel]
    for kk in sorted(bics):
        if bics[kk] <= best + 0.01 * abs(best):
            ksel = kk
            break
    gm = GaussianMixture(ksel, covariance_type='full', random_state=0,
                         n_init=5).fit(S)
    proba = gm.predict_proba(S)
    hard = proba.argmax(1)
    ent = -(proba * np.log(np.maximum(proba, 1e-12))).sum(1) / np.log(ksel)

    # name segments from mean lineage profile
    prof = gm.means_ @ V + mu          # k x L, share space
    names = []
    for c in range(ksel):
        top = np.argsort(-prof[c])[:2]
        names.append('+'.join('%s%.0f' % (lineages[t], prof[c, t])
                              for t in top if prof[c, t] > 8))
    rep = ['ELECTORAL SEGMENTS — pooled GMM in the common space', '=' * 60,
           'BIC scan: ' + '  '.join('k=%d %.0f' % (k, b)
                                    for k, b in sorted(bics.items())),
           'selected k=%d (parsimony rule: within 1%% of best)' % ksel, '']
    rep.append('segment profiles (mean lineage shares, top lineages):')
    for c in range(ksel):
        srt = np.argsort(-prof[c])[:4]
        rep.append('  S%d [%s]: %s' % (c, names[c], ', '.join(
            '%s %.0f%%' % (lineages[t], prof[c, t]) for t in srt)))
    # sizes + entropy per election
    rep.append('\nsegment shares of the vote per election (%):')
    rep.append('%-4s' % 'K' + ''.join('%7s' % ('S%d' % c)
                                      for c in range(ksel)) + '%8s' % 'entr')
    idx_by_k = defaultdict(list)
    for i, (k, key, v) in enumerate(meta):
        idx_by_k[k].append(i)
    for k in KS:
        js = idx_by_k[k]
        w = np.array([meta[i][2] for i in js])
        h = np.array([hard[i] for i in js])
        e = np.array([ent[i] for i in js])
        shares = [100 * w[h == c].sum() / w.sum() for c in range(ksel)]
        rep.append('%-4s' % ('K' + k) + ''.join('%7.1f' % s for s in shares) +
                   '%8.3f' % float(np.average(e, weights=w)))

    # transitions on P08 balanced panel
    l09 = json.load(open(os.path.join(OUT, 'links_2009_to_2022.json'),
                         encoding='utf-8'))
    seg_of = {(meta[i][0], meta[i][1]): hard[i] for i in range(len(meta))}
    w25 = {key: v for key, (v, _) in votes['25'].items()}

    def seg(key, k):
        kk = key if ERA[k] == '2022' else l09.get(key, [None])[0]
        return seg_of.get((k, kk)) if kk else None

    panel = [key for key in votes['25']
             if all(seg(key, k) is not None for k in KS[2:])]
    M = np.zeros((ksel, ksel))
    for key in panel:
        a, b = seg(key, '18'), seg(key, '25')
        M[a, b] += w25[key]
    rep.append('\nK18 -> K25 segment transition matrix '
               '(%d SAs, rows=K18, K25-vote-weighted, row %%):' % len(panel))
    rep.append('%-14s' % '' + ''.join('%7s' % ('S%d' % c)
                                      for c in range(ksel)))
    stay = 0.0
    tot = M.sum()
    for a in range(ksel):
        rs = M[a].sum()
        stay += M[a, a]
        rep.append('%-14s' % ('S%d %s' % (a, names[a][:10])) + ''.join(
            '%7.1f' % (100 * M[a, b] / rs if rs else 0)
            for b in range(ksel)))
    rep.append('overall diagonal share: %.1f%%' % (100 * stay / tot))
    off = [(a, b, M[a, b]) for a in range(ksel) for b in range(ksel)
           if a != b]
    off.sort(key=lambda t: -t[2])
    rep.append('biggest moves: ' + '; '.join(
        'S%d->S%d %.1f%%' % (a, b, 100 * v / tot) for a, b, v in off[:5]))

    # per-election segment CSVs (future map layer)
    for k in KS:
        with open(os.path.join(OUT, 'segments_k%s.csv' % k), 'w',
                  newline='', encoding='utf-8') as f:
            wcsv = csv.writer(f)
            wcsv.writerow(['semel', 'sa', 'segment', 'entropy'])
            for i in idx_by_k[k]:
                semel, sa = meta[i][1].split('|')
                wcsv.writerow([semel, sa, int(hard[i]), round(float(ent[i]), 3)])

    with open(os.path.join(OUT, 'segments_report.txt'), 'w',
              encoding='utf-8') as f:
        f.write('\n'.join(rep) + '\n')
    print('\n'.join(rep))


if __name__ == '__main__':
    main()
