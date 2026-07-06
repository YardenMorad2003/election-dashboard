# -*- coding: utf-8 -*-
"""Stage 2: for census-contradicting flags, find culprit venues and auto-verify
their coordinates against the MOE institution registry."""
import json, io, sys, csv, math, re, collections, urllib.request, urllib.parse, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = r"C:\Users\yarde\Downloads\election-dashboard-extracted\election-dashboard-main"
EM = r"C:\Users\yarde\elections-merge\data"
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

STOP = set("""בי ס ביה בית ספר יסודי תיכון חט ב חטיבת ביניים ממ ד ממלכתי דתי ע ש עש ביס
אולפנת אולפנא אולפנה גן ילדים גני מקיף עירוני מרכז קהילתי מתנ מתנס מועדון אשכול פיס חדש חדשה
ישיבת ישיבה תלמוד תורה ת בנות בנים לבנות לבנים כללי אזורי על שם החדש הישן אגף מבנה שלוחה קריית קרית""".split())

def core_name(venue):
    toks = [t for t in norm(venue).split() if t not in STOP and len(t) >= 2 and not t.isdigit()]
    return " ".join(toks)

# ---- load data
flags = json.load(open(SCRATCH + r"\national_flags.json", encoding="utf-8"))
sc = json.load(open(EM + r"\station_coordinates.json", encoding="utf-8"))["stations"]
fixes_raw = json.load(open(BASE + r"\analysis\statarea_inputs\station_coord_fixes.json", encoding="utf-8"))
fixes = {}
for sem, vmap in fixes_raw.items():
    if sem.startswith("_"): continue
    for ven, ll in vmap.items():
        fixes[(str(sem), norm(ven))] = (ll[0], ll[1])

g = json.load(open(BASE + r"\data\statarea_2022_geo.json", encoding="utf-8"))
cent, sem_of, feats_by_sem = {}, {}, collections.defaultdict(list)
for f in g["features"]:
    pts = []
    def collect(c):
        if isinstance(c[0], (int, float)): pts.append(c)
        else:
            for x in c: collect(x)
    collect(f["geometry"]["coordinates"])
    sid = str(f["properties"]["id"])
    cent[sid] = (sum(p[1] for p in pts)/len(pts), sum(p[0] for p in pts)/len(pts))
    sem_of[sid] = str(f["properties"]["semel"])
    feats_by_sem[str(f["properties"]["semel"])].append(f)

def pip(pt, ring):
    x, y = pt[1], pt[0]; inside = False; j = len(ring)-1
    for i in range(len(ring)):
        xi, yi = ring[i]; xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj-xi)*(y-yi)/(yj-yi)+xi: inside = not inside
        j = i
    return inside

def find_sa(sem, pt):
    for f in feats_by_sem.get(str(sem), []):
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            if pip(pt, poly[0]) and not any(pip(pt, h) for h in poly[1:]):
                return str(f["properties"]["id"])
    return None

city_bbox = {}
for sem, fs in feats_by_sem.items():
    cs = [cent[str(f["properties"]["id"])] for f in fs]
    la = [c[0] for c in cs]; ln = [c[1] for c in cs]
    city_bbox[sem] = (min(la)-0.02, max(la)+0.02, min(ln)-0.025, max(ln)+0.025)

# ---- filter flags to census-contradiction suspects
SUS = []
for r in flags:
    dat = r.get("datiyut") or ""
    if r["delta"] >= 25 and dat == "חילוני": SUS.append(r)
    elif r["delta"] <= -25 and dat == "חרדי": SUS.append(r)
SUS = SUS[:45]
print(f"census-contradiction suspects: {len(SUS)} (of {len(flags)} flags)\n")

# ---- per-year raw ballots + rh parties
PN = json.load(open(BASE + r"\data\parties_national.json", encoding="utf-8"))
rh_parties = {yr: {p["code"] for p in PN[yr]["party_list"] if p.get("bloc") in ("right", "haredi")} for yr in ("24", "25")}

raw = {}
for yr in ("24", "25"):
    idx = collections.defaultdict(lambda: [0, 0])   # (semel, ballot_base) -> [rh, tot]
    with open(EM + rf"\knesset{yr}_ballots.csv", encoding="utf-8-sig", errors="replace") as fh:
        rdr = csv.DictReader(fh)
        flds = rdr.fieldnames
        semcol = next(c for c in flds if "סמל" in c and "ישוב" in c and "בחירות" not in c)
        balcol = next(c for c in flds if "קלפי" in c)
        meta = [c for c in flds if any(w in c for w in ["שם","סמל","קלפי","בזב","מצביעים","פסולים","כשרים","ריכוז","שופט","ברזל"])]
        parties = [c for c in flds if c not in meta]
        for row in rdr:
            sem = row[semcol].strip()
            b = row[balcol].strip().split(".")[0]
            for p in parties:
                try: v = int(row[p] or 0)
                except: continue
                idx[(sem, b)][1] += v
                if p in rh_parties[yr]: idx[(sem, b)][0] += v
    raw[yr] = idx

