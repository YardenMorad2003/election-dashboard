# -*- coding: utf-8 -*-
"""
ingest_k26.py — add Knesset 26 (27 Oct 2026) to the four core data files.

Sources (frozen snapshots, see K26_PLAN.md):
  analysis/official_cec/k26_locality.json  official CEC per-locality export (expc.csv)
  analysis/official_cec/k26_national.json  official totals + seats (CEC national results page)

Writes (idempotent; first run backs each file up to <name>.bak_prek26):
  data/parties_national.json["26"]
  data/core.json                (knesset_years / knesset_info / national.elections /
                                 national_blocs / national_bloc_totals / elections_range)
  data/localities.json          data["26"] per row, joined on `semel` (never on names)
  data/parties_by_locality.json ["26"] = {canonical row name: {code: share %}}

Bloc table approved by the owner 2026-11-20. New at K26: the bloc value "third"
(lists outside both grand blocs: די, ך). It is excluded from right_haredi_pct and
center_left_arab_pct and carried in its own field `third_pct` (K26 entries only).

Conventions copied from the K25 layer (verified against the existing data):
  * shares are % of valid votes; only tracked lists (party_list) count toward blocs,
    so the two grand blocs sum to < 100;
  * locality `center_pct` EXCLUDES opposition_right, `center_left_arab_pct` INCLUDES it;
  * core `national_blocs[k].center` INCLUDES opposition_right, while
    `national.elections[k].center_pct` does not;
  * `eligible` == `kosher_votes` (valid votes); `bzb` is the register;
  * `total_eligible` in core is valid votes; `turnout_pct` is 1 dp;
  * the double-envelope record (semel 9999) lives on the row 'מעטפות חיצוניות'.

Run:    python -X utf8 analysis/ingest_k26.py
Report: analysis/k26_ingest_report.txt
"""
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
D = os.path.join(ROOT, "data")
OFF = os.path.join(HERE, "official_cec")
REPORT = os.path.join(HERE, "k26_ingest_report.txt")
K = "26"
YEAR = 2026
ENVELOPE_SEMEL = 9999
ENVELOPE_ROW = "מעטפות חיצוניות"

OPP_DISPLAY_BEITEINU = "ימין אופוזיציוני (מרכז לצורך חישוב הגושים, החל מהכנסת ה-21)"
OPP_DISPLAY_K26 = "ימין אופוזיציוני (מרכז לצורך חישוב הגושים, בכנסת ה-26)"
THIRD_DISPLAY = "גוש שלישי (מחוץ לשני הגושים הגדולים)"

# code, display name, bloc  — order = party_list order (bloc-grouped, like K25)
PARTY_LIST = [
    ("מחל", "הליכוד", "right", None),
    ("ב", "עוצמה יהודית", "right", None),
    ("ט", "הציונות הדתית וזהות", "right", None),
    ("ל", "ישראל ביתנו", "opposition_right", OPP_DISPLAY_BEITEINU),
    ("רק", "ביחד", "opposition_right", OPP_DISPLAY_K26),
    ("שס", "ש\"ס", "haredi", None),
    ("ג", "יהדות התורה", "haredi", None),
    ("דרך", "ישר", "center", None),
    ("אמת", "הדמוקרטים", "left", None),
    ("ודם", "הרשימה המשותפת", "arab", None),
    ("עם", "רע\"מ", "arab", None),
    ("די", "המילואימניקים והכלכלית", "third", THIRD_DISPLAY),
    ("ך", "עמך ישראל", "third", THIRD_DISPLAY),
]
BLOC_OF = {c: b for c, _, b, _ in PARTY_LIST}
TRACKED = [c for c, _, _, _ in PARTY_LIST]
BLOCS = ["right", "haredi", "center", "left", "arab", "opposition_right", "third"]
META = ("_id", "סמל ועדה", "שם ישוב", "סמל ישוב", "בזב", "מצביעים", "פסולים", "כשרים")

rep_lines = []


