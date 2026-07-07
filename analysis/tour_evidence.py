# Evidence pass for guided-tour stories (pilot: K16 + K25).
# For each candidate story, list top localities so card text quotes real numbers.
import json

geo = json.load(open('data/election_map_geo.json', encoding='utf-8'))
pbl = json.load(open('data/parties_by_locality.json', encoding='utf-8'))

out = []
feats = geo['features']
p0 = feats[0]['properties']
out.append('geo props keys: ' + str(list(p0.keys())))
els = p0.get('elections') or {}
if els:
    k0 = sorted(els)[0]
    out.append(f'elections[{k0}] keys: ' + str(list(els[k0].keys())))

# name -> {size proxy, per-election records}
by_name = {}
for f in feats:
    p = f['properties']
    nm = p.get('name') or p.get('NAME')
    if nm:
        by_name[nm] = p

def voters(p, k):
    e = (p.get('elections') or {}).get(k) or {}
    return e.get('voters') or e.get('eligible') or 0

def top_party(k, code, min_voters=2000, n=14):
    rows = []
    for nm, share in (pbl.get(k) or {}).items():
        v = share.get(code)
        if v is None: continue
        p = by_name.get(nm)
        sz = voters(p, k) if p else 0
        if sz >= min_voters:
            rows.append((v, nm, sz))
    rows.sort(reverse=True)
    return rows[:n]

def dump(title, rows, fmt=lambda r: f'  {r[0]:6.2f}%  {r[1]}  (voters {r[2]:,})'):
    out.append(f'--- {title} ---')
    for r in rows: out.append(fmt(r))

# ===== K16 (2003) =====
dump('K16 Shinui (יש) top', top_party('16','יש'))
dump('K16 Likud (מחל) top', top_party('16','מחל'))
dump('K16 Am Ehad (ם) top', top_party('16','ם'))
dump('K16 YB-NU (ל) top', top_party('16','ל'))
dump('K16 Yisrael BaAliyah (כן) top', top_party('16','כן'))
dump('K16 Meretz (מרצ) top', top_party('16','מרצ'))

# Labor swing K15->K16 (אמת both years)
rows = []
for nm, sh in (pbl.get('16') or {}).items():
    prev = (pbl.get('15') or {}).get(nm, {})
    a, b = prev.get('אמת'), sh.get('אמת')
    p = by_name.get(nm)
    if a is None or b is None or not p: continue
    if voters(p,'16') >= 5000:
        rows.append((b - a, nm, a, b))
rows.sort()
dump('K16 Labor swing 99->03 biggest drops (voters>=5k)', rows[:12],
     lambda r: f'  {r[0]:+6.1f}pp  {r[1]}  ({r[2]:.1f} -> {r[3]:.1f})')

# Shas swing K15->K16
rows = []
for nm, sh in (pbl.get('16') or {}).items():
    prev = (pbl.get('15') or {}).get(nm, {})
    a, b = prev.get('שס'), sh.get('שס')
    p = by_name.get(nm)
    if a is None or b is None or not p: continue
    if voters(p,'16') >= 5000:
        rows.append((b - a, nm, a, b))
rows.sort()
dump('K16 Shas swing 99->03 biggest drops (voters>=5k)', rows[:12],
     lambda r: f'  {r[0]:+6.1f}pp  {r[1]}  ({r[2]:.1f} -> {r[3]:.1f})')

# K16 turnout: lowest among sizable localities + arab-bloc localities
rows = []
for nm, p in by_name.items():
    e = (p.get('elections') or {}).get('16') or {}
    t = e.get('turnout_pct')
    if t and voters(p,'16') >= 4000:
        rows.append((t, nm, e.get('arab_pct') or 0))
rows.sort()
dump('K16 lowest turnout (voters>=4k)', rows[:14],
     lambda r: f'  {r[0]:5.1f}%  {r[1]}  (arab_pct {r[2]:.0f})')

# ===== K25 (2022) =====
dump('K25 Religious Zionism (ט) top', top_party('25','ט'))
dump('K25 Yesh Atid (פה) top', top_party('25','פה'))
dump('K25 Machane Mamlachti (כן) top', top_party('25','כן'))
dump('K25 Meretz (מרצ) top', top_party('25','מרצ'))
dump('K25 Labor (אמת) top', top_party('25','אמת'))
dump('K25 Lieberman (ל) top', top_party('25','ל'))

# RZ swing K24->K25 in big cities (code ט both)
rows = []
for nm, sh in (pbl.get('25') or {}).items():
    prev = (pbl.get('24') or {}).get(nm, {})
    a, b = prev.get('ט'), sh.get('ט')
    p = by_name.get(nm)
    if a is None or b is None or not p: continue
    if voters(p,'25') >= 20000:
        rows.append((b - a, nm, a, b))
rows.sort(reverse=True)
dump('K25 RZ swing 21->22 biggest gains (voters>=20k)', rows[:14],
     lambda r: f'  {r[0]:+6.1f}pp  {r[1]}  ({r[2]:.1f} -> {r[3]:.1f})')

# K25 haredi pct top (from geo elections record)
rows = []
for nm, p in by_name.items():
    e = (p.get('elections') or {}).get('25') or {}
    h = e.get('haredi_pct')
    if h and voters(p,'25') >= 3000:
        rows.append((h, nm, voters(p,'25')))
rows.sort(reverse=True)
dump('K25 haredi_pct top (voters>=3k)', rows[:10])

# K25 vs K24 turnout change, Arab localities (arab_pct>80)
rows = []
for nm, p in by_name.items():
    e25 = (p.get('elections') or {}).get('25') or {}
    e24 = (p.get('elections') or {}).get('24') or {}
    if (e25.get('arab_pct') or 0) > 80 and e24.get('turnout_pct') and e25.get('turnout_pct') and voters(p,'25') >= 4000:
        rows.append((e25['turnout_pct'] - e24['turnout_pct'], nm, e24['turnout_pct'], e25['turnout_pct']))
rows.sort(reverse=True)
dump('K25 Arab-locality turnout change vs K24 (voters>=4k)', rows[:12],
     lambda r: f'  {r[0]:+6.1f}pp  {r[1]}  ({r[2]:.1f} -> {r[3]:.1f})')

# K25 bloc knife-edge: biggest localities with right_haredi near 50
rows = []
for nm, p in by_name.items():
    e = (p.get('elections') or {}).get('25') or {}
    rh = e.get('right_haredi_pct')
    if rh is not None and voters(p,'25') >= 30000:
        rows.append((abs(rh-50), nm, rh, voters(p,'25')))
rows.sort()
dump('K25 most-balanced big localities (voters>=30k)', rows[:12],
     lambda r: f'  |d|={r[0]:4.1f}  {r[1]}  right_haredi {r[2]:.1f}%  voters {r[3]:,}')

open('analysis/tour_evidence_out.txt','w',encoding='utf-8').write('\n'.join(out))
print('ok', len(out))
