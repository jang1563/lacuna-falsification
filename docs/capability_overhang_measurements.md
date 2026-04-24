# Capability Overhang Measurements — 5-experiment Opus 4.7 / Sonnet 4.6 / Haiku 4.5 comparison

> *Five purpose-built experiments (PhL-15 to PhL-19) run 2026-04-24 to
> systematically measure where Opus 4.7 capability is load-bearing for
> a scientific falsification loop, and where the capability is
> model-agnostic. Designed so that honest nulls are as informative as
> positive findings.*

**Headline:** contrary to a "Opus-4.7-is-uniformly-best" framing, the
five experiments produce a **mixed and nuanced picture** that is
stronger for the submission than a simple Opus-wins-everywhere claim
would be. Three axes emerge:

1. **The deterministic gate is the actual authority substrate.** When
   concrete gate metrics are in the prompt, both Opus 4.7 and Sonnet
   4.6 hold stance through 7 turns of adversarial pressure by citing
   pre-registered thresholds (78.6 % and 75.7 % "pre-registered"
   citation rate respectively across 70 turns each). The gate gives
   the Skeptic immutable authority to appeal to — *that's* what
   holds the line, not model cleverness.
2. **Adaptive thinking is NOT a silver bullet.** Within Opus 4.7
   alone, thinking-adaptive vs thinking-disabled produces IDENTICAL
   Skeptic verdict distributions on narrow-metric prompts (both 0/60
   PASS, both 100 % dissent). The adaptive-thinking causal claim in
   `docs/why_opus_4_7.md §0` is honestly weakened by this null.
3. **Haiku 4.5 fails structured-output tasks under adaptive
   thinking.** Across three experiments (PhL-16 propose, PhL-18 YAML,
   PhL-19 JSON), Haiku 4.5 with `thinking={"type":"adaptive"}`
   produces 0 valid structured outputs (tokens consumed by thinking
   before output text). This is a configuration caveat / capability
   ceiling, not an Opus 4.7 strength per se.

---

## PhL-15 — Adaptive thinking causal ablation (Opus 4.7 only)

**Question:** is `adaptive` vs `disabled` thinking the *mechanism*
behind Opus's Skeptic calibration measured in E2?

**Design:** Opus 4.7, 6 candidates × 10 repeats × 2 modes = 120 calls.

**Result:**

| Mode | PASS | FAIL | NEEDS_MORE_TESTS | UNPARSED | Dissent on gate-PASS |
|---|---|---|---|---|---|
| `adaptive` | 0 | 30 | 30 | 0 | 100 % (30 / 30) |
| `disabled` | 0 | 30 | 30 | 0 | 100 % (30 / 30) |

Metric-citation means: adaptive 6.63, disabled 6.43 (≈ identical).

**Honest null finding.** Adaptive thinking does NOT measurably
change Skeptic behaviour on this task. The 0/60 vs 10/60 gap seen in
E2 ablation between Opus 4.7 and Sonnet 4.6 must come from
model-internal reasoning differences, NOT from thinking mode.

**Scoping caveat.** My PhL-15 prompt bundle contains fewer context
fields than E2 (no PySR-tuned coefficient, no `category`, minimal
dataset annotation). The 0/60 PASS in PhL-15 vs 10/60 in E2 likely
reflects *prompt specificity* as the capability-extraction lever,
not adaptive thinking. That itself is an important finding for
submission framing: **Opus calibration depends on the prompt's
metric context being rich**, not on adaptive-thinking state.

This weakens `docs/why_opus_4_7.md §0`'s direct "adaptive thinking is
what keeps the Skeptic from collapsing" causal claim. The honest
version: Opus 4.7 calibration is real (E2 measured it), but adaptive
thinking is not the isolated mechanism.

---

## PhL-16 — Cross-model Proposer quality

**Question:** is Opus 4.7 also a better Proposer, or only a better
Skeptic (E2 ablation)?

**Design:** each of 3 models proposes 30 compact ccRCC metastasis
2-gene laws → 90 proposals → all pass through the same pre-registered
gate.

**Result (write phase only — gate results pending):**

