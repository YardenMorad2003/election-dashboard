# -*- coding: utf-8 -*-
"""One-time K13 data fix (2026-07-02, FINAL): ONE 1992 extraction row had its
מרצ↔מחל values swapped — ניר יצחק (semel 402).

  extraction file said: מחל 267 (82.9%), מרצ 2 (0.6%)
  corrected to:         מחל 2 (0.62%),  מרצ 267 (82.92%)

Evidence: HaShomer-Hatzai r kibbutz, votes 0.3-4.4% right in all 12 other
elections; its official K14 (1996) result is מרץ 74.9% / מחל 0.0%.

HISTORY / LESSON. A K14-based stickiness heuristic (does the swapped reading
fit the locality's own official 1996 מרץ/מחל shares better by >20pp?) flagged
three more rows: בית אורן, שדה ניצן, דאלית אל-כרמל. They were swapped too,
then REVERTED after the user checked the official 1992 results file: all three
were correct as extracted — genuinely large 1992→1996 swings (e.g. Beit Oren
45%→13% Likud around its 1990s collapse/turnover). Cross-election consistency
flags candidates; only the primary source confirms.

Also adjudicated, no change needed:
  - עמיקם, מג'דל שמס, חורפיש, נעורים, אתגר — genuine (K14 matches K13).
  - כפר חב"ד, מבוא מודיעים — RH understated by construction: real 1992 votes
    for sub-threshold lists (גאולת ישראל etc.) live in the excluded 'אחר'.
  - טפחות (n=52) — אמת 75%; user-verified GENUINE against the official 1992 file.
  - Traps: K14's Meretz code is מרץ (final tsadi), NOT מרצ — a naive comparison
    against מרצ returns 0 for every locality and falsely flags 32 rows.
    election_map_geo spells דאלית אל כרמל WITHOUT the hyphen.

DO NOT RE-RUN — the swap below is not idempotent. Kept for the record; the fix
is already applied to parties_by_locality.json, localities.json and
election_map_geo.json, and all downstream JSONs were regenerated.
"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.exit("Already applied on 2026-07-02 - see docstring. Not idempotent; refusing to run.")

ROOT = r"C:/Users/yarde/Downloads/election-dashboard-extracted/election-dashboard-main"
NAME = "ניר יצחק"

p = f"{ROOT}/data/parties_by_locality.json"
pbl = json.load(open(p, encoding="utf-8"))
row = pbl["13"][NAME]
m, z = row["מחל"], row["מרצ"]
row["מחל"], row["מרצ"] = z, m
delta = m - z                                   # vote mass moving right -> left
json.dump(pbl, open(p, "w", encoding="utf-8"), ensure_ascii=False)

p = f"{ROOT}/data/localities.json"
loc = json.load(open(p, encoding="utf-8"))
d = next(e for e in loc if e["name"] == NAME)["data"]["13"]
for f in ("right_pct", "right_haredi_pct"):
    d[f] = round(d[f] - delta, 2)
for f in ("left_pct", "center_left_arab_pct"):
    d[f] = round(d[f] + delta, 2)
json.dump(loc, open(p, "w", encoding="utf-8"), ensure_ascii=False)

p = f"{ROOT}/data/election_map_geo.json"
geo = json.load(open(p, encoding="utf-8"))
for f in geo["features"]:
    if f["properties"].get("name") != NAME: continue
    el = (f["properties"].get("elections") or {}).get("13")
    if not el: continue
    for fld in ("right_pct", "right_haredi_pct"):
        el[fld] = round(el[fld] - delta, 2)
    for fld in ("left_pct", "center_left_arab_pct"):
        el[fld] = round(el[fld] + delta, 2)
json.dump(geo, open(p, "w", encoding="utf-8"), ensure_ascii=False)
