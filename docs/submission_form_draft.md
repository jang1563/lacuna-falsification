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
AI for Science that says no: pre-registered gate rejects 194 of 203 cancer laws, Opus 4.7's own included. Survivor validates cross-cohort.
```
(139 chars.)

---

## Project summary (150 words, 137 counted)

AI-for-Science tools accelerate hypothesis generation — not rejection.
Theory Copilot is the rejection step. Opus 4.7 plays Proposer (emits
compact cancer-law families and the kill-test for each, before any
fit), Skeptic (reviews gate output — never the Proposer's reasoning),
and Interpreter (explains only what the gate failed to reject). On
TCGA-KIRC (n=505), the gate rejected 194 of 203 candidate evaluations
across 11 task-panel combinations. The simplest survivor — `TOP2A −
EPAS1`, the published ccA/ccB ccRCC subtype axis — was rediscovered
by PySR without being seeded. A separately pre-registered survival gate
on IMmotion150 Phase-2 (n=263) confirmed it: log-rank p=0.0003,
HR=1.36, C-index 0.601, robust to treatment adjustment. Our own
LLM-SR loop then proposed a 3-gene extension; same survival gate killed
it (PhL-1, C-index dropped to 0.566). Pre-registrations are
git-tracked YAMLs.

---

## Claude Opus 4.7 usage (150 words, 125 counted)

Four Opus 4.7 calls per loop with
`thinking={"type":"adaptive","display":"summarized"}` and
`output_config={"effort":"high"}`. (1) Proposer emits 3-5 compact law
families and the ex-ante skeptic test for each, before any fit. (2)
The test is executed by plain Python, not Opus. (3) Skeptic reviews
the specific metric pattern (`perm_p=0.049` is weaker than `0.001`;
`ci_lower=0.61` is marginal) and emits PASS / FAIL / NEEDS_MORE_TESTS.
(4) Interpreter writes the mechanism hypothesis and the "what this is
not" paragraph. Adaptive thinking keeps the Skeptic turn from
collapsing across the dual-role prompt: in our 180-call ablation,
Sonnet 4.6 emits **0 PASS of 60** on gate-PASS candidates (full dissent
collapse); Opus 4.7 emits **10 of 60**. **PhL-13 memorization audit:
Opus 4.7 does not retrieve TOP2A−EPAS1 zero-shot (0/10 repeats) —
refutes the LLM-SRBench memorization concern.**

---

## Claude Managed Agents usage (150 words, 127 counted)

**Verification-isolated Managed Agents orchestration.** Three separate
public-beta sessions (Proposer / Skeptic / Interpreter = Opus 4.7;
Searcher = local PySR) with separate context windows and structured-
JSON handoff — the Skeptic never sees the Proposer's reasoning tokens,
so it cannot rationalise its own proposal into passing. Public-beta
compliant per the 2026-04-23 hackathon fairness rule; research-preview
`callable_agents` disabled.

- **Path B (live).** Single-agent `agent_toolset_20260401`; end-to-end
  `agents.create → environments.create → sessions.create → stream →
  send → status_idle` at `04_managed_agents_e2e.log`.
- **Path A (live, PhL-9 + PhL-9v2 on real TCGA-KIRC).** Sequential
  three-session chain, structured-JSON handoff,
  `delegation_mode=sequential_fallback`, 706 s wall.
- **Path C (live, PhL-8).** `/fire` HTTP 200 +
  https://claude.ai/code/session_01NyS541H3qZfJgqFVgWDcoM

**Durability.** `persist_session_events` pages `sessions.events.list`
to JSONL; `replay_session_from_log` re-injects user-origin events into
a different session — any reviewer can replay the run end-to-end.

---

## Prize category justification (100 words, 95 counted)

**Best Claude Managed Agents.** Public-beta-only. Three paths: B
(live), A (PhL-9 sequential 3-session + PhL-9v2 on real TCGA-KIRC),
C (PhL-8 `/fire` HTTP 200). Plus **Memory public beta (integrated
2026-04-23 day-of)**: Skeptic writes rejection lessons; fresh
sessions read, quote, and refine them. PhL-10 + PhL-12 grow the chain
to 8 entries with the ceiling-effect rule generalizing KIRC→LUAD→PRAD.
Server-side persistence verified via raw `/v1/memory_stores/*` API.
Our own H1 LLM-SR extension was killed by the separately pre-registered
IMmotion150 survival replay (PhL-1, not the TCGA classification gate).
Verification as working code.

---

## GitHub

```
https://github.com/jang1563/theory-copilot-falsification
```

Repo has been public since 2026-04-23 19:32 ET.

---

## Demo video

```
[to be pasted on 4/26 morning after Loom render]
```

Canonical narration: `docs/loom_narration_final_90s.md` (254 words,
~109 s at 140 WPM / ~127 s at 120 WPM, seven segments incl. DIPG
generalization tag, opens with problem-first "AI-for-science... built
to say no" hook + published-ccA/ccB-axis unprompted-rediscovery citation).
Shot-list / rehearsal assets: `docs/loom_script.md` (pre-narration
shot list, 6 cuts, single terminal + browser, no overlays).

---

## Broader Program Context (optional, 90 words)

Opus 4.7 proof-of-concept of a larger program (NegBioDB + failure
network + rescue engine for prematurely-rejected clinical hypotheses).
Same 4-role engine re-run on 15 pre-registered H3 K27M diffuse midline
glioma rescue hypotheses (git SHA 8a4ecc5, locked before engine output):
7 supported, 7 mixed, 1 insufficient. Top lead: CED-delivered MTX110
panobinostat in H3 K27M+ DIPG — the pharmacokinetic-not-pharmacodynamic
rescue of PBTC-047 failure — aggregate score 13/15, delivery class.
Deployment pathway with Dr. Mark Souweidane, pioneer of convection-enhanced delivery for pediatric brain tumors. Research-
grade hypotheses; prospective validation required.
