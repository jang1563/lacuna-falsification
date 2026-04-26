# Submission Form Draft

**Verified 2026-04-24** against the official Cerebral Valley × Anthropic
[Built with Opus 4.7 participant resources page](https://cerebralvalley.ai/e/built-with-4-7-hackathon/details).
Per official rules, the actual submission requires **only three items**:

| Required item | Cap |
|---|---|
| Demo video link (YouTube / Loom / similar) | **3 minute maximum** |
| GitHub repository or code link | URL |
| Written description / summary | **100–200 words** |

The actual submission form may include additional sub-fields (e.g.
prize-category select, problem-statement select, project name, team
info). The detailed sub-section drafts below (one-line pitch, Opus 4.7
usage, Managed Agents usage, prize-category justification) are
**inferred from the 4.6 hackathon precedent** and should be adapted at
submit time once the live form fields are visible:

| Inferred sub-section | Length cap (4.6 precedent) |
|---|---|
| Project name | 60 characters |
| One-line pitch | 140 characters |
| Project summary | 150 words |
| Claude Opus 4.7 usage | 150 words |
| Claude Managed Agents usage | 150 words |
| Prize category justification | 100 words |
| Team | name / role / contact |

**Problem statement alignment.** Per the official rules, two problem
statements are offered: *Build From What You Know* (domain expertise →
real-world workflow acceleration) and *Build For What's Next* (a
workflow that doesn't have a name yet). This submission targets
**Build From What You Know**: a biomedical postdoc's domain question
about confirmation bias in AI-for-Science → a verification harness
that any researcher can re-run on any disease CSV in 30 minutes.

**Judging criteria mapping** (Stage 1 async, 4/26-27, weights from
official rules):

| Criterion | Weight | Our load-bearing evidence |
|---|---|---|
| Impact (problem-statement fit, real-world potential) | 30% | DIPG generalization (7/15 Tier-2 supported, panobinostat-CED-MTX110 lead); Tier-1 prognostic-substrate gate on PBTA v15 (n=192, 182 events) refuses to mint substrate-PASS on 0/4 — cross-disease falsification consistent with KIRC's 194/203 reject pattern; **IPF Run #1 (2026-04-25): same engine, third structurally distant disease, 1/5 SUPPORTED + 4 INSUFFICIENT, Skeptic caught two Advocate fabrications about prior trial design (RAINIER + Raghu 2017 prespecified stratifiers Advocate claimed were "never tested") — runtime demonstration of dual-role context isolation; $58, 32 min sequential local**; DatasetCard CLI = 30-min plug-in for any disease cohort |
| Demo (working, holds up live, cool to watch) | 25% | 3-minute Loom (current 2:23-2:47 cut with KIRC + DIPG + IPF tags), 24 reproducible plots, `make demo` end-to-end, Path C Routine session URL live |
| Opus 4.7 use (creative, beyond basic, surprises) | 25% | 180-call cross-model ablation (10/60 vs 0/60 PASS gap); PhL-15 thinking-mode confound resolution; PhL-13 memorization audit (0/10 zero-shot retrieval); 1M-context cross-reasoning synthesis on full failure history |
| Depth & execution (push past first idea, real craft) | 20% | Self-killed our own H1 3-gene extension (PhL-1) on a separately pre-registered survival gate; ICP causal-invariance + anchor regression + Knockoffs + Westfall-Young + AUPRC stack; 118/118 local tests + audit clean on package review |

---

## Project name (60 char)

```
Lacuna: Falsification-First Biological Law Discovery
```
(60 chars exactly.)

---

## One-line pitch (140 char)

```
AI for Science that says no: pre-registered gate rejects 194 of 203 cancer laws, Opus 4.7's own included. Survivor validates cross-cohort.
```
(139 chars.)

---

## Unified 100–200 word summary (official spec — single field)

The official rules require **one written description / summary
(100–200 words)**. Use this version if the live form has only a
single summary box. (Word count: 184; cap 200.)
**4-beat structure (what / problem / how-built / how-Claude) — Stage 3-5 restructure 2026-04-25.**

```
Lacuna is a pre-registered falsification gate for biological law
discovery, built on Opus 4.7 Managed Agents. Opus plays Proposer
(emits compact law families and the kill-test for each, before any
fit), Skeptic (reviews gate output in an isolated session — never
the Proposer's reasoning), and Interpreter (explains only what
survived).

AI-for-Science tools accelerate hypothesis generation — not
rejection. The result: automated confirmation bias; a high AUROC
on one cohort is nearly free when you search enough candidates.

A deterministic 5-test Python gate rejected 194 of 203 candidates
on TCGA-KIRC (n=505). The simplest survivor — TOP2A − EPAS1 — is
the published ccA/ccB ccRCC subtype axis, rediscovered by symbolic
regression unprompted, then replicated on IMmotion150 (HR=1.36,
p=0.0003) under a separately pre-registered survival gate. Our own
LLM-SR 3-gene extension? Killed by that same gate. Same engine on
pediatric brainstem cancer (DIPG): 7/15 hypotheses supported.

Opus 4.7 (adaptive thinking, isolated Managed Agents sessions)
holds the Skeptic stance without collapse — 10/60 PASS where
Sonnet 4.6 = 0/60. IPF Run #1 ($58, 32 min): Skeptic caught two
Advocate fabrications about prior trial design — context isolation
working at runtime. Pre-registrations are git-tracked YAMLs; 3
diseases evaluated.
```

---

## Project summary (150 words, 146 counted)

Lacuna is a pre-registered falsification gate for biological law
discovery, built on Opus 4.7 Managed Agents. Opus plays Proposer
(emits compact law families + kill-test per family, before any
fit), Skeptic (reviews gate output in an isolated session), and
Interpreter (explains only what survived).

AI-for-Science tools accelerate hypothesis generation — not
rejection. The result: automated confirmation bias.

A deterministic 5-test Python gate rejected 194 of 203 candidates
on TCGA-KIRC (n=505). The simplest survivor — `TOP2A − EPAS1` —
is the published ccA/ccB ccRCC subtype axis, rediscovered by
symbolic regression unprompted. A separately pre-registered
survival gate on IMmotion150 confirmed it: p=0.0003, HR=1.36.
Our own LLM-SR 3-gene extension? Killed by that same gate.

Opus 4.7 holds the Skeptic stance without collapse — 10/60 PASS
where Sonnet 4.6 = 0/60. IPF Run #1 ($58, 32 min): Skeptic
caught two Advocate fabrications about prior trial design —
context isolation at runtime. Pre-registrations are git-tracked
YAMLs.

---

## Claude Opus 4.7 usage (150 words, 150 counted)

Four Opus 4.7 calls per loop with
`thinking={"type":"adaptive","display":"summarized"}` and
`output_config={"effort":"high"}`. (1) Proposer emits 3-5 compact law
families and the ex-ante skeptic test for each, before any fit. (2)
The test is executed by plain Python, not Opus. (3) Skeptic reviews
the specific metric pattern (`perm_p=0.049` is weaker than `0.001`;
`ci_lower=0.61` is marginal) and emits PASS / FAIL / NEEDS_MORE_TESTS.
(4) Interpreter writes the mechanism hypothesis and the "what this is
not" paragraph. **180-call cross-model ablation: Sonnet 4.6 = 0/60
PASS on gate-PASS candidates (full dissent collapse); Opus 4.7 =
10/60 — RLHF calibration gap, not thinking-mode**. **PhL-13: Opus 4.7
zero-shot retrieval of TOP2A−EPAS1 = 0/10 (rebuts LLM-SRBench
memorization concern).** **IPF Run #1 (2026-04-25): Skeptic caught
two Advocate fabrications about prior trial design — RAINIER + Raghu
2017 prespecified stratifiers Advocate claimed "never tested". Context
isolation working at runtime.** **1M-context failure synthesis + PhL-17
210-turn adversarial ablation — Most Creative + Keep Thinking secondary
prize candidates.**

---

## Claude Managed Agents usage (150 words, 149 counted)

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

**IPF Run #1 (2026-04-25).** Skeptic caught two Advocate fabrications
about prior trial design (RAINIER + Raghu 2017) — context isolation
working at runtime. See `results/external_validation_ipf/`.

---

## Prize category justification (100 words, 96 counted)

**Best use of Claude Managed Agents ($5K).** Public-beta-only Managed
Agents orchestration with isolated sessions: three live paths — B
(single-agent `agent_toolset_20260401`), A (PhL-9 sequential
three-session chain on real TCGA-KIRC, structured-JSON handoff), C
(PhL-8 Routine `/fire` HTTP 200). Plus Memory public beta (integrated
2026-04-23 day-of): Skeptic writes rejection lessons; fresh sessions
read, quote, refine them; server-side persistence verified via raw
`/v1/memory_stores/*` API. Our own H1 LLM-SR extension was killed by
the separately pre-registered IMmotion150 survival replay (PhL-1).
**IPF Run #1: Skeptic caught two Advocate fabrications about RAINIER
+ Raghu 2017 — single-harness pipelines cannot catch this.**
Verification as working code.

---

## GitHub

```
https://github.com/jang1563/lacuna-falsification
```

Repo has been public since 2026-04-23 19:32 ET.

---

## Demo video

```
[to be pasted on 4/26 morning after Loom render]
```

Canonical narration: `docs/loom_narration_final_90s.md` (333 words,
~143 s at 140 WPM / ~167 s at 120 WPM, **eight segments** incl. DIPG
+ IPF generalization tags, opens with problem-first "AI-for-science...
built to say no" hook and closes with the IPF dual-fabrication-catch
demonstration of 4-role context isolation). Shot-list / rehearsal
assets: `docs/loom_script.md` (pre-narration shot list) +
`docs/loom_visual_cue_map.md` (8-segment asset cue map).

---

## Broader Program Context (optional, 90 words, 89 counted)

Opus 4.7 proof-of-concept of a larger program (NegBioDB + failure
network + rescue engine for prematurely-rejected clinical hypotheses).
Same 4-role engine re-run on 15 H3 K27M DMG rescue hypotheses
(locked-before-output git SHA 8a4ecc5): 7 supported, 7 mixed, 1
insufficient; top lead CED-delivered MTX110 panobinostat (13/15
delivery class). Tier-1 prognostic-substrate gate then re-tested 4
candidates on PBTA v15 (n=192 survival-evaluable, 182 events): 0
PASS, 2 FAIL, 2 UNDERPOWERED — intended falsifier output. **IPF Run
#1: 1/5 supported, two Advocate fabrications caught (2026-04-25).**
Research-grade hypotheses; prospective validation required.
