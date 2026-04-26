# Track A — Task Landscape Summary

**Run date:** 2026-04-22; platform expansion appended 2026-04-26.
**Scope:** original four ccRCC classification tasks plus the
2026-04-26 expanded-panel/platform runs. All use PySR unconstrained
search and the same pre-registered 5-test falsification gate as the
flagship Tier-1 / Tier-2 runs.

---

## Headline (updated 2026-04-26 after platform expansion)

With the **45-gene expanded HIF/Warburg/tubule/proliferation/metastasis
panel**, the falsification gate emits **its first survivors**: 9 /30
candidates on the metastasis M0 vs M1 task, led by a 2-gene law
`TOP2A − EPAS1` (proliferation minus HIF-2α) with AUROC 0.726 and
delta_baseline +0.069 against the best single-gene baseline
(MKI67 = 0.645). This reproduces the published ccRCC "ccA / ccB
subtype" axis (aggressive proliferative-dedifferentiated tumors vs
hypoxic-differentiated tumors) entirely from unconstrained symbolic
regression + pre-registered falsification — *not* from a priori
template injection.

The broader picture now holds in two layers:

- **With the original 11-gene HIF-axis + normal-kidney panel,** the
  gate rejects 0 / 100+ candidates across four tasks. Each task is
  dominated by a different single gene and the compound-law ceiling
  stays below the pre-registered +0.05 threshold: CA9 for
  tumor/normal, CUBN for stage and survival, MKI67 for metastasis.
- **With the 45-gene expanded panel,** the ceiling lifts to +0.069 on
  metastasis (9 passing laws, most reading as proliferation-over-
  hypoxia). The 2026-04-26 KIRC stage rerun also produces **23 / 28**
  survivors on a 45-gene panel, led by `CXCR4 / EPAS1`. Survival
  remains below threshold (0 / 29, best Δbaseline +0.019), while
  tumor-vs-normal remains the designed single-gene-saturation case.

This gives the artifact two complementary outcomes on the same
infrastructure: (a) negative examples where pre-registration bites
and rejects textbook biology alike; (b) a positive example where a
cleanly two-gene, biologically legible law passes the gate and
replays published ccRCC biology. Track B (Gate Robustness) can now
test whether the +0.069 metastasis survivor is robust to
threshold / baseline-definition / scaling perturbations.

---

## Task matrix

Two gene-panel sizes reported side-by-side — the 11-gene HIF-axis
panel (original Tier-1 / Tier-2 / A4 config) and the 45-gene
expanded panel (Option A6 plus the 2026-04-26 stage rerun). Expanded
reruns can differ slightly in n after clinical filtering and are
noted inline.

| Task | n | Labels | Dominant gene (sign-inv AUC) | 11-gene gate | 11-gene best Δbase | 45-gene gate | 45-gene best Δbase |
|---|---|---|---|---|---|---|---|
| Tumor vs Normal (Tier 1) | 609 | 537 / 72 | **CA9 = 0.965** | 0 / 26 | +0.029 | not rerun | — |
| Stage I-II vs III-IV (Tier 2) | 534 | 328 / 206 | CUBN = 0.610 | 0 / 27 | +0.029 | **23 / 28** (n=512) | **+0.092** ✅ |
| 5-year Survival | 301 | 149 / 152 | CUBN = 0.696 | 0 / 29 | +0.000 (best ≡ CUBN) | **0 / 29** | **+0.019** (still fails) |
| Metastasis M0 vs M1 | 505 | 426 / 79 | MKI67 = 0.645 | 0 / 30 | −0.030 | **9 / 30** | **+0.069** ✅ |

All runs: PySR unconstrained search (iter=600–800, populations=10–12,
seeds={1,2,3}, maxsize=15), per-cohort z-score standardisation,
pre-registered 5-test gate (two-sided permutation null, bootstrap CI
lower bound > 0.6, sign-invariant best-single-feature baseline
Δ > 0.05, incremental-covariate confound Δ > 0.03 when covariates
available, decoy-feature null p < 0.05), BH-FDR across candidates.

The original 2026-04-22 ccRCC tasks used the same PySR config: 11 genes,
niter=800, populations=12, seeds={1, 2, 3}, maxsize=15, per-cohort
z-score standardisation. Falsification: two-sided permutation null,
bootstrap CI lower bound, sign-invariant best-single-feature baseline,
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
+0.05. **In the original 11-gene layer, not once in 100+ attempts does
any law clear that bar** — exactly the kind of discovery claim the gate
was designed to *reject*. The expanded-panel/platform rows are the
paired positive control: when the single-gene ceiling is lower and the
panel contains distributed biology, the same bar admits survivors.

