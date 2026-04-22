# E2 — Cross-model ablation on the Skeptic turn

**Status:** Pre-registered (predictions fixed before the sweep runs).

This document was written and committed *before* the 180-call API sweep. The
"Observed results" section below the marker is filled in after the sweep
completes, and any pre-registered prediction that is falsified by the data is
reported verbatim — the same discipline the rest of the repo applies to
symbolic-regression candidates.

## Why run this

`docs/why_opus_4_7.md` claims that Opus 4.7's extended-thinking budget is
load-bearing in the Skeptic role: it forces the model to cite specific metric
values rather than restate the Proposer's own rationale. Smaller models under
the same prompt and the same metric bundle should collapse toward
rubber-stamp agreement. This ablation converts that claim into a measurement.

## Design

- **Models (3):** `claude-opus-4-7`, `claude-sonnet-4-6`, `claude-haiku-4-5`.
  All three receive the same `prompts/skeptic_review.md` system prompt,
  the same metric bundle, and the same candidate equation.
- **Thinking:** all three models use `thinking={"type": "enabled",
  "budget_tokens": 8000}` so the comparison is about the underlying model,
  not about scratch-space availability.
- **Candidates (6):** chosen to span the pass / borderline / fail spectrum:
  1. `TOP2A − EPAS1` (strong survivor, metastasis_expanded)
  2. `MKI67 − EPAS1` (strong survivor, metastasis_expanded)
  3. `log1p(CA9) + log1p(VEGFA) − log1p(AGXT)` (textbook HIF law, borderline
     reject on tumor-vs-normal — Δbase small vs single-gene CA9)
  4. 5-gene compound `log1p(log1p(exp(MKI67 − exp((EPAS1 − PTGER3) + LRP2)
     − RPL13A)))) × 0.627` (stress test: same Δbase as the 2-gene survivor
     but more complex)
  5. `log1p(ACTB) − log1p(GAPDH)` (clean housekeeping null)
  6. `log1p(MKI67) − log1p(RPL13A)` (proliferation / housekeeping null)
- **Repeats:** 10 independent calls per (model, candidate), capturing
  within-model variance in the Skeptic's verdict and language.
- **Total calls:** 3 × 6 × 10 = **180**.
- **Parallelism:** `ThreadPoolExecutor(max_workers=6)` against the Anthropic
  streaming endpoint.
- **Measured per call:** verdict ∈ {PASS, FAIL, NEEDS_MORE_TESTS,
  UNCERTAIN, UNPARSED}, `reason_length_chars`, `metric_citation_count`
  (regex count of distinct metric names followed by a numeric value), cost.

## Pre-registered predictions

**Committed before any sweep call runs.** These are the thresholds the
headline table will be checked against after the sweep completes.

1. **Opus 4.7 cites ≥ 2 specific metric values in ≥ 70% of Skeptic
   critiques.** (Predicted: Opus's extended-thinking scratch space
   forces enumeration of specific metric values.)
2. **Sonnet 4.6 cites ≥ 2 specific metric values in 30–60% of critiques.**
   (Predicted: Sonnet is more specific than Haiku but less than Opus.)
3. **Haiku 4.5 cites ≥ 2 specific metric values in ≤ 30% of critiques.**
   (Predicted: Haiku produces shorter, higher-level critiques that restate
   rather than dissect.)
4. **On marginal-pass candidates (Δbase ∈ [0.04, 0.06]), Opus dissent rate
   ≥ 2× Haiku dissent rate.** Dissent = `verdict ∈ {FAIL, NEEDS_MORE_TESTS}`
   against a gate PASS.

### Falsification contract

If the data falsifies any prediction above, the "Observed results" section
reports the observed number verbatim and `docs/why_opus_4_7.md` §3 is edited
(single sentence; no narrative rewrite) to cite the actual finding. The
plan file's risk register already anticipates this outcome and treats it as
a rigor artefact rather than a setback — "extended thinking does not
measurably change Skeptic behaviour on this task" is itself a publishable
statement.

## Regex for specificity

A reason counts as "cites ≥ 2 specific metric values" if the text contains
two or more distinct metric names in
`{perm_p, perm_p_fdr, ci_lower, ci_width, delta_baseline, delta_confound,
decoy_p, decoy_q95, law_auc, baseline_auc, confound_auc, original_auc}`
each followed (within ~10 characters) by a numeric value.
Implementation: `src/track_a_model_ablation.py::count_metric_citations`.

This is a heuristic — it may miss citations written with awkward
punctuation or prose — but any systematic bias in the regex hits equally
across models, preserving inter-model comparability.

## Budget

Estimated at ~$40–80 per the plan; actual spend reported below. The
$10,000 overall hackathon budget absorbs this easily.

## How to reproduce

```
python src/track_a_model_ablation.py precompute
python src/track_a_model_ablation.py sweep --workers 6 --repeats 10
python src/track_a_model_ablation.py analyze
```

Per-call data in `results/ablation/skeptic_model_sweep.jsonl`.
Histogram of specificity per model in `plots/model_specificity_histogram.png`.
Precomputed metric bundles in `results/ablation/candidate_metrics.json`.

<!-- OBSERVED_RESULTS_BELOW -->
