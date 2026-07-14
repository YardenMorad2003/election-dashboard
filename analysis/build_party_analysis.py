# -*- coding: utf-8 -*-
"""Build data/party_analysis.json: per-party deep analysis (K13-K25).

DATA MODEL (verified):
  * parties_by_locality.json[k][locality][code] = the party's LOCAL VOTE SHARE (%),
    NOT a vote count. Each locality's party values sum to ~100. THREE corrupt rows
    hold raw counts instead (double-space 'תל אביב  יפו', 'פוריה  כפר עבודה',
    'פוריה  נווה עובד'); detected by value-sum > 150 and dropped.
  * Real per-locality VALID-VOTE counts (weights + absolute-vote base) come from
    localities.json data[k].kosher_votes.
  * Socio metrics join the 201 socioeconomic municipalities via a conservative
    Hebrew name matcher. Two universes reported: ALL munis and JEWISH-majority
    (pct_jews>=70) — pooling Arab+Jewish munis confounds within-Jewish SES gradients
    (the handoff's mechanism analysis restricted to Jewish cities for this reason).

Ecological (locality-aggregate) — do not infer individual behavior. Socio subset
excludes regional councils (kibbutz/moshav/settlement selection bias).
"""
import sys, json, re, math
from collections import defaultdict

ROOT = r"C:/Users/yarde/Downloads/election-dashboard-extracted/election-dashboard-main"
def load(f): return json.load(open(f"{ROOT}/data/{f}", encoding="utf-8"))

pnat = load("parties_national.json")
pbl  = load("parties_by_locality.json")
loc  = load("localities.json")
soc  = load("socioeconomic.json")

# Meretz is coded מרץ (final tsadi) in the K14/K19 source files and מרצ everywhere
# else — same list; canonicalize in-memory so it doesn't split into two parties.
# Explicit alias only — do NOT blanket-normalize final letters: צף (K16) and צפ (K19)
# are different parties. dashboard.html keeps the raw codes and maps them per-pair.
CODE_ALIAS = {"מרץ": "מרצ"}
canon = lambda c: CODE_ALIAS.get(c, c)
for e in pnat.values():
    e["party_list"] = [dict(it, code=canon(it["code"])) for it in e["party_list"]]
    for f in ("national", "national_votes", "seats"):
        if f in e:
            e[f] = {canon(c): v for c, v in e[f].items()}

YEARS = sorted(set(pnat) & set(pbl), key=int)
YEAR_OF = {k: pnat[k]["year"] for k in pnat}

# ---------- conservative Hebrew name matcher ----------
FIN = {"ך":"כ","ם":"מ","ן":"נ","ף":"פ","ץ":"צ"}
def norm(s):
    s = re.sub(r"\([^)]*\)", "", s.strip())
    for ch in ['"', "״", "'", "׳"]:
        s = s.replace(ch, "")
    s = re.sub(r"[\s\-–־]+", "", s)
    s = "".join(FIN.get(c, c) for c in s)
    return s.replace("יי", "י").replace("וו", "ו")

ALIAS = {  # socio-name -> pbl-name (genuine alternate names, not spelling variants)
    "בית אריה-עופרים": "בית אריה",
    "ג'ש (גוש חלב)": "גוש חלב",
    "פקיעין (בוקייעה)": "פקיעין",
}

# ---------- clean per-locality party shares (drop corrupt raw-count rows) ----------
PBLC = {}
for k in YEARS:
    clean = {}
    for locname, d in pbl[k].items():
        s = sum(v for v in d.values() if isinstance(v, (int, float)))
        if s > 150:      # corrupt: raw counts mislabeled as a locality
            continue
        clean[locname] = {canon(c): v for c, v in d.items()}
    PBLC[k] = clean

# per-knesset normalized -> pbl-name (dedupe within knesset by higher party-sum)
PBL_NORM = {}
for k in YEARS:
    m = {}
    for locname, d in PBLC[k].items():
        s = sum(v for v in d.values() if isinstance(v, (int, float)))
        key = norm(locname)
        if key not in m or s > m[key][1]:
            m[key] = (locname, s)
    PBL_NORM[k] = {key: v[0] for key, v in m.items()}

