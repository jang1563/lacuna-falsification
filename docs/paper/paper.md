---
title: "Falsification-Aware Biological Law Discovery with Opus 4.7"
subtitle: "A pre-registered 5-test gate accepts one compact law and rejects 100+"
author: "Theory Copilot Discovery — Built with Opus 4.7 Hackathon"
date: "April 2026"
abstract: |
  Most AI-for-Science loops automate confirmation bias: an LLM proposes a
  hypothesis, runs a fit, reports a number. We present **Theory Copilot**,
  a falsification-first discovery loop built around Claude Opus 4.7.
  Opus proposes 3-5 compact biological law families and the skeptic test
  for each, *before* any fit; PySR searches candidates; a deterministic
  Python gate (two-sided permutation, bootstrap CI, sign-invariant
  single-gene baseline, incremental-covariate confound, decoy-feature
  null) decides pass/fail; only survivors get an Opus interpretation.
  On real TCGA-KIRC the gate rejects 100+ candidates across four tasks
  where one gene already solves the problem, *and* accepts 9/30
  candidates on metastasis with a 45-gene expanded panel, led by
  `TOP2A − EPAS1` at AUROC 0.726 with `Δbaseline = +0.069`. This two-
  gene law rediscovers the published ccA/ccB subtype axis from
  unconstrained symbolic regression. We report one honest caveat
  (a logistic-regression pair-with-interaction baseline reaches 0.722
  on the same pair) and cross-cohort replay status. The same pipeline
  generalizes to TCGA-LUAD tumor-vs-normal with the same failure mode
  (SFTPC saturates at AUROC 0.998, no compound can clear +0.05).
geometry: margin=1in
fontsize: 11pt
linkcolor: blue
urlcolor: blue
---

# 1 — Introduction

The older failure mode of confirmation bias was one scientist
p-hacking one dataset. The newer version is cheap and scaled: an LLM
generates forty plausible hypotheses, runs them all, and surfaces
whichever one cleared an arbitrary threshold on one split. The search
space is wide enough that a high AUROC on a single cohort is nearly
free. Confirmation bias used to be a time-limited failure; it is now
a pipeline output.

Pre-registration is the discipline biology keeps pointing back to.
You write down what would falsify the claim *before* you see whether
it passes. Theory Copilot takes that seriously: every law family is
paired with skeptic tests Opus 4.7 writes **before any fit is
attempted**, and the law has to survive those tests as a condition
for being called a survivor. The tests are executed by plain Python
against real data — not by a second LLM call that could also
rationalize its way to agreement.

Contemporary work has converged on the same observation: POPPER
(Falsification-guided AI agents; arXiv:2502.09858), Sakana AI
Scientist v2 (arXiv:2504.08066), and SPOT (scientific peer-review
automation; arXiv:2505.11855) all push toward *adversarial* review
as a missing ingredient in LLM-driven science. This artefact is a
concrete implementation with a deterministic gate and a single
surviving law that was not in the training distribution's most
obvious place to look.

# 2 — Methods

## 2.1 Role architecture

Opus 4.7 is load-bearing in exactly three places. The rest is
deterministic.

- **Proposer (ex-ante).** Emits 3-5 compact law families + a skeptic
  test per family + at least one negative control, *before* any fit.
  Prompt in `prompts/law_family_proposal.md` with JSON schema
  enforcement.
- **Skeptic (post-hoc).** After the gate reports metrics, Opus reviews
  specific numeric values (`perm_p = 0.049` ≠ `0.001`; a
  `ci_lower = 0.61` is marginal; a `delta_confound` just over threshold
  can hide an interaction). Prompt in `prompts/skeptic_review.md`.
- **Interpreter (survivor).** For passed candidates, Opus synthesizes
  mechanism + prediction + hypothesis with literature citations.

Opus does not run the falsification gate and does not decide pass/fail.
The API call uses `thinking={"type":"adaptive","display":"summarized"}`
+ `output_config={"effort":"high"}` via the streaming endpoint (the
non-streaming 32000-token request trips the SDK 10-minute guard; see
`src/theory_copilot/opus_client.py` commit history).

## 2.2 The 5-test gate

Every candidate passes through five deterministic tests. Thresholds
are pre-registered in `src/theory_copilot/falsification.py`.

| Test | Statistic | Threshold |
|---|---|---|
| `label_shuffle_null` | Two-sided permutation p (1000 shuffles) | `p < 0.05` |
| `bootstrap_stability` | Lower bound of 95% CI on AUROC (1000 resamples) | `ci_lower > 0.6` |
| `baseline_comparison` | `law_AUROC − max_i max(AUROC(x_i), 1−AUROC(x_i))` | `delta > 0.05` |
| `confound_only` | `AUROC(LR(cov + law)) − AUROC(LR(cov))` | `delta > 0.03` |
| `decoy_feature_test` | p-value against 100 random features at matched scale | `p < 0.05` |

