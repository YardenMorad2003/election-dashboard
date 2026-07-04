# -*- coding: utf-8 -*-
"""
fix_locality_gaps.py — 2026-07-04 locality data repair (document of record, idempotent).

Fixes three classes of defects in data/localities.json, audited 2026-07-04:

1. SPLIT ROWS: the K23-25 ingest stripped hyphens/geresh/parens from CEC names
   (e.g. 'מעלות-תרשיחא' -> 'מעלותתרשיחא'), and older CEC spelling drift (vav/yod,
   'דיר'/'דייר') split single localities into 2-4 rows with disjoint election sets.
   -> merged under one canonical name (MERGES below, each pair hand-reviewed;
      disjointness asserted at runtime).
   Special case: TWO rows both named ג'ת (Jatt/Triangle) — near-identical duplicates;
   the K15 entry conflicts (rh 8.1 vs 3.83); 8.1 matches parties_by_locality K15
   (ב+ג+מחל+שס = 8.07) so the 8.1 row wins; K13 taken from the other.

2. BROKEN K23/K24/K25 BLOC SPLITS (verified against the official CEC per-locality
   files, data.gov.il dataset votes-knesset, snapshots in analysis/official_cec/):
   - K24, all rows: opposition_right_pct double-counted תקווה חדשה (ת) and
     center_pct subtracted it (errors cancel inside center_left_arab_pct).
   - K23/K24/K25, 50-75 rows each (names containing geresh/gershayim, e.g. בית ג'ן):
     opposition_right_pct=0 with those votes folded into center_pct; at K24 this
     also corrupted center_left_arab_pct (ת dropped from it entirely).
   -> ALL bloc pct fields for K23/24/25 recomputed from official counts using the
      per-election party->bloc map in data/parties_national.json.
      Integer fields (bzb/kosher/voters/disqualified) were verified equal and are
      NOT touched. Calibration: TA/Bnei Brak/Kfar Manda K25 reproduce exactly.

3. MISSING K24/K25 ROWS: ~27 localities present in the official files (and in
   parties_by_locality) had no localities.json row for 24/25 under any spelling —
   incl. אום אל-פחם (35.7k bzb), באקה אל-גרביה, מג'ד אל-כרום, ג'ת, דיר אל-אסד...
   -> entries added from official counts onto the (merged) existing rows;
      brand-new reporting units (e.g. שער שומרון, K25-only) get new rows.
   NOT bugs: עץ אפרים / שערי תקווה end at K24 because the CEC stopped reporting
   them separately at K25 (verified absent from the official K25 file).

Also adds `semel` (official CBS locality code) to every row matchable to the
official 23/24/25 files or the CBS polygon layer — all joins were name-only before.

Run: python -X utf8 analysis/fix_locality_gaps.py
Backup written to data/localities.json.bak_pregapfix (first run only).
Report: analysis/locality_gapfix_report.txt
"""
import json
import os
import re
import shutil
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOC_PATH = os.path.join(ROOT, "data", "localities.json")
PN_PATH = os.path.join(ROOT, "data", "parties_national.json")
OFFICIAL_DIR = os.path.join(HERE, "official_cec")
POLY_PATHS = [os.path.join(ROOT, "locality_polygons.geojson"),
              os.path.join(ROOT, "locality_polygons_extra.geojson")]
REPORT_PATH = os.path.join(HERE, "locality_gapfix_report.txt")

META_COLS = ("_id", "סמל ועדה", "שם ישוב", "סמל ישוב", "בזב", "מצביעים", "פסולים", "כשרים")
BLOCS = ["right", "haredi", "center", "left", "arab", "opposition_right"]

report = []


def rep(s=""):
    report.append(s)


def norm(name):
    """Hebrew-letters-only + final-form normalization (kills punctuation/quotes/parens)."""
    s = re.sub(r"[^א-ת]", "", name)
    finals = {"ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ"}
    return "".join(finals.get(c, c) for c in s)