# ---------- real valid-vote counts per locality per knesset (from localities.json) ----------
# keyed by normalized name; merge spelling-duplicate rows by max kosher_votes
LOCV = {k: {} for k in YEARS}
for x in loc:
    key = norm(x["name"])
    for k, d in x.get("data", {}).items():
        if k not in LOCV: continue
        kv = d.get("kosher_votes")
        if isinstance(kv, (int, float)) and kv > 0:
            if key not in LOCV[k] or kv > LOCV[k][key]:
                LOCV[k][key] = kv

def valid_votes(k, locname):
    return LOCV[k].get(norm(locname))

# ---------- socio field selection (latest snapshot) ----------
SOCIO_FIELDS = [
    ("socio_index_2021",              "מדד חברתי-כלכלי 2021",   "idx"),
    ("pct_academic_degree",           "% בעלי תואר אקדמי",      "%"),
    ("avg_years_schooling",           "ממוצע שנות לימוד",       "yr"),
    ("pct_families_4plus_children",   "% משפחות עם 4+ ילדים",   "%"),
    ("avg_monthly_income_per_capita", "הכנסה חודשית לנפש",      "₪"),
    ("median_age",                    "גיל חציוני",            "yr"),
    ("pct_income_support",            "% מקבלי הבטחת הכנסה",    "%"),
    ("dependency_ratio",              "יחס תלות",              "idx"),
]
def sval(row, field):
    v = row.get(field)
    return float(v) if isinstance(v, (int, float)) else None

def is_jewish(r):
    v = (r.get("religion") or {}).get("pct_jews")
    return isinstance(v, (int, float)) and v >= 70

# per-knesset one-to-one (socio_row, pbl_name) matches
def pbl_name_for(k, socio_name):
    if socio_name in PBLC[k]: return socio_name
    if socio_name in ALIAS and ALIAS[socio_name] in PBLC[k]: return ALIAS[socio_name]
    return PBL_NORM[k].get(norm(socio_name))
MUNI_MATCH = {k: [(r, pbl_name_for(k, r["name"])) for r in soc
                  if pbl_name_for(k, r["name"]) is not None] for k in YEARS}

# ---------- weighted stats ----------
def wmean(pairs):
    num = sum(v*w for v, w in pairs); den = sum(w for _, w in pairs)
    return num/den if den else None
def wpearson(xs, ys, ws):
    W = sum(ws)
    if W == 0: return None, 0
    mx = sum(w*x for x, w in zip(xs, ws))/W
    my = sum(w*y for y, w in zip(ys, ws))/W
    cov = sum(w*(x-mx)*(y-my) for x, y, w in zip(xs, ys, ws))
    vx  = sum(w*(x-mx)**2 for x, w in zip(xs, ws))
    vy  = sum(w*(y-my)**2 for y, w in zip(ys, ws))
    if vx <= 0 or vy <= 0: return None, len(xs)
    return cov/math.sqrt(vx*vy), len(xs)

def univ_stats(k, subset):
    """valid-vote-weighted electorate mean & SD per socio var over a muni subset."""
    stats = {}
    for field, *_ in SOCIO_FIELDS:
        pairs = []
        for r, pn in subset:
            vv = valid_votes(k, pn); val = sval(r, field)
            if vv and val is not None: pairs.append((val, vv))
        m = wmean(pairs); W = sum(w for _, w in pairs)
        sd = math.sqrt(sum(w*(v-m)**2 for v, w in pairs)/W) if (W and m is not None) else None
        stats[field] = (m, sd)
    return stats

