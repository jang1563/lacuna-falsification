# Track B — Gate Robustness: Final Summary

**Scientific question:** is the 0-survivor / +0.029 incremental ceiling
verdict a property of the data, or an artifact of the gate's design?

**One-line answer:** the verdict is robust along four of the five axes
of design freedom (threshold, baseline definition, bootstrap seed,
cohort size) and soft along one (feature scaling on the tier2 task
under z-score). In practice the pre-registered gate's 0-survivor call
is defensible as a scientific finding about ccRCC compound-law
performance, not an artifact of a sharply chosen threshold.

---

## Experiment inventory

| Tag | Experiment | Artifact | Verdict |
|---|---|---|---|
| B1 | Threshold sensitivity grid (5 thresholds × varying values on 67 candidates) | `threshold_grid.csv`, `threshold_heatmap.png`, `threshold_grid_summary.json` | **delta_baseline is the sole operative constraint**; cliff at +0.030 (below +0.05 pre-reg) |
| B2 | Baseline definition ablation (sign_invariant_max, LR-single, LR-pair+interaction) | `baseline_ablation.csv`, `baseline_ablation_summary.json` | Verdict **hardens** under stronger baselines (flagship max Δ +0.029 → +0.010; tier2 → −0.005) |
| B3 | Permutation stability (n ∈ {200,500,1k,2k,5k} × 3 seeds × top 5 per source) | `permutation_stability.json` | (Run pending — results folded in when complete) |
| B4 | Bootstrap seed variance (20 candidates × 5 seeds × n_resamples=1000) | `bootstrap_seed_variance.json` | `ci_lower` stable to 3 decimals (max std 0.003); no seed-flip |
| B5 | Feature-scaling ablation (raw / zscore / rank / minmax) on 67 candidates | `scaling_ablation.csv`, `scaling_ablation_summary.json` | Flagship invariant; **tier2 × zscore** produces 1/34 survivor under reduced gate |
| B6 | Cohort-size subsampling (n ∈ {100, 200, 400, 600} × 5 seeds × HIF law) | `cohort_size_curve.json` | `ci_lower > 0.60` at every n tested; 0 survivors at every n |

## Headline answers to the brief's questions

### Is there any reasonable threshold configuration at which a survivor appears?

**Only if `delta_baseline` drops strictly below the empirical +0.029 ceiling.**
Grid values 0.000, 0.010, 0.020, 0.025 yield 15, 15, 11, 5 survivors
respectively; 0.030 and above yield 0. The flip happens below the
empirically observed max delta — there is no grey zone in which the
gate is "barely missing" survivors. Relaxing any of the other four
thresholds (ci_lower, perm_p_fdr, delta_confound, decoy_p) in isolation
does **not** produce a single survivor at any grid point.

### How stable is the verdict under permutation / bootstrap / scaling variation?

- **Bootstrap (B4):** `ci_lower` is seed-stable to the third decimal
  (max std 0.003, max range 0.008). No verdict flips across seeds
  for any of the 20 top candidates.
- **Permutation (B3):** results in follow-up commit; interim
  expectation is that law_auc values ≥ 0.98 (flagship) or ≈ 0.64
  (tier2) produce perm_p ≈ 0 at every n, making the gate's
  `perm_p_fdr < 0.05` boundary unaffected by permutation count.
- **Scaling (B5):** flagship max Δ stays in [+0.025, +0.030] across
  all four scalings. **tier2 × zscore** raises max Δ to +0.055,
  passing the reduced-gate threshold for one candidate. Other three
  tests (ci_lower, delta_confound, decoy_p, perm_p_fdr) must
  additionally hold under zscore scaling — those are not re-checked
  here and remain a caveat in the SUMMARY narrative.

### What's the minimum cohort size that keeps `ci_lower > 0.6`?

**All tested sizes (n ≥ 100) keep `ci_lower > 0.6`.** At n=100 the
Opus ex-ante HIF/angiogenesis law's ci_lower mean is 0.955 (min 0.927).
The gate's stability floor is not the limiting factor anywhere in the
range probed; `delta_baseline > 0.05` is what rejects the law at
every cohort size.

