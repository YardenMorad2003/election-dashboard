# -*- coding: utf-8 -*-
"""
build_statarea_18.py — STATAREA 2009 build step 6: aggregate K18 votes per
stat08 and compute bloc/party percentages.

Inputs:
- analysis/statarea_inputs/ballot_stat08_18.csv  (step 5: semel,ballot -> stat08)
- elections-merge/data/knesset18_ballots.csv     (raw per-ballot party counts)
- data/parties_national.json['18']               (bloc taxonomy: 5 blocs)

Fixes baked in:
- #1  party columns = hdr[index('פסולים')+1 : index('ת. עדכון')]  (34 cols;
      the raw K18 layout differs from the 2022 join CSV — cannot reuse
      valid..n_ballots boundaries).
- #4  2009 = 5 blocs {right,haredi,center,left,arab}; NO opposition_right.
      rh = right+haredi ; cla = center+left+arab.
- #3  emits analysis/statarea_inputs/statarea_2009_counts.csv (per-stat08 raw
      counts) so validate_statarea_2009.py can rebuild per-party totals.

Outputs:
- analysis/statarea_inputs/statarea_2009_counts.csv   (validator snapshot)
- analysis/statarea_inputs/statarea_2009_votes.json   (areas dict, votes only;
  step 7 adds the 2008 census join, then writes data/statarea_2009.json)

Run: python -X utf8 analysis/build_statarea_18.py
"""
import csv
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAP = os.path.join(HERE, "statarea_inputs")
EM = r"C:\Users\yarde\elections-merge\data"
STAT08_CSV = os.path.join(SNAP, "ballot_stat08_18.csv")
COUNTS = os.path.join(SNAP, "statarea_2009_counts.csv")
VOTES = os.path.join(SNAP, "statarea_2009_votes.json")

BLOCS = ["right", "haredi", "center", "left", "arab"]   # FIX #4: no opposition_right


def canon(bal):
    try:
        f = float(bal)
        return str(int(f)) if f == int(f) else bal
    except ValueError:
        return bal


