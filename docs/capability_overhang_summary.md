# Capability Overhang Summary — what Opus 4.7 specifically enabled

> *A judge-facing one-pager that classifies every Opus-4.7-specific
> finding in this repo by what it actually measures — reasoning,
> instruction-following, calibration, or memory utilization — and
> honestly names the patterns that are NOT differentiators.*

**Context (2026-04, verified via Anthropic public docs):**

- Opus 4.7, Opus 4.6, and Sonnet 4.6 all support **1M-token context
  window** in the production API ([platform.claude.com/docs/.../context-windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)).
  **Context length is not a Opus-4.7 exclusive** on this submission's
  tasks.
- Opus 4.7 **adaptive thinking** (`thinking={"type":"adaptive","display":"summarized"}`
  + `output_config.effort`) is confirmed as agentic-workflow-specific
  by [adaptive-thinking docs](https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking):
  *"Adaptive thinking can drive better performance than extended
  thinking with a fixed budget_tokens for many workloads, especially
  bimodal tasks and long-horizon agentic workflows."* Anthropic has
  not published a quantitative benchmark of the adaptive-thinking
  uplift — so the observation below is our measured one, not a reprise
  of theirs.
- A **third-party eval** ([tessl.io · 880 evals](https://tessl.io/blog/anthropic-openai-or-cursor-model-for-your-agent-skills-7-learnings-from-running-880-evals-including-opus-47),
  2026-04) finds Haiku 4.5 + skills = 84.3% beating Opus 4.7 baseline
  80.5% on an adherence task. **Overhang is task-specific, not
  universal.** Our measurement (below) is for one specific task:
  the scientific-claim Skeptic turn.

## Seven findings, honestly classified

| # | Finding | What the pattern really is | Quoted evidence | Is Opus 4.7 specifically required? |
|---|---|---|---|---|
| **A1** | Cross-model Skeptic ablation: Sonnet 4.6 = **0 / 60 PASS** on gate-PASS candidates (permanent dissent collapse); Opus 4.7 = **10 / 60 PASS** (calibrated dissent); Haiku 4.5 = 14 / 60 | **Calibration + instruction-following under dual-role prompts** | [`results/ablation/SUMMARY.md`](../results/ablation/SUMMARY.md) · 180 calls · identical prompt, metrics, thinking budget | **Yes, measurably.** Sonnet cannot hold the Skeptic-review stance; Haiku over-passes. Opus 4.7 tracks the pre-registered thresholds. This is the strongest overhang demonstration in the repo. |
| **A2** | Opus 4.6 → 4.7 calibration delta inside the not-wrong set: 4.7 commits PASS 10 / 10 on clean survivors (4.6: 7 / 10); 4.7 abstains `NEEDS_MORE_TESTS` 10 / 10 on stress-test compound (4.6: over-commits PASS 2 / 10). Strict miscalibration 0% for both | **Graded-verdict calibration** (not strict error reduction) | [`results/ablation/opus_46_vs_47/`](../results/ablation/opus_46_vs_47/) · n=60 each | **Version-specific.** 4.7 graded calibration tracks Anthropic's own published AA-Omniscience 61→36% hallucination delta; the gate itself works identically. |
| **A3** | Single Opus 4.7 call synthesises across 74 rejections + 9 survivors + 5 paper abstracts → 5 new skeletons, 5 invariant conditions, bimodal-failure-landscape analysis. Invariant #1 ("proliferation ∧ HIF, opposite sign") confirmed by exhaustive 990-pair enumeration in I2 | **Adaptive-thinking synthesis quality** (prompt ~3,553 tokens; 1M context available but not exercised) | [`results/overhang/synthesis_1m.json`](../results/overhang/synthesis_1m.json) + [H2 section in headline_findings](headline_findings.md#opus-47-cross-reasoning-synthesis-over-the-rejection-log-h2) | **Not context-gated.** Both Opus 4.7 and Sonnet 4.6 fit this prompt. The distinguishing factor is synthesis quality — same task type as A1. |
| **A4** | 3-turn role-separated adversarial critique across Opus 4.7 + Sonnet 4.6 (6 sessions). Opus literal per-attack rule following: 5 CRISPR KOs vs Sonnet 1. Both 100% concede under pushback | **Instruction-literalism (mixed)** — strong evidence of stronger instruction-following in Opus; honest null on "epistemic resilience" (both capitulate) | [`results/live_evidence/phl11_adversarial_critique/SUMMARY.md`](../results/live_evidence/phl11_adversarial_critique/SUMMARY.md) | **Partially.** Instruction-literalism differs (Opus > Sonnet) but concede-under-pushback is the same. Honest reporting: the external deterministic gate remains load-bearing *because* multi-turn self-critique has measured limits on both models. |
| **A5** | 10-repeat zero-shot Opus 4.7 query for best 2-gene ccRCC metastasis compound: TOP2A-EPAS1 exact top pick **0 / 10**; proliferation-HIF form anywhere **0 / 10**. Literature-anchor probe: **2 / 2** "structurally_equivalent_to_known" | **Discovery-vs-retrieval boundary** (not an overhang; it is the correct refusal-to-retrieve) | [`results/live_evidence/phl13_memorization_audit/SUMMARY.md`](../results/live_evidence/phl13_memorization_audit/SUMMARY.md) | **Model-agnostic finding** that supports our discovery claim. This is rigour evidence, not a capability ceiling on Opus. |
| **A6** | 8-lesson Memory chain across sessions PhL-3 → PhL-7 → PhL-10 → PhL-12; cross-cancer rule transfer (ceiling-effect lesson generalises KIRC/CA9 → LUAD/SFTPC → PRAD/KLK3) | **Memory-utilization pattern** (not a model-specific overhang; Memory is available to any Managed Agents caller) | [`results/live_evidence/phl12_memory_chain_deepen/SUMMARY.md`](../results/live_evidence/phl12_memory_chain_deepen/SUMMARY.md) | **Not model-specific.** Memory public beta (2026-04-23) is the substrate; any model can write to it. The pattern (accumulating rejection lessons across sessions) is the demo — not the model that wrote them. |
| **A7** | LLM-SR 10-iteration convergence: Opus 4.7 × 9 novel skeletons vs Sonnet 4.6 × 9 novel skeletons post-seed. Both produce 0 additional gate-passing survivors. Peak non-seed Opus AUROC 0.608 (novel Proliferation×HIF cross); Sonnet 0.646 (TOP2A − AGXT) | **Honest null** — gate is the binding constraint, not the proposer model. Opus 0/9 library fallbacks vs Sonnet 4/9 (structured-output reliability) | [`results/overhang/llm_sr_10iter/SUMMARY.md`](../results/overhang/llm_sr_10iter/SUMMARY.md) | **No.** The gate absorbs model variation on this task. This finding is *deliberately* published as a non-overhang case. |

## Pattern summary

**Three real overhang patterns** measured in this repo:

1. **A1** — reasoning / instruction-following / calibration gap under
   dual-role Skeptic prompt. **Strongest evidence.** Sonnet cannot
   hold the stance (0 / 60); Opus 4.7 tracks thresholds.
2. **A2** — graded-verdict calibration delta Opus 4.6 → 4.7. **Internal
   version-specific.** Matches Anthropic's own published hallucination
   delta.
3. **A4 (partial)** — instruction-literalism advantage for Opus. Honest
   null on multi-turn stance-holding.

**Non-overhang findings** (explicitly flagged):

- **A3** is not context-gated (both models fit the prompt).
- **A5** is a discovery-integrity check, not a capability ceiling.
- **A6** is Memory-utilization, substrate-available to any model.
- **A7** is deliberately published as a honest null.

## What this means for the submission narrative

> Opus 4.7 is not "uniformly better than Sonnet 4.6"; the tessl.io
> 880-eval benchmark shows the opposite direction on some adherence
> tasks. **What our submission measures is specific to the scientific-
> claim Skeptic role**: Opus 4.7 is the model that held the gate's
> threshold boundary while Sonnet 4.6 collapsed into permanent dissent.
> That measurement is why the falsification pipeline ships with Opus
> 4.7 at the Skeptic turn. Context length, memorization refusal,
> Memory chain persistence, and instruction-literalism are useful
> features across multiple models; the Skeptic calibration is
> task-measured.

## What we did NOT do (and why)

- **No context-gated demo** — both 1M-context models exist; a demo
  that shows Opus 4.7 doing something "Sonnet literally cannot fit"
  would require >1M tokens, which our scientific data does not
  naturally produce.
- **No thinking-ON-vs-OFF ablation within Opus 4.7** — single-model
  internal ablation carries falsifying risk (a null result would
  weaken why_opus_4_7.md without adding clear value). The existing
  cross-model ablation (A1) already measures the calibration claim.
- **No universal-model-superiority claim** — tessl.io shows
  counter-examples. Our claim is task-specific (scientific-Skeptic
  role) and data-specific (the 60-candidate ablation bundle).

## Cross-cutting caveats

- **Task scope**: ccRCC metastasis prediction + IMmotion150 PFS
  survival validation. Not a general-biology claim.
- **Gate is binding, not Opus**: every finding above sits on top of
  the pre-registered deterministic Python gate in
  `src/lacuna/falsification.py`, thresholds committed before
  fit. Opus-4.7 calibration is the capability that **reads the gate
  output correctly** — it does not replace the gate.
- **Human oversight is essential**: Jan Leike's
  [AAR 2026-04-14](https://www.anthropic.com/research/automated-alignment-researchers)
  explicitly requires *"human inspections of both their results and
  their methods"* even with tamper-resistant evaluations. Theory
  Copilot publishes the rejection log, pre-registrations, and
  `make audit` as the human-inspection surface; the Opus calibration
  makes that inspection *scalable*, not obsolete.

## Quick-reference for judges

- **Best single piece of Opus-4.7-specific evidence**:
  [`results/ablation/SUMMARY.md`](../results/ablation/SUMMARY.md) (A1
  above — 180-call ablation).
- **Best piece of graded-calibration evidence**:
  [`results/ablation/opus_46_vs_47/`](../results/ablation/opus_46_vs_47/) (A2).
- **Best piece of honest-null evidence showing the gate (not the model)
  is load-bearing**: [`results/overhang/llm_sr_10iter/SUMMARY.md`](../results/overhang/llm_sr_10iter/SUMMARY.md) (A7).
- **Best piece of discovery-integrity evidence**:
  [`results/live_evidence/phl13_memorization_audit/SUMMARY.md`](../results/live_evidence/phl13_memorization_audit/SUMMARY.md) (A5).
