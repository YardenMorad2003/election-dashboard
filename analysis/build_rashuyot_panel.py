# -*- coding: utf-8 -*-
"""Phase 4: harmonized panel from the CBS annual local-authority profiles
("הרשויות המקומיות בישראל", p_libud), one file per year 1999-2024, plus the
election-matched analyses that the 2026-07-02 deep exploration
(analysis/explore_rashuyot.py) scoped as worth shipping:

  1. EXTRACT   — authority-year panel: avg wage (w/ reference-year lag), bagrut
                 eligibility %, wage Gini (ends 2021), migration balance
                 (total + internal), socio-economic cluster (w/ per-file index
                 vintage), population. Sector-aware keys (municipal vs regional
                 council — RC codes 1-78 collide with small muni semels).
  2. JOIN      — normalized-name join of municipal authorities to the election
                 localities (localities.json) + jewish flag / census %academics
                 from data/demographics_panel.json.
  3. GRADIENTS — per election K15-K25, bzb-weighted r of right_haredi_pct on
                 ln(wage), bagrut%, and census-interpolated %academics on the
                 SAME authority universe (the "income always divided, education
                 realigned" same-universe test). Panel bootstrap (B=1000,
                 resample authorities) CIs + linear trend of r.
  4. MIGRATION — selective-migration null test: avg annual internal-migration
                 rate vs RH-share change K15->K25 (overall / amplification /
                 distinctiveness) + recent-window robustness + case studies.
  5. GINI      — pop-weighted national city-Gini by year + link to the Phase-3
                 within-city dispersion change.

Output: data/rashuyot_panel.json (~0.5-1 MB). Log: analysis/rashuyot_panel_run.log
Run: python -X utf8 analysis/build_rashuyot_panel.py   (~2-3 min, mostly Excel IO)

Known source traps handled here (see HANDOFF.md deep-exploration section):
- wage reference year = file year - 1 (named in 1999-2015 files, header note in
  2016+); the p_libud_2021 file's wage is a verbatim copy of the 2020 file's
  (ref 2019, stale).
- 2022+ files replace "שכר ממוצע לחודש של שכירים" with an all-earners income
  concept (+17% level jump); we take the "שכר ממוצע" subcolumn under the parent
  "בעלי הכנסה משכר" (wage earners only) for concept continuity. Still marked as
  a break — levels must be spliced, cross-sections are fine (r>=0.97).
- Gini (wage earners) published 1999-2021 only.
- internal-migration split unpublished 2002-2013 (total includes aliya).
- bagrut levels jump with education reforms — cross-section only, never levels.
- cluster column vintage varies by file; per-file vintage map validated
  empirically against the official socio-index publications (100% match).
- pop in thousands through ~2015 files, persons later (normalized here).
"""
import json
import math
import os
import re
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:/Users/yarde/Downloads/election-dashboard-extracted/election-dashboard-main"
D = r"C:\Users\yarde\Downloads\rashuyot_zip\רשויות מקומיות"
LOG = open(f"{ROOT}/analysis/rashuyot_panel_run.log", "w", encoding="utf-8")
B = 1000
RNG = np.random.default_rng(26)


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    LOG.write(s + "\n"); LOG.flush()


def year_of(f):
    m = re.match(r"(\d{4})", f)
    if m: return int(m.group(1))
    m = re.search(r"libud_(\d{4})", f)
    if m: return int(m.group(1))
    m = re.search(r"libud_(\d{2})", f)
    if m: return 2000 + int(m.group(1))
    return None


def clean(s):
    return re.sub(r"\s+", " ", str(s)).strip()


def num(v):
    if v is None: return None
    s = str(v).strip().replace(",", "")
    if s in ("", "-", "..", ".", "nan", "None"): return None
    try:
        f = float(s)
        return f if math.isfinite(f) else None
    except ValueError:
        return None


