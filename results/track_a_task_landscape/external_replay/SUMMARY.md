# E3 + PhF-3 — Independent-cohort replay for TOP2A − EPAS1

**Updated 2026-04-26.** CPTAC-3 M-staging analysis completed via cBioPortal RNA
+ GDC clinical API merge (n=155, 20 M1 / 135 M0). Result: honest negative on the
metastasis gate. See `cptac3_gate_result.json` for full metrics.

| Cohort | Task | Verdict |
|---|---|---|
| GSE53757 (Affymetrix, 144) | tumor-vs-normal sanity | not a metastasis replay; AUROC 0.723 |
| GSE40435 expanded (Illumina, 202) | tumor-vs-normal sanity | not a metastasis replay; AUROC 0.643 |
| **CPTAC-3 ccRCC (cBioPortal, 155)** | **M0 vs M1 metastasis** | **FAIL (2/5 gate tests fail)** — AUROC 0.683, direction preserved, p=0.006; but ci_lower=0.542 (< 0.60) and delta_baseline=−0.007 (TOP2A alone is 0.691, compound does not outperform) |
| **IMmotion150 (cBioPortal, 263)** | **PFS in metastatic ccRCC** | **PASS (3/3 pre-reg tests)** — log-rank p=0.0003, HR 1.36, C-index 0.601 |

The IMmotion150 result **is** a bona-fide external validation: independent
cohort, independent preprocessing (trial-grade log-TPM, not star_tpm),
independent endpoint (time-to-event PFS, not binary M-stage), and the kill
tests were pre-registered before the analysis (see
`preregistrations/20260423T044446Z_phf3_immotion150_pfs_replay.yaml`).

Three ccRCC cohorts evaluated in priority order. The plan:
first cohort with `TOP2A + EPAS1 + M-status` wins the metastasis
replay. If none supply M-stage, tumor-vs-normal AUROC is reported
as a sanity check and flagged as *not* a metastasis replay.

Flagship internal replay remains 5-fold stratified CV on TCGA-KIRC
(AUROC 0.722 ± 0.078; permutation null 0.509).

## Per-cohort table

| Cohort | Platform | N | Task | TOP2A+EPAS1 present | M-stage | law_AUROC | perm_p | ci_lower | Δbase | Gate verdict | Honest caveat |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gse53757 | Affymetrix HG-U133 Plus 2.0 (GPL570) | 144 | tumor_vs_normal_SANITY | yes | no | 0.723 | 0.000 | 0.641 | -0.248 | — | NOT a metastasis replay — cohort lacks M-stage |
| gse40435_expanded | Illumina HumanHT-12 v4 (GPL10558) | 202 | tumor_vs_normal_SANITY | yes | no | 0.643 | 0.001 | 0.557 | -0.351 | — | NOT a metastasis replay — cohort lacks M-stage |
| **cptac3_ccrcc** | **CPTAC-3 proteogenomic (cBioPortal RNA + GDC clinical)** | **155 (20 M1 / 135 M0)** | **metastasis M0 vs M1** | **yes** | **yes** | **0.683** | **0.006** | **0.542** | **−0.007** | **FAIL** | Direction preserved (p=0.006); ci_lower=0.542 < 0.60 gate threshold; TOP2A alone (0.691) outperforms compound — gate correctly refuses cross-platform replication |
| IMmotion150 (cBioPortal) | Trial-grade log-TPM (Phase 2, n=263) | 263 | PFS in metastatic ccRCC | yes | all M1 (survival endpoint) | — | log-rank p=0.0003 | — | — | PASS (3/3 pre-reg tests) | Different endpoint (survival, not M-stage); HR=1.36, C=0.601 |

## Interpretation

**CPTAC-3 metastasis replay (added 2026-04-26).** The gate correctly applies the same pre-registered thresholds. Two failures: (1) ci_lower=0.542 below 0.60 — the small M1 cohort (n=20) produces wide bootstrapped CIs (0.54–0.83); (2) delta_baseline=−0.007 — in this proteogenomic cohort TOP2A alone (AUROC 0.691) marginally outperforms the compound law (0.683). The sign (direction) is maintained: high TOP2A−EPAS1 predicts M1, p=0.006. This is an honest negative: the law's direction generalizes, but the compound advantage over TOP2A alone does not survive the smaller CPTAC-3 cohort. The gate refuses to call this a replication — which is the correct outcome.

**IMmotion150 remains the strongest external validation.** Independent cohort, independent preprocessing, independent endpoint (PFS survival), pre-registered kill tests, 3/3 pass.

**Flagship internal replay** (TCGA-KIRC 5-fold CV, AUROC 0.722 ± 0.078) remains the within-cohort benchmark.

## Files

- `data/build_gse53757.py` — builder for Affymetrix GSE53757 (72T + 72N).
- `data/build_gse40435_expanded.py` — Illumina GSE40435 with the 44-gene
  panel (the existing 8-gene `gse40435_kirc.csv` omits TOP2A/EPAS1).
- `data/build_cptac3_m_stage.py` — cBioPortal RNA (rcc_cptac_gdc) + GDC
  clinical API merge; extracts M-staging from AJCC pathologic/clinical fields,
  excludes MX, runs TOP2A−EPAS1 gate.
- `cptac3_gate_result.json` — full gate metrics for the CPTAC-3 metastasis run.
- `per_cohort.json` — machine-readable per-cohort metric bundle.
