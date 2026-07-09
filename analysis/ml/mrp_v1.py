# -*- coding: utf-8 -*-
"""ML project 6, v1: MRP-lite for K25 — individual-level INES model,
poststratified to statistical areas, validated against ACTUAL SA results.

Design (v1, every simplification disclosed in the report):
  MODEL  weighted logistic regression on INES-2022 Jewish voters:
         P(right-haredi | religiosity tier, academic, age band) + rel x acad
         interactions; the Arab sector is one weighted cell (Druze villages
         are a KNOWN failure of this pooling — reported separately).
  FRAME  per Jewish SA: religiosity is taken DETERMINISTICALLY from the SA's
         dominant-household-datiyut census label (share columns are not
         published at SA level); acad x age(18-64/65+) joint approximated by
         independence from the SA's two published margins.
  P      rh_hat(SA) = sum over cells of w_cell * p_model(cell)
  VALID  vs actual K25 right-haredi share from the vote tensor —
         the validation almost no MRP application can run.

Run from repo root: python -X utf8 analysis/ml/mrp_v1.py   (~1 min)
Outputs: analysis/ml/out/mrp_v1_{report.txt,sa.csv}
"""
import importlib.util
import json
import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

HERE = os.path.dirname(os.path.abspath(__file__))
AN = os.path.dirname(HERE)
OUT = os.path.join(HERE, 'out')
BLOC_RH = ['likud', 'shas', 'utj', 'natrel', 'far_right']

spec = importlib.util.spec_from_file_location(
    'bim', os.path.join(AN, 'build_ines_micro.py'))
bim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bim)

DAT_MAP = {'חילוני': 'hiloni', 'מסורתי': 'masorti',
           'דתי/ דתי מאוד': 'dati', 'חרדי': 'haredi'}
ARAB_REL = {'מוסלמים', 'נוצרים', 'דרוזים'}


