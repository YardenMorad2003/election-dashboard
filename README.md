# 🇮🇱 Israeli Elections Dashboard & Map

Interactive visualizations of Israeli Knesset election results from **Knesset 13 (1992)** to **Knesset 25 (2022)**.

## 🔗 Live site — [**open the dashboard →**](https://yardenmorad2003.github.io/election-dashboard/dashboard.html)

Hosted on GitHub Pages:

- **[Dashboard](https://yardenmorad2003.github.io/election-dashboard/dashboard.html)** (`dashboard.html`) — charts, trends, comparisons, socioeconomic analysis, the **polarization & sorting** research tab, and the coalition builder
- **[Interactive map](https://yardenmorad2003.github.io/election-dashboard/election_map.html)** (`election_map.html`) — color-coded voting patterns, small-locality polygons, and a proportional-**bubble** mode
- **[Research: nationalization & sorting](https://yardenmorad2003.github.io/election-dashboard/findings.html)** (`findings.html`) — standalone writeup with bootstrapped CIs and the demographic mechanism

## Setup

Serve from this folder with any static server:

```bash
# Python
python -m http.server 8000

# Node
npx serve .
```

Then open `http://localhost:8000/dashboard.html`, `http://localhost:8000/election_map.html`, or `http://localhost:8000/findings.html`.

## Project Structure

```
├── dashboard.html          Main analytics dashboard (+ polarization/sorting tab)
├── election_map.html       Interactive Leaflet map (polygons + bubble mode)
├── findings.html           Standalone nationalization/sorting writeup
├── findings_data.json      Precomputed panel metrics, CIs, movers, mechanism
└── data/
    ├── core.json               National results & metadata (6 KB)
    ├── parties_national.json   Party seats & lists (15 KB)
    ├── localities.json         1,391 localities voting data (3.1 MB)
    ├── parties_by_locality.json Party votes per locality (2.8 MB)
    ├── socioeconomic.json      201 municipalities demographics (1.4 MB)
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