# per-file socio-index vintage of the cluster column. 1999-2015 named in the
# column header; 2014+ validated empirically vs the official publications
# (exact cluster match 100% on ~200 municipalities, see probe in HANDOFF).
CLUSTER_VINTAGE = {}
for _yr in range(1999, 2003): CLUSTER_VINTAGE[_yr] = 1995
for _yr in range(2003, 2005): CLUSTER_VINTAGE[_yr] = 1999
for _yr in range(2005, 2008): CLUSTER_VINTAGE[_yr] = 2003
for _yr in range(2008, 2011): CLUSTER_VINTAGE[_yr] = 2006
for _yr in range(2011, 2015): CLUSTER_VINTAGE[_yr] = 2008
CLUSTER_VINTAGE.update({2015: 2013, 2016: 2013, 2017: 2015, 2018: 2015,
                        2019: 2017, 2020: 2017, 2021: 2019, 2022: 2019,
                        2023: 2021, 2024: 2021})

SKIP_SHEETS = ("תוכן", "הערות", "תיקונים", "סיכומ", "מקרא", "מיגזר",
               "שימושי קרקע", "תקציב", "כספיים", "סקר", "רשויות מקומיות")


def match_var(name, var):
    n = name
    if var == "wage":
        return (re.search(r"^שכר ממוצע לחודש של (ה?)שכירים", n) or
                re.search(r"^שכר חודשי ממוצע של שכיר", n) or
                re.search(r"^הכנסה ממוצעת לחודש של (ה?)שכירים", n)) and \
               "אחוז" not in n and "שינוי" not in n and "גברים" not in n and "נשים" not in n
    if var == "gini":
        return "ג'יני" in n and "אחוז" not in n
    if var == "mig_total":
        return "מאזן הגירה" in n and re.search(r'סה.?כ|ביישוב', n) and \
               "פנימית" not in n and "מתוך" not in n and "אחוז" not in n and "ל-1,000" not in n
    if var == "mig_internal":
        return "מאזן הגירה פנימית" in n and "אחוז" not in n and "ל-1,000" not in n
    if var == "bagrut":
        return "זכאים" in n and "בגרות" in n and "אוניברסיט" not in n and \
               "סף" not in n and "שינוי" not in n
    if var == "cluster":
        return (("אשכול" in n and ("חברתי" in n or "הנמוך" in n)) or
                n.startswith("רמה חברתית-כלכלית")) and \
               "קומפקטי" not in n and "פריפריאלי" not in n and "מותאמ" not in n and \
               "טבעי" not in n
    if var == "pop":
        return re.search(r"^סה.?כ אוכלוסי", n) or "אוכלוסייה בסוף השנה" in n or \
               re.search(r"^אוכלוסי(י?)ה - סה", n) or n == "אוכלוסייה"
    return False


VARS = ["pop", "cluster", "wage", "gini", "mig_total", "mig_internal", "bagrut"]

# ================= 1. extract =================
log("[1] extracting", D)
panel = {}        # (sector, semel, year) -> {var: value}   sector 'm'/'r'
NAMES = {}        # (sector, semel) -> heb name (latest file wins)
files = sorted([f for f in os.listdir(D) if year_of(f)], key=year_of)
coverage = {}     # year -> var -> n

