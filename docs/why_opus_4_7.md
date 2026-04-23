# Why Opus 4.7

Theory Copilot is an Opus 4.7-centered discovery loop. The work Opus 4.7 does is
deliberately bounded — the statistical falsification gate is plain Python, PySR
runs locally — but the three places where Opus 4.7 *is* load-bearing cannot be
replaced by a smaller model without changing what the artifact claims.

This document is deliberately honest about what Opus does not do.

## 0. Two complementary layers of self-verification

Anthropic's official Opus 4.7 launch (2026-04-16) introduces the model as
one that *"devises ways to verify its own outputs before reporting back."*
That claim is load-bearing — it's the first capability the launch blog
cites, ahead of any benchmark number.

Theory Copilot's architecture is **complementary** to that native
model-level claim, not an instantiation of it. The two layers address
different failure modes of AI-for-Science:

- **Model-level (native to 4.7):** abstention on unknowns tightened
  from 61% incorrect (Opus 4.6 adaptive) to 36% (Opus 4.7 adaptive),
  accuracy ~constant [Opus 4.7 model card, 2026-04-16]. This is a
  calibration of the model's *own judgement*, without external
  reference.
- **Pipeline-level (this repo):** the 5-test falsification gate is
  deterministic Python that the model cannot rationalise past. It
  works **regardless of which frontier model is in the Skeptic role**
  (empirically tested with Opus 4.6 and 4.7 at n=60 each in
  `results/ablation/opus_46_vs_47/`).

The empirical comparison in G6 shows:
- **Strict miscalibration** (FAIL-on-PASS / PASS-on-FAIL): both models
  0.0%. Neither commits this type of error on our corpus. The gate's
  value here is independent of model choice.
- **Verdict confidence distribution:** Opus 4.7 is more decisive on
  unambiguous survivors (`TOP2A − EPAS1`: PASS 10/10 vs 4.6's PASS
  7/10) and more abstentive on a stress-test case (5-gene compound:
  `NEEDS_MORE_TESTS` 10/10 vs 4.6's 8/10 + **PASS 2/10, an
  over-commitment 4.7 never makes**). This is the *qualitative shape*
  of Anthropic's 61→36% delta, detectable inside the set of
  "not-wrong" answers.

Concretely: the gate makes the pipeline auditable to a reviewer who
does not trust any specific model. Opus 4.7's calibration makes the
*interior* of the pipeline (the Skeptic's graded {PASS, FAIL,
NEEDS_MORE_TESTS} choice) better aligned with the evidence. The two
are independently load-bearing — dropping either degrades a
different reviewer's trust.

## 1. The problem: confirmation bias is automated now

> *A loop that cannot reject is not a loop — it is a pipeline.*

Most AI-for-Science systems today are pipelines dressed as loops. A model
proposes a hypothesis, runs a fit, observes a number that looks good, and
ships the number as a finding. Nothing in that sequence is adversarial. The
model that generates the hypothesis is also the judge of whether the
hypothesis survives, and it is rewarded for agreement.