def main():
    pn = json.load(open(os.path.join(ROOT, "data", "parties_national.json"), encoding="utf-8"))
    bloc_of = {p["code"]: p["bloc"] for p in pn["18"]["party_list"]}
    assert set(bloc_of.values()) <= set(BLOCS), f"unexpected bloc in '18': {set(bloc_of.values())}"

    # stat08 per (semel, ballot)
    s08 = {}
    for r in csv.DictReader(open(STAT08_CSV, encoding="utf-8-sig")):
        if r["stat08"]:
            s08[(r["semel"], r["ballot"])] = int(r["stat08"])

    # ---- read raw K18 CSV, aggregate per stat08 ----
    with open(os.path.join(EM, "knesset18_ballots.csv"), encoding="utf-8-sig") as f:
        rdr = csv.DictReader(f)
        hdr = rdr.fieldnames
        i_voted = hdr.index("מצביעים")
        col_bzb = hdr[i_voted - 1]            # בז"ב sits right before מצביעים
        party_cols = hdr[hdr.index("פסולים") + 1: hdr.index("ת. עדכון")]   # FIX #1 -> 34
        unmapped = [c for c in party_cols if c not in bloc_of]
        missing = [c for c in bloc_of if c not in party_cols]
        print(f"party columns: {len(party_cols)}; mapped to a bloc: {len(party_cols)-len(unmapped)}; "
              f"'other' residue codes: {len(unmapped)}")
        if missing:
            print(f"  WARNING bloc codes absent from CSV: {missing}")

        agg = defaultdict(lambda: {"eligible": 0, "voted": 0, "valid": 0, "disq": 0,
                                   "n_ballots": 0, "p": defaultdict(int)})
        unplaced_votes = 0
        for r in rdr:
            semel = r["סמל ישוב"].strip()
            if semel == "0":
                continue
            sid = s08.get((semel, canon(r["סמל קלפי"].strip())))
            valid = int(r["כשרים"] or 0)
            if sid is None:
                unplaced_votes += valid
                continue
            a = agg[sid]
            a["eligible"] += int(r[col_bzb] or 0)
            a["voted"] += int(r["מצביעים"] or 0)
            a["valid"] += valid
            a["disq"] += int(r["פסולים"] or 0)
            a["n_ballots"] += 1
            for c in party_cols:
                v = int(r[c] or 0)
                if v:
                    a["p"][c] += v

    # ---- build records + counts snapshot ----
    areas = {}
    counts_rows = []
    tot_valid = 0
    for sid, a in agg.items():
        valid = a["valid"]
        if valid <= 0:
            continue
        tot_valid += valid
        semel, sa = divmod(sid, 10000)
        bv = {b: 0 for b in BLOCS}
        other = 0
        for c, v in a["p"].items():
            b = bloc_of.get(c)
            if b:
                bv[b] += v
            else:
                other += v
        blocs = {b: round(100 * bv[b] / valid, 2) for b in BLOCS}
        blocs["rh"] = round(100 * (bv["right"] + bv["haredi"]) / valid, 2)
        blocs["cla"] = round(100 * (bv["center"] + bv["left"] + bv["arab"]) / valid, 2)
        blocs["other"] = round(100 * other / valid, 2)
        parties = {c: round(100 * v / valid, 2) for c, v in a["p"].items() if v / valid >= 0.005}
        winner = max(a["p"], key=a["p"].get) if a["p"] else None
        areas[sid] = {
            "semel": semel, "sa": sa,
            "eligible": a["eligible"], "voted": a["voted"], "valid": valid,
            "n_ballots": a["n_ballots"],
            "turnout": round(100 * a["voted"] / a["eligible"], 1) if a["eligible"] else None,
            "winner": winner, "blocs": blocs, "parties": parties,
        }
        counts_rows.append([sid, semel, sa, a["eligible"], a["voted"], valid, a["disq"],
                            a["n_ballots"]] + [a["p"].get(c, 0) for c in party_cols])

    # ---- write counts snapshot (validator input, FIX #3) ----
    with open(COUNTS, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["stat08", "semel", "sa", "eligible", "voted", "valid", "disq", "n_ballots"] + party_cols)
        w.writerows(counts_rows)

    json.dump({"meta": {"election": "18", "blocs": BLOCS,
                        "built_step": 6, "unplaced_votes": unplaced_votes},
               "areas": {str(k): v for k, v in areas.items()}},
              open(VOTES, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

    # ---- report + bloc-math + spot checks ----
    print(f"\nstat-areas with votes: {len(areas)}")
    print(f"total valid votes in layer: {tot_valid:,}  (unplaced: {unplaced_votes:,})")
    bad = sum(1 for v in areas.values()
              if abs(v["blocs"]["rh"] + v["blocs"]["cla"] + v["blocs"]["other"] - 100) > 0.1)
    print(f"bloc-math check (rh+cla+other==100): {len(areas)-bad}/{len(areas)} ok")

    print("\nspot checks (winner + bloc dominance):")
    def spot(semel, label):
        recs = [v for k, v in areas.items() if v["semel"] == semel]
        if not recs:
            print(f"   {label}: none"); return
        from collections import Counter
        win = Counter(v["winner"] for v in recs).most_common(3)
        import statistics as st
        for b in ("rh", "cla", "haredi", "arab"):
            pass
        m = {b: round(st.mean(v["blocs"][b] for v in recs), 1) for b in ("rh", "cla", "haredi", "arab", "right", "center", "left")}
        print(f"   {label} (semel {semel}, {len(recs)} SAs): winners {win}")
        print(f"        mean blocs rh={m['rh']} cla={m['cla']} (haredi={m['haredi']} arab={m['arab']} right={m['right']} ctr={m['center']} left={m['left']})")
    spot(6100, "Bnei Brak — expect ג/שס, haredi")
    spot(2710, "Umm al-Fahm — expect Arab bloc")
    spot(5000, "Tel Aviv — expect center/left (קדימה/אמת/מרצ)")
    spot(3797, "Modiin Illit — expect ג, haredi")
    print(f"\nwrote {COUNTS}\nwrote {VOTES}")


if __name__ == "__main__":
    main()
