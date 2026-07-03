# -*- coding: utf-8 -*-
"""Build data/demographics_panel.json: Phase 3 — multi-year CBS demographics.

Pieces (all locality-level, joined to localities.json by a code->name bridge):
  1. Census panel 1972/1983/1995/2008 (mesukam1.xls inter-census sheet, 1,050 localities)
     + 2022 endpoint (elections-merge cbs_census_2022_statarea.csv locality rows).
  2. Authority socio-economic index series: clusters 2008/2013/2015(/2017/2019 big
     cities)/2021, index values 2013/2015/2021.
  3. Within-city SES dispersion of stat-area index values: official CBS tables
     (2008 tab02_05, 2019 T14) + computed weighted SD/IQR for 2008/2017/2019/2021,
     validated against the official ones. Indices are standardized PER VINTAGE, so
     cross-year comparison uses rel_sd = city wSD / national pooled wSD that year.
  4. Time-varying education gradient: per election K13-K25, bzb-weighted r and OLS
     slope of right_haredi_pct on census-interpolated %academics; panel bootstrap
     (B=1000, resample localities) CIs + linear trend of the gradient.
     Variant with x FIXED at 2008 (behavioral sorting on a frozen SES map).
  5. Dispersion-vs-political-sorting city link (K18 vs K25 distinctiveness).

Ecological throughout — locality aggregates, not individuals.
Run: python -X utf8 analysis/build_demographics_panel.py  (~1-2 min)
"""
import sys, json, re, math
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:/Users/yarde/Downloads/election-dashboard-extracted/election-dashboard-main"
DL   = r"C:/Users/yarde/Downloads"
RNG  = np.random.default_rng(20260702)
B    = 1000

def load(f): return json.load(open(f"{ROOT}/data/{f}", encoding="utf-8"))

# ---------------- name normalizer (same family as build_party_analysis) ----------------
FIN = {"ך":"כ","ם":"מ","ן":"נ","ף":"פ","ץ":"צ"}
def norm(s):
    s = re.sub(r"\([^)]*\)", "", str(s).strip())
    for ch in ['"', "״", "'", "׳", "*", "‎", "‏"]:
        s = s.replace(ch, "")
    s = re.sub(r"[\s\-–־]+", "", s)
    s = "".join(FIN.get(c, c) for c in s)
    return s.replace("יי", "י").replace("וו", "ו")
def skel(s):
    return re.sub(r"[וי]", "", norm(s))

ALIAS = {  # CBS name -> dashboard name (genuine renames/alternates, not spelling)
    "בית אריה-עופרים": "בית אריה",
    "ג'ש (גוש חלב)": "גוש חלב",
    "פקיעין (בוקייעה)": "פקיעין",
    "נוף הגליל": "נצרת עילית",
    "יהוד": "יהוד-מונוסון",
    "יהוד-נווה אפרים": "יהוד-מונוסון",
}

# ---------------- dashboard localities ----------------
loc = load("localities.json")
LOC = {}                                    # norm(name) -> locality record
for x in loc:
    key = norm(x["name"])
    if key not in LOC or x.get("elections_count", 0) > LOC[key].get("elections_count", 0):
        LOC[key] = x
SKEL_LOC = {}
for key, x in LOC.items():
    SKEL_LOC.setdefault(skel(x["name"]), []).append(key)

soc = load("socioeconomic.json")            # 201 munis, has authoritative code
SOC_BY_CODE = {int(r["code"]): r for r in soc if r.get("code")}

def match_name(cbs_name):
    """CBS Hebrew name -> dashboard locality name (or None)."""
    if cbs_name in ALIAS:
        k = norm(ALIAS[cbs_name])
        return LOC[k]["name"] if k in LOC else None
    k = norm(cbs_name)
    if k in LOC: return LOC[k]["name"]
    cands = SKEL_LOC.get(skel(cbs_name), [])
    if len(cands) == 1: return LOC[cands[0]]["name"]
    return None

BRIDGE = {}                                 # code -> dashboard name
BRIDGE_SRC = {}
def bridge_add(code, cbs_name, src):
    code = int(code)
    if code in BRIDGE: return
    # seed: socioeconomic.json names are already dashboard-compatible
    if code in SOC_BY_CODE:
        nm = match_name(SOC_BY_CODE[code]["name"])
        if nm: BRIDGE[code] = nm; BRIDGE_SRC[code] = "socio_seed"; return
    nm = match_name(cbs_name)
    if nm: BRIDGE[code] = nm; BRIDGE_SRC[code] = src

