# I3 Clinical-utility translation — TOP2A − EPAS1

**Pre-registration:** `preregistrations/20260425T190301Z_i3_clinical_utility.yaml`
(`gate_logic_changed: false`, `extension_type: clinical_translation`)

## Question

How does the AUROC 0.7275 / AUPRC 0.321 survivor read in clinical
language? Cohen's d, odds ratio, and the threshold-based screening
profile translate the math into terms a clinician or domain reviewer
can interpret without re-deriving the underlying classifier.

## Headline numbers

| Metric | Value | 95% CI | Reference |
|---|---|---|---|
| **Cohen's d** (effect size from AUROC) | **0.856** | — | Cohen 1988: small=0.2, medium=0.5, large=0.8 → **medium-large** |
| **Odds ratio** per 1-SD increase in `TOP2A − EPAS1` | **2.07** | 1.65–2.59 | per logistic regression on z-scored score |
| AUROC (sign-invariant) | 0.7275 | — | matches `rigor_extension/` JSON |

Each 1-SD increase in `TOP2A − EPAS1` more than **doubles the
odds** of metastasis, with a 95% CI that excludes 1.0 by a wide
margin.

## Threshold-based screening profile

Two clinically interesting cutoffs, with the score oriented so
high values indicate higher M1 risk:

| Cutoff | Flagged (of 505) | Sensitivity | Specificity | PPV | NPV | NNS |
|---|---|---|---|---|---|---|
| **Top decile** (top 10% of scores) | 51 | **0.241** | **0.925** | 0.373 | 0.868 | **2.68** |
| **Top quintile** (top 20%) | 101 | **0.456** | **0.847** | 0.356 | 0.894 | **2.81** |

**NNS** = number needed to screen (1 / PPV) ≈ 2.7, meaning roughly
1 in every 2-3 patients flagged at the top-quintile cutoff would
actually be M1, against a base rate of ~1 in 6.4 (16% prevalence) —
a **~2.2× enrichment** over uninformed selection.

## Pre-registered prediction verdicts

| Prediction | Threshold | Outcome | Status |
|---|---|---|---|
| **P1** Cohen's d > 0.7 | 0.7 | **0.856** | ✅ PASS |
| **P2** OR per 1-SD ≥ 2.0 | 2.0 | **2.07** (CI 1.65–2.59) | ✅ PASS |
| **P3** Top-quintile sensitivity ≥ 0.50 AND specificity ≥ 0.85 | both | sens **0.456**, spec 0.847 | ❌ FAIL |

P3 fails on **sensitivity** by 0.044 (and on specificity by 0.003).
Honest read: at the top-quintile cutoff the score captures **46%
of M1 cases** at 85% specificity — useful for risk stratification
in a multi-marker clinical workflow but **not sufficient as a
standalone screening tool** at this cutoff.

## What the FAIL on P3 means in narrative terms

The pre-registered P3 was a deliberately stretch screening claim
(50% sensitivity at the top-quintile cutoff). It does not pass.
The result moves the headline framing from *"strong standalone
screening signal"* to *"strong risk-stratification signal that
contributes to a multi-marker decision but is not a one-gene-pair
screening test"*. Both the OR (2.07 per 1-SD) and the medium-large
Cohen's d remain valid; only the absolute sensitivity / specificity
combination at this particular cutoff misses by margin.

This is the falsification framework biting on the I-phase
clinical translation: a pre-registered claim can fail and the
correct response is to reframe accuracy of phrasing, not to move
the threshold.

## Comparison to published ccRCC signatures

For context, ClearCode34 (Brooks et al. 2014, DOI
10.1016/j.eururo.2014.02.035) — the published 34-gene ccA/ccB
classifier — reaches comparable AUROC (~0.72-0.75) on overlapping
cohort definitions but uses 34 genes. The 2-gene `TOP2A − EPAS1`
form trades a small-margin AUROC parity for **dramatic
operational simplicity**: two RT-qPCR assays vs a 34-probe
NanoString panel. That is the specific clinical-translation
contribution of the survivor: same axis, far smaller marker
panel, identical pre-registered statistical guarantees.

## Reproducibility

- Source: `src/track_a_clinical_utility.py`
- JSON: `clinical_metrics.json`
- Pre-reg: `preregistrations/20260425T190301Z_i3_clinical_utility.yaml`

## Citations

- Hanley & McNeil (1982). *The meaning and use of the AUROC*. Radiology 143:29-36.
- Pencina et al. (2008). *Evaluating the added predictive ability of a new marker*. Stat Med 27:157-172.
- Cohen J. (1988). *Statistical Power Analysis for the Behavioral Sciences*, 2nd ed.
- Vickers & Elkin (2006). *Decision curve analysis*. Med Decis Making 26:565-574.
- Brooks et al. (2014). ClearCode34. DOI 10.1016/j.eururo.2014.02.035.
