# -*- coding: utf-8 -*-
"""Map layer: estimated household-religiosity MIX per 2022 statistical area.

CBS publishes only the DOMINANT household-datiyut label per SA. This builder
estimates the full mix (haredi/dati/masorti/hiloni) from vote-free census
covariates — same NNLS-anchor method as analysis/ml/mrp_v2.py (fertility,
median age, academic %, married-18-34 %, household size, %0-19; anchors from
label-homogeneous SAs, haredi/hiloni sharpened by a fertility split). These
are MODEL ESTIMATES, not CBS data — the map labels them as such.

Validation context: this frame lifted MRP SA-level vote prediction from
R2 0.375 to 0.645 (see mrp_v2_report.txt) — the mixes carry real signal, but
individual SAs can be off by 10-20 points.

NOTE 2026-07-09: the per-SA breakdown display was REMOVED from the map as too
noisy (user call); the map instead tags the common-space axis score with
bands calibrated on the label medians. data/relmix.json remains as the
research artifact behind mrp_v2 and the findings write-up.

Run from repo root: python -X utf8 analysis/ml/build_relmix.py
-> data/relmix.json  {"semel|sa": [haredi, dati, masorti, hiloni] in %}
"""
import json
import os

import numpy as np
import pandas as pd
from scipy.optimize import nnls

AN = os.path.join('analysis')
DAT_MAP = {'חילוני': 'hiloni', 'מסורתי': 'masorti',
           'דתי/ דתי מאוד': 'dati', 'חרדי': 'haredi'}
ORDER = ['haredi', 'dati', 'masorti', 'hiloni']
MIX_COVS = ['ChldBorn_avg', 'age_median', 'AcadmCert_pcnt',
            'married18_34_pcnt', 'size_avg', 'age0_19_pcnt']
LABELS = {
    'haredi':  {'he': 'חרדי', 'en': 'Haredi', 'color': '#6d28d9'},
    'dati':    {'he': 'דתי', 'en': 'Religious', 'color': '#16a34a'},
    'masorti': {'he': 'מסורתי', 'en': 'Traditional', 'color': '#fbbf24'},
    'hiloni':  {'he': 'חילוני', 'en': 'Secular', 'color': '#38bdf8'},
}


def main():
    cen = pd.read_csv(os.path.join(AN, 'statarea_inputs',
                                   'cbs_census_2022_statarea.csv'))
    cen = cen[cen.StatArea.notna() & cen.LocalityCode.notna()].copy()
    cen['key'] = (cen.LocalityCode.astype(int).astype(str) + '|' +
                  cen.StatArea.astype(int).astype(str))
    jc = cen[cen.ReligionHeb == 'יהודים'].copy()
    jc['tier'] = jc.hh_MidatDatiyut.map(DAT_MAP)   # NB: CSV columns swapped
    Z = jc[MIX_COVS].astype(float)
    Z = Z.fillna(Z.median())
    mu, sd = Z.mean(), Z.std().replace(0, 1)
    Zs = (Z - mu) / sd

    anchors = {}
    for t, lbl in (('haredi', 'חרדי'), ('dati', 'דתי/ דתי מאוד'),
                   ('masorti', 'מסורתי'), ('hiloni', 'חילוני')):
        sub = Zs[jc.tier == DAT_MAP[lbl]]
        fert = Z.loc[sub.index, 'ChldBorn_avg']
        if t == 'haredi':
            sub = sub[fert >= fert.median()]
        if t == 'hiloni':
            sub = sub[fert <= fert.median()]
        anchors[t] = sub.mean().to_numpy()
    Aaug = np.vstack([np.column_stack([anchors[t] for t in ORDER]),
                      10 * np.ones(len(ORDER))])

    out = {'meta': {
        'built': '2026-07-09',
        'what': ('ESTIMATED household-religiosity mix per 2022 SA (Jewish-'
                 'majority SAs), NNLS on vote-free census covariates — CBS '
                 'publishes only the dominant category; these are model '
                 'estimates (analysis/ml/build_relmix.py, method of mrp_v2)'),
        'order': ORDER, 'labels': LABELS,
    }}
    m = {}
    for key, zrow in zip(jc.key, Zs.to_numpy()):
        b = np.concatenate([zrow, [10.0]])
        w_, _ = nnls(Aaug, b)
        s = w_.sum()
        w_ = w_ / s if s > 0 else np.full(len(ORDER), 1 / len(ORDER))
        pct = np.round(100 * w_).astype(int)
        pct[int(np.argmax(pct))] += 100 - pct.sum()   # force sum=100
        m[key] = pct.tolist()
    out['mix'] = m
    path = os.path.join('data', 'relmix.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    arr = np.array(list(m.values()))
    print('wrote %s: %d SAs (%.0f KB); national mean mix h/d/m/hi = %s'
          % (path, len(m), os.path.getsize(path) / 1024,
             np.round(arr.mean(0), 1).tolist()))


if __name__ == '__main__':
    main()
