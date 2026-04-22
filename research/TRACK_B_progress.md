# Track B — Progress Log

## B1 — Threshold sensitivity grid  `2026-04-22`

**Code:** `src/gate_sensitivity.py`
**Artifacts:**
- `results/track_b_gate_robustness/threshold_grid.csv` (1,809 rows, long format)
- `results/track_b_gate_robustness/threshold_heatmap.png` (67 candidates × 32 scenarios)
- `results/track_b_gate_robustness/threshold_grid_summary.json`

**Inputs loaded (4 sources, 67 candidates):**

| Source | N | Path |
|---|---|---|
| flagship_pysr | 26 | `results/flagship_run/falsification_report.json` |
| tier2_pysr | 27 | `results/tier2_run/falsification_report.json` |
| opus_exante_flagship | 7 | `results/opus_exante/kirc_flagship_report.json` |
| opus_exante_tier2 | 7 | `results/opus_exante/kirc_tier2_report.json` |

Total 67, not the 60 the brief anticipated — Opus ex-ante is evaluated on
both the tumor-vs-normal and stage tasks (7 laws × 2 tasks = 14), making
26 + 27 + 14 = 67. All have the five gate metrics present.

### Headline (current pre-registered thresholds)
- **current_all** → **0 survivors** across all 67 candidates — confirms the
  RESULTS.md verdict.

### delta_baseline flip curve (operative constraint)

| threshold | survivors | by-source breakdown |
|---|---|---|
| 0.000 | 15 | 14 flagship_pysr + 1 opus_exante_flagship |
| 0.010 | 15 | same |
| 0.020 | 11 | flagship_pysr only |
| 0.025 | 5 | flagship_pysr only |
| **0.030** | **0** | **cliff** |
| 0.035 | 0 | — |
| 0.040 | 0 | — |
| 0.050 (current) | 0 | — |
| 0.060 | 0 | — |
| 0.080 | 0 | — |

Cliff at 0.030 is the empirical +0.029 ceiling described in RESULTS.md.
The verdict flips **strictly below** the empirical ceiling — there is no
gray zone between 0.030 and 0.050.

### Other thresholds (held at current for non-operative test)

| Threshold | Grid values | Survivors across grid |
|---|---|---|
| ci_lower | 0.50 … 0.70 | 0 at every value |
| perm_p_fdr | 0.01 … 0.10 | 0 at every value |
| delta_confound | 0.00 … 0.05 | 0 at every value |
| decoy_p | 0.01 … 0.10 | 0 at every value |

Relaxing any of the other four thresholds in isolation does not yield a
single survivor — `delta_baseline` is the sole operative constraint.

### One-line finding

The 0-survivor verdict is robust to *any* reasonable relaxation of the
four non-baseline thresholds and is robust to a ~40% relaxation of
`delta_baseline` (0.05 → 0.030). Survivors appear only when
`delta_baseline` drops below the empirical +0.029 ceiling.

### What's next (B2 — baseline definition ablation)

B1 treats the current sign-invariant max as fixed. B2 will re-derive
`delta_baseline` under two stronger baselines (LR-single and LR-pair+
interaction) to test whether the verdict flips when the *definition*
of "best single-gene baseline" changes, independent of threshold.