def skel(name):
    """norm + matres lectionis (vav/yod) stripped — LAST-RESORT matching only."""
    return norm(name).replace("ו", "").replace("י", "")


# ---------------------------------------------------------------------------
# Hand-reviewed merge table: canonical name -> alias rows to fold in.
# Every group verified: same real locality, disjoint election sets.
# Bedouin-tribe family: the CEC listed tribes bare in K13-15 and added ')שבט('
# from K16 on — 17 disjoint pairs merged under the )שבט( name. The truncated
# 'תראבין א-צאנע )שב' (16,18,19,20) is folded into the tribe chain: pre-K21 the
# tribe was the ONLY Tarabin CEC unit (the yishuv first appears as a separate
# row at K21), so those elections belong to the tribe.
# Deliberately NOT merged (adjudicated 2026-07-04):
#   יהוד / יהוד-מונוסון, קדימה / קדימה-צורן  — overlapping elections (separate
#     CEC reporting units before the municipal merger);
#   באקה-ג'ת (K18 only) — a real merged municipality, distinct entity;
#   שבלי (13,14) / שבלי-אום אל-גנם (15+) — village vs merged council, kept apart;
#   ח'ואלד / ח'ואלד )שבט( — overlapping elections (village vs tribe, distinct).
# ---------------------------------------------------------------------------
MERGES = {
    "אלי-עד": ["אליעד"],
    "אשדות יעקב איחוד": ["אשדות יעקב)איחוד("],
    "אשדות יעקב מאוחד": ["אשדות יעקב)מאוחד("],
    "בועיינה-נוג'ידאת": ["בועיינהנוגידאת"],
    "בית יצחק-שער חפר": ["בית יצחקשער חפר"],
    "בנימינה-גבעת עדה": ["בנימינהגבעת עדה"],
    "ג'דיידה-מכר": ["גדיידהמכר"],
    "ג'סר א-זרקא": ["גסר אזרקא"],
    "חד-נס": ["חדנס"],
    "חפצי-בה": ["חפציבה"],
    "חצור-אשדוד": ["חצוראשדוד"],
    "טובא-זנגריה": ["טובאזנגריה"],
    "טל-אל": ["טלאל"],
    "יאנוח-ג'ת": ["יאנוחגת"],
    "כסרא-סמיע": ["כסראסמיע"],
    "כעביה-טבאש-חג'אג'רה": ["כעביהטבאשחגאגרה"],
    "מעלות-תרשיחא": ["מעלותתרשיחא"],
    "ערערה בנגב": ["ערערהבנגב"],
    "פרדס חנה-כרכור": ["פרדס חנהכרכור"],
    "קצר א-סר": ["קצר אסר"],
    "רם-און": ["רםאון"],
    "שגב-שלום": ["שגבשלום"],
    "שריגים )לי-און(": ["שריגים ליאון"],
    "ניצנה (קהילת חינוך)": ["ניצנה)קהילת חנוך("],
    "קודייראת א-צאנע(שבט)": ["קודייראת אצאנעשבט", "קודייראת א-צאנע", "קדייראת א-צאנע"],
    "תראבין א-צאנע(ישוב)": ["תראבין אצאנעישוב"],
    "תראבין א-צאנע (שבט)": ["תראבין אצאנע שבט", "תראבין א-צאנע", "תראבין א-צאנע )שב"],
    "אבו ג'ווייעד )שבט": ["אבו ג'ווייעד"],
    "אבו עבדון )שבט(": ["אבו עבדון"],
    "אבו קורינאת )שבט(": ["אבו קורינאת"],
    "אבו רובייעה )שבט(": ["אבו רובייעה"],
    "אבו רוקייק )שבט(": ["אבו רוקייק"],
    "אטרש )שבט(": ["אטרש"],
    "אעצם )שבט(": ["אעצם"],
    "ג'נאביב )שבט(": ["ג'נאביב"],
    "הוואשלה )שבט(": ["הוואשלה"],
    "הוזייל )שבט(": ["הוזייל"],
    "נצאצרה )שבט(": ["נצאצרה"],
    "סייד )שבט(": ["סייד"],
    "עטאוונה )שבט(": ["עטאוונה"],
    "קבועה )שבט(": ["קבועה"],
    "קוואעין )שבט(": ["קוואעין"],
    "אום אל-פחם": ["אם אל-פחם"],
    "אום אל-ג'נם": ["אם אל-גנם"],
    "דיר חנא": ["דייר חנא"],
    "דיר אל-אסד": ["דייר אל-אסד"],
    "רומת היב": ["רומת הייב"],
    "חרות": ["חירות"],
    "בית חרות": ["בית חירות"],
    "שייח' דנון": ["שיח' דנון"],
    "חורפיש": ["חרפיש"],
    "מעיליא": ["מעליא"],
    "נאות הכיכר": ["נאות הככר"],
    "אסד )שבט(": ["אסד"],
    "שושנת העמקים רסקו": ["שושנת העמקים )רסק"],
    "כאוכב אבו אל-היג'א": ["כאוכב אבו אל-היגא", "כאוכב אבו אל-היג'", "כאוכב אל-היג'א"],
    "כפר ידידיה": ["ידידיה"],
    "נוף הגליל": ["נצרת עילית"],  # 2019 city rename, same semel 1061, disjoint 13-21/22-25
}

