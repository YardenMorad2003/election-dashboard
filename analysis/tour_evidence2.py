# Turnout evidence for tour stories: turnout = voters/bzb*100 (same as page's getTurnout)
import json

geo = json.load(open('data/election_map_geo.json', encoding='utf-8'))
out = []

def turnout(p, k):
    e = (p.get('elections') or {}).get(k) or {}
    bzb, v = e.get('bzb') or 0, e.get('voters') or 0
    return (v / bzb * 100) if bzb > 0 and v > 0 else None

def arab_pct(p, k):
    e = (p.get('elections') or {}).get(k) or {}
    return e.get('arab_pct') or 0

def eligible(p, k):
    e = (p.get('elections') or {}).get(k) or {}
    return e.get('bzb') or 0

feats = [f['properties'] for f in geo['features']]

for k, prev in (('16', '15'), ('25', '24'), ('24', '23')):
    arab_w = arab_t = jew_w = jew_t = 0
    rows = []
    for p in feats:
        t = turnout(p, k)
        if t is None: continue
        w = eligible(p, k)
        if arab_pct(p, k) > 80:
            arab_w += w; arab_t += t * w
            if w >= 5000: rows.append((t, p.get('name'), turnout(p, prev)))
        elif arab_pct(p, k) < 20:
            jew_w += w; jew_t += t * w
    out.append(f'=== K{k}: weighted turnout — Arab localities (>80% arab): '
               f'{arab_t/arab_w:.1f}%  |  Jewish (<20%): {jew_t/jew_w:.1f}%')
    rows.sort()
    out.append(f'  sample Arab localities (eligible>=5k), turnout K{k} (K{prev}):')
    for t, nm, tp in rows[:10]:
        out.append(f'    {t:5.1f}%  {nm}  (prev {tp if tp is None else round(tp,1)})')

# K16 vs K15 turnout drop, sizable localities overall
rows = []
for p in feats:
    t16, t15 = turnout(p, '16'), turnout(p, '15')
    if t16 and t15 and eligible(p, '16') >= 10000:
        rows.append((t16 - t15, p.get('name'), t15, t16, arab_pct(p, '16')))
rows.sort()
out.append('=== K16 turnout drop vs K15, biggest (eligible>=10k) ===')
for d, nm, a, b, ap in rows[:12]:
    out.append(f'  {d:+6.1f}pp  {nm}  ({a:.1f} -> {b:.1f})  arab={ap:.0f}')

# K25 turnout in haredi cities (for the demographic-engine story)
out.append('=== K25 turnout, Haredi cities ===')
for nm in ('מודיעין עילית', 'ביתר עילית', 'בני ברק', 'אלעד', 'רכסים'):
    p = next((q for q in feats if q.get('name') == nm), None)
    if p: out.append(f'  {nm}: turnout {turnout(p, "25"):.1f}%')

# K25/K24/K21 RZ national context + Tel Aviv vs national gap
p = next((q for q in feats if q.get('name') == 'תל אביב - יפו'), None)
if p:
    e = (p.get('elections') or {}).get('25') or {}
    out.append(f"=== Tel Aviv K25: right_haredi {e.get('right_haredi_pct')}%, left {e.get('left_pct')}%, "
               f"center {e.get('center_pct')}%, turnout {turnout(p,'25'):.1f}%")
p = next((q for q in feats if q.get('name') == 'בני ברק'), None)
if p:
    e = (p.get('elections') or {}).get('25') or {}
    out.append(f"=== Bnei Brak K25: right_haredi {e.get('right_haredi_pct')}%")

open('analysis/tour_evidence2_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('ok')
