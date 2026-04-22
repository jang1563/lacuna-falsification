"""Track B — B2: Baseline definition ablation.

Re-tabulates `delta_baseline` for the 67 existing candidates under three
alternative baseline definitions, keeping each candidate's `law_auc` fixed
(already computed by the original falsification sweep).

Baselines:
    1. `sign_invariant_max`  — ``max_i max(AUC(x_i,y), 1-AUC(x_i,y))``
                                (replicates the current gate).
    2. `lr_single`           — for each feature, fit ``LR(x_i)`` with 5-fold
                                CV, take the best mean CV AUC across features.
    3. `lr_pair_interaction` — for each pair (i,j), fit
                                ``LR(x_i, x_j, x_i*x_j)`` with 5-fold CV, take
                                the best mean CV AUC across pairs.

Outputs (under results/track_b_gate_robustness/):
    - baseline_ablation.csv — per-candidate long table with new baselines and
      pass/fail under each.
    - baseline_ablation_summary.json — per-task baseline AUC + verdict under
      each baseline.

Usage:
    python src/track_b_baseline_ablation.py
"""

from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold


_DISEASE_TOKENS = {"disease", "tumor", "case", "cancer", "1", "true"}


# The pre-registered thresholds for the five gate tests (other than
# delta_baseline) stay fixed for this ablation.
CURRENT_THRESHOLDS: dict[str, float] = {
    "perm_p_fdr": 0.05,
    "ci_lower": 0.60,
    "delta_baseline": 0.05,
    "delta_confound": 0.03,
    "decoy_p": 0.05,
}


# Feature panels used by the original falsification sweep per task.
TASK_FEATURES: dict[str, list[str]] = {
    "flagship": ["CA9", "VEGFA", "LDHA", "NDUFA4L2", "SLC2A1", "ENO2", "AGXT", "ALB"],
    "tier2": [
        "CA9", "VEGFA", "LDHA", "NDUFA4L2", "SLC2A1", "ENO2", "AGXT", "ALB",
        "CUBN", "PTGER3", "SLC12A3",
    ],
}

TASK_DATA: dict[str, str] = {
    "flagship": "data/kirc_tumor_normal.csv",
    "tier2": "data/kirc_stage.csv",
}

# Maps each report source to its task.
SOURCE_TO_TASK: dict[str, str] = {
    "flagship_pysr": "flagship",
    "tier2_pysr": "tier2",
    "opus_exante_flagship": "flagship",
    "opus_exante_tier2": "tier2",
}

DEFAULT_SOURCES: list[tuple[str, str]] = [
    ("flagship_pysr", "results/flagship_run/falsification_report.json"),
    ("tier2_pysr", "results/tier2_run/falsification_report.json"),
    ("opus_exante_flagship", "results/opus_exante/kirc_flagship_report.json"),
    ("opus_exante_tier2", "results/opus_exante/kirc_tier2_report.json"),
]


def _parse_labels(series: pd.Series) -> np.ndarray:
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(int).values
    s = series.astype(str).str.strip().str.lower()
    return s.map(lambda v: 1 if v in _DISEASE_TOKENS else 0).values.astype(int)


