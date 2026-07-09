# -*- coding: utf-8 -*-
"""ML Phase 0a: CURATED party-lineage table, K13-K25.

Hand-authored against two evidence sources: the transfer-matrix vote-origin
compositions (analysis/ml/out/lineage_evidence.json) and party history.
Voter-flow chaining alone is WRONG for lineages (it chains Labor->Kadima->
Yesh Atid because voters flowed that way) — lineage here means the party
ORGANIZATION/stream, with mergers assigned to the dominant partner and every
non-obvious call carrying a note.

The buckets are the fixed basis for the cross-era PCA common space (project 1)
and segment transitions (project 3). Per-era analyses use raw parties and are
unaffected by the coarseness here.

Keying is (knesset, ballot code) — NEVER by letter alone (letters are reused
across unrelated parties: כן = ישראל בעלייה -> קדימה -> כחול לבן -> ממלכתי).

Run from repo root to validate + emit:
  python -X utf8 analysis/ml/lineage_table.py
-> analysis/ml/out/party_lineages.json
"""
import json
import os

LINEAGE_LABELS = {
    'likud':      {'he': 'הליכוד', 'en': 'Likud'},
    'labor':      {'he': 'העבודה וגלגוליה', 'en': 'Labor & successors'},
    'meretz':     {'he': 'מרצ', 'en': 'Meretz'},
    'shas':       {'he': 'ש"ס', 'en': 'Shas'},
    'utj':        {'he': 'יהדות התורה', 'en': 'United Torah Judaism'},
    'natrel':     {'he': 'הציונות הדתית (מפד"ל→ימינה→צה"ד)',
                   'en': 'Religious Zionism (NRP lineage)'},
    'far_right':  {'he': 'ימין רדיקלי/חילוני-לאומי', 'en': 'Far/nationalist right'},
    'beiteinu':   {'he': 'ישראל ביתנו', 'en': 'Yisrael Beiteinu'},
    'baaliyah':   {'he': 'ישראל בעלייה', 'en': 'Yisrael BaAliyah'},
    'center':     {'he': 'זרם המרכז', 'en': 'Center stream'},
    'opp_right':  {'he': 'ימין אופוזיציוני (בנט/סער)',
                   'en': 'Opposition right (Bennett/Saar)'},
    'arab':       {'he': 'המפלגות הערביות', 'en': 'Arab parties'},
    'other':      {'he': 'אחר', 'en': 'Other'},
}

