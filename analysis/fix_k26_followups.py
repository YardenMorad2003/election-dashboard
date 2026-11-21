# -*- coding: utf-8 -*-
"""
fix_k26_followups.py — two data repairs found while wiring K26 (2026-11-20). Idempotent.

1. parties_by_locality.json, K23/K24/K25: rows were keyed by the mangled CEC export
   spelling of those years ('אום אלפחם'), so ~121 localities per election did not join
   to localities.json by name (party comparisons silently fell back for them).
   Re-keyed to the canonical localities.json row name through the official files:
   pbl key == official 'שם ישוב' -> official 'סמל ישוב' -> localities.json row (semel).
   Values are not touched. K13-K22 are left as they are (no official semel source here).

2. socioeconomic.json: election_data["26"] added per municipality from localities.json,
   joined on code == semel, with the same fields the K25 entries carry (+ third_pct).

Run: python -X utf8 analysis/fix_k26_followups.py     Report: analysis/k26_followups_report.txt
"""
import json, os, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); D = os.path.join(ROOT, "data")
rep = []
def load(p): return json.load(open(p, encoding="utf-8"))
def save(p, o):
    b = p + ".bak_prek26"
    if not os.path.exists(b): shutil.copyfile(p, b)
    json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=False)

loc = load(os.path.join(D, "localities.json"))
by_semel = {r["semel"]: r for r in loc if r.get("semel") is not None}
names = {r["name"] for r in loc}

pbl_path = os.path.join(D, "parties_by_locality.json"); pbl = load(pbl_path)
for k in ("23", "24", "25"):
    off = load(os.path.join(HERE, "official_cec", f"k{k}_locality.json"))
    semel_of = {}
    for r in off: semel_of.setdefault(r["שם ישוב"], []).append(r["סמל ישוב"])
    new, moved, left = {}, 0, []
    for key, row in pbl[k].items():
        target = key
        if key not in names:
            s = semel_of.get(key, [])
            cand = by_semel.get(s[0]) if len(s) == 1 else None
            if cand is not None and k in cand["data"]:
                target = cand["name"]; moved += 1
            else:
                left.append(key)
        assert target not in new, f"K{k}: collision on {target}"
        new[target] = row
    assert len(new) == len(pbl[k])
    pbl[k] = new
    rep.append(f"pbl K{k}: {len(new)} rows; re-keyed {moved}; still not a row name: {len(left)} {left}")
    rows_k = {r['name'] for r in loc if k in r['data']}
    rep.append(f"   rows with K{k} lacking a pbl entry: {sorted(rows_k - set(new))}")
save(pbl_path, pbl)

soc_path = os.path.join(D, "socioeconomic.json"); soc = load(soc_path)
tmpl = None; n = 0; miss = []
for m in soc:
    ed = m.get("election_data") or {}
    if tmpl is None and "25" in ed: tmpl = list(ed["25"].keys())
for m in soc:
    r = by_semel.get(m.get("code"))
    if r is None or "26" not in r["data"]: miss.append(m["name"]); continue
    e = r["data"]["26"]
    m.setdefault("election_data", {})["26"] = {f: e[f] for f in tmpl if f in e} | {"third_pct": e["third_pct"]}
    if "elections_count" in m: m["elections_count"] = len(m["election_data"])
    n += 1
save(soc_path, soc)
rep.append(f"socioeconomic: K26 added to {n}/{len(soc)} municipalities; fields = {tmpl} + third_pct; missing: {miss}")
open(os.path.join(HERE, "k26_followups_report.txt"), "w", encoding="utf-8").write("\n".join(rep))
print("done")
