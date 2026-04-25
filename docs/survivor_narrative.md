# The survivor narrative — TOP2A − EPAS1

On 2026-04-22, the pre-registered 5-test gate in this repo rejected
100+ candidates across four ccRCC tasks and then — on the same
infrastructure, same gate, same thresholds — accepted nine candidates
on the metastasis task when the gene panel was expanded from 11 to
45 features. The simplest of those survivors is

```
score = TOP2A − EPAS1
```

This document walks through what that one-line law is, why it passed,
why 100+ other candidates did not, and — most importantly — what it
is *not*.

## One-minute version

**Claim.** On TCGA-KIRC (n = 505, 16% M1), tumours with high TOP2A
(topoisomerase IIα; a direct marker of proliferating cells) relative
to EPAS1 (HIF-2α; the canonical well-differentiated hypoxic ccRCC
driver) are more likely to be metastatic at diagnosis. Measured as
a pre-registered compound law, the equation `TOP2A − EPAS1` reaches
AUROC 0.726 with a lower 95% CI bound of 0.665 and a permutation
null `p < 0.001`; the improvement over the best sign-invariant
single-gene classifier is `Δ = +0.069`, clearing the +0.05
threshold that was fixed before any fit.

**How surprising is this?** It is the published ccA-vs-ccB ccRCC
subtype axis (Brannon et al., Brooks et al., ClearCode34), so the
biology is not new. What is new is that unconstrained symbolic
regression rediscovered it without being seeded with it, and that
the pre-registered falsification gate accepted the compact 2-gene
form on merits written down before the search.

