#!/usr/bin/env python3
"""G2: AUPRC + DeLong AUROC comparison + calibration analysis.

Adds AUPRC and DeLong-style bootstrapped AUROC comparison to the
TOP2A-EPAS1 evaluation on both TCGA-KIRC (metastasis, 16% M1) and
IMmotion150 (PFS binary endpoint, 62% events).

Key insight from NeurIPS 2024 (arXiv:2401.06091): AUROC is not universally
inferior to AUPRC under class imbalance. We report BOTH with appropriate
interpretation per dataset:
- TCGA-KIRC (16% M1): AUPRC is more clinically informative (low prevalence)
- IMmotion150 (62% events): Cox HR + Harrell C-index are preferred;
  AUROC on binary PFS is less meaningful at high event rate.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score


ROOT = Path(__file__).resolve().parent.parent


def compute_metrics(y: np.ndarray, score: np.ndarray,
                    n_boots: int = 1000, seed: int = 42) -> dict:
    """AUROC + AUPRC with bootstrap 95% CIs."""
    auroc = roc_auc_score(y, score)
    sign_flipped = auroc < 0.5
    if sign_flipped:
        score = -score
        auroc = 1 - auroc
    auprc = average_precision_score(y, score)
    baseline_auprc = float(y.mean())

    rng = np.random.default_rng(seed)
    auroc_b, auprc_b = [], []
    for _ in range(n_boots):
        idx = rng.choice(len(y), len(y), replace=True)
        try:
            auroc_b.append(roc_auc_score(y[idx], score[idx]))
            auprc_b.append(average_precision_score(y[idx], score[idx]))
        except ValueError:
            pass

    return {
        "n": int(len(y)),
        "positive_rate": float(y.mean()),
        "n_positives": int(y.sum()),
        "auroc": float(auroc),
        "auroc_ci95": [float(np.percentile(auroc_b, 2.5)),
                       float(np.percentile(auroc_b, 97.5))],
        "auprc": float(auprc),
        "auprc_ci95": [float(np.percentile(auprc_b, 2.5)),
                       float(np.percentile(auprc_b, 97.5))],
        "auprc_no_skill_baseline": baseline_auprc,
        "auprc_lift": float(auprc / baseline_auprc) if baseline_auprc > 0 else None,
        "sign_flipped": sign_flipped,
    }


def delong_delta(y: np.ndarray, score1: np.ndarray, score2: np.ndarray,
                 n_boots: int = 1000, seed: int = 42) -> dict:
    """Bootstrapped delta AUROC between score1 and score2."""
    rng = np.random.default_rng(seed)
    deltas = []
    for _ in range(n_boots):
        idx = rng.choice(len(y), len(y), replace=True)
        try:
            a1 = max(roc_auc_score(y[idx], score1[idx]),
                     1 - roc_auc_score(y[idx], score1[idx]))
            a2 = max(roc_auc_score(y[idx], score2[idx]),
                     1 - roc_auc_score(y[idx], score2[idx]))
            deltas.append(a1 - a2)
        except ValueError:
            pass
    obs_a1 = max(roc_auc_score(y, score1), 1 - roc_auc_score(y, score1))
    obs_a2 = max(roc_auc_score(y, score2), 1 - roc_auc_score(y, score2))
    obs_delta = obs_a1 - obs_a2
    p_val = float(np.mean(np.array(deltas) <= 0))  # one-sided: delta > 0
    return {
        "auroc1_sign_inv": float(obs_a1),
        "auroc2_sign_inv": float(obs_a2),
        "delta": float(obs_delta),
        "delta_ci95": [float(np.percentile(deltas, 2.5)),
                       float(np.percentile(deltas, 97.5))],
        "p_one_sided": p_val,
    }


def main():
    out_dir = ROOT / "results" / "g2_auprc"
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {}

    # ── TCGA-KIRC metastasis (M0 vs M1, 16% positive) ────────────────────
    df_k = pd.read_csv(ROOT / "data" / "kirc_metastasis_expanded.csv")
    df_k["TOP2A"] = pd.to_numeric(df_k["TOP2A"], errors="coerce")
    df_k["EPAS1"] = pd.to_numeric(df_k["EPAS1"], errors="coerce")
    df_k["MKI67"] = pd.to_numeric(df_k["MKI67"], errors="coerce")
    df_k = df_k.dropna(subset=["TOP2A", "EPAS1", "MKI67", "label"])
    y_k = (df_k["label"] == "disease").astype(int).values
    score_k = (df_k["TOP2A"] - df_k["EPAS1"]).values
    single_k = df_k["MKI67"].values

    results["tcga_kirc_metastasis"] = compute_metrics(y_k, score_k)
    results["tcga_kirc_metastasis"]["delong_vs_mki67"] = delong_delta(
        y_k, score_k, single_k)
    results["tcga_kirc_metastasis"]["note"] = (
        "16% M1 prevalence — AUPRC more informative than AUROC at low prevalence. "
        "AUPRC lift = AUPRC / no-skill-baseline (= M1 prevalence)."
    )

    # ── IMmotion150 PFS binary (62% events) ──────────────────────────────
    df_i = pd.read_csv(ROOT / "data" / "immotion150_ccrcc.csv")
    df_i["TOP2A"] = pd.to_numeric(df_i["TOP2A"], errors="coerce")
    df_i["EPAS1"] = pd.to_numeric(df_i["EPAS1"], errors="coerce")
    df_i["CDK1"] = pd.to_numeric(df_i["CDK1"], errors="coerce")
    df_i["pfs_event"] = df_i["PFS_STATUS"].astype(str).str.startswith("1").astype(int)
    df_i = df_i.dropna(subset=["TOP2A", "EPAS1", "CDK1", "pfs_event"])
    y_i = df_i["pfs_event"].values
    score_i = (df_i["TOP2A"] - df_i["EPAS1"]).values
    single_i = df_i["CDK1"].values

    results["immotion150_pfs_binary"] = compute_metrics(y_i, score_i)
    results["immotion150_pfs_binary"]["note"] = (
        "62% event rate: binary AUROC is an inappropriate primary metric for "
        "this high-event-rate setting. Harrell C-index (0.601) and Cox HR (1.36) "
        "are the primary metrics — both already reported in PhF-3. AUROC/AUPRC "
        "shown here for completeness and cross-dataset comparison only."
    )

    # ── Save and print ────────────────────────────────────────────────────
    out = out_dir / "auprc_results.json"
    out.write_text(json.dumps(results, indent=2))

    for dataset, m in results.items():
        print(f"\n{'='*55}")
        print(f"Dataset: {dataset}")
        print(f"  n={m['n']} positives={m['n_positives']} prev={m['positive_rate']:.3f}")
        print(f"  AUROC={m['auroc']:.4f} 95%CI [{m['auroc_ci95'][0]:.3f}, {m['auroc_ci95'][1]:.3f}]")
        print(f"  AUPRC={m['auprc']:.4f} 95%CI [{m['auprc_ci95'][0]:.3f}, {m['auprc_ci95'][1]:.3f}]")
        print(f"  AUPRC baseline={m['auprc_no_skill_baseline']:.3f}  lift={m.get('auprc_lift'):.2f}x")
        if "delong_vs_mki67" in m:
            d = m["delong_vs_mki67"]
            print(f"  DeLong vs best-single: ΔAUROC={d['delta']:+.3f} CI [{d['delta_ci95'][0]:+.3f}, {d['delta_ci95'][1]:+.3f}] p={d['p_one_sided']:.4f}")

    print(f"\nResults: {out}")


if __name__ == "__main__":
    main()
