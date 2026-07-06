# 🇮🇱 Israeli Elections Dashboard & Map

Interactive visualizations of Israeli Knesset election results from **Knesset 13 (1992)** to **Knesset 25 (2022)**.

## 🔗 Live site — [**open the dashboard →**](https://yardenmorad2003.github.io/election-dashboard/dashboard.html)

Hosted on GitHub Pages:

- **[Dashboard](https://yardenmorad2003.github.io/election-dashboard/dashboard.html)** (`dashboard.html`) — charts, trends, comparisons, socioeconomic analysis, the **polarization & sorting** research tab, and the coalition builder
- **[Interactive map](https://yardenmorad2003.github.io/election-dashboard/election_map.html)** (`election_map.html`) — color-coded voting patterns, small-locality polygons, and a proportional-**bubble** mode
- **[Neighborhood map](https://yardenmorad2003.github.io/election-dashboard/statarea_map.html)** (`statarea_map.html`) — **ten elections (2003–2022) at CBS statistical-area level**, each cross-referenced with its era's census (2022 / 2008 / 1995), with corrected polling-venue dots, a modeled **residence estimate** per neighborhood, poster mode and PNG export
- **[Research: nationalization & sorting](https://yardenmorad2003.github.io/election-dashboard/findings.html)** (`findings.html`) — standalone writeup with bootstrapped CIs and the demographic mechanism
- **[Party profiles](https://yardenmorad2003.github.io/election-dashboard/party_analysis.html)** (`party_analysis.html`) — per-party seat/vote trajectory, geographic strongholds, and socioeconomic voter fingerprint (with an all-vs-Jewish-localities toggle)
- **[Vote transfers](https://yardenmorad2003.github.io/election-dashboard/transfers.html)** (`transfers.html`) — ecological-inference transfer Sankeys for every consecutive pair 1992→2022, with an independent INES survey layer
- **[Demographics & voting](https://yardenmorad2003.github.io/election-dashboard/demographics.html)** (`demographics.html`) — the education gradient 1972–2022, income vs education, transfers by education tercile, within-city dispersion, and the migration null

🌐 **English version**: every page has a full English sibling (`*_en.html`) — use the **English / עברית** toggle in the navigation bar, or open e.g. [dashboard_en.html](https://yardenmorad2003.github.io/election-dashboard/dashboard_en.html) directly.

## Setup

Serve from this folder with any static server:

```bash
# Python
python -m http.server 8000

# Node
npx serve .
```

Then open `http://localhost:8000/dashboard.html`, `http://localhost:8000/election_map.html`, `http://localhost:8000/findings.html`, or `http://localhost:8000/party_analysis.html`.

## Project Structure

```
├── dashboard.html          Main analytics dashboard (+ polarization/sorting tab)
├── election_map.html       Interactive Leaflet map (polygons + bubble mode)
├── statarea_map.html       Neighborhood map: 10 elections at statistical-area level
├── findings.html           Standalone nationalization/sorting writeup
├── findings_data.json      Precomputed panel metrics, CIs, movers, mechanism
├── party_analysis.html     Per-party socioeconomic & geographic profiles
├── PARTY_ANALYSIS.md       Docs for the party-analysis page (data model, schema, method)
├── transfers.html          Vote-transfer Sankey (K13→K25, bloc + party views, abstention, CIs, INES survey layer)
├── analysis/               Build scripts (party analysis, transfers, stat-area layers,
│                           venue geocoding audits, residence estimates, validators)
└── data/
    ├── core.json               National results & metadata (6 KB)
    ├── parties_national.json   Party seats & lists (15 KB)
    ├── localities.json         1,391 localities voting data (3.1 MB)
    ├── parties_by_locality.json Party votes per locality (2.8 MB)
    ├── socioeconomic.json      201 municipalities demographics (1.4 MB)
    ├── party_analysis.json     Precomputed per-party metrics (330 KB)
    ├── election_map_geo.json   GeoJSON boundaries + voting data (1.9 MB)
    ├── statarea_*.json          Per-election stat-area layers + slim geometries (3 vintages)
    ├── statarea_estimate_*.json Residence-estimate layers (venue catchments × population)
    ├── venue_dots_*.json        Corrected polling-venue points (votes, winner, parties, turnout)
    └── census_1995_statarea.json 1995 census per stat-area (religion, age, post-1990 aliyah)
```

## Features

### Dashboard
- Election-to-election comparison
- Bloc trend lines (1992–2022)
- Locality deep-dive explorer (incl. valid votes per election)
- Socioeconomic correlations & scatter plots
- Polarization & sorting research (population-weighted, bootstrapped CIs)
- Interactive coalition builder

### Party profiles
- Per-party seat & vote-share trajectory (K13–K25), with ballot-letter reuse warnings
- Strongholds (highest local share) and contributors (most absolute votes)
- Socioeconomic gradient & standardized voter fingerprint, with an all-vs-Jewish-localities toggle
- See **[`PARTY_ANALYSIS.md`](PARTY_ANALYSIS.md)** for the data model, JSON schema, and methodology

### Vote transfers
- Ecological-inference transfer matrices for all 12 consecutive-election pairs, 1992→2022 (constrained least squares over ~1,100 common localities; method credit: Harel Cain & Itamar Mushkin, clean-room reimplementation)
- Bloc-level Sankey with abstention flows, party-level exploratory view, bootstrap CIs, Arab/Jewish-sector split test with automatic warnings
- Independent INES survey estimates for every transition (weighted recalled-vote × current-vote crosstabs), toggleable against the ecological view — including a true April→September 2019 panel with no recall bias

### Map
- Color by bloc, or by individual sub-group (Right, Haredi, Center, Left, Arab, Opposition Right)
- Polygon view (incl. ~1,000 small localities) or proportional-bubble mode
- Click any locality for detailed breakdown
- Election history mini-charts per locality
- Search localities by name
- Demographic overlay

### Neighborhood map (statistical areas)
- **Ten elections, 2003–2022**, on three CBS geometry vintages (1995 / 2008 / 2022), each
  cross-referenced with its **era-matched census** — 2022 census for K21–K25, 2008 for
  K18–K20, and the 1995 census (religion, age, **post-1990 aliyah** per neighborhood)
  for K16–K17 — a cross-referencing not published elsewhere
- Bloc / winner / party / turnout modes + per-era demographic modes; poster mode with a
  municipal underlay and **one-click PNG export** (title, legend, attribution)
- **Corrected polling-venue dots**: every venue placed from multi-source verified
  coordinates — a coordinate-hygiene campaign of **282 verified fixes** cross-checking the
  MOE institutions registry, the CEC's official 2022 kalpi-address file, contemporaneous
  2006 ballot addresses, and street-geometry analysis; click any dot for the venue's full
  vote profile
- **Residence estimate** ("אומדן מגורים"): a modeled answer to *how each neighborhood's
  residents voted* (vs. where votes were physically cast) — each venue's votes are
  distributed back over the stat-areas it serves via population-weighted nearest-venue
  catchments, closure-exact per city, with the hold-out validation error (~4–5 pp median)
  printed on the map
- Mobile-friendly: bottom-sheet profiles and swipeable controls

## Data Sources

- Israel Central Elections Committee — per-ballot results (K16–K25, via data.gov.il) and the official K25 polling-place address file
- Israel Central Bureau of Statistics (CBS) — locality results context, statistical-area boundaries (1995 / 2008 / 2022) and the matching censuses (incl. the 1995 census stat-area tables and the 2008 מצוקם profiles)
- Ministry of Education institutions registry (data.gov.il) — polling-venue coordinate verification
- Polling-venue master list: Harel Cain's *kolot-nodedim* station coordinates (with 282 locally verified corrections; see `analysis/statarea_inputs/station_coord_fixes.json`)
- Israel National Election Studies (INES) — survey validation layer, cited in the official per-study format (full citation list at the bottom of the transfers page), e.g.: *Israel National Election Studies. 2022. INES 2022 Election Study Full Release [dataset and documentation]. https://www.tau.ac.il/~ines/*

## Literature

The research pages anchor their findings in the academic literature, with per-claim citations on-page: the *The Elections in Israel* series (1992–2022 volumes, founded by Asher Arian & Michal Shamir), *The Parties in Israel 1992–2021*, Arian & Shamir's cleavage-structure article (2008), and the Israel Polarization Panel article (*Electoral Studies*, 2022). Page references follow the digital editions.
