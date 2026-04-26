# Track — IPF Survival / Composite Endpoint (GSE93606)

**Run date:** 2026-04-26 (hand-constructed candidates; HPC sweep 2812785_3 pending)
**Data:** `data/ipf_bal_gse93606.csv` (n=57 IPF patients; CEP=1: 34, CEP=0: 23)
**Tissue:** Whole blood (Affymetrix GPL11532), composite endpoint: death OR FVC decline >10%
**Panel:** 17-gene (fibrosis markers, alveolar type II, neutrophil, ECM remodeling)
**PySR:** HPC job 2812785_3 running (16 CPUs, 500 iter, 3 seeds)

---

## Headline

**0 / 12 candidates survive** the pre-registered 5-test gate on IPF composite endpoint.
Best law: `KRT5 − AGER` (AUROC 0.646, Δbase −0.015).

All compound laws are **inferior to the best single gene** (AUROC 0.661 — likely MMP7 or SPP1).
This pattern is consistent with: (a) small n=57 limiting compound signal detection, and
(b) the tissue being whole blood, which attenuates fibrotic tissue-specific compound signatures.

**HPC job 2812785_3** running; results will update this file.

---

## Gate summary

| Metric | Value |
|---|---|
| Total candidates evaluated | 12 |
| Survivors | **0** |
| Rejected | 12 |
| Primary rejection reason | `delta_baseline` (12/12) + `ci_lower` (12/12) |
| Best law AUROC | 0.646 |
| Best Δbaseline | −0.015 (all negative — compounds worse than single gene) |
| Single-gene ceiling | 0.661 |

---

## Pre-registered prediction result

| Pre-reg | AUROC | Δbase | perm_p | Verdict |
|---|---|---|---|---|
| `SPP1 − CCL20` | 0.545 | −0.116 | 0.575 | **FAIL** (all tests) |

SPP1 (osteopontin) is a validated IPF biomarker in BAL fluid and lung tissue. However,
in whole blood (this cohort), SPP1 does not show the expected signal — the BAL/tissue
biology does not transfer to peripheral blood at this gene level. CCL20 (a chemokine)
similarly lacks the expected signal in whole blood.

---

## Tissue caveat

**GSE93606 is whole blood, not BAL or lung tissue.** The briefing specified "BAL fluid
microarray," but the actual series matrix shows `tissue: whole blood`. Fibrotic tissue
markers (SPP1, KRT17, KRT5, COL1A1, SFTPC) are expected to have attenuated signal in
peripheral blood vs. bronchoalveolar lavage. The 0-survivor result is consistent with
this tissue mismatch. A BAL or lung tissue cohort (e.g., GSE70867 if available) would
be the appropriate validation.

---

## Honest caveat

Candidates were hand-constructed (no PySR) due to local memory constraints. HPC sweep
(job 2812785_3) may find any compound signal present. However, the fundamental tissue
mismatch (whole blood vs. BAL) and small cohort size (n=57) are structural limitations.
The gate working correctly: rejecting all candidates on a cohort where the expected
biology is not measurable.
