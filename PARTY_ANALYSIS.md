# 🗳️ Party Analysis — socioeconomic & geographic profiles per party

A standalone page that profiles **each Knesset party separately** (K13 1992 → K25 2022): its
seat/vote trajectory, geographic strongholds, and the **socioeconomic fingerprint** of the
localities where it is strong — education, fertility, income, religiosity, and the CBS
socio-economic index.

Companion to `findings.html` (the nationalization/sorting writeup). Same no-build stack:
single HTML file, vanilla JS, CDN Chart.js 4.4.1, Hebrew RTL, reads one precomputed JSON.

- **Page:** `party_analysis.html`
- **Data:** `data/party_analysis.json` (~330 KB, 38 parties, precomputed)
- **Generator:** `analysis/build_party_analysis.py` (self-contained; reads `data/*.json`)

## View it

Static server required (the page `fetch()`es the JSON — opening the file directly won't load data):

```bash
python -m http.server 8000
# then open:
http://localhost:8000/party_analysis.html
```

## What it shows

Pick a party from the dropdown (grouped by bloc; the 28 lists that ever won a seat). For that party:

| Section | What it is |
|---|---|
| **Trajectory** | Seats (bars) + national vote-share % (line), K13–K25. Tooltip shows the list's name in each election. A banner warns when the **ballot-letter was reused** by different lists (e.g. `כן`: ישראל בעלייה → קדימה → כחול לבן → המחנה הממלכתי). |
| **Strongholds** | Localities where the party's share of the local valid vote is **highest** (≥300 valid votes). |
| **Contributors** | Localities supplying the most **absolute** votes (% of the party's national total) — "where the votes actually are." |
| **Socioeconomic gradient** | Population-weighted correlation of the party's local share with 8 socio variables, with an **All localities / Jewish-majority** toggle (see [Methodology](#methodology-why-two-universes)). |
| **Standardized profile** | Party-voter mean vs the electorate mean for each variable, expressed in **standard-deviation units** (a comparable fingerprint), same toggle. |
| **Religion mix** | Vote-weighted % Jews / Arabs / "no religious classification" (mainly FSU immigrants). |
| **Socio-cluster distribution** | Share of the party's votes by CBS socio-economic cluster (1 = low … 10 = high). |

## Methodology (why two universes)

Every metric is **ecological** — computed at the locality level, weighted by valid votes — and
joins the party-by-locality vote data to the **201 socioeconomic municipalities**.

Pooling Arab and Jewish localities **confounds** party socio gradients: Arab towns are both
low-SES *and* near-zero for most Jewish-sector parties, which swamps the real gradient *within*
the Jewish sector. Example — **Likud**, socio-index correlation:

| | All localities | Jewish-majority (pct_jews ≥ 70) |
|---|---|---|
| socio-index | **+0.26** (misleading) | **−0.02** |
| % academics | +0.06 | **−0.27** |
| income/capita | +0.21 | **−0.13** |

So the page reports **both** and defaults to showing the confound explicitly. (This mirrors the
main research finding, whose mechanism analysis restricted to Jewish cities for the same reason.)

## Data model & gotchas

Two things about the source data that this build depends on — **read before reusing `parties_by_locality.json`:**

1. **`parties_by_locality.json` values are per-locality vote *shares* (%), not counts.** Each
   locality's party values sum to ~100.
2. **It contains 3 corrupt rows** carrying raw counts instead of percentages —
   `'תל אביב  יפו'`, `'פוריה  כפר עבודה'`, `'פוריה  נווה עובד'` (all double-spaced duplicates,
   value-sum > 150). They are **dropped** (detected by sum > 150).
3. **Real valid-vote weights come from `localities.json` → `data[k].kosher_votes`.** Absolute
   votes = `share% × kosher_votes`. External-envelope rows (`מעטפות חיצוניות`) are excluded from
   the geographic lists.
4. **Parties are tracked by ballot-letter code** (stable in Israel: `מחל`=Likud all 13 elections).
   Some letters are inherited by successor lists — surfaced via the name-history banner.
5. **Hebrew name join** uses a conservative normalizer (collapse spaces/hyphens/gershayim, finals,
   double matres `יי→י`,`וו→ו`; keep single letters so `אילת≠אילות`, `צפת≠צופית`) plus 3 hand
   aliases. Muni-anchored, exact-match-first → 199/201 munis matched, one-to-one.

## `party_analysis.json` schema

```jsonc
{
  "meta": { "years": ["13"…"25"], "year_of": {...}, "socio_fields": [...],
            "socio_universe": 201, "caveats": [...] },
  "parties": [{
    "code": "מחל", "name": "הליכוד", "bloc": "right",
    "name_history": { "13": "הליכוד", … }, "bloc_history": {…},
    "peak_seats": 38, "ref_k": "25", "ref_year": 2022, "total_votes_ref": 1004357,
    "trajectory":  [{ "k","year","seats","vote_pct","name","bloc" }, …],
    "strongholds": [{ "name","share","valid","votes" }, …],       // by local share %
    "contributors":[{ "name","share","valid","votes","pct_of_party" }, …], // by abs votes
    "socio_n": 191, "socio_n_jew": 111,
    "profile": { "all": [{ "var","label","unit","party","elec","sd","d","n" }, …],
                 "jewish": [ … ] },                                // d = standardized diff
    "corr":    { "all": [{ "var","label","r","n" }, …], "jewish": [ … ] },
    "religion": { "pct_jews","pct_arabs","pct_russians" },
    "cluster_dist": { "1": …, "10": … }                           // % of party votes
  }, … ]
}
```

## Regenerating

```bash
python analysis/build_party_analysis.py   # reads data/*.json → writes data/party_analysis.json
```

Self-contained, no dependencies beyond the stdlib. On Windows, run under `PYTHONUTF8=1` — the
console is cp1252 and will crash on Hebrew `print()`, though the JSON file is written correctly
regardless (verify the file, not the traceback).

## Caveats

- **Ecological** — locality aggregates, not individual voters (ecological-inference limit).
- Socio profile covers **201 municipalities only** (no regional councils → kibbutz/moshav/
  settlement selection bias).
- Socio snapshot is the **latest** (~2021 base fields, religion 2019, census 2022) applied to the
  reference election; it is not time-varied per election.

## Data sources

- Israel Central Elections Committee (results)
- Israel Central Bureau of Statistics (socioeconomic index, demographics, census 2022)