# (knesset, code) -> lineage.  A '#' comment = judgment call.
TABLE = {
    # ---------------- K13 (1992) ----------------
    ('13', 'אמת'): 'labor',
    ('13', 'מחל'): 'likud',
    ('13', 'מרצ'): 'meretz',
    ('13', 'ץ'):  'far_right',    # צומת — secular-nationalist right
    ('13', 'ב'):  'natrel',       # מפד"ל
    ('13', 'שס'): 'shas',
    ('13', 'ג'):  'utj',
    ('13', 'ו'):  'arab',         # חד"ש
    ('13', 'ט'):  'far_right',    # מולדת
    ('13', 'ע'):  'arab',         # מד"ע
    ('13', 'ת'):  'far_right',    # התחיה
    ('13', 'פ'):  'arab',         # הרשימה המתקדמת לשלום (Arab-Jewish left, mostly Arab electorate)
    ('13', 'קן'): 'other',        # המפלגה הליברלית החדשה
    # ---------------- K14 (1996) ----------------
    ('14', 'אמת'): 'labor',
    ('14', 'מחל'): 'likud',       # ran as ליכוד-גשר-צומת; dominant partner Likud
    ('14', 'שס'): 'shas',
    ('14', 'ב'):  'natrel',
    ('14', 'מרץ'): 'meretz',
    ('14', 'כן'): 'baaliyah',     # new: voters ~49% ex-Likud / 44% ex-Labor (olim wave)
    ('14', 'ו'):  'arab',         # חד"ש-בל"ד
    ('14', 'ג'):  'utj',
    ('14', 'ע'):  'arab',         # מד"ע-רע"מ
    ('14', 'הד'): 'center',       # הדרך השלישית
    ('14', 'ט'):  'far_right',    # מולדת
    # ---------------- K15 (1999) ----------------
    ('15', 'אמת'): 'labor',       # ישראל אחת (עבודה+גשר+מימד); dominant Labor
    ('15', 'שס'): 'shas',
    ('15', 'מחל'): 'likud',
    ('15', 'מרצ'): 'meretz',
    ('15', 'יש'): 'center',       # שינוי
    ('15', 'כן'): 'baaliyah',
    ('15', 'פה'): 'center',       # מפלגת המרכז
    ('15', 'ב'):  'natrel',
    ('15', 'ג'):  'utj',
    ('15', 'ל'):  'beiteinu',     # new: voters ~50% ex-baaliyah + 46% ex-Likud
    ('15', 'עם'): 'arab',         # רע"מ
    ('15', 'ו'):  'arab',         # חד"ש
    ('15', 'ד'):  'arab',         # בל"ד
    ('15', 'ם'):  'labor',        # עם אחד (Peretz/Histadrut; merged back into Labor 2004)
    ('15', 'יט'): 'far_right',    # האיחוד הלאומי (מולדת+תקומה+חרות)
    ('15', 'הד'): 'center',
    # ---------------- K16 (2003) ----------------
    ('16', 'מחל'): 'likud',
    ('16', 'יש'): 'center',       # שינוי
    ('16', 'אמת'): 'labor',
    ('16', 'שס'): 'shas',
    ('16', 'ל'):  'beiteinu',     # ישראל ביתנו-האיחוד הלאומי joint run; assigned to YB (led it)
    ('16', 'מרצ'): 'meretz',
    ('16', 'ם'):  'labor',        # עם אחד
    ('16', 'ג'):  'utj',
    ('16', 'ו'):  'arab',         # חד"ש-תע"ל
    ('16', 'ב'):  'natrel',
    ('16', 'עם'): 'arab',
    ('16', 'ד'):  'arab',
    ('16', 'כן'): 'baaliyah',     # last run; merged into Likud after
    ('16', 'נץ'): 'far_right',    # חרות (Marzel)
    ('16', 'צף'): 'arab',         # ברית לאומית מתקדמת
    # ---------------- K17 (2006) ----------------
    ('17', 'מחל'): 'likud',
    ('17', 'ל'):  'beiteinu',
    ('17', 'טב'): 'natrel',       # איחוד לאומי-מפדל merger; assigned to NRP mainline
    ('17', 'שס'): 'shas',
    ('17', 'ג'):  'utj',
    ('17', 'כן'): 'center',       # קדימה — new party, founded by Likud+Labor defectors -> center stream
    ('17', 'זך'): 'center',       # גיל pensioners — protest-center (voters 51% ex-Labor; site bloc=center)
    ('17', 'אמת'): 'labor',
    ('17', 'מרצ'): 'meretz',
    ('17', 'עם'): 'arab',
    ('17', 'ו'):  'arab',
    ('17', 'ד'):  'arab',
    # ---------------- K18 (2009) ----------------
    ('18', 'כן'): 'center',       # קדימה
    ('18', 'מחל'): 'likud',
    ('18', 'ל'):  'beiteinu',
    ('18', 'אמת'): 'labor',
    ('18', 'שס'): 'shas',
    ('18', 'ג'):  'utj',
    ('18', 'ט'):  'far_right',    # האיחוד הלאומי (ran separately from הבית היהודי)
    ('18', 'ו'):  'arab',
    ('18', 'עם'): 'arab',
    ('18', 'ד'):  'arab',
    ('18', 'ב'):  'natrel',       # הבית היהודי (מפד"ל rebrand)
    ('18', 'מרצ'): 'meretz',
    ('18', 'זך'): 'center',       # גמלאים
    ('18', 'ה'):  'other',        # הירוקים-מימד
    # ---------------- K19 (2013) ----------------
    ('19', 'מחל'): 'likud',       # הליכוד-ישראל ביתנו JOINT; assigned Likud (beiteinu absent K19)
    ('19', 'פה'): 'center',       # יש עתיד (new)
    ('19', 'אמת'): 'labor',
    ('19', 'טב'): 'natrel',       # הבית היהודי (Bennett; absorbed האיחוד הלאומי)
    ('19', 'שס'): 'shas',
    ('19', 'ג'):  'utj',
    ('19', 'צפ'): 'labor',        # התנועה — USER RULING 2026-07-09: center-left,
                                  # categorized with the left; merged into המחנה הציוני K20
    ('19', 'מרץ'): 'meretz',
    ('19', 'ו'):  'arab',
    ('19', 'עם'): 'arab',
    ('19', 'ד'):  'arab',
    ('19', 'כן'): 'center',       # קדימה (residual)
    ('19', 'נץ'): 'far_right',    # עוצמה לישראל
    # ---------------- K20 (2015) ----------------
    ('20', 'מחל'): 'likud',
    ('20', 'אמת'): 'labor',       # המחנה הציוני (עבודה+התנועה); dominant Labor
    ('20', 'ודעם'): 'arab',       # הרשימה המשותפת
    ('20', 'פה'): 'center',
    ('20', 'כ'):  'center',       # כולנו (Kahlon)
    ('20', 'טב'): 'natrel',
    ('20', 'שס'): 'shas',
    ('20', 'ג'):  'utj',
    ('20', 'ל'):  'beiteinu',
    ('20', 'מרצ'): 'meretz',
    ('20', 'קץ'): 'far_right',    # יחד (Yishai Shas-splinter + Otzma) — campaign ran hard-right
    # ---------------- K21 (2019a) ----------------
    ('21', 'מחל'): 'likud',
    ('21', 'פה'): 'center',       # כחול לבן (יש עתיד+חוסן+תל"ם merger)
    ('21', 'ום'): 'arab',
    ('21', 'דעם'): 'arab',
    ('21', 'שס'): 'shas',
    ('21', 'ג'):  'utj',
    ('21', 'ל'):  'beiteinu',
    ('21', 'טב'): 'natrel',       # איחוד מפלגות הימין (הבית היהודי+איחוד+עוצמה)
    ('21', 'אמת'): 'labor',
    ('21', 'מרצ'): 'meretz',
    ('21', 'נ'):  'natrel',       # הימין החדש (Bennett split; same stream, voters 96% ex-בית יהודי)
    ('21', 'כ'):  'center',       # כולנו
    ('21', 'נר'): 'center',       # גשר (Orly Levy)
    ('21', 'ז'):  'far_right',    # זהות (Feiglin)
    # ---------------- K22 (2019b) ----------------
    ('22', 'מחל'): 'likud',
    ('22', 'פה'): 'center',
    ('22', 'ודעם'): 'arab',
    ('22', 'שס'): 'shas',
    ('22', 'ג'):  'utj',
    ('22', 'ל'):  'beiteinu',
    ('22', 'טב'): 'natrel',       # ימינה (ימין חדש+איחוד מפלגות הימין)
    ('22', 'אמת'): 'labor',       # העבודה-גשר
    ('22', 'מרצ'): 'meretz',      # המחנה הדמוקרטי (מרצ+דמוקרטית ישראל)
    ('22', 'כף'): 'far_right',    # עוצמה יהודית standalone
    # ---------------- K23 (2020) ----------------
    ('23', 'מחל'): 'likud',
    ('23', 'פה'): 'center',
    ('23', 'ודעם'): 'arab',
    ('23', 'שס'): 'shas',
    ('23', 'ג'):  'utj',
    ('23', 'ל'):  'beiteinu',
    ('23', 'טב'): 'natrel',       # ימינה
    ('23', 'אמת'): 'labor',       # העבודה-גשר-מרצ JOINT; assigned Labor (meretz absent K23)
    ('23', 'נץ'): 'far_right',    # עוצמה יהודית
    # ---------------- K24 (2021) ----------------
    ('24', 'מחל'): 'likud',
    ('24', 'ט'):  'natrel',       # הציונות הדתית (Smotrich + Otzma on list)
    ('24', 'ת'):  'opp_right',    # תקווה חדשה — USER RULING 2026-07-09: opposition right
    ('24', 'ב'):  'opp_right',    # ימינה K24 — USER RULING 2026-07-09: not clear-cut
                                  # (liberal religious Zionism, joined the change govt);
                                  # sits with תקווה חדשה in the K24-only opp_right bucket
    ('24', 'שס'): 'shas',
    ('24', 'ג'):  'utj',
    ('24', 'פה'): 'center',       # יש עתיד
    ('24', 'כן'): 'center',       # כחול לבן (Gantz)
    ('24', 'ל'):  'beiteinu',
    ('24', 'אמת'): 'labor',
    ('24', 'מרצ'): 'meretz',
    ('24', 'עם'): 'arab',         # רע"מ standalone
    ('24', 'ודעם'): 'arab',
    # ---------------- K25 (2022) ----------------
    ('25', 'מחל'): 'likud',
    ('25', 'ט'):  'natrel',       # הציונות הדתית+עוצמה יהודית joint
    ('25', 'ל'):  'beiteinu',
    ('25', 'ב'):  'natrel',       # הבית היהודי (Shaked's ימינה rebrand)
    ('25', 'שס'): 'shas',
    ('25', 'ג'):  'utj',
    ('25', 'פה'): 'center',
    ('25', 'כן'): 'center',       # המחנה הממלכתי (כחול לבן+תקווה חדשה)
    ('25', 'אמת'): 'labor',
    ('25', 'מרצ'): 'meretz',
    ('25', 'עם'): 'arab',
    ('25', 'ד'):  'arab',
    ('25', 'ום'): 'arab',
}

