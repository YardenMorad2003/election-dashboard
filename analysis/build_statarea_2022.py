# -*- coding: utf-8 -*-
"""
build_statarea_2022.py — 2022 stat-area layer: K25 votes × CBS 2022 census.

Inputs (snapshotted into analysis/statarea_inputs/ on first run):
- k25_demo_join_v11.csv (elections-merge): K25 party votes aggregated per
  stat-area. Provenance: 32,705 polling stations, 98% geocoded (Harel Cain's
  station list) -> point-in-polygon into the CBS 2022 stat-area layer ->
  votes summed per YISHUV_STAT_2022 ("stat22" = semel*10000 + stat area).
  2,408 stat-areas, 4.19M valid votes = 97.3% of geographic K25 votes
  (double-envelope votes have no geography by design).
- cbs_census_2022_statarea.csv (data.gov.il resource 9a9e085f, CBS 2022
  census): 2,193 stat-area rows + 1,185 locality rows. Small localities have
  no SA breakdown -> the locality row doubles as the (single) SA's census.
  StatAreaCmb like "3+1" marks suppressed SAs merged into a combined row —
  each member SA is mapped to that combo row (census_src='combo').

Outputs:
- data/statarea_2022.json  — one record per stat-area: votes, party pcts,
  bloc pcts (project taxonomy incl. opposition_right), census dims, join meta.
- data/statarea_2022_geo.json — slimmed polygons (shapely-simplified,
  5-decimal coords) with {id, semel, sa, name, name_en} properties only;
  the page joins to the data JSON by id at runtime (numeric key, no names).

Run: python -X utf8 analysis/build_statarea_2022.py
Report: analysis/statarea_build_report.txt
"""
import csv
import json
import os
import shutil
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EM = r"C:\Users\yarde\elections-merge"
GEOJSON_SRC = r"C:\Users\yarde\Downloads\statistical_areas_2022.geojson"
SNAP = os.path.join(HERE, "statarea_inputs")
REPORT = os.path.join(HERE, "statarea_build_report.txt")

BLOCS = ["right", "haredi", "center", "left", "arab", "opposition_right"]
META_COLS = {"stat22", "eligible", "voted", "invalid", "valid", "n_ballots",
             "turnout", "LocNameHeb", "LocalityCode"}

CENSUS_KEEP = [
    ("pop_approx", "pop"), ("pop_density", "density"),
    ("ReligionHeb", "religion"), ("hh_MidatDatiyut", "datiyut"),
    ("age_median", "age_med"), ("age0_19_pcnt", "age0_19"), ("age65_pcnt", "age65"),
    ("AcadmCert_pcnt", "acad"), ("employeesAnnual_medWage", "med_wage"),
    ("EmployeesWage_decile9Up", "top2dec"), ("WrkY_pcnt", "work"),
    ("israel_pcnt", "orig_il"), ("europe_pcnt", "orig_eur"), ("asia_pcnt", "orig_asia"),
    ("africa_pcnt", "orig_afr"), ("america_pcnt", "orig_am"),
    ("aliya2002_pcnt", "aliya02"), ("ChldBorn_avg", "chld"), ("size_avg", "hh_size"),
    ("own_pcnt", "own"), ("rent_pcnt", "rent"), ("Vehicle0_pcnt", "no_car"),
]

report = []


def rep(s=""):
    report.append(s)
    print(s)


def num(x):
    if x is None or x == "":
        return None
    try:
        f = float(x)
        return int(f) if f == int(f) and abs(f) < 1e9 else round(f, 2)
    except ValueError:
        return None