def main():
    rep = ['MRP v1 — K25 (INES 2022 -> SA poststratification)', '=' * 60]

    # ---- individuals ----
    cfg = bim.CFG['25']
    df, vl = bim.bst.read_wave(f"{bim.INES}/{cfg['path']}", categoricals=True)
    votes = bim.bst.map_series(df[cfg['vote']], f"2022:{cfg['vote']}", '2022',
                               value_labels=None)
    voters = votes.isin(bim.BLOCS)
    wvar = bim.bst.pick_weight(df, voters, cfg['weights'])
    w = pd.to_numeric(df[wvar], errors='coerce').fillna(0) if wvar \
        else pd.Series(1.0, index=df.index)
    jm, sector_note = bim.jewish_mask(df, vl, cfg['sector'], True)
    rel, _ = bim.rel_tier(df, vl, cfg['rel'], True)
    acad, _ = bim.edu_binary(df, vl, cfg['edu'], True)
    age = pd.to_numeric(df[cfg['age'][1]], errors='coerce')
    age65 = age.map(lambda v: None if pd.isna(v) or v < 18 else bool(v >= 65))
    rh = votes.isin(bim.RH)

    J = voters & jm & rel.notna() & acad.notna() & age65.notna()
    rep.append('INES 2022: %d voters (weight %s); Jewish modeled n=%d; '
               'rel tiers: %s' % (int(voters.sum()), wvar or 'none',
                                  int(J.sum()),
                                  sorted(rel[J].unique().tolist())))

    tiers = sorted(rel[J].unique().tolist())
    X = np.column_stack([
        *[(rel[J] == t).astype(float) for t in tiers[1:]],
        acad[J].astype(float),
        age65[J].astype(float),
        *[((rel[J] == t) & acad[J].astype(bool)).astype(float)
          for t in tiers[1:]],
    ])
    m = LogisticRegression(C=1.0, max_iter=2000)
    m.fit(X, rh[J].astype(int), sample_weight=w[J])

    def cell_p(tier, ac, a65):
        x = np.zeros(X.shape[1])
        nt = len(tiers) - 1
        if tier != tiers[0]:
            x[tiers[1:].index(tier)] = 1
        x[nt] = ac
        x[nt + 1] = a65
        if tier != tiers[0] and ac:
            x[nt + 2 + tiers[1:].index(tier)] = 1
        return float(m.predict_proba([x])[0, 1])

    rep.append('\ncell P(right-haredi), model vs raw weighted cell mean:')
    for t in tiers:
        for ac in (0, 1):
            ps = [cell_p(t, ac, a) for a in (0, 1)]
            mask = J & (rel == t) & (acad == bool(ac))
            raw = 100 * float(w[mask & rh].sum()) / float(w[mask].sum()) \
                if w[mask].sum() > 0 else float('nan')
            rep.append('  %-8s acad=%d: 18-64 %5.1f%%  65+ %5.1f%%   '
                       '(raw %5.1f%%, n=%d)'
                       % (t, ac, 100 * ps[0], 100 * ps[1], raw,
                          int(mask.sum())))
    A = voters & ~jm
    p_arab = float(w[A & rh].sum()) / float(w[A].sum())
    rep.append('Arab-sector cell: rh=%.1f%% (n=%d)' % (100 * p_arab,
                                                       int(A.sum())))

    # ---- frame + poststratify ----
    cen = pd.read_csv(os.path.join(AN, 'statarea_inputs',
                                   'cbs_census_2022_statarea.csv'))
    cen = cen[cen.StatArea.notna() & cen.LocalityCode.notna()].copy()
    cen['key'] = (cen.LocalityCode.astype(int).astype(str) + '|' +
                  cen.StatArea.astype(int).astype(str))
    v25 = pd.read_csv(os.path.join(OUT, 'votes_k25.csv'))
    v25['key'] = v25.semel.astype(str) + '|' + v25.sa.astype(str)
    v25['rh'] = v25[BLOC_RH].sum(axis=1)
    dfm = v25.merge(cen, on='key', how='inner')

    rows, skipped = [], {}
    for r in dfm.itertuples():
        relig = str(r.ReligionHeb)
        a_tot = (r.age20_64_pcnt or 0) + (r.age65_pcnt or 0)
        w65 = (r.age65_pcnt / a_tot) if a_tot > 0 else 0.12
        if relig in ARAB_REL:
            rh_hat = 100 * p_arab
            kind = 'arab'
        elif relig == 'יהודים':
            # NB: the CSV's datiyut columns are swapped — hh_MidatDatiyut
            # carries the NAME strings, hh_MidatDatiyut_Name the codes
            tier = DAT_MAP.get(str(r.hh_MidatDatiyut))
            if tier is None or tier not in tiers or \
                    pd.isna(r.AcadmCert_pcnt):
                skipped[str(r.hh_MidatDatiyut)] = \
                    skipped.get(str(r.hh_MidatDatiyut), 0) + 1
                continue
            pa = r.AcadmCert_pcnt / 100
            rh_hat = 100 * sum(
                wc * cell_p(tier, ac, a65)
                for ac, wac in ((1, pa), (0, 1 - pa))
                for a65, wa in ((1, w65), (0, 1 - w65))
                for wc in [wac * wa])
            kind = 'jewish'
        else:
            skipped[relig] = skipped.get(relig, 0) + 1
            continue
        rows.append({'key': r.key, 'kind': kind, 'relig': relig,
                     'rh_hat': round(rh_hat, 2), 'rh': r.rh,
                     'valid': r.valid})
    res = pd.DataFrame(rows)
    rep.append('\nposstrat coverage: %d SAs scored; skipped: %s'
               % (len(res), skipped))

    # ---- validation ----
    def stats(d, tag):
        wv = d['valid'].to_numpy()
        y, yh = d['rh'].to_numpy(), d['rh_hat'].to_numpy()
        ybar = np.average(y, weights=wv)
        r2 = 1 - np.average((y - yh)**2, weights=wv) / \
            np.average((y - ybar)**2, weights=wv)
        mae = np.average(np.abs(y - yh), weights=wv)
        r = np.corrcoef(y, yh)[0, 1]
        rep.append('%-22s n=%4d  r=%.3f  R2=%.3f  MAE=%.1fpp'
                   % (tag, len(d), r, r2, mae))
    rep.append('\nvalidation vs ACTUAL K25 right-haredi share '
               '(valid-vote weighted):')
    stats(res, 'all scored SAs')
    stats(res[res.kind == 'jewish'], 'Jewish SAs')
    stats(res[res.relig == 'דרוזים'], 'Druze SAs (known fail)')
    stats(res[(res.kind == 'arab') & (res.relig != 'דרוזים')],
          'Arab SAs excl. Druze')

    rep.append('\ncalibration (Jewish SAs, deciles of prediction):')
    jd = res[res.kind == 'jewish'].copy()
    jd['dec'] = pd.qcut(jd.rh_hat, 10, labels=False, duplicates='drop')
    for d_, g in jd.groupby('dec'):
        rep.append('  d%d: pred %5.1f  actual %5.1f  (n=%d)'
                   % (d_, np.average(g.rh_hat, weights=g.valid),
                      np.average(g.rh, weights=g.valid), len(g)))

    rep.append('\ncontext: project-2 GBM (18 census vars, held-out cities) '
               'R2=0.885; MRP v1 uses 3 covariates + survey of ~1k — the '
               'point is individual grounding + calibrated cells, not raw '
               'predictive power. Deterministic datiyut stratum and the '
               'single Arab cell are the two v1 simplifications to lift.')
    res.to_csv(os.path.join(OUT, 'mrp_v1_sa.csv'), index=False)
    with open(os.path.join(OUT, 'mrp_v1_report.txt'), 'w',
              encoding='utf-8') as f:
        f.write('\n'.join(rep) + '\n')
    print('\n'.join(rep))


if __name__ == '__main__':
    main()