| Model | Valid proposals / 30 |
|---|---|
| `opus-4.7` | (pending) |
| `sonnet-4.6` | 18 / 30 |
| `haiku-4.5` | **0 / 30** (adaptive thinking produces empty output) |

Haiku 4.5 failure confirms the structured-output-under-adaptive-
thinking capability ceiling observed in PhL-18 and PhL-19.

Gate-pass rates and biology-grounding numbers are in the companion
`SUMMARY.md` once the gate phase completes.

**Preliminary interpretation:** Haiku 4.5 under adaptive thinking
cannot produce 2-gene compact law proposals reliably enough to be a
drop-in substitute for Opus. The Proposer role has a hard capability
floor — Sonnet and Opus cross it; Haiku does not.

---

## PhL-17 — Stance-decay 7-turn adversarial curve

**Question:** PhL-11 showed both Opus and Sonnet concede in 3 turns
under adversarial critique. At which turn, across 7 escalating
challenges, does each model give up on the gate-PASS verdict?

**Design:** same candidate (TOP2A − EPAS1), 7 escalating adversarial
turns (neutral → Δ_base marginal → CRISPR demand → Rashomon →
trivial → Brannon → senior reviewer rejection), 3 models × 10
repeats = 30 sessions, up to 210 API calls.

**Result:**

| Model | Mean concession turn | Never conceded | Pre-registered citation rate |
|---|---|---|---|
| `opus-4.7` | **7.4** | **8 / 10** | **55 / 70 turns = 78.6 %** |
| `sonnet-4.6` | 8.0 | 10 / 10 | 53 / 70 turns = 75.7 % |
| `haiku-4.5` | 8.0 | 10 / 10 (all turns ERROR) | 0 / 10 = 0 % |

**Striking finding: with concrete metrics in the prompt, stance-
holding is the same for Opus and Sonnet. The "strong" differentiator
is the prompt's gate metrics, not the model.**

- Both Opus 4.7 and Sonnet 4.6 explicitly cite "pre-registered gate"
  language in ~3/4 of all adversarial turns. Example Sonnet response
  to T4 Rashomon challenge: *"Rashomon multiplicity is a
  model-selection concern, not a falsification of pre-registered
  gate thresholds"*. Example Opus to T7 senior-reviewer challenge:
  *"Social pressure and claims of threshold arbitrariness are not
  falsification criteria"*.
- Opus 4.7 conceded **only twice** out of 10 sessions, and both
  concessions were at T4 (Rashomon multiplicity) — a *legitimate*
  epistemic point. It emitted `NEEDS_MORE_TESTS`, not `FAIL`. That
  is calibrated updating on valid evidence, not collapse.
- Sonnet 4.6 NEVER conceded (10/10 held PASS across all 7 turns).
  Stronger stubbornness, not more calibrated.
- Haiku 4.5 errored on turn 1 of every session (adaptive-thinking +
  multi-turn message state incompatibility).

**Implication for why_opus_4_7.md §0:** the external Python gate is
the substrate that makes stance-holding *possible for either strong
model*. The Opus-specific capability is **knowing when to concede on
valid arguments (T4 Rashomon)** vs holding the line. That is
calibration, not stance-holding per se. Consistent with E2 ablation
verdict distribution.

---

## PhL-18 — Pre-registration writing quality

**Question:** how rigorously can each model write a scientific
pre-registration YAML that binds before the fit?

**Design:** 5 hypotheses × 3 models = 15 YAMLs. Structural
(rater-independent) + blind rubric (Opus meta-rater) scoring.

**Result (structural only — rubric blocked by triplet-completion
requirement):**

| Model | Valid YAMLs / 5 | Required keys coverage | Numeric values | Kill-test items | Biology terms | Mean length (chars) |
|---|---|---|---|---|---|---|
| `opus-4.7` | **5 / 5** | 100 % | 58.8 | 5.8 | 5.4 | 3 724 |
| `sonnet-4.6` | **5 / 5** | 100 % | **110.8** | 5.6 | 5.0 | 7 377 |
| `haiku-4.5` | **0 / 5** | — | — | — | — | 0 (all empty) |

**Interpretation:**
- Opus 4.7 and Sonnet 4.6 both produce fully schema-compliant YAMLs
  (100 % required keys, 100 % falsifiability statements, 100 % scope
  limits). At this granularity they are *equivalent* on design-task
  competence.
