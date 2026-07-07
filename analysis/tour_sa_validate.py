# Validate statarea_tours.json: years/modes/toggles valid, focus semel+sa exist in that year's data
import json, re

tours = json.load(open('data/statarea_tours.json', encoding='utf-8'))
page = open('statarea_map.html', encoding='utf-8').read()

YEARS_DATA = {'2022': 'statarea_2022.json', '2021': 'statarea_k24.json', '2020': 'statarea_k23.json',
              '2019b': 'statarea_k22.json', '2019a': 'statarea_k21.json', '2015': 'statarea_k20.json',
              '2013': 'statarea_k19.json', '2009': 'statarea_2009.json', '2006': 'statarea_k17.json',
              '2003': 'statarea_k16.json'}
D22 = ['datiyut','acad','wage','age','aliya','origin']
D08 = ['religion','acad','ses','age','aliya','origin']
DEMO = {'2022': D22, '2021': D22, '2020': D22, '2019b': D22, '2019a': D22,
        '2015': D08, '2013': D08, '2009': D08,
        '2006': ['religion','age','aliya','origin','oc'], '2003': ['religion','age','aliya','origin','oc']}
VOTE_MODES = ['bloc', 'winner', 'party', 'turnout']
EST_YEARS = {'2022','2021','2020','2019b','2019a'}

cache = {}
def areas(year):
    if year not in cache:
        cache[year] = json.load(open('data/' + YEARS_DATA[year], encoding='utf-8'))['areas']
    return cache[year]

errs = []
for tk, tour in tours['tours'].items():
    for i, s in enumerate(tour['steps']):
        st = s.get('state', {})
        y = st.get('year')
        if y not in YEARS_DATA:
            errs.append(f'{tk} step {i+1}: bad year {y}'); continue
        m = st.get('mode', 'bloc')
        if m not in VOTE_MODES and m not in DEMO[y]:
            errs.append(f'{tk} step {i+1}: mode {m} unavailable in {y}')
        if m == 'turnout' and y == '2006':
            errs.append(f'{tk} step {i+1}: turnout hidden in 2006')
        if st.get('est') and y not in EST_YEARS:
            errs.append(f'{tk} step {i+1}: est unavailable in {y}')
        if st.get('code'):
            # party codes: check exists in that year's data (any area)
            found = any(st['code'] in (r.get('parties') or {}) for r in areas(y).values())
            if not found: errs.append(f'{tk} step {i+1}: code {st["code"]} not found in {y} data')
        for f in s.get('focus', []):
            recs = [r for r in areas(y).values() if r.get('semel') == f['semel']]
            if not recs:
                errs.append(f'{tk} step {i+1}: semel {f["semel"]} not in {y} data'); continue
            for sa_num in f.get('sa', []):
                if not any(r.get('sa') == sa_num for r in recs):
                    errs.append(f'{tk} step {i+1}: sa {sa_num} not in semel {f["semel"]} ({y})')
        for lang in ('he', 'en'):
            if not s['title'].get(lang) or not s['text'].get(lang):
                errs.append(f'{tk} step {i+1}: missing {lang}')

out = errs if errs else ['ALL OK — ' + ', '.join(f'{k} ({len(t["steps"])} steps)' for k, t in tours['tours'].items())]
open('analysis/tour_sa_validate_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('errors:', len(errs))
