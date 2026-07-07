# -*- coding: utf-8 -*-
"""
build_venue_dots.py — per-election venue-point files for the statarea_map dots layer.

One dot per polling VENUE (building), aggregated over its ballots:
  data/venue_dots_k{16..25}.json
  {"meta": {...}, "venues": [[lat, lng, valid, "winner", winner_pct, rh_pct,
    n_ballots, "name", semel, turnout_pct|null, cla_pct, {party: pct}], ...]}
(turnout = venue voted/bzb; null for K16/K17 which have no bzb column.
 parties = top 8 codes at >=0.1%. Fields 0-8 are the original schema — the
 page's dots renderer destructures by index, appended fields are additive.)

Coordinate resolution (modern + 2008-era K19/K20): station_coord_fixes override
by (semel, norm(venue)) -> Cain direct (settlement|ballot) -> per-city venue-name
index (most common coord). K18 uses ballot_coords_18.csv; K16/K17 use the
address-geocoded ballot_stat95_*.csv coordinates.

Run: python -X utf8 analysis/build_venue_dots.py [16 17 18 ...]
"""
import json, os, re, csv, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAP = os.path.join(ROOT, "analysis", "statarea_inputs")
EM = r"C:\Users\yarde\elections-merge\data"
OUT = os.path.join(ROOT, "data")

GERESH = "'׳״‘’“”\"`"
def norm(s):
    if not s: return ""
    for ch in GERESH: s = s.replace(ch, "")
    s = re.sub(r"[()\-,./\\:;+]", " ", s)
    s = s.replace("יי", "י").replace("וו", "ו")
    return " ".join(s.split())

def canon_ballot(b):
    try:
        f = float(b)
        return str(int(f)) if f == int(f) else str(f)
    except ValueError:
        return str(b)

# ---- shared inputs -------------------------------------------------------
PN = json.load(open(os.path.join(ROOT, "data", "parties_national.json"), encoding="utf-8"))

fixes = {}
for sem, vmap in json.load(open(os.path.join(SNAP, "station_coord_fixes.json"), encoding="utf-8")).items():
    if sem.startswith("_"): continue
    for ven, ll in vmap.items():
        fixes[(str(sem), norm(ven))] = (ll[0], ll[1])

# K25 official per-kalpi addresses (make_k25_ballot_addresses.py) — the only
# field that can split same-name venues at different buildings (kashish class,
# 2026-07-06) — plus address-scoped coord fixes ("venue@@addr" keys, K25 only).
addr25 = {}
_p = os.path.join(SNAP, "k25_ballot_addresses.json")
if os.path.exists(_p):
    addr25 = json.load(open(_p, encoding="utf-8"))
addr_fixes = {}
_p = os.path.join(SNAP, "station_coord_fixes_k25_addr.json")
if os.path.exists(_p):
    for sem, vmap in json.load(open(_p, encoding="utf-8")).items():
        if sem.startswith("_"): continue
        for k, ll in vmap.items():
            ven, _, adr = k.partition("@@")
            addr_fixes[(str(sem), norm(ven), norm(adr))] = (ll[0], ll[1])

sc = json.load(open(os.path.join(EM, "station_coordinates.json"), encoding="utf-8"))["stations"]
cain_direct = {}                                 # (norm_sett, canon_ballot) -> (lat,lng)
cain_byname = collections.defaultdict(collections.Counter)   # (norm_sett, norm_loc) -> Counter{(lat,lng)}
for st in sc.values():
    la, ln = st.get("lat"), st.get("lng")
    if la is None or ln is None: continue
    ns = norm(st.get("settlement", ""))
    cain_direct[(ns, canon_ballot(st.get("ballot", "")))] = (la, ln)
    loc = norm(st.get("location") or "")
    if loc:
        cain_byname[(ns, loc)][(round(la, 6), round(ln, 6))] += 1

