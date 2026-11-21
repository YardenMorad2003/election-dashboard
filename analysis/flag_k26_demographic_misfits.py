# -*- coding: utf-8 -*-
"""
flag_k26_demographic_misfits.py — polling sites whose VOTE does not fit the place they
were put (owner rule, 2026-11-21: "if something doesn't make sense in terms of
demographics, check it"). Motivating miss: בי"ס מוריה, Haifa — 57% Joint List, placed on
the Carmel (inherited from the 2022 layer, which geocoded the NAME to Moriah Blvd)
instead of downtown.

Per located site (semel + venue + address) compute the vote profile
(arab / haredi / right / other %) and flag when ANY of:
  census   Arab-majority site (>=50%) in an SA whose 2022-census religion is Jewish, or
           a Jewish site (arab < 10%) in an Arab SA, or a Haredi site (>=40%) in a
           secular SA (datiyut חילוני) with the SA's other sites non-Haredi
  hood     profile differs by >= 35 pt (max component) from the 6 nearest other sites
           within 1.5 km (>= 3 needed)
  registry the school registry has this exact school (core name + sibling letter, one
           place) >= 0.5 km from our point

Output: analysis/k26_misfit_flags.json  (list of dicts; consumed by the resolver / web check)
        analysis/k26_misfit_flags.txt   (readable)
Run: python -X utf8 analysis/flag_k26_demographic_misfits.py
"""
import collections
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAP = os.path.join(HERE, "statarea_inputs")
EM = r"C:\Users\yarde\elections-merge\data"
sys.path.insert(0, HERE)
from build_venue_dots import canon_ballot  # noqa: E402
from audit_k26_locations import name_key, dkm  # noqa: E402


