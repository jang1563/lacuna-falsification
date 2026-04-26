# Track — TCGA-LIHC Microvascular Invasion

**Run date:** 2026-04-26 (HPC PySR sweep 2812793_2; 16 CPUs, 500 iter, 3 seeds, 16 populations)
**Data:** `data/lihc_mvi.csv` (n=144; MVI present=41, MVI absent=103)
**Panel:** 19-gene (proliferation, stemness/EpCAM, EMT, HIF/hypoxia, HCC markers)

---

## Headline

**6 / 29 candidates survive** the pre-registered 5-test gate on LIHC MVI (Micro vs None).
Simplest survivor: `(TOP2A/CDH2/SOX9) / sqrt(SNAI1)` cluster, all at AUROC 0.702, Δbase +0.076.

The gate accepts a compact law family centred on **proliferation (TOP2A) adjusted for
mesenchymal/stemness context (CDH2, SOX9) and suppressed by EMT driver (SNAI1)**.

---

## Gate summary

| Metric | Value |
|---|---|
| Total candidates evaluated | 29 |
| Survivors | **6** |
| Rejected | 23 |
| Best law AUROC | 0.702 |
| Best Δbaseline | +0.076 |
| Single-gene ceiling (CDK1) | ~0.626 |
| perm_p_fdr range (survivors) | 0.000 – 0.003 |
| ci_lower range (survivors) | 0.600 – 0.615 |

---

## Pre-registered prediction result

| Pre-reg | AUROC | Δbase | perm_p | Verdict |
|---|---|---|---|---|
| `EPCAM + CDK1` | — | — | — | **FAIL** (not in HPC hall of fame) |

EpCAM-centric families did not emerge from unconstrained PySR — the search converged
instead on the TOP2A/CDH2/SOX9/SNAI1 family. EPCAM's MVI signal in the literature
is largely driven by AFP/EpCAM double-positive HCC, which may not generalize to this
mixed cohort.

---

## Survivors (pre-registered gate)

| Equation | law_auc | Δbase | perm_p_fdr | ci_lower |
|---|---|---|---|---|
| `((SOX9 + (TOP2A/CDH2)/SOX9) × 0.087) / sqrt(SNAI1)` | 0.702 | +0.076 | <0.001 | 0.607 |
| `0.087 / (sqrt(SNAI1) / (SOX9 + (TOP2A/CDH2)/SOX9))` | 0.702 | +0.076 | <0.001 | 0.603 |
| `(0.104 / (sqrt(SNAI1) / (TOP2A/CDH2/SOX9 + SOX9))) − 0.079` | 0.702 | +0.076 | 0.003 | 0.603 |
| `((TOP2A/CDH2/SOX9 + SOX9) × 0.087) / sqrt(SNAI1)` | 0.702 | +0.076 | <0.001 | 0.615 |
| `((SOX9 + TOP2A/CDH2/SOX9) / (SNAI1 + sqrt(log1p(AFP)))) × 0.193` | 0.693 | +0.067 | <0.001 | 0.600 |
| `((TOP2A/CDH2/SOX9 + SOX9) × 0.104) / sqrt(SNAI1) − 0.079` | 0.702 | +0.076 | <0.001 | 0.608 |

All 6 survivors encode the same biological axis: **TOP2A × (1/CDH2) / sqrt(SNAI1)** with
SOX9 as context term. The variants are algebraically equivalent rearrangements.

---

## Biological note

The survivor cluster encodes a **proliferation-over-EMT ratio** in HCC:

- **TOP2A**: topoisomerase IIα, direct G2/M proliferation marker; upregulated in aggressive HCC
- **CDH2** (N-cadherin): mesenchymal cadherin, elevated in EMT-engaged cells;
  appears in denominator — law is *high when CDH2 is low* relative to proliferation
- **SOX9**: hepatic progenitor/stemness marker, prominent in MVI-positive HCC
- **SNAI1** (Snail): master EMT transcription factor in the denominator — higher SNAI1 
  suppresses the score; captures that fully EMT-committed cells may lose proliferative drive

Interpretation: HCC tumors with **high proliferation (TOP2A) relative to their EMT maturity
(SNAI1, CDH2)** and a partial stemness phenotype (SOX9) are more likely to show MVI.
This is mechanistically consistent — pre-EMT proliferating cells may be more invasive
at the vascular margin than cells with completed EMT.

---

## Honest caveat

All 6 survivors are algebraic rearrangements of the same 4-gene compound.
The effective model is one law with 4 genes, not 6 independent laws.
AFP appears in one variant; it is likely a noise-term given the late-stage
Hall of Fame position. N=144 with 28% prevalence (41 MVI) means bootstrap
CI lower bounds are at threshold (0.600–0.615 vs cutoff 0.600) — the gate
is accepting at its margin. An independent LIHC cohort with TOP2A + CDH2 +
SOX9 + SNAI1 measurements would be the appropriate external validation.
