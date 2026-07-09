# -*- coding: utf-8 -*-
"""Build data/ses_statarea.json — the runtime SES layer for statarea_map's
modern years (2022 geometry, K21-K25).

For every 2022-geo (semel, sa) and each vintage, pick the finest available
SES-2019/2021 source:
  'sa'  crosswalked SA-level value (build_ses_crosswalk, m='geo')
  'q'   quarter-mean fill (m='q' — mainly East Jerusalem)
  'loc' authority-level value (T01) for cities/local councils w/o SA tables
  'vil' village-level value (T08) for localities inside regional councils
The loc/vil tier exists only in the 2019 publication and is reused for the
2021 map (flagged identically; vintage noted in meta).

Inputs : analysis/statarea_inputs/ses_statarea_2022keys.json
         analysis/statarea_inputs/ses_locality_2019.json
         data/statarea_2022_geo.json
Output : data/ses_statarea.json   {vintage: {"semel|sa": [value, cluster, src]}}

Run from repo root: python -X utf8 analysis/build_ses_layer.py
"""
import json
import os
from collections import Counter

IN_DIR = os.path.join('analysis', 'statarea_inputs')
VINTAGES = ('2019', '2021')


def main():
    with open(os.path.join(IN_DIR, 'ses_statarea_2022keys.json'),
              encoding='utf-8') as f:
        cw = json.load(f)
    with open(os.path.join(IN_DIR, 'ses_locality_2019.json'),
              encoding='utf-8') as f:
        loc = json.load(f)
    with open(os.path.join('data', 'statarea_2022_geo.json'),
              encoding='utf-8') as f:
        geo = json.load(f)

    auth = {a['semel']: a for a in loc['authorities']
            if a['status'] != 'regional_council' and a['value'] is not None}
    vil = {v['semel']: v for v in loc['villages'] if v['value'] is not None}

    keys = [(f['properties']['semel'], f['properties']['sa'])
            for f in geo['features']]
    out = {'meta': {
        'built': '2026-07-09',
        'source': ('CBS socio-economic index: SA-level 2019/2021 (crosswalked'
                   ' to 2022-census SA boundaries), locality-level 2019'
                   ' (authorities T01 + villages-in-regional-councils T08)'),
        'src_codes': {'sa': 'SA-level, crosswalked to 2022 boundaries',
                      'q': 'quarter mean (no per-SA figure; mainly E. J-m)',
                      'loc': 'authority-level 2019 publication',
                      'vil': 'village-level 2019 publication'},
        'note': ('loc/vil values are the 2019 vintage on both maps — no'
                 ' locality-level 2021 snapshot exists'),
    }}
    for v in VINTAGES:
        m = {}
        tiers = Counter()
        # cities with SA-level coverage never take the authority-wide value:
        # their few unassigned SAs are zero-pop industrial/park areas where a
        # city mean is false precision — leave them no-data
        covered = {int(k.split('|')[0]) for k in cw[v]}
        for semel, sa in keys:
            k = '%d|%d' % (semel, sa)
            e = cw[v].get(k)
            if e is not None:
                src = 'sa' if e['m'] == 'geo' else 'q'
                m[k] = [round(e['v'], 2), e['c'], src]
            elif semel in covered:
                tiers['none'] += 1
                continue
            elif semel in auth:
                a = auth[semel]
                m[k] = [round(a['value'], 2), a['cluster'], 'loc']
            elif semel in vil:
                w = vil[semel]
                m[k] = [round(w['value'], 2), w['cluster'], 'vil']
            else:
                tiers['none'] += 1
                continue
            tiers[m[k][2]] += 1
        out[v] = m
        print('%s: %d/%d SAs assigned  %s'
              % (v, len(m), len(keys), dict(tiers)))

    path = os.path.join('data', 'ses_statarea.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print('wrote %s (%.1f KB)' % (path, os.path.getsize(path) / 1024))


if __name__ == '__main__':
    main()
