"""I4 Information-theoretic analysis of TOP2A−EPAS1 compound.

Pre-registered in preregistrations/20260425T190552Z_i4_information_theory.yaml.

Histogram-based mutual information on quartile-discretized features +
Miller-Madow bias correction. Reports:
  I(TOP2A; y), I(EPAS1; y), I(TOP2A, EPAS1; y), I(TOP2A − EPAS1; y),
  synergy, compactness ratio.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data/kirc_metastasis_expanded.csv"
RESULTS = REPO / "results/track_a_task_landscape/information_theory"
RESULTS.mkdir(parents=True, exist_ok=True)


def quantile_bin(x: np.ndarray, n_bins: int) -> np.ndarray:
    """Quantile discretization: returns integer bin index in [0, n_bins-1]."""
    quantiles = np.quantile(x, np.linspace(0.0, 1.0, n_bins + 1))
    quantiles[0] = -np.inf
    quantiles[-1] = np.inf
    return np.digitize(x, quantiles[1:-1])


def mi_discrete(x_bins: np.ndarray, y: np.ndarray) -> tuple[float, int]:
    """MI between discrete x and binary y using counts (in nats).

    Returns (mi_nats, k_used) where k_used = number of joint cells with
    nonzero count, used for Miller-Madow bias correction.
    """
    n = len(y)
    # Joint (x, y) counts
    joint = np.zeros((int(x_bins.max()) + 1, 2), dtype=float)
    for xi, yi in zip(x_bins, y):
        joint[int(xi), int(yi)] += 1
    px = joint.sum(axis=1) / n
    py = joint.sum(axis=0) / n
    pxy = joint / n
    mi = 0.0
    k_used = 0
    for i in range(joint.shape[0]):
        for j in range(joint.shape[1]):
            if pxy[i, j] > 0 and px[i] > 0 and py[j] > 0:
                mi += pxy[i, j] * np.log(pxy[i, j] / (px[i] * py[j]))
                k_used += 1
    return mi, k_used


def miller_madow_correction(mi_nats: float, k_used: int, n: int) -> float:
    """Subtract (k-1) / (2n) bias term."""
    return mi_nats - (k_used - 1) / (2.0 * n)


def main():
    df = pd.read_csv(DATA)
    y = (df["label"] == "disease").astype(int).to_numpy()
    n = len(y)
    print(f"n={n}, prevalence={y.mean():.3f}")

    top2a = df["TOP2A"].to_numpy()
    epas1 = df["EPAS1"].to_numpy()

    # 4-bin quartile discretization for individual genes
    n_bins = 4
    top2a_bins = quantile_bin(top2a, n_bins)
    epas1_bins = quantile_bin(epas1, n_bins)

    # Individual MIs
    mi_t, k_t = mi_discrete(top2a_bins, y)
    mi_t_corrected = miller_madow_correction(mi_t, k_t, n)
    mi_e, k_e = mi_discrete(epas1_bins, y)
    mi_e_corrected = miller_madow_correction(mi_e, k_e, n)

    # Joint MI: encode (top2a_bin, epas1_bin) as a single integer
    joint_bins = top2a_bins * n_bins + epas1_bins  # 0..15
    mi_j, k_j = mi_discrete(joint_bins, y)
    mi_j_corrected = miller_madow_correction(mi_j, k_j, n)

    # Compound score MI: TOP2A − EPAS1 (z-scored), 8 quantile bins
    top2a_z = (top2a - top2a.mean()) / top2a.std()
    epas1_z = (epas1 - epas1.mean()) / epas1.std()
    score = top2a_z - epas1_z
    score_bins = quantile_bin(score, 8)
    mi_c, k_c = mi_discrete(score_bins, y)
    mi_c_corrected = miller_madow_correction(mi_c, k_c, n)

    # Synergy
    synergy = mi_j_corrected - mi_t_corrected - mi_e_corrected
    # Compactness
    compactness = mi_c_corrected / mi_j_corrected if mi_j_corrected > 0 else float("nan")

    print(f"\nI(TOP2A; y)        = {mi_t_corrected:.4f} nats")
    print(f"I(EPAS1; y)        = {mi_e_corrected:.4f} nats")
    print(f"I(joint; y)        = {mi_j_corrected:.4f} nats")
    print(f"I(TOP2A−EPAS1; y)  = {mi_c_corrected:.4f} nats")
    print(f"Synergy            = {synergy:.4f} nats")
    print(f"Compactness ratio  = {compactness:.3f}")

    # Pre-registered predictions
    max_indiv = max(mi_t_corrected, mi_e_corrected)
    p1 = mi_j_corrected > 1.25 * max_indiv
    p2 = synergy > 0
    p3 = compactness >= 0.70

    out = {
        "n_samples": n,
        "prevalence": float(y.mean()),
        "n_bins_individual": n_bins,
        "n_bins_compound": 8,
        "bias_correction": "miller_madow",
        "units": "nats",
        "mi": {
            "I_TOP2A_y_nats": mi_t_corrected,
            "I_EPAS1_y_nats": mi_e_corrected,
            "I_joint_y_nats": mi_j_corrected,
            "I_compound_y_nats": mi_c_corrected,
            "raw_uncorrected": {
                "I_TOP2A_y": mi_t,
                "I_EPAS1_y": mi_e,
                "I_joint_y": mi_j,
                "I_compound_y": mi_c,
            },
        },
        "synergy_nats": synergy,
        "compactness_ratio": compactness,
        "predictions": {
            "p1_joint_gt_1p25x_max_individual": {
                "pass": bool(p1),
                "joint_nats": mi_j_corrected,
                "max_individual_nats": max_indiv,
                "ratio": mi_j_corrected / max_indiv if max_indiv > 0 else float("nan"),
                "threshold_ratio": 1.25,
            },
            "p2_synergy_positive": {
                "pass": bool(p2),
                "synergy_nats": synergy,
            },
            "p3_compactness_ge_0p70": {
                "pass": bool(p3),
                "compactness": compactness,
                "threshold": 0.70,
            },
        },
    }

    out_path = RESULTS / "info_metrics.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)

    print(f"\n=== Pre-registered prediction verdicts ===")
    print(f"  P1 (joint > 1.25× max individual): {'PASS' if p1 else 'FAIL'}  ({mi_j_corrected/max_indiv:.2f}×)")
    print(f"  P2 (synergy > 0):                  {'PASS' if p2 else 'FAIL'}  ({synergy:+.4f} nats)")
    print(f"  P3 (compactness ≥ 0.70):           {'PASS' if p3 else 'FAIL'}  ({compactness:.3f})")
    print(f"\nWrote: {out_path}")


if __name__ == "__main__":
    main()