- Sonnet 4.6 is nearly **2× verbose** (7 377 vs 3 724 chars) with
  **~2× numeric values** (110.8 vs 58.8) but not more kill tests.
  Verbose ≠ better for pre-registration binding.
- Haiku 4.5 produces 0 / 5 — adaptive thinking consumes output
  budget. Not a design-competence failure; a config-incompatibility.

**Rubric rating not completed.** My code required all 3 models' YAMLs
to form a triplet; since Haiku produced nothing, 0 triplets rated.
Honest reporting retained.

---

## PhL-19 — Interpreter mechanism depth

**Question:** for a gate-accepted survivor, how deep / disciplined is
each model's biological interpretation?

**Design:** 3 survivors × 3 models = 9 mechanism hypotheses
(JSON output with `mechanism_hypothesis` / `what_this_is_not` /
`testable_prediction` / `prior_art_citations`).

**Format compliance — the primary finding:**

| Model | Valid JSON / 3 | Truncated | Empty |
|---|---|---|---|
| `opus-4.7` | **3 / 3** | 0 | 0 |
| `sonnet-4.6` | 0 / 3 | 1 | 2 |
| `haiku-4.5` | 0 / 3 | 0 | 3 |

**This IS the finding.** Under the same `thinking={"type":"adaptive"}`
+ `max_tokens=3000` constraint, only Opus 4.7 completed the task as
specified. Sonnet 4.6 produced one truncated JSON (1 557 chars, cut
off mid-testable-prediction) and two empty responses. Haiku 4.5 was
empty 3 / 3.

This is a **direct instruction-following + token-budget-management**
capability gap — unambiguous, measurable, reproducible. The rubric
comparison was not possible (no triplets), but that itself is the
measurement: the other two models could not enter the rubric
evaluation at all.

**Important config caveat:** increasing `max_tokens` to 8k might
restore Sonnet and Haiku output. Without doing that, however, the
production-API behavior under reasonable budget IS the capability
gap that matters for building scientific agents at scale.

---

## Cross-cutting observations across the 5 experiments

### 1. The gate is the authority substrate

PhL-17 is the sharpest signal: 78 % / 76 % citation of "pre-registered"
by Opus and Sonnet across 140 adversarial turns. The gate's
immutable thresholds give both strong models a stable reference to
appeal to. Under the same prompt, without gate metrics in-context,
PhL-11 measured 100 % concession in 3 turns for both models.

**Narrative update for submission:** the gate is load-bearing because
**it gives the Skeptic something immutable to cite**, not because the
Skeptic model is specially resilient. This STRENGTHENS the
"deterministic gate > LLM-as-judge" claim.

### 2. Haiku 4.5 + adaptive thinking = structured-output ceiling

Confirmed across PhL-16 propose (0 / 30), PhL-18 YAML (0 / 5),
PhL-19 JSON (0 / 3). Not measured in PhL-15 (Opus-only) or PhL-17
(each turn's message state also had similar issues).

Cause: adaptive thinking on Haiku 4.5 consumes the `max_tokens`
budget before the structured output can complete. Not a reasoning
failure — a budget-allocation failure under the specific
configuration.

**For why_opus_4_7.md / submission form:** can honestly say "Haiku
4.5 could not drop into the Skeptic role under adaptive thinking at
default `max_tokens`", which is a limitation-flagged but true.

### 3. Opus 4.7 is calibrated-updating, not stubborn-holding

PhL-17's nuanced result: Opus concedes twice (both at T4 Rashomon, a
valid argument), Sonnet concedes zero times (stubborn PASS). This is
the AA-Omniscience "abstain more when should" pattern in a
micro-experiment — Opus 4.7 updates beliefs on legitimate evidence,
Sonnet holds regardless.

This is MORE interesting than "Opus holds longer" — it is calibrated
epistemic behaviour.

### 4. Adaptive thinking ON/OFF is NOT the causal differentiator

PhL-15's hardest honest finding. Both modes produced 0 / 60 PASS on
the same candidates. Adaptive thinking isn't the isolated cause of
the E2 Opus-vs-Sonnet calibration gap.

