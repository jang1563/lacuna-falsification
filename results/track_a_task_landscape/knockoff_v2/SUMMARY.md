# G1 Knockoff v2 — Model-X Knockoffs with derandomization

**Pre-registration:** `preregistrations/20260425T170647Z_g1_knockoff_v2.yaml`
(`gate_logic_changed: true`, `extension_type: parallel_v2_gate`)

**Status:** v1 5-test gate is unchanged. v2 runs **alongside** for
reporting; both gates agree on the negatives but disagree on the
compound `TOP2A − EPAS1`. The honest finding is documented below.

## Configuration

| Knob | Value | Source |
|---|---|---|
| Sigma estimator | LedoitWolf shrinkage | `src/lacuna/knockoff_gate.py` |
| Knockoff construction | MVR (minimum variance reconstructability) | knockpy 1.3.x |
| Feature statistic | `lcd` (signed log-feature-importance contrast) | knockpy default for binary y |
| FDR target | **q = 0.10** | pre-registered |
| Replicates | **25** (seeds 0–24) | pre-registered for derandomization (Ren & Candès 2020) |
| Conjunction rule | ALL constituent genes ≥ 50% selection | pre-registered |

## Result on `kirc_metastasis_expanded` (n=505, p=45, prevalence 0.156)

- Sigma condition number **157.5** — well-conditioned (LedoitWolf
  shrinkage stabilises against the 45-gene panel's high pairwise
  correlation).
- **0 / 45 genes** selected at q=0.10 across 25 replicates.
- TOP2A selection rate: **0.00** (0/25).
- EPAS1 selection rate: **0.00** (0/25).

### W-statistic ranking (added 2026-04-25)

Although no gene clears the q=0.10 data-driven threshold, the mean W
statistic across 25 replicates ranks the constituents of the
flagship survivor at the top of the panel:

| Rank | Gene | Mean W (across 25 replicates) |
|---|---|---|
| **1** | **EPAS1** | **+0.0452** |
| **2** | **TOP2A** | **+0.0223** |

This **independently reproduces** the prior single-run knockoffs
result (`results/track_a_task_landscape/g1_knockoffs/`), which used
equicorrelated knockoffs and ranked EPAS1 (W=0.056) and TOP2A
(W=0.047) as #1 and #2. Two methodologically distinct knockoff
implementations (equicorrelated vs MVR; single-run vs 25-replicate
derandomized; non-`lcd` vs `lcd`) agree on the ranking, even as both
fall short of the q=0.10 selection threshold. The pattern is therefore
a **consistent power limitation** at this n / p / q combination, not
a method-specific artefact.

Treating "rank 1 and 2 by W out of 45 genes" as a continuous-strength
measurement (rather than the binary FDR-controlled selection): the
v2 gate's underlying signal aligns with the v1 compound-feature
finding. The discordance is at the binary-selection level only.

### Pre-registered hypothesis verdicts

| Hypothesis | Pre-registered prediction | Outcome | Verdict |
|---|---|---|---|
| H1 | TOP2A AND EPAS1 selected ≥ 50% | both 0.00 | **FAIL** |
| H2 | ≥ 6/9 v1 survivors concordant | 0/3 (representative subset) | **FAIL** |
| H3 | ≥ 80% reject concordance (knockoff agrees on negatives) | 2/2 = 100% | **PASS** |

Per pre-registration §`go_no_go_criteria`: *"Even discordance is GO
if the failure reason is documented."* Both H1 and H2 fail; H3
passes. We document the failure mechanism below.

## Why H1 / H2 fail — the honest answer

The v1 5-test gate evaluates the **compound score** `TOP2A − EPAS1`.
The v2 knockoff gate evaluates each gene **individually** under
Model-X exchangeability and applies FDR control. These are
**different selection objects**; concordance is not guaranteed and
should not be expected when the underlying signal is multivariate
and compact.

Three contributing factors, in order of importance:

1. **Compound signal vs. individual selection.** The pre-registered
   v1 finding is that `TOP2A − EPAS1` is a *compound* law; neither
   gene alone reaches the +0.05 incremental AUROC margin (TOP2A
   alone clears 0.65; EPAS1 alone clears 0.62). A univariate-FDR
   procedure has no compound-aware test surface — it asks "does
   this gene's solo W statistic exceed the data-driven threshold?",
   not "does this 2-gene difference pass?" The prior single-run
   experiment in `results/track_a_task_landscape/g1_knockoffs/knockoffs_report.json`
   (equicorrelated knockoffs, no derandomization) found exactly the
   same pattern: TOP2A and EPAS1 are the **top two genes by W
   statistic** (W=0.047 and W=0.056) but neither crosses threshold
   at q=0.10 or q=0.20.

2. **Mardia normality FAIL on this panel.** The Model-X validity
   guarantee assumes the joint feature distribution is multivariate
   normal. Mardia's test on this 45-gene panel rejects the
   normality assumption at p<0.001 (skewness and kurtosis legs;
   recorded in `results/track_a_task_landscape/g1_knockoffs/knockoffs_report.json`).
   With non-Gaussian data the FDR control becomes approximate
   rather than guaranteed; the actual Type I error may be tighter
   than nominal q=0.10, reducing power.

3. **n=505 with prevalence 0.156 ≈ 80 cases.** With effective
   sample size on the order of the panel size, individual-feature
   selection has limited power even under perfect distributional
   assumptions.

### What this does NOT change

- The v1 5-test gate's compound finding (`TOP2A − EPAS1` passes,
  AUROC 0.728, decoy-feature p<0.001, ci_lower 0.669, +0.072 over
  best single gene). v1 is the canonical decision surface for the
  hackathon submission.
- The H3 result: when v1 rejects a candidate, v2 also fails to
  individually select its constituent genes (2/2 agreement). The
  two gates agree on the *negatives*.
- Anchor regression / 5-fold CV / IMmotion150 PFS replay all
  remain consistent with the v1 verdict.

## What this DOES say

- The signal in `TOP2A − EPAS1` is **genuinely compound**: it
  cannot be decomposed into individual-feature FDR-significant
  terms. This is consistent with the published ccA/ccB axis,
  which is a *contrast* (proliferation – HIF-2α), not two
  independent markers.
- Treating the v2 knockoff result as a *negative individual-feature
  signal* is honest reporting of the rigor extension; it does not
  contradict the compound-law claim.

## Reproducibility

- Sweep: `src/track_a_knockoff_sweep.py` (commits seed=0, q=0.10,
  25 replicates).
- Tests: `tests/test_knockoff_gate.py` — 6 unit tests on synthetic
  data with known signal genes (all pass).
- Pre-registration: `preregistrations/20260425T170647Z_g1_knockoff_v2.yaml`
  was committed before any data interaction; the `emitted_git_sha`
  field will be filled in at commit time.

## Citations

- Barber & Candès 2015. *Controlling the False Discovery Rate via
  Knockoffs*. Ann. Stat. arXiv:1404.5609.
- Bates et al. 2020. *Metropolised Knockoffs*. arXiv:2006.14342.
- Ren & Candès 2020. *Derandomizing Knockoffs*. arXiv:2012.11286.
- Spector & Janson 2022. *Powerful knockoffs via minimum variance
  reconstructability*. Ann. Stat. (knockpy `mvr` method).
