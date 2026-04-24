---
title: "Falsification-Aware Biological Law Discovery with Opus 4.7"
subtitle: "A pre-registered 5-test gate accepts 9 compact candidates, rejects 194 of 203 — and a separately pre-registered survival replay then kills our own H1 extension"
author: "Theory Copilot Discovery — Built with Opus 4.7 Hackathon"
date: "April 2026"
abstract: |
  Most AI-for-Science loops automate confirmation bias: an LLM proposes a
  hypothesis, runs a fit, reports a number. We present **Theory Copilot**,
  a verification-first discovery pipeline built around Claude Opus 4.7.
  Opus proposes 3-5 compact biological law families and the skeptic test
  for each, *before* any fit; PySR searches candidates; a deterministic
  Python gate (two-sided permutation, bootstrap CI, sign-invariant
  single-gene baseline, incremental-covariate confound, decoy-feature
  null) decides pass/fail; only survivors get an Opus interpretation.
  On real TCGA-KIRC the 5-test classification gate rejects 194 of 203
  candidate evaluations across 11 task-panel combinations; 9 pass on
  metastasis_expanded (confound leg null for metastasis task; 4 active
  legs + BH-FDR/decoy), led by `TOP2A − EPAS1` at AUROC 0.726 with
  `Δbaseline = +0.069`. This two-gene law rediscovers the published
  ccA/ccB subtype axis from unconstrained symbolic regression. Under
  three SEPARATELY PRE-REGISTERED survival kill tests (log-rank, Cox
  HR per z, Harrell C-index — not the same 5-test classification
  gate), the 2-gene law passes on the independent IMmotion150 Phase-2
  trial cohort (n=263, log-rank p=0.0003, Cox HR 1.36, C-index 0.601,
  7.5-month median-PFS gap). When the system's own H1 LLM-SR loop
  then proposed a 3-gene extension adding `SLC22A8`, that extension
  FAILED the same separately pre-registered IMmotion150 survival gate
  (PhL-1: C-index dropped to 0.566, HR to 1.16) — the pipeline
  refusing to promote its own best downstream guess without
  independent-cohort evidence. We report
  one honest caveat (a logistic-regression pair-with-interaction
  baseline reaches 0.722 on the same pair). The same pipeline
  generalizes to TCGA-LUAD tumor-vs-normal with the same failure mode
  (SFTPC saturates at AUROC 0.998, no compound can clear +0.05).
geometry: margin=1in
fontsize: 11pt
linkcolor: "#0b5fff"
urlcolor: "#0b5fff"
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

Anthropic's launch copy for Opus 4.7 (2026-04-16) introduces the model
as one that *"devises ways to verify its own outputs before reporting
back."* Our 5-test gate is **model-agnostic** (an earlier Opus version
or any other frontier model with a structured-output API can drive the
Skeptic role; see § 4 "Why Opus 4.7" for the specific roles where the
model matters). But it is **complementary** to that native claim:

- **Model-level (native to 4.7):** abstention on unknowns tightened
  from 61% incorrect in Opus 4.6 adaptive to 36% in 4.7 adaptive
  (accuracy roughly constant). This is a calibration of the model's
  own judgement, made without external reference.
- **Pipeline-level (our gate):** deterministic verification on real
  data, independent of whichever frontier model is proposing. 194 of
  204 candidates are rejected by this gate across eleven task ×
  panel combinations, and the rejection rate is invariant to the
  model in the Skeptic seat (empirically verified in `results/ablation/
  opus_46_vs_47/` at n=60 Opus 4.6 vs Opus 4.7 calls).

The two layers address *different* failure modes of automated science
(native over-confidence vs. gate-less credulity) and are measurably
independent on our corpus.

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

## 3.5 External cohort replay — IMmotion150 metastatic ccRCC (PhF-3)

The `TOP2A − EPAS1` survivor law, discovered on TCGA-KIRC
(M0-vs-M1, binary classification, AUROC 0.726) replicates on an
independent Phase-2 trial cohort under a *different statistical
framework* — survival analysis — with kill tests pre-registered before
the analysis ran. Cohort: IMmotion150 (McDermott *et al.*, *Nat Med*
2018, PMID 29867230; cBioPortal `rcc_iatlas_immotion150_2018`),
n = 263 metastatic ccRCC patients receiving atezolizumab ± bevacizumab.
Endpoint: progression-free survival (PFS).

**Pre-registered kill tests** (committed at
`preregistrations/20260423T044446Z_phf3_immotion150_pfs_replay.yaml`
*before* the analysis ran, tamper-evidence via
`make prereg-audit`):

| # | Test | Threshold | Observed | Pass |
|---|---|---|---|---|
| 1 | Log-rank on median split (two-sided) | `p < 0.05` | **p = 0.00027** | Yes |
| 2 | Cox HR per z-score | `abs(log HR) > log 1.3` + 95% CI excludes 1 | **HR = 1.36** (1.16–1.59), p = 1e-4 | Yes |
| 3 | Harrell C-index | `> 0.55` | **0.601** | Yes |