for f in files:
    yr = year_of(f)
    path = os.path.join(D, f)
    xl = pd.ExcelFile(path)
    for s in xl.sheet_names:
        if any(k in s for k in SKIP_SHEETS):
            continue
        sheet_rc = "אזורי" in s
        df = pd.read_excel(path, sheet_name=s, header=None)
        hit = None
        for r in range(min(12, len(df))):
            for c in range(min(8, df.shape[1])):
                v = df.iat[r, c]
                if isinstance(v, str) and "סמל הרשות" in v:
                    hit = (r, c); break
            if hit: break
        if hit is None:
            continue
        r, c = hit
        col_below = [v for v in df.iloc[r:r+8, c] if isinstance(v, str) and re.search(r"[א-ת]", str(v))]
        transposed = len(col_below) >= 6

        if transposed:
            # 1999-2002 era: variables as rows, authorities as columns.
            # Sector comes from the sheet name (RC sheets are separate here).
            sector = "r" if sheet_rc else "m"
            semels = [num(v) for v in df.iloc[r, c+1:]]
            name_row = None
            for rr in range(len(df)):
                v = df.iat[rr, c]
                if isinstance(v, str) and "שם" in v and "רשות" in v:
                    name_row = rr; break
            for rr in range(len(df)):
                v = df.iat[rr, c]
                if not isinstance(v, str):
                    continue
                nm = clean(v)
                for var in VARS:
                    if match_var(nm, var):
                        for j, sem in enumerate(semels):
                            if sem is None: continue
                            val = num(df.iat[rr, c+1+j])
                            if val is None: continue
                            panel.setdefault((sector, int(sem), yr), {}).setdefault(var, val)
            if name_row is not None:
                for j, sem in enumerate(semels):
                    if sem is not None and isinstance(df.iat[name_row, c+1+j], str):
                        NAMES[(sector, int(sem))] = clean(df.iat[name_row, c+1+j])
        else:
            # rows layout (2003-2015 header row 0; 2016+ header row 3)
            def colname(j):
                for rr in (r, r+1, r-1, r-2):
                    if 0 <= rr < len(df):
                        v = df.iat[rr, j]
                        if isinstance(v, str) and re.search(r"[א-ת]", v):
                            return clean(v)
                return ""
            def parent_of(j):
                # nearest non-empty header-row string at or left of j (merged cells)
                for jj in range(j, max(j-3, -1), -1):
                    v = df.iat[r, jj]
                    if isinstance(v, str) and re.search(r"[א-ת]", v):
                        return clean(v)
                return ""
            name_col = status_col = None
            for j in range(min(8, df.shape[1])):
                nm = colname(j)
                if name_col is None and "שם" in nm and "רשות" in nm:
                    name_col = j
                if status_col is None and "מעמד מוניציפלי" in nm and "שנת" not in nm:
                    status_col = j
            var_cols = {}
            for j in range(df.shape[1]):
                nm = colname(j)
                if not nm: continue
                for var in VARS:
                    if match_var(nm, var) and var not in var_cols:
                        var_cols[var] = j
                # 2022+ concept-continuous wage: "שכר ממוצע" subcolumn under
                # the parent header "בעלי הכנסה משכר" (wage earners only)
                if "wage" not in var_cols and nm == "שכר ממוצע" and \
                        parent_of(j) == "בעלי הכנסה משכר":
                    var_cols["wage"] = j
            for i in range(r + 1, len(df)):
                sem = num(df.iat[i, c])
                if sem is None: continue
                sem = int(sem)
                if status_col is not None:
                    st = df.iat[i, status_col]
                    sector = "r" if (isinstance(st, str) and "אזורי" in st) else "m"
                else:
                    sector = "r" if sheet_rc else "m"
                if name_col is not None and isinstance(df.iat[i, name_col], str):
                    NAMES[(sector, sem)] = clean(df.iat[i, name_col])
                for var, j in var_cols.items():
                    val = num(df.iat[i, j])
                    if val is not None:
                        panel.setdefault((sector, sem, yr), {}).setdefault(var, val)

    cov = {v: sum(1 for (sec, sem, y), d in panel.items() if y == yr and v in d) for v in VARS}
    coverage[yr] = cov
    log(f"  {yr}: " + "  ".join(f"{v}={cov[v]}" for v in VARS))

# pop unit normalization: thousands through ~2015-era files, persons later
years_all = sorted({y for (_, _, y) in panel})
for yr in years_all:
    tot = sum(d.get("pop", 0) for (sec, sem, y), d in panel.items() if y == yr)
    if 0 < tot < 20000:
        for (sec, sem, y), d in panel.items():
            if y == yr and "pop" in d:
                d["pop"] *= 1000

# wage reference year: file year - 1 everywhere (verified in column names
# 1999-2015 + header notes 2016+), except the stale 2021 file (= 2019 data)
WAGE_REF = {yr: yr - 1 for yr in years_all}
WAGE_REF[2021] = 2019