def num(v):
    try:
        f = float(v)
        return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None

# ================= 1. census panel =================
print("[1] census panel ...")
cmp_df = pd.read_excel(rf"{DL}/mesukam1.xls", sheet_name="השוואות_בין_מפקדים", header=None)
hdr = cmp_df.index[cmp_df[0] == "LocalityCode"][0]
eng = cmp_df.iloc[hdr].tolist()
COLM = {str(v): i for i, v in enumerate(eng) if isinstance(v, str)}
CEN_VARS = {  # short name -> mesukam english stem
    "acad": "AcadmCert_pcnt", "fert": "ChldBorn_avg", "noeduc": "NoEduc_pcnt",
    "educ8": "educ8_pcnt", "pop": "pop_sef_thou", "age65": "age65sef_pcnt",
    "worked_w": "Worked_w", "vehicle": "Vehicle1up_pcnt", "size": "size_avg",
}
CEN_YEARS = ["72", "83", "95", "08"]
CENSUS = {}                                  # code -> {"name":..., "1972": {...}, ...}
for _, row in cmp_df.iloc[hdr+1:].iterrows():
    code = num(row[0])
    if code is None: continue
    code = int(code)
    rec = {"cbs_name": str(row[1]).strip()}
    for yy in CEN_YEARS:
        yr = ("19" + yy) if yy != "08" else "2008"
        d = {}
        for k, stem in CEN_VARS.items():
            c = COLM.get(f"{stem}_{yy}")
            v = num(row[c]) if c is not None else None
            if v is not None: d[k] = v
        if d: rec[yr] = d
    CENSUS[code] = rec
    bridge_add(code, rec["cbs_name"], "census_cmp")
assert CENSUS[472]["2008"]["acad"] == 8.1, "spot-check Abu Ghosh 2008 acad"
print(f"    mesukam comparisons: {len(CENSUS)} localities")

# 2022 endpoint (locality-total rows: StatArea empty)
c22 = pd.read_csv(r"C:/Users/yarde/elections-merge/data/cbs_census_2022_statarea.csv")
locrows = c22[c22["LocalityCode"].notna() & c22["StatArea"].isna() & c22["StatAreaCmb"].isna()]
n22 = 0
REL22 = {}                                   # code -> (religion code, religiosity name)
for _, row in locrows.iterrows():
    code = int(row["LocalityCode"])
    d = {}
    for k, src in [("acad", "AcadmCert_pcnt"), ("fert", "ChldBorn_avg"),
                   ("age65", "age65_pcnt"), ("size", "size_avg"), ("pop", "pop_approx")]:
        v = num(row[src])
        if v is not None: d[k] = v if k != "pop" else v/1000.0   # pop in thousands like mesukam
    if d:
        CENSUS.setdefault(code, {"cbs_name": str(row["LocNameHeb"]).strip()})["2022"] = d
        n22 += 1
    REL22[code] = (num(row["religion"]), str(row.get("hh_MidatDatiyut_Name") or "").strip() or None)
    bridge_add(code, str(row["LocNameHeb"]).strip(), "census22")
assert abs(CENSUS[472]["2022"]["acad"] - 16.0) < 1e-9, "spot-check Abu Ghosh 2022 acad"
print(f"    2022 locality rows: {n22}")

# ================= 2. socio-index authority series =================
print("[2] socio-index series ...")
CL = {}                                      # code -> {vintage: cluster}
IV = {}                                      # code -> {vintage: index value}
def put(dic, code, vint, v):
    if v is None: return
    dic.setdefault(int(code), {})[vint] = v

t13f = pd.read_excel(rf"{DL}/t02 (1).xls", sheet_name="t02", header=None)          # 2013 (+2008)
for _, r in t13f.iloc[8:].iterrows():
    code = num(r[1])
    if code is None: continue
    put(IV, code, "2013", num(r[4])); put(CL, code, "2013", num(r[6])); put(CL, code, "2008", num(r[8]))
