# -*- coding: utf-8 -*-
"""ML Phase 0b: build the SA x lineage vote tensor + census features + links.

Outputs (analysis/ml/out/):
  votes_k{16..25}.csv    — one row per SA with votes: semel, sa, valid,
                           turnout + one share column per lineage (% of valid;
                           'other' absorbs the residual below-threshold vote)
  census_2022.csv        — census features per 2022-geo SA (used by K21-K25)
                           incl. ses_value/ses_cluster (2019 vintage: K21-23
                           analyses should use it; 2021 vintage col too)
  census_2008.csv        — census features per 2009-geo SA (K18-K20)
  links_2009_to_2022.json, links_1995_to_2022.json
                         — dominant-ancestor links {new "semel|sa":
                           [old "semel|sa", overlap_share_of_new]}
Sanity: per-election lineage totals (valid-weighted) vs national results.

Run from repo root: python -X utf8 analysis/ml/prep_tensor.py   (~2 min)
"""
import csv
import json
import math
import os
from collections import defaultdict

from shapely.geometry import shape
from shapely.ops import transform
from shapely.strtree import STRtree

OUT = os.path.join('analysis', 'ml', 'out')
KX = 111320 * math.cos(math.radians(31.8))
KY = 111320

ELECTIONS = {  # k -> (data file, geo era)
    '16': ('statarea_k16.json', '1995'), '17': ('statarea_k17.json', '1995'),
    '18': ('statarea_2009.json', '2009'), '19': ('statarea_k19.json', '2009'),
    '20': ('statarea_k20.json', '2009'), '21': ('statarea_k21.json', '2022'),
    '22': ('statarea_k22.json', '2022'), '23': ('statarea_k23.json', '2022'),
    '24': ('statarea_k24.json', '2022'), '25': ('statarea_2022.json', '2022'),
}
CENSUS_KEYS = ['pop', 'density', 'datiyut', 'age_med', 'age0_19', 'age65',
               'acad', 'med_wage', 'top2dec', 'work', 'orig_il', 'orig_eur',
               'orig_asia', 'orig_afr', 'orig_am', 'aliya02', 'chld',
               'hh_size', 'own', 'rent', 'no_car', 'religion', 'rel_dom',
               'ses_cluster', 'matric', 'pc', 'income']


def proj(g):
    return transform(lambda x, y, z=None: (x * KX, y * KY), g)


def load_geo(path):
    gj = json.load(open(path, encoding='utf-8'))
    out = {}
    for f in gj['features']:
        p = f['properties']
        g = proj(shape(f['geometry']))
        out[(p['semel'], p['sa'])] = g.buffer(0) if not g.is_valid else g
    return out


def build_links(old_path, new_geo, out_name):
    old = load_geo(old_path)
    by_semel = defaultdict(list)
    for k, g in old.items():
        by_semel[k[0]].append((k, g))
    trees = {s: STRtree([g for _, g in lst]) for s, lst in by_semel.items()}
    links = {}
    for (semel, sa), gn in new_geo.items():
        lst = by_semel.get(semel)
        if not lst:
            continue
        best, ba = None, 0.0
        for i in trees[semel].query(gn):
            k, go = lst[i]
            a = gn.intersection(go).area
            if a > ba:
                ba, best = a, k
        if best and gn.area and ba / gn.area >= 0.10:
            links['%d|%d' % (semel, sa)] = ['%d|%d' % best,
                                            round(ba / gn.area, 3)]
    path = os.path.join(OUT, out_name)
    json.dump(links, open(path, 'w', encoding='utf-8'), ensure_ascii=False)
    print('%s: %d links' % (out_name, len(links)))
    return links