rc_set = {sem for (sec, sem) in NAMES if sec == "r"}
mu_set = {sem for (sec, sem) in NAMES if sec == "m"}
log(f"  total: {len(panel)} authority-years | munis={len(mu_set)} RCs={len(rc_set)} "
    f"| semel collisions muni∩RC: {sorted(mu_set & rc_set)}")

# ================= 2. join to election data =================
log("\n[2] joining to localities.json / demographics_panel.json")
FIN = {"ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ"}
def norm(s):
    s = re.sub(r"\([^)]*\)", "", str(s).strip())
    for ch in ['"', "״", "'", "׳", "*"]:
        s = s.replace(ch, "")
    s = re.sub(r"[\s\-–־]+", "", s)
    s = "".join(FIN.get(c, c) for c in s)
    return s.replace("יי", "י").replace("וו", "ו")

loc = json.load(open(f"{ROOT}/data/localities.json", encoding="utf-8"))
LOC = {}
for x in loc:
    k = norm(x["name"])
    if k not in LOC or x.get("elections_count", 0) > LOC[k].get("elections_count", 0):
        LOC[k] = x
demo = json.load(open(f"{ROOT}/data/demographics_panel.json", encoding="utf-8"))
CENSUS = demo["census"]                     # display-name keyed
CEN_NORM = {norm(n): n for n in CENSUS}

SEM2LOC = {}                                # muni semel -> localities.json entry
SEM2CEN = {}                                # muni semel -> census record
for (sec, sem), nm in NAMES.items():
    if sec != "m": continue
    k = norm(nm)
    if k in LOC:
        SEM2LOC[sem] = LOC[k]
    if k in CEN_NORM:
        SEM2CEN[sem] = CENSUS[CEN_NORM[k]]

def is_jewish(sem):
    cen = SEM2CEN.get(sem)
    if cen is not None and isinstance(cen.get("jewish"), bool):
        return cen["jewish"]
    x = SEM2LOC.get(sem)
    if x:
        aps = [d.get("arab_pct") for d in x["data"].values() if d.get("arab_pct") is not None]
        if aps: return (sum(aps) / len(aps)) < 30
    return False

unmatched_big = sorted(((max(panel.get(("m", sem, y), {}).get("pop", 0) for y in years_all), nm)
                        for (sec, sem), nm in NAMES.items()
                        if sec == "m" and sem not in SEM2LOC), reverse=True)
log(f"  matched {len(SEM2LOC)}/{len(mu_set)} municipal authorities to election localities")
log("  unmatched munis with pop>10k: " +
    ("; ".join(f"{nm} ({int(p):,})" for p, nm in unmatched_big if p > 10000) or "none"))

# ================= 3. gradients (same-universe test) =================
log("\n[3] election-matched gradients, same universe")
EYEAR = {"15": 1999.4, "16": 2003.1, "17": 2006.25, "18": 2009.1, "19": 2013.1,
         "20": 2015.2, "21": 2019.3, "22": 2019.7, "23": 2020.2, "24": 2021.2, "25": 2022.8}
EFILE = {"15": 1999, "16": 2003, "17": 2006, "18": 2009, "19": 2013, "20": 2015,
         "21": 2019, "22": 2019, "23": 2020, "24": 2021, "25": 2022}
KS = list(EYEAR)
CPTS = [("1972", 1972), ("1983", 1983), ("1995", 1995), ("2008", 2008), ("2022", 2022)]

def acad_interp(rec, year):
    pts = [(y, rec[k]["acad"]) for k, y in CPTS if k in rec and "acad" in rec[k]]
    if len(pts) < 2: return None
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return float(np.interp(min(max(year, xs[0]), xs[-1]), xs, ys))

