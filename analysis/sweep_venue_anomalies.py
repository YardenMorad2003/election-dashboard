# -*- coding: utf-8 -*-
"""
Full national venue-level sweep, automating the manual verification recipe:

1. Flag venues whose rh diverges >=35pp from their 6-nearest same-city venues
   (<=1.5 km), votes >= 250, K24 U K25 — plus ISOLATED venues (no same-city
   neighbor within 1.5 km).
2. For each flag: MOE-registry candidates in-city (normalized core-name match,
   accuracy high/very-high only, generic names excluded).
3. Verdicts with a PROFILE-COHERENCE gate (the Amiel logic, automated):
   - OK/ENCLAVE: nearest candidate <= 0.35 km from current coord.
   - CONFIRM: best candidate >= 0.5 km away AND moving there improves
     |venue_rh - local_hood_rh| by >= 15pp AND residual <= 20pp.
   - OPEN: everything else (no registry, generic name, ambiguous).
4. CONFIRMed venues drag along sibling strings parked at the same wrong spot.
"""
import json, io, sys, math, re, collections, urllib.request, urllib.parse, time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"C:\Users\yarde\Downloads\election-dashboard-extracted\election-dashboard-main"
SCRATCH = r"C:\Users\yarde\AppData\Local\Temp\claude\C--Users-yarde\cac22b10-e30f-4c26-8097-a59c76e120c8\scratchpad"
KX = 0.845
def dkm(a, b): return math.hypot((a[1]-b[1])*111*KX, (a[0]-b[0])*111)

GERESH = "'׳״‘’“”\"`"
def norm(s):
    if not s: return ""
    for ch in GERESH: s = s.replace(ch, "")
    s = re.sub(r"[()\-,./\\:;+]", " ", s)
    s = s.replace("יי", "י").replace("וו", "ו")
    return " ".join(s.split())

STOP = set("""בי ס ביה בית ספר יסודי תיכון חט ב חטיבת ביניים ממ ד ממלכתי דתי ע ש עש ביס בנין בניין
אולפנת אולפנא אולפנה גן ילדים גני מקיף עירוני מרכז קהילתי מתנ מתנס מועדון אשכול פיס חדש חדשה חינוך
ישיבת ישיבה תלמוד תורה ת בנות בנים לבנות לבנים כללי אזורי על שם החדש הישן אגף מבנה שלוחה קריית קרית
כניסה ראשית צפונית דרומית אולם ספורט סניף שכ שכונת רח רחוב הספר""".split())
def core_name(v):
    toks = [t for t in norm(v).split() if t not in STOP and len(t) >= 2 and not t.isdigit()]
    return " ".join(toks)

# ---------- load dots (post-rebuild) ----------
DOTS = {}
for yr in ("24", "25"):
    DOTS[yr] = json.load(open(BASE + rf"\data\venue_dots_k{yr}.json", encoding="utf-8"))["venues"]

def hood_rh(venues_of_city, pt, self_name):
    """vote-weighted rh of the 6 nearest other venues within 1.5km of pt"""
    near = sorted(((dkm(pt, (o[0], o[1])), o) for o in venues_of_city if o[7] != self_name), key=lambda x: x[0])
    sel = [o for d, o in near[:6] if d <= 1.5]
    if len(sel) < 3: return None
    w = sum(o[2] for o in sel)
    return sum(o[5] * o[2] for o in sel) / w

by_city = {}
for yr in ("24", "25"):
    c = collections.defaultdict(list)
    for v in DOTS[yr]: c[v[8]].append(v)
    by_city[yr] = c

# ---------- stage 1: flags ----------
flags = {}   # (sem, norm_name) -> record
for yr in ("24", "25"):
    for sem, vs in by_city[yr].items():
        if len(vs) < 6: continue
        for v in vs:
            lat, lng, valid, win, winpct, rh, nb, name, _ = v
            if valid < 250 or not name: continue
            h = hood_rh(vs, (lat, lng), name)
            isolated = h is None
            if not isolated and abs(rh - h) < 35: continue
            key = (sem, norm(name))
            score = (abs(rh - (h if h is not None else 50))) * valid
            if key not in flags or score > flags[key]["score"]:
                flags[key] = {"yr": yr, "sem": sem, "name": name, "pt": (lat, lng), "valid": valid,
                              "rh": rh, "hood": None if h is None else round(h, 1),
                              "isolated": isolated, "score": round(score)}
print(f"stage 1: {len(flags)} flagged venues (K24∪K25)")

