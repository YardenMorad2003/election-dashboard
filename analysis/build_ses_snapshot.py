# -*- coding: utf-8 -*-
"""Snapshot CBS Socio-Economic Index Table 12 (statistical-area level) into
analysis/statarea_inputs/ses_statarea_{vintage}.json.

Vintages 2017/2019/2021. All three sit on the PRE-2022-census SA delineation
(96.3% code match vs statarea_2009_geo.json, only ~67% vs 2022 geo, and same
code != same polygon after the 2022 renumbering) — so these snapshots are
consumed by build_ses_crosswalk.py, never joined to 2022 keys directly.

External inputs (Downloads, not in repo):
  - "3 (3).zip"            -> T12.xlsx            (SES 2019)
  - more_socio_econ.zip    -> "more_socio_econ/3 (1).zip" -> 3/t12.xlsx (2021)
                           -> "more_socio_econ/3 (2).zip" -> t12.xls    (2017)
  - "1 (6).zip"            -> T01.xlsx  (SES 2019, ALL 255 local authorities:
    cities + local councils + regional councils as units -> fallback layer for
    map localities without SA-level SES)
  - "2 (2).zip"            -> T08.xlsx  (SES 2019, ~995 localities WITHIN
    regional councils, per-village value/rank/cluster; rank is within the
    995-village universe, NOT comparable to T01/T12 ranks) + T10.xlsx (18
    villages for which no index was computed)

Run from repo root: python -X utf8 analysis/build_ses_snapshot.py
"""
import io
import json
import os
import zipfile

import pandas as pd

DOWNLOADS = os.path.join(os.path.expanduser('~'), 'Downloads')
OUT_DIR = os.path.join('analysis', 'statarea_inputs')

# T12 layout (identical in all three vintages): data starts at row 8;
# cols 0-6 = semel, name_he, sa, pop, index value, rank, cluster;
# 14 indicators at cols 7,10,...,46 (each followed by standardized value+rank).
IND_COLS = {
    7: 'median_age',
    10: 'dependency',
    13: 'fam4plus_pct',
    16: 'school_years',
    19: 'academic_pct',
    22: 'earners_pct',
    25: 'women_noincome_pct',
    28: 'above2x_wage_pct',
    31: 'below_minwage_pct',
    34: 'income_support_pct',
    37: 'income_percap',
    40: 'vehicles_per100',
    43: 'license_fee',
    46: 'days_abroad',
}
IND_DESC = {
    'median_age': 'median age',
    'dependency': 'dependency ratio (per 100 aged 20-64)',
    'fam4plus_pct': '% families with 4+ children',
    'school_years': 'avg years of schooling, aged 25-54',
    'academic_pct': '% academic degree holders, aged 27-54',
    'earners_pct': '% with income from work, aged 25-54',
    'women_noincome_pct': '% women aged 25-54 with no income from work',
    'above2x_wage_pct': '% earners above 2x average wage',
    'below_minwage_pct': '% earners below minimum wage',
    'income_support_pct': '% income-support/supplement recipients',
    'income_percap': 'avg monthly income per capita (NIS)',
    'vehicles_per100': 'vehicles owned per 100 residents aged 18+',
    'license_fee': 'avg vehicle licence fee (NIS)',
    'days_abroad': 'avg days abroad',
}