def build_socio(subset, k, c):
    """Standardized voter profile + pop-weighted correlations over a muni subset."""
    stats = univ_stats(k, subset)
    profile, corr = [], []
    for field, label, unit in SOCIO_FIELDS:
        m, sd = stats[field]
        ppairs, xs, ys, ws = [], [], [], []
        for r, pn in subset:
            val = sval(r, field); vv = valid_votes(k, pn)
            if val is None or not vv: continue
            share = PBLC[k].get(pn, {}).get(c, 0) or 0
            av = share/100.0*vv                     # party's absolute votes in muni
            if av > 0: ppairs.append((val, av))
            xs.append(val); ys.append(share); ws.append(vv)
        pm = wmean(ppairs)
        d = (pm - m)/sd if (pm is not None and m is not None and sd) else None
        profile.append({"var": field, "label": label, "unit": unit,
                        "party": pm, "elec": m, "sd": sd, "d": d, "n": len(ppairs)})
        rr, n = wpearson(xs, ys, ws)
        corr.append({"var": field, "label": label, "r": rr, "n": n})
    npart = sum(1 for r, pn in subset if (PBLC[k].get(pn, {}).get(c, 0) or 0) > 0
                and valid_votes(k, pn))
    return profile, corr, npart

# ---------- party registry ----------
reg = defaultdict(lambda: {"name": {}, "bloc": {}, "seats": {}, "vote_pct": {}})
for k in YEARS:
    e = pnat[k]; seats = e.get("seats", {}); vpct = e.get("national", {})
    for it in e["party_list"]:
        c = it["code"]
        reg[c]["name"][k] = it["name"]; reg[c]["bloc"][k] = it["bloc"]
        reg[c]["seats"][k] = seats.get(c, 0); reg[c]["vote_pct"][k] = vpct.get(c)

MIN_STRONGHOLD_VOTES = 300   # ignore micro-localities in the "strongholds by share" list

def rnd(v, d=4):
    return None if v is None else round(v, d)

def election_snapshot(c, k):
    """Full per-election panel data for party c in knesset k: geography +
    socio profile/correlations (socio side = fixed modern snapshot)."""
    rows = []
    for locn, d in PBLC[k].items():
        if "מעטפות" in locn:      # external/soldier envelopes — not a geographic locality
            continue
        share = d.get(c, 0) or 0
        vv = valid_votes(k, locn)
        if vv is None: continue
        rows.append((locn, share, vv, share/100.0*vv))
    total_votes = sum(av for *_, av in rows)
    strongholds = sorted([r for r in rows if r[2] >= MIN_STRONGHOLD_VOTES],
                         key=lambda x: -x[1])[:14]
    contributors = sorted(rows, key=lambda x: -x[3])[:12]

    all_sub = MUNI_MATCH[k]
    jew_sub = [t for t in all_sub if is_jewish(t[0])]
    prof_all, corr_all, socio_n = build_socio(all_sub, k, c)
    prof_jew, corr_jew, socio_n_jew = build_socio(jew_sub, k, c)
    for pr in (prof_all, prof_jew):
        for e in pr:
            for f in ("party", "elec", "sd", "d"): e[f] = rnd(e[f])
    for co in (corr_all, corr_jew):
        for e in co: e["r"] = rnd(e["r"])

    relj, rela, relr = [], [], []
    cluster_w = defaultdict(float)
    for r, pn in all_sub:
        vv = valid_votes(k, pn)
        share = PBLC[k].get(pn, {}).get(c, 0) or 0
        av = (share/100.0*vv) if vv else 0
        if av <= 0: continue
        rel = r.get("religion") or {}
        if isinstance(rel.get("pct_jews"),(int,float)):    relj.append((rel["pct_jews"], av))
        if isinstance(rel.get("pct_arabs"),(int,float)):   rela.append((rel["pct_arabs"], av))
        if isinstance(rel.get("pct_russians"),(int,float)):relr.append((rel["pct_russians"], av))
        cl = r.get("socio_cluster_2021")
        if isinstance(cl,(int,float)): cluster_w[int(cl)] += av
    csum = sum(cluster_w.values())
    religion = {"pct_jews": rnd(wmean(relj), 2), "pct_arabs": rnd(wmean(rela), 2),
                "pct_russians": rnd(wmean(relr), 2)}
    cluster_dist = {str(cl): rnd(cluster_w[cl]/csum*100, 2) for cl in sorted(cluster_w)} if csum else {}

    return {
        "total_votes": rnd(total_votes, 1),
        "strongholds": [{"name": n, "share": s, "valid": vv, "votes": rnd(av, 1)}
                        for n, s, vv, av in strongholds],
        "contributors": [{"name": n, "share": s, "valid": vv, "votes": rnd(av, 1),
                          "pct_of_party": rnd(100.0*av/total_votes if total_votes else 0, 2)}
                         for n, s, vv, av in contributors],
        "socio_n": socio_n, "socio_n_jew": socio_n_jew,
        "profile": {"all": prof_all, "jewish": prof_jew},
        "corr": {"all": corr_all, "jewish": corr_jew},
        "religion": religion, "cluster_dist": cluster_dist,
    }

