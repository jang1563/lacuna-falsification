# Research Track B — Gate Robustness

**Goal:** characterize how robust the 0-survivor verdict is. Is the
+0.029 incremental ceiling a statistical artifact of our gate design,
or a real property of ccRCC compound laws?

**Scientific question:** if we had pre-registered a different gate
(different threshold, different baseline definition, different
permutation count, different feature scaling), would the verdict
change? If the verdict is invariant to reasonable design choices, the
0-survivor finding hardens. If it flips under mild threshold change,
we learn that our threshold was the operative constraint.

**Why this matters:** judges will ask, "would any survivors have
appeared if the threshold were +0.03?" We need a quantitative answer,
not a rhetorical one. And if the gate's 0-survivor verdict is robust,
that is itself a scientific claim worth a paragraph in the submission
narrative.

---

## File ownership (exclusive write)

| Path | Role |
|---|---|
| `src/gate_sensitivity.py` | Sweep the gate's five thresholds, re-emit per-candidate pass/fail with new thresholds |
| `src/track_b_*.py` | Any Track-B-specific helpers |
| `research/TRACK_B_*.md` | This brief + progress notes |
| `results/track_b_gate_robustness/**` | All Track B outputs |

**Read-only for this track:** everything under `src/lacuna/**`,
`src/pysr_sweep.py`, `src/falsification_sweep.py`, the existing
falsification reports under `results/flagship_run/`,
`results/tier2_run/`, `results/opus_exante/`. If a change in the
falsification module is needed, open `HANDOFF_to_shared.md`.

---

## Experiment list

### B1 — Threshold sensitivity grid

For each of the five gate tests, sweep the pre-registered threshold
across a range and re-tabulate the 60-candidate pass/fail at each
point. The existing `falsification_report.json` files already contain
the raw metrics (`perm_p_fdr`, `ci_lower`, `delta_baseline`,
`delta_confound`, `decoy_p`), so this requires no re-execution of the
gate — just re-applying `passes_falsification` with new thresholds.

Grids:
- `delta_baseline` threshold: 0.00, 0.01, 0.02, 0.025, 0.03, 0.035,
  0.04, 0.05 (current), 0.06, 0.08.
- `ci_lower` threshold: 0.50, 0.55, 0.60 (current), 0.65, 0.70.
- `perm_p_fdr` threshold: 0.01, 0.05 (current), 0.10.
- `delta_confound` threshold: 0.00, 0.01, 0.02, 0.03 (current), 0.05.
- `decoy_p` threshold: 0.01, 0.05 (current), 0.10.

Produce `results/track_b_gate_robustness/threshold_grid.csv` with
columns `candidate_id, source, threshold_name, threshold_value, pass`.

Produce `results/track_b_gate_robustness/threshold_heatmap.png`
with rows = candidates, columns = threshold scenarios, cell = pass/fail.

Key diagnostic: what's the smallest `delta_baseline` threshold at
which any candidate passes? Is it +0.030 (one-off flip) or +0.025
(small window of multiple flips)? The answer shapes the submission
narrative.

### B2 — Baseline definition ablation

Three alternative baselines:

1. **Current**: `max_i max(AUROC(x_i), 1 − AUROC(x_i))` — sign-invariant
   single-gene best.
2. **Logistic regression single-feature**: for each feature, fit
   `LR(x_i)` and take the best CV AUROC. Accounts for calibration.
3. **Logistic regression with 2-feature interaction**: for each pair
   `(x_i, x_j)`, fit `LR(x_i + x_j + x_i * x_j)` and take the best.
   This is a "strong linear + interaction" baseline against which
   compound laws have to beat.

Re-run `baseline_comparison`-equivalent under each definition on the
same 60 candidates. Produce `results/track_b_gate_robustness/baseline_ablation.csv`.

### B3 — Permutation stability

Re-run `label_shuffle_null` with n_permutations ∈ {200, 500, 1000,
2000, 5000} for the top 5 candidates from each source. Show the
distribution of p-values under resampling. Output:
`results/track_b_gate_robustness/permutation_stability.json`.

### B4 — Bootstrap seed variance

For the top 5 candidates, re-run `bootstrap_stability` with different
RNG seeds and check that the `ci_lower` estimate is stable to the
third decimal. Output:
`results/track_b_gate_robustness/bootstrap_seed_variance.json`.

### B5 — Feature-scaling ablation

The existing pipeline standardises within the cohort. Alternatives:

- **No transform** (raw log2 TPM / intensity).
- **Z-score within cohort** (current).
- **Rank-transform** (non-parametric; invariant to monotone transforms).
- **Min-max to [0, 1]**.

Re-run the falsification sweep under each scaling. Produce
`results/track_b_gate_robustness/scaling_ablation.csv`.

### B6 — Cohort-size effect

Subsample TCGA-KIRC tumor-vs-normal to n ∈ {100, 200, 400, 600} and
re-run the gate on the Opus ex-ante `kirc_hif_angiogenesis_log` law.
Does the 0-survivor verdict hold at smaller cohorts? Is there a
sample-size at which `ci_lower` drops below 0.60? Output:
`results/track_b_gate_robustness/cohort_size_curve.json`.

### B7 — Report

Write `results/track_b_gate_robustness/SUMMARY.md` answering:

- Is there any reasonable threshold configuration at which a survivor
  appears?
- How stable is the verdict under permutation / bootstrap / scaling
  variation?
- What's the minimum cohort size that keeps `ci_lower > 0.6`?
- One-paragraph verdict on "is +0.029 ceiling robust or soft?"

---

## Execution steps

### Step B1 — Pull + start

```bash
cd lacuna_discovery
git pull --rebase origin main
git status --short       # expect: nothing under src/gate_* or results/track_b_*
make audit
```

### Step B2 — Write `src/gate_sensitivity.py`

Reuse:
- `results/flagship_run/falsification_report.json`
- `results/tier2_run/falsification_report.json`
- `results/opus_exante/*.json`

All have raw metrics. No new data needed.

Function signatures to implement:

```python
def threshold_grid_pass(reports: list[dict], grids: dict) -> pd.DataFrame:
    """Return candidate-wise pass/fail under each threshold scenario."""

def baseline_alternative_auroc(X, y, kind: str) -> float:
    """`single_lr`, `pair_lr_interaction`, or `current_sign_invariant`."""

def permutation_stability_scan(X, y, equation_fn, ns: list[int]) -> dict:
    """Return p-value distribution across n_permutations values."""
```

### Step B3 — Run experiments B1–B6 sequentially or in parallel

Each writes its own CSV/JSON under `results/track_b_gate_robustness/`.

### Step B4 — Report + commit

Write `SUMMARY.md`, plot key figure, commit under `[Sci-B]` or `[T-B]`
prefix.

---

## Commit rules

- Prefix commit messages with `[Sci-B]` or `[T-B]`.
- Commit within one hour of starting a work block.
- `make audit` before every push.
- Never touch the other track's directories.
- Never touch `src/lacuna/**` or the canonical
  `falsification_sweep.py` without a `HANDOFF_to_shared.md` request.