t15f = pd.read_excel(rf"{DL}/24_18_351t3.xls", sheet_name="table 3 לוח", header=None)  # 2015
for _, r in t15f.iloc[8:].iterrows():
    code = num(r[1])
    if code is None or num(r[4]) is None: continue
    put(IV, code, "2015", num(r[4])); put(CL, code, "2015", num(r[6]))
# big-city cluster vintages from the stat-area publications
def city_clusters(path, sheet, v_new, v_old, skiprows):
    df = pd.read_excel(path, sheet_name=sheet, header=None)
    for _, r in df.iloc[skiprows:].iterrows():
        code = num(r[1])
        if code is None or num(r[8]) is None: continue
        put(CL, code, v_new, num(r[4])); put(CL, code, v_old, num(r[5]))
    return df
t17f = city_clusters(rf"{DL}/24_20_403t3.xlsx", "Tab 1b upgrade", "2017", "2015", 9)
t19f = city_clusters(rf"{DL}/T13 (1).xlsx", "לוח 13", "2019", "2017", 10)
t21f = city_clusters(rf"{DL}/24_24_230t4.xlsx", "לוח ג table C", "2021", "2019", 9)
for c, r in SOC_BY_CODE.items():             # 2021 authority index values (repo snapshot)
    put(IV, c, "2021", num(r.get("socio_index_2021")))
    put(CL, c, "2021", num(r.get("socio_cluster_2021")))
for code, nmrec in list(CL.items()):
    if code not in BRIDGE and code in SOC_BY_CODE:
        bridge_add(code, SOC_BY_CODE[code]["name"], "socio")
print(f"    clusters: {len(CL)} authorities | values: {len(IV)}")

# ================= 3. within-city dispersion =================
print("[3] dispersion series ...")
def wq(vals, wts, q):
    idx = np.argsort(vals)
    v, w = np.asarray(vals)[idx], np.asarray(wts)[idx]
    cw = np.cumsum(w) - 0.5*w
    return float(np.interp(q * w.sum(), cw, v))
def wsd(vals, wts):
    v, w = np.asarray(vals, float), np.asarray(wts, float)
    m = np.average(v, weights=w)
    return float(math.sqrt(np.average((v-m)**2, weights=w)))

SA = {}                                      # vintage -> list of (code, value, pop)
sa08 = pd.read_excel(rf"{DL}/socio_index_zip2/2/tab02_01.xls", sheet_name="ב1", header=None)
SA["2008"] = [(int(num(r[1])), num(r[6]), num(r[5])) for _, r in sa08.iloc[9:].iterrows()
              if num(r[1]) is not None and num(r[6]) is not None and num(r[5])]
SA["2017"] = [(int(num(r[1])), num(r[8]), num(r[7])) for _, r in t17f.iloc[9:].iterrows()
              if num(r[1]) is not None and num(r[8]) is not None and num(r[7])]
t12f = pd.read_excel(rf"{DL}/socio_index_zip3/T12.xlsx", sheet_name="t12", header=None)
SA["2019"] = [(int(num(r[0])), num(r[4]), num(r[3])) for _, r in t12f.iloc[8:].iterrows()
              if num(r[0]) is not None and num(r[4]) is not None and num(r[3])]
SA["2021"] = [(int(num(r[1])), num(r[8]), num(r[7])) for _, r in t21f.iloc[10:].iterrows()
              if num(r[1]) is not None and num(r[8]) is not None and num(r[7])]

DISP = {}                                    # code -> {vintage: {...}}
NATSD = {}
for vint, rows in SA.items():
    allv = [v for _, v, _ in rows]; allw = [w for _, _, w in rows]
    NATSD[vint] = wsd(allv, allw)
    by = {}
    for c, v, w in rows: by.setdefault(c, []).append((v, w))
    for c, vw in by.items():
        if len(vw) < 3: continue
        v = [a for a, _ in vw]; w = [b for _, b in vw]
        s = wsd(v, w); iqr = wq(v, w, .75) - wq(v, w, .25)
        DISP.setdefault(c, {})[vint] = {
            "sd": round(s, 4), "iqr": round(iqr, 4), "rel_sd": round(s/NATSD[vint], 4),
            "n_areas": len(vw), "pop": round(sum(w))}
