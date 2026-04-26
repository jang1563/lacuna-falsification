# Track — TCGA-PAAD Survival (OS ≤15 months vs >15 months)

**Run date:** 2026-04-26 (local symbolic regression, seed 1; HPC sweep 2812785_1 pending)
**Data:** `data/paad_survival.csv` (n=183; short-OS=91, long-OS=92, median split ≈15.2 mo)
**Panel:** 19-gene (EMT, proliferation, TGF-β/SMAD, Warburg, stromal markers)
**PySR (initial):** 4 populations × 30 pop_size × 80 iterations × seed 1, local

---

## Headline

**0 / 13 candidates survive** the pre-registered 5-test gate on PAAD OS survival.
Best compound law: `log1p(23.37 / (exp(2.23) + SMAD4 × KRT17))` (AUROC 0.632, Δbase +0.004).

Gate rejects all candidates on `delta_baseline` — the best single gene (KRT17, AUROC 0.629)
already captures most survival signal, leaving < +0.05 incremental headroom for any compound.

**HPC job 2812785_1** (16 CPUs, 500 iter, 3 seeds) is running; results will update this file.

---

## Gate summary

| Metric | Value |
|---|---|
| Total candidates evaluated | 13 |
| Survivors | **0** |
| Rejected | 13 |
| Primary rejection reason | `delta_baseline` (13/13) + `ci_lower` (13/13) |
| Best law AUROC | 0.632 |
| Best Δbaseline | +0.004 |
| Single-gene ceiling (KRT17) | 0.629 |

---

## Pre-registered prediction result

| Pre-reg | AUROC | Δbase | perm_p | Verdict |
|---|---|---|---|---|
| `GATA6 − VIM` | 0.563 | −0.066 | 0.148 | **FAIL** (delta_baseline, perm_p, ci_lower) |

GATA6 is a pancreatic lineage transcription factor; VIM is an EMT marker. Neither
clears the compound threshold here — VIM alone (negative orientation, sign-invariant AUROC ≈0.63)
largely subsumes the signal.

---

## Best candidates (gate-evaluated)

| Equation | AUROC | Δbase | perm_p | ci_lower |
|---|---|---|---|---|
| `log1p(23.37 / (exp(2.23) + SMAD4 × KRT17))` | 0.632 | +0.004 | 0.003 | 0.556 |
| `1.2021 / sqrt(KRT17)` | 0.629 | +0.000 | 0.002 | 0.555 |
| `sqrt(log1p(2.047 / KRT17))` | 0.629 | +0.000 | 0.002 | 0.546 |

All candidates fail `delta_baseline` (threshold: >0.05) and `ci_lower` (threshold: >0.6).

---

## Biological note

KRT17 (Keratin 17) dominates PAAD survival signal on this cohort — consistent with its
role as a basal/squamous PAAD subtype marker associated with worse prognosis. The SMAD4×KRT17
compound (Δ=+0.004) adds marginal signal from TGF-β pathway loss, which is expected in ~55%
of PAAD tumors, but not sufficient to clear the +0.05 gate threshold on n=183.

---

## Honest caveat

This run used only seed 1 (80 iterations) due to local memory constraints. A fuller sweep
(HPC, 500 iter × 3 seeds) is in progress. The 0-survivor result is consistent with a high
single-gene ceiling (KRT17 ≈ 0.629) that leaves limited incremental headroom for compound laws
on the current 19-gene panel. An expanded panel including KRAS pathway markers or PDAC
subtype genes may reveal compound signal.
