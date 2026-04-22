# Why Opus 4.7

Theory Copilot is an Opus 4.7-centered discovery loop. The work Opus 4.7 does is
deliberately bounded — the statistical falsification gate is plain Python, PySR
runs locally — but the three places where Opus 4.7 *is* load-bearing cannot be
replaced by a smaller model without changing what the artifact claims.

This document is deliberately honest about what Opus does not do.

## 1. The problem: confirmation bias is automated now

Most AI-for-Science pipelines have the same shape. A model proposes a hypothesis,
runs a fit, observes a number that looks good, and ships the number as a finding.
Nothing in that loop is adversarial. The model that generated the hypothesis is
also the judge of whether the hypothesis survives, and it is rewarded for
agreement.

The older version of this failure mode was a human researcher p-hacking one
dataset. The newer version is faster: an LLM generates forty plausible
hypotheses, runs them all, and surfaces whichever one cleared an arbitrary
threshold on one split. The search space is wide enough that a high AUROC on a
single cohort is nearly free. Confirmation bias used to be a time-limited
failure of individual scientists; it is now a cheap, scalable pipeline output.

The remedy biology keeps pointing back to is pre-registration: write down what
would falsify the claim *before* seeing whether it passes. This project takes
that seriously: every law family is paired with skeptic tests Opus 4.7 writes
**before any fit is attempted**, and the law has to survive those tests as a
condition for being called a survivor. The skeptic tests are executed by plain
Python against real data — not by another LLM call that could also rationalize
its way to agreement.

## 2. Where Opus 4.7 is load-bearing, and where it is not

**What Opus 4.7 does:**

1. **Proposer (ex-ante).** Given a dataset card and a feature list, emit 3–5
   compact law families and a concrete skeptic test per family. The skeptic
   tests are written before any fit, so they cannot be p-hacked to match the
   observed metrics. This is the pre-registration step.
2. **Ex-ante negative control.** The Proposer is required by the prompt to emit
   at least one family it expects to *fail* (e.g., housekeeping-gene contrast).
   The demo then shows the falsification gate killing that control alongside
   the survivors. This is what makes the gate legible as rigor instead of as
   theater.
3. **Skeptic (post-hoc review).** After the gate has produced pass/fail
   metrics, Opus 4.7 reviews the specific metric values — `perm_p = 0.049` is
   weaker than `perm_p = 0.001`; `ci_lower = 0.61` is marginal; a
   `delta_confound` just over threshold can hide an interaction the gate's
   threshold missed. Opus flags these edge cases and proposes one additional
   test.
4. **Interpreter (survivor).** For a surviving law, Opus 4.7 synthesizes a
   mechanism hypothesis across pathways (HIF axis, Warburg, normal-kidney
   markers) and states one downstream testable prediction.

**What Opus 4.7 does not do:**

- It does not run the falsification gate. `src/theory_copilot/falsification.py`
  runs the two-sided permutation null, bootstrap stability, sign-invariant
  best-single-feature baseline, incremental-covariate confound, and
  decoy-feature null. These are deterministic Python.
- It does not decide pass/fail. The gate decides; Opus reviews.
- It does not run PySR. Search is local and deterministic.

## 3. Why these specific roles need Opus 4.7

Three reasons, each measurable rather than stylistic.

**Extended thinking for ex-ante skeptic tests.** Writing a falsification test
*before* seeing data forces enumeration of failure modes the proposal does not
mention. Sonnet 4.6 tends to restate the proposal's own rationale as a weak
null check. Opus 4.7 with `thinking={"type":"adaptive","display":"summarized"}`
plus `output_config={"effort":"high"}` has enough internal scratch space to
hold the proposal and its adversarial complement long enough to emit a test
that the proposal's own rationale cannot trivially satisfy.

**Dual-role context that does not collapse.** The Skeptic role reviews the
Proposer's own output. Smaller models drift into "looks good to me" because
the tokens that generated the proposal are still the likely continuation.
Adaptive thinking lets Opus 4.7 maintain the review stance long enough to emit
a dissent when one is warranted. When none is warranted, its PASS verdict is
informative precisely because the prior is set against the proposal.

**Cross-pathway interpretation.** The Interpreter step is a multi-pathway
synthesis task: VHL loss → HIF stabilization → CA9/VEGFA induction → metabolic
rewiring (LDHA, SLC2A1) → suppression of normal-kidney oxidative metabolism
(AGXT, ALB). Opus 4.7 produces a short mechanism hypothesis with explicit
caveats; Sonnet produces a longer, less-anchored summary.

## 4. The honest demo moment

The pipeline does **not** show "Opus 4.7 tried to falsify a law and it
survived." Opus does not run the falsification.

What it does show:

1. Opus 4.7 proposes 5 law families for KIRC (3 pathway-grounded + 1
   single-gene anchor + at least 1 housekeeping negative control) and writes
   the ex-ante skeptic test for each.
2. PySR instantiates the families using Opus's `initial_guess` seeds with
   `variable_names=gene_cols` so equations come back in biological names.
3. The 5-test gate (permutation, bootstrap, sign-invariant baseline,
   incremental confound, decoy-feature null) runs on a held-out split of
   TCGA-KIRC with BH-FDR across candidates.
4. The demo shows the housekeeping negative control *failing* alongside the
   survivors passing — which is the moment that makes the gate legible as
   rigor rather than cherry-picked success.
5. Opus 4.7 reviews the metric pattern of each survivor and adds a post-hoc
   comment; any law where `train_auroc >> test_auroc` is flagged as overfit.
6. The surviving laws are replayed on GSE40435 with per-cohort z-score
   standardization to surface genuine cross-cohort replication.

## 5. Why Sonnet cannot be dropped in

In principle the pipeline could run with Sonnet 4.6 at every LLM step. It
would fail three measurable ways:

- Ex-ante skeptic tests would be weaker — Sonnet restates the proposer's
  rationale instead of attacking it — so the pre-registration is hollow.
- The housekeeping negative control would not be proactively emitted — Sonnet
  tends to only propose laws it expects to pass.
- Post-hoc review would miss marginal metric patterns (`perm_p` just under
  0.05, `ci_lower` just over 0.6) — Sonnet reports threshold outcomes, not
  metric *patterns*.

Each of these is something the user can verify by running both models through
`opus_client.propose_laws` and diffing the outputs. The Opus 4.7 claim in this
project is not "only Opus can do it" — it is "Opus 4.7 does it correctly
enough that the rest of the pipeline can stay deterministic, which is what
makes the final artifact auditable."