# ---- CKAN
def ckan(q):
    url = "https://data.gov.il/api/3/action/datastore_search?" + urllib.parse.urlencode(
        {"resource_id": "5c5d6bb0-755d-470d-84b6-d7dd3135ba9c", "q": q, "limit": 300})
    req = urllib.request.Request(url, headers={"User-Agent": "datagov-external-client"})
    return json.load(urllib.request.urlopen(req, timeout=30))["result"]["records"]

ckan_cache = {}
def registry_lookup(core, sem):
    if not core: return []
    if core not in ckan_cache:
        try:
            ckan_cache[core] = ckan(core)
            time.sleep(0.4)
        except Exception:
            ckan_cache[core] = []
    la0, la1, ln0, ln1 = city_bbox.get(str(sem), (0, 0, 0, 0))
    hits = []
    ncore = norm(core)
    for r in ckan_cache[core]:
        nm = norm(str(r.get("SHEM_MOSAD", "")))
        if ncore not in nm: continue
        try: la, ln = float(r["UTM_Y"]), float(r["UTM_X"])
        except (TypeError, ValueError): continue
        if la0 <= la <= la1 and ln0 <= ln <= ln1:
            hits.append((r["SHEM_MOSAD"], r["SEMEL_MOSAD"], la, ln, r.get("RAMAT_DIYUK_MIKUM", "")))
    return hits

# ---- verify each suspect SA's venues
results = []
seen_venues = set()
for r in SUS:
    yr, sid, sem = r["yr"], r["sid"], r["semel"]
    bl = json.load(open(EM + rf"\ballot_locations_{yr}.json", encoding="utf-8"))["ballot_to_location"]
    venues = collections.defaultdict(list)   # venue -> [(ballot, valid)]
    with open(BASE + rf"\analysis\statarea_inputs\ballot_stat22_{yr}.csv", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if str(row["stat22"]) == sid:
                sm = str(int(float(row["semel"])))
                k = f"{sm}:{row['ballot']}"
                venues[bl.get(k, "?")].append((row["ballot"], row["valid"]))
    for ven, blist in venues.items():
        vkey = (sem, norm(ven))
        if vkey in seen_venues: continue
        seen_venues.add(vkey)
        # per-venue rh from raw
        rh = tot = 0
        for b, _ in blist:
            rr = raw[yr].get((sem, b.split(".")[0]))
            if rr: rh += rr[0]; tot += rr[1]
        ven_rh = round(100*rh/tot, 1) if tot else None
        # effective coordinate
        fix = fixes.get(vkey)
        ce = sc.get(f"{r.get('loc') or ''}|x")  # placeholder
        # find Cain entry by (settlement name unknown) — search by semel via ballot key: use first ballot
        eff = fix
        cain_src = "fix" if fix else None
        if not eff:
            # find any Cain station whose settlement maps to this semel AND ballot matches
            b0 = blist[0][0]
            for cand_key in (f"{r.get('loc')}|{b0}", f"{r.get('loc')}|{b0}.0"):
                pass
            # fallback: scan sc lazily by venue name+city bbox
            la0, la1, ln0, ln1 = city_bbox[str(sem)]
            nv = norm(ven)
            for st in sc.values():
                if norm(st.get("location") or "") == nv and st.get("lat") is not None:
                    if la0-0.05 <= st["lat"] <= la1+0.05 and ln0-0.05 <= st["lng"] <= ln1+0.05:
                        eff = (st["lat"], st["lng"]); cain_src = st.get("source"); break
        core = core_name(ven)
        reg = registry_lookup(core, sem) if core else []
        verdict = "UNVERIFIED"
        best = None
        if eff and reg:
            reg_d = sorted((dkm(eff, (la, ln)), nm, sm2, la, ln, acc) for nm, sm2, la, ln, acc in reg)
            d0, nm, sm2, la, ln, acc = reg_d[0]
            reg_sa = find_sa(sem, (la, ln))
            if d0 <= 0.35: verdict = "OK"
            elif d0 >= 0.5 and reg_sa and reg_sa != sid:
                verdict = "MISGEOCODE?"
            else: verdict = "AMBIG"
            best = {"reg_name": nm, "reg_sm": sm2, "d_km": round(d0, 2), "reg_sa": reg_sa,
                    "lat": round(la, 6), "lng": round(ln, 6), "acc": acc, "n_cand": len(reg)}
        results.append({"sid": sid, "sem": sem, "yr": yr, "sa_rh": r["rh"], "hood_rh": r["hood_rh"],
                        "venue": ven, "ballots": len(blist), "venue_rh": ven_rh,
                        "eff_src": cain_src, "verdict": verdict, "best": best})

json.dump(results, open(SCRATCH + r"\national_verdicts.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
order = {"MISGEOCODE?": 0, "AMBIG": 1, "UNVERIFIED": 2, "OK": 3}
results.sort(key=lambda x: (order[x["verdict"]], -(x["venue_rh"] or 0)))
for x in results:
    b = x["best"] or {}
    print(f"[{x['verdict']:<11}] {x['sid']} sa_rh={x['sa_rh']} hood={x['hood_rh']} | {x['venue']!r} "
          f"({x['ballots']} ballots, venue_rh={x['venue_rh']}) src={x['eff_src']} "
          + (f"-> reg {b.get('reg_name')!r} d={b.get('d_km')}km sa={b.get('reg_sa')} acc={b.get('acc')} cands={b.get('n_cand')}" if b else ""))
