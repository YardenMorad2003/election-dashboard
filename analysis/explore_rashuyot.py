# -*- coding: utf-8 -*-
"""Deep exploration of the CBS annual local-authority profiles (1999-2024)
BEFORE building a Phase-4 harmonized panel. Three passes:

  1. CATALOG  — per year, which column names match each key-variable pattern
                (exposes naming drift + missing years; printed per variable).
  2. EXTRACT  — pilot panel (semel x year) for: avg wage, Gini, migration
                balance (total/internal), bagrut %, socio cluster, population.
                Handles all three layout eras (transposed / rows-hdr0 / rows-hdr3).
  3. QC + PREVIEW — unit/plausibility checks, cross-source validation vs the
                Phase-3 files, and quick previews of the candidate analyses
                (annual wage gradient, migration vs political shift, Gini trend).

Outputs: scratchpad rashuyot_catalog.json + rashuyot_pilot_panel.csv; log to stdout.
Run: python -X utf8 analysis/explore_rashuyot.py  (~1-2 min)
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
SCRATCH = (r"C:\Users\yarde\AppData\Local\Temp\claude\C--Users-yarde"
           r"\78afd9b2-f95d-46e7-86e4-17b754853316\scratchpad")

SKIP_SHEETS = ("תוכן", "הערות", "תיקונים", "סיכומ", "מקרא")


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


# variable name matchers: (must-contain list of alternatives via |, must-not-contain)
def match_var(name, var):
    n = name
    if var == "wage":
        return (re.search(r"^שכר ממוצע לחודש של (ה?)שכירים", n) or
                re.search(r"^שכר חודשי ממוצע של שכיר", n) or
                n == "שכר ממוצע" or
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
               "קומפקטי" not in n and "פריפריאלי" not in n and "מותאמ" not in n
    if var == "pop":
        return re.search(r"^סה.?כ אוכלוסי", n) or "אוכלוסייה בסוף השנה" in n or \
               re.search(r"^אוכלוסי(י?)ה - סה", n) or n == "אוכלוסייה"
    return False


VARS = ["pop", "cluster", "wage", "gini", "mig_total", "mig_internal", "bagrut"]

# ---------------- pass over files ----------------
catalog = {}                       # year -> var -> [matched names]
panel = {}                         # (semel, year) -> {var: value, name: str}
NAMES = {}                         # semel -> heb name (latest)
DUMP_YEARS = {2006, 2007, 2012, 2022, 2023, 2024}
DUMP_TERMS = ["שכר", "הכנסה ממוצ", "ג'יני", "שוויון", "הגירה", "רמה חברתית", "אשכול"]
dump = {}                          # year -> set of names hitting dump terms

files = sorted([f for f in os.listdir(D) if year_of(f)], key=year_of)
for f in files:
    yr = year_of(f)
    path = os.path.join(D, f)
    cat = {v: [] for v in VARS}
    xl = pd.ExcelFile(path)
    for s in xl.sheet_names:
        if any(k in s for k in SKIP_SHEETS):
            continue
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
                if yr in DUMP_YEARS and any(t in nm for t in DUMP_TERMS):
                    dump.setdefault(yr, set()).add(nm)
                for var in VARS:
                    if match_var(nm, var):
                        cat[var].append(nm)
                        for j, sem in enumerate(semels):
                            if sem is None: continue
                            val = num(df.iat[rr, c+1+j])
                            if val is None: continue
                            panel.setdefault((int(sem), yr), {}).setdefault(var, val)
            if name_row is not None:
                for j, sem in enumerate(semels):
                    if sem is not None and isinstance(df.iat[name_row, c+1+j], str):
                        NAMES[int(sem)] = clean(df.iat[name_row, c+1+j])
        else:
            # column names live on the semel row (fallback: row above/below)
            def colname(j):
                for rr in (r, r+1, r-1, r-2):
                    if 0 <= rr < len(df):
                        v = df.iat[rr, j]
                        if isinstance(v, str) and re.search(r"[א-ת]", v):
                            return clean(v)
                return ""
            name_col = None
            for j in range(min(6, df.shape[1])):
                if "שם" in colname(j) and "רשות" in colname(j):
                    name_col = j; break
            var_cols = {}
            for j in range(df.shape[1]):
                nm = colname(j)
                if not nm: continue
                if yr in DUMP_YEARS and any(t in nm for t in DUMP_TERMS):
                    dump.setdefault(yr, set()).add(nm)
                for var in VARS:
                    if match_var(nm, var) and var not in var_cols:
                        var_cols[var] = j
                        cat[var].append(nm)
            for i in range(r + 1, len(df)):
                sem = num(df.iat[i, c])
                if sem is None: continue
                sem = int(sem)
                if name_col is not None and isinstance(df.iat[i, name_col], str):
                    NAMES[sem] = clean(df.iat[i, name_col])
                for var, j in var_cols.items():
                    val = num(df.iat[i, j])
                    if val is not None:
                        panel.setdefault((sem, yr), {}).setdefault(var, val)
    catalog[yr] = {v: sorted(set(n))[:3] for v, n in cat.items()}

# ---------------- 1. catalog report ----------------
print("=" * 100)
print("[1] CATALOG — matched name per variable per year (naming drift)")
years = sorted(catalog)
for var in VARS:
    print(f"\n--- {var} ---")
    prev = None
    for yr in years:
        names = catalog[yr][var]
        cov = sum(1 for (s, y), d in panel.items() if y == yr and var in d)
        tag = names[0] if names else "(NOT FOUND)"
        if tag != prev:
            print(f"  {yr}: n={cov:>3}  {tag}")
            prev = tag
        else:
            print(f"  {yr}: n={cov:>3}  ''")

with open(f"{SCRATCH}\\rashuyot_catalog.json", "w", encoding="utf-8") as fh:
    json.dump(catalog, fh, ensure_ascii=False, indent=1)

# diagnostics dump for problem years
print("\n--- diagnostics: candidate names in problem years ---")
for yr in sorted(dump):
    print(f"  {yr}:")
    for nm in sorted(dump[yr]):
        print(f"    {nm[:110]}")

# ---------------- 2. pilot panel ----------------
rows = []
for (sem, yr), d in sorted(panel.items()):
    rows.append({"semel": sem, "year": yr, "name": NAMES.get(sem, ""), **d})
pdf = pd.DataFrame(rows)
# pop unit normalization: files through ~2016 report thousands, later ones persons
for yr, grp in pdf.groupby("year"):
    if "pop" in pdf and grp["pop"].sum() < 20000:
        pdf.loc[pdf.year == yr, "pop"] *= 1000
pdf.to_csv(f"{SCRATCH}\\rashuyot_pilot_panel.csv", index=False, encoding="utf-8-sig")
print(f"\n[2] pilot panel: {len(pdf)} authority-years, {pdf['semel'].nunique()} authorities, "
      f"years {pdf['year'].min()}-{pdf['year'].max()}")

# ---------------- 3. QC ----------------
print("\n" + "=" * 100)
print("[3] QC")
# national means / sums per year for unit sanity
for var, agg in [("wage", "mean"), ("gini", "mean"), ("bagrut", "mean"),
                 ("mig_internal", "sum"), ("mig_total", "sum"), ("pop", "sum")]:
    sub = pdf.dropna(subset=[var]) if var in pdf else pd.DataFrame()
    if sub.empty:
        print(f"  {var}: NO DATA"); continue
    g = sub.groupby("year")[var].agg(agg)
    yrs_show = [y for y in [1999, 2003, 2008, 2013, 2016, 2019, 2021, 2024] if y in g.index]
    print(f"  {var} ({agg} by yr): " + "  ".join(f"{y}:{g[y]:,.1f}" for y in yrs_show))

# cross-source: cluster 2013 here vs socio-index t02 file
t13 = pd.read_excel(r"C:/Users/yarde/Downloads/t02 (1).xls", sheet_name="t02", header=None)
ref13 = {}
for _, r in t13.iloc[8:].iterrows():
    cd, cl = num(r[1]), num(r[6])
    if cd is not None and cl is not None:
        ref13[int(cd)] = int(cl)
sub = pdf[(pdf.year == 2013) & pdf.cluster.notna()]
both = [(int(r.cluster), ref13[int(r.semel)]) for _, r in sub.iterrows() if int(r.semel) in ref13]
if both:
    eq = sum(1 for a, b in both if a == b)
    print(f"  cluster-2013 vs socio-index publication: {eq}/{len(both)} exact match")

# cross-source: wage 2021 vs socioeconomic.json income per capita (different concept; expect r~0.7-0.9)
soc = json.load(open(f"{ROOT}/data/socioeconomic.json", encoding="utf-8"))
inc = {int(r["code"]): r.get("avg_monthly_income_per_capita") for r in soc if r.get("code")}
sub = pdf[(pdf.year == 2021) & pdf.wage.notna()]
xs, ys = [], []
for _, r in sub.iterrows():
    v = inc.get(int(r.semel))
    if isinstance(v, (int, float)):
        xs.append(r.wage); ys.append(v)
if len(xs) > 30:
    print(f"  wage-2021 vs socio-json income/capita: r={np.corrcoef(xs, ys)[0,1]:.3f} (n={len(xs)}) [different concepts]")

# ---------------- 4. ANALYSIS PREVIEWS ----------------
print("\n" + "=" * 100)
print("[4] ANALYSIS PREVIEWS")
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

def is_jewishish(x):
    aps = [d.get("arab_pct") for d in x["data"].values() if d.get("arab_pct") is not None]
    return aps and (sum(aps) / len(aps)) < 30

SEM2LOC = {}
for sem, nm in NAMES.items():
    k = norm(nm)
    if k in LOC:
        SEM2LOC[sem] = LOC[k]
print(f"  name join: {len(SEM2LOC)}/{len(NAMES)} authorities matched to localities.json")

def wcorr(xs, ys, ws):
    xs, ys, ws = map(np.asarray, (xs, ys, ws))
    W = ws.sum()
    mx, my = (xs*ws).sum()/W, (ys*ws).sum()/W
    cov = (ws*(xs-mx)*(ys-my)).sum()
    vx, vy = (ws*(xs-mx)**2).sum(), (ws*(ys-my)**2).sum()
    return cov/math.sqrt(vx*vy) if vx > 0 and vy > 0 else None

EK = {"15": 1999, "16": 2003, "17": 2006, "18": 2009, "19": 2013, "20": 2015,
      "21": 2019, "22": 2019, "23": 2020, "24": 2021, "25": 2022}

# A. annual wage & bagrut gradients per election (Jewish-majority authorities)
print("\n  [A] RH-share gradient on ln(avg wage) and bagrut%, per election (Jewish-majority):")
for k, yr in EK.items():
    sub = pdf[pdf.year == yr]
    res = {}
    for var in ["wage", "bagrut"]:
        xs, ys, ws = [], [], []
        for _, r in sub.iterrows():
            x = SEM2LOC.get(int(r.semel))
            v = r.get(var)
            if x is None or v is None or (isinstance(v, float) and math.isnan(v)) or not is_jewishish(x):
                continue
            d = x["data"].get(k)
            if not d or d.get("right_haredi_pct") is None: continue
            w = d.get("bzb") or d.get("kosher_votes")
            if not w: continue
            xs.append(math.log(v) if var == "wage" else v)
            ys.append(d["right_haredi_pct"]); ws.append(w)
        res[var] = (wcorr(xs, ys, ws), len(xs))
    wr, wn = res["wage"]; br, bn = res["bagrut"]
    print(f"    K{k} ({yr}): wage r={'—' if wr is None else format(wr,'+.3f')} (n={wn})"
          f"   bagrut r={'—' if br is None else format(br,'+.3f')} (n={bn})")

# B. migration balance vs political shift
print("\n  [B] cumulative internal-migration rate vs RH-share change K15->K25:")
mig = pdf[pdf.mig_internal.notna() & pdf["pop"].notna()].copy()
cum = {}
for sem, grp in mig.groupby("semel"):
    rate = (grp.mig_internal / grp["pop"]).mean() * 1000     # avg annual per-1000 rate
    cum[int(sem)] = (rate, len(grp))
xs, ys, ws, tab = [], [], [], []
for sem, (rate, nyr) in cum.items():
    x = SEM2LOC.get(sem)
    if x is None or nyr < 10 or not is_jewishish(x): continue
    d15, d25 = x["data"].get("15"), x["data"].get("25")
    if not d15 or not d25: continue
    rh15, rh25 = d15.get("right_haredi_pct"), d25.get("right_haredi_pct")
    if rh15 is None or rh25 is None: continue
    w = d25.get("bzb") or 0
    if not w: continue
    xs.append(rate); ys.append(rh25 - rh15); ws.append(w)
    tab.append((rate, rh25 - rh15, NAMES.get(sem, "?"), w))
r = wcorr(xs, ys, ws)
print(f"    weighted r = {'—' if r is None else format(r,'+.3f')} (n={len(xs)} Jewish-majority authorities, >=10 yrs data)")
# sharper tests: does migration AMPLIFY the existing lean / increase distinctiveness?
rh15s = [t[1] for t in []]  # placeholder to keep flake quiet
nat15 = np.average([SEM2LOC[s]["data"]["15"]["right_haredi_pct"] for s, (rt, ny) in cum.items()
                    if s in SEM2LOC and SEM2LOC[s]["data"].get("15", {}).get("right_haredi_pct") is not None],
                   weights=[SEM2LOC[s]["data"]["15"].get("bzb") or 1 for s, (rt, ny) in cum.items()
                            if s in SEM2LOC and SEM2LOC[s]["data"].get("15", {}).get("right_haredi_pct") is not None])
nat25 = np.average([SEM2LOC[s]["data"]["25"]["right_haredi_pct"] for s, (rt, ny) in cum.items()
                    if s in SEM2LOC and SEM2LOC[s]["data"].get("25", {}).get("right_haredi_pct") is not None],
                   weights=[SEM2LOC[s]["data"]["25"].get("bzb") or 1 for s, (rt, ny) in cum.items()
                            if s in SEM2LOC and SEM2LOC[s]["data"].get("25", {}).get("right_haredi_pct") is not None])
amp_x, amp_y, dist_y, ws2 = [], [], [], []
for sem, (rate, nyr) in cum.items():
    x = SEM2LOC.get(sem)
    if x is None or nyr < 10 or not is_jewishish(x): continue
    d15, d25 = x["data"].get("15"), x["data"].get("25")
    if not d15 or not d25: continue
    rh15, rh25 = d15.get("right_haredi_pct"), d25.get("right_haredi_pct")
    if rh15 is None or rh25 is None: continue
    w = d25.get("bzb") or 0
    if not w: continue
    amp_x.append(rate * (1 if rh15 >= nat15 else -1))
    amp_y.append(rh25 - rh15)
    dist_y.append(abs(rh25 - nat25) - abs(rh15 - nat15))
    ws2.append(w)
r_amp = wcorr(amp_x, amp_y, ws2)
r_dist = wcorr([abs(v) for v in amp_x], dist_y, ws2)
print(f"    AMPLIFICATION test (rate x sign(initial lean) vs dRH): r = {r_amp:+.3f}")
print(f"    DISTINCTIVENESS test (|rate| vs d|RH - national|):     r = {r_dist:+.3f}")
tab.sort(key=lambda t: -t[0])
print("    top net-gainers (per-1000/yr, dRH):  " + "; ".join(f"{n} {rt:+.1f} ({dr:+.1f})" for rt, dr, n, _ in tab[:6]))
print("    top net-losers:                      " + "; ".join(f"{n} {rt:+.1f} ({dr:+.1f})" for rt, dr, n, _ in tab[-6:]))

# C. Gini trend + link to Phase-3 dispersion change
print("\n  [C] city wage-Gini: pop-weighted national mean by year:")
g = pdf[pdf.gini.notna() & pdf["pop"].notna()]
byyr = {yr: np.average(grp.gini, weights=grp["pop"]) for yr, grp in g.groupby("year") if len(grp) > 50}
print("    " + "  ".join(f"{y}:{v:.3f}" for y, v in sorted(byyr.items()) if y in
                         (1999, 2002, 2005, 2008, 2011, 2014, 2017, 2019, 2021)))
demo = json.load(open(f"{ROOT}/data/demographics_panel.json", encoding="utf-8"))
disp = demo["dispersion"]
code2d = {v["code"]: v["series"] for v in disp.values()}
xs, ys = [], []
for sem in set(g.semel):
    ser = code2d.get(int(sem))
    if not ser or "2008" not in ser or "2019" not in ser: continue
    g08 = g[(g.semel == sem) & (g.year == 2008)]; g19 = g[(g.semel == sem) & (g.year == 2019)]
    if g08.empty or g19.empty: continue
    xs.append(float(g19.gini.iloc[0]) - float(g08.gini.iloc[0]))
    ys.append(ser["2019"]["rel_sd"] - ser["2008"]["rel_sd"])
if len(xs) > 20:
    print(f"    dGini(08->19) vs d(rel_sd stat-area dispersion): r={np.corrcoef(xs, ys)[0,1]:+.3f} (n={len(xs)})")

print("\ndone — catalog + pilot panel saved to scratchpad")
