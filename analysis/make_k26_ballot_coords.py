# -*- coding: utf-8 -*-
"""
make_k26_ballot_coords.py — per-kalpi coordinates for K26 (27 Oct 2026).

Input: the official CEC K26 polling-station list
(statarea_inputs/k26_polling/polling_stations_k26.xlsx: semel, kalpi, rikuz
(site code), address, venue name, registered voters).

K26 has an official address file (like K25), so every kalpi carries its own
venue name + address. Coordinates are inherited from the verified K25 layer
(station_coordinates + all coord fixes) in descending order of evidence:

  addr_fix    K25 address-scoped fix ("venue@@addr") matches K26 venue+address
  k25_addr    same semel + same official address as a K25 kalpi
  name_fix    name-keyed coord fix (semel, venue)
  k25_name    same semel + same venue name as a K25 kalpi
  addr_geocode / moe  weak inherited point overruled by the official-address geocode and/or the
              Ministry of Education school registry (see cross-check in main())
  geocode*    new site geocoded by geocode_k26_addresses.py (address / street / venue)
  k25_rikuz   same semel + same site code, only where the code is proven stable
              in that settlement (see rikuz_stable below)
  k25_addr_amb  address string shared by several distant K25 buildings (village-name
              "addresses"), new venue name: modal K25 point (weak)
  k25_fuzzy   venue-name token Jaccard >= 0.5 inside the semel
  (none)      left blank: single-SA settlements are still placed by the builder

Outputs (statarea_inputs/):
  k26_ballot_addresses.json  {semel: {ballot: "street,num"}}
  k26_ballot_venues.json     {semel: {ballot: venue name}}
  k26_ballot_coords.csv      semel,ballot,lat,lng,coord_src,rikuz,venue,addr,bzb
  ../k26_coords_report.txt

Run: python -X utf8 analysis/make_k26_ballot_coords.py
"""
import collections
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(HERE, "statarea_inputs")
EM = r"C:\Users\yarde\elections-merge\data"
XLSX = os.path.join(SNAP, "k26_polling", "polling_stations_k26.xlsx")
sys.path.insert(0, HERE)
from build_venue_dots import norm, canon_ballot  # noqa: E402


def load_fix(fn, addr_scoped):
    out = {}
    p = os.path.join(SNAP, fn)
    if not os.path.exists(p):
        return out
    for sem, vmap in json.load(open(p, encoding="utf-8")).items():
        if sem.startswith("_"):
            continue
        for k, ll in vmap.items():
            if addr_scoped:
                ven, _, adr = k.partition("@@")
                out[(str(sem), norm(ven), norm(adr))] = (ll[0], ll[1])
            else:
                out[(str(sem), norm(k))] = (ll[0], ll[1])
    return out