---

## Implications for the submission narrative

1. **Pre-registration bites on the original 4-task layer, not 1.** The
   0-survivor result is not a quirk of tumor-vs-normal. It replicates
   across biologically distinct 11-gene tasks (saturated
   classification, ordinal stage, prognostic survival, discrete
   metastasis), with different dominant genes each time.
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

## The metastasis survivors in detail (Option A6)

Nine PySR candidates cleared the full 5-test gate on the metastasis
task with the 45-gene panel. They cluster into three biologically
distinct shapes:

**Cluster 1 — `TOP2A − EPAS1` (proliferation − HIF-2α)** — 5 laws at
AUROC 0.726. The simplest member:

    0.0986 * (TOP2A − EPAS1) + 0.161         (AUROC 0.726, ci_lower 0.658)

plus four monotone rewrites (`log1p(log1p(exp(TOP2A − EPAS1)) * k)`
etc.) that collapse to the same score ranking.

**Cluster 2 — `MKI67 − EPAS1`** — 2 laws at AUROC 0.708 with
`delta_baseline = +0.051`. Same axis as Cluster 1 but uses MKI67
(proliferation-marker canonical) instead of TOP2A (proliferation-
marker enzymatic).

**Cluster 3 — 5-gene compound** — 2 laws at AUROC 0.726, using
`MKI67 - exp(((EPAS1 - PTGER3) + LRP2) - RPL13A)` style
structure. This wraps the proliferation / HIF-2α core with
normal-kidney markers (LRP2, PTGER3) and a housekeeping reference
(RPL13A). Same AUROC as the 2-gene Cluster 1 laws, so the extra
genes are not adding discriminative value; the 2-gene form is
preferred by parsimony.

### Why this is biologically legible

EPAS1 is HIF-2α, the dominant hypoxia-response transcription factor
in well-differentiated ccRCC. TOP2A and MKI67 are canonical
proliferation markers. The ratio *`proliferation > hypoxia-
differentiation`* reproduces the published ClearCode34 / ccA-vs-ccB
subtype axis: aggressive, proliferative, less HIF-2α-driven tumors
are more likely to be metastatic (M1). The unconstrained symbolic
search found this axis *without* being seeded with it, and the
pre-registered gate accepted it only because its incremental AUROC
over MKI67 alone is +0.069 — comfortably above the +0.05 threshold.

At the time of the 2026-04-22 Track-A run, this was the first candidate
in the pipeline (across 150+ candidates and six task/panel combinations)
that survived every falsification test. The 2026-04-26 platform
expansion later added KIRC stage, COAD, and LGG survivors under the same
gate. Track B (Gate Robustness) should specifically stress-test this
survivor under threshold / baseline-definition / scaling perturbations
before we over-commit to the narrative.

## Numerical artifacts

### Original 11-gene panel (A4–A5)

- `results/track_a_task_landscape/survival/candidates.json` — 29 PySR candidates on survival
- `results/track_a_task_landscape/survival/candidates_named.json` — same, with xi → gene name substitution
- `results/track_a_task_landscape/survival/falsification_report.json` — 5-test gate output on PySR survival candidates
- `results/track_a_task_landscape/survival/opus_exante_report.json` — 5-test gate output on Opus ex-ante laws × survival cohort
- `results/track_a_task_landscape/metastasis/candidates.json` — 30 PySR candidates on metastasis
- `results/track_a_task_landscape/metastasis/candidates_named.json` — same, renamed
- `results/track_a_task_landscape/metastasis/falsification_report.json` — 5-test gate output on PySR metastasis candidates
- `results/track_a_task_landscape/metastasis/opus_exante_report.json` — 5-test gate output on Opus ex-ante laws × metastasis cohort

### Expanded 45-gene panel (A6)

- `results/track_a_task_landscape/survival_expanded/candidates.json`
- `results/track_a_task_landscape/survival_expanded/candidates_named.json`
- `results/track_a_task_landscape/survival_expanded/falsification_report.json` — 0 / 29 survivors, best law `TOP2A − CUBN − PCNA` at AUROC 0.715 / Δbase +0.019
- `results/track_a_task_landscape/metastasis_expanded/candidates.json`
- `results/track_a_task_landscape/metastasis_expanded/candidates_named.json`
- `results/track_a_task_landscape/metastasis_expanded/falsification_report.json` — **9 / 30 survivors**, proliferation-over-HIF-2α family

