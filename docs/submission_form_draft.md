# Submission Form Draft

Target constraints per the Cerebral Valley × Anthropic submission form
(inferred from the 4.6 hackathon form structure; confirm at submit time):

| Field | Length cap |
|---|---|
| Project name | 60 characters |
| One-line pitch | 140 characters |
| Project summary | 150 words |
| Claude Opus 4.7 usage | 150 words |
| Claude Managed Agents usage | 150 words |
| Prize category justification | 100 words |
| GitHub link | URL |
| Demo video link | URL |
| Team | name / role / contact |

---

## Project name (60 char)

```
Theory Copilot: Falsification-Aware Biological Law Discovery
```
(60 chars exactly.)

---

## One-line pitch (140 char)

```
Verification-as-skill: Opus 4.7 rediscovers TOP2A-EPAS1, a gate kills 194/204 candidates — then kills our own H1-loop extension too.
```
(140 chars.)

---

## Project summary (150 words, 145 counted)

Theory Copilot is a verification-as-shipped-skill biological discovery
loop powered by Opus 4.7 + Managed Agents (public beta 2026-04-08).
Opus plays Proposer, Skeptic, Interpreter around a deterministic 5-test
Python gate that runs before any LLM judgement. The gate rejected 194
of 204 candidates (95.1%) across 11 task-panel combinations — including
two explicit negative controls. The simplest surviving law is `TOP2A −
EPAS1`, the published ccA-vs-ccB ccRCC subtype axis, rediscovered on
TCGA-KIRC (AUROC 0.726) and replicated on IMmotion150 Phase-2 (n=263,
log-rank p=0.00027, Cox HR 1.36, C-index 0.601, robust to 3-arm
treatment adjustment). When our own H1 LLM-SR loop later proposed a
3-gene extension adding SLC22A8, the same gate killed it on cross-cohort
replay (PhL-1, pre-reg committed before the analysis ran — C-index
dropped to 0.566, HR to 1.16). Pre-registrations are git-tracked YAMLs.
The 194 rejections are the product, not an appendix.

---

## Claude Opus 4.7 usage (150 words, 147 counted)

Four Opus 4.7 calls per loop, all with
`thinking={"type":"adaptive","display":"summarized"}` and
`output_config={"effort":"high"}`. `budget_tokens` is removed on Opus
4.7 (400 error); `effort` is the control. (1) Scientist proposes
three-to-five compact law families and writes the ex-ante skeptic
test for each, before any fit. (2) The pre-registered test is then
executed by plain Python, not by Opus. (3) Skeptic reviews the
specific metric pattern (`perm_p = 0.049` is weaker than `0.001`;
`ci_lower = 0.61` is marginal) and emits PASS / FAIL /
NEEDS_MORE_TESTS with a written justification. (4) Interpreter
writes the mechanism hypothesis and, critically, the "what this is
not" paragraph. Extended thinking is what keeps the Skeptic turn
from collapsing into rubber-stamp agreement with the Proposer turn
— smaller models collapse; Opus 4.7 holds the tension.

---

## Claude Managed Agents usage (150 words, 141 counted)

Three-agent architecture (Proposer / Skeptic / Interpreter = Opus 4.7;
Searcher = local PySR). Structured PASS / FAIL / NEEDS_MORE_TESTS
output. Public-beta compliant per the 2026-04-23 hackathon fairness
rule; research-preview features disabled.

- **Path B — `agent_toolset_20260401`, live-verified.** End-to-end
  trace `results/live_evidence/04_managed_agents_e2e.log` covers
  `agents.create → environments.create → sessions.create → stream →
  send → status_idle`.
- **Path A — sequential chain.** Three Path-B sessions with
  structured-JSON handoff in a shared environment. Agent Teams
  `callable_agents` code path retained as architectural reference,
  env-flag-guarded, not exercised.
- **Path C — Claude Code Routines.** `POST /v1/claude_code/routines/
  {trig_id}/fire` (`routines_client.py`); `--use-routine` flag swaps
  the local watch-dir loop for cloud-triggered execution. Triggers:
  `pull_request`, `release`.

**Durability primitives:** `persist_session_events` pages
`sessions.events.list` to JSONL; `replay_session_from_log` re-injects
user-origin events into a different session — working code, not prose.

All paths return `{session_id, agent_id, output, status}`; Path A adds
`delegation_mode`, Path C adds `routine_session_url`.

---

## Prize category justification (100 words, 98 counted)

**Best Claude Managed Agents ($5K).** Public-beta-only. Three paths:
B (single agent + `agent_toolset_20260401`, live), A (sequential
chain), C (Claude Code Routines `/fire`, local fallback). Plus
**Memory public beta (integrated 2026-04-23, announcement day)**: Skeptic writes rejection lessons to a memory store
in session 1, a fresh session 2 reads and quotes the lesson verbatim
before judging a structurally analogous candidate — the exact
Rakuten "distill lessons from every session" pattern, with
server-side persistence verified via raw `/v1/memory_stores/*` API.
Our own H1 LLM-SR loop's 3-gene extension was killed by the same
gate on cross-cohort replay (PhL-1). Verification as working code.

---

## GitHub

```
https://github.com/jang1563/theory-copilot-falsification
```

Repo is currently private; flipped to public immediately before
submission cutoff per plan.

---

## Demo video

```
[to be pasted on 4/26 morning after Loom render]
```

Script: `docs/loom_script.md` (90 s, six cuts, single terminal +
browser, no overlays). Fallback GIF path documented in the same file
for upload failures.

---

## Broader Program Context (optional, 90 words)

This hackathon artefact is the Opus 4.7-centered proof-of-concept of
a larger research program — **NegBioDB**, a structured database
aggregating ~32.8 million confirmed negative biomedical results
(drug-target inactives, failed clinical trials, protein non-
interactions, non-essential genes, benign variants) paired with
benchmarks for how publication bias propagates into ML/LLM
predictions. Theory Copilot operationalises NegBioDB's core thesis
— that falsification is the expensive, neglected half of
scientific inference — as a runnable Opus 4.7 loop on real
cancer-genomics data.
