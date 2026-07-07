# Fill-in evidence: turnout coverage per election, K19 merger math, K21->K22 reunion vs combined lists
import json

geo = json.load(open('data/election_map_geo.json', encoding='utf-8'))
pbl = json.load(open('data/parties_by_locality.json', encoding='utf-8'))
out = []

by_name = {}
for f in geo['features']:
    p = f['properties']
    nm = p.get('name')
    if nm and nm not in by_name:
        by_name[nm] = p

def ed(p, k): return (p.get('elections') or {}).get(k) or {}
def turnout(p, k):
    e = ed(p, k); bzb, v = e.get('bzb') or 0, e.get('voters') or 0
    return (v / bzb * 100) if bzb > 0 and v > 0 else None

# 1. turnout coverage + weighted arab/jewish for all elections
out.append('=== turnout coverage (localities with bzb+voters) & weighted arab/jewish ===')
for k in ('13','14','15','16','17','18','19','20','21','22','23','24','25'):
    n = sum(1 for p in by_name.values() if turnout(p, k) is not None)
    aw = at = jw = jt = 0
    for p in by_name.values():
        t = turnout(p, k)
        if t is None: continue
        w = ed(p, k).get('bzb') or 0
        ap = ed(p, k).get('arab_pct') or 0
        if ap > 80: aw += w; at += t * w
        elif ap < 20: jw += w; jt += t * w
    a = at / aw if aw else 0; j = jt / jw if jw else 0
    out.append(f'  K{k}: {n} localities | Arab {a:.1f}% Jewish {j:.1f}%')

# 2. K19 merged list vs K18 Likud+YB combined
out.append('=== K19 (Likud-Beiteinu) vs K18 Likud+YB combined ===')
for nm in ('אריאל','כרמיאל','אשדוד','קרית ים','באר שבע','נצרת עילית','נוף הגליל','ערד','מגדל העמק'):
    s18 = (pbl.get('18') or {}).get(nm); s19 = (pbl.get('19') or {}).get(nm)
    if not s18 or not s19: continue
    comb = (s18.get('מחל') or 0) + (s18.get('ל') or 0)
    out.append(f"  {nm}: K18 מחל {s18.get('מחל')} + ל {s18.get('ל')} = {comb:.1f} -> K19 מחל {s19.get('מחל')}")

# 3. K22 ודעם vs K21 ום+דעם combined
out.append('=== K22 Joint List vs K21 both lists combined ===')
for nm in ('תל שבע','סח\'נין','אום אל פחם','נצרת','טייבה','רהט','טמרה','כפר קאסם'):
    s21 = (pbl.get('21') or {}).get(nm); s22 = (pbl.get('22') or {}).get(nm)
    if not s21 or not s22: continue
    comb = (s21.get('ום') or 0) + (s21.get('דעם') or 0)
    out.append(f"  {nm}: K21 ום+דעם = {comb:.1f} -> K22 ודעם {s22.get('ודעם')}")

# 4. K23 Acre detail + K21 national wasted-right total sanity
p = by_name.get('עכו')
if p:
    e = ed(p, '23')
    out.append(f"=== Acre K23: rh {e.get('right_haredi_pct')} arab_pct {e.get('arab_pct')} turnout {turnout(p,'23')}")

# 5. K15 Shas 1999 national map spread: how many localities >=20%
n20 = sum(1 for nm, sh in (pbl.get('15') or {}).items() if (sh.get('שס') or 0) >= 20)
n20_prev = sum(1 for nm, sh in (pbl.get('14') or {}).items() if (sh.get('שס') or 0) >= 20)
out.append(f'=== localities with Shas >=20%: K14 {n20_prev} -> K15 {n20}')

open('analysis/tour_evidence_fill_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('ok')