def read_ballot_csv(yr):
    """yield (semel, ballot_str, name, addr, {party: votes}, (bzb, voted))"""
    path = os.path.join(EM, f"knesset{yr}_ballots.csv")
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        rdr = csv.DictReader(fh)
        flds = rdr.fieldnames
        semcol = next((c for c in flds if "סמל" in c and "ישוב" in c and "בחירות" not in c), None)
        namecol = next((c for c in flds if "שם ישוב" in c), None)
        balcol = next(c for c in flds if "קלפי" in c and "ריכוז" not in c)
        meta = [c for c in flds if any(w in c for w in
                ["שם", "סמל", "קלפי", "בז", "בוחרים", "מצביעים", "פסולים", "כשרים", "ריכוז", "שופט", "ברזל", "ת. עדכון", "כתובת", "מקום"])]
        parties = [c for c in flds if c not in meta]
        addrcol = next((c for c in flds if "כתובת" in c), None)
        bzbcol = next((c for c in flds if "בז" in c), None)       # K16/17: absent
        votedcol = next((c for c in flds if "מצביע" in c), None)
        def iv(row, col):
            try:
                return int(float(row[col] or 0)) if col else 0
            except (ValueError, TypeError):
                return 0
        for row in rdr:
            sem = (row.get(semcol) or "").strip() if semcol else ""
            if sem:
                try:
                    sem = str(int(float(sem)))   # "28.0" -> "28" (old-CSV float hygiene)
                except (ValueError, TypeError):
                    continue
                if sem in ("0", "875", "9999", "99999"):   # double/external envelopes
                    continue          # (modern CSVs use the 9999/99999 pseudo-semel — found
                                      #  via validate_dots_vs_api.py, 2026-07-06)
            else:
                sem = None   # K17: no semel column — resolved by settlement name upstream
            b = (row.get(balcol) or "").strip()
            pv = {}
            for p in parties:
                try:
                    v = int(float(row[p] or 0))
                except (ValueError, TypeError):
                    continue
                if v: pv[p] = v
            yield (sem, canon_ballot(b), (row.get(namecol) or "").strip(),
                   (row.get(addrcol) or "").strip() if addrcol else "", pv,
                   (iv(row, bzbcol), iv(row, votedcol)))

def load_locnames(yr):
    """(semel:str) -> settlement display name; and ballot_to_location dict"""
    try:
        bl = json.load(open(os.path.join(EM, f"ballot_locations_{yr}.json"), encoding="utf-8"))
    except FileNotFoundError:
        return {}, {}
    setts = {str(k): (v.get("name") if isinstance(v, dict) else str(v)) for k, v in bl.get("settlements", {}).items()}
    return setts, bl.get("ballot_to_location", {})

def coords_from_csv(path, latf="lat", lngf="lng"):
    m = {}
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        for row in csv.DictReader(fh):
            try:
                la, ln = float(row[latf]), float(row[lngf])
            except (ValueError, TypeError, KeyError):
                continue
            m[(str(int(float(row["semel"]))), canon_ballot(row["ballot"]))] = (la, ln)
    return m

