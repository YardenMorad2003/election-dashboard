# -*- coding: utf-8 -*-
"""Crosswalk CBS SES index values (2017/2019/2021, on the pre-2022 SA
delineation) onto the 2022-census SA keys used by statarea_map.

Method: areal interpolation. Old-SA polygons come from statarea_2009_geo.json
(96.3% code match with the SES tables); for every 2022-geo SA in a covered
municipality, each intersecting same-semel old SA contributes weight =
overlap_area x (old_pop / old_area), i.e. population spread uniformly over the
old SA. New value = weighted mean; cluster = dominant contributor's cluster.
A direct (semel,sa) code join would be WRONG: 25% of code-matched pairs have
IoU < 0.5 after the 2022 renumbering (several ~0, e.g. Jerusalem 921/923).

Inputs : analysis/statarea_inputs/ses_statarea_{2017,2019,2021}.json
         data/statarea_2009_geo.json, data/statarea_2022_geo.json
         analysis/statarea_inputs/cbs_census_2022_statarea.csv (pop, for QA)
Outputs: analysis/statarea_inputs/ses_statarea_2022keys.json
         analysis/statarea_inputs/ses_crosswalk_report.txt

Run from repo root: python -X utf8 analysis/build_ses_crosswalk.py
"""
import json
import math
import os
from collections import defaultdict

import pandas as pd
from shapely.geometry import shape
from shapely.ops import transform
from shapely.strtree import STRtree

IN_DIR = os.path.join('analysis', 'statarea_inputs')
VINTAGES = (2017, 2019, 2021)
# below this share of SES-bearing overlap the geometric assignment is refused
# (a 1-3% boundary sliver once painted East-Jerusalem SAs with West-Jerusalem
# cluster-6/7 values — better a hole / quarter fallback than a wrong value)
MIN_COV = 0.25
# equirectangular metres at ~lat 31.8 (ratios are what matter, but metric
# areas keep the coverage numbers interpretable)
KX = 111320 * math.cos(math.radians(31.8))
KY = 111320


def proj(g):
    return transform(lambda x, y, z=None: (x * KX, y * KY), g)


def load_geo(path):
    with open(path, encoding='utf-8') as f:
        gj = json.load(f)
    out = {}
    for feat in gj['features']:
        p = feat['properties']
        g = proj(shape(feat['geometry']))
        if not g.is_valid:
            g = g.buffer(0)
        out[(p['semel'], p['sa'])] = g
    return out


