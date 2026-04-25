---
name: falsification-gate
description: "Use this skill whenever a candidate biological law, compact equation, symbolic-regression survivor, or gene-expression classifier needs to be subjected to the pre-registered 5-test falsification gate (permutation null, bootstrap CI lower bound, sign-invariant best-single-feature baseline, incremental-covariate confound, decoy-feature null) and logged as a pass/fail verdict. TRIGGER when: the user asks to falsify, reject, gate, or stress-test a candidate law; the user hands you an equation plus a metric bundle (perm_p, ci_lower, delta_baseline, confound_delta, decoy_p); the user asks 'does this survive the falsification gate?'; a PySR run emits candidates that need adjudication; the user mentions the TOP2A-EPAS1 survivor, the 11-gene or 45-gene panel, or the pre-registered thresholds. SKIP when: the user wants to propose new law families (that's the Proposer), write a mechanism hypothesis (that's the Interpreter), or is asking a general statistics question not bound to this repo's pre-registered thresholds."
when_to_use: "Also triggers on: 'audit this claim', 'audit this candidate', 'would this hold up?', 'hold up against the gate?', 'is this PASS or FAIL?', 'verify the verdict', 'does this candidate survive?'. If the user has a hypothesis but no metric bundle yet, route to `pre-register-claim` first to lock the kill-tests, then return here once metrics are computed."
allowed-tools: Read, Grep, Bash
---

# Falsification gate — pre-registered 5-test adjudicator

You are invoking the Theory Copilot pre-registered falsification gate. The
thresholds below were committed to `src/theory_copilot/falsification.py`
before any fit was run. **You do not re-negotiate them. You apply them.**

## What this skill does

Given a candidate equation and its metric bundle, apply the 5-test gate
and append a single pass/fail verdict row to the rejection log at
`results/live_evidence/skill_verdicts.jsonl`. No threshold is ever
softened; no test is ever skipped without recording `null` for the
inactive leg.

## Pre-registered thresholds (load-bearing — do not edit)

Read `src/theory_copilot/falsification.py` before applying. As of the
`emitted_git_sha` in the latest `preregistrations/*.yaml`:

| Test                   | Statistic                                                                  | Threshold          |
| ---------------------- | -------------------------------------------------------------------------- | ------------------ |
| `label_shuffle_null`   | Two-sided permutation p (1000 shuffles)                                    | `perm_p < 0.05`    |
| `bootstrap_stability`  | Lower bound of 95% percentile CI on sign-invariant AUROC (1000 resamples) | `ci_lower > 0.6`   |
| `baseline_comparison`  | `law_AUROC − max_i max(AUROC(x_i), 1 − AUROC(x_i))`                         | `delta_auroc > 0.05` |
| `confound_only`        | Incremental AUC: `AUROC(LR(cov+law)) − AUROC(LR(cov))`                     | `delta_auroc > 0.03` |
| `decoy_feature_test`   | p vs AUROC distribution of 100 random features at matched scale            | `p < 0.05`         |

Across-candidate permutation p-values are adjusted with Benjamini-Hochberg
FDR (α = 0.1). The gate uses the FDR-adjusted `perm_p`, not the raw one.

## Contract

### Input

The invoking turn must hand you a JSON object shaped like:

```json
{
  "candidate_id": "top2a_minus_epas1",
  "equation": "TOP2A - EPAS1",
  "variables": ["TOP2A", "EPAS1"],
  "metrics": {
    "perm_p": 0.001,
    "perm_p_fdr": 0.009,
    "ci_lower": 0.665,
    "delta_baseline": 0.069,
    "delta_confound": null,
    "decoy_p": 0.0
  },
  "dataset_sha256": "<from data/SHA256SUMS>",
  "prereg_id": "<preregistrations/*.yaml id>"
}
```

If any field is missing, **stop and ask** — do not guess defaults. A gate
that runs on imputed thresholds is not a gate.

### Algorithm (deterministic — no LLM judgement)

1. Read `src/theory_copilot/falsification.py::passes_falsification` and
   confirm thresholds match this SKILL.md's table. If they have drifted,
   STOP and report a pre-registration integrity violation.
2. Apply each threshold to the supplied metric. For an inactive leg
   (value is `null`, e.g. `delta_confound` on a cohort without
   non-degenerate covariates), record `null` in the verdict and do
   NOT treat a `null` as PASS.
3. Aggregate: the candidate `passes` iff every active leg clears its
   threshold AND the FDR-adjusted `perm_p` clears 0.05.
4. If `passes=false`, enumerate every failing leg (comma-separated) in
   `fail_reason`. Do not summarize.

### Output (MUST be committed to the log, not just printed)

Append one JSONL row to `results/live_evidence/skill_verdicts.jsonl`:

```json
{
  "event": "verdict",
  "timestamp_utc": "<iso8601>",
  "candidate_id": "<from input>",
  "equation": "<from input>",
  "passes": true|false,
  "fail_reason": "<comma-separated failing legs, or empty string>",
  "thresholds_applied": {
    "perm_p": 0.05,
    "ci_lower": 0.6,
    "delta_baseline": 0.05,
    "delta_confound": 0.03,
    "decoy_p": 0.05
  },
  "metrics_supplied": {...input.metrics...},
  "prereg_id": "<input.prereg_id>",
  "dataset_sha256": "<input.dataset_sha256>",
  "gate_source_sha": "<git rev-parse HEAD of src/theory_copilot/falsification.py>"
}
```

The `event` field is the schema discriminator for `skill_verdicts.jsonl`:
this skill emits `event: "verdict"`; `pre-register-claim` emits
`event: "preregistered"`. Downstream parsers should branch on `event`.

Use `Bash` with `date -u +%Y-%m-%dT%H:%M:%SZ` for the timestamp and
`git log -1 --format=%H -- src/theory_copilot/falsification.py` for
the gate source SHA. Append with `>>`, never overwrite.

## Role boundary (important)

You are NOT the Skeptic subagent. The Skeptic (`.claude/agents/skeptic-reviewer.md`)
reviews borderline cases with LLM judgement and can emit
`NEEDS_MORE_TESTS`. This skill is deterministic: PASS or FAIL only, no
third option. If the metric bundle is borderline, the skill still emits a
binary verdict — downstream human review or the Skeptic subagent decides
what to do with a marginal pass.

## Why this exists

> *A loop that cannot reject is not a loop — it is a pipeline.*

The same thresholds that rejected 100+ candidates on TCGA-KIRC
(including the textbook HIF-axis law `log1p(CA9)+log1p(VEGFA)−log1p(AGXT)`)
also accepted the 2-gene survivor `TOP2A − EPAS1` on the 45-gene
metastasis panel. Pre-registration must bite on both sides.

## Example invocation

```
/falsification-gate on candidate "MKI67 − EPAS1" with
{"perm_p": 0.002, "ci_lower": 0.623, "delta_baseline": 0.051,
 "delta_confound": null, "decoy_p": 0.0}
```

The skill reads the thresholds from falsification.py, compares each
supplied metric to its threshold, and writes:

```json
{"passes": true, "fail_reason": "", ...}
```

## References

- `src/theory_copilot/falsification.py` — load-bearing thresholds.
- `docs/methodology.md §3` — full per-test rationale and caveats.
- `docs/survivor_narrative.md` — worked accept/reject examples.
- `preregistrations/*.yaml` — per-task emitted_git_sha binding.
