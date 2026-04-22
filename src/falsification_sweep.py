#!/usr/bin/env python3
"""Batch falsification runner over PySR equation candidates."""

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
    label_shuffle_null,
    passes_falsification,
)


def make_equation_fn(equation_str, col_names):
    def fn(X):
        ns = {f"x{i}": X[:, i] for i in range(X.shape[1])}
        ns.update(
            {k: getattr(np, k) for k in ["log", "log1p", "exp", "abs", "sqrt", "sin", "cos"]}
        )
        return eval(equation_str, {"__builtins__": {}}, ns)  # noqa: S307
    return fn


def _fail_reason(r: dict) -> str:
    if r["passes"]:
        return ""
    if r["perm_p"] >= 0.05:
        return "perm_p"
    if r["ci_width"] >= 0.10:
        return "ci_width"
    if r["delta_baseline"] <= 0.05:
        return "delta_baseline"
    if r["delta_confound"] is not None and r["delta_confound"] <= 0.03:
        return "delta_confound"
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch falsification runner over PySR candidates")
    parser.add_argument("--candidates", required=True, help="Path to candidates JSON")
    parser.add_argument("--data", required=True, help="Path to data CSV")
    parser.add_argument("--covariate-cols", default="", help="Comma-separated covariate column names")
    parser.add_argument("--n-permutations", type=int, default=1000)
    parser.add_argument("--n-resamples", type=int, default=1000)
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    candidates = json.loads(Path(args.candidates).read_text())

    df = pd.read_csv(args.data)
    covariate_cols = [c.strip() for c in args.covariate_cols.split(",") if c.strip()]
    label_col = "label"
    exclude_cols = {label_col} | set(covariate_cols)
    gene_cols = [
        c for c in df.select_dtypes(include=[np.number]).columns if c not in exclude_cols
    ]

    X_bio = df[gene_cols].values.astype(float)
    y = df[label_col].values.astype(int)
    X_cov = df[covariate_cols].values.astype(float) if covariate_cols else None

    raw_results: list[dict] = []
    for cand in candidates:
        fn = make_equation_fn(cand["equation"], gene_cols)

        perm_p, _ = label_shuffle_null(X_bio, y, fn, args.n_permutations)
        ci_width, _ = bootstrap_stability(X_bio, y, fn, args.n_resamples)
        delta_baseline, law_auc, baseline_auc = baseline_comparison(X_bio, y, fn)

        delta_confound = confound_auc = None
        if X_cov is not None:
            delta_confound, law_auc, confound_auc = confound_only(X_bio, X_cov, y, fn)

        passes = passes_falsification(perm_p, ci_width, law_auc, baseline_auc, confound_auc)

        raw_results.append(
            {
                **cand,
                "passes": passes,
                "perm_p": perm_p,
                "ci_width": ci_width,
                "delta_baseline": delta_baseline,
                "delta_confound": delta_confound,
            }
        )

    perm_ps = [r["perm_p"] for r in raw_results]
    _, p_adj, _, _ = multipletests(perm_ps, alpha=0.1, method="fdr_bh")

    results: list[dict] = []
    for r, p_fdr in zip(raw_results, p_adj):
        r["perm_p_fdr"] = float(p_fdr)
        r["fail_reason"] = _fail_reason(r)
        results.append(r)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2))

    n_pass = sum(r["passes"] for r in results)
    print(f"{len(results)} candidates → {n_pass} survived falsification")


if __name__ == "__main__":
    main()
