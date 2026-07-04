# -*- coding: utf-8 -*-
"""
rebuild_map_geo.py — 2026-07-04 map data rebake (companion to fix_locality_gaps.py).

data/election_map_geo.json had election data baked per polygon by an exact-name
join against localities.json, so every naming drift left polygons with partial
histories (e.g. Umm al-Fahm gray from K24, Pardes Hanna-Karkur gray from K23,
Isfiya/'עוספייא' empty for ALL elections), and ~40 small localities whose CBS
polygons exist in locality_polygons*.geojson never made it into the map at all.

This script:
1. Matches every geo feature to a (post-gapfix) localities.json row —
   exact name, then Hebrew-letters-only normalization, then a vav/yod-stripped
   skeleton (unique matches only), then a hand-reviewed override list for the
   five corrupted feature names. Stamps `semel` on each matched feature.
2. REPLACES each matched feature's baked `elections` with the full row data
   (minus turnout_pct, per the existing baked schema) and refreshes the
   top-level convenience props (latest_election + pct/count fields).
3. ADDS features for localities that have data + a CBS polygon but no feature:
   geometry from locality_polygons.geojson (fallback _extra), semel-keyed.
   Bedouin tribes / IDF camps / double-envelopes / Hebron have no CBS polygon
   and correctly stay off-map.

Run AFTER fix_locality_gaps.py:  python -X utf8 analysis/rebuild_map_geo.py
Backup: data/election_map_geo.json.bak_pregapfix (first run only).
Report: analysis/map_rebake_report.txt
"""
import json
import os
import re
import shutil
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GEO_PATH = os.path.join(ROOT, "data", "election_map_geo.json")
LOC_PATH = os.path.join(ROOT, "data", "localities.json")
POLY_PATHS = [os.path.join(ROOT, "locality_polygons.geojson"),
              os.path.join(ROOT, "locality_polygons_extra.geojson")]
REPORT_PATH = os.path.join(HERE, "map_rebake_report.txt")

# corrupted / alternate-source feature names, hand-mapped to their locality row
GEO_NAME_TO_LOC = {
    "באקה אל גרבייה (באקה אל ררבי": "באקה אל-גרביה",
    "שבלי - אום אל רנם": "שבלי-אום אל-גנם",
    "גוש חלב (ג'יש)": "ג'ש )גוש חלב(",
    "רג'ר": "ע'ג'ר",          # Ghajar — second polygon under the Arabic-Rajar name
    "ג'סר אל-זרקא": "ג'סר א-זרקא",
    "עין קיניה": "עין קנייא",   # Ein Qiniyye — CEC spells with final aleph
    "ידידיה": "כפר ידידיה",     # CEC renamed at K16; row merged under כפר ידידיה
}

PCT_FIELDS = ("right_haredi_pct", "center_left_arab_pct", "right_pct", "haredi_pct",
              "center_pct", "left_pct", "arab_pct", "opposition_right_pct")

# Features renamed to their canonical localities.json row name. Two reasons:
# (a) corrupt CBS-derived display names ('באקה אל גרבייה (באקה אל ררבי');
# (b) the map panel's runtime findPartyData(name, k) join against
#     parties_by_locality resolves punctuation but NOT vav/yod, so CBS-spelled
#     features (עוספייא/כסייפה/שהם...) never matched their party rows.
# Verified in-browser 2026-07-04: renaming fixes the panel join for all of these.
# NOT renamed (pbl itself spells them differently per era — pre-existing panel
# residual): דיר חנא, דיר אל אסד, חרות, יהוד(K16).
RENAME_TO_CANONICAL = {
    "עוספייא", "כסייפה", "ג'וליס", "שהם", "עילבון", "ידידיה", "רג'ר",
    "באקה אל גרבייה (באקה אל ררבי", "גוש חלב (ג'יש)", "ניצנה)קהילת חנוך(",
    "שבלי - אום אל רנם", "ג'סר אל-זרקא",
}

report = []


def rep(s=""):
    report.append(s)


def norm(name):
    s = re.sub(r"[^א-ת]", "", name or "")
    finals = {"ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ"}
    return "".join(finals.get(c, c) for c in s)


def skel(name):
    return norm(name).replace("ו", "").replace("י", "")


def baked_entry(entry):
    e = {k: v for k, v in entry.items() if k != "turnout_pct"}
    return e


