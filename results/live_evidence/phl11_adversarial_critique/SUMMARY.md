# PhL-11 — Adversarial self-critique (3-turn, role-separated)

**Verdict:** OK — 6-session harness (3 turns × 2 models) ran
end-to-end in 616 s. Cross-model comparison shipped as strict-JSON
metrics. **Mixed result, reported honestly.**

## Why this exists

Anthropic's Opus 4.7 launch (2026-04-16) positions the model as one
that *"devises ways to verify its own outputs before reporting back."*
Tharik (Cloud Code, 2026-04-22 live session) named the complement as
an **open problem**: *"a verification script that forces the agent to
test its own outputs against hard constraints."*

Self-refine WITHOUT role separation amplifies self-bias monotonically
([Pride and Prejudice, arXiv 2402.11436](https://arxiv.org/abs/2402.11436),
ACL 2024: 10 self-refine iterations increase self-bias linearly) and
Anthropic's Petri 2.0 audit flags Opus 4.7 as "prone to sycophantic
agreement under pushback". The fix from
[POPPER (arXiv 2502.09858)](https://arxiv.org/abs/2502.09858) is
**role separation with different epistemic rules per turn**. PhL-11
ships this as three separate Managed Agents sessions with three
different system prompts.

## Design

- **T1 Interpreter:** computational biologist; emits mechanism +
  falsifiable predictions grounded in cited ccA/ccB biology.
- **T2 Adversary:** Nature Methods hostile reviewer; editor-enforced
  rules: (a) every criticism includes a specific calculation /
  effect size / named alternative model, (b) exactly ONE concrete
  CRISPR KO experiment with target / cell line / readout / expected
  effect size, (c) cites specific numbers from T1 and argues
  distinguishability from noise at n=505, (d) vague critiques
  auto-rejected.
- **T3 Defender:** responds to each attack with concrete recomputation
  (DEFEND) or named ≥20-char limitation (CONCEDE). "We will
  investigate" is forbidden.

Runs the same 3-turn flow on **`claude-opus-4-7`** and
**`claude-sonnet-4-6`** to produce measurable model-swap evidence.

## Cross-model metrics (from verdict.json)

| Metric | Opus 4.7 | Sonnet 4.6 | Differentiator |
|---|---|---|---|
| `n_calculations_in_T2` | 18 | 32 | Sonnet chattier; not a capability win |
| `n_named_alt_models_in_T2` | 4 | 4 | Tied |
| `n_falsification_experiments_in_T2` (CRISPR KO) | **5** | **1** | **Opus followed "one per attack" rule literally across all 5 attacks; Sonnet aggregated to 1 total** |
| `concede_rate_in_T3` | 1.00 | 1.00 | **Both capitulated 100%** — honest limit of adversarial critique under forceful prompting |
| `limitation_specificity_mean_chars` | 532.6 | 658.8 | Sonnet longer concessions; not interpretability |

## Honest interpretation

**The clean Opus 4.7 differentiator is literal per-attack instruction
following** — Opus emitted 5 CRISPR KO experiments (one per each of
5 attacks) while Sonnet aggregated to 1 total across 4 attacks. This
matches the Opus 4.7 docs:
*"More literal instruction following, particularly at lower effort levels."*
[What's new in Claude Opus 4.7](https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-7).

**Both models capitulated fully under the adversarial attack** —
`concede_rate = 1.00` on both. `net_position_change = "softened"` on
both. This is consistent with Petri 2.0's "sycophantic agreement under
pushback" flag for Opus 4.7 and is a real-world limit of multi-turn
critique harnesses. We report it verbatim rather than reframe.

## Implications for the submission claim

The previous why_opus_4_7.md claim that "smaller models collapse to
rubber-stamp agreement" was the pre-registered strong form, and was
FALSIFIED by the main E2 ablation (all 3 models cite metrics equally;
Sonnet over-dissents rather than rubber-stamps). PhL-11 adds a
complementary honest finding: under forceful adversarial prompting,
BOTH Opus 4.7 and Sonnet 4.6 concede 100%. The differentiator in
this 3-turn harness is not "who holds their ground better" but
"who follows the per-attack instruction more literally" — where
Opus 4.7 wins cleanly (5 vs 1 CRISPR KO).

## Artefacts

| File | Contents |
|---|---|
| `verdict.json` | session_ids, metrics, cross-model comparison |
| `T1_interpreter_opus_4_7.txt` | 6 809 chars |
| `T2_adversary_opus_4_7.txt` | 8 755 chars |
| `T3_defender_opus_4_7.txt` | 3 138 chars |
| `T1_interpreter_sonnet_4_6.txt` | 7 194 chars |
| `T2_adversary_sonnet_4_6.txt` | 11 118 chars |
| `T3_defender_sonnet_4_6.txt` | 3 211 chars |

## Reproduce

```bash
source ~/.api_keys
PYTHONPATH=src .venv/bin/python src/phl11_adversarial_critique.py
```

Cost: ~$2. Wall: 616 s.
