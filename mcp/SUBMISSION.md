# OpenAI ChatGPT App Submission — Israeli Elections

Everything needed for the app-review form, ready to paste. Prerequisites on
the OpenAI side (done in the ChatGPT / platform UI, not here): organization
**identity verification** and the `api.apps.write` permission.

## App details

| Field | Value |
|---|---|
| App name | Israeli Elections |
| Logo | https://yardenmorad2003.github.io/election-dashboard/mcp/logo.png (512×512 full-bleed RGB PNG, no alpha) |
| Composer icon (≥48×48) | https://yardenmorad2003.github.io/election-dashboard/mcp/logo_small.png (128×128 full-bleed RGB PNG) |
| Short description | Query Israeli national election results 1992–2022: locality-level results, party histories, vote-transfer estimates, and demographics — in Hebrew or English. |
| Company / website URL | https://yardenmorad2003.github.io/election-dashboard/ |
| Support URL | https://yardenmorad2003.github.io/election-dashboard/mcp/support.html |
| Privacy policy URL | https://yardenmorad2003.github.io/election-dashboard/mcp/privacy.html |
| Category | Reference / Research / Data |

**Long description.** Israeli Elections turns a research dataset of Israeli
national elections into a conversational reference. It covers all thirteen
Knesset elections from 1992 to 2022 (K13–K25) at the locality level — every
city, town, kibbutz and village — plus the 1996/1999/2001 direct
prime-ministerial contests, party seat/vote trajectories with strongholds,
bloc-level vote-transfer matrices between consecutive elections (ecological
inference over ~1,000 localities, cross-checked against INES survey
crosstabs), and CBS socio-economic municipal profiles. Sources are the
official Central Elections Committee locality results, CBS statistics, and
the Israel National Election Studies series. Localities and parties can be
asked about in Hebrew or English. Read-only, no account needed, and no user
data is collected.

## MCP server

| Field | Value |
|---|---|
| Endpoint | https://israeli-elections-mcp.yardenmorad2003.workers.dev/mcp |
| Transport | Streamable HTTP (stateless JSON-RPC over POST) |
| Protocol versions | 2025-06-18, 2025-03-26, 2024-11-05 |
| Authentication | **None** — public, read-only, aggregate historical data |
| OAuth | N/A (no auth); no demo account needed |
| UI component / widget | None (tools only) |
| CSP | N/A — no UI component is rendered. Server-side, the only domain the app fetches from is `yardenmorad2003.github.io` (GitHub Pages CDN hosting the dataset). |

## Tools (11)

All tools are annotated `readOnlyHint: true`, `destructiveHint: false`,
`idempotentHint: true`, `openWorldHint: false` (closed historical dataset).

| Name | Title | Purpose |
|---|---|---|
| `list_elections` | All Elections Overview | Years, turnout, national bloc shares for K13–K25 + direct-PM years |
| `search_locality` | Find a Locality | Resolve Hebrew/English name or semel code; population + religious composition |
| `get_locality_results` | Locality Results | Bloc percentages, turnout, eligible/valid votes; one election or full series |
| `get_locality_parties` | Locality Party Breakdown | Party-level shares of valid votes + estimated vote counts |
| `get_national_results` | National Results | Every party's votes, share, seats, bloc for one election |
| `get_party` | Party History | 1992–2022 trajectory, name history, strongholds |
| `get_vote_transfers` | Vote-Transfer Matrix | Bloc transfer matrix between consecutive elections (ballot or survey) |
| `get_pm_direct` | Direct PM Elections | 1996/1999/2001 two-candidate results, national or per locality |
| `get_demographics` | Locality Demographics | CBS 2021 socio-economic profile + religion |
| `search` | Search Localities | Deep-research-compatible document search over localities |
| `fetch` | Fetch Locality Document | Deep-research-compatible document fetch by id |

## Test prompts and expected responses

1. **"How did Bnei Brak vote in 2022, party by party?"**
   → calls `get_locality_parties(Bnei Brak, 25)`. Expected: United Torah
   Judaism 59.79% (~52,431 votes), Shas 30.17% (~26,457), Religious Zionism
   4.43%, Likud 3.39%, out of 87,692 valid votes.

2. **"Where did left-bloc voters go between 2021 and 2022?"**
   → calls `get_vote_transfers(24, 25)`. Expected: left bloc retained 61.4%,
   22.0% moved to the center bloc, 15.7% did not vote (R² = 0.9965,
   1,165 localities).

3. **"Compare Umm al-Fahm's turnout in the 1999 and 2001 PM elections."**
   → calls `get_pm_direct(1999, Umm al-Fahm)` and `get_pm_direct(2001,
   Umm al-Fahm)`. Expected: 1999 turnout 74.53% vs 2001 turnout 4.09%
   (mass Arab boycott) — a 70-point collapse.

4. **"Show Likud's history since 1992."**
   → calls `get_party(Likud)`. Expected: 13-election trajectory (e.g. 32
   seats in 2022), name history, top-10 strongholds.

5. **"Which parties won nationally in 2022 and how many seats?"**
   → calls `get_national_results(25)`. Expected: Likud 32, Yesh Atid 24,
   Religious Zionism 14, with votes and bloc totals.

6. **"מה היו התוצאות בחיפה ב-2015?"** (Hebrew input)
   → calls `get_locality_results(חיפה, 20)`. Expected: Haifa's K20 bloc
   breakdown and turnout, demonstrating Hebrew-language queries.

7. **Deep research: "Profile the electoral history of Rahat."**
   → `search("Rahat")` then `fetch(<id>)`. Expected: a document with the
   full 1992–2022 bloc series.

## Localization

- Tool descriptions, field names, and instructions: **English (en-US)**.
- Inputs accepted in **Hebrew and English** (locality and party names, or
  numeric semel / ballot codes); unambiguous partial matches resolve.
- Outputs include both Hebrew (`name`) and English (`name_en`) names, so
  responses localize naturally to conversations in either language.
- No other locales; no region-specific pricing or content restrictions.

## Data & safety notes for review

- All data is public, aggregate, historical (1992–2022); no personal data.
- No user data is collected, stored, or logged (see privacy policy).
- The app is read-only: no tool has side effects; nothing is written.
- Political neutrality: the app reports official published results and
  peer-methodology estimates (clearly labeled ecological inference / survey
  crosstabs); it makes no predictions and takes no positions.
