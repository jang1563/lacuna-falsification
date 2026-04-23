# Theory Copilot — Submission Description

## Project Summary

**Theory Copilot is a verification-first discovery pipeline — the
agent kills its own best guesses, including ones it generates downstream,
when independent data says no.** On real cancer data the pipeline rejected
194 of its own 204 hypotheses; on cross-cohort replay it then rejected one
of the 10 accepted ones' own H1-loop-proposed extensions. Our own output,
killed by our own gate on data it had never seen.

Powered by Opus 4.7, Opus plays three roles around a deterministic
statistical gate: a Scientist that proposes compact symbolic law
families (with pathway-level rationale and an ex-ante negative
control), a Skeptic that reviews each candidate's metric pattern
after the gate has run, and an Interpreter that writes a mechanism
hypothesis for the survivors. The gate itself — two-sided permutation
null, bootstrap CI lower bound, sign-invariant single-feature
baseline, incremental covariate confound, decoy-feature null, with
Benjamini-Hochberg FDR across candidates — is plain Python, so Opus
4.7 cannot rationalize its own proposals into passing. The Skeptic
runs as a sub-agent with isolated context; the 5-test gate is the
shareable verification pattern; `make audit` + pre-registration
YAMLs form the Stop hook that refuses to mark a task complete
without proving it works.

At the 2026-04-23 *Claude Managed Agents* live session, Michael
Cohen (Anthropic technical staff) described the upcoming `outcomes`
research-preview feature as *"effectively a self-verification loop"*
with plain-text rubrics stating *"in order for you to think of this
task as done, these things have to be true."* Our pre-registered
5-test gate is that shape, already shipping as working Python —
before `outcomes` releases.

Applied to real TCGA-KIRC, the gate rejects 100+ candidates across
tumor-vs-normal, stage, and survival tasks on an 11-gene HIF-axis
panel (each task is saturated by a single gene; compound laws cannot
clear the pre-registered +0.05 `delta_baseline` threshold). On a
45-gene expanded panel the same gate accepts 9 / 30 candidates on
metastasis, centred on **`TOP2A − EPAS1`** — proliferation minus
HIF-2α — which reproduces the published ccA-vs-ccB ccRCC subtype
axis from unconstrained symbolic regression, without being seeded
with it. What gets reported is only what the gate failed to reject,
and the accept-reject pair on the same infrastructure is the
artifact.

## Opus 4.7 Usage

- **Extended thinking** via `thinking={"type": "adaptive",
  "display": "summarized"}` plus `output_config={"effort": "high"}`
  on every Scientist / Skeptic / Interpreter call. `budget_tokens`
  removed (400 on Opus 4.7); `effort` is the control knob.
- **Multi-role adversarial reasoning.** The same model authors both
  the proposal and the ex-ante skeptic test, then writes the
  post-hoc review of the statistical gate's verdict, then writes the
  mechanism interpretation of the survivor — four Opus 4.7 calls
  around one deterministic gate.
- **Multi-step discovery loop.** Proposal → Search → Falsification
  → Survivor → Replay. The Proposer's output is the Skeptic's
  input; the Skeptic's per-metric critique is the Interpreter's
  input; the Interpreter's hypothesis is replayed on the held-out
  test split (and, where possible, an independent cohort).

Live transcripts of all four roles at `results/live_evidence/`.

## Claude Managed Agents Usage

- **Three-agent architecture:** `Proposer` (Opus 4.7, extended
  thinking), `Searcher` (local PySR, no API), `Falsifier` (Opus 4.7,
  extended thinking). Clean role separation, structured
  PASS / FAIL / NEEDS_MORE_TESTS verdicts.
- **Path B — public-beta, fully implemented and live-verified.**
  A single Managed Agent with `agent_toolset_20260401` drives the
  Night-2 / Night-3 / Night-4 tasks via structured tool calls. End-
  to-end verification at
  `results/live_evidence/04_managed_agents_e2e.log`
  (`agents.create` → `environments.create` → `sessions.create` →
  `stream` → `send` → `session.status_idle`).
- **Path A — sequential falsification chain.** Per the hackathon fairness
  rule (2026-04-23, Anthropic: Agent Teams / `callable_agents` multi-agent
  research-preview access is disabled for participants, only public-beta
  features are evaluated), Path A runs three sequential Managed Agents
  sessions (Proposer → Searcher → Skeptic) with structured-JSON handoff in
  a shared environment. This is NOT the `callable_agents` multi-agent
  primitive; it is a client-side orchestration of three public-beta Path
  B sessions. The orchestrator-with-`callable_agents` shape is kept in the
  code (`run_path_a` waitlist-gated branch) as an architectural reference
  that becomes live the day the research-preview opens, but is not
  exercised in the submitted run.