print(f"    stat-areas per vintage: " + ", ".join(f"{v}:{len(SA[v])}" for v in SA))

OFF = {}                                     # code -> {"2008": {...}, "2019": {...}}
off08 = pd.read_excel(rf"{DL}/socio_index_zip2/2/tab02_05.xls", sheet_name="ב5", header=None)
for _, r in off08.iloc[7:].iterrows():
    code = num(r[0])
    if code is None or num(r[6]) is None: continue
    OFF.setdefault(int(code), {})["2008"] = {"sd": round(num(r[6]), 4), "iqr": round(num(r[7]), 4),
                                             "adj_iqr": round(num(r[9]), 4), "n_areas": int(num(r[3]) or 0)}
off19 = pd.read_excel(rf"{DL}/socio_index_zip3/T14.xlsx", sheet_name="t14", header=None)
for _, r in off19.iloc[8:].iterrows():
    code = num(r[0])
    if code is None or num(r[6]) is None: continue
    OFF.setdefault(int(code), {})["2019"] = {"sd": round(num(r[6]), 4), "iqr": round(num(r[7]), 4),
                                             "adj_iqr": round(num(r[9]), 4), "n_areas": int(num(r[3]) or 0)}
# validation computed vs official
for vint in ["2008", "2019"]:
    pairs = [(DISP[c][vint]["sd"], OFF[c][vint]["sd"]) for c in OFF
             if vint in OFF.get(c, {}) and vint in DISP.get(c, {})]
    a = np.array([p[0] for p in pairs]); b = np.array([p[1] for p in pairs])
    r = float(np.corrcoef(a, b)[0, 1]); mad = float(np.mean(np.abs(a-b)))
    print(f"    validate {vint}: n={len(pairs)} r={r:.4f} mean|d|={mad:.4f} (computed vs official wSD)")

# ================= bridge diagnostics =================
codes_all = set(CENSUS) | set(CL) | set(DISP)
unmatched = [(c, CENSUS.get(c, {}).get("cbs_name", "?"),
              (CENSUS.get(c, {}).get("2008", {}) or CENSUS.get(c, {}).get("2022", {})).get("pop", 0))
             for c in codes_all if c not in BRIDGE]
unmatched.sort(key=lambda t: -(t[2] or 0))
srcs = {}
for c in BRIDGE: srcs[BRIDGE_SRC[c]] = srcs.get(BRIDGE_SRC[c], 0) + 1
print(f"[bridge] matched {len(BRIDGE)}/{len(codes_all)} codes  by {srcs}")
print("    top unmatched (pop thousands):")
for c, n, p in unmatched[:15]:
    print(f"      {c:>5}  {n}  pop={p}")

# ================= 4. education gradient =================
print("[4] education gradient ...")
EYEAR = {"13":1992.5,"14":1996.4,"15":1999.4,"16":2003.1,"17":2006.25,"18":2009.1,
         "19":2013.1,"20":2015.2,"21":2019.3,"22":2019.7,"23":2020.2,"24":2021.2,"25":2022.8}
KS = list(EYEAR)
CPTS = [("1972",1972),("1983",1983),("1995",1995),("2008",2008),("2022",2022)]

def acad_interp(rec, year):
    pts = [(y, rec[k]["acad"]) for k, y in CPTS if k in rec and "acad" in rec[k]]
    if len(pts) < 2: return None
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return float(np.interp(min(max(year, xs[0]), xs[-1]), xs, ys))

def is_jewish(code, dname):
    rel = REL22.get(code, (None, None))[0]
    if rel is not None: return rel == 1
    sr = SOC_BY_CODE.get(code)
    if sr and isinstance((sr.get("religion") or {}).get("pct_jews"), (int, float)):
        return sr["religion"]["pct_jews"] >= 70
    x = LOC.get(norm(dname))
    if x:
        aps = [d.get("arab_pct") for d in x["data"].values() if d.get("arab_pct") is not None]
        if aps: return (sum(aps)/len(aps)) < 30
    return False

# build panel arrays over census-matched localities
rows = []                                    # (code, dname, jewish, acad2008, rec)
for code, rec in CENSUS.items():
    dname = BRIDGE.get(code)
    if not dname: continue
    rows.append((code, dname, is_jewish(code, dname), rec))