def main():
    pn = json.load(open(os.path.join(ROOT, "data", "parties_national.json"), encoding="utf-8"))["26"]
    bloc = {p["code"]: p["bloc"] for p in pn["party_list"]}
    votes = {}
    with open(os.path.join(EM, "knesset26_ballots.csv"), encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            v = collections.Counter()
            for c, b in bloc.items():
                if c in r:
                    v[{"arab": "arab", "haredi": "haredi", "right": "right"}.get(b, "other")] += int(r[c] or 0)
            votes[(r["סמל ישוב"].strip(), canon_ballot(r["קלפי"].strip()))] = (int(r["כשרים"] or 0), v)
    sa_of = {(r["semel"], r["ballot"]): r["stat22"] for r in
             csv.DictReader(open(os.path.join(SNAP, "ballot_stat22_26.csv"), encoding="utf-8-sig"))}
    areas = json.load(open(os.path.join(ROOT, "data", "statarea_k26.json"), encoding="utf-8"))["areas"]

    sites = {}
    for r in csv.DictReader(open(os.path.join(SNAP, "k26_ballot_coords.csv"), encoding="utf-8-sig")):
        if not r["lat"]:
            continue
        k = (r["semel"], r["venue"], r["addr"])
        s = sites.setdefault(k, {"sem": r["semel"], "sett": r["sett"], "venue": r["venue"], "addr": r["addr"],
                                 "pt": (float(r["lat"]), float(r["lng"])), "src": r["coord_src"],
                                 "valid": 0, "v": collections.Counter(), "sa": sa_of.get((r["semel"], r["ballot"]), "")})
        n, v = votes.get((r["semel"], r["ballot"]), (0, {}))
        s["valid"] += n; s["v"].update(v)
    by_city = collections.defaultdict(list)
    for s in sites.values():
        if s["valid"] >= 150:
            s["p"] = {k: 100 * s["v"][k] / s["valid"] for k in ("arab", "haredi", "right")}
            by_city[s["sem"]].append(s)

    # registry (strict)
    bbox = {}
    for f in json.load(open(os.path.join(ROOT, "data", "statarea_2022_geo.json"), encoding="utf-8"))["features"]:
        sm = str(f["properties"]["semel"]); g = f["geometry"]
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

    def moe(sem, venue):
        core, suf = name_key(venue)
        b = bbox.get(sem)
        if not b or len(core) < 3:
            return None
        ct = set(core.split())
        c = [(la, ln) for (cn, cs), la, ln in registry
             if (cn == core or (len(ct) >= 2 and ct <= set(cn.split()))) and (not suf or cs == suf)
             and b[0] - .005 <= la <= b[1] + .005 and b[2] - .005 <= ln <= b[3] + .005]
        return c[0] if c and all(dkm(c[0], x) <= 0.3 for x in c) else None

    def hood(s, pt=None):
        pt = pt or s["pt"]
        near = sorted(((dkm(pt, o["pt"]), i) for i, o in enumerate(by_city[s["sem"]])
                       if o is not s and dkm(o["pt"], s["pt"]) > 0.02))
        sel = [by_city[s["sem"]][i] for d, i in near[:6] if d <= 1.5]
        if len(sel) < 3:
            return None
        w = sum(o["valid"] for o in sel)
        return {k: sum(o["p"][k] * o["valid"] for o in sel) / w for k in ("arab", "haredi", "right")}

    # official-address geocodes (building, or a street <= 1.2 km long: see geocode_k26_addresses.py)
    geo = {}
    _p = os.path.join(SNAP, "k26_address_geocodes.json")
    if os.path.exists(_p):
        for k, v in json.load(open(_p, encoding="utf-8")).items():
            if v.get("src") in (None, "none"):
                continue
            kind, sp = v.get("kind", "highway"), v.get("spread")
            if not kind.startswith("highway"):
                geo[k] = ((v["lat"], v["lng"]), "building")
            elif sp is not None and sp <= 0.5:
                geo[k] = ((v["lat"], v["lng"]), "street")
    HAND = ("addr_fix", "name_fix", "override")
    flags = []
    for sem, ss in by_city.items():
        for s in ss:
            why = []
            cen = (areas.get(s["sa"]) or {}).get("census") or {}
            rel, dat = cen.get("religion") or "", cen.get("datiyut") or ""
            others = [o for o in ss if o is not s and o["sa"] == s["sa"]]
            if s["p"]["arab"] >= 50 and rel.startswith("יהוד"):
                why.append(f"census: {s['p']['arab']:.0f}% Arab-list vote in a Jewish area")
            # Druze localities vote for Jewish-led lists: not a misfit, so only Muslim/Christian/Arab areas count
            if s["p"]["arab"] < 10 and rel.startswith(("מוסלמ", "נוצר", "ערב")):
                why.append(f"census: Jewish vote in an area whose census religion is {rel}")
            if s["p"]["haredi"] >= 40 and dat == "חילוני" and all(o["p"]["haredi"] < 20 for o in others):
                why.append(f"census: {s['p']['haredi']:.0f}% Haredi vote in a secular area")
            h = hood(s)
            if h:
                d = max(abs(s["p"][k] - h[k]) for k in h)
                if d >= 35:
                    why.append(f"neighbours: differs {d:.0f} pt from the nearest sites")
            m = moe(sem, s["venue"])
            if m and dkm(s["pt"], m) >= 0.5:
                why.append(f"registry: same-name school {dkm(s['pt'], m):.1f} km away")
            if why:
                rec = {"sem": sem, "sett": s["sett"], "venue": s["venue"], "addr": s["addr"], "src": s["src"],
                       "lat": s["pt"][0], "lng": s["pt"][1], "valid": s["valid"],
                       "profile": {k: round(v, 1) for k, v in s["p"].items()}, "why": why,
                       "moe": [round(m[0], 6), round(m[1], 6)] if m else None}
                if m:
                    hm = hood(s, m)
                    if h and hm:
                        rec["fit_now"] = round(max(abs(s["p"][k] - h[k]) for k in h), 1)
                        rec["fit_moe"] = round(max(abs(s["p"][k] - hm[k]) for k in hm), 1)
                g = geo.get(f"{sem}|{s['addr']}|{s['venue']}")
                if g:
                    rec["geo"] = [round(g[0][0], 6), round(g[0][1], 6)]
                    rec["geo_kind"] = g[1]
                    rec["geo_km"] = round(dkm(s["pt"], g[0]), 2)
                    hg = hood(s, g[0])
                    if h and hg:
                        rec["fit_now"] = round(max(abs(s["p"][k] - h[k]) for k in h), 1)
                        rec["fit_geo"] = round(max(abs(s["p"][k] - hg[k]) for k in hg), 1)
                # ---- verdict: move only on two independent agreeing sources ----
                fn = rec.get("fit_now")
                demo = any(w.startswith(("census", "neighbours")) for w in why)
                better = lambda x: fn is not None and x is not None and fn - x >= 15 and x <= 25
                if s["src"] in HAND:
                    rec["verdict"] = "review (hand-verified point, not auto-changed)"
                elif m and g and dkm(m, g[0]) <= 0.4 and dkm(s["pt"], m) >= 0.5:
                    rec["verdict"], rec["to"] = "move: registry + official address agree", rec["moe"]
                elif m and dkm(s["pt"], m) >= 0.5 and better(rec.get("fit_moe")):
                    rec["verdict"], rec["to"] = "move: registry + vote fit", rec["moe"]
                elif g and rec["geo_km"] >= 0.5 and better(rec.get("fit_geo")):
                    rec["verdict"], rec["to"] = "move: official address + vote fit", rec["geo"]
                elif g and rec["geo_km"] <= 0.4:
                    rec["verdict"] = "cleared: official address confirms the point (real enclave)"
                elif demo:
                    rec["verdict"] = "web-check"
                else:
                    rec["verdict"] = "review (registry disagrees, nothing corroborates)"
                flags.append(rec)
    flags.sort(key=lambda r: (-len(r["why"]), -r["valid"]))
    json.dump(flags, open(os.path.join(HERE, "k26_misfit_flags.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, "k26_misfit_flags.txt"), "w", encoding="utf-8") as f:
        for r in flags:
            f.write(f"{r['sem']} {r['sett']} | {r['venue']} | {r['addr']} | {r['src']} | v={r['valid']} "
                    f"{r['profile']} | {'; '.join(r['why'])} | moe={r['moe']} geo={r.get('geo')} "
                    f"fit now {r.get('fit_now')} moe {r.get('fit_moe')} geo {r.get('fit_geo')} | {r['verdict']}\n")
    # cumulative overrides (never dropped: an overridden site stops being flagged on the next run)
    op = os.path.join(SNAP, "k26_site_overrides.json")
    ov = json.load(open(op, encoding="utf-8")) if os.path.exists(op) else {}
    for r in flags:
        if r.get("to"):
            ov.setdefault(r["sem"], {})[f"{r['venue']}@@{r['addr']}"] = [
                r["to"][0], r["to"][1], f"{r['verdict']} (was {r['src']}; {'; '.join(r['why'])})"]
    json.dump(ov, open(op, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump([r for r in flags if r["verdict"] == "web-check"],
              open(os.path.join(HERE, "k26_web_check_queue.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(collections.Counter(r["verdict"].split(":")[0].split(" (")[0] for r in flags))
    c = collections.Counter()
    for r in flags:
        for w in r["why"]:
            c[w.split(":")[0]] += 1
    print(len(flags), "flagged sites", dict(c), "| with 2+ signals:", sum(1 for r in flags if len(r["why"]) >= 2))


if __name__ == "__main__":
    main()