### Data

- `data/kirc_survival.csv` — 301 ccRCC tumor samples, 11-gene panel, 5-yr OS labels
- `data/kirc_metastasis.csv` — 505 ccRCC tumor samples, 11-gene panel, M0/M1 labels
- `data/kirc_survival_expanded.csv` — same 301 samples, 45-gene panel
- `data/kirc_metastasis_expanded.csv` — same 505 samples, 45-gene panel
- `data/build_tcga_kirc_expanded.py` — re-extracts the 45 Ensembl IDs from the cached `TCGA-KIRC.star_tpm.tsv.gz`

### Plots

- `results/track_a_task_landscape/plots/task_auroc_comparison.png` — 11-gene panel cross-task AUROC scatter
- `results/track_a_task_landscape/plots/delta_baseline_by_task.png` — 11-gene panel Δbaseline histogram

---

## Platform generalization (2026-04-26 HPC expansion)

Same pre-registered gate extended to 3 additional cancer types. All runs use conda env `lacuna-pysr`
on HPC (20 CPUs): 20 populations × 50 pop_size × 1000 iterations × 3 seeds.

| Cancer | Task | Panel | n | Top law | AUROC | Δbase | Survivors |
|---|---|---|---|---|---|---|---|
| KIRC | Stage I-II vs III-IV | 45-gene | 512 | `CXCR4/EPAS1` | 0.689 | +0.051 | **23/28** ✅ |
| LIHC | Tumor vs Normal | 31-gene | 424 | — (ALB/TTR ~0.985) | — | +0.015 | **0/26** |
| COAD | Stage I-II vs III-IV | 31-gene | 484 | `SLC2A1+PDCD1LG2+VIM−MYC` | 0.658 | +0.107 | **15/22** ✅ |
| LGG | Grade II vs III | 30-gene | 384 | `log1p(TWIST1×MKI67+VIM)−CDH2/NES` | 0.840 | +0.051 | **2/25** ✅ |

**Pattern:** Gate accepts survivors when the feature landscape is distributed (moderate single-gene ceiling).
Gate refuses when one gene saturates (LIHC: hepatic function marker, same as ccRCC CA9 pattern).
Gate finds sparse survivors when ceiling is high but not absolute (LGG: MKI67 ~0.789 est.).

Subdirectories: `stage_expanded/`, `lihc/`, `coad_msi/`, `gbm_idh/` — each with `SUMMARY.md`.

(An expanded-panel cross-comparison plot is a natural next addition.)

---

## New disease tracks (2026-04-26 discovery session)

Three new datasets built and falsification-tested. HPC sweep (SLURM 2812785) running for
fuller PySR candidates; results below reflect hand-constructed / seed-1 candidates.

| Cancer | Task | Panel | n | Pre-reg law | Pre-reg AUROC | Δbase | Survivors (initial) | Notes |
|---|---|---|---|---|---|---|---|---|
| PAAD | OS ≤15mo vs >15mo | 19-gene | 183 | `GATA6−VIM` | 0.563 | −0.066 | **0/13** | KRT17 ceiling 0.629; SMAD4+KRT17 best (Δ+0.004) |
| LIHC | MVI Micro vs None | 19-gene | 144 | `EPCAM+CDK1` | 0.556 | −0.070 | **0/12** | CDK1 ceiling ~0.626; CDK1/SNAI1 best (Δ+0.014) |
| IPF | CEP (death/FVC>10%) | 17-gene | 57 | `SPP1−CCL20` | 0.545 | −0.116 | **0/12** | Whole blood (not BAL); single-gene ceiling 0.661 |
| DIPG | H3K27M vs WT | — | — | `OLIG2−UQCRC1` | — | — | **NOT RUN** | Data acquisition failed (OpenPedCan S3 404) |

**Pre-reg predictions all fail on initial candidate set.** Three independent reasons:
- PAAD: KRT17 captures most OS signal alone (>GATA6 additive contribution)
- LIHC MVI: n=144 + 28% prevalence → bootstrap CI lower bounds constrained; EPCAM+CDK1 Δ negative
- IPF: Tissue mismatch (whole blood not BAL); all compounds weaker than best single gene

HPC sweep 2812785 (16 CPUs × 500 iter × 3 seeds per task) may find compound laws that clear
the gate. Will update SUMMARY.md in each task directory when results arrive.

Subdirectories: `paad_survival/`, `lihc_mvi/`, `ipf_lgrc/`, `dipg/` — each with `SUMMARY.md`.
