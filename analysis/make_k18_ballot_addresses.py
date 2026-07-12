# -*- coding: utf-8 -*-
"""
make_k18_ballot_addresses.py — snapshot the official CEC K18 polling-place list
(knesset18_polling_places.xlsx, Downloads; digitized from the 2008-12-28 PDF)
into statarea_inputs/k18_ballot_addresses.json: {semel: {ballot: "street,num"}}
— the same shape as k25_ballot_addresses.json.

Why: the 2009 layer was placed by venue-NAME matching into the modern station
index (a decade-long name bridge, ~99.7% coverage but imprecise). This list
carries a period-true street address per kalpi; joined on (semel, kalpi number)
it covers 98.55% of K18 geographic votes, with 97.8% exact eligible-voter
agreement against knesset18_ballots.csv (join validated 2026-07-11).

Locality codes in the xlsx are zero-padded ('0472') — normalized to int form.

Run: python -X utf8 analysis/make_k18_ballot_addresses.py
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(HERE, "statarea_inputs")
XLSX = r"C:\Users\yarde\Downloads\knesset18_polling_places.xlsx"
sys.path.insert(0, HERE)
from build_venue_dots import canon_ballot  # noqa: E402


def main():
    import openpyxl
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    out = {}
    names = {}   # period-true venue names ("Polling place" column) — display fallback
    elig = {}    # official eligible voters — roster guard for the K19/K20 crosswalk
    n = 0
    hdr = None
    for row in wb["Polling Places"].iter_rows(values_only=True):
        if hdr is None:
            if row and row[0] == "Committee code":
                hdr = list(row)
            continue
        if not row or row[3] is None:
            continue
        sem = str(int(str(row[3]).strip()))
        ballot = canon_ballot(row[5])
        addr = (str(row[8]).strip() if row[8] is not None else "")
        vname = (str(row[9]).strip() if row[9] is not None else "")
        if vname:
            names.setdefault(sem, {})[ballot] = vname
        if isinstance(row[11], (int, float)):
            elig.setdefault(sem, {})[ballot] = int(row[11])
        if not addr:
            continue
        out.setdefault(sem, {})[ballot] = addr
        n += 1
    path = os.path.join(SNAP, "k18_ballot_addresses.json")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    vpath = os.path.join(SNAP, "k18_ballot_venues.json")
    json.dump(names, open(vpath, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    epath = os.path.join(SNAP, "k18_ballot_eligible.json")
    json.dump(elig, open(epath, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{n:,} kalpi addresses in {len(out):,} settlements -> {path} "
          f"({os.path.getsize(path)//1024} KB)")
    print(f"venue names -> {vpath} ({os.path.getsize(vpath)//1024} KB)")
    print(f"eligible voters -> {epath} ({os.path.getsize(epath)//1024} KB)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