# panel arrays over jewish-majority matched municipal authorities
sems = sorted(sem for sem in SEM2LOC if is_jewish(sem))
NA = len(sems)
NK = len(KS)
Y  = np.full((NA, NK), np.nan)      # right_haredi share
Wt = np.full((NA, NK), np.nan)      # bzb weight
Xw = np.full((NA, NK), np.nan)      # ln(avg wage), file year = election calendar year
Xb = np.full((NA, NK), np.nan)      # bagrut %
Xa = np.full((NA, NK), np.nan)      # census %academics interpolated to election
for i, sem in enumerate(sems):
    x = SEM2LOC[sem]
    cen = SEM2CEN.get(sem)
    for j, k in enumerate(KS):
        d = x["data"].get(k)
        if not d or d.get("right_haredi_pct") is None: continue
        w = d.get("bzb") or d.get("kosher_votes")
        if not w: continue
        Y[i, j] = d["right_haredi_pct"]; Wt[i, j] = w
        pd_ = panel.get(("m", sem, EFILE[k]), {})
        if pd_.get("wage"):
            Xw[i, j] = math.log(pd_["wage"])
        if pd_.get("bagrut") is not None:
            Xb[i, j] = pd_["bagrut"]
        if cen is not None:
            ai = acad_interp(cen, EYEAR[k])
            if ai is not None: Xa[i, j] = ai

def wcorr(x, y, w):
    m = np.isfinite(x) & np.isfinite(y) & np.isfinite(w)
    if m.sum() < 20: return None, 0
    x, y, w = x[m], y[m], w[m]
    mx, my = np.average(x, weights=w), np.average(y, weights=w)
    cov = np.average((x-mx)*(y-my), weights=w)
    vx, vy = np.average((x-mx)**2, weights=w), np.average((y-my)**2, weights=w)
    if vx <= 0 or vy <= 0: return None, int(m.sum())
    return float(cov/math.sqrt(vx*vy)), int(m.sum())

# same-universe mask: rows with wage AND census-acad (and Y, W) that election;
# bagrut reported on its sub-universe (missing entirely in the 1999 file)
UNIV = np.isfinite(Y) & np.isfinite(Wt) & np.isfinite(Xw) & np.isfinite(Xa)

def grad_row(rows_idx, j):
    u = UNIV[rows_idx, j]
    idx = rows_idx[u]
    rw, n = wcorr(Xw[idx, j], Y[idx, j], Wt[idx, j])
    ra, _ = wcorr(Xa[idx, j], Y[idx, j], Wt[idx, j])
    ub = idx[np.isfinite(Xb[idx, j])]
    rb, nb = wcorr(Xb[ub, j], Y[ub, j], Wt[ub, j])
    return rw, ra, rb, n, nb

def trend(rs, yrs):
    m = np.array([v is not None and np.isfinite(v) for v in rs])
    if m.sum() < 5: return None
    return float(np.polyfit(np.asarray(yrs)[m], np.asarray(rs, float)[m], 1)[0])

all_idx = np.arange(NA)
point = [grad_row(all_idx, j) for j in range(NK)]
yrs_arr = [EYEAR[k] for k in KS]

log("  bootstrap B=%d ..." % B)
boot_r = np.full((B, NK, 3), np.nan)          # wage, acad, bagrut
boot_tr = np.full((B, 3), np.nan)
for b in range(B):
    samp = RNG.choice(all_idx, size=NA, replace=True)
    for j in range(NK):
        rw, ra, rb, n, nb = grad_row(samp, j)
        boot_r[b, j] = [v if v is not None else np.nan for v in (rw, ra, rb)]
    for v in range(3):
        boot_tr[b, v] = trend(boot_r[b, :, v], yrs_arr) or np.nan

def ci(a, axis=0):
    lo = np.nanpercentile(a, 2.5, axis=axis); hi = np.nanpercentile(a, 97.5, axis=axis)
    return lo, hi

