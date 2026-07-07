# -*- coding: utf-8 -*-
"""
make_manual_review.py — sortable review page for the venue-placement MANUAL piles
(built 2026-07-06 after the user out-arbitrated the automation three times in one
evening: kashish, gan-dekel, gan-hadas).

Merges, deduped by (semel, venue):
  - sa_mismatch_resolve.json "manual"  (sub-1.5km SA mismatches, weak geocode)
  - sa_mismatch_resolve.json "has_fix" (existing hand fix disagrees with geocode)
  - k25_official_sweep.json manual flags (>1.5km, no registry/street confirmation)

Each row: city, venue, official address, votes, distance, SA current -> SA of the
address geocode, map links (current point / geocode point / address search /
govmap), a verdict select + note. "ייצוא" dumps decisions as JSON for the next
apply pass. Local audit artifact — not for the public repo.

Writes analysis/manual_review.html.
Run: python -X utf8 analysis/make_manual_review.py
"""
import json, os, sys, html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAP = os.path.join(HERE, "statarea_inputs")
sys.path.insert(0, HERE)
from build_venue_dots import norm  # noqa: E402


def main():
    res = json.load(open(os.path.join(SNAP, "sa_mismatch_resolve.json"), encoding="utf-8"))
    sweep = json.load(open(os.path.join(SNAP, "k25_official_sweep.json"), encoding="utf-8"))
    cache = json.load(open(os.path.join(SNAP, "k25_address_geocodes.json"), encoding="utf-8"))
    fixes = json.load(open(os.path.join(SNAP, "station_coord_fixes.json"), encoding="utf-8"))
    fixed = {(sem, norm(v)) for sem, vm in fixes.items() if not sem.startswith("_") for v in vm}

    rows, seen = [], set()

    def add(sem, city, venue, addr, valid, cur, geo, d, sa_cur, sa_geo, tag):
        key = (str(sem), norm(venue or ""))
        if key in seen:
            return
        seen.add(key)
        if key in fixed and tag != "פיקס-קיים":
            tag = "פיקס-קיים*"          # fixed since the pile was computed (e.g. tonight)
        rows.append({"sem": str(sem), "city": city, "venue": venue, "addr": addr,
                     "valid": valid, "cur": cur, "geo": geo, "d": d,
                     "sa_cur": sa_cur, "sa_geo": sa_geo, "tag": tag})

    for c in res["manual"]:
        gc = cache.get(f"{c['city']}|{c['addr']}")
        add(c["semel"], c["city"], c["venue"], c["addr"], c["valid"], c["cur"],
            gc, None, c.get("sa_cur"), c.get("sa_geo"), "תת-1.5")
    for c in res["has_fix"]:
        gc = cache.get(f"{c['city']}|{c['addr']}")
        add(c["semel"], c["city"], c["venue"], c["addr"], c["valid"], None,
            gc, c.get("d_km"), c.get("sa_cur"), c.get("sa_geo"), "פיקס-קיים")
    for f in sweep["flags"]:
        if f["verdict"] != "manual":
            continue
        add(f["semel"], f["city"], f["venue"], f["addr22"], f["valid"], f["cur"],
            f.get("geo"), f.get("d_km"), None, None, "מעל-1.5")

    rows.sort(key=lambda r: -(r["valid"] or 0))
    data = json.dumps(rows, ensure_ascii=False)
    n_sub = sum(1 for r in rows if r["tag"] == "תת-1.5")
    n_over = sum(1 for r in rows if r["tag"] == "מעל-1.5")
    n_fix = sum(1 for r in rows if r["tag"].startswith("פיקס"))

    page = """<!DOCTYPE html>
<html lang="he" dir="rtl"><head><meta charset="utf-8">
<title>ביקורת ידנית — מיקומי משכני קלפי K25</title>
<style>
:root{--bg:#0b0f1a;--panel:#111827;--border:#26324a;--text:#dbe4f3;--muted:#8ba3c7;--acc:#4a9eff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,'Segoe UI',sans-serif;font-size:.9rem}
header{position:sticky;top:0;background:var(--panel);border-bottom:1px solid var(--border);padding:10px 16px;z-index:5}
h1{font-size:1.05rem;margin:0 0 4px}.sub{color:var(--muted);font-size:.8rem}
.controls{display:flex;gap:10px;margin-top:8px;align-items:center;flex-wrap:wrap}
input[type=text]{background:#0e1526;border:1px solid var(--border);color:var(--text);padding:5px 10px;border-radius:8px;width:240px}
button{background:#16233d;border:1px solid var(--border);color:var(--text);padding:5px 12px;border-radius:8px;cursor:pointer}
button:hover{border-color:var(--acc)}
table{border-collapse:collapse;width:100%}
th{position:sticky;top:96px;background:#101a30;border-bottom:1px solid var(--border);padding:6px 8px;font-size:.78rem;color:var(--muted);cursor:pointer;text-align:right;white-space:nowrap}
td{border-bottom:1px solid #1b2438;padding:5px 8px;vertical-align:top}
tr:hover td{background:#0f1729}
.n{font-variant-numeric:tabular-nums;direction:ltr;display:inline-block}
.tag{font-size:.7rem;padding:1px 7px;border-radius:9px;border:1px solid var(--border);white-space:nowrap}
.tag.t1{color:#fbbf24}.tag.t2{color:#f87171}.tag.t3{color:#a78bfa}
a{color:var(--acc);text-decoration:none;white-space:nowrap}a:hover{text-decoration:underline}
select,td input[type=text]{background:#0e1526;border:1px solid var(--border);color:var(--text);border-radius:6px;padding:2px 6px;font-size:.8rem}
td input[type=text]{width:130px}
#exportBox{width:100%;height:140px;background:#0e1526;color:var(--text);border:1px solid var(--border);border-radius:8px;margin:10px 16px;display:none;font-family:monospace;font-size:.75rem;direction:ltr}
.decided td{opacity:.55}
</style></head><body>
<header>
<h1>ביקורת ידנית — מיקומי משכני קלפי (K25)</h1>
<div class="sub">__NSUB__ תת-1.5 ק"מ (SA שונה, גיאוקוד חלש) · __NOVER__ מעל-1.5 ק"מ (ללא אימות) · __NFIX__ פיקס-קיים חולק על הכתובת · ממוין לפי קולות. לחץ על כותרת עמודה למיון. סמן הכרעה ← ייצוא JSON.</div>
<div class="controls">
<input type="text" id="flt" placeholder="סינון עיר / משכן / כתובת...">
<button onclick="exportJSON()">📋 ייצוא הכרעות</button>
<span class="sub" id="cnt"></span>
</div>
</header>
<textarea id="exportBox" readonly></textarea>
<table id="tbl"><thead><tr>
<th data-k="city">עיר</th><th data-k="venue">משכן</th><th data-k="addr">כתובת רשמית</th>
<th data-k="valid">קולות</th><th data-k="d">ק"מ</th><th>SA נוכחי ← כתובת</th>
<th>מפות</th><th data-k="tag">סוג</th><th>הכרעה</th><th>הערה</th>
</tr></thead><tbody id="tb"></tbody></table>
<script>
const DATA = __DATA__;
let sortK = 'valid', sortDir = -1;
function gm(ll){ return 'https://maps.google.com/?q=' + ll[0] + ',' + ll[1]; }
function links(r){
  const L = [];
  if(r.cur) L.push('<a target="_blank" href="' + gm(r.cur) + '">נוכחי</a>');
  if(r.geo) L.push('<a target="_blank" href="' + gm(r.geo) + '">גיאוקוד</a>');
  L.push('<a target="_blank" href="https://www.google.com/maps/search/' +
    encodeURIComponent(r.addr.replace(',', ' ') + ' ' + r.city) + '">חיפוש כתובת</a>');
  L.push('<a target="_blank" href="https://www.govmap.gov.il/?q=' +
    encodeURIComponent(r.addr.replace(',', ' ') + ' ' + r.city) + '">govmap</a>');
  return L.join(' · ');
}
function tagCls(t){ return t==='תת-1.5' ? 't1' : t==='מעל-1.5' ? 't2' : 't3'; }
function render(){
  const q = document.getElementById('flt').value.trim();
  const rows = DATA.filter(r => !q || (r.city + ' ' + r.venue + ' ' + r.addr).includes(q));
  rows.sort((a,b) => { const x=a[sortK], y=b[sortK];
    if(x==null) return 1; if(y==null) return -1;
    return (typeof x==='number' ? x-y : String(x).localeCompare(String(y),'he')) * sortDir; });
  document.getElementById('tb').innerHTML = rows.map(r => {
    const i = DATA.indexOf(r);
    return '<tr data-i="' + i + '"' + (r.verdict ? ' class="decided"' : '') + '>' +
    '<td>' + r.city + '</td><td><b>' + r.venue + '</b></td><td>' + r.addr + '</td>' +
    '<td class="n">' + (r.valid||'') + '</td><td class="n">' + (r.d!=null? r.d : '') + '</td>' +
    '<td class="n">' + (r.sa_cur||'?') + ' ← ' + (r.sa_geo||'?') + '</td>' +
    '<td>' + links(r) + '</td>' +
    '<td><span class="tag ' + tagCls(r.tag) + '">' + r.tag + '</span></td>' +
    '<td><select onchange="setV(' + i + ',this.value)">' +
      ['','כתובת צודקת','נוכחי צודק','לא ברור'].map(o =>
        '<option' + (r.verdict===o ? ' selected' : '') + '>' + o + '</option>').join('') +
    '</select></td>' +
    '<td><input type="text" value="' + (r.note||'') + '" onchange="setN(' + i + ',this.value)"></td></tr>';
  }).join('');
  document.getElementById('cnt').textContent = rows.length + ' שורות · ' +
    DATA.filter(r=>r.verdict).length + ' הוכרעו';
}
function setV(i, v){ DATA[i].verdict = v; save(); render(); }
function setN(i, v){ DATA[i].note = v; save(); }
function save(){ localStorage.setItem('manual_review_decisions',
  JSON.stringify(DATA.filter(r=>r.verdict||r.note).map(r=>({sem:r.sem,venue:r.venue,addr:r.addr,verdict:r.verdict,note:r.note})))); }
function loadSaved(){
  const s = localStorage.getItem('manual_review_decisions'); if(!s) return;
  for(const d of JSON.parse(s)){
    const r = DATA.find(r => r.sem===d.sem && r.venue===d.venue);
    if(r){ r.verdict = d.verdict; r.note = d.note; }
  }
}
function exportJSON(){
  const out = DATA.filter(r=>r.verdict).map(r=>({sem:r.sem,venue:r.venue,addr:r.addr,verdict:r.verdict,note:r.note||''}));
  const box = document.getElementById('exportBox');
  box.style.display='block'; box.value = JSON.stringify(out, null, 1);
  box.select(); document.execCommand('copy');
}
document.getElementById('flt').addEventListener('input', render);
document.querySelectorAll('th[data-k]').forEach(th => th.addEventListener('click', () => {
  const k = th.dataset.k;
  sortDir = (sortK===k) ? -sortDir : (k==='valid'||k==='d' ? -1 : 1);
  sortK = k; render();
}));
loadSaved(); render();
</script></body></html>"""
    page = page.replace("__DATA__", data).replace("__NSUB__", str(n_sub)) \
               .replace("__NOVER__", str(n_over)).replace("__NFIX__", str(n_fix))
    out = os.path.join(HERE, "manual_review.html")
    open(out, "w", encoding="utf-8").write(page)
    print(f"{len(rows)} rows ({n_sub} sub-1.5, {n_over} over-1.5, {n_fix} has-fix) -> {out} "
          f"({os.path.getsize(out)//1024} KB)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
