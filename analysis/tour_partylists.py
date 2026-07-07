# Dump party lists + national pcts for the 11 remaining tour elections
import json

pn = json.load(open('data/parties_national.json', encoding='utf-8'))
core = json.load(open('data/core.json', encoding='utf-8'))
nat = core['national']['elections']
out = []

for k in ('13', '14', '15', '17', '18', '19', '20', '21', '22', '23', '24'):
    el = pn[k]
    n = nat[k]
    out.append(f"=== K{k} ({n['year']}) turnout {n['turnout_pct']}% | rh {n['right_haredi_pct']} cla {n['center_left_arab_pct']} "
               f"| r {n['right_pct']} h {n['haredi_pct']} c {n['center_pct']} l {n['left_pct']} a {n['arab_pct']} opp {n['opposition_right_pct']}")
    for e in sorted(el.get('party_list', []), key=lambda x: -el['national'].get(x['code'], 0)):
        pct = el['national'].get(e['code'], 0)
        out.append(f"  {e['code']:>5}  {pct:5.2f}%  {e.get('bloc','?'):<17} {e['name']}")

open('analysis/tour_partylists_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('ok')
