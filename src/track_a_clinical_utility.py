"""I3 Clinical utility translation of TOP2A−EPAS1.

Pre-registered in preregistrations/20260425T190301Z_i3_clinical_utility.yaml.

Translates AUROC into clinician-readable metrics:
- Cohen's d (effect size from AUROC: d = sqrt(2) · Φ⁻¹(AUROC))
- Odds ratio per 1-SD increase via logistic regression
- Threshold-based screening metrics (sensitivity, specificity, PPV, NPV, NNS)
  at top-decile and top-quintile cutoffs
- Confusion matrix at the top-quintile decision boundary
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, roc_auc_score

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data/kirc_metastasis_expanded.csv"
RESULTS = REPO / "results/track_a_task_landscape/clinical_utility"
RESULTS.mkdir(parents=True, exist_ok=True)


def cohens_d_from_auroc(auc: float) -> float:
    """Cohen's d = sqrt(2) · Φ⁻¹(AUROC).

    Hanley & McNeil 1982; standard AUC-to-d under Gaussian-marginals
    assumption. d is symmetric in the sign of the score.
    """
    return float(np.sqrt(2.0) * stats.norm.ppf(auc))


def metrics_at_threshold(y, score_oriented, top_frac: float) -> dict:
    n = len(y)
    k = int(np.ceil(top_frac * n))
    threshold = float(np.partition(score_oriented, -k)[-k])
    pred = (score_oriented >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    sens = float(tp) / max(tp + fn, 1)
    spec = float(tn) / max(tn + fp, 1)
    ppv = float(tp) / max(tp + fp, 1)
    npv = float(tn) / max(tn + fn, 1)
    nns = float("inf") if ppv == 0 else 1.0 / ppv
    return {
        "top_fraction": float(top_frac),
        "n_flagged": int(tp + fp),
        "threshold": threshold,
        "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn),
        "sensitivity": sens,
        "specificity": spec,
        "ppv": ppv,
        "npv": npv,
        "nns": nns,
    }


def main():
    df = pd.read_csv(DATA)
    y = (df["label"] == "disease").astype(int).to_numpy()
    n = len(y)
    prevalence = float(y.mean())
    print(f"Loaded n={n}, prevalence={prevalence:.3f}")

    # Z-score TOP2A and EPAS1, compute survivor score
    for g in ("TOP2A", "EPAS1"):
        assert g in df.columns, f"Missing {g}"
    top2a = df["TOP2A"].to_numpy()
    epas1 = df["EPAS1"].to_numpy()
    top2a_z = (top2a - top2a.mean()) / top2a.std()
    epas1_z = (epas1 - epas1.mean()) / epas1.std()
    score = top2a_z - epas1_z
    score_z = (score - score.mean()) / score.std()  # 1-SD scaling for OR

    # Sign-invariant orientation (matches gate's convention)
    raw_auc = float(roc_auc_score(y, score))
    auc_pos = max(raw_auc, 1.0 - raw_auc)
    score_oriented = score if raw_auc >= 0.5 else -score
    score_z_oriented = score_z if raw_auc >= 0.5 else -score_z
    print(f"AUROC (sign-inv): {auc_pos:.4f}")

    # Cohen's d from AUROC
    d = cohens_d_from_auroc(auc_pos)
    print(f"Cohen's d:        {d:.3f}")

    # OR per 1-SD increase via logistic regression (no regularization for raw OR)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        lr = LogisticRegression(penalty=None, max_iter=1000, solver="lbfgs")
        lr.fit(score_z_oriented.reshape(-1, 1), y)
    beta = float(lr.coef_[0, 0])
    or_per_sd = float(np.exp(beta))
    # 95% CI on OR via standard logistic inference
    # SE(β) computed from observed Fisher information; quick approximation:
    # SE ≈ sqrt(1 / sum(p̂(1-p̂)·x²))
    p_hat = lr.predict_proba(score_z_oriented.reshape(-1, 1))[:, 1]
    fisher = float(np.sum(p_hat * (1 - p_hat) * score_z_oriented ** 2))
    se = float(np.sqrt(1.0 / max(fisher, 1e-9)))
    or_ci_lo = float(np.exp(beta - 1.96 * se))
    or_ci_hi = float(np.exp(beta + 1.96 * se))
    print(f"OR per 1-SD:      {or_per_sd:.3f}  (95% CI {or_ci_lo:.3f}–{or_ci_hi:.3f})")

    # Threshold-based metrics at top decile (10%) and top quintile (20%)
    m_dec = metrics_at_threshold(y, score_oriented, 0.10)
    m_qui = metrics_at_threshold(y, score_oriented, 0.20)
    print(f"\nTop decile (n={m_dec['n_flagged']}):")
    print(f"  sensitivity={m_dec['sensitivity']:.3f}  specificity={m_dec['specificity']:.3f}  PPV={m_dec['ppv']:.3f}  NPV={m_dec['npv']:.3f}  NNS={m_dec['nns']:.2f}")
    print(f"Top quintile (n={m_qui['n_flagged']}):")
    print(f"  sensitivity={m_qui['sensitivity']:.3f}  specificity={m_qui['specificity']:.3f}  PPV={m_qui['ppv']:.3f}  NPV={m_qui['npv']:.3f}  NNS={m_qui['nns']:.2f}")

    # Pre-registered prediction verdicts
    p1 = d > 0.7
    p2 = or_per_sd >= 2.0
    p3 = m_qui["sensitivity"] >= 0.50 and m_qui["specificity"] >= 0.85

    out = {
        "n_samples": n,
        "prevalence": prevalence,
        "auroc_sign_invariant": auc_pos,
        "cohens_d": d,
        "odds_ratio_per_1sd": {
            "estimate": or_per_sd,
            "log_or": beta,
            "se_log_or": se,
            "ci_lower_95": or_ci_lo,
            "ci_upper_95": or_ci_hi,
        },
        "top_decile": m_dec,
        "top_quintile": m_qui,
        "predictions": {
            "p1_cohens_d_gt_0p7": {"pass": bool(p1), "value": d, "threshold": 0.7},
            "p2_or_per_sd_ge_2": {"pass": bool(p2), "value": or_per_sd, "threshold": 2.0},
            "p3_top_quintile_sens_ge_0p5_spec_ge_0p85": {
                "pass": bool(p3),
                "sensitivity": m_qui["sensitivity"],
                "specificity": m_qui["specificity"],
                "thresholds": {"sensitivity": 0.50, "specificity": 0.85},
            },
        },
    }

    out_path = RESULTS / "clinical_metrics.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)

    print(f"\n=== Pre-registered prediction verdicts ===")
    print(f"  P1 (Cohen's d > 0.7):                                     {'PASS' if p1 else 'FAIL'}  (d={d:.3f})")
    print(f"  P2 (OR per 1-SD ≥ 2.0):                                   {'PASS' if p2 else 'FAIL'}  (OR={or_per_sd:.3f})")
    print(f"  P3 (top-quintile sens ≥ 0.50 AND spec ≥ 0.85):            {'PASS' if p3 else 'FAIL'}")
    print(f"\nWrote: {out_path}")


if __name__ == "__main__":
    main()
