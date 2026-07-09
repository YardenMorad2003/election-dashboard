# MRP Feasibility Memo (ML project 6) — 2026-07-09

## Verdict: feasible, with one data gap to close

**Individual level (the "MR"):** raw INES microdata exists locally for every
wave 1992–2025 (`C:\Users\yarde\Downloads\INES\<year>\`, STATA/SPSS + the
transfer-project's `INES_INVENTORY.md`). Vote (post-election where available,
n≈580–1,900/wave), education, religiosity (4-tier self-definition), age,
sector. Weights ship 2009+ only; 1996 is two separate samples (Jews/Arabs)
needing electorate-share pooling. `data/ines_micro.json` is aggregates built
from these — the raw rows are what MRP needs, and they're present.

**Poststratification frame (the "P"):** the 2022 census gives per-SA
MARGINALS (academic %, age bands, datiyut, religion) — but our site files
kept only what the map shows (e.g. `datiyut` = dominant household category,
not shares). Gap to close: re-pull the full census SA file (CKAN resource,
verified keyless) and check whether religiosity/education SHARES per SA are
published; where only marginals exist, synthesize joint cells per SA via
raking/IPF anchored on the INES joint distribution. This is standard but must
be disclosed as modeled.

**Cell design (v1):** Jewish sector: religiosity(4) × education(2) × age(3)
= 24 cells/SA; Arab sector: single cell v1 (INES Arab-sample n is thin;
religion shares per SA are solid). Fit hierarchical logit per bloc on INES
(wave-pooled 2019–2022 first), predict cells, poststratify to SA.

**Validation (the unusual asset):** predicted SA-level bloc shares can be
checked against ACTUAL SA results from the tensor — most MRP work can never
do this. Hold-out at city level.

**Order of work:** (1) census re-pull for share columns; (2) INES harmonized
extract (vote+covariates, one CSV/wave — reuse inventory's variable maps);
(3) raked frame; (4) model + validate K25, then extend back.

**Risks:** small INES n per covariate cell (partial pooling handles);
religiosity scale changes pre-2009 ("observance" waves lack a haredi tier);
census religiosity available only for Jewish-majority SAs; disclosure burden.
