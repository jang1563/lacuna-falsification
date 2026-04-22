#!/usr/bin/env python3
"""Batch falsification runner over PySR equation candidates.

Equations are expected in gene-name form (e.g., "log1p(CA9) + log1p(VEGFA) - log1p(AGXT)")
as produced by pysr_sweep.py with variable_names=gene_cols.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).parent))

from theory_copilot.falsification import (
    baseline_comparison,
    bootstrap_stability,
    confound_only,
    decoy_feature_test,
    label_shuffle_null,
    passes_falsification,
)


_DISEASE_TOKENS = {"disease", "tumor", "case", "cancer", "1", "true"}
_NUMPY_FUNCS = ["log", "log1p", "exp", "abs", "sqrt", "sin", "cos"]


def _parse_labels(series: pd.Series) -> np.ndarray:
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(int).values
    s = series.astype(str).str.strip().str.lower()
    return s.map(lambda v: 1 if v in _DISEASE_TOKENS else 0).values.astype(int)


def _zscore_within_cohort(X: np.ndarray) -> np.ndarray:
    mean = X.mean(axis=0, keepdims=True)
    std = X.std(axis=0, keepdims=True)
    std = np.where(std < 1e-8, 1.0, std)
    return (X - mean) / std


def make_equation_fn(equation_str: str, col_names: list[str]):
    """Build an evaluator for a gene-name equation against a feature matrix.

    The matrix X is indexed positionally, but the equation references
    columns by their biological name — so the callable binds names -> columns
    and ignores column order.
    """
    safe_globals = {"__builtins__": {}}
    np_ns = {k: getattr(np, k) for k in _NUMPY_FUNCS}

    def fn(X: np.ndarray) -> np.ndarray:
        ns = {col_names[i]: X[:, i] for i in range(len(col_names))}
        # Also bind xi aliases so legacy equations still work.
        ns.update({f"x{i}": X[:, i] for i in range(len(col_names))})
        ns.update(np_ns)
        return eval(equation_str, safe_globals, ns)  # noqa: S307

    return fn


def _fail_reason(r: dict) -> str:
    if r["passes"]:
        return ""
    reasons: list[str] = []
    if r.get("perm_p_fdr", r["perm_p"]) >= 0.05:
        reasons.append("perm_p")
    if r["ci_lower"] <= 0.6:
        reasons.append("ci_lower")
    if r["delta_baseline"] <= 0.05:
        reasons.append("delta_baseline")
    if r.get("delta_confound") is not None and r["delta_confound"] <= 0.03:
        reasons.append("delta_confound")
    if r.get("decoy_p") is not None and r["decoy_p"] >= 0.05:
        reasons.append("decoy_p")
    return ",".join(reasons) if reasons else "threshold_edge"


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch falsification runner over PySR candidates")
    parser.add_argument("--candidates", required=True, help="Path to candidates JSON")
    parser.add_argument("--data", required=True, help="Path to data CSV")
    parser.add_argument("--genes", default=None,
                        help="Comma-separated gene column order (must match pysr_sweep --genes).")
    parser.add_argument("--covariate-cols", default="", help="Comma-separated covariate column names")
    parser.add_argument("--n-permutations", type=int, default=1000)
    parser.add_argument("--n-resamples", type=int, default=1000)
    parser.add_argument("--n-decoys", type=int, default=100)
    parser.add_argument("--skip-decoy", action="store_true",
                        help="Skip the decoy-feature null test (faster but weaker).")
    parser.add_argument("--standardize", action="store_true",
                        help="Z-score features within this cohort before evaluation (use with cross-cohort replay).")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    candidates = json.loads(Path(args.candidates).read_text())

    df = pd.read_csv(args.data)
    covariate_cols = [c.strip() for c in args.covariate_cols.split(",") if c.strip()]
    label_col = "label"
    exclude_cols = {label_col, "sample_id"} | set(covariate_cols)

    if args.genes:
        gene_cols = [g.strip() for g in args.genes.split(",") if g.strip() and g.strip() in df.columns]
    else:
        gene_cols = [
            c for c in df.select_dtypes(include=[np.number]).columns
            if c not in exclude_cols
        ]

    if not gene_cols:
        raise ValueError(f"No gene columns resolved from data file {args.data}")

    X_bio = df[gene_cols].values.astype(float)
    if args.standardize:
        X_bio = _zscore_within_cohort(X_bio)
    y = _parse_labels(df[label_col])
    X_cov = df[covariate_cols].values.astype(float) if covariate_cols else None

    raw_results: list[dict] = []
    for cand in candidates:
        fn = make_equation_fn(cand["equation"], gene_cols)

        perm_p, _ = label_shuffle_null(X_bio, y, fn, args.n_permutations)
        ci_width, ci_lower, _ = bootstrap_stability(X_bio, y, fn, args.n_resamples)
        delta_baseline, law_auc, baseline_auc = baseline_comparison(X_bio, y, fn)

        delta_confound = confound_auc = None
        if X_cov is not None:
            delta_confound, law_auc, confound_auc = confound_only(X_bio, X_cov, y, fn)

        decoy_p = decoy_q95 = None
        if not args.skip_decoy:
            decoy_p, decoy_q95, law_auc = decoy_feature_test(
                X_bio, y, fn, n_decoys=args.n_decoys
            )

        raw_results.append(
            {
                **cand,
                "perm_p": perm_p,
                "ci_width": ci_width,
                "ci_lower": ci_lower,
                "law_auc": law_auc,
                "baseline_auc": baseline_auc,
                "delta_baseline": delta_baseline,
                "delta_confound": delta_confound,
                "confound_auc": confound_auc,
                "decoy_p": decoy_p,
                "decoy_q95": decoy_q95,
            }
        )

    # FDR across candidates (Benjamini–Hochberg). Gate on FDR-adjusted p.
    perm_ps = [r["perm_p"] for r in raw_results] or [1.0]
    if len(raw_results) > 1:
        _, p_adj, _, _ = multipletests(perm_ps, alpha=0.1, method="fdr_bh")
    else:
        p_adj = np.asarray(perm_ps)

    results: list[dict] = []
    for r, p_fdr in zip(raw_results, p_adj):
        r["perm_p_fdr"] = float(p_fdr)
        r["passes"] = passes_falsification(
            perm_p=float(p_fdr),
            ci_lower=r["ci_lower"],
            law_auc=r["law_auc"],
            baseline_auc=r["baseline_auc"],
            confound_delta=r["delta_confound"],
            decoy_p=r["decoy_p"],
        )
        r["fail_reason"] = _fail_reason(r)
        results.append(r)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2))

    n_pass = sum(r["passes"] for r in results)
    print(f"{len(results)} candidates → {n_pass} survived falsification")


if __name__ == "__main__":
    main()
