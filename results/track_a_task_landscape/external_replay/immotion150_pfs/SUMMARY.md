# IMmotion150 external replay — TOP2A − EPAS1 stratifies PFS

**Status.** All 3 pre-registered kill tests **PASS** (2026-04-23).
**Pre-registration** written and git-committed *before* this analysis ran:
[`preregistrations/20260423T044446Z_phf3_immotion150_pfs_replay.yaml`](../../../../preregistrations/20260423T044446Z_phf3_immotion150_pfs_replay.yaml)

## Cohort

IMmotion150 (cBioPortal study `rcc_iatlas_immotion150_2018`). Phase-2
randomized trial of **atezolizumab ± bevacizumab** in previously untreated
metastatic renal clear-cell carcinoma. Published: McDermott *et al.*,
*Nature Medicine* 2018 (PMID 29867230). All patients metastatic at baseline
— therefore *not* an M0-vs-M1 replay. This is a prognostic-score replay:
does the survivor-law *score* stratify progression-free survival in an
ImTx-treated cohort?

- n = 263 samples after QC
- Events (PFS progression) = 164
- Platform: bulk tumor RNA-seq, TPM (log2)
- Not a subset of TCGA-KIRC (trial-level biopsy collection, different
  preprocessing pipeline)

## Score definition

The same equation the 5-test falsification gate accepted on TCGA-KIRC
metastasis (M0 vs M1, n=505, AUROC 0.726, Δbaseline +0.069):

$$\text{score} = \text{TOP2A} - \text{EPAS1}$$

No per-gene z-scoring, no cohort-specific refitting. Same numbers, same
signs. The only cohort-specific step is z-scoring the **final score**
to report Cox HR per standardized unit.

## Pre-registered kill tests (committed 2026-04-23T04:44:46Z, before
this analysis ran)

| # | Test | Threshold | Observed | Pass |
|---|---|---|---|---|
| 1 | Log-rank on median split (two-sided) | `p < 0.05` | **p = 0.00027**, χ² = 13.26 | ✅ |
| 2 | Cox HR per z-score | `|log HR| > log 1.3` AND 95 % CI excludes 1 | **HR = 1.36** (95 % CI 1.16–1.59), p = 0.0001 | ✅ |
| 3 | Harrell C-index (risk direction) | `> 0.55` | **0.601** | ✅ |

Verdict = **PASS**. Direction observed: *high score → worse PFS.* Matches
the biological prediction written into the pre-reg (ccA/ccB proliferation-
over-HIF-2α axis).

## Clinical-effect summary

| Group (median-split on `TOP2A − EPAS1`) | n | Median PFS | 95 % CI |
|---|---|---|---|
| High score (proliferation > HIF-2α) | 132 | **5.35 months** | from KM |
| Low score (HIF-2α > proliferation) | 131 | **12.88 months** | from KM |

**Absolute median PFS gap: 7.53 months.** On an independent metastatic
ccRCC cohort receiving immunotherapy + anti-VEGF, a two-gene tumor-biology
score — discovered by unconstrained symbolic regression on TCGA and
accepted by a pre-registered 5-test gate — separates median PFS by more
than seven months.

## Why this is a fair external replay

1. **Cohort independence.** IMmotion150 is a multi-site Phase-2 trial; no
   known overlap with TCGA-KIRC (which used Surgery-of-origin banking
   rather than clinical-trial enrollment).
2. **Preprocessing independence.** TCGA-KIRC data is star_tpm from the
   GDC-Xena hub (RSEM on STAR alignment); IMmotion150 is cBioPortal's
   log-TPM release from the published trial. Different pipelines, different
   normalization choices.
3. **Endpoint independence.** Training endpoint was categorical
   (M-stage classification). Replay endpoint is time-to-event (PFS under
   immunotherapy). Same score, different question.
4. **Pre-registration.** The three kill tests were locked before this
   analysis was run (see `preregistrations/20260423T044446Z_phf3_immotion150_pfs_replay.yaml`).
   Direction-of-effect was NOT pre-specified — the pre-reg accepts either
   direction if magnitudes clear.

## What this is *not*

- Not a claim that TOP2A − EPAS1 beats existing ccRCC prognostic
  scores (IMDC / MSKCC risk). We have not benchmarked against those.
- Not a claim of treatment-effect interaction with atezolizumab +
  bevacizumab. IMmotion150 had two arms; this analysis pooled them
  because the pre-reg did not specify arm-stratified Cox.
- Not a claim of causality. High proliferation biology is a hazard
  marker across most solid tumors; the novelty is the *compactness*
  of a pre-registered 2-gene form that replicates.

## Files

- `verdict.json` — machine-readable kill-test outcomes.
- `km_median_split.png` — Kaplan-Meier curves with log-rank + Cox + C-index
  in the title.
- `../../../../preregistrations/20260423T044446Z_phf3_immotion150_pfs_replay.yaml`
  — the pre-registration committed before this analysis.
- `../../../../src/phf3_immotion150_replay.py` — the script that produced
  this verdict (reproducible from `data/immotion150_ccrcc.csv`).
- `../../../../data/build_immotion150.py` — builder that fetches the
  263-sample slice from cBioPortal's public REST API.

## G3-NEW: Adjusted Cox — confounding control (2026-04-23)

Pre-registration: `preregistrations/20260423T060533Z_g3_adjusted_cox_immotion150.yaml`
Full results: `g3_adjusted_cox/adjusted_cox.json`

**Important finding about IMmotion150**: The cBioPortal data includes **three
treatment arms** — atezolizumab alone (n=86), atezo+bevacizumab (n=88), and
**sunitinib** (n=89, non-ICI VEGF inhibitor). This means TOP2A-EPAS1 was tested
on ICI and non-ICI treated patients simultaneously.

| Cox model | n | HR (score_z) | 95% CI | p |
|---|---|---|---|---|
| Unadjusted | 263 | 1.361 | 1.165–1.591 | 0.0001 |
| + treatment arm (3-level) | 263 | **1.365** | 1.168–1.594 | 0.0001 |
| + treatment + log(TMB) | 158 | 1.293 | 1.034–1.618 | 0.024 |

HR **actually increased** by 0.4% after treatment adjustment (attenuation = −0.9%,
i.e. slightly negative). This means the TOP2A-EPAS1 prognostic signal is
**not explained by treatment arm** — including sunitinib vs immunotherapy.
This suggests TOP2A-EPAS1 is a **general prognostic marker** for metastatic
ccRCC regardless of treatment modality, not an ICI-specific biomarker.

Domain-expert critique "is the result confounded by treatment arm?" →
**Directly answered: No.**

## G2: AUPRC supplement (2026-04-23)

IMmotion150 (62% event rate): binary AUROC=0.581 is expected to be weak — this
is a high-event-rate setting. The appropriate primary metrics are C-index (0.601)
and Cox HR (1.36), already reported above. AUPRC=0.706 vs baseline 0.624 (lift
1.13x) — modest positive signal.

TCGA-KIRC (16% M1): AUROC=0.726, **AUPRC=0.321** vs baseline 0.156 (**lift 2.05x**).
At low prevalence, AUPRC demonstrates meaningful clinical discrimination.

## Reproduce

```bash
python data/build_immotion150.py
# → data/immotion150_ccrcc.csv (263 samples × 17 cols)

python src/phf3_immotion150_replay.py
# → results/.../immotion150_pfs/{verdict.json,km_median_split.png}
```
