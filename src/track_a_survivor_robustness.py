#!/usr/bin/env python3
"""Stress-test the Track A metastasis survivor ``TOP2A - EPAS1``.

Track B demonstrated that the 0-survivor verdict on the 11-gene flagship
reports is robust to 6 design axes. This script applies the same
methodology specifically to the new 9-survivor finding from the 45-gene
metastasis_expanded report, so we can claim the accept verdict is as
robust as the reject verdict was.

Axes:
  R1. Threshold grid — Δbase, ci_lower, perm_p, decoy_p — at what
      threshold does the survivor cluster collapse?
  R2. Baseline definition — re-compute Δbase under LR single-feature
      and LR pair-with-interaction; does the law still beat them?
  R3. Permutation count stability — does perm_p stay < 0.05 across
      n ∈ {200, 500, 1000, 2000, 5000}?
  R4. Bootstrap seed variance — ci_lower stability to 3 decimals?
  R5. Feature-scaling ablation — no-scale / z-score / rank / min-max.
  R6. Cohort-size subsample — at what n does ci_lower drop below 0.6?

Output: results/track_a_task_landscape/survivor_robustness/
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lacuna.falsification import (
    baseline_comparison,
    bootstrap_stability,
    decoy_feature_test,
    label_shuffle_null,
)


EXP_GENES = [
    "CA9","CA12","VEGFA","ANGPTL4","EPAS1","BHLHE40","DDIT4","NDUFA4L2",
    "LDHA","LDHB","SLC2A1","ENO1","ENO2","HK2","PFKP","ALDOA","PDK1","PGK1","PKM",
    "AGXT","ALB","CUBN","LRP2","PTGER3","CALB1","SLC12A1","SLC12A3","SLC22A8",
    "MKI67","CDK1","CCNB1","TOP2A","PCNA","MCM2",
    "COL4A2","SPP1","MMP9","S100A4","CXCR4",
    "PAX8","PAX2","KRT7",
    "ACTB","GAPDH","RPL13A",
]


def _auc_sign_inv(y, scores) -> float:
    a = roc_auc_score(y, scores)
    return float(max(a, 1 - a))


def _law_scores(X: np.ndarray, col_names: list[str]) -> np.ndarray:
    """Evaluate TOP2A - EPAS1 on the feature matrix."""
    name_to_col = {n: X[:, i] for i, n in enumerate(col_names)}
    return name_to_col["TOP2A"] - name_to_col["EPAS1"]


def _zscore(X: np.ndarray) -> np.ndarray:
    mean = X.mean(axis=0, keepdims=True)
    std = X.std(axis=0, keepdims=True)
    std = np.where(std < 1e-8, 1.0, std)
    return (X - mean) / std


def _rank(X: np.ndarray) -> np.ndarray:
    ranks = np.empty_like(X, dtype=float)
    for j in range(X.shape[1]):
        ranks[:, j] = pd.Series(X[:, j]).rank(pct=True).values
    return ranks


def _minmax(X: np.ndarray) -> np.ndarray:
    mn = X.min(axis=0, keepdims=True)
    mx = X.max(axis=0, keepdims=True)
    rng = mx - mn
    rng = np.where(rng < 1e-8, 1.0, rng)
    return (X - mn) / rng


def load_metastasis() -> tuple[np.ndarray, np.ndarray, list[str]]:
    df = pd.read_csv("data/kirc_metastasis_expanded.csv")
    y = (df["label"] == "disease").astype(int).values
    cols = [c for c in EXP_GENES if c in df.columns]
    X = df[cols].values.astype(float)
    return X, y, cols


def r1_threshold_grid(out: Path) -> dict:
    """Does the survivor cluster collapse at nearby thresholds?"""
    X, y, cols = load_metastasis()
    scores = _law_scores(X, cols)

    np.random.seed(7)
    perm_p, auc = label_shuffle_null(X, y, lambda a: _law_scores(a, cols), n_permutations=1000)
    ci_width, ci_lower, mean_auc = bootstrap_stability(
        X, y, lambda a: _law_scores(a, cols), n_resamples=1000
    )
    delta_baseline, law_auc, baseline_auc = baseline_comparison(
        X, y, lambda a: _law_scores(a, cols)
    )
    decoy_p, decoy_q95, _ = decoy_feature_test(
        X, y, lambda a: _law_scores(a, cols), n_decoys=500, seed=7
    )

    # Grid — report pass/fail of TOP2A-EPAS1 at each threshold.
    grid = {
        "delta_baseline": [0.00, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.10],
        "ci_lower":       [0.50, 0.55, 0.60, 0.65, 0.70, 0.75],
        "perm_p":         [0.001, 0.01, 0.05, 0.10, 0.20],
        "decoy_p":        [0.001, 0.01, 0.05, 0.10],
    }
    results = {
        "law": "TOP2A - EPAS1",
        "metrics": {
            "law_auc": law_auc,
            "baseline_auc": baseline_auc,
            "delta_baseline": delta_baseline,
            "ci_lower": ci_lower,
            "perm_p": perm_p,
            "decoy_p": decoy_p,
        },
        "grid_pass": {
            "delta_baseline": {str(t): bool(delta_baseline > t) for t in grid["delta_baseline"]},
            "ci_lower":       {str(t): bool(ci_lower > t) for t in grid["ci_lower"]},
            "perm_p":         {str(t): bool(perm_p < t) for t in grid["perm_p"]},
            "decoy_p":        {str(t): bool(decoy_p < t) for t in grid["decoy_p"]},
        },
    }
    out.write_text(json.dumps(results, indent=2))
    print(f"R1 -> {out}")
    return results


def r2_baseline_ablation(out: Path) -> dict:
    """Does the survivor still beat alternative baseline definitions?"""
    X, y, cols = load_metastasis()
    law = _law_scores(X, cols)
    law_auc = float(roc_auc_score(y, law))

    # Sign-invariant best single gene
    sign_inv = max(_auc_sign_inv(y, X[:, i]) for i in range(X.shape[1]))

    # LR single-feature best
    best_lr = 0.0
    best_lr_gene = ""
    for i, g in enumerate(cols):
        lr = LogisticRegression(max_iter=1000).fit(X[:, [i]], y)
        pred = lr.predict_proba(X[:, [i]])[:, 1]
        auc = float(roc_auc_score(y, pred))
        if auc > best_lr:
            best_lr = auc
            best_lr_gene = g

    # LR pair + interaction best
    best_pair = 0.0
    best_pair_tag = ""
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            Xij = np.column_stack([X[:, i], X[:, j], X[:, i] * X[:, j]])
            lr = LogisticRegression(max_iter=1000).fit(Xij, y)
            pred = lr.predict_proba(Xij)[:, 1]
            auc = float(roc_auc_score(y, pred))
            if auc > best_pair:
                best_pair = auc
                best_pair_tag = f"{cols[i]} x {cols[j]} +int"

    res = {
        "law": "TOP2A - EPAS1",
        "law_auc": law_auc,
        "baselines": {
            "sign_invariant_max_single_gene": float(sign_inv),
            "lr_single_best": {"auc": best_lr, "gene": best_lr_gene},
            "lr_pair_with_interaction_best": {"auc": best_pair, "pair": best_pair_tag},
        },
        "delta_vs_baseline": {
            "sign_invariant": float(law_auc - sign_inv),
            "lr_single_best": float(law_auc - best_lr),
            "lr_pair_interaction": float(law_auc - best_pair),
        },
        "survives_0p05_threshold_under_each_baseline": {
            "sign_invariant": bool(law_auc - sign_inv > 0.05),
            "lr_single_best": bool(law_auc - best_lr > 0.05),
            "lr_pair_interaction": bool(law_auc - best_pair > 0.05),
        },
    }
    out.write_text(json.dumps(res, indent=2))
    print(f"R2 -> {out}")
    return res


def r3_permutation_stability(out: Path) -> dict:
    X, y, cols = load_metastasis()
    fn = lambda a: _law_scores(a, cols)
    per_n = {}
    for n in [200, 500, 1000, 2000, 5000]:
        ps = []
        for seed in range(5):
            np.random.seed(seed * 101)
            p, _ = label_shuffle_null(X, y, fn, n_permutations=n)
            ps.append(float(p))
        per_n[str(n)] = {"ps": ps, "mean": float(np.mean(ps)), "max": float(np.max(ps))}
    res = {
        "law": "TOP2A - EPAS1",
        "per_n_permutations": per_n,
        "verdict_flip_at_0p05": any(v["max"] >= 0.05 for v in per_n.values()),
    }
    out.write_text(json.dumps(res, indent=2))
    print(f"R3 -> {out}")
    return res


def r4_bootstrap_variance(out: Path) -> dict:
    X, y, cols = load_metastasis()
    fn = lambda a: _law_scores(a, cols)
    results = []
    for seed in range(10):
        np.random.seed(seed * 17 + 1)
        ci_w, ci_lo, mean = bootstrap_stability(X, y, fn, n_resamples=1000)
        results.append({"seed": seed, "ci_width": float(ci_w), "ci_lower": float(ci_lo), "mean_auc": float(mean)})
    cil_values = [r["ci_lower"] for r in results]
    res = {
        "law": "TOP2A - EPAS1",
        "per_seed": results,
        "ci_lower_stats": {
            "min": float(min(cil_values)),
            "max": float(max(cil_values)),
            "mean": float(np.mean(cil_values)),
            "std": float(np.std(cil_values)),
        },
        "verdict_flip_at_0p6": any(v < 0.6 for v in cil_values),
    }
    out.write_text(json.dumps(res, indent=2))
    print(f"R4 -> {out}")
    return res


def r5_scaling(out: Path) -> dict:
    df = pd.read_csv("data/kirc_metastasis_expanded.csv")
    y = (df["label"] == "disease").astype(int).values
    cols = [c for c in EXP_GENES if c in df.columns]
    X_raw = df[cols].values.astype(float)
    ti = cols.index("TOP2A")
    ei = cols.index("EPAS1")

    per_scale = {}
    for name, Xs in [
        ("raw", X_raw),
        ("zscore", _zscore(X_raw)),
        ("rank", _rank(X_raw)),
        ("minmax", _minmax(X_raw)),
    ]:
        law = Xs[:, ti] - Xs[:, ei]
        law_auc = float(roc_auc_score(y, law))
        baseline = max(_auc_sign_inv(y, Xs[:, i]) for i in range(Xs.shape[1]))
        per_scale[name] = {
            "law_auc": law_auc,
            "baseline_auc": float(baseline),
            "delta_baseline": law_auc - float(baseline),
            "pass_0p05": bool(law_auc - baseline > 0.05),
        }
    res = {"law": "TOP2A - EPAS1", "per_scale": per_scale}
    out.write_text(json.dumps(res, indent=2))
    print(f"R5 -> {out}")
    return res


def r6_cohort_size(out: Path) -> dict:
    X, y, cols = load_metastasis()
    fn = lambda a: _law_scores(a, cols)
    per_n = {}
    rng = np.random.default_rng(3)
    for n in [100, 200, 300, 400, 505]:
        if n > X.shape[0]:
            continue
        cil_vals = []
        db_vals = []
        auc_vals = []
        for trial in range(5):
            idx = rng.choice(X.shape[0], size=n, replace=False)
            Xs = X[idx]
            ys = y[idx]
            # re-check that both classes present
            if len(np.unique(ys)) < 2:
                continue
            np.random.seed(trial * 11)
            _, ci_lo, _ = bootstrap_stability(Xs, ys, fn, n_resamples=500)
            db, law_auc, _ = baseline_comparison(Xs, ys, fn)
            cil_vals.append(float(ci_lo))
            db_vals.append(float(db))
            auc_vals.append(float(law_auc))
        per_n[str(n)] = {
            "ci_lower_mean": float(np.mean(cil_vals)) if cil_vals else None,
            "ci_lower_min": float(np.min(cil_vals)) if cil_vals else None,
            "delta_baseline_mean": float(np.mean(db_vals)) if db_vals else None,
            "law_auc_mean": float(np.mean(auc_vals)) if auc_vals else None,
        }
    res = {"law": "TOP2A - EPAS1", "per_n": per_n}
    out.write_text(json.dumps(res, indent=2))
    print(f"R6 -> {out}")
    return res


def main() -> None:
    out_dir = Path("results/track_a_task_landscape/survivor_robustness")
    out_dir.mkdir(parents=True, exist_ok=True)
    r1 = r1_threshold_grid(out_dir / "r1_threshold_grid.json")
    r2 = r2_baseline_ablation(out_dir / "r2_baseline_ablation.json")
    r3 = r3_permutation_stability(out_dir / "r3_permutation_stability.json")
    r4 = r4_bootstrap_variance(out_dir / "r4_bootstrap_variance.json")
    r5 = r5_scaling(out_dir / "r5_scaling.json")
    r6 = r6_cohort_size(out_dir / "r6_cohort_size.json")

    summary = {
        "law": "TOP2A - EPAS1",
        "task": "TCGA-KIRC metastasis M0 vs M1, n=505",
        "robust_at_default_threshold_0p05_delta_baseline": r1["grid_pass"]["delta_baseline"]["0.05"],
        "smallest_threshold_that_rejects_delta_baseline": next(
            (t for t in ["0.0", "0.01", "0.02", "0.03", "0.04", "0.05", "0.06", "0.07", "0.08", "0.1"]
             if not r1["grid_pass"]["delta_baseline"][t]),
            "robust even at 0.1",
        ),
        "survives_lr_single_baseline": r2["survives_0p05_threshold_under_each_baseline"]["lr_single_best"],
        "survives_lr_pair_interaction_baseline": r2["survives_0p05_threshold_under_each_baseline"]["lr_pair_interaction"],
        "perm_p_verdict_flip": r3["verdict_flip_at_0p05"],
        "bootstrap_ci_lower_verdict_flip": r4["verdict_flip_at_0p6"],
        "scaling_invariance": {s: v["pass_0p05"] for s, v in r5["per_scale"].items()},
        "min_cohort_size_still_passing": min(
            (int(n) for n, v in r6["per_n"].items()
             if v.get("ci_lower_min") is not None and v["ci_lower_min"] > 0.6
             and v.get("delta_baseline_mean", 0) > 0.05),
            default=None,
        ),
    }
    (out_dir / "SUMMARY.json").write_text(json.dumps(summary, indent=2))
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
