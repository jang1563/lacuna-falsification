# Track A — Task Landscape Summary

**Run date:** 2026-04-22
**Scope:** four ccRCC classification tasks with the same 11-15-gene
HIF-axis / metabolism / normal-kidney panel; PySR unconstrained search
on the compute node; same pre-registered 5-test falsification gate
as the flagship Tier-1 / Tier-2 runs.

---

## Headline

**0 / ~100 candidates survive across four biologically meaningful
ccRCC tasks.** Each task is dominated by a different single gene, and
the compound-law ceiling for 11-gene PySR search is at or below the
best single-gene classifier in every case. Opus 4.7's pathway-grounded
ex-ante laws also fail, often *worse* than PySR's unconstrained
candidates on task 2 and 3 (survival, metastasis).

This generalizes the +0.029 ceiling observed on Tier-1 / Tier-2 to a
**+0.0 ceiling on survival** and a **−0.030 ceiling on metastasis**:
Track B (Gate Robustness) can now ask whether that ceiling is a
property of our gene panel, our gate, or ccRCC itself.

---

## Task matrix

| Task | n | Labels | Dominant gene (sign-inv AUC) | Gate pass? | Best law AUC (PySR) | Δ_baseline |
|---|---|---|---|---|---|---|
| Tumor vs Normal (Tier 1) | 609 | 537 / 72 | **CA9 = 0.965** | 0 / 26 | 0.995 | +0.029 |
| Stage I-II vs III-IV (Tier 2) | 534 | 328 / 206 | CUBN = 0.610 | 0 / 27 | 0.691 | +0.029 |
| 5-year Survival | 301 | 149 / 152 | CUBN = 0.696 | 0 / 29 | 0.696 | **+0.000** (best law ≡ CUBN) |
| Metastasis M0 vs M1 | 505 | 426 / 79 | MKI67 = 0.645 | 0 / 30 | 0.592 | **-0.030** (worse than MKI67) |

All four tasks used the same PySR config: 11 genes, niter=800,
populations=12, seeds={1, 2, 3}, maxsize=15, per-cohort z-score
standardisation. Falsification: two-sided permutation null, bootstrap
CI lower bound, sign-invariant best-single-feature baseline,
decoy-feature null; covariate-only confound omitted on survival /
metastasis because the surviving covariate (`batch_index`) has zero
variance after tumor-only filtering.

---

## Task-level observations

### Survival (5-year overall survival, n=301, balanced)

- Best PySR candidate: `0.5240662 - (x8 * 0.18470868)` i.e.
  `0.524 - 0.185 · CUBN`. This is literally a single-gene CUBN
  classifier with an affine dressing. AUROC 0.696 matches the
  single-gene AUROC to three decimals; `delta_baseline = +0.000`.
- Across 29 PySR candidates the top 11 all reduce to a monotone
  function of CUBN; the next cluster (AUC 0.65) uses CUBN combined
  with CA9 or PTGER3 but never adds incremental AUROC.
- Opus ex-ante pathway laws (CA9/VEGFA/AGXT etc.) perform **worse**
  than the best single gene (top AUC 0.569). This is the task where
  pathway knowledge helps least — survival in ccRCC is not directly
  read out by HIF-axis magnitude.

### Metastasis (M0 vs M1, n=505, 16% M1)

- Best PySR candidate AUC 0.592 on a heavily class-imbalanced task;
  MKI67 alone reaches 0.645.
- PySR's compound laws reuse `exp(x5 - x7) - x1` = `exp(ENO2 − ALB) −
  VEGFA`. Biologically interpretable (Warburg/angiogenesis vs
  liver-like baseline), but weaker than MKI67 alone.
- Opus ex-ante top AUC 0.631 (glycolysis_hypoxia family), still
  `delta_baseline = -0.013`. The Opus negative-control laws
  (housekeeping, proliferation) fail as expected.

### Tumor vs Normal (Tier 1) & Stage (Tier 2)

See `results/RESULTS.md` for the earlier analysis. Both tasks have
+0.029 incremental ceiling. CUBN turns out to be the operative single
gene for stage (0.610) as well as for survival (0.696), suggesting
that tubule-identity loss carries most of the prognostic information
in ccRCC.

---

## What the gate is actually doing

On every task, PySR converges on equations that are monotone
functions of the best single gene for that task:

- Tumor vs Normal → monotone in CA9
- Stage → monotone in CUBN
- Survival → monotone in CUBN
- Metastasis → exp/log wrappers around ENO2 / ALB / VEGFA combinations
  but never adds measurable AUROC over MKI67

The 5-test falsification gate catches this through `delta_baseline`:
the "compound law" is compared to the best single-feature classifier
with sign-invariant AUROC, and the compound must improve by at least
+0.05. **Not once in 100+ attempts does any law clear that bar** —
which is exactly the kind of discovery claim the gate was designed
to *reject*.

---

## Implications for the submission narrative

1. **Pre-registration bites on 4 tasks, not 1.** The 0-survivor
   result is not a quirk of tumor-vs-normal. It replicates on
   biologically distinct tasks (saturated classification, ordinal
   stage, prognostic survival, discrete metastasis), with different
   dominant genes each time.
2. **Opus ex-ante pathway laws fail too, for distinct reasons.**
   On tumor-vs-normal the pathway law AUROC was near 1.0 (saturated
   biology); on survival it was 0.569 (pathway signal is weaker than
   CUBN's tissue-identity signal). Same gate, different failure mode,
   same verdict.
3. **The artifact is the gate, not the survivor.** The most-defensible
   reading of this run is that pre-registered falsification correctly
   identifies *which task is already solved by one gene*, and refuses
   to call "wrapped CUBN" a discovery.
4. **Track B (Gate Robustness) is the natural next question.** If
   the +0.0 ceiling on survival holds up to threshold sensitivity and
   baseline-definition ablation, we can claim robustness; if it
   flips at +0.03, we learn the threshold was the binding constraint.

---

## Numerical artifacts

- `results/track_a_task_landscape/survival/candidates.json` — 29 PySR candidates on survival
- `results/track_a_task_landscape/survival/falsification_report.json` — 5-test gate output on PySR survival candidates
- `results/track_a_task_landscape/survival/opus_exante_report.json` — 5-test gate output on Opus ex-ante laws × survival cohort
- `results/track_a_task_landscape/metastasis/candidates.json` — 30 PySR candidates on metastasis
- `results/track_a_task_landscape/metastasis/falsification_report.json` — 5-test gate output on PySR metastasis candidates
- `results/track_a_task_landscape/metastasis/opus_exante_report.json` — 5-test gate output on Opus ex-ante laws × metastasis cohort

Data:
- `data/kirc_survival.csv` — 301 ccRCC tumor samples labelled by 5-year OS
- `data/kirc_metastasis.csv` — 505 ccRCC tumor samples labelled by M0/M1