codes_arr  = [r[0] for r in rows]
jew_mask   = np.array([r[2] for r in rows])
NLOC = len(rows)
Y  = np.full((NLOC, len(KS)), np.nan)        # right_haredi share
Wt = np.full((NLOC, len(KS)), np.nan)        # bzb weight
Xt = np.full((NLOC, len(KS)), np.nan)        # interpolated %acad
Xf = np.full((NLOC, len(KS)), np.nan)        # fixed 2008 %acad
for i, (code, dname, _, rec) in enumerate(rows):
    x = LOC[norm(dname)]
    a08 = rec.get("2008", {}).get("acad")
    for j, k in enumerate(KS):
        d = x["data"].get(k)
        if not d or d.get("right_haredi_pct") is None: continue
        w = d.get("bzb") or d.get("kosher_votes")
        if not w: continue
        Y[i, j] = d["right_haredi_pct"]; Wt[i, j] = w
        ai = acad_interp(rec, EYEAR[k])
        if ai is not None: Xt[i, j] = ai
        if a08 is not None: Xf[i, j] = a08

def wgrad(x, y, w):
    m = np.isfinite(x) & np.isfinite(y) & np.isfinite(w)
    if m.sum() < 20: return None, None, 0
    x, y, w = x[m], y[m], w[m]
    mx, my = np.average(x, weights=w), np.average(y, weights=w)
    cov = np.average((x-mx)*(y-my), weights=w)
    vx, vy = np.average((x-mx)**2, weights=w), np.average((y-my)**2, weights=w)
    if vx <= 0 or vy <= 0: return None, None, int(m.sum())
    return float(cov/vx), float(cov/math.sqrt(vx*vy)), int(m.sum())

def grad_series(X, mask):
    out = []
    for j, k in enumerate(KS):
        sl, r, n = wgrad(X[mask, j], Y[mask, j], Wt[mask, j])
        out.append({"k": k, "year": EYEAR[k], "slope": None if sl is None else round(sl, 4),
                    "r": None if r is None else round(r, 4), "n": n})
    return out

def boot(X, mask, stat="slope"):
    idxs = np.where(mask)[0]
    slopes = np.full((B, len(KS)), np.nan); trends = np.full(B, np.nan)
    yrs = np.array([EYEAR[k] for k in KS])
    for b in range(B):
        samp = RNG.choice(idxs, size=len(idxs), replace=True)
        vals = []
        for j in range(len(KS)):
            sl, r, n = wgrad(X[samp, j], Y[samp, j], Wt[samp, j])
            v = sl if stat == "slope" else r
            slopes[b, j] = np.nan if v is None else v
            vals.append(v)
        m = np.isfinite(slopes[b])
        if m.sum() >= 5:
            t = np.polyfit(yrs[m], slopes[b][m], 1)[0]
            trends[b] = t
    lo = np.nanpercentile(slopes, 2.5, axis=0); hi = np.nanpercentile(slopes, 97.5, axis=0)
    tlo, thi = np.nanpercentile(trends, [2.5, 97.5])
    return ([None if not np.isfinite(v) else round(float(v), 4) for v in lo],
            [None if not np.isfinite(v) else round(float(v), 4) for v in hi],
            round(float(np.nanmean(trends)), 5), round(float(tlo), 5), round(float(thi), 5))

GRAD = {}
for label, X in [("interp", Xt), ("fixed2008", Xf)]:
    for uni, mask in [("jewish", jew_mask), ("all", np.ones(NLOC, bool))]:
        ser = grad_series(X, mask)
        slo, shi, tr, tlo, thi = boot(X, mask, "slope")
        for e, l, h in zip(ser, slo, shi): e["ci"] = [l, h]
        yrs = np.array([EYEAR[k] for k in KS])
        pt = [e["slope"] for e in ser]
        m = np.array([v is not None for v in pt])
        tr_pt = float(np.polyfit(yrs[m], np.array(pt, float)[m], 1)[0])
        GRAD[f"{label}_{uni}"] = {"series": ser,
            "trend_per_decade": round(tr_pt*10, 4), "trend_ci_per_decade": [round(tlo*10,4), round(thi*10,4)]}
        print(f"    {label}/{uni}: slope K13={ser[0]['slope']} -> K25={ser[-1]['slope']} "
              f"trend/decade={tr_pt*10:+.3f} ci=[{tlo*10:+.3f},{thi*10:+.3f}] n~{ser[-1]['n']}")

