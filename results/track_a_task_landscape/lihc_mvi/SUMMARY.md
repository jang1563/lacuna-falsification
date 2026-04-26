# Track — TCGA-LIHC Microvascular Invasion

**Run date:** 2026-04-26 (hand-constructed candidates; HPC sweep 2812785_2 pending)
**Data:** `data/lihc_mvi.csv` (n=144; MVI present=41, MVI absent=103)
**Panel:** 19-gene (proliferation, stemness/EpCAM, EMT, HIF/hypoxia, HCC markers)
**PySR:** HPC job 2812785_2 running (16 CPUs, 500 iter, 3 seeds)

---

## Headline

**0 / 12 candidates survive** the pre-registered 5-test gate on LIHC MVI (Micro vs None).
Best compound: `log1p(log1p(CDK1 × 0.198 / SNAI1))` (AUROC 0.640, Δbase +0.014).

Gate rejects all on `delta_baseline` — single-gene ceiling (CDK1, AUROC ~0.626) dominates.
28% MVI prevalence (41/144) constrains bootstrap CI lower bounds.

**HPC job 2812785_2** running; results will update this file.

---

## Gate summary

| Metric | Value |
|---|---|
| Total candidates evaluated | 12 |
| Survivors | **0** |
| Rejected | 12 |
| Primary rejection reason | `delta_baseline` (12/12) + `ci_lower` (12/12) |
| Best law AUROC | 0.640 |
| Best Δbaseline | +0.014 |
| Single-gene ceiling (CDK1) | ~0.626 |

---

## Pre-registered prediction result

| Pre-reg | AUROC | Δbase | perm_p | Verdict |
|---|---|---|---|---|
| `EPCAM + CDK1` | 0.556 | −0.070 | 0.294 | **FAIL** (delta_baseline, perm_p, ci_lower) |
| `EPCAM × CDK1` | 0.502 | −0.124 | 0.983 | **FAIL** (all tests) |

EpCAM (EPCAM) is a key MVI marker in published literature (AFP/EpCAM double-positive HCC),
but it does not add to CDK1 on this cohort — CDK1 alone (proliferation) captures most
MVI-associated signal. This may reflect that the published EpCAM MVI association is strongest
in small n studies; at n=144 the compound advantage does not clear +0.05.

---

## Best candidates (gate-evaluated)

| Equation | AUROC | Δbase | perm_p | ci_lower |
|---|---|---|---|---|
| `log1p(log1p(CDK1 × 0.198 / SNAI1))` | 0.640 | +0.014 | 0.009 | 0.529 |
| `CDK1 − SNAI1` | 0.627 | +0.001 | 0.020 | 0.519 |
| `PCNA × 0.041` | 0.500 | −0.126 | 0.125 | 0.507 |

---

## Biological note

CDK1/SNAI1 compound (`CDK1 − SNAI1` and log-form) suggests **proliferation offset by EMT**
as a partial MVI discriminant. CDK1 is a G2/M kinase upregulated in proliferating tumors;
SNAI1 (Snail) drives EMT. Their ratio may capture tumors that are proliferating without
full EMT engagement — a partial MVI phenotype. However, Δ=+0.014 is well below the +0.05
gate threshold, indicating the signal is modest on n=144.

---

## Honest caveat

Candidates were hand-constructed (no PySR) due to local memory constraints. The HPC sweep
(job 2812785_2, 500 iter × 3 seeds) may find compound laws that clear the gate. The 28%
MVI prevalence (41/144) limits bootstrap CI lower bounds — small imbalanced cohorts
are structurally harder to pass the `ci_lower > 0.6` criterion.
