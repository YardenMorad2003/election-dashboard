# -*- coding: utf-8 -*-
"""
inject_redesign.py — one-time injection of the redesign layer into the HEBREW pages.

Per page: <link redesign.css> before </head>, body class rd rd-<page>, the old
emoji sitenav replaced with the slim brand nav (election_map keeps its compact
mapnav <details>, inner links rewritten), dashboard section-tab emoji stripped.

English pages are NOT touched here — they are regenerated from the Hebrew pages
by analysis/build_english_pages.py (nav labels live in en_strings.py).

Idempotent (skips pages already carrying the rd-injected marker):
    python -X utf8 analysis/inject_redesign.py
"""
import io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ["dashboard", "election_map", "statarea_map", "transfers",
         "demographics", "party_analysis", "findings"]

NAV = [
    ("dashboard.html", "לוח מחוונים"),
    ("election_map.html", "מפה ארצית"),
    ("statarea_map.html", "מפת שכונות"),
    ("transfers.html", "נדידת קולות"),
    ("demographics.html", "דמוגרפיה"),
    ("party_analysis.html", "מפלגות"),
    ("findings.html", "ממצאים"),
]
BRAND = '<a class="rd-brand" href="index.html">בחירות בישראל <span class="rd-yrs">1992–2022</span></a>'
MARK = "<!-- rd-injected -->"


def build_sitenav(page):
    cur = page + ".html"
    links = "\n".join(
        '    <a{} href="{}">{}</a>'.format(' class="on"' if f == cur else "", f, lab)
        for f, lab in NAV)
    return ('<nav class="sitenav" aria-label="ניווט האתר">{mark}\n'
            '    {brand}\n'
            '    <span class="rd-gap"></span>\n'
            '{links}\n'
            '    <span class="rd-gap"></span>\n'
            '    <a class="lang" lang="en" href="{page}_en.html">EN</a>\n'
            '</nav>').format(mark=MARK, brand=BRAND, links=links, page=page)


def build_mapnav_inner(page):
    cur = page + ".html"
    links = ['      <a href="index.html">דף הבית</a>']
    for f, lab in NAV:
        links.append('      <a{} href="{}">{}</a>'.format(
            ' class="on"' if f == cur else "", f, lab))
    links.append('      <a class="lang" lang="en" href="{}_en.html">English</a>'.format(page))
    return "<nav>{}\n{}\n    </nav>".format(MARK, "\n".join(links))


def inject(page):
    fname = os.path.join(ROOT, page + ".html")
    with io.open(fname, encoding="utf-8") as f:
        html = f.read()
    if MARK in html:
        print("skip (already injected):", page)
        return

    html = html.replace("</head>",
        '<link rel="stylesheet" href="redesign.css?v=2">\n</head>', 1)

    def add_class(m):
        attrs = m.group(1)
        cls = "rd rd-" + page
        if 'class="' in attrs:
            return "<body" + attrs.replace('class="', 'class="' + cls + " ", 1) + ">"
        return "<body" + attrs + ' class="' + cls + '">'
    html, n = re.subn(r"<body([^>]*)>", add_class, html, count=1)
    assert n == 1, "body tag not found in " + page

    if page == "election_map":
        pat = re.compile(r'(<details class="mapnav"[^>]*>.*?<summary[^>]*>.*?</summary>\s*)<nav>.*?</nav>', re.S)
        html, n = re.subn(pat, lambda m: m.group(1) + build_mapnav_inner(page), html, count=1)
        assert n == 1, "mapnav not found in " + page
    else:
        pat = re.compile(r'<nav class="sitenav".*?</nav>', re.S)
        html, n = re.subn(pat, lambda m: build_sitenav(page), html, count=1)
        assert n == 1, "sitenav not found in " + page

    if page == "dashboard":
        html = re.sub(u"(<button class=\"nav-btn[^>]*data-section[^>]*>)\\s*[\U0001F300-\U0001FAFF☀-➿️]+\\s*",
                      r"\1", html)

    with io.open(fname, "w", encoding="utf-8") as f:
        f.write(html)
    print("injected:", page)


if __name__ == "__main__":
    for p in (sys.argv[1:] or PAGES):
        inject(p)
