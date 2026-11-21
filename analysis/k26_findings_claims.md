# K26: findings claims vs the rebuilt data (agent A4, 2026-11-20)

Every sentence on `findings.html` (including the `mechNote` text, city examples, tags and footer)
whose number or claim no longer matches `findings_data.json` as rebuilt with Knesset 26.
Nothing in this list has been reworded on the page. The owner decides the wording.

Columns: **page text** = what the page says now · **old data** = `findings_data.json.bak_prek26`
(the stale 896-locality / 13-election file the page was written from) · **new data** = the rebuilt
file (917-locality balanced panel, 14 elections, 1992–2026). R² = R² of a linear trend on election
year, computed the same way for both files (it reproduces the page's old tags exactly: 0.842 / 0.802).

Already data-driven after this pass (no owner action needed): panel size 917, "14 elections",
K13–K26, 1992–2026 in kicker / lede / dist panel / footer, the dist histogram (now 1992 vs 2026),
the four stat cards (+47%, 39.69→74.32, 0.2675→0.4682 "+75% in 34 years", 7.45→2.39), the CI tags,
`mechNote` correlations and n (35), movers chart + lists, and the profiles table.

## A. Claims whose number changed or weakened (priority order)

| # | Where | Page text | Old data | New data | Status |
|---|---|---|---|---|---|
| 1 | Movers / `mechNote` city examples | `mechNote`: "הערים החרדיות (ירושלים, בית שמש, בני ברק) נעו ימינה" | Jerusalem +12.0 (65.3→77.3), Beit Shemesh +18.6, Bnei Brak +14.1 | Jerusalem **+2.9** (65.3→68.3), Beit Shemesh +13.5, Bnei Brak +9.9 | **Weakens for Jerusalem.** Jerusalem left the right-mover list (top 6) but is still in `movers.featured_right`, so the chart still draws it as a right mover. |
| 2 | Seg tag | "0.27→0.44 (+64%)" | 0.2658→0.4354 (+64%) | 0.2675→**0.4682** (**+75%**) | Number outdated; claim **strengthens** (2026 is the series maximum). |
| 3 | Fan tag | "SD 17→26 (+50%)" | 17.29→25.87 (+50%) | 17.48→25.72 (**+47%**) | Number outdated. Note: dispersion in 2026 (25.72) is slightly **below** 2022 (26.06). |
| 4 | R² tags + footer | Fan "R²=0.84"; Seg "R²=0.80"; footer "מגמות המיון עקביות וחזקות (R²≥0.80)" | wsd 0.842 · dissim 0.802 · P90–P10 0.829 | wsd **0.810** · dissim **0.839** · P90–P10 **0.662** | Tags outdated. Footer "R²≥0.80" no longer holds if it covers the P90–P10 gap (0.66); holds for SD and dissimilarity. |
| 5 | Right-mover list (data-driven, listed for prose impact) | — | Beit Shemesh +18.6, Bnei Brak +14.1, Afula +13.6, Kiryat Gat +13.1, Jerusalem +12.0, Tiberias +11.6 | Beit Shemesh +13.5, **Beitar Illit +11.2**, **Dimona +10.9**, Kiryat Gat +10.5, Bnei Brak +9.9, Afula +7.7 | Jerusalem and Tiberias out; Beitar Illit and Dimona in. Any prose naming the right movers should follow. |
| 6 | Left-mover list (data-driven) | — | Rosh HaAyin −21.5, Hod HaSharon −19.5, Tel Aviv −17.2, Givatayim −12.9, Kiryat Ono −11.2, Ramat HaSharon −10.7 | Rosh HaAyin −26.9, Hod HaSharon −25.6, Tel Aviv −23.2, Givatayim −19.1, **Ramat Gan −18.1**, Kiryat Ono −17.5 | Ramat Gan in, Ramat HaSharon out (now −15.9). Left movers all **strengthen**. |
| 7 | `mechNote` aside | "ערי העלייה מברה"מ/פריפריה, כמו באר שבע, נעו ימינה במנגנון שלישי (קפיצת 1996)" | Beer Sheva 56.8→67.1 (+10.4) | 56.8→**60.3 (+3.5)** | Weakens (still rightward, much smaller). |
| 8 | Lede | "פיזור ההצבעה לימין-חרדים בין הישובים גדל ב-~50%" | +50% | **+47%** | "~50%" still defensible; the card now says +47%. |
| 9 | Card sub (static) | "כמעט הוכפל" (P90–P10) | 38.45→72.6 (×1.89) | 39.69→74.32 (×1.87) | Holds. |
| 10 | Lede / card sub | "התנודות מסתנכרנות", "ירדה → תנודות מסונכרנות" | swing SD 7.29 → last 5.50, min 2.32; slope −0.091/yr [−0.115, −0.069]; R² 0.28 | 7.45 → last (25→26) **3.20**, min 2.39; slope −0.096/yr [−0.123, −0.073]; R² 0.34 | Holds (slightly stronger). |
| 11 | Dist panel caption | "2026 (כתום) מפוזר לקצוות; 1992 (ירוק) מרוכז יותר" (years now from data) | 2022: P10 7.2 / P90 79.8, bimodality 0.459 | 2026: P10 **1.2** / P90 **75.5**, bimodality 0.452 | Holds, but the spread in 2026 comes from the low end (P10 collapse); the top decile fell back from 82.6 (2022). |
| 12 | Lede / footer | "הישובים ... התרחקו זה מזה" / dissimilarity | — | dissim 2026 = 0.4682 (max of series) | Holds; strongest single point is 2026. |
| 13 | `mechNote` correlations (data-driven) | r = −0.80 / +0.60 / +0.56, 31 cities | — | r = −0.81 / +0.62 / +0.58, **35** cities | Updated automatically. |

## B. Same issue on other pages (prose, left untouched)

| Page | Text | Old | New |
|---|---|---|---|
| party_analysis `#sysLit` | "את שיא 2006 (41.4% אצלנו)" | 2006 = list-level Pedersen peak | **2026 = 49.0%** is now the peak (stat card already says so). |
| party_analysis `#sysLit` | "תנודתיות הרשימות (ממוצע ~27%) לתנודתיות הגושים (~12%)" | 27.4% / 12.4% (12 transitions) | **29.0%** / 12.1% (13 transitions). |
| party_analysis intro | "פיצול שיא" | ENP-votes peak 9.01 (1999) | peak now **9.06 (2026)**; claim strengthens. |
| party_analysis card | "(ירידה עקבית)" | PSNS 0.7013→0.5448 | 0.7013→**0.5008** (series minimum); holds. |
| demographics `gradient` lead | "השיפוע ... כמעט הוכפל בין 1992 ל-2022, והמתאם התחזק מ-0.35− ל-0.82−" | series ended 2022 | series now ends at **2026: r −0.835, slope −1.664** (Jewish, interpolated). Text is still literally true for 1992–2022; the stats bar now shows 2026. |
| demographics `gradient` lead | "מפקדי הלמ"ס 1972–2022, באינטרפולציה לשנת הבחירות" | — | the 2026 point lies after the last census, so it is an extrapolation/carry-forward, not an interpolation (builder detail: `analysis/build_demographics_panel.py`). |
