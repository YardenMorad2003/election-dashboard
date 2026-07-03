# Source-check: dashboard vs. the Elections-in-Israel literature (2026-07-03)

Cross-check of the dashboard's computed metrics and interpretive claims against the verified-conclusions
digest of the academic literature (`~/Downloads/israel_elections_complete_with_epub_crosscheck_1992_2022.md`,
built from the *The Elections in Israel* volumes 1992–2022, *The Parties in Israel 1992–2021*,
Arian & Shamir 2008, and the Israel Polarization Panel article in *Electoral Studies* 2022).
Page anchors refer to the digital editions.

## Confirmations (dashboard ↔ literature agree)

| # | Dashboard claim/number | Literature | Verdict |
|---|---|---|---|
| 1 | ENP by seats: 8.69 (1999) → 6.17 (2003) — `party_system.json` | "effective number of parliamentary parties fell from 8.69 in 1999 to 6.17 in 2003" [2003 vol., PDF pp. 44–46, 58–59] | **Exact match to 2 decimals** — independent replication |
| 2 | Pedersen list volatility 2006 = 41.4%, bloc = 21.0% | 2006 party instability 42.7% (different convention), individual switching 63%, party ≫ bloc instability [2006 vol., Kadima ch.] | Consistent; the qualitative claim (party ≫ bloc) is directly supported |
| 3 | party_analysis #system lede: "lists stormy, blocs stable, nationalization falls" | Hazan: high bloc stability alongside party instability; post-2003 "non-system" [Parties, pp. 720–723, 722] | Supported |
| 4 | findings.html thesis: "levels diverge, swings synchronize" | Same macro trend at the locality level; books add the individual-level complement | Consistent (books don't measure locality geography — complementary) |
| 5 | INES survey layer 2003→2006: right→center 32.1% | Kadima drew 42% of its votes from 2003 Likud voters [2006 vol., Kadima ch.] | Consistent — the survey layer sides with the literature |
| 6 | `opposition_right` bloc split (YB from K21; Yamina/New Hope K24) | "right bloc" ≠ "Netanyahu-compatible bloc"; Liberman's refusal explains the deadlock [2019–2021 vol., pp. 20–21] | Classification directly supported |
| 7 | demographics: income divided the map by 1999; identity channels it | Representation gap: 58% of MKs economically liberal vs 68% public preferring social approach; system locked on conflict cleavage [2009 vol., pp. 23–24]; 2013 protest → centrist leverage [2013 vol., pp. 16–17] | Consistent |

## Discrepancies found (ours) and what was done

| # | Issue | Evidence | Action taken |
|---|---|---|---|
| 1 | **Ecological party matrix 2003→2006 inverts Kadima's sources**: Shinui 59% / Labor 26% / Likud 14% (and a near-corner 88% of Shinui voters → Kadima) vs literature INES 42% Likud / 23% Labor / 17% Shinui / 4% new | [2006 vol., Kadima ch.] | Added a targeted warning on transfers.html shown only for 16→17 + party view, plus a "validation against the literature" paragraph in the method box |
| 2 | **Tooltip label "רשימות בכנסת" was wrong**: `n_lists` counts *tracked* lists incl. 0-seat ones (16 for 1999 vs 15 entered; 14 for 2009 vs 12 entered; 13 for 2022 vs 10 entered) | Books' entered-Knesset counts: 15 (1999), 12 (2006), 12 (2009) | Relabeled to "רשימות במעקב" (tooltip + per-election card + chart caption) |
| 3 | **sysNote claimed ENP-votes uses "only lists that entered the Knesset"** — actually computed over all tracked lists incl. below-threshold (verified numerically: stored 7.75 for 2022 = all-tracked; entered-only would be 6.76) | build_party_system.py L77; literature's true electoral ENP for 1999 is 10.3 (all lists that ran) vs our 9.01 | Corrected the note and added the 10.3-vs-9.01 calibration sentence |
| 4 | **sysCards "bloc volatility — a third of list level"**: actual ratio is 12.4/29.2 ≈ 0.42 | internal | Changed to "כ-40%" |

## Content added (with citations)

- **findings.html**: new panel "הממצא מול ספרות המחקר" — 6 cited items (non-system/bloc stability;
  2006 individual-level volatility benchmark; Arian–Shamir cleavage persistence 1977/1996–2006;
  2022 identity-cleavage prediction; post-2001 turnout regime; affective polarization 2019–2021) + sources line.
- **party_analysis.html**: static "עוגן בספרות" paragraph under the party-system section
  (exact ENP replication, direct-election repeal effect, non-system, 2006 benchmark).
- **transfers.html**: 16→17 party-view warning + method-box validation paragraph (see above).
- **demographics.html**: "הקשר מחקרי" note under the income-vs-education section
  (2009 representation gap, 2013 protest translation).
- **dashboard.html**: cited sentence in the bloc-definitions card supporting the opposition-right split.
- All translated in `analysis/en_strings.py`; EN pages rebuilt; leftover reports clean
  (dashboard's 1 remaining Hebrew line is a pre-existing dev-facing CSS comment).

## Notes / not fixed

- Book seat-count nit (external, not ours): the digest's Likud trajectory row lists Sept 2019 as 31 seats;
  the official result was 32. Everything else in the digest checked out against known results.
- The eco bloc matrix 16→17 sends 25.7% of the 2003 right bloc to abstention (survey: 4.5%) — partly the
  documented 2006-registry interpolation issue (already flagged on-page); no change beyond the existing warning.
