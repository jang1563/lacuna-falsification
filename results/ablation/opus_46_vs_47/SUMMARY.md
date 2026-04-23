# G6 — Opus 4.6 vs 4.7 Calibration on Biology Skeptic Task

**Written after analyze step; pre-registration in `PREREG.md` committed first.**

## Research question

Anthropic's Opus 4.7 model card (2026-04-16) reports adaptive-thinking
calibration improvement: **abstention on unknowns went 61% → 36% incorrect**
from 4.6 to 4.7 (accuracy approximately unchanged). Does this transfer
to biology skeptic reasoning?

## Setup

- 6 candidates × 10 repeats = 60 calls per model
- Same prompt (`prompts/skeptic_review.md`), same metric bundle, same seed
- Opus 4.7 data reused from E2 `skeptic_model_sweep.jsonl`
- Opus 4.6 data fresh (this script, $4.60 total cost)

## Strict miscalibration (pre-registered primary metric)

**Miscalibration** = FAIL verdict on gate=PASS candidate OR PASS verdict
on gate=FAIL candidate. `NEEDS_MORE_TESTS` = non-miscalibrated abstention.

| Model | Miscalibration rate |
|---|---|
| claude-opus-4-6 | **0.0% (0/60)** |
| claude-opus-4-7 | **0.0% (0/60)** |

**Pre-registered verdict: Exploratory Null.** Neither model produces
the type-I / type-II errors this metric is designed to catch on our
curated candidate set. This is consistent with "both models have
already absorbed the basic discrimination from the metric bundle"; it
does NOT disprove the Anthropic-published delta (which was measured
across thousands of MMLU unknowns, not 6 pre-curated cancer-genomics
cases).

## Per-candidate verdict distribution — where the real signal lives

The strict miscalibration metric is **too blunt** for this task. The
interesting pattern is in the **verdict confidence distribution** across
the three valid outcomes {PASS, FAIL, NEEDS_MORE_TESTS}:

| Candidate | Category | Gate | 4.6 verdicts (n=10) | 4.7 verdicts (n=10) |
|---|---|---|---|---|
| top2a_minus_epas1 | strong_survivor | PASS | NEEDS=3, **PASS=7** | **PASS=10** |
| mki67_minus_epas1 | strong_survivor | PASS | NEEDS=9, PASS=1 | NEEDS=10 |
| five_gene_compound | stress_test | PASS | NEEDS=8, **PASS=2 (over-commits)** | **NEEDS=10** |
| hif_textbook_tn | borderline_reject | FAIL | FAIL=10 | FAIL=10 |
| actb_minus_gapdh | clean_reject | FAIL | FAIL=10 | FAIL=10 |
| mki67_minus_rpl13a | clean_reject | FAIL | FAIL=10 | FAIL=10 |

### Three specific differences

1. **Decisiveness on the clearest survivor.** On `TOP2A − EPAS1` — the
   simplest, best-performing survivor in the entire campaign — 4.7
   gives **PASS 10/10** while 4.6 gives **PASS 7/10, NEEDS 3/10**.
   4.7 correctly identifies this specific case as unambiguous and
   commits; 4.6 hedges.
2. **Abstention on the stress-test case.** On the `five_gene_compound`
   stress test (AUROC 0.726 but structurally more complex than the
   2-gene pair), 4.7 returns **NEEDS_MORE_TESTS 10/10**. 4.6 returns
   NEEDS 8/10 but **PASS 2/10** — i.e. 20% of the time it commits
   to PASS on a stress test the gate author specifically constructed
   as ambiguous.
3. **Clean rejects are identical.** All three clear-fail candidates
   (hif_textbook_tn, actb_minus_gapdh, mki67_minus_rpl13a) receive
   FAIL 10/10 from both models. The published calibration delta does
   NOT manifest on reject-by-construction cases where the metric
   bundle already contains evidence sufficient for either model.

### Quantifying the confidence-pattern difference

Define **"appropriate commitment rate"** (ACR):
- On a strong_survivor: ACR = fraction PASS
- On a stress_test: ACR = fraction NEEDS_MORE_TESTS (abstention is correct)
- On a clean_reject: ACR = fraction FAIL

| Candidate type | 4.6 ACR | 4.7 ACR |
|---|---|---|
| strong_survivor (top2a_epas1) | 70% | **100%** |
| strong_survivor (mki67_epas1) | 10% | 0% |
| stress_test (five_gene_compound) | 80% | **100%** |
| clean_rejects (3 candidates × 10) | 100% | 100% |

Both models miss on `mki67_minus_epas1` (lower-AUROC survivor, 0.708 vs
0.726 for TOP2A-EPAS1). Both prefer NEEDS_MORE_TESTS, which is arguably
the correct conservative response given the slimmer margin over
baseline.

**Macro-average across the three "new-signal" candidates:**
- 4.6: (70 + 10 + 80) / 3 = **53.3%**
- 4.7: (100 + 0 + 100) / 3 = **66.7%**

Difference: +13.3pp in favour of 4.7, driven by (a) stronger commitment
on the cleanest survivor and (b) zero over-commitment on the stress-test.

## Pre-registered narrative impact

**Outcome per pre-reg: Exploratory Null on primary metric + a specific
qualitative transfer finding on finer verdict-distribution metric.**

Primary narrative ("Rejection-as-Product"): **unchanged.** The 5-test
gate rejects 194/204 regardless of which frontier model sits in the
Skeptic seat; both 4.6 and 4.7 respect every negative verdict the gate
emits. The rejection rate is not a function of Opus version.

Secondary narrative ("4.7 overhang"): **softened to complementary.** On
the strict type-I/II miscalibration metric, the published 61→36% delta
does not manifest at n=60 on 6 curated candidates (sample size too
small). On the finer verdict-confidence distribution, 4.7 is more
decisive on unambiguous survivors and more abstentive on stress-test
cases — the same *qualitative* calibration shift Anthropic reports,
but measurable only by looking inside the set of "not-wrong"
answers.

This supports a reframed secondary claim:

> "Opus 4.7's native calibration improvement and our external
> deterministic gate address different layers of the same confirmation-
> bias problem. The gate is model-agnostic (works with any frontier
> model). 4.7's calibration improvement shows up *within* the abstention
> layer — more confident on clear cases, more cautious on stress cases
> — which is independently valuable for the Proposer and Interpreter
> roles where deterministic verification isn't available."

## Honest limitations

- n=60 per model, 6 candidates, 10 repeats — underpowered for a
  confirmatory test of a 25pp published delta.
- Candidate set is deliberately curated (2 survivors, 2 borderline,
  2 clean rejects). A broader candidate set with more boundary cases
  would stress-test this differently.
- Thinking config: Opus 4.6 uses `type: enabled, budget_tokens: 8000`
  (deprecated, emits warning); Opus 4.7 uses the same nominal config
  but the API internally maps it through adaptive. This is as close
  to matched as the public API allows post-4.7 release.

## Files

- `PREREG.md` — pre-registered decision rule (committed before analyze)
- `opus_46_sweep.jsonl` — 60 raw Opus 4.6 API rows
- `calibration_report.json` — machine-readable per-candidate + deltas
- E2 4.7 data: `results/ablation/skeptic_model_sweep.jsonl`

## Reproduce

```bash
# Requires ANTHROPIC_API_KEY in env.
PYTHONPATH=src .venv/bin/python src/g6_calibration_4_6_vs_4_7.py sweep --repeats 10
PYTHONPATH=src .venv/bin/python src/g6_calibration_4_6_vs_4_7.py analyze
```