rlo, rhi = ci(boot_r)
tlo, thi = ci(boot_tr)
GRAD_SER = []
for j, k in enumerate(KS):
    rw, ra, rb, n, nb = point[j]
    e = {"k": k, "year": EYEAR[k], "file_year": EFILE[k], "n": n, "n_bagrut": nb}
    for v, (nm, val) in enumerate([("wage", rw), ("acad", ra), ("bagrut", rb)]):
        e[nm + "_r"] = None if val is None else round(val, 4)
        e[nm + "_ci"] = [None if not np.isfinite(rlo[j, v]) else round(float(rlo[j, v]), 4),
                         None if not np.isfinite(rhi[j, v]) else round(float(rhi[j, v]), 4)]
    GRAD_SER.append(e)
    log(f"  K{k} ({EFILE[k]}): wage r={e['wage_r']} acad r={e['acad_r']} "
        f"bagrut r={e['bagrut_r']} n={n} (bagrut n={nb})")

TRENDS = {}
for v, nm in enumerate(["wage", "acad", "bagrut"]):
    pt = trend([p[v] for p in point], yrs_arr)
    TRENDS[nm] = {"per_decade": None if pt is None else round(pt * 10, 4),
                  "ci_per_decade": [round(float(tlo[v]) * 10, 4), round(float(thi[v]) * 10, 4)]}
    log(f"  trend/decade {nm}: {TRENDS[nm]['per_decade']} ci={TRENDS[nm]['ci_per_decade']}")
# paired test: did the education gradient steepen MORE than the wage gradient?
# (difference of trends within each bootstrap draw - draws share the resample)
dif = boot_tr[:, 1] - boot_tr[:, 0]
dlo, dhi = np.nanpercentile(dif, [2.5, 97.5])
pt_dif = trend([p[1] for p in point], yrs_arr) - trend([p[0] for p in point], yrs_arr)
TRENDS["acad_minus_wage"] = {"per_decade": round(pt_dif * 10, 4),
                             "ci_per_decade": [round(float(dlo) * 10, 4), round(float(dhi) * 10, 4)]}
log(f"  paired trend diff (acad - wage)/decade: {TRENDS['acad_minus_wage']['per_decade']} "
    f"ci={TRENDS['acad_minus_wage']['ci_per_decade']}")

# ================= 4. migration null test =================
log("\n[4] selective-migration test")
def mig_rates(sector, sem, y0=None, y1=None):
    out = {}
    for y in years_all:
        if (y0 and y < y0) or (y1 and y > y1): continue
        d = panel.get((sector, sem, y), {})
        if d.get("mig_internal") is not None and d.get("pop"):
            out[y] = d["mig_internal"] / d["pop"] * 1000
    return out

SCATTER = []
tests = {}
for span, k0, k1, min_yrs, y0, y1 in [("full", "15", "25", 10, None, None),
                                      ("recent", "19", "25", 7, 2014, 2024)]:
    xs, ys, ws, dist_y, amp_x = [], [], [], [], []
    rows = []
    for sem in SEM2LOC:
        rates = mig_rates("m", sem, y0, y1)
        if len(rates) < min_yrs: continue
        rate = float(np.mean(list(rates.values())))
        x = SEM2LOC[sem]
        d0, d1 = x["data"].get(k0), x["data"].get(k1)
        if not d0 or not d1: continue
        rh0, rh1 = d0.get("right_haredi_pct"), d1.get("right_haredi_pct")
        if rh0 is None or rh1 is None: continue
        w = d1.get("bzb") or 0
        if not w: continue
        rows.append((sem, rate, rh0, rh1, w))
    jrows = [t for t in rows if is_jewish(t[0])]
    nat0 = np.average([t[2] for t in jrows], weights=[t[4] for t in jrows])
    nat1 = np.average([t[3] for t in jrows], weights=[t[4] for t in jrows])
    for sem, rate, rh0, rh1, w in jrows:
        xs.append(rate); ys.append(rh1 - rh0); ws.append(w)
        amp_x.append(rate * (1 if rh0 >= nat0 else -1))
        dist_y.append(abs(rh1 - nat1) - abs(rh0 - nat0))
    r_all, _ = wcorr(np.array(xs), np.array(ys), np.array(ws))
    r_amp, _ = wcorr(np.array(amp_x), np.array(ys), np.array(ws))
    r_dist, _ = wcorr(np.abs(np.array(amp_x)), np.array(dist_y), np.array(ws))
    tests[span] = {"r": round(r_all, 3), "r_amplification": round(r_amp, 3),
                   "r_distinctiveness": round(r_dist, 3), "n": len(jrows),
                   "transition": f"K{k0}→K{k1}"}
    log(f"  [{span}] K{k0}->K{k1}: r={r_all:+.3f} amp={r_amp:+.3f} dist={r_dist:+.3f} n={len(jrows)}")
    if span == "full":
        for sem, rate, rh0, rh1, w in rows:
            SCATTER.append({"name": NAMES[("m", sem)], "rate": round(rate, 1),
                            "drh": round(rh1 - rh0, 1), "w": int(w),
                            "jewish": bool(is_jewish(sem))})

