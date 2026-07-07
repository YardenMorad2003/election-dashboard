# Headline bloc flows for transfers-story candidates (with-abstention variant, matching page default)
import json

D = json.load(open('data/vote_transfers.json', encoding='utf-8'))
out = []

def dump(k):
    t = D['transitions'][k]
    labs = t['bloc_labels'] + ['dnv']            # page appends "didn't vote"? verify by matrix width
    bw = t['bloc_with_abstention']
    M = bw['M']
    n = len(M)
    m = len(M[0])
    out.append(f"=== {k}  ({t['from']['year']}→{t['to']['year']})  rows {n} cols {m} labels {t['bloc_labels']}")
    src = bw.get('src') or bw.get('source_sizes')
    out.append('  bw keys: ' + str(list(bw.keys())))
    # print all cells >= 8% off-diagonal
    for i in range(n):
        for j in range(m):
            v = M[i][j]
            if v >= 0.08 and i != j:
                fl = t['bloc_labels'][i] if i < len(t['bloc_labels']) else f'row{i}'
                tl = t['bloc_labels'][j] if j < len(t['bloc_labels']) else f'col{j}'
                out.append(f'    {fl} -> {tl}: {v*100:.1f}%')

for k in ('15_to_16', '16_to_17', '20_to_21', '23_to_24', '24_to_25', '21_to_22'):
    dump(k)

open('analysis/tt_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('ok')
