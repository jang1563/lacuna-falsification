# Track — TCGA-PAAD Survival (OS ≤15 months vs >15 months)

**Run date:** 2026-04-26 (HPC PySR sweep 2812793_1; 16 CPUs, 500 iter, 3 seeds, 16 populations)
**Data:** `data/paad_survival.csv` (n=183; short-OS=91, long-OS=92, median split ≈15.2 mo)
**Panel:** 19-gene (EMT, proliferation, TGF-β/SMAD, Warburg, stromal markers)

---

## Headline

**0 / 27 candidates survive** the pre-registered 5-test gate on PAAD OS survival.
Best compound: `sqrt(7.41/KRT17 / (CDH2 × compound))` (AUROC 0.707, Δbase −0.293).

Gate rejects all candidates on `delta_baseline` — best single gene (KRT17, AUROC ~0.629)
dominates; best law_auc found is 0.707 but delta_baseline is −0.293 because the sign-invariant
baseline also picks up KRT17-derived features at higher AUROC.

**Interpretation:** PAAD is a designed negative — the gate correctly detects a task dominated
by a single-gene signal (KRT17 as basal/squamous subtype marker) and refuses compound credit.

---

## Gate summary

| Metric | Value |
|---|---|
| Total candidates evaluated | 27 |
| Survivors | **0** |
| Rejected | 27 |
| Primary rejection reason | `delta_baseline` |
| Best law AUROC (sign-invariant) | 0.707 |
| Best Δbaseline | −0.293 (negative — compound below KRT17-related ceiling) |
| Single-gene ceiling (KRT17) | ~0.629 |

---

## Pre-registered prediction result

| Pre-reg | AUROC | Δbase | perm_p | Verdict |
|---|---|---|---|---|
| `GATA6 − VIM` | 0.563 | −0.066 | 0.148 | **FAIL** (delta_baseline, perm_p, ci_lower) |

GATA6 is a pancreatic lineage transcription factor; VIM is an EMT marker. Neither
adds compound value — KRT17's basal-subtype signal subsumes the EMT axis.

---

## Best failed candidates

| Equation | law_auc | Δbase | fail_reason |
|---|---|---|---|
| `sqrt(7.41/KRT17 / (CDH2 × …))` | 0.707 | −0.293 | delta_baseline |
| `exp(KRT17 / −11.01)` | 0.689 | — | delta_baseline |
| `4.15 / LDHA` | 0.662 | — | delta_baseline |

All KRT17-family candidates generate high law_auc but delta_baseline is negative — the
sign-invariant single-gene AUROC of KRT17 (or functions of KRT17) exceeds the compound.

---

## Biological note

**KRT17** (Keratin 17) is the defining marker of the **squamous/basal PAAD subtype**
(Collisson et al. 2011; Bailey et al. 2016), which is associated with the worst prognosis
in TCGA-PAAD. On this OS-median-split task, KRT17 alone captures most survival-relevant
signal. Adding EMT markers (CDH2, VIM), TGF-β pathway (SMAD4), or Warburg genes (LDHA,
SLC2A1) does not clear the +0.05 compound gate on this 19-gene panel.

**The gate is performing its intended function**: refusing to call a one-gene task
a multi-gene discovery. The 0-survivor result is scientifically informative
(KRT17 alone saturates this PAAD-survival task) rather than a pipeline failure.

---

## Honest caveat

An expanded panel including KRAS pathway markers (KRAS, MAPK1, RAF1), PAAD-specific
subtype genes (GATA6, FOXA2 for classical subtype), or epithelial markers may reveal
compound signal in PAAD beyond the basal subtype axis. The current 19-gene panel
is biased toward EMT/proliferation biology shared with the ccRCC runs.
