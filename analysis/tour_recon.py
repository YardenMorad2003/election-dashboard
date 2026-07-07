# Recon for guided-tour story curation: dump party catalogs + data shapes (K16, K25)
import json, sys

ROOT = '.'
out = []

pn = json.load(open(f'{ROOT}/data/parties_national.json', encoding='utf-8'))
pbl = json.load(open(f'{ROOT}/data/parties_by_locality.json', encoding='utf-8'))
core = json.load(open(f'{ROOT}/data/core.json', encoding='utf-8'))

for k in ('16', '25'):
    out.append(f'=== K{k} national party list ===')
    el = pn[k]
    for e in sorted(el.get('party_list', []), key=lambda x: -el['national'].get(x['code'], 0)):
        pct = el['national'].get(e['code'], 0)
        out.append(f"  {e['code']:>4}  {pct:5.2f}%  bloc={e.get('bloc','?'):<18} {e['name']}")

out.append('\n=== parties_by_locality top-level keys ===')
out.append(str(list(pbl.keys())[:5]))
k16 = pbl.get('16')
if k16:
    names = list(k16.keys())
    out.append(f'K16 localities: {len(names)}; sample entry ({names[0]}):')
    out.append(json.dumps(k16[names[0]], ensure_ascii=False)[:400])

out.append('\n=== core.json national elections keys ===')
nat = core.get('national', {}).get('elections', {})
out.append(str(list(nat.keys())))
out.append('K16 national record: ' + json.dumps(nat.get('16', {}), ensure_ascii=False)[:600])
out.append('K25 national record: ' + json.dumps(nat.get('25', {}), ensure_ascii=False)[:600])

open('analysis/tour_recon_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('written', len(out), 'lines')