### Is +0.029 ceiling robust or soft?

**Robust along four of five design axes; soft along one.**

- **Robust:** threshold grid (cliff at empirical max, no gray zone),
  baseline definition (+0.029 → +0.010 under pair+interaction LR;
  compound advantage shrinks rather than grows), bootstrap seed
  (3-decimal stability), cohort size (n down to 100 keeps the gate's
  stability floor).
- **Soft:** feature scaling on tier2 — z-score bumps max delta to
  +0.055, the only configuration in the analysis that crosses the
  pre-registered +0.05 threshold. This is confined to the stage
  classification task; the flagship (tumor-vs-normal) verdict is
  unaffected by scaling.

### Net narrative

The headline 0-survivor verdict in `results/RESULTS.md` is a
data-level property, not a threshold-level artifact. Relaxing the
delta_baseline threshold to the empirical ceiling, strengthening the
baseline to a pair+interaction LR, or dropping the cohort to 100
samples all leave the verdict intact. The only design knob that
materially shifts tier2 is feature scaling — and even there the
flagship task remains invariant.

For the submission narrative, the +0.029 ceiling on flagship can be
stated plainly: "any reasonable pre-registration of the gate would
reach the same conclusion." On tier2, honesty requires noting that
scaling-choice alone can flip one candidate under a reduced-gate
reading; the full 5-test gate still needs to be re-applied under
zscore to confirm the rejection holds.

---

## Figures (judge-facing visuals)

- `threshold_heatmap.png` — B1, 67 candidates × 32 threshold scenarios
  (pass=green, fail=red). Reading: the entire column for the current
  `delta_baseline=0.05` threshold is red; relaxing that threshold past
  the empirical cliff turns rows progressively green.
- `b2_baseline_ablation.png` — bar chart of max delta_baseline per
  (task, baseline_kind). Pair+interaction baseline flattens the
  flagship advantage (+0.029 → +0.010) and turns tier2 negative.
- `b4_bootstrap_seed_variance.png` — scatter of 5-seed ci_lower per
  candidate; the 0.60 gate line separates flagship (all well above)
  from tier2 (all well below). Seed scatter is invisible at plot scale.
- `b5_scaling_ablation.png` — max delta_baseline by (task, scaling);
  the tier2 × zscore bar is the only one that crosses the 0.05 line.
- `b6_cohort_size_curve.png` — law_auc and ci_lower vs n (left);
  delta_baseline vs n (right). ci_lower stays well above 0.60;
  delta stays well below 0.05 at every tested cohort size.

## Artifacts

All outputs under `results/track_b_gate_robustness/`:

```
SUMMARY.md                        (this file)
threshold_grid.csv                (B1) 1809 rows, candidate × scenario
threshold_heatmap.png             (B1) 67 × 32 pass/fail grid
threshold_grid_summary.json       (B1) flip curves by threshold
baseline_ablation.csv             (B2) 201 rows, 67 candidates × 3 baselines
baseline_ablation_summary.json    (B2) task-level baseline AUCs + survivor counts
b2_baseline_ablation.png          (B2) bar chart max delta per baseline kind
permutation_stability.json        (B3) pending
bootstrap_seed_variance.json      (B4) 20 candidates × 5 seeds
b4_bootstrap_seed_variance.png    (B4) per-candidate seed scatter
scaling_ablation.csv              (B5) 268 rows
scaling_ablation_summary.json     (B5) per (task, scaling) survivors
b5_scaling_ablation.png           (B5) bar chart max delta per scaling
cohort_size_curve.json            (B6) 4 sizes × 5 seeds
b6_cohort_size_curve.png          (B6) dual-panel curves vs n
```

Code under `src/`:

```
gate_sensitivity.py               (B1)
track_b_baseline_ablation.py      (B2)
track_b_permutation_stability.py  (B3)
track_b_bootstrap_variance.py     (B4)
track_b_scaling_ablation.py       (B5)
track_b_cohort_size.py            (B6)
```

Progress log: `research/TRACK_B_progress.md`

---

*Draft v1 — 2026-04-22. Updated with B3 numbers when the permutation
scan finishes.*
