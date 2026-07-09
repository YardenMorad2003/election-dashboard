# -*- coding: utf-8 -*-
"""ML map layer: pack the common-space scores + GMM segments into
data/electoral_space.json for statarea_map's new 'seg' / 'pc2' modes.

Per map-year, per "semel|sa": [pc1, pc2, segment, entropy]. Meta carries
{he,en} segment labels + colors + the pc2 display scale. Segment labels are
hardcoded to the k=9 pooled fit (segments.py, random_state=0) and GUARDED:
the builder recomputes each segment's mean lineage profile and refuses to
emit if the expected top lineage doesn't match (protects against silent
re-fit renumbering).

Run from repo root: python -X utf8 analysis/ml/build_space_layer.py
"""
import csv
import json
import os
from collections import defaultdict

import numpy as np

OUT = os.path.join('analysis', 'ml', 'out')
K2YEAR = {'16': '2003', '17': '2006', '18': '2009', '19': '2013',
          '20': '2015', '21': '2019a', '22': '2019b', '23': '2020',
          '24': '2021', '25': '2022'}

SEGMENTS = {  # id -> (expected top lineage, he, en, color)
    0: ('likud', 'ימין-מרכז ותיק', 'Legacy center-right', '#64748b'),
    1: ('arab', 'ערבי', 'Arab', '#22c55e'),
    2: ('likud', 'מעוז ליכוד', 'Likud stronghold', '#3b82f6'),
    3: ('utj', 'חרדי', 'Haredi', '#6d28d9'),
    4: ('labor', 'מעוז עבודה (נעלם)', 'Labor stronghold (vanished)', '#ef4444'),
    5: ('center', 'מרכז-שמאל', 'Center-left', '#f472b6'),
    6: ('likud', 'ימין מעורב/פריפריה', 'Mixed right/periphery', '#f59e0b'),
    7: ('arab', 'מעורב/דרוזי', 'Mixed & Druze', '#14b8a6'),
    8: ('center', 'מרכז מודרני', 'Modern center', '#22d3ee'),
}


def main():
    # guard: recompute mean lineage profile per segment across all elections
    prof = defaultdict(lambda: defaultdict(float))
    wsum = defaultdict(float)
    lineages = None
    seg_rows = {}
    for k, yr in K2YEAR.items():
        segs = {}
        with open(os.path.join(OUT, 'segments_k%s.csv' % k),
                  encoding='utf-8') as f:
            for r in csv.DictReader(f):
                segs['%s|%s' % (r['semel'], r['sa'])] = (
                    int(r['segment']), float(r['entropy']))
        seg_rows[k] = segs
        with open(os.path.join(OUT, 'votes_k%s.csv' % k),
                  encoding='utf-8') as f:
            rd = csv.DictReader(f)
            if lineages is None:
                lineages = [c for c in rd.fieldnames
                            if c not in ('semel', 'sa', 'valid', 'turnout')]
            for r in rd:
                key = '%s|%s' % (r['semel'], r['sa'])
                s = segs[key][0]
                v = float(r['valid'])
                wsum[s] += v
                for l in lineages:
                    prof[s][l] += v * float(r[l])
    for sid, (top, he, en, col) in SEGMENTS.items():
        mean_prof = {l: prof[sid][l] / wsum[sid] for l in lineages}
        got = max(mean_prof, key=mean_prof.get)
        if got != top:
            raise SystemExit('segment %d: expected top lineage %r, got %r '
                             '(%.0f%%) — re-fit renumbered the segments; '
                             'update SEGMENTS' % (sid, top, got,
                                                  mean_prof[got]))

    out = {'meta': {
        'built': '2026-07-09',
        'what': ('common electoral space (weighted PCA over all 10 elections'
                 ' x SA lineage shares) + pooled k=9 GMM segments;'
                 ' entries [pc1, pc2, segment, entropy]'),
        'segments': {str(i): {'he': he, 'en': en, 'color': col}
                     for i, (_, he, en, col) in SEGMENTS.items()},
        'axes': {'pc1': {'he': 'ציר ערבי-יהודי', 'en': 'Arab-Jewish axis'},
                 'pc2': {'he': 'ציר חרדי-חילוני',
                         'en': 'Haredi-secular axis'}},
    }}
    all_pc2 = []
    for k, yr in K2YEAR.items():
        scores = {}
        with open(os.path.join(OUT, 'pca_scores_k%s.csv' % k),
                  encoding='utf-8') as f:
            for r in csv.DictReader(f):
                scores['%s|%s' % (r['semel'], r['sa'])] = (
                    float(r['pc1']), float(r['pc2']))
        m = {}
        for key, (seg, ent) in seg_rows[k].items():
            pc1, pc2 = scores[key]
            m[key] = [round(pc1, 1), round(pc2, 1), seg, round(ent, 2)]
            all_pc2.append(pc2)
        out[yr] = m
    lo, hi = np.percentile(all_pc2, 2), np.percentile(all_pc2, 98)
    out['meta']['pc2_scale'] = [round(float(lo)), round(float(hi))]

    path = os.path.join('data', 'electoral_space.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print('wrote %s (%.0f KB), pc2 scale [%d, %d]'
          % (path, os.path.getsize(path) / 1024, lo, hi))


if __name__ == '__main__':
    main()
