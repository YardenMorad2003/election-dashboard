# Validate map_tours.json: parseability, focus names exist in geo, party codes exist in that
# election's party list, modes exist on the page.
import json, re, sys

tours = json.load(open('data/map_tours.json', encoding='utf-8'))
geo = json.load(open('data/election_map_geo.json', encoding='utf-8'))
pn = json.load(open('data/parties_national.json', encoding='utf-8'))

geo_names = {f['properties'].get('name') for f in geo['features']}
page = open('election_map.html', encoding='utf-8').read()
mode_ids = set(re.findall(r"\{id:'([a-z_]+)'", page))

# tour states use canonical codes; the page maps them per-election via PARTY_ALIASES
ALIASES = {'מרצ': {'14': 'מרץ', '19': 'מרץ'}, 'נץ': {'22': 'כף'}}

def codes_for(k):
    cs = {e['code'] for e in pn[k]['party_list']}
    for canon, by_el in ALIASES.items():
        if by_el.get(k) in cs:
            cs.add(canon)
    return cs

errs = []
for k, tour in tours['tours'].items():
    is_arc = k not in pn          # thematic arc: steps carry their own state.k
    for i, s in enumerate(tour['steps']):
        st = s.get('state', {})
        sk = st.get('k', k)
        if is_arc and 'k' not in st:
            errs.append(f'{k} step {i+1}: arc step missing state.k')
            continue
        if sk not in pn:
            errs.append(f'{k} step {i+1}: unknown election {sk}')
            continue
        codes = codes_for(sk)
        m = st.get('mode', 'bloc')
        if m not in mode_ids:
            errs.append(f'K{k} step {i+1}: unknown mode {m}')
        c = st.get('code')
        if c and c not in codes:
            errs.append(f'{k} step {i+1}: code {c} not in K{sk} party list')
        c2 = st.get('code2')
        if c2 and c2 not in codes:
            errs.append(f'{k} step {i+1}: code2 {c2} not in K{sk} party list')
        if st.get('sub') and st['sub'] not in ('share', 'swing', 'gap'):
            errs.append(f'K{k} step {i+1}: bad sub {st["sub"]}')
        if st.get('display') and st['display'] not in ('polygons', 'bubbles', 'dorling'):
            errs.append(f'K{k} step {i+1}: bad display {st["display"]}')
        for nm in s.get('focus', []):
            if nm not in geo_names:
                errs.append(f'K{k} step {i+1}: focus locality not in geo: "{nm}"')
        for lang in ('he', 'en'):
            if not s['title'].get(lang) or not s['text'].get(lang):
                errs.append(f'K{k} step {i+1}: missing {lang} text')

out = errs if errs else ['ALL OK — tours: ' + ', '.join(
    f'K{k} ({len(t["steps"])} steps)' for k, t in tours['tours'].items())]
open('analysis/tour_validate_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('errors:', len(errs))