parties = []
for c, info in reg.items():
    contested = [k for k in YEARS if info["vote_pct"].get(k) is not None]
    if not contested: continue
    ref = max(contested, key=int)
    peak_seats = max(info["seats"].get(k, 0) for k in YEARS)

    trajectory = [{"k": k, "year": YEAR_OF[k], "seats": info["seats"].get(k, 0),
                   "vote_pct": info["vote_pct"].get(k), "name": info["name"].get(k),
                   "bloc": info["bloc"].get(k)}
                  for k in YEARS if info["vote_pct"].get(k) is not None]

    by_el = {k: election_snapshot(c, k) for k in contested}
    refsnap = by_el[ref]

    parties.append({
        "code": c, "name": info["name"].get(ref), "bloc": info["bloc"].get(ref),
        "name_history": info["name"], "bloc_history": info["bloc"],
        "peak_seats": peak_seats, "ref_k": ref, "ref_year": YEAR_OF[ref],
        "total_votes_ref": refsnap["total_votes"],
        "trajectory": trajectory,
        # ref-election panels kept top-level for backward compatibility
        "strongholds": refsnap["strongholds"], "contributors": refsnap["contributors"],
        "socio_n": refsnap["socio_n"], "socio_n_jew": refsnap["socio_n_jew"],
        "profile": refsnap["profile"], "corr": refsnap["corr"],
        "religion": refsnap["religion"], "cluster_dist": refsnap["cluster_dist"],
        "by_election": by_el,
    })

parties.sort(key=lambda p: -p["peak_seats"])

out = {
    "meta": {
        "years": YEARS, "year_of": YEAR_OF,
        "socio_fields": [{"var": f, "label": l, "unit": u} for f, l, u in SOCIO_FIELDS],
        "socio_snapshot": "latest (~2021 base fields, religion 2019, census 2022)",
        "socio_universe": len(soc),
        "caveats": [
            "מדדים אקולוגיים (רמת יישוב) — לא להסיק על מצביע יחיד (כשל אקולוגי).",
            "פרופיל חברתי-כלכלי מבוסס על 201 עיריות (ללא מועצות אזוריות → הטיית בחירה).",
            "מפלגות עוקבות לפי אות הרשימה; חלק מהאותיות עברו למפלגות-המשך (למשל כן).",
            "מתאמים ופרופיל משוקללים במספר הקולות הכשרים ביישוב.",
            "מתאם 'כל היישובים' מערבב יישובים יהודיים וערביים ולכן מבלבל מפלגות יהודיות — ראו טור 'יישובים יהודיים'.",
            "פרופיל מתוקנן = הפרש (מפלגה − ממוצע) ביחידות סטיית-תקן.",
            "בתצוגה לפי בחירות: המאפיינים החברתיים-כלכליים הם צילום עדכני קבוע (~2021, דת 2019) גם לבחירות היסטוריות — ההצבעה משתנה, מאפייני היישוב לא. פרשנות לאחור בזהירות.",
        ],
    },
    "parties": parties,
}
with open(f"{ROOT}/data/party_analysis.json", "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False)

sys.stdout.reconfigure(encoding="utf-8")
print(f"wrote data/party_analysis.json : {len(parties)} parties, K{YEARS[0]}-K{YEARS[-1]}")
for p in parties[:6]:
    top = p["contributors"][0] if p["contributors"] else {"name":"-","pct_of_party":0}
    print(f"  [{p['code']}] {p['name'][:14]:14s} ref=K{p['ref_k']} votes~{p['total_votes_ref']:>9,.0f} "
          f"| #1 contrib: {top['name']} {top['pct_of_party']:.1f}% | socioN {p['socio_n']}/{p['socio_n_jew']}")
