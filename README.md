# 🇮🇱 Israeli Elections Dashboard & Maps

Interactive analysis of Israeli Knesset election results from **Knesset 13 (1992)** to **Knesset 25 (2022)** — national trends, locality-level maps, neighborhood-level (statistical-area) maps, ecological vote-transfer estimates validated against surveys, party profiles, and a population-weighted polarization & sorting study.

## 🔗 Live site — [**open the dashboard →**](https://yardenmorad2003.github.io/election-dashboard/dashboard.html)

Hosted on GitHub Pages. Every page has a full English sibling (`*_en.html`) — use the **English / עברית** toggle in the navigation, or open e.g. [dashboard_en.html](https://yardenmorad2003.github.io/election-dashboard/dashboard_en.html) directly.

| Page | What it does |
|---|---|
| [Dashboard](https://yardenmorad2003.github.io/election-dashboard/dashboard.html) | National results & trends, locality explorer, socioeconomic correlations, coalition builder, polarization & sorting research tab, and the full **About & Methodology** section |
| [Interactive map](https://yardenmorad2003.github.io/election-dashboard/election_map.html) | ~1,400 localities (incl. ~1,000 small ones) colored by bloc / party / swing / turnout, polygon, bubble and Dorling-cartogram modes, head-to-head duels, threshold filtering |
| [Neighborhood map](https://yardenmorad2003.github.io/election-dashboard/statarea_map.html) | **Ten elections (2003–2022) at CBS statistical-area level** — each cross-referenced with its era's census (2022 / 2008 / 1995), with verified polling-venue dots, a modeled residence estimate, poster mode and PNG export |
| [Vote transfers](https://yardenmorad2003.github.io/election-dashboard/transfers.html) | Ecological-inference transfer Sankeys for every consecutive pair 1992→2022, with an independent INES survey layer and bootstrap CIs |
| [Demographics & voting](https://yardenmorad2003.github.io/election-dashboard/demographics.html) | The education gradient 1972–2022, transfers by education tercile, within-city dispersion vs between-city sorting, the migration null |
| [Party profiles](https://yardenmorad2003.github.io/election-dashboard/party_analysis.html) | Per-party trajectory, strongholds & vote contributors, standardized socioeconomic voter fingerprint (all vs Jewish-majority localities) |
| [Polarization & sorting](https://yardenmorad2003.github.io/election-dashboard/findings.html) | Standalone research writeup: geographic sorting rises while swings nationalize, with bootstrapped CIs and the demographic mechanism |

## 🤖 Ask the data — MCP server

The whole dataset is also queryable **conversationally** from Claude, ChatGPT,
or any [Model Context Protocol](https://modelcontextprotocol.io) client — ask
*"How did Bnei Brak vote in 2022, party by party?"* or *"Where did left-bloc
voters go between 2021 and 2022?"* in Hebrew or English and the assistant
queries the same JSON artifacts this site renders. Eleven read-only tools
cover locality and national results, party histories, vote transfers, the
direct-PM contests, and CBS demographics; every answer is a small
question-shaped slice, never a data dump.

Live endpoint (no auth, nothing logged):

```
https://israeli-elections-mcp.yardenmorad2003.workers.dev/mcp
```

Setup for claude.ai / ChatGPT / Claude Code / Claude Desktop, the local stdio
variant, and the Cloudflare Worker architecture are documented in
[`mcp/README.md`](mcp/README.md).

## Scope

- **13 elections** (K13 1992 → K25 2022) at the national and locality level; **10 elections** (K16 2003 → K25 2022) at statistical-area (neighborhood) level.
- **Era-matched censuses**: each stat-area layer joins the census closest to its election — 2022 census for K21–K25, 2008 for K18–K20, 1995 (religion, age, post-1990 aliyah) for K16–K17 — a cross-referencing not published elsewhere.
- **Two bloc systems**: five sub-groups (Right, Haredi, Center, Left, Arab) plus **opposition-right** (Yisrael Beiteinu K21–25; Yamina & New Hope K24) following the research literature's Netanyahu-bloc distinction, aggregated into Right-Haredi vs Center-Left-Arabs. K24 views include a **Yamina-in-Right / Yamina-in-Center-Left toggle** on both maps, since that placement is genuinely contested.
- **Party identity, not ballot letters**: ballot letters are reused across unrelated parties (פה was the Center Party in 1999 before Yesh Atid; ת was Tehiya in 1992 before New Hope; כן chained Yisrael BaAliyah → Kadima → Blue & White → National Unity). All cross-year views identify parties by each election's own list name, with curated identity segments in the map's party picker and explicit reuse warnings in the party profiles.

## Methodology highlights

**Polling-venue locations (neighborhood map).** ~32,700 polling venues per modern election are geocoded and assigned to statistical areas by point-in-polygon. For **2022** the anchor is the CEC's official per-station address file plus **545 manually verified coordinate fixes** (cross-checked against the Education Ministry institution registry, street geometries, contemporaneous 2006 addresses, and voting-profile checks; every batch documented in ledgers inside `analysis/statarea_inputs/station_coord_fixes.json`). Same-named venues in one city are separated by their official addresses (`station_coord_fixes_k25_addr.json`). Per-locality closure is validated at 99.69%, with zero cross-locality spillover.

**Residence estimate.** A separate, clearly labeled model layer answers *how each neighborhood's residents voted* (vs where votes were physically cast): each venue's votes are redistributed over the stat-areas it serves via population-weighted catchments, closure-exact per city, with hold-out validation (median bloc error ~4–5.5 pp) printed on the map.

**Vote transfers.** Constrained least squares ecological inference (Goodman lineage; method credit: Harel Cain & Itamar Mushkin, clean-room reimplementation): the national transfer matrix minimizing prediction error over ~1,000–1,150 common localities, non-negative, row sums tied to electorate growth, non-voters as a real category. Validated three ways: r≈0.99 agreement with Cain's independent ballot-box-level estimates; an independent INES survey estimate per transition (agreement r=0.78–1.00, mean gap 2–10 pp), including a true April→September 2019 panel that measures recall bias directly (6–19 pp per row); and the published INES 2006 panel for the Kadima birth. Sector-split tests flag transitions where the national-table assumption visibly fails.

**Polarization & sorting study.** A balanced panel of 896 localities across all 13 elections, population-weighted; sorting metrics (weighted SD, P90–P10 gap, dissimilarity index) and a nationalization metric (weighted SD of between-election swings); 2,000-resample bootstrap CIs; mechanism tested against education, fertility, and Haredi-vote gradients in the 31 largest Jewish cities.

## Data sources

- **Central Elections Committee (CEC)** — per-locality results K13–K25 and per-ballot results K16–K25 (historical files via [data.gov.il](https://data.gov.il)); the official **K25 polling-place address file** (kalpiplaces).
- **Central Bureau of Statistics (CBS)** — statistical-area boundaries (1995 / 2008 / 2022) and the matching censuses (incl. the 1995 census stat-area tables); socioeconomic index publications for municipalities (2008–2021) and intra-city statistical areas (2008–2021); annual "Local Authorities in Israel" profiles 1999–2024 (wages, matriculation, Gini, migration); religion / "no religion classification" locality data (2019).
- **Ministry of Education institutions registry** (data.gov.il) — 28k geocoded schools/kindergartens used to verify polling-venue coordinates.
- **Harel Cain's *kolot-nodedim* station coordinates** — the polling-venue master list for pre-2022 elections (with the 545 verified corrections above).
- **Israel National Election Studies (INES)** — 14 election surveys 1992–2022 as the transfers validation layer; cited per-study in the official format (full list at the bottom of the transfers page).
- **Base maps** — CARTO tiles © OpenStreetMap contributors (ODbL).

## Limitations — read before quoting numbers

**Geography & locations**
- An official polling-station address file exists **only for 2022**. Earlier elections are reconstructions: K21–24 from venue-*name* geocoding, K18–20 from venue-name matching across elections, K16–17 from the addresses in the era's own results files. Verified fixes propagate backwards **by venue name** — a venue that changed buildings between elections may appear at its 2022 location, and same-named venues cannot be split in years without an address file.
- Double-envelope ballots (soldiers, hospitals, diplomats — ~458K votes in 2022, ~10%) are inherently unmappable below the national level.
- Geocoding coverage is below average in some Arab localities and in the settlements; **within-area percentages are reliable, but national sums from the stat-area layer are slightly biased**. Dots-layer vote placement: ~99% of votes in K21–25 and K18, ~88–89% in K19–20, ~82–85% in K16–17.
- The residence estimate is a **model, not a count** — use it with its printed hold-out error.

**Statistical inference**
- Everything locality- or area-level is **ecological**: correlations, transfer matrices, and sorting metrics describe aggregates, not individual voters (ecological fallacy).
- The transfer matrices assume **one national transfer table** across all localities. This is a knowing simplification: it is stress-tested (sector and SES splits, INES triangulation, bootstrap CIs) and fails visibly on at least one transition (2003→2006 Kadima, flagged on-page), but it cannot be fully verified. Bootstrap CIs measure sampling noise only, not assumption violations.
- The INES survey layer has its own biases (turnout over-reporting, recall drift toward winners) — measured at 6–19 pp per row where a true panel exists. The ecological and survey estimates serve as mutual sanity checks, not ground truth.

**Data coverage**
- Socioeconomic data covers **201 municipalities** (no regional councils; kibbutzim/moshavim covered via census data on the demographics page). The CBS socioeconomic index is re-standardized every vintage — cross-year comparisons use clusters or relative units only.
- Census timing ≠ election timing: K21–25 use the *later* 2022 census; K18–20 use the *earlier* 2008 census; demographics reflect the census year, not election day.
- Religion / "Russians" (no-religion-classification) data exists only from 2019. The 2006 locality voter roll is missing and imputed as the 2003/2009 average (flagged).
- K13 (1992): no socioeconomic analysis (CBS data doesn't reach back); ~67 small/historical localities unmatched and dropped; sub-threshold votes (~2.2%) unassigned to blocs except three named lists.

**Classification**
- Bloc assignment is per-election and partly subjective, especially for center parties; some bloc-level "movement" is party *reclassification* (e.g., Kulanu), which the party-level views separate.
- Ballot-letter reuse is handled (see Scope), but party *lineages that changed letters* (e.g., Bayit Yehudi across ב/טב) appear per-letter, not unified.

## Project structure

```
├── dashboard.html            Main dashboard (+ About & Methodology section)
├── election_map.html         Interactive Leaflet map (polygons / bubbles / cartogram)
├── statarea_map.html         Neighborhood map: 10 elections × era census
├── transfers.html            Vote-transfer Sankeys + INES survey layer
├── demographics.html         Education gradient & within-city dispersion study
├── party_analysis.html       Per-party profiles (see PARTY_ANALYSIS.md)
├── findings.html             Polarization & sorting writeup
├── *_en.html                 Generated English siblings (analysis/build_english_pages.py)
├── data/                     ~60 JSON artifacts (results, geometries, censuses,
│   │                         transfer matrices, per-party metrics)
│   ├── statarea_k{16..25}.json     Stat-area vote layers (3 geometry vintages)
│   ├── statarea_estimate_k*.json   Residence-estimate layers
│   ├── venue_dots_k*.json          Verified polling-venue points
│   ├── vote_transfers.json         All transfer matrices + CIs + survey layer
│   └── mcp/                        Pre-sliced artifacts for the remote MCP server
├── mcp/                      MCP server (see mcp/README.md):
│   ├── server.py                   Local stdio server (Claude Code / Desktop)
│   ├── worker/                     Cloudflare Worker (claude.ai / ChatGPT)
│   └── build_worker_data.py        data/mcp/ artifact builder
└── analysis/                 ~54 Python build scripts & audit instruments:
    ├── build_statarea_*.py         Era-specific stat-area pipelines
    ├── build_venue_dots.py         Venue aggregation + coordinate resolution
    ├── build_residence_estimate.py Residence-estimate model + hold-out validation
    ├── build_transfer_data.py      CVXPY transfer solver (+ bootstrap, SES splits)
    ├── sweep_k25_official.py       Official-address audit sweep (+ tier-2/3 resolvers)
    ├── resolve_sa_mismatch.py      Sub-1.5km placement auditor
    └── statarea_inputs/
        ├── station_coord_fixes.json         545 verified fixes + evidence ledgers
        ├── station_coord_fixes_k25_addr.json Address-scoped fixes (same-name venues)
        └── k25_ballot_addresses.json        Official CEC address snapshot
```

## Running locally

Static site — serve the folder with anything:

```bash
python -m http.server 8000        # or: npx serve .
```

Then open `http://localhost:8000/dashboard.html`. The analysis scripts (Python 3, `numpy`/`pandas`/`cvxpy`/`shapely`/`openpyxl`) regenerate the `data/` artifacts; each script's docstring documents its inputs, method, and validation gates. After any coordinate-fix change, the full stat-area rebuild chain + validators must be run (documented in the scripts).

## Credits & literature

- **Vote-transfer method**: [Harel Cain — *kolot-nodedim*](https://kolot-nodedim.netlify.app/) and Itamar Mushkin (original under CC BY-NC-SA; this is an independent clean-room reimplementation on locality data, validated against their ballot-box estimates at r≈0.99).
- **INES** — the Israel National Election Studies (Tel Aviv University), founded by Asher Arian ז"ל and Michal Shamir. Surveys are used as an independent cross-check only; all analysis and interpretation are this site's responsibility.
- **Official data** — CBS and the CEC. All processing, cross-referencing and conclusions are this site's own and not endorsed by the official bodies.
- **Literature** anchoring the research pages (per-claim citations on-page): the *The Elections in Israel* series (1992–2022 volumes), *The Parties in Israel 1992–2021*, Arian & Shamir (2008) on the cleavage structure, and the Israel Polarization Panel (*Electoral Studies*, 2022).
- **Libraries**: Chart.js, Leaflet; Python — pandas, NumPy, CVXPY/SCS, Shapely.
