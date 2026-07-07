# -*- coding: utf-8 -*-
"""
make_k25_ballot_addresses.py — snapshot the official CEC K25 kalpi address file
(kalpiplaces_kalpieslist_27-10.xlsx, Downloads) into
statarea_inputs/k25_ballot_addresses.json: {semel: {ballot: "street,num"}}.

Why: same-name venues at DIFFERENT addresses were merged into one point by the
(semel, venue-name) key (found 2026-07-06: TLV מרכז יום לקשיש = 3 buildings,
11 kalpiot, all dumped into נווה אביבים). The address is the only field that
splits them, and it exists only for K25. build_venue_dots.py and
build_statarea_modern.py consume this snapshot for K25 only.

Run: python -X utf8 analysis/make_k25_ballot_addresses.py
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(HERE, "statarea_inputs")
XLSX = r"C:\Users\yarde\Downloads\kalpiplaces_kalpieslist_27-10.xlsx"
sys.path.insert(0, HERE)
from build_venue_dots import canon_ballot  # noqa: E402


def main():
    import openpyxl
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    out = {}
    n = 0
    for row in wb["DataSheet"].iter_rows(min_row=2, values_only=True):
        sem, ballot, addr = str(row[2]), canon_ballot(row[4]), (row[6] or "").strip()
        if not addr:
            continue
        out.setdefault(sem, {})[ballot] = addr
        n += 1
    path = os.path.join(SNAP, "k25_ballot_addresses.json")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{n:,} kalpi addresses in {len(out):,} settlements -> {path} "
          f"({os.path.getsize(path)//1024} KB)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