Permutation p-values across candidates are adjusted with Benjamini-
Hochberg FDR (α = 0.1); the gate uses the FDR-adjusted p. A
two-sided null was chosen because symbolic regression can return a
sign-flipped winner, and the sign-invariant baseline (AGXT in ccRCC
has raw AUC 0.03 but is a perfectly usable classifier at
1 − AUC = 0.97) keeps the delta from being inflated by sign.

## 2.3 Search and data

PySR v1.5.9 on Julia 1.10.0 runs locally with `variable_names=gene_cols`
so equations come back in biological symbols. `niterations=1000-2000`
on flagship runs; `maxsize≤15` so the winner is human-readable. The
Proposer's `initial_guess` seeds PySR's `guesses=[...]` pool at
`fraction_replaced_guesses=0.3`.

Flagship cohort: TCGA-KIRC STAR TPM from GDC-Xena (609 samples).
Replay cohort: GSE40435 microarray (202 paired). The expanded 45-gene
panel adds HIF-2α partners, proliferation markers, EMT markers, and
metastasis signals on top of the original 11-gene HIF-axis panel.
Second-disease validation: TCGA-LUAD STAR TPM (589 samples) via the
same GDC-Xena path.

# 3 — Results

## 3.1 The reject cycle (four tasks × 11-gene panel)

Across four biologically distinct ccRCC tasks, the 11-gene panel
produced **0 survivors out of 100+ candidates** (33 Opus ex-ante + 27-30
PySR per task). Each task is dominated by a different single gene.

| Task | n | Dominant single gene (sign-inv AUROC) | Survivors |
|---|---|---|---|
| Tumor vs Normal | 609 | CA9 (0.965) | 0 / 33 |
| Stage I-II vs III-IV | 534 | CUBN (0.610) | 0 / 34 |
| 5-yr Survival | 301 | CUBN (0.696) | 0 / 36 |
| Metastasis M0 vs M1 | 505 | MKI67 (0.645) | 0 / 37 |

All 33 Opus-proposed pathway laws fail in the same pattern. This is
not a failure of LLM guidance; it is the gate refusing to call a
single-gene-saturated task a multi-gene discovery. Crucially, the
textbook HIF-axis law `log1p(CA9) + log1p(VEGFA) − log1p(AGXT)`
achieves AUROC 0.984 on tumor-vs-normal but is rejected — CA9 alone
already reaches 0.965, so the compound's Δbaseline is +0.019, below
the +0.05 pre-registered threshold.

## 3.2 The accept cycle (metastasis × 45-gene expanded panel)

Expanding the gene list to 45 features yields the first survivor
cohort at the default pre-registered thresholds:

- **9 of 30 PySR candidates pass on metastasis** (`Δbaseline` up to
  +0.069, `ci_lower` 0.654-0.670, two-sided permutation `p < 0.001`,
  decoy-feature `p < 0.001`).
- Survivors cluster into three shapes, all centred on proliferation
  minus HIF-2α:
  - `TOP2A − EPAS1` (5 laws, AUROC 0.726)
  - `MKI67 − EPAS1` (2 laws, AUROC 0.708)
  - a 5-gene compound at AUROC 0.726 (no incremental gain)

`EPAS1` is HIF-2α, the canonical well-differentiated hypoxic ccRCC
driver. `TOP2A` and `MKI67` are proliferation markers. The simplest
surviving law reads as *"proliferation running ahead of HIF-2α
predicts metastasis"* — the published ccA-vs-ccB ccRCC subtype axis
(Brannon et al. 2010, PMID 20871783; Brooks et al. ClearCode34,
DOI 10.1016/j.eururo.2014.02.035; TOP2A in ccRCC metastasis,
PMID 38730293). The axis was not seeded into the search.

## 3.3 Honest caveat on the survivor

Six robustness axes were run: threshold grid, two-sided permutation
stability, bootstrap seed variance, feature scaling, cohort-size
subsample, and baseline ablation. The survivor passes five of six.
The single caveat: a logistic regression on the same gene pair with
an interaction term (`TOP2A`, `EPAS1`, `TOP2A × EPAS1`) reaches
AUROC 0.722 on the same cohort, so against that specific engineered
baseline the compound wins by only `Δ = +0.004`. The survivor's
distinctive contribution is therefore interpretable compactness plus
pre-registered falsification, **not** an AUROC ceiling that no other
two-gene model can reach.

## 3.4 Second-disease generalization (TCGA-LUAD)

