# -*- coding: utf-8 -*-
"""
build_english_pages.py — generates the English site (*_en.html) from the Hebrew pages.

For each page in PAGES:
  1. structural transforms: lang/dir flip, he-IL -> en-US locale, cross-links and the
     dashboard iframe rewired to the *_en siblings
  2. per-page structural FIXES from analysis/en_strings.py (exact replacements, e.g.
     RTL-specific CSS, reversed chart axes)
  3. name-literal pass: quoted JS/HTML string literals that exactly equal a key in
     data/names_en.json are replaced (keeps code literals consistent with the
     runtime-translated data: WINNER_COLORS keys, featured-city lists, ...)
  4. translation dictionary (GLOBAL + per-page), applied longest-first
  5. fetch-shim injection right after <head>: wraps window.fetch so every fetched
     JSON is deep-translated (keys+values) through names_en.json — pickers, panels,
     tooltips and search all show English names without touching the shared data
  6. leftover scan: any line still containing Hebrew goes to analysis/en_leftovers_<page>.txt

Re-run after editing the Hebrew pages or analysis/en_strings.py:
    python -X utf8 analysis/build_english_pages.py [page ...]
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "analysis"))
from en_strings import GLOBAL, PAGES, FIXES  # noqa: E402

HEB = re.compile(r"[֐-׿]")
ALL_PAGES = ["findings", "transfers", "party_analysis", "demographics", "election_map", "dashboard", "statarea_map"]

SHIM = """<script>
/* EN build (analysis/build_english_pages.py): translate Hebrew names inside every
   fetched JSON via data/names_en.json — keys AND values, exact-match only, so party
   ballot codes and other join keys pass through untouched. */
(function(){
  var orig = window.fetch.bind(window);
  var mapP = null;
  function getMap(){
    if(!mapP) mapP = orig('data/names_en.json').then(function(r){return r.json();}).then(function(d){
      var m = {};
      [d.localities, d.parties, d.misc, d.elections].forEach(function(part){
        if(part) for(var k in part) m[k] = part[k];
      });
      return m;
    });
    return mapP;
  }
  var HEBRE = /[\\u0590-\\u05FF]/;
  function tr(m, s){ return (m[s] !== undefined && HEBRE.test(s)) ? m[s] : s; }
  function deep(m, o){
    if(Array.isArray(o)){
      for(var i=0;i<o.length;i++) o[i] = deep(m, o[i]);
      return o;
    }
    if(o && typeof o === 'object'){
      var ks = Object.keys(o);
      for(var j=0;j<ks.length;j++){
        var k = ks[j], nk = tr(m, k), v = deep(m, o[k]);
        if(nk !== k){ delete o[k]; }
        o[nk] = v;
      }
      return o;
    }
    return (typeof o === 'string') ? tr(m, o) : o;
  }
  window.fetch = function(input, init){
    var url = (typeof input === 'string') ? input : ((input && input.url) || '');
    var p = orig(input, init);
    if(url.indexOf('names_en.json') !== -1) return p;
    return p.then(function(r){
      if(!r || !r.ok) return r;
      var j = r.json.bind(r);
      r.json = function(){
        return Promise.all([getMap(), j()]).then(function(a){ return deep(a[0], a[1]); });
      };
      return r;
    });
  };
})();
</script>"""

def load_names():
    with open(os.path.join(ROOT, "data", "names_en.json"), encoding="utf-8") as f:
        d = json.load(f)
    m = {}
    for part in ("localities", "parties", "misc", "elections"):
        m.update(d.get(part) or {})
    return m

def name_literal_pass(src, names):
    """Replace quoted literals ('X', "X", `X`) whose entire inner text is a names key.
    One pass per quote type so a name may contain the other quote chars (בית ג'ן)."""
    n_hits = 0
    for q in ("'", '"', "`"):
        def repl(m, q=q):
            nonlocal n_hits
            inner = m.group(1)
            if HEB.search(inner) and inner in names:
                en = names[inner]
                if q in en:
                    en = en.replace(q, "\\" + q)
                n_hits += 1
                return q + en + q
            return m.group(0)
        src = re.sub(q + r"([^" + q + r"\n]{1,60}?)" + q, repl, src)
    return src, n_hits

def build(page):
    src_path = os.path.join(ROOT, page + ".html")
    out_path = os.path.join(ROOT, page + "_en.html")
    with open(src_path, encoding="utf-8") as f:
        src = f.read()

    # 1. structural globals
    src = src.replace('lang="he"', 'lang="en"').replace("lang='he'", "lang='en'")
    src = src.replace('dir="rtl"', 'dir="ltr"').replace("dir='rtl'", "dir='ltr'")
    src = src.replace("he-IL", "en-US")
    for p in ALL_PAGES:
        src = src.replace(p + ".html", p + "_en.html")

    # 2. per-page structural fixes
    for old, new in FIXES.get(page, []):
        if old not in src:
            print(f"  [WARN] fix not found in {page}: {old[:70]!r}")
        src = src.replace(old, new)

    # 3. name literals
    names = load_names()
    src, nlit = name_literal_pass(src, names)

    # 4. dictionary, longest-first
    entries = dict(GLOBAL)
    entries.update(PAGES.get(page, {}))
    unused = []
    for he in sorted(entries, key=len, reverse=True):
        if he in src:
            src = src.replace(he, entries[he])
        else:
            unused.append(he)

    # 5. shim
    m = re.search(r"<head[^>]*>", src)
    src = src[:m.end()] + "\n" + SHIM + src[m.end():]

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(src)

    # 6. leftover report — quoted ballot-letter codes are join keys, intentionally Hebrew
    CODES = ("מחל|פה|כן|שס|ל|ג|אמת|ט|טב|עם|ו|ד|כף|נץ|זך|ום|יש|ם|הד|ת|ע|כ|ב|ה|ז|נ|נר|קן|קץ|יט|צפ|צף|דעם|ודעם|מרץ")
    code_lit = re.compile(r"(['\"])(?:" + CODES + r")\1")
    js_comment = re.compile(r"//.*$|/\*.*?\*/")  # Hebrew in dev-facing comments is fine
    leftovers = [(i + 1, ln.strip()) for i, ln in enumerate(src.splitlines())
                 if HEB.search(js_comment.sub("", code_lit.sub("''", ln)))]
    rep_path = os.path.join(ROOT, "analysis", f"en_leftovers_{page}.txt")
    with open(rep_path, "w", encoding="utf-8") as f:
        f.write(f"{page}_en.html: {len(leftovers)} lines with Hebrew, {nlit} name-literals, "
                f"{len(unused)} unused dict entries\n")
        for he in unused:
            f.write(f"UNUSED: {he[:100]}\n")
        for no, ln in leftovers:
            f.write(f"{no}: {ln[:300]}\n")
    print(f"{page}: {len(leftovers)} Hebrew lines left, {nlit} name-literals, "
          f"{len(unused)} unused entries -> {os.path.basename(rep_path)}")

if __name__ == "__main__":
    targets = sys.argv[1:] or ALL_PAGES
    for page in targets:
        build(page)