def k25_reference():
    """Per-K25-kalpi resolved coordinate, mirroring build_statarea_modern (e=25)."""
    stations = json.load(open(os.path.join(EM, "station_coordinates.json"), encoding="utf-8"))["stations"]
    cain_norm = {}
    for k, stn in stations.items():
        sett, _, bal = k.rpartition("|")
        if stn.get("lat") is not None:
            cain_norm[(norm(sett), canon_ballot(bal))] = (stn["lat"], stn["lng"])
    coord_fixes = load_fix("station_coord_fixes.json", False)
    addr_fixes = load_fix("station_coord_fixes_k25_addr.json", True)
    addr25 = json.load(open(os.path.join(SNAP, "k25_ballot_addresses.json"), encoding="utf-8"))
    bl = json.load(open(os.path.join(EM, "ballot_locations_25.json"), encoding="utf-8"))["ballot_to_location"]
    rows = []
    with open(os.path.join(EM, "knesset25_ballots.csv"), encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            semel = r["סמל ישוב"].strip()
            if semel in ("0", "875", "9999", "99999"):
                continue
            bal = canon_ballot(r["קלפי"].strip())
            st = stations.get(f"{r['שם ישוב'].strip()}|{r['קלפי'].strip()}") or {}
            venue = st.get("location") or bl.get(f"{semel}:{bal}") or bl.get(f"{semel}:{bal}.1") or ""
            oaddr = addr25.get(semel, {}).get(bal, "")
            pt = None
            if venue and oaddr:
                pt = addr_fixes.get((semel, norm(venue), norm(oaddr)))
            if not pt and venue:
                pt = coord_fixes.get((semel, norm(venue)))
            if not pt and st.get("lat") is not None:
                pt = (st["lat"], st["lng"])
            if not pt:
                pt = cain_norm.get((norm(r["שם ישוב"]), bal))
            rows.append({"semel": semel, "ballot": bal, "venue": venue, "addr": oaddr,
                         "rikuz": canon_ballot(r["ריכוז"].strip()), "pt": pt,
                         "sett": r["שם ישוב"].strip()})
    return rows, coord_fixes, addr_fixes


def _spread_km(counter):
    pts = list(counter)
    la = [p[0] for p in pts]; ln = [p[1] for p in pts]
    return max((max(la) - min(la)) * 111.0, (max(ln) - min(ln)) * 94.0)


def mode(counter):
    return counter.most_common(1)[0][0]


def main():
    import openpyxl
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    ws = wb[wb.sheetnames[0]]
    k26 = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0 or row[3] is None:
            continue
        k26.append({"semel": str(int(float(row[3]))), "sett": str(row[4] or "").strip(),
                    "ballot": canon_ballot(str(row[5]).strip()), "rikuz": canon_ballot(str(row[6]).strip()),
                    "addr": str(row[7] or "").strip(), "venue": str(row[8] or "").strip(),
                    "bzb": int(float(row[12] or 0))})

    ref, coord_fixes, addr_fixes = k25_reference()
    by_addr = collections.defaultdict(collections.Counter)
    by_addr_name = collections.defaultdict(collections.Counter)
    by_name = collections.defaultdict(collections.Counter)
    by_rikuz = collections.defaultdict(collections.Counter)
    rikuz_addr25 = collections.defaultdict(set)      # (semel, rikuz) -> K25 norm addrs
    rikuz_name25 = collections.defaultdict(set)
    names_by_semel = collections.defaultdict(dict)
    for r in ref:
        if r["addr"]:
            rikuz_addr25[(r["semel"], r["rikuz"])].add(norm(r["addr"]))
        if r["venue"]:
            rikuz_name25[(r["semel"], r["rikuz"])].add(norm(r["venue"]))
        if not r["pt"]:
            continue
        pt = (round(r["pt"][0], 6), round(r["pt"][1], 6))
        if r["addr"]:
            by_addr[(r["semel"], norm(r["addr"]))][pt] += 1
            if r["venue"]:
                by_addr_name[(r["semel"], norm(r["addr"]), norm(r["venue"]))][pt] += 1
        if r["venue"]:
            by_name[(r["semel"], norm(r["venue"]))][pt] += 1
            names_by_semel[r["semel"]][norm(r["venue"])] = pt
        by_rikuz[(r["semel"], r["rikuz"])][pt] += 1

    # Is the site code (rikuz) a stable building id K25 -> K26? Test per settlement
    # on the codes we can check: K26 kalpi whose address or name is known in K25.
    chk = collections.defaultdict(lambda: [0, 0])    # semel -> [agree, total]
    for r in k26:
        key = (r["semel"], r["rikuz"])
        if key not in by_rikuz:
            continue
        a25, n25 = rikuz_addr25.get(key, set()), rikuz_name25.get(key, set())
        if not a25 and not n25:
            continue
        ok = (norm(r["addr"]) in a25) or (norm(r["venue"]) in n25)
        chk[r["semel"]][1] += 1
        chk[r["semel"]][0] += 1 if ok else 0
    tot_ok = sum(v[0] for v in chk.values()); tot_n = sum(v[1] for v in chk.values())
    rikuz_stable = {s for s, (a, n) in chk.items() if n >= 3 and a / n >= 0.9}

    # new sites geocoded by geocode_k26_addresses.py (hit validated inside the settlement)
    geocache = {}
    p = os.path.join(SNAP, "k26_address_geocodes.json")
    if os.path.exists(p):
        for k, v in json.load(open(p, encoding="utf-8")).items():
            if v.get("src") and v["src"] != "none":
                # precision: a non-highway hit is a building/place (precise); a highway hit is one
                # segment of the street, usable only if the street is short (spread <= 0.5 km).
                # Long-road hits (spread unknown or > 0.5 km) are NOT a location (Kiryat Ata lesson).
                kind = v.get("kind", "highway")
                spread = v.get("spread")
                if not kind.startswith("highway"):
                    tier = "geocode" if v["src"] != "venue" else "geocode_venue"
                elif spread is not None and spread <= 0.5:
                    tier = "geocode_street"
                elif spread is not None and spread <= 1.2:
                    # mid-length street: the middle segment is at most ~0.6 km off. Good enough to
                    # place an otherwise unlocated site (flagged), never to overrule another point.
                    tier = "geocode_street_mid"
                else:
                    tier = "long_street"
                geocache[k] = ((v["lat"], v["lng"]), tier)

    # ---- independent reference: Ministry of Education school registry (audit 2026-11-21) ----
    from audit_k26_locations import name_key, dkm
    bbox = {}
    for f in json.load(open(os.path.join(os.path.dirname(HERE), "data", "statarea_2022_geo.json"),
                            encoding="utf-8"))["features"]:
        sm = str(f["properties"]["semel"])
        g = f["geometry"]
        rings = g["coordinates"] if g["type"] == "Polygon" else [rr for pp in g["coordinates"] for rr in pp]
        xs = [x for rr in rings for x, _ in rr]; ys = [y for rr in rings for _, y in rr]
        b = bbox.get(sm); nb = (min(ys), max(ys), min(xs), max(xs))
        bbox[sm] = nb if not b else (min(b[0], nb[0]), max(b[1], nb[1]), min(b[2], nb[2]), max(b[3], nb[3]))
    registry = []
    for rr in json.load(open(os.path.join(SNAP, "moe_registry_cache.json"), encoding="utf-8")):
        if "גבוהה" in str(rr.get("acc", "")):
            try:
                registry.append((name_key(rr["name"]), float(rr["lat"]), float(rr["lng"])))
            except (TypeError, ValueError):
                pass
    moe_memo = {}

    def moe_point(sem, venue):
        """Registry point for a venue: the in-city schools whose core name EQUALS the venue's
        core name, and only if they all sit in one place (<= 300 m). Else None."""
        core, suf = name_key(venue)
        key = (sem, core, suf)
        if key not in moe_memo:
            b = bbox.get(sem); res = None
            if b and len(core) >= 3:
                # same core name; when the venue carries a sibling letter (א/ב/ג) only registry
                # schools with that letter count; without one, every sibling must be in one place
                # a registry name may add a network / city tag around the same name
                # ('עמל ליידי דייויס ת"א' for 'בי"ס ליידי דייויס', TLV 2026-11-21): accept it when the
                # venue's core has >= 2 words and all of them appear in the registry name
                ct = set(core.split())
                c = [(la, ln) for (cn, cs), la, ln in registry
                     if (cn == core or (len(ct) >= 2 and ct <= set(cn.split()))) and (not suf or cs == suf)
                     and b[0] - .005 <= la <= b[1] + .005 and b[2] - .005 <= ln <= b[3] + .005]
                if c and all(dkm(c[0], x) <= 0.3 for x in c):
                    res = c[0]
            moe_memo[key] = res
        return moe_memo[key]

    AGREE, FAR = 0.4, 0.5
    WEAK = ("k25_rikuz", "k25_addr_amb", "k25_fuzzy")
    decisions = []

    # confirmed site overrides (flag_k26_demographic_misfits.py / web check): {semel: {"venue@@addr": [lat, lng, why]}}
    overrides = {}
    _p = os.path.join(SNAP, "k26_site_overrides.json")
    if os.path.exists(_p):
        for sm_, vmap in json.load(open(_p, encoding="utf-8")).items():
            for k_, v_ in vmap.items():
                overrides[(sm_, k_)] = (v_[0], v_[1])
    out, src_bzb, src_n = [], collections.Counter(), collections.Counter()
    for r in k26:
        sem, nv, na = r["semel"], norm(r["venue"]), norm(r["addr"])
        pt, src = None, ""
        if nv and na and (sem, nv, na) in addr_fixes:
            pt, src = addr_fixes[(sem, nv, na)], "addr_fix"
        elif na and nv and (sem, na, nv) in by_addr_name:
            pt, src = mode(by_addr_name[(sem, na, nv)]), "k25_addr"
        elif na and len(by_addr.get((sem, na), ())) == 1:
            pt, src = mode(by_addr[(sem, na)]), "k25_addr"
        elif nv and (sem, nv) in coord_fixes:
            pt, src = coord_fixes[(sem, nv)], "name_fix"
        elif nv and (sem, nv) in by_name:
            pt, src = mode(by_name[(sem, nv)]), "k25_name"
        elif na and (sem, na) in by_addr and _spread_km(by_addr[(sem, na)]) <= 0.25:
            # same address string, several K25 points, all within 250 m: one campus
            pt, src = mode(by_addr[(sem, na)]), "k25_addr"
        elif sem in rikuz_stable and (sem, r["rikuz"]) in by_rikuz:
            pt, src = mode(by_rikuz[(sem, r["rikuz"])]), "k25_rikuz"
        elif na and (sem, na) in by_addr:
            # address string is not a real address (village / neighbourhood name shared
            # by several K25 buildings) and the venue name is new: modal point, weak
            pt, src = mode(by_addr[(sem, na)]), "k25_addr_amb"
        elif nv and names_by_semel.get(sem):
            tv, best, bj = set(nv.split()), None, 0.0
            for cand, cpt in names_by_semel[sem].items():
                cs = set(cand.split())
                j = len(tv & cs) / len(tv | cs)
                if j > bj:
                    best, bj = cpt, j
            if bj >= 0.5:
                pt, src = best, "k25_fuzzy"
        # ---- triangulate: inherited point (I) x official-address geocode (G) x school registry (M).
        # A point is only replaced when independent evidence contradicts it:
        #   verified K25 tiers  -> moved only if G (address-level) AND M agree with each other and
        #                          both sit >= 0.5 km from I
        #   weak tiers          -> kept if G or M confirms I; else G+M agreement, else the
        #                          official-address geocode, else left as is
        #   no inherited point  -> G, corrected to M when G is only street/venue level
        G, gsrc = geocache.get(f"{sem}|{r['addr']}|{r['venue']}", (None, ""))
        M = moe_point(sem, r["venue"])
        I, isrc = pt, src
        gm = G is not None and M is not None and dkm(G, M) <= AGREE
        long_g = gsrc == "long_street"
        if long_g and not gm:
            G = None            # a long-road segment is evidence only when the registry agrees with it
        why = ""
        if I is None:
            if M is not None and (G is None or gsrc != "geocode"):
                pt, src = M, "moe"
                why = ("registry school (long street, address not locatable)" if long_g
                       else "registry school preferred over street-level geocode" if G is not None
                       else "no address match; registry school")
            elif G is not None:
                pt, src = G, ("geocode_street" if long_g else gsrc)
            elif long_g:
                why = "NOT LOCATED: address is on a long road and no registry school matches"
        elif isrc in WEAK:
            g_ok = G is not None and dkm(I, G) <= AGREE
            m_ok = M is not None and dkm(I, M) <= AGREE
            if g_ok or m_ok:
                pass
            elif gm:
                pt, src, why = M, "moe", f"address geocode and registry agree, {dkm(I, M):.1f} km from {isrc} point"
            elif G is not None and gsrc in ("geocode", "geocode_street") and dkm(I, G) >= FAR:
                pt, src, why = G, "addr_geocode", f"official address geocodes {dkm(I, G):.1f} km from {isrc} point"
        else:
            if gm and dkm(I, G) >= FAR and dkm(I, M) >= FAR:
                pt, src, why = M, "moe", f"address geocode and registry agree, {dkm(I, M):.1f} km from {isrc} point"
        okey = (sem, f"{r['venue']}@@{r['addr']}")
        if okey in overrides:
            pt, src, why = overrides[okey], "override", ""
        if why:
            decisions.append((sem, r["sett"], r["venue"], r["addr"], isrc or "none", src, why))
        r["pt"], r["src"] = pt, src or "none"
        src_bzb[r["src"]] += r["bzb"]; src_n[r["src"]] += 1
        out.append(r)

    addrs, vens = {}, {}
    for r in out:
        if r["addr"]:
            addrs.setdefault(r["semel"], {})[r["ballot"]] = r["addr"]
        if r["venue"]:
            vens.setdefault(r["semel"], {})[r["ballot"]] = r["venue"]
    json.dump(addrs, open(os.path.join(SNAP, "k26_ballot_addresses.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    json.dump(vens, open(os.path.join(SNAP, "k26_ballot_venues.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(SNAP, "k26_ballot_coords.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["semel", "ballot", "lat", "lng", "coord_src", "rikuz", "venue", "addr", "bzb", "sett"])
        for r in out:
            la, ln = (f"{r['pt'][0]:.6f}", f"{r['pt'][1]:.6f}") if r["pt"] else ("", "")
            w.writerow([r["semel"], r["ballot"], la, ln, r["src"], r["rikuz"], r["venue"], r["addr"], r["bzb"], r["sett"]])

    tot = sum(src_bzb.values())
    lines = [f"K26 kalpiot in official list: {len(out):,}  registered: {tot:,}",
             f"site-code (rikuz) stability check: {tot_ok:,}/{tot_n:,} = {100*tot_ok/max(tot_n,1):.1f}% "
             f"of checkable kalpiot keep the K25 address or name; settlements passing (>=90%, n>=3): {len(rikuz_stable)}",
             "", "coordinate source        kalpiot   registered   share"]
    for s in ("override", "addr_fix", "k25_addr", "name_fix", "k25_name", "geocode", "geocode_street",
              "geocode_street_mid", "geocode_venue", "addr_geocode", "moe", "k25_rikuz", "k25_addr_amb", "k25_fuzzy", "none"):
        lines.append(f"  {s:<20} {src_n[s]:>8,} {src_bzb[s]:>12,} {100*src_bzb[s]/tot:>6.1f}%")
    none_by = collections.Counter()
    for r in out:
        if r["src"] == "none":
            none_by[r["semel"]] += r["bzb"]
    lines += ["", f"settlements with unplaced kalpiot: {len(none_by)}; top 25 by registered (semel: registered)"]
    lines += [f"  {s}: {n:,}" for s, n in none_by.most_common(25)]
    seen = set()
    lines += ["", "points changed by the address x registry cross-check (site: from -> to, reason)"]
    for d in decisions:
        if d[:4] not in seen:
            seen.add(d[:4])
            lines.append(f"  {d[0]} {d[1]} | {d[2]} | {d[3]} : {d[4]} -> {d[5]} ({d[6]})")
    lines.insert(len(lines) - len(seen) - 1, f"sites changed by cross-check: {len(seen)}")
    open(os.path.join(HERE, "k26_coords_report.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(l for l in lines))


if __name__ == "__main__":
    main()