def main():
    os.makedirs(SNAP, exist_ok=True)
    for src, name in [(os.path.join(EM, "output", "k25_demo_join_v11.csv"), "k25_demo_join_v11.csv"),
                      (os.path.join(EM, "data", "cbs_census_2022_statarea.csv"), "cbs_census_2022_statarea.csv")]:
        dst = os.path.join(SNAP, name)
        if not os.path.exists(dst):
            shutil.copyfile(src, dst)
            rep(f"snapshotted {name}")

    pn = json.load(open(os.path.join(ROOT, "data", "parties_national.json"), encoding="utf-8"))
    bloc_of = {p["code"]: p["bloc"] for p in pn["25"]["party_list"]}

    # ---- census index ----
    census_sa = {}       # stat22 -> row (direct or combo member)
    census_src = {}      # stat22 -> 'sa' | 'combo'
    census_loc = {}      # semel -> locality row
    with open(os.path.join(SNAP, "cbs_census_2022_statarea.csv"), encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            lc, sa = r["LocalityCode"], r["StatArea"]
            if lc and not sa:
                census_loc[int(float(lc))] = r
            elif lc and sa:
                semel = int(float(lc))
                members = r["StatAreaCmb"].split("+") if r["StatAreaCmb"] else [sa]
                for m in members:
                    try:
                        sid = semel * 10000 + int(float(m))
                    except ValueError:
                        continue
                    census_sa[sid] = r
                    census_src[sid] = "sa" if len(members) == 1 else "combo"
    rep(f"census index: {len(census_sa)} stat22 keys "
        f"({sum(1 for v in census_src.values() if v=='combo')} via combos), "
        f"{len(census_loc)} locality rows")

    # ---- votes per stat-area ----
    out = {}
    skipped = []
    with open(os.path.join(SNAP, "k25_demo_join_v11.csv"), encoding="utf-8-sig") as f:
        rdr = csv.DictReader(f)
        hdr = rdr.fieldnames
        # party count columns sit strictly between 'valid' and 'n_ballots'
        party_codes = hdr[hdr.index("valid") + 1:hdr.index("n_ballots")]
        unmapped = [c for c in party_codes if not bloc_of.get(c)]
        rep(f"party columns: {len(party_codes)} ({len(unmapped)} sub-threshold, counted as 'other': "
            + ",".join(unmapped) + ")")
        for r in rdr:
            try:
                sid = int(r["stat22"])
                semel, sa = divmod(sid, 10000)
                assert semel > 0 and sa > 0
            except (ValueError, AssertionError):
                skipped.append((r["stat22"], r["valid"]))
                continue
            valid = int(float(r["valid"]))
            if valid <= 0:
                skipped.append((r["stat22"], r["valid"]))
                continue
            votes = {c: int(float(r[c] or 0)) for c in party_codes}
            bv = {b: 0 for b in BLOCS}
            other = 0
            for c, v in votes.items():
                b = bloc_of.get(c)
                if b:
                    bv[b] += v
                else:
                    other += v
            blocs = {b: round(100 * bv[b] / valid, 2) for b in BLOCS}
            blocs["rh"] = round(100 * (bv["right"] + bv["haredi"]) / valid, 2)
            blocs["cla"] = round(100 * (bv["center"] + bv["left"] + bv["arab"] + bv["opposition_right"]) / valid, 2)
            parties = {c: round(100 * v / valid, 2) for c, v in votes.items() if v / valid >= 0.005}
            winner = max(votes, key=votes.get)
            rec = {
                "semel": semel, "sa": sa, "loc": r["LocNameHeb"] or None,
                "eligible": int(float(r["eligible"])), "voted": int(float(r["voted"])),
                "valid": valid, "n_ballots": int(float(r["n_ballots"])),
                "turnout": round(100 * float(r["voted"]) / float(r["eligible"]), 1) if float(r["eligible"]) else None,
                "winner": winner,
                "blocs": blocs, "parties": parties,
            }
            # census join: direct SA/combo, else locality fallback
            crow = census_sa.get(sid)
            src = census_src.get(sid)
            if crow is None:
                crow = census_loc.get(semel)
                src = "locality" if crow is not None else None
            if crow is not None:
                rec["census"] = {short: (crow[col] if col in ("ReligionHeb", "hh_MidatDatiyut") else num(crow[col]))
                                 for col, short in CENSUS_KEEP}
                rec["census_src"] = src
            out[sid] = rec

    # census-only stat-areas (no mapped votes): keep them so demographic modes
    # can still color them; the page shows "no vote data" in their panel.
    n_census_only = 0
    for sid, crow in census_sa.items():
        if sid in out:
            continue
        semel, sa_num = divmod(sid, 10000)
        out[sid] = {"semel": semel, "sa": sa_num, "loc": None,
                    "census": {short: (crow[col] if col in ("ReligionHeb", "hh_MidatDatiyut") else num(crow[col]))
                               for col, short in CENSUS_KEEP},
                    "census_src": census_src.get(sid)}
        n_census_only += 1
    rep(f"census-only stat-areas added (no mapped votes): {n_census_only}")

    n_census = sum(1 for v in out.values() if "census" in v)
    by_src = defaultdict(int)
    for v in out.values():
        by_src[v.get("census_src")] += 1
    tot_valid = sum(v.get("valid") or 0 for v in out.values())
    rep(f"stat-areas with votes: {sum(1 for v in out.values() if 'valid' in v)} | "
        f"skipped rows: {len(skipped)} {skipped}")
    rep(f"census joined: {n_census}/{len(out)} ({json.dumps(dict(by_src))})")
    rep(f"total valid votes in layer: {tot_valid:,}")

    # locality names fallback: fill loc from geojson later if empty
    data_obj = {
        "meta": {
            "built": "2026-07-04",
            "election": "25",
            "coverage_note": ("4.19M valid votes = 97.3% of K25 geographic votes; "
                              "double-envelope votes (458,714) have no geography; "
                              "per-SA turnout uses only the eligible voters of matched ballots"),
            "source": "K25 ballots × geocoded stations (Cain) × CBS 2022 stat-areas; census resource 9a9e085f (data.gov.il)",
        },
        "areas": out,
    }

    # ---- geometry ----
    from shapely.geometry import shape, mapping
    rep("loading full geojson (126MB)...")
    g = json.load(open(GEOJSON_SRC, encoding="utf-8"))
    keep_ids = set(out) | set(census_sa)
    feats = []
    n_in = len(g["features"])
    for f in g["features"]:
        p = f["properties"]
        sid = p.get("YISHUV_STAT_2022")
        if sid is None or int(sid) not in keep_ids:
            continue
        sid = int(sid)
        geom = shape(f["geometry"]).simplify(0.0003, preserve_topology=True)
        gj = mapping(geom)

        def rnd(coords):
            if isinstance(coords[0], (int, float)):
                return [round(coords[0], 5), round(coords[1], 5)]
            return [rnd(c) for c in coords]
        gj = {"type": gj["type"], "coordinates": rnd(gj["coordinates"])}
        name = p.get("SHEM_YISHUV")
        if sid in out and not out[sid].get("loc"):
            out[sid]["loc"] = name
        feats.append({"type": "Feature",
                      "properties": {"id": sid, "semel": int(p["SEMEL_YISHUV"]),
                                     "sa": sid % 10000, "name": name,
                                     "name_en": p.get("SHEM_YISHUV_ENGLISH")},
                      "geometry": gj})
    rep(f"geometry: kept {len(feats)}/{n_in} features")

    data_path = os.path.join(ROOT, "data", "statarea_2022.json")
    geo_path = os.path.join(ROOT, "data", "statarea_2022_geo.json")
    json.dump(data_obj, open(data_path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    json.dump({"type": "FeatureCollection", "features": feats},
              open(geo_path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    rep(f"wrote {data_path} ({os.path.getsize(data_path):,} bytes)")
    rep(f"wrote {geo_path} ({os.path.getsize(geo_path):,} bytes)")
    open(REPORT, "w", encoding="utf-8").write("\n".join(report))


if __name__ == "__main__":
    main()
