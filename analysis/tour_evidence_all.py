# Evidence pass for the 11 remaining tours: per planned story, top-share tables,
# swings vs previous election, turnout splits (voters/bzb, page convention), balanced localities.
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

def ed(p, k):
    return (p.get('elections') or {}).get(k) or {}

def voters(p, k):
    return ed(p, k).get('voters') or 0

def turnout(p, k):
    e = ed(p, k)
    bzb, v = e.get('bzb') or 0, e.get('voters') or 0
    return (v / bzb * 100) if bzb > 0 and v > 0 else None

def top_party(k, code, min_v=2000, n=12):
    rows = []
    for nm, share in (pbl.get(k) or {}).items():
        v = share.get(code)
        p = by_name.get(nm)
        if v is None or not p: continue
        if voters(p, k) >= min_v:
            rows.append((v, nm, voters(p, k)))
    rows.sort(reverse=True)
    return rows[:n]

def swing(k, prev, code_k, code_prev, min_v=5000, n=10, direction='drop'):
    rows = []
    for nm, sh in (pbl.get(k) or {}).items():
        pv = (pbl.get(prev) or {}).get(nm, {})
        a, b = pv.get(code_prev), sh.get(code_k)
        p = by_name.get(nm)
        if a is None or b is None or not p: continue
        if voters(p, k) >= min_v:
            rows.append((b - a, nm, a, b))
    rows.sort(reverse=(direction == 'gain'))
    return rows[:n]

def wturnout(k):
    aw = at = jw = jt = 0
    for p in by_name.values():
        t = turnout(p, k)
        if t is None: continue
        w = ed(p, k).get('bzb') or 0
        ap = ed(p, k).get('arab_pct') or 0
        if ap > 80: aw += w; at += t * w
        elif ap < 20: jw += w; jt += t * w
    return (at / aw if aw else 0, jt / jw if jw else 0)

def tchange(k, prev, arab_only=None, min_v=4000, n=10, direction='drop'):
    rows = []
    for nm, p in by_name.items():
        a, b = turnout(p, prev), turnout(p, k)
        if a is None or b is None or voters(p, k) < min_v: continue
        ap = ed(p, k).get('arab_pct') or 0
        if arab_only is True and ap <= 80: continue
        if arab_only is False and ap >= 20: continue
        rows.append((b - a, nm, a, b))
    rows.sort(reverse=(direction == 'gain'))
    return rows[:n]

def balanced(k, min_v=25000, n=10):
    rows = []
    for nm, p in by_name.items():
        rh = ed(p, k).get('right_haredi_pct')
        if rh is not None and voters(p, k) >= min_v:
            rows.append((abs(rh - 50), nm, rh, voters(p, k)))
    rows.sort()
    return rows[:n]

def dump(title, rows, fmt):
    out.append(f'--- {title} ---')
    for r in rows: out.append(fmt(*r))

F_TOP = lambda v, nm, sz: f'  {v:6.2f}%  {nm}  ({sz:,})'
F_SW = lambda d, nm, a, b: f'  {d:+6.1f}pp  {nm}  ({a:.1f} -> {b:.1f})'

# (k, kind, args) — kind: top / swing / turnout / tchange / balanced
PLAN = [
  ('13','top',('אמת',)), ('13','top',('מחל',)), ('13','top',('מרצ', 400)), ('13','top',('ץ',)),
  ('13','top',('שס',)), ('13','top',('ת', 400)), ('13','balanced',()),
  ('14','swing',('שס','שס','gain')), ('14','top',('כן',)), ('14','swing',('אמת','אמת','drop')),
  ('14','top',('הד', 1000)), ('14','top',('מרץ', 400)), ('14','top',('ב',)),
  ('15','swing',('שס','שס','gain')), ('15','swing',('מחל','מחל','drop')), ('15','top',('יש',)),
  ('15','top',('פה',)), ('15','top',('ל',)), ('15','top',('כן',)), ('15','top',('יט', 1000)),
  ('17','top',('כן',)), ('17','swing',('מחל','מחל','drop')), ('17','top',('זך',)),
  ('17','swing',('ל','ל','gain')), ('17','top',('אמת',)), ('17','top',('טב', 1000)),
  ('17','tchange',('16', None, 'drop')), ('17','turnout',()),
  ('18','top',('כן',)), ('18','top',('ל',)), ('18','swing',('אמת','אמת','drop')),
  ('18','swing',('מחל','מחל','gain')), ('18','top',('ט', 1000)), ('18','balanced',()),
  ('19','top',('פה',)), ('19','top',('טב',)), ('19','swing',('מחל','מחל','drop')),
  ('19','top',('אמת',)), ('19','top',('צפ',)),
  ('20','swing',('מחל','מחל','gain')), ('20','top',('ודעם',)), ('20','top',('אמת',)),
  ('20','top',('כ',)), ('20','swing',('טב','טב','drop')), ('20','tchange',('19', True, 'gain')), ('20','turnout',()),
  ('21','top',('פה',)), ('21','top',('מחל',)), ('21','top',('נ', 1000)), ('21','swing',('אמת','אמת','drop')),
  ('21','tchange',('20', True, 'drop')), ('21','turnout',()), ('21','top',('ום', 1000)), ('21','top',('דעם', 1000)),
  ('22','swing',('ל','ל','gain')), ('22','tchange',('21', True, 'gain')), ('22','turnout',()),
  ('22','top',('כף', 1000)), ('22','swing',('ודעם','ום','gain')),
  ('23','swing',('מחל','מחל','gain')), ('23','top',('ודעם', 1000)), ('23','tchange',('22', True, 'gain')),
  ('23','turnout',()), ('23','balanced',()),
  ('24','swing',('מחל','מחל','drop')), ('24','top',('ת', 1000)), ('24','top',('ב', 1000)),
  ('24','top',('עם', 1000)), ('24','top',('ודעם', 1000)), ('24','top',('ט', 1000)),
  ('24','tchange',('23', True, 'drop')), ('24','turnout',()),
]

for k, kind, args in PLAN:
    if kind == 'top':
        code = args[0]; mv = args[1] if len(args) > 1 else 2000
        dump(f'K{k} top {code} (v>={mv})', top_party(k, code, mv), F_TOP)
    elif kind == 'swing':
        code_k, code_prev, dr = args
        prev = str(int(k) - 1)
        dump(f'K{k} swing {code_k} vs K{prev} ({dr})', swing(k, prev, code_k, code_prev, direction=dr), F_SW)
    elif kind == 'turnout':
        a, j = wturnout(k)
        out.append(f'--- K{k} weighted turnout: Arab {a:.1f}% | Jewish {j:.1f}% ---')
    elif kind == 'tchange':
        prev, arab, dr = args
        lbl = 'arab' if arab else ('jewish' if arab is False else 'all')
        dump(f'K{k} turnout change vs K{prev} ({lbl},{dr})', tchange(k, prev, arab, direction=dr), F_SW)
    elif kind == 'balanced':
        dump(f'K{k} balanced big localities', balanced(k),
             lambda d, nm, rh, v: f'  |d|={d:4.1f}  {nm}  rh {rh:.1f}%  ({v:,})')

open('analysis/tour_evidence_all_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('lines:', len(out))