def refresh_top_props(props, row):
    ks = sorted(row["data"], key=int)
    latest = ks[-1]
    e = row["data"][latest]
    props["latest_election"] = latest
    props["matched"] = True
    for f in PCT_FIELDS:
        props[f] = e.get(f, 0)
    for f in ("eligible", "kosher_votes", "bzb", "voters"):
        if e.get(f) is not None:
            props[f] = e[f]
    props["elections"] = {k: baked_entry(v) for k, v in row["data"].items()}


def main():
    geo = json.load(open(GEO_PATH, encoding="utf-8"))
    loc = json.load(open(LOC_PATH, encoding="utf-8"))

    bak = GEO_PATH + ".bak_pregapfix"
    if not os.path.exists(bak):
        shutil.copyfile(GEO_PATH, bak)
        rep(f"backup written: {bak}")

    rows_by_name = {r["name"]: r for r in loc}
    loc_by_norm = defaultdict(list)
    loc_by_skel = defaultdict(list)
    for r in loc:
        loc_by_norm[norm(r["name"])].append(r)
        loc_by_skel[skel(r["name"])].append(r)

    # --- 1+2: match & rebake existing features ---
    stats = defaultdict(int)
    unmatched = []
    skel_matches = []
    covered_semels = set()
    for f in geo["features"]:
        p = f["properties"]
        name = p["name"]
        row = None
        if name in GEO_NAME_TO_LOC:
            row = rows_by_name.get(GEO_NAME_TO_LOC[name])
            stats["override"] += 1
        elif name in rows_by_name:
            row = rows_by_name[name]
            stats["exact"] += 1
        else:
            cands = loc_by_norm.get(norm(name), [])
            if len(cands) == 1:
                row = cands[0]
                stats["norm"] += 1
            else:
                cands = loc_by_skel.get(skel(name), [])
                if len(cands) == 1:
                    row = cands[0]
                    stats["skeleton"] += 1
                    skel_matches.append(f"{name} -> {row['name']}")
        if row is None:
            unmatched.append(name)
            stats["unmatched"] += 1
            continue
        if name in RENAME_TO_CANONICAL and name != row["name"]:
            p["name"] = row["name"]
            stats["renamed"] += 1
            rep(f"   renamed feature: {name} -> {row['name']}")
        if row.get("semel"):
            p["semel"] = row["semel"]
            covered_semels.add(row["semel"])
        refresh_top_props(p, row)
    rep("feature->row matching: " + json.dumps(dict(stats), ensure_ascii=False))
    for s in skel_matches:
        rep(f"   skeleton match (review): {s}")
    for u in unmatched:
        rep(f"   UNMATCHED feature left as-is: {u}")

    # --- 3: add features for polygon-less localities ---
    poly_by_semel = {}
    for path in POLY_PATHS:
        try:
            g = json.load(open(path, encoding="utf-8"))
        except FileNotFoundError:
            continue
        for f in g["features"]:
            sm = int(f["properties"]["semel"])
            poly_by_semel.setdefault(sm, f)   # first file wins
    added = []
    for r in loc:
        sm = r.get("semel")
        if not sm or sm in covered_semels or sm not in poly_by_semel:
            continue
        src = poly_by_semel[sm]
        props = {
            "name": r["name"],
            "name_en": src["properties"].get("name_en"),
            "type": "יישוב",
            "matched": True,
            "semel": sm,
            "src": "gapfix_statarea_2022",
        }
        refresh_top_props(props, r)
        geo["features"].append({"type": "Feature", "geometry": src["geometry"], "properties": props})
        covered_semels.add(sm)
        latest = sorted(r["data"], key=int)[-1]
        added.append((r["data"][latest].get("bzb") or 0, r["name"], sm))
    added.sort(reverse=True)
    rep(f"features added from CBS polygon layer: {len(added)}")
    for b, n, sm in added:
        rep(f"   + {n} (semel {sm}, latest bzb={b})")

    # remaining off-map rows (no polygon anywhere)
    off = [r["name"] for r in loc if (r.get("semel") not in covered_semels)]
    rep(f"rows still off-map (no CBS polygon / pseudo rows): {len(off)}")
    for n in off:
        rep(f"   off-map: {n}")

    json.dump(geo, open(GEO_PATH, "w", encoding="utf-8"), ensure_ascii=False)
    rep(f"written: {GEO_PATH} ({len(geo['features'])} features)")
    open(REPORT_PATH, "w", encoding="utf-8").write("\n".join(report))
    print(f"done; report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