**Independent per-gene annotation.** Human Protein Atlas v21.0
pathology.tsv (Uhlén et al., *Science* 2015;
https://v21.proteinatlas.org/download/, queried 2026-04-23) flags
**TOP2A** as *prognostic\_unfavorable* and **EPAS1** as
*prognostic\_favorable* in renal cancer. This is a genome-wide
annotation computed from TCGA survival data by HPA curators — not
from our own cohort. The assignment aligns with the score direction
("high TOP2A − EPAS1 → worse PFS / M1") without any circular
reasoning from our analysis.

**How robust is this?** The survivor passes five of six robustness
axes (threshold grid, two-sided permutation stability, bootstrap
seed variance, feature scaling, cohort-size subsample) and a 5-fold
held-out CV (0.722 ± 0.078). The one caveat is that a logistic
regression on the same pair *with an interaction term* reaches
AUROC 0.722 on the same cohort — so against that specific
engineered baseline the compound wins by only +0.004. The
survivor's distinctive contribution is therefore interpretable
compactness plus pre-registered falsification, not an AUROC ceiling
that no other 2-gene model reaches.

**Beyond AUROC — imbalance-aware metrics (G2 rigor extension).** Per
TRIPOD+AI 2024 and Steyerberg (2019), AUROC alone is incomplete on
a 16% prevalence task. The G2 reporting layer
([`results/track_a_task_landscape/rigor_extension/`](../results/track_a_task_landscape/rigor_extension/SUMMARY.md))
adds: **AUPRC 0.321** (2.05× over the 0.156 prevalence baseline);
**Brier 0.122** (7.6% reduction vs the uninformative reference 0.132,
on 5-fold OOF Platt-scaled probabilities); **calibration slope 0.540**
with intercept −1.85. The slope being below the well-calibrated
range [0.85, 1.15] is itself an honest signal: the raw `TOP2A − EPAS1`
score is more discriminative than its scale, and the Platt-scaled
probability — not the raw difference — is the right object for any
downstream probability claim. The reliability curve's top quintile
predicts 32% M1 and observes 35% — well-calibrated at the high
(screening-relevant) end. This adds a probabilistic-correctness
dimension to the AUROC discrimination claim without changing any
gate decision.

**Information-theoretic compactness (I4).** A pre-registered
histogram-based mutual-information analysis with Miller-Madow
bias correction
([`results/track_a_task_landscape/information_theory/`](../results/track_a_task_landscape/information_theory/SUMMARY.md))
finds: I(joint; y) is **1.82×** larger than max individual MI
(P1 PASS — genes work together, not separately); **synergy is
positive** (+0.0014 nats; P2 PASS — genes are not redundant);
and the linear `TOP2A − EPAS1` form captures **98.1%** of the
bivariate joint information (P3 PASS — the difference is
essentially lossless relative to any function of the pair).
This is the information-theoretic version of the compactness
claim: out of every possible quadratic, log-ratio, neural-net,
or kernel function of (TOP2A, EPAS1), the best one could
recover at most an additional 0.0006 nats — the simple
1-line difference is near-optimal.

**Clinical-language translation (I3).** AUROC 0.728 in clinician
terms
([`results/track_a_task_landscape/clinical_utility/`](../results/track_a_task_landscape/clinical_utility/SUMMARY.md)):
**Cohen's d = 0.856** (medium-large effect by Cohen 1988; P1 PASS);
**OR per 1-SD = 2.07** (95% CI 1.65–2.59; P2 PASS — each
standard-deviation increase in `TOP2A − EPAS1` more than doubles
M1 odds). At the top-quintile cutoff, sensitivity 0.456 /
specificity 0.847 / NNS ≈ 2.81 — useful for **risk stratification**,
not standalone screening; the screening-grade prediction P3
(sens ≥ 0.50 at spec ≥ 0.85) **fails honestly by 0.044**, which
is the framework biting on the I-phase claim. Comparable AUROC
to the published 34-gene ClearCode34 panel, with 2 genes —
operational simplicity is the specific clinical-translation
contribution.

**Rashomon set — how unique among 2-gene laws (I2).** A pre-registered
enumeration of all `C(45, 2) = 990` two-gene differences on this panel
([`results/track_a_task_landscape/rashomon_set/`](../results/track_a_task_landscape/rashomon_set/SUMMARY.md))
finds that **TOP2A − EPAS1 is rank 1 / 990** by sign-invariant AUROC.
The tight Rashomon set (within ε = 0.02 of the survivor) is exactly
**3 pairs** — TOP2A − EPAS1 (0.7275), CDK1 − EPAS1 (0.7192), and
EPAS1 − MKI67 (0.7100) — all of the form *(proliferation marker −
HIF-2α)*. 100% of the tight set contains either EPAS1 or a
proliferation marker. All three pre-registered predictions
(P1: top-5 rank, P2: tight set ≤ 20 pairs, P3: ≥ 80% prolif/EPAS1
membership) PASS. The compactness claim is now a measured one:
within the 2-gene-difference model class, TOP2A − EPAS1 *is* the
AUROC ceiling, and the entire near-equivalent neighbourhood is a
three-pair cluster of the same biology.

**Individual-feature FDR check (G1 knockoff v2).** A Model-X
knockoff filter
([`results/track_a_task_landscape/knockoff_v2/`](../results/track_a_task_landscape/knockoff_v2/SUMMARY.md);
LedoitWolf Sigma, MVR construction, q=0.10, 25 derandomized
replicates per Ren & Candès 2020) applied to the 45-gene panel
selects **0 / 45 genes** individually. TOP2A and EPAS1 are ranked
#1 and #2 by W statistic but neither crosses threshold at the
pre-registered q=0.10. Read honestly, this is **not** a contradiction
of the v1 5-test gate's compound finding — it confirms the signal in
`TOP2A − EPAS1` is *genuinely compound*. The v1 gate evaluates the
contrast directly; the v2 knockoff gate evaluates each gene under a
univariate-FDR procedure that has no compound-aware test surface.
Both gates agree on negatives (rejected laws have no constituent
genes selected). The compound-vs-individual disagreement is the
same pattern that makes the published ccA/ccB axis a *contrast*,
not two independent markers.

**Cross-cohort causal stability (anchor regression).** Anchor
regression ([Rothenhäusler et al., JRSS-B 2021](https://arxiv.org/abs/1801.06229))
pooling TCGA-KIRC (n=505) and IMmotion150 (n=263) as two independent
environments yields: TOP2A coefficient +0.197 (stable γ=0→100),
EPAS1 coefficient -0.201 (stable γ=0→100). Cochran Q heterogeneity
tests: Q=1.39, p=0.238 (TOP2A); Q=0.68, p=0.410 (EPAS1). No
significant inter-cohort disagreement. The coefficient direction and
the sign of `TOP2A − EPAS1` do not change across cohorts or under
increasing anchor penalty — consistent with a law that is not an
artefact of one dataset's distribution shift. Honest caveat: both
cohorts are kidney clear-cell (same disease), so this tests
platform/patient-selection heterogeneity, not biological context
transfer. IMmotion150 is metastatic-only (Stage IV), so the anchor
does not swap biological context from M0 to M1.

**What it is not.** Not a diagnostic biomarker. Not novel biology.
Not a replacement for prospective validation. Research use only.

## Why 100+ other candidates failed

Four ccRCC tasks were run with the same pipeline before the 45-gene
panel was tried:

| Task | Dominant single gene (sign-inv AUROC) | Survivors |
|---|---|---|
| Tumor vs Normal | CA9 = 0.965 | 0 / 33 |
| Stage I-II vs III-IV | CUBN = 0.610 | 0 / 34 |
| 5-yr Survival | CUBN = 0.696 | 0 / 36 |
| Metastasis (11-gene panel) | MKI67 = 0.645 | 0 / 37 |

Each task is dominated by a different single gene. On tumor-vs-
normal, CA9 alone saturates classification at AUROC 0.965, which
makes +0.05 mathematically unreachable for any compound
(`law_AUROC` would have to exceed 1.015). On stage and survival,
CUBN — a proximal-tubule marker lost during tumor dedifferentiation
— already carries most of the separation signal. On metastasis
with the 11-gene HIF-axis panel, the panel simply does not
contain genes that encode the aggressive proliferation program.

On the 45-gene expanded panel (which adds TOP2A, MKI67, CDK1,
CCNB1, PCNA, MCM2, plus HIF-2α partners and EMT markers), the
signal that was absent in the 11-gene run becomes available and
the gate starts accepting. The nine surviving laws cluster into
three shapes, all centred on `proliferation − HIF-2α`:

- `TOP2A − EPAS1` (5 laws at AUROC 0.726)
- `MKI67 − EPAS1` (2 laws at AUROC 0.708)
- a 5-gene compound (`MKI67 / EPAS1 / LRP2 / PTGER3 / RPL13A`) at
  the same AUROC 0.726 as the simpler pair

All three clusters encode the same biology. Parsimony preference
picks the 2-gene form.

## Why this is interesting *as a discovery artefact*

Three properties matter:

1. **Pre-registration actually bites on both sides.** The same +0.05
   threshold that rejected the textbook Opus-proposed HIF-axis law
   on tumor-vs-normal (`log1p(CA9) + log1p(VEGFA) − log1p(AGXT)`,
   AUROC 0.984 — but +0.019 over CA9 alone, so FAIL) accepts an
   unseeded 2-gene law on metastasis. Neither decision was made
   after the fact.
2. **The accept doesn't collapse under stress.** The 6-axis
   robustness profile (see
   [`survivor_robustness/SUMMARY.md`](../results/track_a_task_landscape/survivor_robustness/SUMMARY.md))
   matches the specific toolkit Sci-B used to harden the *reject*
   verdict. Same methodology, same toolkit, opposite direction.
3. **The caveat is named explicitly.** A 2-gene LR with interaction
   on the same pair reaches AUROC 0.722. The survivor's value is
   not that nothing else could pass — it's that it passed a
   pre-registered gate while staying readable in one line.

**Citations.** Published ccA/ccB ccRCC subtype axis: Brannon 2010 ([PMID 20871783](https://pubmed.ncbi.nlm.nih.gov/20871783/)); Brooks 2014 ClearCode34 ([DOI 10.1016/j.eururo.2014.02.035](https://doi.org/10.1016/j.eururo.2014.02.035)); TOP2A prognostic in ccRCC 2024 ([PMID 38730293](https://pubmed.ncbi.nlm.nih.gov/38730293/)). Contemporary falsification-oriented AI-for-Science benchmarks: POPPER ([arXiv 2502.09858](https://arxiv.org/abs/2502.09858)); Sakana AI Scientist v2 ([arXiv 2504.08066](https://arxiv.org/abs/2504.08066)); SPOT ([arXiv 2505.11855](https://arxiv.org/abs/2505.11855)); FIRE-Bench ([arXiv 2602.02905](https://arxiv.org/abs/2602.02905)) — formalises agent evaluation by rediscovery of published findings (SOTA <50 F1), the paradigm under which our 2-gene ccA/ccB axis re-derivation is the positive result.

## What would make this claim stronger

1. **Independent-cohort replay** on a ccRCC dataset with TOP2A +
   EPAS1 measurements and M-staging at the patient level. GSE40435
   (our current transfer cohort) has neither. Candidate cohorts:
   - **CPTAC-3 ccRCC** (proteogenomic, has M-staging)
   - **cBioPortal MSKCC-IMPACT metastatic ccRCC**
2. **Larger panel** (200-gene Hallmark HYPOXIA or the full
   transcriptome). Hypothesis: the +0.069 incremental gap holds
   but the survivor count grows; alternatively, the
   pair-interaction baseline ceiling also rises to match the
   compound, which would narrow the compactness claim.
3. **Prospective held-out sample** (TCGA-KIRC freshly accessed via
   GDC rather than the cached star_tpm release).

Each of the three is scoped in the live `STATUS.md` "What's left"
section.

## Short version for the demo / Loom

> We pre-registered a five-test statistical gate before touching
> data. Opus 4.7 proposed seven KIRC law families. PySR searched
> the space. The gate rejected every one of the textbook HIF-axis
> compounds — including the law Opus 4.7 itself most wanted to
> survive. Then we expanded the panel, re-ran the same gate, and
> nine compact laws passed on metastasis. The simplest is
> **TOP2A − EPAS1**: when a ccRCC tumour's proliferation program
> runs ahead of its HIF-2α differentiation program, it's more
> likely to be metastatic. This is the published ccA-vs-ccB
> subtype axis. We didn't put it there. The gate accepted it
> because the numbers pre-registered before the fit said "accept
> if it clears +0.05 over the best single gene" and it cleared by
> +0.069.

## Related reading

- [`docs/methodology.md`](methodology.md) — Section 6 has the full
  accept/reject table.
- [`docs/why_opus_4_7.md`](why_opus_4_7.md) — Section 4 walks the
  accept + reject cycle in Opus-role terms.
- [`results/track_a_task_landscape/SUMMARY.md`](../results/track_a_task_landscape/SUMMARY.md)
  — cross-task matrix.
- [`results/track_a_task_landscape/survivor_robustness/SUMMARY.md`](../results/track_a_task_landscape/survivor_robustness/SUMMARY.md)
  — 6-axis stress test.
- [`results/track_a_task_landscape/survivor_robustness/INTERPRETATION_top2a_epas1.md`](../results/track_a_task_landscape/survivor_robustness/INTERPRETATION_top2a_epas1.md)
  — Opus-4.7-authored mechanism + caveat statement.
- [`results/track_b_gate_robustness/SUMMARY.md`](../results/track_b_gate_robustness/SUMMARY.md)
  — robustness of the *reject* verdict on the 11-gene panel.
