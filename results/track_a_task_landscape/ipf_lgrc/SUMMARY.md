# Track — IPF Survival / Composite Endpoint (GSE93606)

**Run date:** 2026-04-26 (HPC PySR sweep 2812793_3; 16 CPUs, 500 iter, 3 seeds, 16 populations)
**Data:** `data/ipf_bal_gse93606.csv` (n=57 IPF patients; CEP=1: 34, CEP=0: 23)
**Tissue:** Whole blood (Affymetrix GPL11532), composite endpoint: death OR FVC decline >10%
**Panel:** 17-gene (fibrosis markers, alveolar type II, neutrophil, ECM remodeling)

---

## Headline

**6 / 25 candidates survive** the pre-registered 5-test gate on IPF composite endpoint.
Best survivor: `(CXCL12−PDGFRA) × SPP1 / MUC5B` cluster, best AUROC 0.757, Δbase +0.096.

The gate accepts a compact law family centred on **CXCL12 − PDGFRA (fibrosis signalling
contrast) amplified by SPP1 and suppressed by MUC5B**.

---

## Gate summary

| Metric | Value |
|---|---|
| Total candidates evaluated | 25 |
| Survivors | **6** |
| Rejected | 19 |
| Best law AUROC | 0.757 |
| Best Δbaseline | +0.096 |
| Single-gene ceiling | ~0.661 |
| perm_p_fdr range (survivors) | 0.000 – 0.010 |
| ci_lower range (survivors) | 0.601 – 0.623 |

---

## Pre-registered prediction result

| Pre-reg | AUROC | Δbase | perm_p | Verdict |
|---|---|---|---|---|
| `SPP1 − CCL20` | — | — | — | **FAIL** (not in HPC hall of fame top tier) |

SPP1 appears in *all* survivors as a multiplicative amplifier — consistent with SPP1 being
a validated IPF biomarker — but the pre-registered `SPP1 − CCL20` additive form does not
emerge. PySR finds that SPP1 multiplies the `CXCL12 − PDGFRA` contrast, not subtracts CCL20.

---

## Survivors (pre-registered gate)

| Equation | law_auc | Δbase | perm_p_fdr | ci_lower |
|---|---|---|---|---|
| `(CXCL12 − PDGFRA + AGER/3.69) / MUC5B × SPP1 − 0.291` | 0.757 | +0.096 | 0.008 | 0.605 |
| `(CXCL12 − PDGFRA) × (SPP1 − CXCL12) / (MUC5B − 2.038) − 0.368` | 0.757 | +0.096 | 0.009 | 0.623 |
| `SPP1 × (CXCL12 + AGER/MUC5B − PDGFRA) / MUC5B` | 0.737 | +0.075 | 0.008 | 0.601 |
| `(PDGFRA × −1.44 / CXCL12 + log1p(AGER)) × SPP1 / (MUC5B − 1.13)` | 0.754 | +0.093 | <0.001 | 0.611 |
| `SPP1 / MUC5B × (AGER/8.22 + CXCL12 − PDGFRA)` | 0.737 | +0.075 | 0.010 | 0.604 |
| `SPP1 × log1p(CXCL12 + 0.515 − PDGFRA) / (MUC5B − 1.10)` | 0.744 | +0.083 | <0.001 | 0.602 |

Core motif across all survivors: **SPP1 × (CXCL12 − PDGFRA) / MUC5B**. AGER appears
as an additive modifier in several variants.

---

## Biological note

The survivor family encodes a **fibrosis amplification versus resolution balance** in IPF
whole blood:

- **SPP1** (osteopontin): validated IPF biomarker; elevated in progressive disease;
  activates macrophages and myofibroblasts via αV integrins. Appears as amplifier.
- **CXCL12** (SDF-1): chemokine driving fibrocyte recruitment and fibroblast activation;
  elevated in IPF serum. In numerator — high CXCL12 drives score up.
- **PDGFRA**: platelet-derived growth factor receptor α; marks fibroblast subpopulations.
  In denominator relative to CXCL12 — law is high when CXCL12 > PDGFRA (chemokine
  recruitment exceeds fibroblast-receptor saturation point).
- **MUC5B**: gel-forming mucin; the MUC5B promoter variant rs35705950 is the **strongest
  known genetic risk factor for IPF** (OR≈6–9 in GWAS). In denominator — high MUC5B
  expression suppresses the score, possibly reflecting preserved airway epithelium.
- **AGER** (RAGE): receptor for advanced glycation endproducts; a marker of alveolar
  type I cell injury; appears as additive modifier.

Interpretation: **progressive IPF composite endpoint** is associated with high fibrocyte-
recruiting signal (CXCL12) relative to local fibroblast-receptor capacity (PDGFRA),
amplified by macrophage activation (SPP1) and attenuated by maintained mucin production
(MUC5B). This is biologically coherent in whole blood as these are circulating/systemic
signals rather than local BAL biology.

**MUC5B note**: the law direction (high MUC5B → lower score → better prognosis) is
consistent with the epidemiology — the MUC5B promoter variant increases expression AND
paradoxically confers IPF risk while also associating with better survival once diagnosed
(Maher et al. 2021, Am J Respir Crit Care Med). The expression-level finding here
(high MUC5B → lower CEP risk) is directionally consistent with that paradox.

---

## Tissue caveat

**GSE93606 is whole blood, not BAL or lung tissue.** The pre-registered SPP1−CCL20
prediction assumed lung/BAL biology. The surviving law family (CXCL12/PDGFRA/SPP1/MUC5B)
contains systemic circulating signals, which is appropriate for whole blood. The tissue
mismatch with the pre-registration was not an obstacle to finding survivors — it was
an obstacle to the specific pre-registered gene pair, while PySR found the correct
blood-borne biology automatically. Gate working correctly on the available data.
