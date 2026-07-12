# -*- coding: utf-8 -*-
"""
build_coords_18.py — STATAREA 2009 build steps 1-3.

Turns the venue_match_18_feasibility.py *counting* experiment into the real
artifact: a (lat,lng,coord_src) per K18 geographic ballot, ready for step-5 PIP.

Steps implemented (per STATAREA_2009_README.md):
  1. Normalization + settlement bridge (norm/canon_ballot verbatim from
     feasibility; bridge station-settlement-name -> semel; optional manual
     dictionary settlement_name_fixes_18.json).
  2. Venue assignment per K18 geographic ballot: fallback chain
     l18 -> l19 -> l25 -> l25+".1" -> l19+".1", then name-match into the
     same-semel station venue index (exact, then token-Jaccard >= 0.5),
     inheriting lat/lng + a precise/centroid quality flag.
  3. Neighbor imputation for multi-SA ballots still without coords: nearest
     matched ballot NUMBER in the same locality, tiered |dN|<=1 then <=2.

Single-SA localities (2008 layer) need no coords -> coord_src='single_sa'
(step 5 assigns them by semel directly).

Output: analysis/statarea_inputs/ballot_coords_18.csv
        + prints a coverage report; reproduces the feasibility category table
          as a sanity gate and computes the neighbor-availability figure
          (readme finding #6) that the feasibility script never produced.

Run: python -X utf8 analysis/build_coords_18.py
"""
import csv
import glob
import json
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = r"C:\Users\yarde\elections-merge\data"
SHP = glob.glob(r"C:\Users\yarde\Downloads\statistical_areas_2008\*\*_1335.shp")[0]
SNAP = os.path.join(HERE, "statarea_inputs")
FIXES = os.path.join(SNAP, "settlement_name_fixes_18.json")
OUT = os.path.join(SNAP, "ballot_coords_18.csv")

PRECISE_SRC = ("venue", "google_venue", "manual", "manual_correction")
GERESH = "'׳״‘’“”\"`"


def norm(s):
    if not s:
        return ""
    for ch in GERESH:
        s = s.replace(ch, "")
    s = re.sub(r"[()\-,./\\:;+]", " ", s)
    s = s.replace("יי", "י").replace("וו", "ו")  # יי->י, וו->ו
    return " ".join(s.split())