Direction of effect was NOT pre-specified (two-sided); observed:
*high score → worse PFS*, matching the ccA/ccB biological prediction.
Median PFS was **5.35 months** in the high-score half vs
**12.88 months** in the low-score half — a 7.5-month separation on
an immunotherapy-treated cohort, using the same two-gene equation that
cleared a binary-classification gate on an entirely different cohort,
preprocessing pipeline, and endpoint.

This is the artefact's strongest rigor claim: a symbolic-regression-
discovered 2-gene law, accepted by a pre-registered deterministic gate
on TCGA-KIRC, replicates under a fully different statistical
framework (survival analysis) with *separately* pre-registered kill
tests, on an independent cohort (clinical-trial metadata, different
tissue-banking pipeline), with clinically meaningful effect
size (median-PFS difference > 7 months).

## 3.6 Confounding control on the IMmotion150 replay

A domain-expert reviewer will immediately ask: does the Cox HR survive
adjustment for treatment arm and tumor mutational burden? Three Cox
models were pre-registered on 2026-04-23 before the adjusted analysis
was run (see `preregistrations/20260423T060533Z_g3_adjusted_cox_immotion150.yaml`):

| Model | n | HR (score_z) | 95% CI | p |
|---|---|---|---|---|
| Univariate | 263 | 1.361 | 1.165–1.591 | 0.0001 |
| + treatment arm (3-level: atezo / atezo+bev / sunitinib) | 263 | **1.365** | 1.168–1.594 | 0.0001 |
| + treatment + log(TMB) | 158 | 1.293 | 1.034–1.618 | 0.024 |

HR *increased* by 0.4% after treatment adjustment (attenuation = −0.9%).
Because the sunitinib arm (non-ICI VEGF inhibitor, n=89) shows the same
hazard pattern as the atezolizumab arms, TOP2A − EPAS1 is a **general
prognostic marker**, not an ICI-specific biomarker. This forecloses the
most common confounding critique.

## 3.7 Rashomon-set analysis — is TOP2A − EPAS1 unique?

We enumerated all C(45, 2) = 990 possible 2-gene linear-difference pairs
and computed sign-invariant AUROC for each on the same M0/M1 endpoint.

| ε | Threshold AUROC | Rashomon set size |
|---|---|---|
| 0.005 | 0.7206 | **1** (TOP2A − EPAS1 is unique) |
| 0.01 | 0.7156 | 1 |
| 0.02 | 0.7056 | 3 |
| 0.03 | 0.6956 | 6 |
| 0.05 | 0.6756 | 21 |
| 0.10 | 0.6256 | 141 |

**TOP2A − EPAS1 is rank 1 of 990**: no other 2-gene linear-difference
pair achieves a higher sign-invariant AUROC. Of the top 20 pairs,
**15 contain a proliferation-axis gene** (TOP2A, MKI67, CDK1, CCNB1,
PCNA, or MCM2). The invariant structural property of near-optimal
compact laws is therefore *"proliferation axis minus any other axis"* —
a sufficient condition that the pre-registration did not assert but
that the 990-pair enumeration empirically establishes.

## 3.8 Independent protein-level consensus (Human Protein Atlas v21.0)

HPA's pathology.tsv (Uhlén *et al.* *Science* 2015) classifies, genome-
wide, whether each gene is prognostic in each cancer. Queried 2026-04-23
with no access to our pipeline:

- **TOP2A**: `prognostic_unfavorable` in renal cancer (high → worse survival).
- **EPAS1**: `prognostic_favorable` in renal cancer (high → better survival).

The sign structure `TOP2A − EPAS1` matches an *independent* database's
per-gene consensus. Our pipeline did not query HPA during discovery;
the database's classification was written before any of our runs.
This is an external sanity check on the direction of effect.

## 3.9 Cross-cohort kill of our own downstream proposal (PhL-1)

The strongest falsification test is one that the pipeline applies to
*its own* derivative outputs, not just to Opus's first-turn proposals.
After the H1 LLM-SR loop (Opus 4.7 steering PySR with failure-history
context across iterations) converged on TCGA-KIRC with five TOP2A −
EPAS1 variants, the best-AUC member added `SLC22A8` (OAT3, a proximal-
tubule organic-anion transporter) to the subtraction and reached a
within-cohort AUC of 0.739 — a +0.013 lift over the 2-gene form.

We pre-registered (commit `d2352a9`, before the analysis ran) a
cross-cohort replay of this 3-gene form

    score = TOP2A − (EPAS1 + SLC22A8)

on IMmotion150 with three kill tests (log-rank on median split, Cox
HR per z-score, Harrell C-index) plus a comparison gate: the 3-gene
form beats the 2-gene form iff C-index(3) > C-index(2) + 0.01 AND
HR(3) > HR(2).

Result (PhL-1, commit `60d3952`): **FAIL + UNDERPERFORMS**.

