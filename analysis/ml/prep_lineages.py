# -*- coding: utf-8 -*-
"""ML Phase 0a: draft party-lineage table K13-K25 from transfer-matrix evidence.

For every adjacent election pair the site's ecological transfer matrices
(data/vote_transfers.json, Cain-method) give M[i][j] = share of source party
i's voters going to destination j, plus source vote counts. For each
destination party we compute its VOTE-ORIGIN COMPOSITION (who its voters
supported last time). A destination whose voters come predominantly (>= DOM)
from one source party is chained into that source's lineage; anything else
(mergers, new parties, splits) is flagged AMBIGUOUS for manual adjudication.

Outputs (analysis/ml/out/):
  lineage_evidence.json  — per (election, party): parent composition
  party_lineages_draft.json — auto-chained lineages + ambiguous list
  lineage_review.txt     — human-readable adjudication sheet

Run from repo root: python -X utf8 analysis/ml/prep_lineages.py
"""
import json
import os
from collections import defaultdict

DOM = 0.55          # dominant-parent threshold (share of dest votes)
MIN_SHARE = 0.10    # parents below this are noise for the evidence sheet
OUT = os.path.join('analysis', 'ml', 'out')


def main():
    os.makedirs(OUT, exist_ok=True)
    vt = json.load(open(os.path.join('data', 'vote_transfers.json'),
                        encoding='utf-8'))
    pn = json.load(open(os.path.join('data', 'parties_national.json'),
                        encoding='utf-8'))

    # name -> code map per election (transfers use harmonized names)
    name2code = {k: {p['name']: p['code'] for p in v['party_list']}
                 for k, v in pn.items()}

    evidence = {}          # (k, party_name) -> [(parent_name, share_of_dest)]
    order = sorted(vt['transitions'], key=lambda s: int(s.split('_')[0]))
    for key in order:
        t = vt['transitions'][key]
        pw = t['party_with_abstention']
        src, dst = pw['from_labels'], pw['to_labels']
        M, votes = pw['M'], pw['source_votes']
        k_to = t['to']['k']
        # dest composition: inflow[i][j] = M[i][j] * votes[i]
        for j, d in enumerate(dst):
            if d in ('other', 'לא הצביעו'):
                continue
            inflow = [(src[i], M[i][j] * votes[i]) for i in range(len(src))]
            tot = sum(v for _, v in inflow)
            if tot <= 0:
                continue
            comp = sorted(((s, v / tot) for s, v in inflow if v / tot >= MIN_SHARE),
                          key=lambda x: -x[1])
            evidence[(k_to, d)] = comp

    # chain lineages forward from K13
    first_k = order[0].split('_')[0]
    lineage_of = {}        # (k, party_name) -> lineage id
    lineages = defaultdict(dict)   # lid -> {k: [party names]}
    ambiguous = []
    for p in pn[first_k]['party_list']:
        lid = p['name']
        lineage_of[(first_k, p['name'])] = lid
        lineages[lid][first_k] = [p['name']]

    for key in order:
        t = vt['transitions'][key]
        k_from, k_to = t['from']['k'], t['to']['k']
        for p in pn.get(k_to, {}).get('party_list', []):
            d = p['name']
            comp = evidence.get((k_to, d), [])
            # drop non-party sources for dominance judgement
            party_comp = [(s, sh) for s, sh in comp
                          if s not in ('other', 'לא הצביעו')]
            same_name_parent = (k_from, d) in lineage_of
            if same_name_parent:
                lid = lineage_of[(k_from, d)]
                lineage_of[(k_to, d)] = lid
                lineages[lid].setdefault(k_to, []).append(d)
                continue
            if party_comp and party_comp[0][1] >= DOM and \
               (k_from, party_comp[0][0]) in lineage_of:
                lid = lineage_of[(k_from, party_comp[0][0])]
                lineage_of[(k_to, d)] = lid
                lineages[lid].setdefault(k_to, []).append(d)
                continue
            ambiguous.append({'k': k_to, 'party': d,
                              'code': name2code.get(k_to, {}).get(d),
                              'composition': [[s, round(sh, 3)]
                                              for s, sh in comp]})

    # ---- write outputs ----
    with open(os.path.join(OUT, 'lineage_evidence.json'), 'w',
              encoding='utf-8') as f:
        json.dump({f'{k}|{d}': [[s, round(sh, 4)] for s, sh in comp]
                   for (k, d), comp in evidence.items()},
                  f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, 'party_lineages_draft.json'), 'w',
              encoding='utf-8') as f:
        json.dump({'meta': {'method': 'transfer-matrix chaining, DOM=%.2f' % DOM,
                            'status': 'DRAFT - pending manual adjudication'},
                   'lineages': lineages, 'ambiguous': ambiguous},
                  f, ensure_ascii=False, indent=1)

    lines = ['LINEAGE ADJUDICATION SHEET', '=' * 60,
             'auto-chained lineages: %d; ambiguous cases: %d' %
             (len(lineages), len(ambiguous)), '']
    lines.append('--- AMBIGUOUS (need a call) ---')
    for a in ambiguous:
        comp = '  +  '.join('%s %.0f%%' % (s, sh * 100)
                            for s, sh in a['composition']) or '(no evidence)'
        lines.append('K%s  %s [%s]:  voters came from  %s'
                     % (a['k'], a['party'], a['code'], comp))
    lines.append('')
    lines.append('--- AUTO-CHAINED (spot-check) ---')
    for lid, mem in sorted(lineages.items()):
        span = sorted(mem, key=int)
        chain = ' -> '.join('K%s:%s' % (k, '/'.join(mem[k])) for k in span
                            if mem[k] != [lid])
        lines.append('%s  (K%s-K%s)%s'
                     % (lid, span[0], span[-1],
                        ('   ' + chain) if chain else ''))
    with open(os.path.join(OUT, 'lineage_review.txt'), 'w',
              encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('lineages: %d, ambiguous: %d -> %s' %
          (len(lineages), len(ambiguous), OUT))


if __name__ == '__main__':
    main()