CASE_NAMES = ["אלעד", "בית שמש", "גני תקווה"]
CASES = []
for want in CASE_NAMES:
    sem = next((s for (sec, s), nm in NAMES.items() if sec == "m" and norm(nm) == norm(want)), None)
    if sem is None or sem not in SEM2LOC:
        log(f"  case {want}: NOT FOUND"); continue
    rates = mig_rates("m", sem)
    x = SEM2LOC[sem]
    rh = {k: x["data"][k]["right_haredi_pct"] for k in KS
          if x["data"].get(k, {}).get("right_haredi_pct") is not None}
    CASES.append({"name": NAMES[("m", sem)], "semel": sem,
                  "rate": round(float(np.mean(list(rates.values()))), 1),
                  "drh": round(rh["25"] - rh["15"], 1) if "15" in rh and "25" in rh else None,
                  "rh": {k: round(v, 1) for k, v in rh.items()},
                  "mig_rate_by_year": {str(y): round(v, 1) for y, v in sorted(rates.items())}})
    log(f"  case {want}: rate={CASES[-1]['rate']:+.1f}/1000/yr dRH={CASES[-1]['drh']}")

# ================= 5. gini =================
log("\n[5] gini")
GINI_NAT = {}
for y in years_all:
    vals = [(d["gini"], d["pop"]) for (sec, sem, yy), d in panel.items()
            if yy == y and d.get("gini") is not None and d.get("pop")]
    if len(vals) > 50:
        GINI_NAT[str(y)] = round(float(np.average([v for v, _ in vals],
                                                  weights=[w for _, w in vals])), 4)
disp = demo["dispersion"]
code2d = {v["code"]: v["series"] for v in disp.values()}
xs, ys = [], []
for sem in mu_set:
    ser = code2d.get(sem)
    if not ser or "2008" not in ser or "2019" not in ser: continue
    g08 = panel.get(("m", sem, 2008), {}).get("gini")
    g19 = panel.get(("m", sem, 2019), {}).get("gini")
    if g08 is None or g19 is None: continue
    xs.append(g19 - g08); ys.append(ser["2019"]["rel_sd"] - ser["2008"]["rel_sd"])
g_link = round(float(np.corrcoef(xs, ys)[0, 1]), 3) if len(xs) > 20 else None
log(f"  national gini: " + "  ".join(f"{y}:{v}" for y, v in sorted(GINI_NAT.items())
                                     if y in ("1999", "2008", "2015", "2021")))
log(f"  dGini(08->19) vs d(rel_sd): r={g_link} n={len(xs)}")

# ================= QC =================
log("\n[QC]")
for y in (1999, 2008, 2016, 2024):
    tot = sum(d.get("pop", 0) for (sec, sem, yy), d in panel.items() if yy == y)
    log(f"  pop sum {y}: {tot:,.0f}")
soc = json.load(open(f"{ROOT}/data/socioeconomic.json", encoding="utf-8"))
inc = {int(r["code"]): r.get("avg_monthly_income_per_capita") for r in soc if r.get("code")}
xs, ys = [], []
for sem in mu_set:
    w = panel.get(("m", sem, 2021), {}).get("wage")
    v = inc.get(sem)
    if w and isinstance(v, (int, float)):
        xs.append(w); ys.append(v)