- **Path C — Claude Code Routines (separate product).** `POST
  /v1/claude_code/routines/{trig_id}/fire` with per-routine bearer
  token (`src/theory_copilot/routines_client.py`). GitHub trigger
  categories: `pull_request` + `release`. Local watch-dir / cadence
  loop runs when no token is configured, so the replication watchdog
  ships regardless of whether the Routines research preview is
  available to the reviewer's account.
- **Durability:** `persist_session_events` pages `sessions.events.list`
  into JSONL; `replay_session_from_log` re-injects user-origin events
  into a different session. Brain/body decoupling as a working
  primitive, not prose.

## External Validation of the Problem Framing

At the 2026-04-22 *Built with Opus 4.7* live session, Tharik (Cloud Code team) named "a verification script that forces the agent to test its own outputs against hard constraints before it sends the payload" as an open community problem on Opus 4.7 — serious enough that he proposed writing a follow-up article on it. The same session's stated development posture was "trying to **disprove it** versus trying to test a bunch of different hypotheses." Theory Copilot is a worked example of exactly that script, ported from product development into scientific discovery: a pre-registered deterministic gate that the proposing model itself cannot rationalize past. This is not a coincidence of framing — the falsification-first loop was built to solve the confirmation-bias-automation problem that the Cloud Code team publicly flagged the same week.

## Prize Category Justification

- **Keep Thinking ($5K).** The load-bearing cognitive work is the
  ex-ante skeptic test written before any fit, the four-role review
  loop, and the post-hoc metric-pattern interpretation. All three
  require the Skeptic stance to survive against the model's own
  Proposer output. Smaller models collapse to rubber-stamp
  agreement on the Skeptic turn. Adaptive thinking with
  `effort=high` is what keeps the tension live long enough to emit
  a dissent or a well-defended PASS.
- **Best Claude Managed Agents ($5K).** Explicit multi-agent
  delegation with biological domain specialization per agent
  (Proposer knows pathway biology, Searcher knows symbolic
  regression, Falsifier knows statistics). Both delegation paths
  implemented against the verified 2026-04-01 API. Path B runs
  live; Path A is one flag-flip away.

## What We Built

- `src/theory_copilot/falsification.py` — 5-test statistical gate.
- `src/theory_copilot/opus_client.py` — three-role Opus 4.7 wrapper
  with adaptive thinking, JSON-fence-tolerant parser, cost ledger.
- `src/theory_copilot/managed_agent_runner.py` — Path A + Path B.
- `src/theory_copilot/cli.py` — `theory-copilot compare` + `replay`.
- `src/pysr_sweep.py` — PySR 1.5.9 sweep with law-family injection,
  train/test split, novelty scoring.
- `src/falsification_sweep.py` — BH-FDR batch falsification.
- `src/track_a_survivor_robustness.py` — Sci-B methodology applied
  to the survivor (6 axes + 5-fold CV).
- Track B robustness scripts (`src/gate_sensitivity.py`,
  `src/track_b_*.py`) — 6-axis stress test of the reject verdict.
- Opus-proposed `config/law_proposals.json` (14 law family templates,
  7 for KIRC + 2 ex-ante negative controls) used to seed PySR.
- Real public data pipeline: TCGA-KIRC (GDC star_tpm, 609 samples,
  with 11-gene and 45-gene derivatives) + GSE40435 (microarray,
  202 paired samples).
- Offline synthetic-data test suite so the pipeline reproduces
  without API credentials.

## Technical Novelty

Most AI-for-Science pipelines optimize for hit rate: propose, fit,
report whatever cleared a threshold. Theory Copilot inverts the
incentive — a proposal only counts if a pre-registered five-test
gate fails to reject it, and the thresholds are written down before
any fit. Confirmation bias is engineered out of the loop rather
than hoped against. The Managed Agents implementation enforces this
at the architecture level by making the Scientist, Searcher, and
Falsifier literally separate agents with separate system prompts —
Opus 4.7 cannot let a proposal pass by rephrasing its defence.

The twin outcome on the same infrastructure — the gate rejecting
textbook HIF-axis biology (`log1p(CA9) + log1p(VEGFA) − log1p(AGXT)`
fails on tumor-vs-normal because CA9 alone saturates at AUROC
0.965) and the gate accepting an unseen compact law
(`TOP2A − EPAS1` on metastasis, AUROC 0.726, `Δbase = +0.069`, cluster
of 9 survivors reading as the published ccA/ccB subtype axis) — is
the artifact. Both outcomes are reproducible end-to-end from the
committed data + `make audit` + `make test` + `make demo-kirc`.

## Broader Program Context

This hackathon artifact is the Opus 4.7-centered proof-of-concept of
a larger research program — **NegBioDB**, a structured database
aggregating ~32.8 million confirmed negative biomedical results
(drug–target inactives, failed clinical trials, protein non-
interactions, non-essential genes, benign variants) paired with
benchmarks for how publication bias propagates into ML / LLM
predictions. Theory Copilot operationalizes NegBioDB's core thesis
— that falsification is the expensive, neglected half of scientific
inference — as a runnable Opus 4.7 loop on real cancer-genomics data.