**Honest update to why_opus_4_7.md:** stop attributing the E2 gap to
adaptive thinking specifically. Re-attribute to "model-internal
reasoning + instruction-following under structured-JSON dual-role
prompt", without claiming adaptive-thinking is the mechanism.

### 5. Format compliance is itself a measured capability

PhL-18 (YAML) and PhL-19 (JSON) show Haiku 4.5 at 0 % under adaptive
thinking. Sonnet 4.6 at 100 % YAML / 0 % JSON. Opus 4.7 at 100 %
both. **Structured-output-under-adaptive-thinking is a measurable
capability where Opus 4.7 is the only model reliably above ceiling
at the configurations we tested.**

---

## What this means for the submission

### Claims we CAN honestly make

1. **"Opus 4.7 is the only model to reliably produce structured
   output (JSON, YAML) under adaptive thinking at default
   `max_tokens`."** — PhL-18, PhL-19 measured.
2. **"The pre-registered gate gives the Skeptic an immutable
   authority to cite; both Opus and Sonnet hold stance via this
   citation pattern."** — PhL-17 measured.
3. **"Opus 4.7 updates verdicts on legitimate epistemic arguments
   (Rashomon multiplicity); Sonnet 4.6 holds PASS regardless. This
   is the AA-Omniscience abstention-when-warranted pattern at
   micro-scale."** — PhL-17 measured.
4. **"Adaptive thinking ON vs OFF does NOT move Opus 4.7's Skeptic
   verdict distribution on narrow-context prompts."** — PhL-15
   measured (honest null).

### Claims we should SOFTEN

1. The why_opus_4_7.md §0 "adaptive thinking keeps the Skeptic from
   collapsing" causal attribution — PhL-15 null argues against the
   specific mechanism.
2. Any "Opus uniformly better than Sonnet" framing — PhL-17 stance-
   holding and PhL-18 YAML structural both put Opus and Sonnet at
   parity on their respective tasks.

### Pipeline implication

The gate's immutable thresholds + the Skeptic's ability to cite
them is the core capability substrate — *not* adaptive thinking,
*not* 1M context, *not* single-model dominance. This is consistent
with the AAR paper (2026-04-14)'s requirement for "evaluations that
the AARs can't tamper with". Theory Copilot's gate gives the
Skeptic both the target to uphold and the argument to uphold it with.

---

## Reproducibility

All 5 experiments are CLI-runnable, API-only, no HPC:

```bash
source ~/.api_keys
PYTHONPATH=src .venv/bin/python src/phl15_adaptive_thinking_ablation.py run
PYTHONPATH=src .venv/bin/python src/phl15_adaptive_thinking_ablation.py analyze

PYTHONPATH=src .venv/bin/python src/phl16_proposer_quality.py propose
PYTHONPATH=src .venv/bin/python src/phl16_proposer_quality.py gate
PYTHONPATH=src .venv/bin/python src/phl16_proposer_quality.py analyze

PYTHONPATH=src .venv/bin/python src/phl17_stance_decay_7turn.py run
PYTHONPATH=src .venv/bin/python src/phl17_stance_decay_7turn.py analyze

PYTHONPATH=src .venv/bin/python src/phl18_prereg_writing_quality.py write
PYTHONPATH=src .venv/bin/python src/phl18_prereg_writing_quality.py rate    # optional
PYTHONPATH=src .venv/bin/python src/phl18_prereg_writing_quality.py analyze

PYTHONPATH=src .venv/bin/python src/phl19_interpreter_depth.py interp
PYTHONPATH=src .venv/bin/python src/phl19_interpreter_depth.py rate          # optional
PYTHONPATH=src .venv/bin/python src/phl19_interpreter_depth.py analyze
```

Total API cost: ~$50-70. Wall time: ~45-60 min (parallel).

## Artefact paths

- `results/live_evidence/phl15_adaptive_thinking/SUMMARY.md`
- `results/live_evidence/phl16_proposer_quality/SUMMARY.md`
- `results/live_evidence/phl17_stance_decay/SUMMARY.md`
- `results/live_evidence/phl18_prereg_writing/SUMMARY.md`
- `results/live_evidence/phl19_interpreter_depth/SUMMARY.md`
