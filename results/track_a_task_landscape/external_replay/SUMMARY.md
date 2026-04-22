# E3 — Independent-cohort replay for TOP2A − EPAS1

Three ccRCC cohorts evaluated in priority order. The plan:
first cohort with `TOP2A + EPAS1 + M-status` wins the metastasis
replay. If none supply M-stage, tumor-vs-normal AUROC is reported
as a sanity check and flagged as *not* a metastasis replay.

Flagship internal replay remains 5-fold stratified CV on TCGA-KIRC
(AUROC 0.722 ± 0.078; permutation null 0.509).

## Per-cohort table

| Cohort | Platform | N | Task | TOP2A+EPAS1 present | M-stage | law_AUROC | perm_p | ci_lower | Δbase | Gate verdict | Honest caveat |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gse53757 | Affymetrix HG-U133 Plus 2.0 (GPL570) | 144 | tumor_vs_normal_SANITY | yes | no | 0.723 | 0.000 | 0.632 | -0.248 | — | This is NOT a metastasis replay — the cohort lacks M-stage. The AUROC here refle… |
| gse40435_expanded | Illumina HumanHT-12 v4 (GPL10558) | 202 | tumor_vs_normal_SANITY | yes | no | 0.643 | 0.000 | 0.560 | -0.351 | — | This is NOT a metastasis replay — the cohort lacks M-stage. The AUROC here refle… |
| cptac3_ccrcc | CPTAC-3 proteogenomic (PDC) | — | metastasis_preferred | stub | — | — | — | — | — | stub (see NOTE) |  |

## Interpretation

No M-stage cohort was available in this session. The tumor-vs-normal sanity checks (flagged *not* as metastasis replay) gave law_AUROC values of 0.723, 0.643 on cohorts gse53757, gse40435_expanded.

These values test a different thing than the survivor claim: they ask whether a proliferation-over-HIF-2α score separates tumor from normal (expected to be high on any ccRCC cohort). They do NOT test whether the same score separates M1 from M0 patients, which is what the survivor narrative claims.

**Flagship internal replay** (TCGA-KIRC 5-fold CV, AUROC 0.722 ± 0.078) remains the strongest within-cohort replay evidence. The three external cohorts map the infrastructure of an independent-cohort metastasis replay and identify CPTAC-3 as the natural next step once a PDC-API token is available.

## Files

- `data/build_gse53757.py` — builder for Affymetrix GSE53757 (72T + 72N).
- `data/build_gse40435_expanded.py` — Illumina GSE40435 with the 44-gene
  panel (the existing 8-gene `gse40435_kirc.csv` omits TOP2A/EPAS1).
- `data/build_cptac3_ccrcc.py` — PDC GraphQL probe; falls back to a
  header-only stub + `cptac3_ccrcc_NOTE.md` manual-retrieval notes when
  the public endpoint is unreachable from the current environment.
- `per_cohort.json` — machine-readable per-cohort metric bundle.