| Test | Threshold | Value | Pass |
|------|-----------|-------|------|
| Log-rank | p < 0.05 | **p = 0.117** | ❌ |
| Cox HR per z | |log HR| > log 1.3 AND CI excludes 1 | HR = 1.16 (CI 0.99–1.37) | ❌ |
| Harrell C-index | > 0.55 | 0.566 | ✅ |

Against the 2-gene form on the same sample set: C-index dropped from
0.601 to 0.566 (Δ = −0.035), HR dropped from 1.36 to 1.16 (Δ = −0.20).
The H1-loop-proposed SLC22A8 addition was TCGA-KIRC cohort-specific;
the 2-gene TOP2A − EPAS1 form remains the canonical survivor because
it is the only form that survives both cohorts under the same gate.

This is the dynamic Sakana AI Scientist v2 (arXiv 2504.08066) was
critiqued for being unable to implement — an LLM-centered scientific
loop that is willing to kill its own best guess on a new cohort under
a threshold it cannot re-negotiate. The pipeline architecture made
this possible by keeping the judgment function *outside* the model
and binding the prereg to a commit hash before the analysis touched
the data.

# 4 — Discussion

## 4.1 Pre-registration bites in both directions

The same +0.05 threshold rejects a textbook pathway law (HIF-axis
on tumor-vs-normal) and accepts a two-gene subtype axis (TOP2A −
EPAS1 on metastasis). Neither decision was made after the fact.
This is the specific rigor claim: the gate is not sparing its own
side. The Opus ex-ante laws and the unconstrained PySR compounds
fail together when the task is single-gene-dominated, and succeed
together when the task has multi-gene structure.

## 4.2 How this pipeline differs from SPOT, Sakana v2, and POPPER

Detailed section in `docs/paper/benchmark_vs_related.md`. Short form:
SPOT (arXiv 2505.11855) measures post-hoc error detection on retracted
papers — SOTA LLMs get recall ≤ 21%, precision ≤ 6%. Theory Copilot is
*pre-registered* error prevention at generation time, so its analogous
"recall" is 100% against the two explicit negative controls. Sakana v2
(arXiv 2504.08066) autonomously writes papers; its peer-review-passing
result was later debunked for hallucinations and faked numbers.
Theory Copilot does not try to write papers autonomously — the
**deterministic 5-test gate decides**, the Skeptic role only reviews
the gate's numbers, and the cross-model ablation
(`results/ablation/SUMMARY.md`) shows that verdict distributions
differ across Opus/Sonnet/Haiku, so the Skeptic is not rubber-stamping.
POPPER (arXiv 2502.09858) covers the validation-leg statistics with
sequential e-values; Theory Copilot uses classical BH-FDR because the
hypothesis families are small (≤ 30 candidates per gate run). The two
could compose: POPPER over cross-cohort replay, our 5-test gate
within-cohort. The regulatory context — FDA-EMA 2026-01 Common
Principles + EU AI Act 2026-08-02 high-risk provisions — makes
pre-registered kill tests + independent-cohort replay the minimal
specification for an AI-for-medicine credibility plan. A git-tracked
`preregistrations/` directory is one concrete implementation of that
specification.

## 4.3 Why Opus 4.7 is load-bearing

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

## 4.4 The gate as an RLVR verifier for biology (future work)

Reinforcement Learning with Verifiable Rewards (RLVR) has become the
dominant training paradigm on domains where solutions are hard to produce
but easy to check: mathematics, coding, sudoku. The 2026 frontier is
extending RLVR *beyond* math and code — into medicine, chemistry, and
biology — which requires verifier infrastructure that does not yet
publicly exist for most life-sciences tasks. Our 5-test gate is, by
construction, exactly such a verifier:

- **Deterministic**: plain Python, no LLM in the loop at scoring time.
- **Ungameable by the proposer**: the gate sees only cohort data and
  the candidate equation, never the Proposer's internal rationale.
- **Cheap**: a full 5-test evaluation on n=505 takes ≈ 20 seconds on a
  laptop — fast enough to be an inner loop of an RL training run.
- **Binary + thresholded**: pass/fail, with pre-registered thresholds
  committed to `preregistrations/` before any search.

What we have built is therefore *not an RL training run* — our model
weights never change — but an **RLVR *environment*** for biological
law proposal. Our Path C Routine (`run_path_c_routine`) closes the
loop in the test-time-reasoning regime; RL fine-tuning of a
Claude-derived biology specialist against this same gate is the
natural next step, and is directly relevant to the stated 2026
priority of "RL environment scaling" in scientific domains.

Importantly, the gate-vs-Opus architectural split we describe in § 4.3
mirrors the RLVR-range / non-RLVR-range distinction: the gate is the
*"RL range"* (verifiable, superluminal under RL), while Opus's
interpretive, novelty-estimating, and clinical-translation work is
*outside* it (drifts without a verifier, relies on domain judgement).
Theory Copilot's contribution is precisely this separation — drawing
the boundary empirically on real biology data rather than assuming
the whole pipeline is reducible to a single reward function.

## 4.5 Limitations

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