The same pipeline runs unmodified on TCGA-LUAD tumor-vs-normal via
the DatasetCard abstraction (`--dataset-card config/dataset_cards/luad_tumor_normal.json`).
All four LUAD-specific Opus ex-ante laws clear four of five gate
tests (permutation, bootstrap CI, confound, decoy) but fail on
`delta_baseline` because `SFTPC` (surfactant protein C, lost in
tumor-dedifferentiated lung) saturates at AUROC 0.998. This
reproduces the KIRC tumor-vs-normal failure mode in a second cancer:
the gate refuses to call a single-gene-dominated task a multi-gene
discovery in LUAD just as it does in KIRC. Pipeline generalization is
demonstrated; a harder LUAD task (stage or metastasis) is the next
step.

# 4 — Discussion

## 4.1 Pre-registration bites in both directions

The same +0.05 threshold rejects a textbook pathway law (HIF-axis
on tumor-vs-normal) and accepts a two-gene subtype axis (TOP2A −
EPAS1 on metastasis). Neither decision was made after the fact.
This is the specific rigor claim: the gate is not sparing its own
side. The Opus ex-ante laws and the unconstrained PySR compounds
fail together when the task is single-gene-dominated, and succeed
together when the task has multi-gene structure.

## 4.2 Why Opus 4.7 is load-bearing

In principle the pipeline could run with Sonnet 4.6 at every LLM
step. It would fail three measurable ways: the ex-ante skeptic tests
would be weaker (Sonnet restates the proposer's rationale instead of
attacking it); the housekeeping negative control would not be
proactively emitted; post-hoc review would miss marginal metric
patterns. These are testable — Phase-E2 cross-model ablation (Lane 2)
runs 180 API calls (3 models × 6 candidates × 10 repeats) against a
pre-registered metric-specificity prediction. The claim is not "only
Opus can do it"; it is "Opus 4.7 does it correctly enough that the
rest of the pipeline can stay deterministic, which is what makes the
final artefact auditable."

## 4.3 Limitations

(i) The compact survivor is biological *rediscovery* of a published
subtype axis, not novel biology. The novelty is procedural — that
pre-registered falsification accepted it. (ii) The caveat on the
pair-with-interaction baseline is real. (iii) Cross-cohort replay
on a dataset with both TOP2A/EPAS1 and M-staging is still pending
(GSE40435's 8-gene subset omits TOP2A and EPAS1; CPTAC-3 proteogenomic
ccRCC is the natural target). (iv) Second-disease generalization was
shown on an easier task (LUAD tumor-vs-normal); a LUAD-stage run
would test whether the survivor-accept behaviour also generalizes.

# 5 — Conclusion

A falsification-first LLM discovery loop built around Opus 4.7 accepts
one compact law and rejects 100+ on the same infrastructure with the
same thresholds. The accepted law is the published ccA/ccB subtype
axis, rediscovered from unconstrained symbolic regression under a
gate whose accept criteria were written before any fit. The same
pipeline rejects saturated single-gene tasks in TCGA-LUAD with the
same pattern. Claude Opus 4.7 + a deterministic Python gate +
symbolic regression is a workable substrate for an auditable AI-for-
Science artefact. The pre-registration discipline, not the model, is
the rigor — but the model has to be good enough to supply honest
skeptic tests for that discipline to have bite.

# Code, data, and reproducibility

Code: `https://github.com/jang1563/theory-copilot-falsification`
(flipped public at submission). Primary entry points:
`make install && make test && make demo-kirc`. Re-running the full
flagship flow: `theory-copilot compare --dataset-card
config/dataset_cards/kirc_metastasis_expanded.json --proposals
config/law_proposals.json --output-root artifacts/`, then the PySR +
falsification commands the CLI prints.

# References

- Brannon AR, *et al.* "Molecular stratification of clear cell renal
  cell carcinoma by consensus clustering reveals distinct subtypes
  and survival patterns." *Genes Cancer.* 2010. PMID 20871783.
- Brooks SA, *et al.* "ClearCode34: a prognostic risk predictor for
  localized clear cell renal cell carcinoma." *Eur Urol.* 2014. DOI
  10.1016/j.eururo.2014.02.035.
- Huang L, *et al.* "TOP2A expression predicts aggressive clinical
  outcomes in renal cell carcinoma." *(2024).* PMID 38730293.
- Huang Y, *et al.* POPPER: Falsification-Guided Agent. arXiv:2502.09858,
  2025.
- Sakana AI. "The AI Scientist v2." arXiv:2504.08066, 2025.
- Zhang Y, *et al.* SPOT: Structured Peer-Review from Observations.
  arXiv:2505.11855, 2025.
- Amodei D. "Machines of Loving Grace." Essay, 2024.