def num(v, nd=2):
    """Numeric cell or None ('..' = CBS not-for-publication)."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f != f:  # NaN
        return None
    return round(f, nd)


def parse_t12(xls_bytes, vintage):
    df = pd.read_excel(io.BytesIO(xls_bytes), header=None)
    areas = []
    for _, r in df.iterrows():
        try:
            semel = int(r[0])
            sa = int(r[2])
        except (TypeError, ValueError):
            continue
        if semel <= 0 or not (0 < sa < 100000):
            continue
        rank = num(r[5], 0)
        cluster = num(r[6], 0)
        area = {
            'semel': semel,
            'sa': sa,
            'name': str(r[1]).replace('*', '').strip(),
            'pop': num(r[3], 1),
            'value': num(r[4], 4),
            'rank': int(rank) if rank is not None else None,
            'cluster': int(cluster) if cluster is not None else None,
            'ind': {k: num(r[c], 2) for c, k in IND_COLS.items()},
        }
        areas.append(area)
    # national reference row sits above the data (col0 is a label, col1 text)
    national = None
    for _, r in df.iterrows():
        if str(r[49]).strip() == 'NATIONWIDE VALUE':
            national = {k: num(r[c], 2) for c, k in IND_COLS.items()}
            national['pop'] = num(r[3], 0)
            break
    return areas, national


def parse_t01(xls_bytes):
    """Locality-level Table 1: col0 = municipal status (0 city, 99 local
    council, N = regional-council number with semel 10000+N), col1 = semel,
    then name/pop/value/rank/cluster + the same indicator triplets."""
    df = pd.read_excel(io.BytesIO(xls_bytes), header=None)
    auths = []
    for _, r in df.iterrows():
        try:
            status = int(r[0])
            semel = int(r[1])
        except (TypeError, ValueError):
            continue
        if semel <= 0 or not isinstance(r[2], str):
            continue
        rank = num(r[5], 0)
        cluster = num(r[6], 0)
        auths.append({
            'semel': semel,
            'status': ('city' if status == 0 else
                       'local_council' if status == 99 else 'regional_council'),
            'name': str(r[2]).replace('*', '').strip(),
            'pop': num(r[3], 1),
            'value': num(r[4], 4),
            'rank': int(rank) if rank is not None else None,
            'cluster': int(cluster) if cluster is not None else None,
            'ind': {k: num(r[c], 2) for c, k in IND_COLS.items()},
        })
    return auths


def parse_t08(xls_bytes):
    """Villages within regional councils (Table 8, alphabetical): value/rank/
    cluster only — no component indicators at this level."""
    df = pd.read_excel(io.BytesIO(xls_bytes), header=None)
    villages = []
    for _, r in df.iterrows():
        try:
            rc = int(r[0])
            semel = int(r[5])
        except (TypeError, ValueError):
            continue
        if semel <= 0 or not isinstance(r[6], str):
            continue
        rank = num(r[11], 0)
        cl19 = num(r[12], 0)
        cl17 = num(r[13], 0)
        villages.append({
            'semel': semel,
            'name': str(r[6]).replace('*', '').strip(),
            'rc_semel': 10000 + rc,
            'rc_name': str(r[1]).strip(),
            'type_code': num(r[8], 0),
            'pop': num(r[9], 1),
            'value': num(r[10], 4),
            'rank': int(rank) if rank is not None else None,
            'cluster': int(cl19) if cl19 is not None else None,
            'cluster_2017': int(cl17) if cl17 is not None else None,
        })
    return villages


def parse_t10(xls_bytes):
    df = pd.read_excel(io.BytesIO(xls_bytes), header=None)
    out = []
    for _, r in df.iterrows():
        try:
            semel = int(r[3])
        except (TypeError, ValueError):
            continue
        if semel > 0 and isinstance(r[4], str):
            out.append({'semel': semel, 'name': str(r[4]).strip()})
    return out


def main():
    sources = {}
    p2019 = os.path.join(DOWNLOADS, '3 (3).zip')
    with zipfile.ZipFile(p2019) as z:
        sources[2019] = (z.read('T12.xlsx'), '3 (3).zip :: T12.xlsx')
    pmore = os.path.join(DOWNLOADS, 'more_socio_econ.zip')
    with zipfile.ZipFile(pmore) as z:
        with zipfile.ZipFile(io.BytesIO(z.read('more_socio_econ/3 (1).zip'))) as zi:
            sources[2021] = (zi.read('3/t12.xlsx'),
                             'more_socio_econ.zip :: 3 (1).zip :: 3/t12.xlsx')
        with zipfile.ZipFile(io.BytesIO(z.read('more_socio_econ/3 (2).zip'))) as zi:
            sources[2017] = (zi.read('t12.xls'),
                             'more_socio_econ.zip :: 3 (2).zip :: t12.xls')

    for vintage, (raw, src) in sorted(sources.items()):
        areas, national = parse_t12(raw, vintage)
        semels = {a['semel'] for a in areas}
        out = {
            'meta': {
                'vintage': vintage,
                'source': ('CBS Characterization and Classification of '
                           'Statistical Areas by Socio-Economic Level %d, '
                           'Table 12 (%s)' % (vintage, src)),
                'snapshotted': '2026-07-09',
                'n_areas': len(areas),
                'n_localities': len(semels),
                'delineation': 'pre-2022-census statistical areas',
                'indicators': IND_DESC,
                'notes': 'value/rank/cluster per CBS; None = suppressed (..)',
            },
            'national': national,
            'areas': areas,
        }
        path = os.path.join(OUT_DIR, 'ses_statarea_%d.json' % vintage)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
        n_null = sum(1 for a in areas if a['value'] is None)
        print('%d: %d SAs, %d localities, %d suppressed values -> %s (%.1f KB)'
              % (vintage, len(areas), len(semels), n_null, path,
                 os.path.getsize(path) / 1024))

    # locality-level fallback layer (2019 only for now)
    p_loc = os.path.join(DOWNLOADS, '1 (6).zip')
    p_vil = os.path.join(DOWNLOADS, '2 (2).zip')
    if os.path.exists(p_loc):
        with zipfile.ZipFile(p_loc) as z:
            auths = parse_t01(z.read('T01.xlsx'))
        villages, excluded = [], []
        if os.path.exists(p_vil):
            with zipfile.ZipFile(p_vil) as z:
                villages = parse_t08(z.read('T08.xlsx'))
                excluded = parse_t10(z.read('T10.xlsx'))
        out = {
            'meta': {
                'vintage': 2019,
                'source': ('CBS Characterization and Classification of Local'
                           ' Authorities by Socio-Economic Level 2019:'
                           ' Table 1 (1 (6).zip :: T01.xlsx, 255 authorities'
                           ' incl. regional councils as units) + Table 8'
                           ' (2 (2).zip :: T08.xlsx, localities within'
                           ' regional councils) + Table 10 (villages with no'
                           ' computed index)'),
                'snapshotted': '2026-07-09',
                'n_authorities': len(auths),
                'n_villages': len(villages),
                'indicators': IND_DESC,
                'notes': ('authority/village ranks are within separate'
                          ' universes (255 authorities / ~995 villages) and'
                          ' NOT comparable to T12 SA ranks; village rows have'
                          ' no component indicators'),
            },
            'authorities': auths,
            'villages': villages,
            'no_index': excluded,
        }
        path = os.path.join(OUT_DIR, 'ses_locality_2019.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
        by_status = {}
        for a in auths:
            by_status[a['status']] = by_status.get(a['status'], 0) + 1
        print('2019 localities: %d authorities %s + %d villages'
              ' (%d no-index) -> %s (%.1f KB)'
              % (len(auths), by_status, len(villages), len(excluded), path,
                 os.path.getsize(path) / 1024))
    else:
        print('1 (6).zip not found - skipping locality-level snapshot')


if __name__ == '__main__':
    main()