# ---------- stage 2: registry ----------
def ckan(q):
    url = "https://data.gov.il/api/3/action/datastore_search?" + urllib.parse.urlencode(
        {"resource_id": "5c5d6bb0-755d-470d-84b6-d7dd3135ba9c", "q": q, "limit": 300})
    req = urllib.request.Request(url, headers={"User-Agent": "datagov-external-client"})
    return json.load(urllib.request.urlopen(req, timeout=30))["result"]["records"]

city_bbox = {}
for yr in ("24", "25"):
    for sem, vs in by_city[yr].items():
        la = [v[0] for v in vs]; ln = [v[1] for v in vs]
        b = city_bbox.get(sem)
        nb_ = (min(la)-0.02, max(la)+0.02, min(ln)-0.025, max(ln)+0.025)
        city_bbox[sem] = nb_ if not b else (min(b[0],nb_[0]), max(b[1],nb_[1]), min(b[2],nb_[2]), max(b[3],nb_[3]))

cache = {}
def registry(core, sem):
    if not core or len(core) < 3: return []
    if core not in cache:
        try:
            cache[core] = ckan(core); time.sleep(0.35)
        except Exception:
            cache[core] = []
    la0, la1, ln0, ln1 = city_bbox[sem]
    ncore = norm(core)
    out = []
    for r in cache[core]:
        nm = norm(str(r.get("SHEM_MOSAD", "")))
        if ncore not in nm: continue
        acc = str(r.get("RAMAT_DIYUK_MIKUM", ""))
        if "גבוהה" not in acc: continue
        try: la, ln = float(r["UTM_Y"]), float(r["UTM_X"])
        except (TypeError, ValueError): continue
        if la0 <= la <= la1 and ln0 <= ln <= ln1:
            out.append((r["SHEM_MOSAD"], la, ln, acc))
    return out

# ---------- stage 3: verdicts ----------
confirms, cleared, openlist = [], [], []
for (sem, nname), f in sorted(flags.items(), key=lambda kv: -kv[1]["score"]):
    yr = f["yr"]
    core = core_name(f["name"])
    cands = registry(core, sem)
    if not cands:
        openlist.append({**f, "why": "no-registry" if core else "generic-name"})
        continue
    dists = sorted((dkm(f["pt"], (la, ln)), nm, la, ln, acc) for nm, la, ln, acc in cands)
    d0 = dists[0][0]
    if d0 <= 0.35:
        cleared.append({**f, "reg": dists[0][1], "d": round(d0, 2)})
        continue
    # coherence gate: pick the candidate whose local hood best matches the voters
    vs = by_city[yr][sem]
    cur_h = f["hood"]
    best = None
    for d, nm, la, ln, acc in dists:
        if d < 0.5: continue
        h2 = hood_rh(vs, (la, ln), f["name"])
        if h2 is None: continue
        resid = abs(f["rh"] - h2)
        if best is None or resid < best["resid"]:
            best = {"nm": nm, "la": la, "ln": ln, "acc": acc, "d": round(d, 2), "dest_hood": round(h2, 1), "resid": resid}
    cur_resid = abs(f["rh"] - cur_h) if cur_h is not None else 999
    if best and best["resid"] <= 20 and (cur_resid - best["resid"]) >= 15:
        confirms.append({**f, **best})
    else:
        openlist.append({**f, "why": f"ambig d0={d0:.2f}" + (f" resid={best['resid']:.0f}" if best else "")})

print(f"\n=== CONFIRM ({len(confirms)}):")
for c in confirms:
    print(f"  sem {c['sem']:<5} {c['name']!r:<40} v={c['valid']:>5} rh={c['rh']:>5} hood={c['hood']} "
          f"-> {c['nm']!r} d={c['d']}km dest_hood={c['dest_hood']} @({c['la']:.5f},{c['ln']:.5f}) [{c['acc']}]")
print(f"\n=== CLEARED at current spot ({len(cleared)}):")
for c in cleared:
    print(f"  sem {c['sem']:<5} {c['name']!r:<40} rh={c['rh']} hood={c['hood']} d={c['d']}km (enclave/real)")
print(f"\n=== OPEN ({len(openlist)}):")
for c in sorted(openlist, key=lambda x: -x["score"])[:35]:
    print(f"  sem {c['sem']:<5} {c['name']!r:<40} v={c['valid']:>5} rh={c['rh']:>5} hood={c['hood']} [{c['why']}]")

json.dump({"confirms": confirms, "cleared": cleared, "open": openlist},
          open(SCRATCH + r"\sweep2_results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
