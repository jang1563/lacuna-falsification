# Judge FAQ — anticipated questions and 30-second answers

This document consolidates the most likely reviewer challenges and the
exact evidence file each answer points to. Every claim here is also
load-bearing somewhere else in the repo; this file just routes a
reviewer to the right artifact in one click.

Reading order if you have 5 minutes:
- [Q1 — discovery vs rediscovery](#q1)
- [Q2 — AUROC ceiling +0.004](#q2)
- [Q3 — clinical magnitude HR=1.36](#q3)
- [Q4 — cohort independence](#q4)
- [Q5 — Sonnet drop-in](#q5)
- [Q6 — memorization risk](#q6)

---

## Q1 — "Is this discovery or rediscovery?" <a id="q1"></a>

**Honest answer.** Rediscovery. The `TOP2A − EPAS1` axis is the published
ccA/ccB ccRCC subtype axis (Brannon 2010, Brooks 2014 ClearCode34). We
do not claim novel biology.

**Why that is the contribution, not the limitation.** FIRE-Bench
([arXiv 2602.02905](https://arxiv.org/abs/2602.02905)) formalises
*rediscovery of established findings* as the evaluation paradigm for
science agents and reports that current SOTA agents score <50 F1 on it.
POPPER ([arXiv 2502.09858](https://arxiv.org/abs/2502.09858)) shows
falsification-driven validation at human-comparable accuracy with a 10×
speedup. In that framing, **the unit of value is hypothesis-validation
accuracy, not generation novelty** — and our pipeline ships the
validation harness in plain Python rather than another LLM judge.

**Evidence.**
- [`docs/why_opus_4_7.md` §1](why_opus_4_7.md) — POPPER + FIRE-Bench framing
- [`docs/methodology.md` §6](methodology.md) — full accept/reject table
- [`docs/survivor_narrative.md`](survivor_narrative.md) "What it is not" — explicit non-claims

---

## Q2 — "AUROC 0.726 vs LR-with-interaction 0.722. The gap is +0.004. Is that meaningful?" <a id="q2"></a>

**Honest answer.** No, that gap is not the value claim. We document
this caveat ourselves in the survivor narrative. The compound `TOP2A − EPAS1`
does not beat an LR with interaction term meaningfully on AUROC.

**What is meaningful.**
1. **Interpretable compactness**: a 1-line `subtract` law that any
   reviewer can read, compared with an interaction-coefficient LR that
   needs three numbers and a sign convention to read.
2. **Pre-registration bites symmetrically**: the same `+0.05` baseline
   threshold rejects the textbook HIF-axis Opus law on tumor-vs-normal
   *and* accepts the unseeded 2-gene law on metastasis. Neither
   decision was made post-hoc.
3. **Falsification continuity**: the same survivor passes 6/6 robustness
   axes (threshold grid, permutation, bootstrap, scaling, cohort-size,
   5-fold CV — `survivor_robustness/SUMMARY.md`).

**Evidence.**
- [`docs/survivor_narrative.md`](survivor_narrative.md) "How robust is this?"
- [`results/track_a_task_landscape/survivor_robustness/SUMMARY.md`](../results/track_a_task_landscape/survivor_robustness/SUMMARY.md)

---

## Q3 — "HR=1.36 on IMmotion150 is clinically modest. Is this actionable?" <a id="q3"></a>

**Honest answer.** Not clinically actionable yet. HR=1.36 is
statistically clean (log-rank p=0.0003, 7.5-month median PFS gap) but
clinically modest compared to actionable hazards (HR > 2). We do not
claim diagnostic or therapeutic utility.

**Why we replicate it anyway.** Replication on IMmotion150 (n=263,
metastatic-only Phase-2 cohort, separately pre-registered survival
gate) is method validation, not clinical translation. The point is
that the law survives a **different** gate, on a **different** cohort,
under a **different** endpoint (PFS vs M-staging), without any
parameter retuning. The C-index 0.601 + log-rank p=0.0003 + treatment
robustness is the rigor signal; the HR magnitude is the disease
signal.

**Evidence.**
- [`results/track_a_task_landscape/external_replay/immotion150_pfs/`](../results/track_a_task_landscape/external_replay/immotion150_pfs/) — full replay
- [`preregistrations/phf3_immotion150_pfs.yaml`](../preregistrations/) — pre-reg YAML, SHA-bound

---

## Q4 — "Both cohorts are ccRCC. Is this real cross-cohort validation?" <a id="q4"></a>

**Honest answer.** Same disease, same tissue. What transfers is
*platform-invariant* (RNA-seq → microarray → bulk RNA panel) and
*patient-selection-invariant* (M-staging endpoint vs PFS endpoint),
**not biology-invariant** across diseases. We name this scoping
constraint explicitly in `docs/methodology.md §1`.

**What we do as cross-disease evidence.** The DIPG generalization
artifact (`results/external_validation_dipg/`, git SHA `8a4ecc5` locked
before engine output): 15 pre-registered rescue hypotheses on H3 K27M
diffuse midline glioma, 7 supported / 7 mixed / 1 rejected. Same 4-role
engine, structurally distant disease, same rejection-as-product
pattern.

**Evidence.**
- [`docs/methodology.md` §1](methodology.md) — explicit cohort scoping
- [`results/external_validation_dipg/RESULTS.md`](../results/external_validation_dipg/RESULTS.md) — DIPG full results
- Anchor regression cross-cohort stability: `methodology.md` § "Anchor regression"

---

## Q5 — "Could Sonnet 4.6 replace Opus 4.7 here?" <a id="q5"></a>

**Honest answer.** No, and we have the empirical case in 180 calls.

**The data.** Same 6 candidates × 10 repeats × 3 models = 180 calls
(`results/ablation/SUMMARY.md`):

| model | PASS | dissent_on_gate_PASS_pct |
|---|---|---|
| `claude-opus-4-7` | **10 / 60** | 66.7% |
| `claude-haiku-4-5` | 14 / 60 | 53.3% |
| `claude-sonnet-4-6` | **0 / 60** | **100.0%** |

Sonnet dissents on 100% of gate-PASS candidates — it cannot hold the
review stance across the dual-role prompt and collapses into permanent
rejection, even with extended thinking budget. Opus 4.7 dissents
calibratedly: PASS when the gate output warrants it, dissent when the
margin is thin.

**Two important caveats.** (1) The Opus 4.7 ablation calls returned
HTTP 400 on `enabled` thinking and fell back to no-thinking; the gap
is therefore Opus 4.7 *base calibration* vs Sonnet 4.6 with thinking.
Opus wins anyway, which is the cleaner result. (2) PhL-15v2 isolates
thinking mode and finds it does not change verdict distribution on
this prompt — the load-bearing variable is **prompt context richness +
RLHF base calibration**, not thinking budget.

**Evidence.**
- [`results/ablation/SUMMARY.md`](../results/ablation/SUMMARY.md) — full E2 results
- [`docs/why_opus_4_7.md` §0](why_opus_4_7.md) — interpretation + caveats
- [`results/live_evidence/phl15_adaptive_thinking/SUMMARY.md`](../results/live_evidence/phl15_adaptive_thinking/SUMMARY.md) — thinking ablation

---

## Q6 — "Did Opus 4.7 just memorize TOP2A−EPAS1 from training data?" <a id="q6"></a>

**Honest answer.** Tested directly, no. PhL-13 memorization audit:
Opus 4.7 was prompted to retrieve a 2-gene compact ccRCC metastasis
law without any data context. **0/10 repeats returned `TOP2A − EPAS1`**;
none of the returned guesses match the survivor pair.

This refutes the LLM-SRBench memorization concern: the law is not
recoverable from Opus's pre-training memory; it is recoverable only by
running PySR symbolic search on the data with the gate adjudicating.

**Evidence.**
- `results/live_evidence/phl13_memorization/` — full transcript
- [`docs/submission_form_draft.md`](submission_form_draft.md) Opus 4.7 usage section — PhL-13 line

---

## Q7 — "Why no prospective validation?"

Out of scope for a 5-day hackathon. We commit:
- All thresholds in git before the analysis ran (`preregistrations/*.yaml`).
- Cross-cohort replay where independent data exists (IMmotion150 PFS).
- Self-kill on our own H1 LLM-SR extension (PhL-1, the 3-gene SLC22A8
  variant fails the same survival gate, C-index drops to 0.566).

The DIPG top-lead (panobinostat-CED-MTX110, score 13/15) names
Dr. Mark Souweidane (pioneer of convection-enhanced delivery for
pediatric brain tumors) as the deployment pathway — wet-lab validation
remains a separate post-hackathon track.

---

## Q8 — "No `.claude/commands/`?"

`.claude/commands/` is a personal-workflow primitive (Boris Cherny
documents using it himself, [X thread](https://x.com/bcherny)). It is
not a winning-submission requirement: the 1st-place Opus 4.6 winner
CrossBeam ([github.com/mikeOnBreeze/cc-crossbeam](https://github.com/mikeOnBreeze/cc-crossbeam))
ships with `.claude/skills/` only, no `commands/`.

We ship 4 sub-agents (`agents/proposer.md`,
`agents/skeptic-reviewer.md`, `agents/interpreter.md`,
`agents/qa-validator.md`) plus the `falsification-gate` skill — both
extension surfaces Boris validates in his
[Pragmatic Engineer interview](https://newsletter.pragmaticengineer.com/p/building-claude-code-with-boris-cherny).

---

## Q9 — "No web UI?"

By design. Lydia Hallie's
[Frontend Masters Advanced Claude Code workshop](https://frontendmasters.com/workshops/advanced-claude-code/)
emphasises *"the mental model of what the harness does versus what the
model does"*. The Loom + GitHub repo + `make demo` flow keeps the
harness inspectable; a web UI would obscure the deterministic gate
that is the central artifact.

The judge-facing surfaces we *do* ship:
- 90-second Loom narration
- `make demo` end-to-end (no API key needed; synthetic-data path)
- `make test` (105 tests, ~90 s, audit clean)
- `theory-copilot persist-events` + `replay-events` CLI two-liner

---

## Q10 — "Path A `callable_agents` is research-preview only. Did you actually use it?"

No. The submitted run uses **public-beta features only**, per the
2026-04-23 hackathon fairness rule. Path A in our code executes as a
**sequential 3-session chain** (Proposer → Searcher → Skeptic), each
step a Path-B-shaped Managed Agents session, with structured-JSON
handoff between steps (`delegation_mode=sequential_fallback`, 706 s
wall, PhL-9v2 on real TCGA-KIRC).

The `_run_path_a_callable_agents` code path exists as an architectural
reference of the full Agent Teams shape (orchestrator with
`callable_agents=[Proposer, Searcher, Skeptic]`, `session.thread_created`
delegation events) and is gated behind `MANAGED_AGENTS_WAITLIST=approved`
— a client-side feature flag, not a platform toggle.

**Evidence.**
- [`docs/methodology.md` §4](methodology.md) — three-path architecture + fairness caveat
- `src/theory_copilot/managed_agent_runner.py` — `_run_path_a_callable_agents` body

---

## Q11 — "The E2 thinking mode was confounded. Doesn't that weaken the Opus claim?"

It clarifies the claim, doesn't weaken it. The honest unified finding
across E2 + PhL-15v2:

- **E2** (rich-context Skeptic prompt, no thinking on Opus due to
  HTTP 400 fallback): Opus 10/60 PASS vs Sonnet 0/60 PASS with full
  thinking.
- **PhL-15v2** (narrow-context Skeptic prompt, clean adaptive_max vs
  no_thinking comparison): both modes 0/60 PASS, 100% dissent — thinking
  does not change verdict distribution on narrow-context prompts.

Together: **prompt context richness + RLHF / pre-training base
calibration**, not thinking budget, is the capability-extraction
lever on this task. The Opus 4.7 base-calibration win is more durable
than a "thinking helps" claim would have been.

**Evidence.**
- [`docs/why_opus_4_7.md` §0](why_opus_4_7.md) — unified finding paragraph
- [`results/live_evidence/phl15_adaptive_thinking/SUMMARY.md`](../results/live_evidence/phl15_adaptive_thinking/SUMMARY.md)

---

## Q12 — "Is the 5-test gate really 5 tests if `delta_confound` is null?"

The 5-test gate is the *framework*; the *active legs* depend on data
availability. For the metastasis_expanded task, all 9 surviving
candidates have `delta_confound = null` because the task has no
non-degenerate covariate after cohort filtering. The active legs that
actually adjudicated those 9 survivors are: permutation null,
bootstrap CI lower-bound, sign-invariant best-single-feature baseline,
decoy-feature null — plus BH-FDR across candidates.

This is documented per-row in `results/track_a_task_landscape/metastasis_expanded/falsification_report.json`,
in the README "Honest scoping note", and in `docs/methodology.md §3`.
We do **not** claim the survivors cleared a covariate-controlled
incremental-AUC test on this task.

**Evidence.**
- [`docs/methodology.md` §3](methodology.md) — "Task-dependent active legs"
- `results/track_a_task_landscape/metastasis_expanded/falsification_report.json` — per-row legs

---

## What we explicitly do NOT claim

(Pulled from `docs/CLAIM_LOCK.md` — the canonical lock list for narration and forms.)

- Not a diagnostic biomarker
- Not a clinical decision tool
- Not novel ccRCC biology
- Not a replacement for prospective validation
- Not "194 of 204" — the number is 194 of 203
- Not "10 survivors" — the number is 9
- Not "full 5-test pass" — `delta_confound = null` for the metastasis survivors
- Not "callable_agents Path A in the submitted run" — sequential public-beta only
- Not "thinking mode caused the Opus calibration win" — base calibration + prompt context did
- Not "novel kidney cancer biology" — this is rediscovery under a falsification gate