def collect_venues(yr):
    """Aggregate a year's ballots into polling venues with resolved coordinates.

    Returns (venues, tot_votes, dropped_votes): venues = list of dicts
    {sem:str, lat, lng, valid, pv:Counter, nb, name, sett} — only venues with a
    resolvable coordinate; dropped_votes = valid votes at venues with none.
    """
    setts, b2l = load_locnames(yr)
    era95 = yr in ("16", "17")
    csv_coords = {}
    if era95:
        csv_coords = coords_from_csv(os.path.join(SNAP, f"ballot_stat95_{yr}.csv"))
    elif yr == "18":
        csv_coords = coords_from_csv(os.path.join(SNAP, "ballot_coords_18.csv"))

    venues = collections.defaultdict(lambda: {"valid": 0, "pv": collections.Counter(),
                                              "coords": collections.Counter(), "nb": 0, "sett": "",
                                              "bzb": 0, "voted": 0})
    inv = {norm(v): k for k, v in setts.items() if v}

    # K25: venue names whose kalpiot span 2+ distinct official addresses get an
    # address-qualified key, so each building becomes its own venue (dot).
    multi_addr = set()
    if yr == "25" and addr25:
        peraddr = collections.defaultdict(set)
        for semb, ven in b2l.items():
            sm, _, bb = semb.partition(":")
            a = addr25.get(sm, {}).get(canon_ballot(bb))
            if ven and a:
                peraddr[(sm, norm(ven))].add(a)
        multi_addr = {k for k, s in peraddr.items() if len(s) > 1}

    tot_votes = 0
    for sem, b, settname, addr, pv, (bzb, voted) in read_ballot_csv(yr):
        if sem is None:
            sem = inv.get(norm(settname))
        if not sem or not pv: continue
        valid = sum(pv.values())
        tot_votes += valid
        vname = b2l.get(f"{sem}:{b}") or b2l.get(f"{sem}:{b}.0") or ""
        if not vname and era95 and addr:
            vname = addr
        oaddr = addr25.get(sem, {}).get(b, "") if yr == "25" else ""
        key = (sem, norm(vname) if vname else f"__{b}")
        if vname and oaddr and (sem, norm(vname)) in multi_addr:
            key = (sem, f"{norm(vname)}@@{norm(oaddr)}")
        # coordinate resolution
        pt = addr_fixes.get((sem, norm(vname), norm(oaddr))) if (vname and oaddr) else None
        if not pt and vname:
            pt = fixes.get((sem, norm(vname)))
        if not pt:
            pt = csv_coords.get((sem, b))
        if not pt:
            ns = norm(settname or setts.get(sem, ""))
            pt = cain_direct.get((ns, b)) or cain_direct.get((ns, b + ".0"))
            if not pt and vname:
                cnt = cain_byname.get((ns, norm(vname)))
                if cnt: pt = cnt.most_common(1)[0][0]
        v = venues[key]
        v["valid"] += valid
        v["pv"].update(pv)
        v["nb"] += 1
        v["bzb"] += bzb
        v["voted"] += voted
        v["sett"] = settname or setts.get(sem, "")
        if pt: v["coords"][(round(pt[0], 6), round(pt[1], 6))] += valid
        if not v.get("name") and vname: v["name"] = vname

    out, dropped_votes = [], 0
    for (sem, _), v in venues.items():
        if not v["coords"]:
            dropped_votes += v["valid"]
            continue
        (la, ln), _ = v["coords"].most_common(1)[0]
        out.append({"sem": sem, "lat": la, "lng": ln, "valid": v["valid"], "pv": v["pv"],
                    "nb": v["nb"], "name": v.get("name", ""), "sett": v["sett"],
                    "bzb": v["bzb"], "voted": v["voted"]})
    return out, tot_votes, dropped_votes

def build_year(yr):
    pn = PN.get(yr)
    bloc_of = {p["code"]: p.get("bloc") for p in pn["party_list"]} if pn else {}
    rh = {c for c, b in bloc_of.items() if b in ("right", "haredi")}
    vlist, tot_votes, dropped_votes = collect_venues(yr)
    out, placed = [], 0
    for v in vlist:
        win, wv = v["pv"].most_common(1)[0]
        rhv = sum(cnt for p, cnt in v["pv"].items() if p in rh)
        clav = sum(cnt for p, cnt in v["pv"].items()
                   if bloc_of.get(p) and bloc_of[p] not in ("right", "haredi"))
        turnout = round(100 * v["voted"] / v["bzb"], 1) if v["bzb"] else None
        parties = {p: round(100 * cnt / v["valid"], 1) for p, cnt in v["pv"].most_common(8)
                   if 100 * cnt / v["valid"] >= 0.1}
        placed += v["valid"]
        out.append([round(v["lat"], 5), round(v["lng"], 5), v["valid"], win,
                    round(100 * wv / v["valid"], 1), round(100 * rhv / v["valid"], 1),
                    v["nb"], v["name"], int(v["sem"]),
                    turnout, round(100 * clav / v["valid"], 1), parties])
    out.sort(key=lambda r: -r[2])
    meta = {"knesset": int(yr), "venues": len(out), "votes_placed": placed,
            "votes_total": tot_votes, "votes_dropped_nocoord": dropped_votes}
    path = os.path.join(OUT, f"venue_dots_k{yr}.json")
    json.dump({"meta": meta, "venues": out}, open(path, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"K{yr}: {len(out):,} venues, {placed:,}/{tot_votes:,} votes placed "
          f"({100*placed/tot_votes:.1f}%), dropped {dropped_votes:,} -> {os.path.basename(path)} "
          f"({os.path.getsize(path)//1024} KB)")

if __name__ == "__main__":
    years = sys.argv[1:] or ["16", "17", "18", "19", "20", "21", "22", "23", "24", "25"]
    for yr in years:
        build_year(yr)