# index-value gradient (authority level, nearest vintage <=2y)
IDX_MAP = {"19": "2013", "20": "2015", "24": "2021", "25": "2021"}
IDXGRAD = []
for k, vint in IDX_MAP.items():
    xs, ys, ws = [], [], []
    for code, vals in IV.items():
        v = vals.get(vint); dname = BRIDGE.get(code)
        if v is None or not dname: continue
        d = LOC[norm(dname)]["data"].get(k)
        if not d or d.get("right_haredi_pct") is None: continue
        w = d.get("bzb") or d.get("kosher_votes")
        if not w: continue
        xs.append(v); ys.append(d["right_haredi_pct"]); ws.append(w)
    sl, r, n = wgrad(np.array(xs), np.array(ys), np.array(ws))
    IDXGRAD.append({"k": k, "year": EYEAR[k], "vintage": vint, "n": n,
                    "r": None if r is None else round(r, 4),
                    "slope": None if sl is None else round(sl, 4)})
    print(f"    idx-gradient K{k} (v{vint}): r={r if r is None else round(r,3)} n={n}")

# ================= 5. dispersion vs political sorting =================
print("[5] dispersion vs sorting ...")
def nat_rh(k):
    ys, ws = [], []
    for x in LOC.values():
        d = x["data"].get(k)
        if d and d.get("right_haredi_pct") is not None and (d.get("bzb") or d.get("kosher_votes")):
            ys.append(d["right_haredi_pct"]); ws.append(d.get("bzb") or d.get("kosher_votes"))
    return float(np.average(ys, weights=ws))
NAT = {"18": nat_rh("18"), "25": nat_rh("25")}
CITY_LINK = []
for code, dser in DISP.items():
    if "2008" not in dser or "2021" not in dser: continue
    dname = BRIDGE.get(code)
    if not dname: continue
    x = LOC[norm(dname)]
    d18, d25 = x["data"].get("18"), x["data"].get("25")
    if not d18 or not d25: continue
    rh18, rh25 = d18.get("right_haredi_pct"), d25.get("right_haredi_pct")
    if rh18 is None or rh25 is None: continue
    CITY_LINK.append({
        "name": dname, "code": code, "jewish": bool(is_jewish(code, dname)),
        "rel_sd": {v: dser[v]["rel_sd"] for v in dser},
        "d_rel_sd": round(dser["2021"]["rel_sd"] - dser["2008"]["rel_sd"], 4),
        "rh": {"18": rh18, "25": rh25},
        "distinct": {"18": round(abs(rh18 - NAT["18"]), 2), "25": round(abs(rh25 - NAT["25"]), 2)},
        "d_distinct": round(abs(rh25 - NAT["25"]) - abs(rh18 - NAT["18"]), 2),
        "pop": dser["2021"]["pop"],
    })
xs = np.array([c["d_rel_sd"] for c in CITY_LINK]); ys = np.array([c["d_distinct"] for c in CITY_LINK])
ws = np.array([c["pop"] for c in CITY_LINK], float)
sl, r_link, n_link = wgrad(xs, ys, ws)
jm = np.array([c["jewish"] for c in CITY_LINK])
sl_j, r_link_j, n_link_j = wgrad(xs[jm], ys[jm], ws[jm])
# national within-city dispersion trend — BALANCED panel (cities in all 4 vintages)
VINTS = ["2008", "2017", "2019", "2021"]
bal = [c for c, d in DISP.items() if all(v in d for v in VINTS)]
NATDISP = {}
for vint in VINTS:
    vals = [(d[vint]["rel_sd"], d[vint]["pop"]) for d in DISP.values() if vint in d]
    bv = [(DISP[c][vint]["rel_sd"], DISP[c][vint]["pop"]) for c in bal]
    NATDISP[vint] = {
        "mean_rel_sd": round(float(np.average([v for v,_ in vals], weights=[w for _,w in vals])), 4),
        "n_cities": len(vals),
        "balanced_mean_rel_sd": round(float(np.average([v for v,_ in bv], weights=[w for _,w in bv])), 4),
        "balanced_mean_iqr_rel": round(float(np.average(
            [DISP[c][vint]["iqr"]/NATSD[vint] for c in bal], weights=[w for _,w in bv])), 4)}
    print(f"    national mean rel_sd {vint}: full {NATDISP[vint]['mean_rel_sd']} (n={NATDISP[vint]['n_cities']}) | "
          f"balanced {NATDISP[vint]['balanced_mean_rel_sd']} (n={len(bal)})")