def main():
    geo_old = load_geo(os.path.join('data', 'statarea_2009_geo.json'))
    geo_new = load_geo(os.path.join('data', 'statarea_2022_geo.json'))

    ses = {}
    for v in VINTAGES:
        with open(os.path.join(IN_DIR, 'ses_statarea_%d.json' % v),
                  encoding='utf-8') as f:
            ses[v] = json.load(f)

    # census pop on 2022 keys, for QA weighting
    cen = pd.read_csv(os.path.join(IN_DIR, 'cbs_census_2022_statarea.csv'))
    cen = cen[cen['StatArea'].notna() & cen['LocalityCode'].notna()]
    pop22 = {(int(r.LocalityCode), int(r.StatArea)): r.pop_approx
             for r in cen.itertuples() if r.pop_approx == r.pop_approx}

    rep = []
    out = {'meta': {
        'built': '2026-07-09',
        'method': ('areal interpolation old-SA (statarea_2009_geo) -> 2022 SA;'
                    ' weight = overlap_area * old_pop/old_area; value ='
                    ' weighted mean; cluster = dominant contributor;'
                    ' dom = dominant weight share; cov = share of new-SA area'
                    ' covered by SES-bearing old SAs. m="geo". Sliver filter:'
                    ' overlaps under 5pct of the new SA AND under 15pct of the'
                    ' old SA are dropped when substantial contributors exist.'
                    ' m="q" = quarter fallback (cov<' + str(MIN_COV) +
                    ' or no overlap): pop-weighted mean of SES SAs sharing the'
                    ' zfill(4)[:2] quarter prefix — used mainly for East'
                    ' Jerusalem, which is absent from the old geometry layer.'),
        'source': 'CBS SES index T12 snapshots (ses_statarea_*.json)',
        'warning': ('code-equal (semel,sa) join across delineations is unsafe;'
                    ' always use this file for 2022-key lookups'),
    }}

    for v in VINTAGES:
        areas = ses[v]['areas']
        by_semel = defaultdict(list)
        no_geom, no_geom_pop, tot_pop = [], 0.0, 0.0
        for a in areas:
            key = (a['semel'], a['sa'])
            tot_pop += a['pop'] or 0
            if a['value'] is None:
                continue
            if key not in geo_old:
                no_geom.append(key)
                no_geom_pop += a['pop'] or 0
                continue
            g = geo_old[key]
            dens = (a['pop'] or 0) / g.area if g.area else 0
            by_semel[a['semel']].append((key, g, dens, a))

        rep.append('=== vintage %d ===' % v)
        rep.append('SES SAs: %d; with geometry+value: %d; missing geometry: %d'
                   ' (%.1f%% of SES pop)'
                   % (len(areas), sum(len(x) for x in by_semel.values()),
                      len(no_geom), 100 * no_geom_pop / tot_pop))
        miss_by_city = defaultdict(int)
        for k in no_geom:
            miss_by_city[k[0]] += 1
        top_miss = sorted(miss_by_city.items(), key=lambda kv: -kv[1])[:6]
        rep.append('  missing-geometry by semel: %s' % top_miss)

        # spatial index per semel
        trees = {s: STRtree([g for _, g, _, _ in lst])
                 for s, lst in by_semel.items()}

        result = {}
        code_match_delta = []   # |crosswalked - original| where same code, IoU>=0.9
        naive_wrong = 0         # same code exists but crosswalk differs >0.25
        n_out = 0
        fallback_todo = []
        for (semel, sa), gnew in geo_new.items():
            lst = by_semel.get(semel)
            if lst is None:
                continue
            idx = trees[semel].query(gnew)
            contrib = []
            for i in idx:
                key, gold, dens, a = lst[i]
                inter = gnew.intersection(gold).area
                if inter <= 0:
                    continue
                contrib.append((inter * max(dens, 1e-12), inter, key, a,
                                gold.area))
            # sliver filter: digitization noise between the two vintage layers
            # (tiny share of BOTH polygons) must not out-weigh true overlaps
            substantial = [c for c in contrib
                           if c[1] >= 0.05 * gnew.area or c[1] >= 0.15 * c[4]]
            if substantial:
                contrib = substantial
            wsum = sum(c[0] for c in contrib)
            cov = (sum(c[1] for c in contrib) / gnew.area
                   if contrib and gnew.area else 0)
            if not contrib or wsum <= 0 or cov < MIN_COV:
                fallback_todo.append((semel, sa))
                continue
            val = sum(c[0] * c[3]['value'] for c in contrib) / wsum
            dom = max(contrib, key=lambda c: c[0])
            result['%d|%d' % (semel, sa)] = {
                'v': round(val, 4),
                'c': dom[3]['cluster'],
                'dom': round(dom[0] / wsum, 3),
                'cov': round(min(cov, 1.0), 3),
                'n': len(contrib),
                'm': 'geo',
            }
            n_out += 1
            # QA: compare with a naive same-code join
            same = next((c[3] for c in contrib if c[2] == (semel, sa)), None)
            if same is not None:
                gold = geo_old[(semel, sa)]
                iou = (gnew.intersection(gold).area /
                       gnew.union(gold).area)
                if iou >= 0.9:
                    code_match_delta.append(abs(val - same['value']))
                if abs(val - same['value']) > 0.25:
                    naive_wrong += 1

        # quarter fallback: CBS SA codes carry the quarter in zfill(4)[:2];
        # East Jerusalem (quarters 21-29) is entirely absent from the old
        # geometry layer, yet its SES rows exist — fill each refused/uncovered
        # 2022 SA with its quarter's pop-weighted mean, flagged m='q'
        quarters = defaultdict(list)
        for a in areas:
            if a['value'] is None:
                continue
            quarters[(a['semel'], str(a['sa']).zfill(4)[:2])].append(a)
        n_fb, fb_pop, fb_jlm = 0, 0.0, 0
        for semel, sa in fallback_todo:
            q = quarters.get((semel, str(sa).zfill(4)[:2]))
            if not q:
                continue
            psum = sum(x['pop'] or 0 for x in q)
            if psum <= 0:
                continue
            val = sum((x['pop'] or 0) * x['value'] for x in q) / psum
            domq = max(q, key=lambda x: x['pop'] or 0)
            result['%d|%d' % (semel, sa)] = {
                'v': round(val, 4), 'c': domq['cluster'],
                'dom': None, 'cov': None, 'n': len(q), 'm': 'q'}
            n_fb += 1
            fb_pop += pop22.get((semel, sa), 0)
            if semel == 3000:
                fb_jlm += 1
        n_out += n_fb
        rep.append('quarter fallback: %d SAs filled (census pop %s), of'
                   ' them %d in Jerusalem; %d refused SAs had no quarter data'
                   % (n_fb, '{:,.0f}'.format(fb_pop), fb_jlm,
                      len(fallback_todo) - n_fb))

        out[str(v)] = result

        # coverage of 2022 SAs in covered municipalities
        semels = set(by_semel)
        new_in_scope = [k for k in geo_new if k[0] in semels]
        got = sum(1 for k in new_in_scope if '%d|%d' % k in result)
        pop_all = sum(pop22.get(k, 0) for k in new_in_scope)
        pop_got = sum(pop22.get(k, 0) for k in new_in_scope
                      if '%d|%d' % k in result)
        n_geo = sum(1 for r in result.values() if r['m'] == 'geo')
        rep.append('2022 SAs in the %d covered municipalities: %d; assigned:'
                   ' %d (%.1f%%) [%d geo + %d quarter]; census-pop share'
                   ' assigned: %.2f%%'
                   % (len(semels), len(new_in_scope), got,
                      100 * got / len(new_in_scope), n_geo, n_fb,
                      100 * pop_got / pop_all if pop_all else 0))
        lowconf = [k for k, r in result.items() if r['m'] == 'geo'
                   and (r['dom'] < 0.5 or r['cov'] < 0.5)]
        doms = sorted(r['dom'] for r in result.values() if r['m'] == 'geo')
        rep.append('confidence (geo rows): median dom %.3f; low-confidence'
                   ' (dom<0.5 or cov<0.5): %d (%.1f%%)'
                   % (doms[len(doms) // 2], len(lowconf),
                      100 * len(lowconf) / n_geo))
        if code_match_delta:
            code_match_delta.sort()
            n = len(code_match_delta)
            rep.append('machinery sanity (same code, IoU>=0.9, n=%d):'
                       ' |crosswalk - original| median %.4f  p90 %.4f  max %.4f'
                       % (n, code_match_delta[n // 2],
                          code_match_delta[int(n * .9)], code_match_delta[-1]))
        rep.append('naive code-join would err >0.25 index pts on %d SAs'
                   % naive_wrong)

    # cross-vintage stability of the OUTPUT (crosswalked values)
    for a, b in ((2019, 2021), (2017, 2019)):
        ka, kb = out[str(a)], out[str(b)]
        common = [k for k in ka if k in kb]
        xs = [ka[k]['v'] for k in common]
        ys = [kb[k]['v'] for k in common]
        n = len(xs)
        mx, my = sum(xs) / n, sum(ys) / n
        cov_ = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
        sy = math.sqrt(sum((y - my) ** 2 for y in ys))
        rep.append('crosswalked %d vs %d: n=%d, r=%.4f'
                   % (a, b, n, cov_ / (sx * sy)))

    # per-city sanity for the biggest cities (2019): original pop-weighted
    # mean vs crosswalked census-pop-weighted mean
    rep.append('--- per-city weighted-mean check, vintage 2019 ---')
    big = [3000, 5000, 4000, 70, 6100, 7900, 8300, 2610]
    names = {a['semel']: a['name'] for a in ses[2019]['areas']}
    for s in big:
        orig = [(a['pop'] or 0, a['value']) for a in ses[2019]['areas']
                if a['semel'] == s and a['value'] is not None]
        if not orig:
            continue
        om = sum(p * v for p, v in orig) / sum(p for p, _ in orig)
        xs = [(pop22.get((s, sa), 0), out['2019']['%d|%d' % (s, sa)]['v'])
              for (ss, sa) in geo_new if ss == s
              and '%d|%d' % (s, sa) in out['2019']]
        xm = (sum(p * v for p, v in xs) / sum(p for p, _ in xs)
              if xs and sum(p for p, _ in xs) else float('nan'))
        rep.append('  semel %d (%s): original %.3f -> crosswalked %.3f'
                   ' (delta %+.3f)' % (s, names.get(s, '?'), om, xm, xm - om))

    path = os.path.join(IN_DIR, 'ses_statarea_2022keys.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    rep.append('wrote %s (%.1f KB)' % (path, os.path.getsize(path) / 1024))

    report = '\n'.join(rep)
    with open(os.path.join(IN_DIR, 'ses_crosswalk_report.txt'), 'w',
              encoding='utf-8') as f:
        f.write(report + '\n')
    print(report)


if __name__ == '__main__':
    main()
