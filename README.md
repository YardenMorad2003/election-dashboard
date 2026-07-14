# 🇮🇱 Israeli Elections — Interactive Dashboard & Maps

Every Israeli election since 1992, from the national picture down to the city block: locality and neighborhood-level maps, ecological vote-transfer estimates validated against surveys and a true panel, the 1996–2001 direct-PM contests, party profiles, a population-weighted polarization & sorting study — plus a live polling tracker for the upcoming 2026 election. Fully bilingual (Hebrew / English).

## 🔗 [**Open the site →**](https://yardenmorad2003.github.io/election-dashboard/index_en.html)

**The landing page is the front door**: a live dot-map of 1,266 localities colored by real bloc margins, a 13-election scrubber (1992 → 2022), locality search that deep-links straight into the full map, and a rail of guided stories — the Russian aliyah, the Haredi engine, the shrinking left, Arab turnout, and a story arc for every election. All links here open the **English versions**; the Hebrew originals live at the [site root](https://yardenmorad2003.github.io/election-dashboard/) and are one **עברית** toggle away on every page.

### The pages

| Page | What it does |
|---|---|
| [**Landing**](https://yardenmorad2003.github.io/election-dashboard/index_en.html) | The exploration instrument: scrub 13 elections, search any locality, jump into guided stories |
| [Dashboard](https://yardenmorad2003.github.io/election-dashboard/dashboard_en.html) | National results & trends, locality explorer, socioeconomic correlations, coalition builder, party-system metrics, polarization & sorting research tab, and the full **About & Methodology** section |
| [Interactive map](https://yardenmorad2003.github.io/election-dashboard/election_map_en.html) | ~1,400 localities colored by bloc / party / swing / turnout; polygon, bubble and Dorling-cartogram modes; head-to-head duels; **the 1996/1999/2001 direct-PM contests** with seven submodes (result, swing, gap, net votes, turnout, ticket-splitting); 19 guided tours |
| [Neighborhood map](https://yardenmorad2003.github.io/election-dashboard/statarea_map_en.html) | **Ten elections (2003–2022) at CBS statistical-area level**, each cross-referenced with its era's census (2022 / 2008 / 1995) — anchored on official CEC polling-place address files for 2022 **and 2009** (2013/2015 inherit by kalpi-number crosswalk), with verified venue dots, a modeled residence estimate, SES layers, address search, poster mode and PNG export |
| [Vote transfers](https://yardenmorad2003.github.io/election-dashboard/transfers_en.html) | Ecological-inference transfer Sankeys for every consecutive pair 1992→2022, triangulated against **two independent survey estimates** — INES cross-sections and, for 2019–2022, the **IPP true panel** — with bootstrap CIs |
| [Demographics & voting](https://yardenmorad2003.github.io/election-dashboard/demographics_en.html) | The education gradient 1972–2022 at locality level **and at the individual level** (14 INES surveys: education, religiosity, age and **ethnic origin**), income vs education, within-city dispersion vs between-city sorting |
| [Party profiles](https://yardenmorad2003.github.io/election-dashboard/party_analysis_en.html) | Per-party trajectory, strongholds & vote contributors, standardized socioeconomic voter fingerprint (all vs Jewish-majority localities) |
| [Polarization & sorting](https://yardenmorad2003.github.io/election-dashboard/findings_en.html) | Standalone research writeup: geographic sorting rises while swings nationalize, with bootstrapped CIs and the demographic mechanism |
| [2026 Polling](https://yardenmorad2003.github.io/election-dashboard/dashboard_en.html#polls2026) | The **live 26th-Knesset polling tracker** — the companion [Israeli Polling Saga](https://github.com/YardenMorad2003/israel-polls-dashboard) (1,181 polls across six cycles, blocs lens, pollster accuracy scoring) embedded as a dashboard tab and refreshed as new polls publish |

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

- **13 Knesset elections** (K13 1992 → K25 2022) at the national and locality level; **10 elections** (K16 2003 → K25 2022) at statistical-area (neighborhood) level; the **three direct-PM contests** (1996, 1999, 2001) at locality level, including ticket-splitting against the same-day Knesset vote.
- **Era-matched censuses**: each stat-area layer joins the census closest to its election — 2022 census for K21–K25, 2008 for K18–K20, 1995 (religion, age, post-1990 aliyah) for K16–K17 — a cross-referencing not published elsewhere.
- **Two bloc systems**: five sub-groups (Right, Haredi, Center, Left, Arab) plus **opposition-right** (Yisrael Beiteinu K21–25; Yamina & New Hope K24) following the research literature's Netanyahu-bloc distinction, aggregated into Right-Haredi vs Center-Left-Arabs. K24 views include a **Yamina-in-Right / Yamina-in-Center-Left toggle** on both maps, since that placement is genuinely contested.
- **Party identity, not ballot letters**: ballot letters are reused across unrelated parties (פה was the Center Party in 1999 before Yesh Atid; ת was Tehiya in 1992 before New Hope; כן chained Yisrael BaAliyah → Kadima → Blue & White → National Unity). All cross-year views identify parties by each election's own list name, with curated identity segments in the map's party picker and explicit reuse warnings in the party profiles.

## Methodology highlights

**Polling-venue locations (neighborhood map).** ~32,700 polling venues per modern election are geocoded and assigned to statistical areas by point-in-polygon. Two elections are anchored on **official CEC per-station address files**: 2022 (kalpiplaces) and 2009 (the CEC polling-place list of 2008-12-28, digitized for this project — 55% of the 2009 vote sits on a period-true street address, per-locality closure 99.94%). **2013 and 2015 inherit the 2009 official coordinates by (locality, kalpi-number) identity**, guarded by venue-name agreement or voter-roster agreement — measured at 92%/90% vote-weighted match before wiring. On top of that: **546 manually verified coordinate fixes** (cross-checked against the Education Ministry institution registry, street geometries, contemporaneous addresses, and voting-profile checks; every batch documented in evidence ledgers inside `analysis/statarea_inputs/`). Same-named venues in one city are separated by their official addresses. The dots layer is coordinate-keyed for 2009–2015 — one dot per building, dots ≡ stat-area placement by construction.

**Residence estimate.** A separate, clearly labeled model layer answers *how each neighborhood's residents voted* (vs where votes were physically cast): each venue's votes are redistributed over the stat-areas it serves via population-weighted catchments, closure-exact per city, with hold-out validation (median bloc error ~4–5.5 pp) printed on the map.

**Vote transfers.** Constrained least squares ecological inference (Goodman lineage; method credit: Harel Cain & Itamar Mushkin, clean-room reimplementation): the national transfer matrix minimizing prediction error over ~1,000–1,150 common localities, non-negative, row sums tied to electorate growth, non-voters as a real category. Validated three ways: r≈0.99 agreement with Cain's independent ballot-box-level estimates; an independent INES survey estimate per transition (agreement r=0.78–1.00, mean gap 2–10 pp), including a true April→September 2019 panel that measures recall bias directly (6–19 pp per row); and the published INES 2006 panel for the Kadima birth. For the four 2019–2022 transitions a **third, fully recall-free estimate** is layered on: the Israel Polarization Panel (the same respondents re-interviewed after every election) agrees with the ecological matrices at **r=0.96–0.97 with a ~4 pp weighted mean gap** — the tightest corroboration the method has. Sector-split tests flag transitions where the national-table assumption visibly fails.

**Polarization & sorting study.** A balanced panel of 896 localities across all 13 elections, population-weighted; sorting metrics (weighted SD, P90–P10 gap, dissimilarity index) and a nationalization metric (weighted SD of between-election swings); 2,000-resample bootstrap CIs; mechanism tested against education, fertility, and Haredi-vote gradients in the 31 largest Jewish cities.

## Data sources

- **Central Elections Committee (CEC)** — per-locality results K13–K25 and per-ballot results K16–K25 (historical files via [data.gov.il](https://data.gov.il)); the official **2022 polling-place address file** (kalpiplaces) and the official **2008-12-28 polling-place list** for the 2009 election (digitized for this project: 9,569 stations with street addresses and eligible-voter counts).
- **Central Bureau of Statistics (CBS)** — statistical-area boundaries (1995 / 2008 / 2022) and the matching censuses (incl. the 1995 census stat-area tables); socioeconomic index publications for municipalities and intra-city statistical areas (2008–2021); annual "Local Authorities in Israel" profiles 1999–2024 (wages, matriculation, Gini, migration); religion / "no religion classification" locality data (2019).
- **Ministry of Education institutions registry** (data.gov.il) — 28k geocoded schools/kindergartens used to verify polling-venue coordinates.
- **Harel Cain's *kolot-nodedim* station coordinates** — the polling-venue master list for pre-2022 elections (with the verified corrections above).
- **Israel National Election Studies (INES)** — 14 election surveys 1992–2022 as the transfers validation layer and the demographics page's individual-level panel (education, religiosity, age, ethnic origin); cited per-study in the official format (full list at the bottom of the transfers page).
- **Israel Polarization Panel (IPP)** — Gidron, Sheffer & Mor's eleven-wave 2019–2023 panel of the same respondents (Harvard Dataverse), the transfers page's **true-panel validation layer** for the 2019–2022 transitions (Jewish sample, unweighted — used row-normalized only).
- **1967 Green Line** — [geoBoundaries](https://www.geoboundaries.org) gbOpen (PSE ADM0), CC BY 4.0, simplified for display.
- **Base maps** — CARTO tiles © OpenStreetMap contributors (ODbL).

## Limitations — read before quoting numbers

**Geography & locations**
- Official polling-station address files exist **only for 2022 and 2009**. Other elections are reconstructions: 2013/2015 inherit the 2009 addresses by kalpi-number identity (name/roster-guarded; the number-stability assumption is shared with the prior method), K21–24 rest on venue-*name* geocoding, K16–17 on the addresses in the era's own results files. Verified fixes propagate across years **by venue name** — a venue that changed buildings between elections may appear at its anchor-year location.
- Double-envelope ballots (soldiers, hospitals, diplomats — ~458K votes in 2022, ~10%) are inherently unmappable below the national level.
- Geocoding coverage is below average in some Arab localities and in the settlements; **within-area percentages are reliable, but national sums from the stat-area layer are slightly biased**. Dots-layer vote placement: ~99% of votes in 2009–2022, ~82–85% in 2003–2006.
- The residence estimate is a **model, not a count** — use it with its printed hold-out error.

**Statistical inference**
- Everything locality- or area-level is **ecological**: correlations, transfer matrices, and sorting metrics describe aggregates, not individual voters (ecological fallacy).
- The transfer matrices assume **one national transfer table** across all localities. This is a knowing simplification: it is stress-tested (sector and SES splits, INES triangulation, bootstrap CIs) and fails visibly on at least one transition (2003→2006 Kadima, flagged on-page), but it cannot be fully verified. Bootstrap CIs measure sampling noise only, not assumption violations.
- The INES survey layer has its own biases (turnout over-reporting, recall drift toward winners) — measured at 6–19 pp per row where a true panel exists. The ecological and survey estimates serve as mutual sanity checks, not ground truth.
- The IPP panel layer is Jewish-only, unweighted and attrition-prone — its vote *levels* are visibly skewed. Only row-normalized transitions are used, and its social gradients are cross-checked against INES 2022 (education gap 21.5 vs 21.2 pp) before being trusted.

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
├── index.html + landing.js   THE landing page: canvas dot-map, 13-election
│                             scrubber, search, guided-stories rail
├── dashboard.html            Main dashboard (+ About & Methodology section)
├── election_map.html         Interactive Leaflet map (polygons / bubbles /
│                             cartogram / direct-PM mode / guided tours)
├── statarea_map.html         Neighborhood map: 10 elections × era census
├── transfers.html            Vote-transfer Sankeys + INES survey layer
├── demographics.html         Education gradient & within-city dispersion study
├── party_analysis.html       Per-party profiles (see PARTY_ANALYSIS.md)
├── findings.html             Polarization & sorting writeup
├── *_en.html                 Generated English siblings (analysis/build_english_pages.py)
├── data/                     ~60 JSON artifacts (results, geometries, censuses,
│   │                         transfer matrices, per-party metrics)
│   ├── landing_points.json         Landing dot-map (centroids × 13 elections)
│   ├── statarea_k{16..25}.json     Stat-area vote layers (3 geometry vintages)
│   ├── statarea_estimate_k*.json   Residence-estimate layers
│   ├── venue_dots_k*.json          Verified polling-venue points
│   ├── pm_direct.json              1996/1999/2001 direct-PM locality results
│   ├── vote_transfers.json         All transfer matrices + CIs + survey layer
│   ├── ipp_transfers.json          IPP true-panel matrices (2019–2022 transitions)
│   └── mcp/                        Pre-sliced artifacts for the remote MCP server
├── mcp/                      MCP server (see mcp/README.md):
│   ├── server.py                   Local stdio server (Claude Code / Desktop)
│   ├── worker/                     Cloudflare Worker (claude.ai / ChatGPT)
│   └── build_worker_data.py        data/mcp/ artifact builder
└── analysis/                 ~55 Python build scripts & audit instruments:
    ├── build_statarea_*.py         Era-specific stat-area pipelines
    ├── build_venue_dots.py         Venue aggregation + coordinate resolution
    ├── build_residence_estimate.py Residence-estimate model + hold-out validation
    ├── build_transfer_data.py      CVXPY transfer solver (+ bootstrap, SES splits)
    ├── build_ipp_transfers.py      IPP panel → true-panel transfer layer
    ├── build_ines_micro.py         INES individual-level panel (4 dimensions)
    ├── measure_k18_crosswalk.py    2009→2013/2015 crosswalk measurement gates
    ├── check_dots_vs_sa.py         Dots-vs-polygons consistency probe
    └── statarea_inputs/
        ├── station_coord_fixes.json      546 verified fixes + evidence ledgers
        ├── k25_ballot_addresses.json     Official CEC 2022 address snapshot
        ├── k18_ballot_addresses.json     Official CEC 2008-12-28 address snapshot
        └── ballot_coords_{18,19,20}.csv  Per-ballot resolved-coordinate audit trail
```

## Running locally

Static site — serve the folder with anything:

```bash
python -m http.server 8000        # or: npx serve .
```

Then open `http://localhost:8000/` (the landing page) and explore from there. The analysis scripts (Python 3, `numpy`/`pandas`/`cvxpy`/`shapely`/`openpyxl`) regenerate the `data/` artifacts; each script's docstring documents its inputs, method, and validation gates. After any coordinate-fix change, the full stat-area rebuild chain + validators must be run (documented in the scripts).

## Credits & literature

- **Vote-transfer method**: [Harel Cain — *kolot-nodedim*](https://kolot-nodedim.netlify.app/) and Itamar Mushkin (original under CC BY-NC-SA; this is an independent clean-room reimplementation on locality data, validated against their ballot-box estimates at r≈0.99).
- **INES** — the Israel National Election Studies (Tel Aviv University), founded by Asher Arian ז"ל and Michal Shamir. Surveys are used as an independent cross-check only; all analysis and interpretation are this site's responsibility.
- **Official data** — CBS and the CEC. All processing, cross-referencing and conclusions are this site's own and not endorsed by the official bodies.
- **Israel Polarization Panel** — Noam Gidron, Lior Sheffer & Guy Mor; *The Israel Polarization Panel Dataset, 2019–2023* (Harvard Dataverse). Used as the transfers page's true-panel validation layer; all processing and interpretation are this site's own.
- **Literature** anchoring the research pages (per-claim citations on-page): the *The Elections in Israel* series (1992–2022 volumes), *The Parties in Israel 1992–2021*, Arian & Shamir (2008) on the cleavage structure, and the affective-polarization work around the Israel Polarization Panel (*Electoral Studies*, 2022).
- **Libraries**: Chart.js, Leaflet; Python — pandas, NumPy, CVXPY/SCS, Shapely.