print(f"    link: d_rel_sd vs d_distinct r={r_link if r_link is None else round(r_link,3)} n={n_link} | "
      f"jewish r={r_link_j if r_link_j is None else round(r_link_j,3)} n={n_link_j}")

# ================= assemble output =================
census_out = {}
for code, rec in CENSUS.items():
    dname = BRIDGE.get(code)
    if not dname: continue
    e = {"code": code, "jewish": bool(is_jewish(code, dname))}
    rel = REL22.get(code)
    if rel and rel[1]: e["religiosity_2022"] = rel[1]
    for k, yr in CPTS:
        if k in rec: e[k] = {kk: round(vv, 2) for kk, vv in rec[k].items()}
    census_out[dname] = e
clusters_out = {}
for code, vals in CL.items():
    dname = BRIDGE.get(code)
    if not dname: continue
    clusters_out[dname] = {"code": code,
                           **{v: int(c) for v, c in sorted(vals.items()) if c is not None}}
values_out = {}
for code, vals in IV.items():
    dname = BRIDGE.get(code)
    if not dname or not vals: continue
    values_out[dname] = {"code": code, **{v: round(x, 3) for v, x in sorted(vals.items())}}
disp_out = {}
for code, dser in DISP.items():
    dname = BRIDGE.get(code)
    if not dname: continue
    disp_out[dname] = {"code": code, "series": dser}
    if code in OFF: disp_out[dname]["official"] = OFF[code]

out = {
    "meta": {
        "built": "2026-07-02", "b_bootstrap": B,
        "sources": {
            "census": "CBS mesukam 2008 inter-census comparisons (1972/1983/1995/2008) + census 2022 locality rows",
            "socio_index": "CBS socio-economic index: authority 2013 (w/2008), 2015, city clusters 2017/2019/2021, values 2021 via repo socioeconomic.json",
            "dispersion": "stat-area index tables 2008/2017/2019/2021; official within-city tables 2008 (B5) + 2019 (T14)",
        },
        "caveats": [
            "אקולוגי: אגרגטים יישוביים, לא פרטים.",
            "אחוז אקדמאים: בסיס בני 15+ בהגדרת הלמס, אינטרפולציה ליניארית בין מפקדים.",
            "מדדים חברתיים-כלכליים מתוקננים לכל שנתון בנפרד — השוואה בין שנים ביחידות יחסיות (rel_sd) בלבד.",
            "מדגם המפקד 1972-2008: יישובים בני ~2,000+ בחלק מהמשתנים; אל תסיקו על יישובים קטנים.",
        ],
        "nat_rh": {k: round(v, 2) for k, v in NAT.items()},
        "nat_sd": {v: round(s, 4) for v, s in NATSD.items()},
    },
    "census": census_out,
    "clusters": clusters_out,
    "index_values": values_out,
    "dispersion": disp_out,
    "gradient": GRAD,
    "index_gradient": IDXGRAD,
    "dispersion_national": NATDISP,
    "sorting_link": {"cities": sorted(CITY_LINK, key=lambda c: -c["pop"]),
                     "r_weighted": None if r_link is None else round(r_link, 4),
                     "slope": None if sl is None else round(sl, 4), "n": n_link,
                     "r_weighted_jewish": None if r_link_j is None else round(r_link_j, 4),
                     "n_jewish": n_link_j, "balanced_cities": len(bal)},
}
with open(f"{ROOT}/data/demographics_panel.json", "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False)
kb = len(json.dumps(out, ensure_ascii=False)) // 1024
print(f"wrote data/demographics_panel.json (~{kb} KB) | census {len(census_out)} | "
      f"clusters {len(clusters_out)} | dispersion {len(disp_out)} | link cities {len(CITY_LINK)}")