# rows that must NOT get a semel via skeleton matching (false-positive pairs caught
# in review: ידידיה almost matched ידידה/1144 — the real chain is כפר ידידיה/233 —
# and pre-merger קדימה almost matched kibbutz קדמה/392).
SEMEL_SKEL_BLACKLIST = {"ידידיה", "קדימה"}
# bogus semels to strip if a previous run wrote them (idempotent cleanup)
SEMEL_CLEANUP = {"קדימה": 392, "ידידיה": 1144}


def load_official(k):
    with open(os.path.join(OFFICIAL_DIR, f"k{k}_locality.json"), encoding="utf-8") as f:
        return json.load(f)


def bloc_votes(rec, bm):
    votes = {b: 0 for b in BLOCS}
    for c, v in rec.items():
        if c in META_COLS:
            continue
        b = bm.get(c)
        if b:
            votes[b] += v or 0
    return votes


def official_entry(rec, bm):
    """Build a localities.json data-entry from an official CEC locality record."""
    kosher = rec["כשרים"]
    if not kosher:
        return None
    v = bloc_votes(rec, bm)
    e = {
        "eligible": kosher,
        "right_haredi_pct": round(100 * (v["right"] + v["haredi"]) / kosher, 2),
        "center_left_arab_pct": round(100 * (v["center"] + v["left"] + v["arab"] + v["opposition_right"]) / kosher, 2),
        "right_pct": round(100 * v["right"] / kosher, 2),
        "haredi_pct": round(100 * v["haredi"] / kosher, 2),
        "center_pct": round(100 * v["center"] / kosher, 2),
        "left_pct": round(100 * v["left"] / kosher, 2),
        "arab_pct": round(100 * v["arab"] / kosher, 2),
        "kosher_votes": kosher,
        "opposition_right_pct": round(100 * v["opposition_right"] / kosher, 2),
        "bzb": rec["בזב"],
        "voters": rec["מצביעים"],
        "disqualified": rec["פסולים"],
    }
    if rec["בזב"]:
        e["turnout_pct"] = round(100 * rec["מצביעים"] / rec["בזב"], 1)
    return e