The older version of this failure mode was a human researcher p-hacking
one dataset. The newer version is faster — an LLM generates forty plausible
hypotheses, runs them all, and surfaces whichever one clears an arbitrary
threshold on one split. **This is p-hacking at computational speed.** The
search space is wide enough that a high AUROC on a single cohort is nearly
free, and confirmation bias moves from a time-limited failure of individual
scientists to a cheap, scalable pipeline output. The empirical record
already shows the cost: Sakana's AI Scientist v2 ([arXiv 2504.08066](https://arxiv.org/abs/2504.08066))
had 42% of its proposed experiments fail on coding errors alone, and
several of its "novel" ideas were rediscoveries of well-known techniques;
the 2025 LLM-hacking survey ([arXiv 2509.08825](https://arxiv.org/abs/2509.08825))
measures a 31% false-conclusion rate across 13M machine-generated labels
used as downstream evidence.

The remedy biology keeps pointing back to is pre-registration: write down
what would falsify the claim *before* seeing whether it passes. Theory
Copilot takes that seriously. Every law family is paired with skeptic
tests that Opus 4.7 writes **before any fit is attempted**; the law must
survive those tests as a condition for being called a survivor; the tests
are executed by plain Python against held-out data, not by another LLM
call that could also rationalise its way to agreement. The system
**selects for truth, not self-consistency** — every candidate must
survive contact with pre-specified experimental reality before it is
reported.

This is what distinguishes an agentic loop from an agentic pipeline. The
three structural requirements ([Karpathy autoresearch, 2026-03](https://karpathy.ai/posts/2026-03-autoresearch):
630-line harness, 700 autonomous experiments, 11% benchmark improvement)
are: (1) **measurable output**, (2) **pre-specified judgment function**,
(3) **machine-executable falsification — no human decides whether the
result is good enough; the comparison is automatic and deterministic.**
Theory Copilot's three analogues: (1) H1 LLM-SR loop convergence on
held-out AUROC + Δ-baseline lift, (2) the 5-test gate thresholds
committed in `src/theory_copilot/falsification.py` and the YAMLs in
`preregistrations/` before any analysis ran, (3) `make audit` + `make
test` re-runnable by any reviewer without a human call.

Karpathy's autoresearch judgment function is training loss — continuous
but ungrounded. Theory Copilot's judgment function is a pre-registered
statistical gate on independent biology — binary and experimentally
grounded. Same loop shape, different truth conditions. That is the move
biology needs.

This rigor framing matches the NeurIPS 2025 AI4Science workshop *"[The Reach and Limits of AI for Scientific Discovery](https://ai4sciencecommunity.github.io/neurips25.html)"* call and has been named publicly by the Claude Code team as the desired product-development stance. At the 2026-04-22 *Built with Opus 4.7* live session (Tharik, Cloud Code team), the recommendation was:

> "Have conviction... trying to **disprove it** versus trying to test a bunch of different hypotheses."

Theory Copilot ports that epistemic posture from product development into scientific discovery itself: Opus 4.7 proposes a law *and writes the test that would kill it*, then a deterministic gate runs the kill test, then Opus 4.7 interprets only what the gate failed to reject. The same-session Q&A also confirmed that "a verification script that forces the agent to test its own outputs against hard constraints" is an open problem the Cloud Code team intends to write a post about. This repository is a worked example of that script.

The same pattern was described the following day by Michael Cohen (Anthropic technical staff) at the 2026-04-23 *Claude Managed Agents* live session as the intended shape of the upcoming `outcomes` research-preview feature:

> *"It is effectively a self-verification loop... in order for you to think of this task as done, these things have to be true."*

Our pre-registered 5-test gate is exactly that shape — a plain-text rubric (five statistical thresholds committed before the fit) plus a boolean pass/fail that the model cannot re-negotiate — shipping as plain Python months before `outcomes` releases. What Michael described as a forthcoming primitive, the falsification pipeline already instantiates.

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

The researcher's role has shifted from *implementer* (writing code to test
hypotheses) to *orchestrator* (specifying judgment criteria and letting
agents iterate). In that framing, the single most important design
decision is not the architecture of the agent but the specification of
the judgment function: **what counts as better?** Opus 4.7 is Theory
Copilot's orchestrator — it proposes law families, writes the kill-tests
that would falsify each, and interprets survivors — but it does not
decide pass/fail. The deterministic gate decides. This is the direct
counter to the class of failure mode where an LLM-as-judge, trained on
data that shaped what "good science" looks like, silently optimises for
paper-acceptance probability rather than empirical truth. Our gate is
not LLM-judged. Opus proposes; the gate disposes. Opus cannot
re-negotiate the criterion mid-run.

Three places where the orchestrator role concretely needs Opus 4.7,
each measurable rather than stylistic.

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
survived." Opus does not run the falsification. What it does show is
the gate accepting and rejecting in complementary patterns on the
same infrastructure, with Opus 4.7 in the Proposer, Skeptic, and
Interpreter roles at the points where LLM judgement is load-bearing.

The *durability* axis of the demo is carried by Managed Agents +
Routines, which are **two separate products** that we compose here
for the first time (to our knowledge): Managed Agents give us a
session event log that persists server-side, surviving harness
crashes — `persist_session_events` dumps it to JSONL and
`replay_session_from_log` re-injects client-originated events into a
fresh session, literally decoupling the "brain" (event log) from the
"body" (session container). Claude Code Routines (beta header
`experimental-cc-routine-2026-04-01`) give us a trigger surface —
GitHub `pull_request` / `release` events, scheduled cron (min 1 h),
or API `/fire` — so the falsification gate runs on every proposed
change without a human hitting a button. Managed Agents lives on
`platform.claude.com`, Routines lives on `code.claude.com`; bridging
them is an architectural seam most implementations conflate.

**What the event log actually preserves** (empirically verified
2026-04-23 via `src/phk_events_list_thinking_probe.py`, see
`results/overhang/phk_events_list_probe/SUMMARY.md`):

- ✅ Every `agent.message` is retrievable via `events.list` with full
  content (up to 3.7k output tokens observed), including any
  step-by-step reasoning the model chooses to write out.
- ✅ `agent.thinking` events fire with server-attested
  `processed_at` timestamps, giving an auditable ordering: *thinking
  happened at T, output at T+Δ*.
- ❌ The intermediate thinking TOKENS themselves are NOT in the event
  payload — `agent.thinking` serialises to `{id, processed_at, type}`
  only. Adaptive-thinking content drops after the turn completes.

So the durable log is a *conclusions-and-output substrate* with
attested timing, not a *reasoning-trace substrate*. Our 1M-context
synthesis (`src/opus_1m_synthesis.py`) operates on the former — it
ingests rejection records and survivor equations, not prior thinking
tokens — so the architecture stands. This scoping is stated here to
avoid a narrow overclaim that other entries might accidentally make.

**Hackathon fairness caveat (2026-04-23).** Anthropic restricts
participants to public-beta Managed Agents features; Agent Teams
(`callable_agents` multi-agent coordination, research preview) is not
used in the submitted run. Path A in our code executes as a sequential
public-beta chain; the `_run_path_a_callable_agents` branch is an
architectural reference that activates the day the research-preview
opens to this workspace.

### The reject cycle (four tasks × 11-gene panel)

1. Opus 4.7 proposes 5-7 KIRC law families for each task (pathway-
   grounded + single-gene anchor + at least one housekeeping negative
   control) and writes the ex-ante skeptic test for each.
2. PySR searches the space with `variable_names=gene_cols` so the
   returned equations read in biological names.
3. The 5-test gate (permutation, bootstrap, sign-invariant baseline,
   incremental confound, decoy-feature null) runs on TCGA-KIRC
   tumor-vs-normal / stage / 5-yr survival / metastasis with BH-FDR
   across candidates.
4. **100+ candidates are rejected** across the four tasks, including
   the textbook HIF-axis law `log1p(CA9) + log1p(VEGFA) − log1p(AGXT)`
   (AUROC 0.984, fails because CA9 alone reaches 0.965). Both the
   Opus-planted negative controls *and* the Opus-proposed pathway
   laws fail on the same threshold. The gate is not sparing its own
   side.

### The accept cycle (metastasis × 45-gene expanded panel)

5. The Proposer is re-run with a 45-gene expanded panel that adds
   proliferation markers (`TOP2A`, `MKI67`, `CDK1`, `CCNB1`, `TOP2A`,
   `PCNA`, `MCM2`), HIF-2α and related hypoxia partners (`EPAS1`,
   `BHLHE40`, `DDIT4`, `PGK1`), Warburg-expanded metabolism, and
   metastasis / EMT markers on top of the original 11 genes.
6. PySR emits 30 candidates; **9 pass the same pre-registered
   5-test gate** on M0-vs-M1 with `delta_baseline` up to +0.069.
7. The simplest surviving law is `TOP2A − EPAS1` — proliferation
   minus HIF-2α — which reproduces the published ccA-vs-ccB ccRCC
   subtype axis without being seeded with it.
8. Opus 4.7 in the Interpreter role then writes the mechanism
   hypothesis, the testable downstream prediction, and — critically
   — the "what this is *not*" paragraph: not a diagnostic biomarker,
   not novel biology, not dramatically superior to a 2-gene LR with
   interaction (that baseline reaches AUROC 0.722 on the same pair).

The shock moment is not one clip. It is the *pair* of outcomes on
one pipeline: the gate kills the textbook law the user wrote on task
1, and the gate accepts the subtype axis the user did not write on
task 4. Pre-registered falsification is doing both jobs.

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