log(f"  wage(2021 file) vs socio-json income/capita: r={np.corrcoef(xs, ys)[0,1]:.3f} (n={len(xs)})")
mi_sums = {y: sum(d.get("mig_internal", 0) for (sec, sem, yy), d in panel.items() if yy == y)
           for y in (1999, 2016, 2021, 2024)}
log("  mig_internal national sum (≈0 expected): " +
    "  ".join(f"{y}:{v:+,.0f}" for y, v in mi_sums.items()))

# ================= write =================
AUTH = {}
for (sec, sem), nm in sorted(NAMES.items()):
    key = f"{sec}{sem}"
    ser = {}
    for y in years_all:
        d = panel.get((sec, sem, y))
        if not d: continue
        e = {}
        if d.get("pop"): e["pop"] = int(round(d["pop"]))
        if d.get("wage"): e["wage"] = int(round(d["wage"]))
        if d.get("bagrut") is not None: e["bagrut"] = round(d["bagrut"], 1)
        if d.get("gini") is not None: e["gini"] = round(d["gini"], 3)
        if d.get("mig_total") is not None: e["mig_total"] = int(d["mig_total"])
        if d.get("mig_internal") is not None: e["mig_internal"] = int(d["mig_internal"])
        if e: ser[str(y)] = e
    clus = {}
    for y in years_all:
        v = panel.get((sec, sem, y), {}).get("cluster")
        if v is not None:
            clus.setdefault(str(CLUSTER_VINTAGE[y]), int(v))
    entry = {"semel": sem, "name": nm, "rc": sec == "r", "series": ser}
    if clus: entry["cluster_by_vintage"] = clus
    if sec == "m" and sem in SEM2LOC:
        entry["locality"] = SEM2LOC[sem]["name"]
        entry["jewish"] = bool(is_jewish(sem))
    AUTH[key] = entry

OUT = {
    "meta": {
        "built": "2026-07-02", "b_bootstrap": B,
        "source": "CBS annual local-authority profiles (הרשויות המקומיות בישראל), one file per year 1999-2024",
        "wage_ref_year": {str(y): WAGE_REF[y] for y in years_all},
        "wage_concept_break": "2022+ files: avg wage of wage-earners subgroup of the new all-earners income table (levels not comparable to the pre-2022 employees series; cross-sections fine)",
        "cluster_vintage_by_file": {str(y): CLUSTER_VINTAGE[y] for y in years_all},
        "notes": [
            "wage reference year = file year - 1; the 2021 file's wage is a stale copy of the 2020 file (ref 2019)",
            "gini (wage earners) published 1999-2021 only",
            "internal-migration split unpublished 2002-2013; migration totals include aliya",
            "bagrut eligibility jumps with education reforms - cross-section only",
            "1999 file: regional-council clusters are on a 1-5 scale (not 1-10)",
            "pop normalized to persons (thousands in files through 2015)",
            "all analyses ecological - authority aggregates, not individuals",
        ],
    },
    "gradients": {
        "universe": "jewish-majority municipal authorities matched to election localities; identical rows per election for wage/acad (bagrut on its subuniverse)",
        "series": GRAD_SER,
        "trends_r_per_decade": TRENDS,
    },
    "migration": {
        "tests": tests,
        "coverage": "internal-migration years: 1999-2001 + 2014-2024 (split unpublished 2002-2013)",
        "scatter": sorted(SCATTER, key=lambda e: -e["w"]),
        "cases": CASES,
    },
    "gini": {"national_by_year": GINI_NAT, "link_dgini_drelsd_r": g_link, "link_n": len(xs)},
    "authorities": AUTH,
}
out_path = f"{ROOT}/data/rashuyot_panel.json"
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(OUT, fh, ensure_ascii=False, separators=(",", ":"))
log(f"\nwrote {out_path} ({os.path.getsize(out_path):,} bytes)")
LOG.close()