def main():
    loc = json.load(open(LOC_PATH, encoding="utf-8"))
    pn = json.load(open(PN_PATH, encoding="utf-8"))

    # ---- 0. backup (first run only) ----
    bak = LOC_PATH + ".bak_pregapfix"
    if not os.path.exists(bak):
        shutil.copyfile(LOC_PATH, bak)
        rep(f"backup written: {bak}")

    # ---- 1. ג'ת duplicate rows ----
    gt_rows = [r for r in loc if r["name"] == "ג'ת"]
    if len(gt_rows) == 2:
        a, b = gt_rows
        # the row whose K15 rh matches parties_by_locality (8.1) wins conflicts
        winner = a if abs((a["data"].get("15", {}).get("right_haredi_pct") or 0) - 8.1) < 0.5 else b
        loser = b if winner is a else a
        for k, v in loser["data"].items():
            if k not in winner["data"]:
                winner["data"][k] = v
        loc.remove(loser)
        rep(f"ג'ת duplicate merged: kept K15 rh={winner['data']['15']['right_haredi_pct']}, "
            f"absorbed elections {sorted(set(loser['data']) - set(winner['data']))} from duplicate")
    by_name = defaultdict(list)
    for r in loc:
        by_name[r["name"]].append(r)
    dups = {n: rs for n, rs in by_name.items() if len(rs) > 1}
    assert not dups, f"unexpected duplicate names remain: {list(dups)}"

    # ---- 2. merges ----
    rows_by_name = {r["name"]: r for r in loc}
    merged_groups = 0
    for canon, aliases in MERGES.items():
        present = [a for a in aliases if a in rows_by_name]
        if not present:
            continue  # idempotent: already merged
        canon_row = rows_by_name.get(canon)
        if canon_row is None:
            canon_row = {"name": canon, "elections_count": 0, "data": {}}
            loc.append(canon_row)
            rows_by_name[canon] = canon_row
        moved = []
        for a in present:
            arow = rows_by_name[a]
            overlap = set(arow["data"]) & set(canon_row["data"])
            assert not overlap, f"merge overlap {canon} <- {a}: {overlap}"
            canon_row["data"].update(arow["data"])
            loc.remove(arow)
            del rows_by_name[a]
            moved.append(f"{a} ({','.join(sorted(arow['data'], key=int))})")
        canon_row["elections_count"] = len(canon_row["data"])
        merged_groups += 1
        rep(f"MERGED -> {canon}: " + " + ".join(moved))
    rep(f"merge groups applied: {merged_groups}")

    # ---- 3+4. recompute K23/24/25 from official + add missing ----
    loc_by_norm = defaultdict(list)
    for r in loc:
        loc_by_norm[norm(r["name"])].append(r)
    loc_by_skel = defaultdict(list)
    for r in loc:
        loc_by_skel[skel(r["name"])].append(r)

    semel_of_row = {}   # id(row) -> semel
    new_rows = []
    for k in ["23", "24", "25"]:
        bm = {p["code"]: p["bloc"] for p in pn[k]["party_list"]}
        recs = load_official(k)
        n_changed_rows = 0
        n_changed_cells = 0
        int_mismatch = []
        added = []
        seen_rows = set()
        for rec in recs:
            name_off = rec["שם ישוב"]
            # official record -> loc row: exact, then norm, then skeleton (unique)
            row = rows_by_name.get(name_off)
            if row is None:
                cands = loc_by_norm.get(norm(name_off), [])
                if len(cands) == 1:
                    row = cands[0]
            if row is None:
                cands = [r for r in loc_by_skel.get(skel(name_off), [])]
                if len(cands) == 1:
                    row = cands[0]
            entry = official_entry(rec, bm)
            if entry is None:
                continue
            if row is not None:
                assert id(row) not in seen_rows, \
                    f"two official K{k} records map to loc row {row['name']} (second: {name_off})"
                seen_rows.add(id(row))
            if row is None:
                # brand-new reporting unit -> new row named as in the official file
                row = {"name": name_off, "elections_count": 0, "data": {}}
                loc.append(row)
                rows_by_name[name_off] = row
                loc_by_norm[norm(name_off)].append(row)
                loc_by_skel[skel(name_off)].append(row)
                new_rows.append(name_off)
            # semel bookkeeping (envelope row has semel 875 in CEC; skip non-geo pseudo row)
            if name_off != "מעטפות חיצוניות":
                s = rec["סמל ישוב"]
                prev = semel_of_row.get(id(row))
                assert prev is None or prev == s, f"semel conflict for {row['name']}: {prev} vs {s}"
                semel_of_row[id(row)] = s
            old = row["data"].get(k)
            if old is None:
                row["data"][k] = entry
                row["elections_count"] = len(row["data"])
                added.append(f"{row['name']} (bzb={entry['bzb']})")
                continue
            # verify integers untouched; recompute pct fields
            for f_ in ("bzb", "kosher_votes", "voters"):
                if old.get(f_) != entry.get(f_):
                    int_mismatch.append(f"{row['name']}.{f_}: loc={old.get(f_)} official={entry.get(f_)}")
            changed = []
            for f_ in ("right_haredi_pct", "center_left_arab_pct", "right_pct", "haredi_pct",
                       "center_pct", "left_pct", "arab_pct", "opposition_right_pct"):
                if old.get(f_) != entry[f_]:
                    changed.append(f_)
                    old[f_] = entry[f_]
            if changed:
                n_changed_rows += 1
                n_changed_cells += len(changed)
        rep(f"K{k}: recomputed pct fields on {n_changed_rows} rows ({n_changed_cells} cells); "
            f"added {len(added)} missing entries; int mismatches: {len(int_mismatch)}")
        for a in added:
            rep(f"   +K{k}: {a}")
        for m in int_mismatch[:20]:
            rep(f"   INT MISMATCH (not modified): {m}")
    if new_rows:
        rep("brand-new rows created: " + ", ".join(sorted(set(new_rows))))

    # ---- 5. semel from official files + CBS polygon layer for the rest ----
    for r in loc:
        s = semel_of_row.get(id(r))
        if s is not None:
            r["semel"] = int(s)
    cbs = {}
    for p in POLY_PATHS:
        try:
            g = json.load(open(p, encoding="utf-8"))
        except FileNotFoundError:
            continue
        for f in g["features"]:
            sm = int(f["properties"]["semel"])
            cbs.setdefault(sm, f["properties"].get("name"))
    cbs_by_norm = defaultdict(list)
    cbs_by_skel = defaultdict(list)
    for sm, nm in cbs.items():
        cbs_by_norm[norm(nm)].append(sm)
        cbs_by_skel[skel(nm)].append(sm)
    for r in loc:
        if r["name"] in SEMEL_CLEANUP and r.get("semel") == SEMEL_CLEANUP[r["name"]]:
            del r["semel"]
            rep(f"semel cleanup: removed bogus semel {SEMEL_CLEANUP[r['name']]} from {r['name']}")
    claimed = {r.get("semel") for r in loc if r.get("semel")}
    n_cbs_semel = 0
    skel_log = []
    for r in loc:
        if r.get("semel"):
            continue
        nm = r["name"]
        cands = cbs_by_norm.get(norm(nm), [])
        via = "norm"
        if len(cands) != 1:
            if nm in SEMEL_SKEL_BLACKLIST:
                continue
            cands = cbs_by_skel.get(skel(nm), [])
            via = "skel"
        if len(cands) == 1 and cands[0] not in claimed:
            r["semel"] = cands[0]
            claimed.add(cands[0])
            n_cbs_semel += 1
            if via == "skel":
                skel_log.append(f"{nm} -> semel {cands[0]} ({cbs[cands[0]]})")
    rep(f"semel attached: {sum(1 for r in loc if r.get('semel'))} rows total "
        f"({n_cbs_semel} via CBS polygon layer); rows without semel: "
        f"{sum(1 for r in loc if not r.get('semel'))}")
    for s in skel_log:
        rep(f"   skeleton semel match (review): {s}")

    # ---- write ----
    json.dump(loc, open(LOC_PATH, "w", encoding="utf-8"), ensure_ascii=False)
    rep(f"written: {LOC_PATH} ({len(loc)} rows)")
    open(REPORT_PATH, "w", encoding="utf-8").write("\n".join(report))
    print(f"done; report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