# adjudicated 2026-07-09 (user rulings); kept for provenance
RESOLVED = [
    ('24', 'ת', "USER: opposition right -> new opp_right bucket (with ימינה K24)."),
    ('24', 'ב', "USER: not clear-cut (liberal relig. Zionism, joined change "
                "govt) -> opp_right bucket, not natrel/center."),
    ('20', 'קץ', "USER: far_right confirmed (Yishai+Otzma joint list)."),
    ('19', 'צפ', "USER: center-left, categorized left -> labor bucket."),
    ('15', 'ם', "default kept: עם אחד -> labor (merged back 2004)."),
    ('17', 'זך', "default kept: גיל pensioners -> center."),
    ('16', 'ל', "convention: ישראל ביתנו-האיחוד הלאומי joint -> beiteinu."),
    ('19', 'מחל', "convention: הליכוד-ישראל ביתנו joint -> likud; beiteinu "
                  "has no K19 column."),
    ('23', 'אמת', "convention: העבודה-גשר-מרצ joint -> labor; meretz has no "
                  "K23 column."),
    ('20', 'אמת', "convention: המחנה הציוני (עבודה+התנועה) -> labor."),
]
FLAGGED = []   # all adjudicated


def main():
    import importlib.util
    pn = json.load(open(os.path.join('data', 'parties_national.json'),
                        encoding='utf-8'))
    # coverage validation: every party_list entry must be mapped, no extras
    missing, extra = [], dict(TABLE)
    for k, v in pn.items():
        for p in v['party_list']:
            key = (k, p['code'])
            if key not in TABLE:
                missing.append((k, p['code'], p['name']))
            else:
                extra.pop(key, None)
    if missing:
        raise SystemExit('UNMAPPED parties: %s' % missing)
    if extra:
        raise SystemExit('TABLE keys not in party lists: %s' % list(extra))

    out_dir = os.path.join('analysis', 'ml', 'out')
    os.makedirs(out_dir, exist_ok=True)
    name_of = {(k, p['code']): p['name'] for k, v in pn.items()
               for p in v['party_list']}
    out = {
        'meta': {
            'built': '2026-07-09',
            'method': ('hand-curated against transfer-matrix vote-origin '
                       'evidence (lineage_evidence.json); mergers -> dominant '
                       'partner; keyed by (knesset, ballot code)'),
            'status': 'CURATED v2 — all calls adjudicated 2026-07-09',
        },
        'labels': LINEAGE_LABELS,
        'map': {'%s|%s' % k: v for k, v in TABLE.items()},
        'names': {'%s|%s' % k: name_of[k] for k in TABLE},
        'flagged': [{'k': k, 'code': c, 'note': n} for k, c, n in FLAGGED],
        'resolved': [{'k': k, 'code': c, 'note': n} for k, c, n in RESOLVED],
    }
    path = os.path.join(out_dir, 'party_lineages.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    from collections import Counter
    cnt = Counter(TABLE.values())
    print('coverage OK: %d party-elections mapped, %d lineages, %d flagged'
          % (len(TABLE), len(cnt), len(FLAGGED)))
    print('bucket sizes:', dict(cnt.most_common()))
    print('->', path)


if __name__ == '__main__':
    main()