def jacc(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def canon_ballot(bal):
    try:
        f = float(bal)
        return str(int(f)) if f == int(f) else bal
    except ValueError:
        return bal


def rank(e):
    """donor/venue-entry quality: precise-with-coord > any-coord > nothing."""
    has = e["lat"] is not None
    return (e["precise"] and has, has)


def main():
    os.makedirs(SNAP, exist_ok=True)

    # ---- load ----
    b18 = json.load(open(rf"{DATA}\ballot_locations_18.json", encoding="utf-8"))
    b19 = json.load(open(rf"{DATA}\ballot_locations_19.json", encoding="utf-8"))
    b25 = json.load(open(rf"{DATA}\ballot_locations_25.json", encoding="utf-8"))
    sc = json.load(open(rf"{DATA}\station_coordinates.json", encoding="utf-8"))
    stations = sc["stations"]
    l18, l19 = b18["ballot_to_location"], b19["ballot_to_location"]
    l25 = {}
    for semel, s in b25["settlements"].items():
        for b in s["ballots"]:
            l25[f"{semel}:{b['ballot']}"] = b["location"]

    with open(rf"{DATA}\knesset18_ballots.csv", encoding="utf-8-sig") as fh:
        r18 = list(csv.DictReader(fh))
    with open(rf"{DATA}\knesset25_ballots.csv", encoding="utf-8-sig") as fh:
        r25 = list(csv.DictReader(fh))

    # ---- SA counts per semel from the 2008 layer (FIX #2: SEMEL_YISH > 0) ----
    import shapefile
    sf = shapefile.Reader(SHP, encoding="cp1255")
    sa_count = defaultdict(int)
    for rec in sf.iterRecords(fields=["SEMEL_YISH", "STAT08"]):
        if rec["SEMEL_YISH"] and rec["SEMEL_YISH"] > 0:
            sa_count[str(rec["SEMEL_YISH"])] += 1

    # ---- step 1: bridge normalized settlement name -> semel ----
    name_to_semel = {}
    for row in r25:
        name_to_semel[norm(row["שם ישוב"])] = row["סמל ישוב"].strip()
    for semel, s in b25["settlements"].items():
        name_to_semel.setdefault(norm(s["name"]), semel)
    # manual fixes (station spelling -> semel), if reviewed & written
    fixes = json.load(open(FIXES, encoding="utf-8")) if os.path.exists(FIXES) else {}
    for nm, semel in fixes.items():
        name_to_semel[norm(nm)] = str(semel)
    # manual coordinate corrections for mis-geocoded venues (semel -> venue -> [lat,lng])
    coord_fixes = {}
    _cf = os.path.join(SNAP, "station_coord_fixes.json")
    if os.path.exists(_cf):
        for sem, vmap in json.load(open(_cf, encoding="utf-8")).items():
            if sem.startswith("_"):
                continue
            for ven, ll in vmap.items():
                coord_fixes[(str(sem), norm(ven))] = (ll[0], ll[1])
    print(f"coord fixes loaded: {len(coord_fixes)}")

    # ---- official K18 per-kalpi addresses (CEC 2008-12-28 list) + geocodes ----
    # Period-true street addresses (make_k18_ballot_addresses.py) geocoded by
    # geocode_k18_addresses.py; the top non-manual coordinate source (2026-07-11).
    # Geocodes exist only for multi-SA-2008 localities (single-SA need no coords).
    addr18 = {}
    _a = os.path.join(SNAP, "k18_ballot_addresses.json")
    if os.path.exists(_a):
        addr18 = json.load(open(_a, encoding="utf-8"))
    addr_geo = {}
    _g = os.path.join(SNAP, "k18_address_geocodes.json")
    if os.path.exists(_g):
        addr_geo = json.load(open(_g, encoding="utf-8"))
    print(f"official addresses: {sum(len(v) for v in addr18.values()):,} kalpiot; "
          f"geocoded: {sum(1 for v in addr_geo.values() if v.get('src') != 'none')}/{len(addr_geo)}")

    # ---- venue index per semel WITH coords ----
    venues_by_semel = defaultdict(dict)   # semel -> {norm_venue: entry}
    unmapped = defaultdict(int)           # station settlement name -> #stations
    for st in stations.values():
        semel = name_to_semel.get(norm(st["settlement"]))
        if semel is None:
            unmapped[st["settlement"]] += 1
            continue
        v = norm(st.get("location") or "")
        if not v:
            continue
        entry = {"lat": st.get("lat"), "lng": st.get("lng"),
                 "precise": st.get("source") in PRECISE_SRC and st.get("lat") is not None}
        cur = venues_by_semel[semel].get(v)
        if cur is None or rank(entry) > rank(cur):
            venues_by_semel[semel][v] = entry

    print(f"station settlements unmapped: {len(unmapped)} "
          f"({sum(unmapped.values())} stations)")
    # propose a semel for each unmapped name from the K18-vintage settlement list
    b18names = {norm(nm): semel for semel, nm in b18["settlements"].items()}
    if unmapped:
        print("  proposed fixes (station spelling -> K18 semel via b18 name match):")
        for nm in sorted(unmapped, key=lambda n: -unmapped[n]):
            prop = b18names.get(norm(nm))
            # fall back to token-Jaccard against b18 names
            if prop is None:
                tn = set(norm(nm).split())
                best, bj = None, 0.0
                for bn, sem in b18names.items():
                    j = jacc(tn, set(bn.split()))
                    if j > bj:
                        best, bj = sem, j
                prop = f"{best}?j={bj:.2f}" if bj >= 0.5 else "UNRESOLVED"
            print(f"    {nm:32s} x{unmapped[nm]:<4d} -> {prop}")

    # ---- step 2: assign a venue coord to every geographic K18 ballot ----
    # rows kept for imputation & output: per (semel) list of ballot dicts
    per_semel = defaultdict(list)
    cat_votes = defaultdict(int)   # feasibility-parity category tally (by votes)
    cat_ct = defaultdict(int)
    geo_votes = 0
    for row in r18:
        semel = row["סמל ישוב"].strip()
        kosher = int(row["כשרים"] or 0)
        if semel == "0":
            continue  # double envelopes: no geography (FIX/trap #3)
        geo_votes += kosher
        b = canon_ballot(row["סמל קלפי"].strip())
        k = f"{semel}:{b}"
        venue = l18.get(k) or l19.get(k) or l25.get(k) or l25.get(k + ".1") or l19.get(k + ".1")
        single = sa_count.get(semel, 0) <= 1
        lat = lng = None
        coord_src = None
        cfix = coord_fixes.get((semel, norm(venue))) if venue else None
        ageo = None
        addr = addr18.get(semel, {}).get(b)
        if addr:
            ageo = addr_geo.get(f"{semel}|{' '.join(addr.split())}")
            if ageo and ageo.get("lat") is None:   # covers "none" and "none_retried"
                ageo = None
        if cfix:
            lat, lng = cfix
            coord_src = "venue"      # corrected precise coordinate (human-verified, beats all)
        elif single:
            coord_src = "single_sa"
        elif ageo and ageo.get("src") != "city":
            lat, lng = ageo["lat"], ageo["lng"]
            coord_src = "address"    # official CEC address, Nominatim-geocoded + polygon-validated
        else:
            vv = venues_by_semel.get(semel)
            hit = None
            if venue and vv:
                nv = norm(venue)
                hit = vv.get(nv)
                if hit is None:
                    tv = set(nv.split())
                    best, bj = None, 0.0
                    for cand, e in vv.items():
                        j = jacc(tv, set(cand.split()))
                        if j > bj:
                            best, bj = e, j
                    if bj >= 0.5:
                        hit = best
            if hit and hit["lat"] is not None:
                lat, lng = hit["lat"], hit["lng"]
                coord_src = "venue" if hit["precise"] else "centroid"
            elif ageo:
                # bare-city geocode (unnumbered address): coarser than a venue-name
                # match, so it only fills where the name match failed
                lat, lng = ageo["lat"], ageo["lng"]
                coord_src = "address_city"
        # feasibility-parity categorization for the sanity gate
        if single:
            cat = "single_sa"
        elif coord_src == "address":
            cat = "address"
        elif coord_src == "venue":
            cat = "precise"
        elif coord_src == "centroid":
            cat = "centroid_multi"
        elif coord_src == "address_city":
            cat = "address_city"
        elif not venue:
            cat = "noname_multi"
        else:
            cat = "nomatch_multi"
        cat_votes[cat] += kosher
        cat_ct[cat] += 1
        per_semel[semel].append({
            "semel": semel, "ballot": b, "kosher": kosher, "single": single,
            "coord_src": coord_src, "lat": lat, "lng": lng, "dN": "",
            "num": float(b) if re.match(r"^\d+(\.\d+)?$", b) else None,
        })

    # ---- feasibility-parity report (sanity gate: expect precise ~76.9%) ----
    print(f"\ngeographic votes: {geo_votes:,}")
    print(f"{'category':16s} {'ballots':>8s} {'votes':>11s} {'%geo':>7s}")
    usable = 0
    for cat in ("address", "precise", "single_sa", "centroid_multi", "address_city", "noname_multi", "nomatch_multi"):
        print(f"{cat:16s} {cat_ct[cat]:8d} {cat_votes[cat]:11,d} {cat_votes[cat]/geo_votes:7.1%}")
        if cat in ("address", "precise", "single_sa"):
            usable += cat_votes[cat]
    print(f"usable w/o imputation (address + precise + single_sa): {usable:,} = {usable/geo_votes:.1%}")

    # ---- step 3: neighbor imputation (multi-SA, no coords) ----
    imp_have1 = imp_have2 = imp_none = 0
    nv1 = nv2 = nvnone = 0  # votes
    imputed = 0
    for semel, ballots in per_semel.items():
        donors = [x for x in ballots if x["coord_src"] in ("address", "venue", "centroid")
                  and x["num"] is not None]
        for x in ballots:
            if x["single"] or x["coord_src"] is not None or x["num"] is None:
                continue
            # nearest donor by |dN|, tiered <=1 then <=2
            best, bd = None, 99
            for d in donors:
                dd = abs(x["num"] - d["num"])
                if dd < bd and dd > 0:
                    best, bd = d, dd
            if best and bd <= 2:
                if bd <= 1:
                    imp_have1 += 1; nv1 += x["kosher"]
                else:
                    imp_have2 += 1; nv2 += x["kosher"]
                x["lat"], x["lng"] = best["lat"], best["lng"]
                x["coord_src"] = "neighbor_impute"
                x["dN"] = int(bd) if bd == int(bd) else round(bd, 1)
                imputed += 1
            else:
                imp_none += 1; nvnone += x["kosher"]

    noimp_votes = nv1 + nv2 + nvnone
    if noimp_votes:
        print(f"\nneighbor imputation (multi-SA ballots lacking coords):")
        print(f"  votes needing coords: {noimp_votes:,}")
        print(f"  have neighbor |dN|<=1: {nv1:,} ({nv1/noimp_votes:.0%})  "
              f"cumulative <=2: {nv1+nv2:,} ({(nv1+nv2)/noimp_votes:.0%})  "
              f"[readme #6 target 81% / 91%]")
        print(f"  imputed {imputed} ballots; still uncovered: {nvnone:,} votes "
              f"({imp_none} ballots)")

    # ---- final coverage ----
    final_ok = 0
    by_src = defaultdict(int)
    for ballots in per_semel.values():
        for x in ballots:
            by_src[x["coord_src"]] += 1
            if x["coord_src"] in ("address", "venue", "single_sa", "centroid", "address_city", "neighbor_impute"):
                final_ok += x["kosher"]
    print(f"\nfinal coord_src distribution (ballots): {dict(by_src)}")
    print(f"final geographic coverage (has usable coord or single-SA): "
          f"{final_ok:,} = {final_ok/geo_votes:.1%} of geo votes")

    # ---- write ----
    with open(OUT, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["semel", "ballot", "kosher", "single_sa", "coord_src", "lat", "lng", "dN"])
        for ballots in per_semel.values():
            for x in ballots:
                w.writerow([x["semel"], x["ballot"], x["kosher"], int(x["single"]),
                            x["coord_src"] or "none", x["lat"] if x["lat"] is not None else "",
                            x["lng"] if x["lng"] is not None else "", x["dN"]])
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