def rep(s=""):
    rep_lines.append(s)


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save(p, obj):
    bak = p + ".bak_prek26"
    if not os.path.exists(bak):
        shutil.copyfile(p, bak)
        rep(f"backup written: {os.path.basename(bak)}")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def bloc_votes(rec):
    v = {b: 0 for b in BLOCS}
    for c in TRACKED:
        v[BLOC_OF[c]] += rec.get(c, 0) or 0
    return v


def pct(n, d, nd=2):
    return round(100 * n / d, nd)


def entry_from(rec):
    """localities.json data entry — same field order as official_entry() in fix_locality_gaps.py."""
    kosher = rec["כשרים"]
    if not kosher:
        return None
    v = bloc_votes(rec)
    e = {
        "eligible": kosher,
        "right_haredi_pct": pct(v["right"] + v["haredi"], kosher),
        "center_left_arab_pct": pct(v["center"] + v["left"] + v["arab"] + v["opposition_right"], kosher),
        "right_pct": pct(v["right"], kosher),
        "haredi_pct": pct(v["haredi"], kosher),
        "center_pct": pct(v["center"], kosher),
        "left_pct": pct(v["left"], kosher),
        "arab_pct": pct(v["arab"], kosher),
        "kosher_votes": kosher,
        "opposition_right_pct": pct(v["opposition_right"], kosher),
        "third_pct": pct(v["third"], kosher),
        "bzb": rec["בזב"],
        "voters": rec["מצביעים"],
        "disqualified": rec["פסולים"],
    }
    if rec["בזב"]:
        e["turnout_pct"] = round(100 * rec["מצביעים"] / rec["בזב"], 1)
    return e


