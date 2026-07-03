# 🇮🇱 Israeli Elections Dashboard & Map

Interactive visualizations of Israeli Knesset election results from **Knesset 13 (1992)** to **Knesset 25 (2022)**.

## 🔗 Live site — [**open the dashboard →**](https://yardenmorad2003.github.io/election-dashboard/dashboard.html)

Hosted on GitHub Pages:

- **[Dashboard](https://yardenmorad2003.github.io/election-dashboard/dashboard.html)** (`dashboard.html`) — charts, trends, comparisons, socioeconomic analysis, the **polarization & sorting** research tab, and the coalition builder
- **[Interactive map](https://yardenmorad2003.github.io/election-dashboard/election_map.html)** (`election_map.html`) — color-coded voting patterns, small-locality polygons, and a proportional-**bubble** mode
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
├── findings.html           Standalone nationalization/sorting writeup
├── findings_data.json      Precomputed panel metrics, CIs, movers, mechanism
├── party_analysis.html     Per-party socioeconomic & geographic profiles
├── PARTY_ANALYSIS.md       Docs for the party-analysis page (data model, schema, method)
├── transfers.html          Vote-transfer Sankey (K13→K25, bloc + party views, abstention, CIs, INES survey layer)
├── analysis/               Build scripts (party analysis, transfer matrices, bootstrap, survey crosstabs)
└── data/
    ├── core.json               National results & metadata (6 KB)
    ├── parties_national.json   Party seats & lists (15 KB)
    ├── localities.json         1,391 localities voting data (3.1 MB)
    ├── parties_by_locality.json Party votes per locality (2.8 MB)
    ├── socioeconomic.json      201 municipalities demographics (1.4 MB)
    ├── party_analysis.json     Precomputed per-party metrics (330 KB)
    └── election_map_geo.json   GeoJSON boundaries + voting data (1.9 MB)
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

## Data Sources

- Israel Central Elections Committee
- Israel Central Bureau of Statistics (CBS)
- Israel National Election Studies (INES) — survey validation layer, cited in the official per-study format (full citation list at the bottom of the transfers page), e.g.: *Israel National Election Studies. 2022. INES 2022 Election Study Full Release [dataset and documentation]. https://www.tau.ac.il/~ines/*

## Literature

The research pages anchor their findings in the academic literature, with per-claim citations on-page: the *The Elections in Israel* series (1992–2022 volumes, founded by Asher Arian & Michal Shamir), *The Parties in Israel 1992–2021*, Arian & Shamir's cleavage-structure article (2008), and the Israel Polarization Panel article (*Electoral Studies*, 2022). Page references follow the digital editions.