def _safe_float(value: Any) -> float:
    if value is None:
        return np.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def load_candidates(sources: list[tuple[str, str]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for source_tag, path in sources:
        p = Path(path)
        if not p.exists():
            continue
        data = json.loads(p.read_text())
        for idx, entry in enumerate(data):
            if not isinstance(entry, dict):
                continue
            rows.append(
                {
                    "candidate_id": f"{source_tag}::{idx:03d}",
                    "source": source_tag,
                    "task": SOURCE_TO_TASK[source_tag],
                    "equation": entry.get("equation", ""),
                    "law_family": entry.get("law_family", ""),
                    "law_auc": _safe_float(entry.get("law_auc")),
                    "baseline_auc_current": _safe_float(entry.get("baseline_auc")),
                    "delta_baseline_current": _safe_float(entry.get("delta_baseline")),
                    "ci_lower": _safe_float(entry.get("ci_lower")),
                    "perm_p_fdr": _safe_float(entry.get("perm_p_fdr")),
                    "delta_confound": _safe_float(entry.get("delta_confound")),
                    "decoy_p": _safe_float(entry.get("decoy_p")),
                }
            )
    return pd.DataFrame(rows)


def sign_invariant_single_auc(x: np.ndarray, y: np.ndarray) -> float:
    auc = roc_auc_score(y, x)
    return max(auc, 1.0 - auc)


def baseline_sign_invariant_max(X: np.ndarray, y: np.ndarray) -> tuple[float, dict[str, Any]]:
    per_feat = np.array([sign_invariant_single_auc(X[:, j], y) for j in range(X.shape[1])])
    best_idx = int(np.argmax(per_feat))
    return float(per_feat[best_idx]), {"best_feature_index": best_idx, "per_feature": per_feat.tolist()}


def baseline_lr_single(
    X: np.ndarray, y: np.ndarray, features: list[str], n_splits: int = 5, seed: int = 0
) -> tuple[float, dict[str, Any]]:
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    per_feat: list[float] = []
    for j in range(X.shape[1]):
        scores: list[float] = []
        for train_idx, test_idx in cv.split(X, y):
            x_train = X[train_idx, j].reshape(-1, 1)
            x_test = X[test_idx, j].reshape(-1, 1)
            clf = LogisticRegression(max_iter=500, solver="liblinear")
            clf.fit(x_train, y[train_idx])
            p_test = clf.predict_proba(x_test)[:, 1]
            scores.append(roc_auc_score(y[test_idx], p_test))
        per_feat.append(float(np.mean(scores)))
    # Sign-invariant to mirror the gate's own convention.
    per_feat_arr = np.array(per_feat)
    per_feat_arr = np.maximum(per_feat_arr, 1.0 - per_feat_arr)
    best_idx = int(np.argmax(per_feat_arr))
    return float(per_feat_arr[best_idx]), {
        "best_feature": features[best_idx],
        "per_feature_auc": dict(zip(features, per_feat_arr.tolist())),
    }


def baseline_lr_pair_interaction(
    X: np.ndarray, y: np.ndarray, features: list[str], n_splits: int = 5, seed: int = 0
) -> tuple[float, dict[str, Any]]:
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    best_auc = -1.0
    best_pair: tuple[str, str] | None = None
    all_pairs: dict[str, float] = {}
    for i, j in combinations(range(X.shape[1]), 2):
        xi = X[:, i]
        xj = X[:, j]
        pair_X = np.column_stack([xi, xj, xi * xj])
        scores: list[float] = []
        for train_idx, test_idx in cv.split(pair_X, y):
            clf = LogisticRegression(max_iter=500, solver="liblinear")
            clf.fit(pair_X[train_idx], y[train_idx])
            p_test = clf.predict_proba(pair_X[test_idx])[:, 1]
            scores.append(roc_auc_score(y[test_idx], p_test))
        mean_auc = float(np.mean(scores))
        sign_inv = max(mean_auc, 1.0 - mean_auc)
        key = f"{features[i]}|{features[j]}"
        all_pairs[key] = sign_inv
        if sign_inv > best_auc:
            best_auc = sign_inv
            best_pair = (features[i], features[j])
    return float(best_auc), {"best_pair": best_pair, "per_pair_auc": all_pairs}


def compute_task_baselines(task: str) -> dict[str, Any]:
    features = TASK_FEATURES[task]
    csv_path = TASK_DATA[task]
    df = pd.read_csv(csv_path)
    missing = [f for f in features if f not in df.columns]
    if missing:
        raise ValueError(f"Missing features for task={task}: {missing}")
    X = df[features].to_numpy(dtype=float)
    y = _parse_labels(df["label"])

    sign_max, sign_meta = baseline_sign_invariant_max(X, y)
    lr1, lr1_meta = baseline_lr_single(X, y, features)
    lr2, lr2_meta = baseline_lr_pair_interaction(X, y, features)

    return {
        "task": task,
        "n_samples": int(len(y)),
        "n_features": int(X.shape[1]),
        "positive_rate": float(np.mean(y)),
        "baselines": {
            "sign_invariant_max": {"auc": sign_max, "meta": sign_meta},
            "lr_single": {"auc": lr1, "meta": lr1_meta},
            "lr_pair_interaction": {"auc": lr2, "meta": lr2_meta},
        },
    }


def passes_with_new_baseline(
    row: pd.Series,
    new_baseline_auc: float,
    thresholds: dict[str, float] = CURRENT_THRESHOLDS,
) -> tuple[bool, float]:
    """Re-evaluate gate using a new baseline_auc; returns (pass, delta)."""
    delta = float(row["law_auc"]) - float(new_baseline_auc)
    perm_ok = (not np.isnan(row["perm_p_fdr"])) and row["perm_p_fdr"] < thresholds["perm_p_fdr"]
    ci_ok = (not np.isnan(row["ci_lower"])) and row["ci_lower"] > thresholds["ci_lower"]
    delta_ok = delta > thresholds["delta_baseline"]
    conf_ok = (not np.isnan(row["delta_confound"])) and row["delta_confound"] > thresholds["delta_confound"]
    decoy_ok = (not np.isnan(row["decoy_p"])) and row["decoy_p"] < thresholds["decoy_p"]
    return bool(perm_ok and ci_ok and delta_ok and conf_ok and decoy_ok), delta


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out-dir", default="results/track_b_gate_robustness",
    )
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    candidates = load_candidates(DEFAULT_SOURCES)
    print(f"Loaded {len(candidates)} candidates across {candidates['task'].nunique()} tasks")
    print(candidates.groupby(["task", "source"]).size().to_string())

    task_summary: dict[str, Any] = {}
    for task in TASK_FEATURES:
        print(f"\n=== Computing baselines for task={task} ===")
        task_summary[task] = compute_task_baselines(task)
        for kind, spec in task_summary[task]["baselines"].items():
            print(f"  {kind}: AUC={spec['auc']:.4f}")

    records: list[dict[str, Any]] = []
    for _, cand in candidates.iterrows():
        task = cand["task"]
        law_auc = cand["law_auc"]
        for kind, spec in task_summary[task]["baselines"].items():
            new_b = spec["auc"]
            passes, delta = passes_with_new_baseline(cand, new_b)
            records.append(
                {
                    "candidate_id": cand["candidate_id"],
                    "source": cand["source"],
                    "task": task,
                    "equation": cand["equation"],
                    "law_auc": law_auc,
                    "baseline_kind": kind,
                    "baseline_auc": new_b,
                    "delta_baseline": delta,
                    "delta_baseline_current_report": cand["delta_baseline_current"],
                    "pass": passes,
                }
            )
    ablation_df = pd.DataFrame.from_records(records)
    csv_path = out_dir / "baseline_ablation.csv"
    ablation_df.to_csv(csv_path, index=False)
    print(f"\nWrote {csv_path} ({len(ablation_df)} rows)")

    per_kind = (
        ablation_df.groupby(["task", "baseline_kind"])
        .agg(survivors=("pass", "sum"), n_candidates=("pass", "size"), max_delta=("delta_baseline", "max"))
        .reset_index()
    )
    summary_path = out_dir / "baseline_ablation_summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "task_baselines": task_summary,
                "per_task_per_kind": per_kind.to_dict(orient="records"),
                "thresholds": CURRENT_THRESHOLDS,
            },
            indent=2,
            default=float,
        )
    )
    print(f"Wrote {summary_path}")
    print("\n=== Survivors per (task, baseline_kind) ===")
    print(per_kind.to_string(index=False))


if __name__ == "__main__":
    main()
