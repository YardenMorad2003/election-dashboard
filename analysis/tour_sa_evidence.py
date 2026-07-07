# Evidence for stat-area tour stories — semel-keyed (2022 records carry no loc name)
import json
from collections import defaultdict

sa = json.load(open('data/statarea_2022.json', encoding='utf-8'))['areas']
emg = json.load(open('data/election_map_geo.json', encoding='utf-8'))
sem_name = {}
for f in emg['features']:
    p = f['properties']
    if p.get('semel') and p.get('name'):
        sem_name.setdefault(p['semel'], p['name'])

out = []
def rh(r): return (r.get('blocs') or {}).get('rh')

by_sem = defaultdict(list)
for a, r in sa.items():
    if rh(r) is not None and (r.get('valid') or 0) >= 300:
        by_sem[r['semel']].append(r)

out.append('--- widest internal rh spread, cities with >=10 SAs (valid>=300) ---')
rows = []
for sem, recs in by_sem.items():
    if len(recs) >= 10:
        vals = sorted(recs, key=rh)
        rows.append((rh(vals[-1]) - rh(vals[0]), sem, vals[0], vals[-1], len(recs)))
rows.sort(reverse=True)
for d, sem, lo, hi, n in rows[:14]:
    out.append(f'  {d:5.1f}pp  {sem_name.get(sem, sem)} ({n} SAs) | min sa{lo["sa"]} rh {rh(lo):.1f} '
               f'(win {lo["winner"]}) | max sa{hi["sa"]} rh {rh(hi):.1f} (win {hi["winner"]})')

out.append('--- specific cities: extremes + notable SAs ---')
for sem, nm in [(5000, 'TLV'), (3000, 'JLM'), (4000, 'Haifa'), (6100, 'BneiBrak'), (8600, 'RamatGan'),
                (70, 'Ashdod'), (9000, 'BeerSheva'), (7000, 'Lod'), (8500, 'Ramla'), (7600, 'Acre'), (7400, 'Netanya')]:
    recs = by_sem.get(sem, [])
    if not recs: continue
    vals = sorted(recs, key=rh)
    lo, hi = vals[0], vals[-1]
    med = vals[len(vals)//2]
    out.append(f'{nm} ({sem_name.get(sem,sem)}): {len(recs)} SAs | rh {rh(lo):.1f} (sa{lo["sa"]}, win {lo["winner"]}, '
               f'datiyut {(lo.get("census") or {}).get("datiyut")}) .. {rh(hi):.1f} (sa{hi["sa"]}, win {hi["winner"]}, '
               f'datiyut {(hi.get("census") or {}).get("datiyut")}) | median {rh(med):.1f}')

# TLV: gradient — mean rh by sa-number band (rough north-south proxy won't work; instead top/bottom 5)
recs = sorted(by_sem.get(5000, []), key=rh)
out.append('--- TLV lowest-rh 5 SAs ---')
for r in recs[:5]:
    out.append(f'  sa{r["sa"]} rh {rh(r):.1f} win {r["winner"]} valid {r["valid"]} datiyut {(r.get("census") or {}).get("datiyut")}')
out.append('--- TLV highest-rh 5 SAs ---')
for r in recs[-5:]:
    out.append(f'  sa{r["sa"]} rh {rh(r):.1f} win {r["winner"]} valid {r["valid"]} datiyut {(r.get("census") or {}).get("datiyut")}')

# census fields available
c0 = next(iter(sa.values())).get('census') or {}
out.append('census keys: ' + str(list(c0.keys())))

# Ashdod: highest opposition_right/ל proxy = parties ל share top SAs
recs = by_sem.get(70, [])
recs2 = sorted(recs, key=lambda r: -(r.get('parties') or {}).get('ל', 0))
out.append('--- Ashdod top ל SAs ---')
for r in recs2[:5]:
    out.append(f'  sa{r["sa"]} ל {(r.get("parties") or {}).get("ל",0):.1f}% rh {rh(r):.1f} aliya-field {(r.get("census") or {}).get("aliya")}')

# Lod/Ramla/Acre winner diversity
for sem, nm in [(7000,'Lod'), (8500,'Ramla'), (7600,'Acre')]:
    wins = defaultdict(int)
    for r in by_sem.get(sem, []):
        wins[r['winner']] += 1
    out.append(f'{nm} winners: ' + json.dumps(dict(wins), ensure_ascii=False))

open('analysis/tour_sa_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('ok')
