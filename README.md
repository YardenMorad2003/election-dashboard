# 🇮🇱 Israeli Elections Dashboard & Map

Interactive visualizations of Israeli Knesset election results from **Knesset 14 (1996)** to **Knesset 25 (2022)**.

## Live Pages

- **`dashboard.html`** — Charts, trends, comparisons, socioeconomic analysis, coalition builder
- **`map.html`** — Interactive geographic map with color-coded voting patterns

## Setup

Serve from this folder with any static server:

```bash
# Python
python -m http.server 8000

# Node
npx serve .
```

Then open `http://localhost:8000/dashboard.html` or `http://localhost:8000/map.html`.

## Project Structure

```
├── dashboard.html          Main analytics dashboard
├── map.html                Interactive Leaflet map
├── PROJECT_MAP.md          Developer reference (file structure & line map)
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
- Bloc trend lines (1996–2022)
- Locality deep-dive explorer
- Socioeconomic correlations & scatter plots
- Interactive coalition builder

### Map
- Color by bloc, or by individual sub-group (Right, Haredi, Center, Left, Arab, Opposition Right)
- Click any locality for detailed breakdown
- Election history sparklines per locality
- Search localities by name
- Demographic overlay

## Data Sources

- Israel Central Elections Committee
- Israel Central Bureau of Statistics (CBS)
