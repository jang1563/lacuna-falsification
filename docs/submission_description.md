# Theory Copilot — Submission Description

## Project Summary

Theory Copilot is a falsification-first biological discovery loop powered
by Opus 4.7. The model plays two opposed roles against itself: a
Scientist that proposes compact symbolic law families (with pathway-level
rationale), then a Skeptic that attempts to falsify each proposal via a
pre-registered 5-test statistical gate (two-sided permutation null, bootstrap
stability, best-single-feature baseline, incremental covariate confound, and
a decoy-feature null), plus an ex-ante negative-control family from the
Proposal stage. Candidates that survive are replayed on an independent
cohort (TCGA-KIRC flagship → GSE40435 validation). What gets reported is
only what Opus 4.7 failed to falsify. The result is a discovery artifact
where confirmation bias is engineered out of the loop rather than hoped
against, and where the surviving law is automatically a cross-cohort
replication rather than a within-cohort fit.

## Opus 4.7 Usage

- **Extended thinking** via `thinking={"type": "adaptive",
  "display": "summarized"}` plus `output_config={"effort": "high"}` on
  every Scientist/Skeptic/Interpreter call.
- **Dual-role adversarial reasoning:** the same model that authored
  each proposal writes the attacks against it, and the pre-registered
  statistical gate enforces that the attacks are honest.
- **Multi-step discovery loop** across five stages: Proposal → Search
  → Falsification → Survivor → Replay. The Proposer's output is the
  Skeptic's input; the Skeptic's surviving verdict is the
  Interpreter's input; the Interpreter's hypothesis is replayed on
  GSE40435.

## Claude Managed Agents Usage

- **Three-agent architecture:** `Proposer` (Opus 4.7, extended
  thinking), `Searcher` (local PySR — no API), `Falsifier` (Opus 4.7,
  extended thinking). Each agent has a distinct system prompt and a
  single role.
- **Path B — fully implemented and tested.** Single agent with the
  public-beta `agent_toolset_20260401` drives the pipeline via
  structured tool calls. This is what the demo runs on.
- **Path A — implemented, gated on waitlist.** Parent agent uses
  `callable_agents` to delegate to Proposer and Falsifier subagents.
  Guarded behind a feature flag; flips on when Managed Agents
  multiagent research-preview access is granted.

## Prize Category Justification

- **Keep Thinking ($5K).** Opus 4.7 extended thinking is the core
  reasoning engine, not a feature we toggled. The Skeptic role
  requires the model to hold a proposal and simultaneously argue
  against it across a long adversarial trajectory — a task smaller
  models collapse to rubber-stamp agreement on. Adaptive thinking
  with `effort=high` is what makes the dual Scientist/Skeptic tension
  hold.
- **Best Claude Managed Agents ($5K).** Explicit multi-agent
  delegation with biological domain specialization per agent:
  Proposer knows pathway biology, Searcher knows symbolic regression,
  Falsifier knows statistics. Both delegation paths (callable_agents
  + single agent tool loop) are implemented against the verified
  2026-04-01 API, with clean role separation and structured
  PASS/FAIL/NEEDS_MORE_TESTS verdicts.

## What We Built

- `src/theory_copilot/falsification.py` — 5-test statistical
  falsification gate (two-sided permutation null, bootstrap stability,
  sign-invariant single-feature baseline, incremental covariate confound,
  decoy-feature null) plus explicit fail-reason reporting.
- `src/theory_copilot/opus_client.py` — Opus 4.7 three-role wrapper
  (Scientist / Skeptic / Interpreter) with adaptive thinking and
  `effort=high`.
- `src/theory_copilot/managed_agent_runner.py` — Managed Agents
  Path A (callable_agents) + Path B (public-beta single agent tool
  loop).
- `scripts/pysr_sweep.py` — PySR v1.5.9 symbolic regression with
  law-family injection via `guesses=` and
  `fraction_replaced_guesses=0.3`.
- `scripts/falsification_sweep.py` — Benjamini-Hochberg FDR-corrected
  batch falsification over candidate equations.
- `src/theory_copilot/visualize.py` — separation histogram +
  falsification panel for the surviving law.
- `config/law_proposals.json` — KIRC-first law family proposals
  with biological rationale, initial guesses, and at least one negative control.
- Offline synthetic-data tests under `tests/` so the full pipeline
  runs reproducibly without an API key.

## Technical Novelty

Most AI-for-Science pipelines optimize for hit rate: propose, fit,
report whatever cleared a threshold. Theory Copilot inverts the
incentive — a proposal only counts if the same model, switching to
Skeptic role, *failed* to break it against a pre-registered gate, and
the survivor replays on a fully independent cohort. Confirmation bias
is engineered out, not hoped against. The Managed Agents
implementation enforces this at the architecture level by making the
Scientist and Skeptic literally separate agents with separate system
prompts.

## Broader Program Context

This hackathon artifact is the Opus 4.7-centered proof-of-concept of a
larger research program — **NegBioDB**, a structured database aggregating
~32.8 million confirmed negative biomedical results (drug–target
inactives, failed clinical trials, protein non-interactions, non-essential
genes, benign variants) paired with benchmarks quantifying how publication
bias propagates into ML/LLM predictions. Theory Copilot operationalizes
NegBioDB's core thesis — that falsification is the expensive, neglected
half of scientific inference — as a runnable Opus 4.7 loop on real
cancer-genomics data. The public-facing NegBioDB repository will be
linked from this README at release; until then, this artifact stands on
its own.