def main():
    os.makedirs(OUT, exist_ok=True)
    lin = json.load(open(os.path.join(OUT, 'party_lineages.json'),
                         encoding='utf-8'))
    lmap = lin['map']
    lineages = sorted(set(lmap.values()))
    pn = json.load(open('data/parties_national.json', encoding='utf-8'))

    # ---- votes tensor ----
    for k, (fname, era) in sorted(ELECTIONS.items(), key=lambda x: int(x[0])):
        sa_data = json.load(open(os.path.join('data', fname),
                                 encoding='utf-8'))
        rows = []
        nat = defaultdict(float)
        tot_valid = 0.0
        for rec in sa_data['areas'].values():
            if not rec.get('parties') or not rec.get('valid'):
                continue
            shares = defaultdict(float)
            for code, sh in rec['parties'].items():
                lid = lmap.get('%s|%s' % (k, code))
                if lid is None:
                    lid = 'other'   # sub-threshold or unlisted code
                shares[lid] += sh
            listed = sum(shares.values())
            shares['other'] += max(0.0, round(100 - listed, 2))
            row = {'semel': rec['semel'], 'sa': rec['sa'],
                   'valid': rec['valid'], 'turnout': rec.get('turnout')}
            for l in lineages:
                row[l] = round(shares.get(l, 0.0), 2)
            rows.append(row)
            for l in lineages:
                nat[l] += shares.get(l, 0.0) * rec['valid']
            tot_valid += rec['valid']
        path = os.path.join(OUT, 'votes_k%s.csv' % k)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, ['semel', 'sa', 'valid', 'turnout'] + lineages)
            w.writeheader()
            w.writerows(rows)
        # sanity vs national results
        nat_true = defaultdict(float)
        e = pn[k]
        tot_nat = sum(e['national_votes'].get(p['code'], 0)
                      for p in e['party_list'])
        all_votes = sum(e['national_votes'].values()) if 'national_votes' in e else 0
        for p in e['party_list']:
            lid = lmap['%s|%s' % (k, p['code'])]
            nat_true[lid] += e['national_votes'].get(p['code'], 0)
        msg = []
        for l in lineages:
            got = nat[l] / tot_valid if tot_valid else 0
            true = 100 * nat_true[l] / all_votes if all_votes else float('nan')
            if l != 'other' and abs(got - true) > 2.0:
                msg.append('%s got %.1f true %.1f' % (l, got, true))
        print('K%s [%s geo]: %d SAs%s' % (k, era, len(rows),
              ('  DRIFT>2pp: ' + '; '.join(msg)) if msg else '  ok(<2pp)'))

    # ---- census features ----
    ses = json.load(open('data/ses_statarea.json', encoding='utf-8'))
    for era, src, ses_v in (('2022', 'statarea_2022.json', ('2019', '2021')),
                            ('2008', 'statarea_2009.json', None)):
        sa_data = json.load(open(os.path.join('data', src), encoding='utf-8'))
        rows = []
        for rec in sa_data['areas'].values():
            c = rec.get('census')
            if not c:
                continue
            row = {'semel': rec['semel'], 'sa': rec['sa']}
            for key in CENSUS_KEYS:
                if key in c:
                    row[key] = c[key]
            if ses_v:
                for v in ses_v:
                    e = ses[v].get('%d|%d' % (rec['semel'], rec['sa']))
                    row['ses%s_value' % v] = e[0] if e else None
                    row['ses%s_cluster' % v] = e[1] if e else None
                    row['ses%s_src' % v] = e[2] if e else None
            rows.append(row)
        cols = sorted({k for r in rows for k in r},
                      key=lambda c: (c not in ('semel', 'sa'), c))
        path = os.path.join(OUT, 'census_%s.csv' % era)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, cols)
            w.writeheader()
            w.writerows(rows)
        print('census_%s: %d SAs, %d cols' % (era, len(rows), len(cols)))

    # ---- cross-era links ----
    new_geo = load_geo('data/statarea_2022_geo.json')
    build_links('data/statarea_2009_geo.json', new_geo,
                'links_2009_to_2022.json')
    build_links('data/statarea_1995_geo.json', new_geo,
                'links_1995_to_2022.json')


if __name__ == '__main__':
    main()