def main():
    off = load(os.path.join(OFF, "k26_locality.json"))
    nat = load(os.path.join(OFF, "k26_national.json"))
    letters = [c for c in off[0] if c not in META]
    assert all(c in letters for c in TRACKED), "tracked code missing from official file"

    # ------------------------------------------------------------------ totals
    tot = {c: sum(r[c] for r in off) for c in letters}
    valid = sum(r["כשרים"] for r in off)
    voters = sum(r["מצביעים"] for r in off)
    bzb = sum(r["בזב"] for r in off)
    invalid = sum(r["פסולים"] for r in off)
    assert (bzb, voters, invalid, valid) == (nat["registered"], nat["voters"], nat["invalid"], nat["valid"]), \
        "locality sums differ from the official national totals"
    assert sum(tot.values()) == valid, "list votes do not sum to valid votes"
    nat_votes = {x["code"]: x["votes"] for x in nat["lists"]}
    assert all(nat_votes[c] == tot[c] for c in letters), "per-list totals differ from k26_national.json"
    seats = {x["code"]: x["seats"] for x in nat["lists"] if x["seats"]}
    assert sum(seats.values()) == 120 and set(seats) <= set(TRACKED)
    untracked = sorted(((c, tot[c]) for c in letters if c not in TRACKED), key=lambda t: -t[1])
    rep("== NATIONAL ==")
    rep(f"registered {bzb:,} | voters {voters:,} | invalid {invalid:,} | valid {valid:,} | "
        f"turnout {100 * voters / bzb:.2f}% | official rows {len(off)}")
    rep(f"untracked lists: {len(untracked)} lists, {sum(v for _, v in untracked):,} votes "
        f"({pct(sum(v for _, v in untracked), valid)}%); largest: "
        + ", ".join(f"{c} {v:,}" for c, v in untracked[:4]))

    # -------------------------------------------------------- parties_national
    pn = load(os.path.join(D, "parties_national.json"))
    plist = []
    for code, name, bloc, disp in PARTY_LIST:
        p = {"code": code, "name": name, "bloc": bloc}
        if disp:
            p["bloc_display"] = disp
        plist.append(p)
    pn[K] = {
        "election_name": f"כנסת {K} ({YEAR})",
        "year": YEAR,
        "party_list": plist,
        "national": {c: pct(tot[c], valid) for c in sorted(TRACKED)},
        "national_votes": {c: tot[c] for c in sorted(TRACKED)},
        "seats": dict(sorted(seats.items(), key=lambda t: -t[1])),
    }
    save(os.path.join(D, "parties_national.json"), pn)
    rep()
    rep("== PARTY LIST (approved bloc table) ==")
    for code, name, bloc, _ in PARTY_LIST:
        rep(f"  {code:<4} {bloc:<17} votes {tot[code]:>9,}  {pct(tot[code], valid):>5}%  seats {seats.get(code, 0):>2}  {name}")

    # -------------------------------------------------------------------- core
    core = load(os.path.join(D, "core.json"))
    bv = {b: sum(tot[c] for c in TRACKED if BLOC_OF[c] == b) for b in BLOCS}
    b2 = {b: pct(bv[b], valid) for b in BLOCS}
    rh = pct(bv["right"] + bv["haredi"], valid)
    cla = pct(bv["center"] + bv["left"] + bv["arab"] + bv["opposition_right"], valid)
    n_loc = sum(1 for r in off if r["סמל ישוב"] != ENVELOPE_SEMEL and r["כשרים"])
    core["metadata"]["knesset_years"][K] = YEAR
    core["metadata"]["elections_range"] = "Knesset 13 (1992) to Knesset 26 (2026)"
    core["national"]["knesset_info"][K] = YEAR
    core["national"]["elections"][K] = {
        "year": YEAR,
        "total_eligible": valid,
        "localities_count": n_loc,
        "right_haredi_pct": rh,
        "center_left_arab_pct": cla,
        "right_pct": b2["right"],
        "haredi_pct": b2["haredi"],
        "center_pct": b2["center"],
        "left_pct": b2["left"],
        "arab_pct": b2["arab"],
        "opposition_right_pct": b2["opposition_right"],
        "third_pct": b2["third"],
        "turnout_pct": round(100 * voters / bzb, 1),
    }
    nb = {
        "left": b2["left"],
        "center": pct(bv["center"] + bv["opposition_right"], valid),
        "arab": b2["arab"],
        "right": b2["right"],
        "haredi": b2["haredi"],
        "center_left_arab": cla,
        "third": b2["third"],
    }
    core["national_blocs"][K] = dict(nb)
    core["national_bloc_totals"][K] = dict(nb)
    save(os.path.join(D, "core.json"), core)
    rep()
    rep("== NATIONAL BLOCS ==")
    rep(f"  right-haredi {rh} | center-left-arab {cla} | third {b2['third']} | "
        f"untracked {round(100 - rh - cla - b2['third'], 2)}")
    rep("  " + " | ".join(f"{b} {b2[b]}" for b in BLOCS))
    bs = {b: sum(s for c, s in seats.items() if BLOC_OF[c] == b) for b in BLOCS}
    rep("  seats: " + " | ".join(f"{b} {bs[b]}" for b in BLOCS)
        + f" || right-haredi {bs['right'] + bs['haredi']} vs center-left-arab "
          f"{bs['center'] + bs['left'] + bs['arab'] + bs['opposition_right']}")

    # -------------------------------------------------------------- localities
    loc = load(os.path.join(D, "localities.json"))
    by_semel = {}
    for r in loc:
        if r.get("semel") is not None:
            assert r["semel"] not in by_semel, f"duplicate semel in localities.json: {r['semel']}"
            by_semel[r["semel"]] = r
    by_name = {r["name"]: r for r in loc}
    assert len(by_name) == len(loc), "duplicate row names in localities.json"
    env_row = by_name[ENVELOPE_ROW]

    new_rows, renamed, skipped_empty, outliers = [], [], [], []
    row_of = {}          # official semel -> row
    for rec in off:
        s = rec["סמל ישוב"]
        e = entry_from(rec)
        if e is None:
            skipped_empty.append((s, rec["שם ישוב"]))
            continue
        if s == ENVELOPE_SEMEL:
            row = env_row
        else:
            row = by_semel.get(s)
            if row is None:
                assert rec["שם ישוב"] not in by_name, \
                    f"new semel {s} but a row named {rec['שם ישוב']} already exists — review by hand"
                row = {"name": rec["שם ישוב"], "elections_count": 0, "data": {}, "semel": s}
                loc.append(row)
                by_semel[s] = row
                by_name[row["name"]] = row
                new_rows.append((s, row["name"], e["bzb"], e["kosher_votes"]))
        assert id(row) not in {id(x) for x in row_of.values()}, f"two official records map to {row['name']}"
        row_of[s] = row
        prev = row["data"].get("25")
        row["data"][K] = e
        row["elections_count"] = len(row["data"])
        if prev and s != ENVELOPE_SEMEL:
            d_rh = round(e["right_haredi_pct"] - prev["right_haredi_pct"], 1)
            d_bzb = (e["bzb"] / prev["bzb"] - 1) if prev.get("bzb") else None
            if abs(d_rh) > 25 or (d_bzb is not None and abs(d_bzb) > 0.40):
                outliers.append((row["name"], s, prev.get("bzb"), e["bzb"], prev["right_haredi_pct"],
                                 e["right_haredi_pct"], d_rh))
    save(os.path.join(D, "localities.json"), loc)

    with_26 = [r for r in loc if K in r["data"]]
    s_valid = sum(r["data"][K]["kosher_votes"] for r in with_26)
    s_voters = sum(r["data"][K]["voters"] for r in with_26)
    s_bzb = sum(r["data"][K]["bzb"] for r in with_26)
    assert (s_bzb, s_voters, s_valid) == (bzb, voters, valid), "localities.json K26 sums != official totals"
    had25 = [r for r in loc if "25" in r["data"] and K not in r["data"]]
    rep()
    rep("== LOCALITIES ==")
    rep(f"rows with K26: {len(with_26)} (official records {len(off)}, empty skipped {len(skipped_empty)}); "
        f"sums equal official totals exactly: bzb {s_bzb:,} voters {s_voters:,} valid {s_valid:,}")
    rep(f"total rows now {len(loc)}; rows with K25 but no K26: {len(had25)} "
        + ", ".join(r["name"] for r in had25))
    rep(f"NEW ROWS ({len(new_rows)}) — first-time reporting units, named as in the official file:")
    for s, n, b, kv in sorted(new_rows, key=lambda t: -t[2]):
        rep(f"   semel {s}: {n} (bzb {b:,}, valid {kv:,})")
    rep(f"OUTLIERS FOR REVIEW ({len(outliers)}) — |d right-haredi| > 25 pts or register change > 40% "
        f"vs K25. Not altered:")
    for n, s, b0, b1, r0, r1, d in sorted(outliers, key=lambda t: -(t[3] or 0)):
        rep(f"   {n} (semel {s}): bzb {b0:,} -> {b1:,}; right-haredi {r0} -> {r1} ({d:+})")

    # ------------------------------------------------------- parties_by_locality
    pbl = load(os.path.join(D, "parties_by_locality.json"))
    out = {}
    for rec in off:
        s = rec["סמל ישוב"]
        if s not in row_of:
            continue
        out[row_of[s]["name"]] = {c: pct(rec[c], rec["כשרים"]) for c in TRACKED}
    assert len(out) == len(with_26)
    pbl[K] = out
    save(os.path.join(D, "parties_by_locality.json"), pbl)
    rep()
    rep(f"== PARTIES BY LOCALITY ==  {len(out)} rows keyed by the canonical localities.json name, "
        f"{len(TRACKED)} tracked codes, shares of valid votes (2 dp)")

    # name drift is informational: rows keep their canonical name
    for rec in off:
        s = rec["סמל ישוב"]
        if s in row_of and row_of[s]["name"] != rec["שם ישוב"]:
            renamed.append((s, row_of[s]["name"], rec["שם ישוב"]))
    rep()
    rep(f"== NAME DIFFERENCES (row name kept; official K26 spelling shown) == {len(renamed)}")
    for s, a, b in renamed:
        rep(f"   {s}: {a}  |  {b}")

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(rep_lines))
    print("done ->", REPORT)


if __name__ == "__main__":
    main()
