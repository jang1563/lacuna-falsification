from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

try:
    import pysr
    PYSR_AVAILABLE = hasattr(pysr, "PySRRegressor")
except (ImportError, Exception):
    pysr = None  # type: ignore[assignment]
    PYSR_AVAILABLE = False


_DISEASE_TOKENS = {"disease", "tumor", "case", "cancer", "1", "true"}


def _parse_labels(series: pd.Series) -> np.ndarray:
    """Unified label parser shared with falsification_sweep."""
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(int).values
    s = series.astype(str).str.strip().str.lower()
    return s.map(lambda v: 1 if v in _DISEASE_TOKENS else 0).values.astype(int)


def _zscore_within_cohort(X: np.ndarray) -> np.ndarray:
    mean = X.mean(axis=0, keepdims=True)
    std = X.std(axis=0, keepdims=True)
    std = np.where(std < 1e-8, 1.0, std)
    return (X - mean) / std


def _load_data(
    csv_path: str,
    genes: list[str],
    standardize: bool,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    df = pd.read_csv(csv_path)
    y = _parse_labels(df["label"])
    gene_cols = [g for g in genes if g in df.columns]
    if not gene_cols:
        raise ValueError(
            f"None of the requested genes found in {csv_path}. "
            f"Requested: {genes[:10]}... Available: {list(df.columns)[:20]}..."
        )
    X = df[gene_cols].values.astype(float)
    if standardize:
        X = _zscore_within_cohort(X)
    return X, y, gene_cols


def _extract_guesses(proposals: list[dict], genes: list[str]) -> list[str]:
    gene_set = set(genes)
    guesses: list[str] = []
    for p in proposals:
        ig = p.get("initial_guess", "")
        if not ig:
            continue
        tf = p.get("target_features", [])
        if tf and not gene_set.issuperset(tf):
            continue
        guesses.append(ig)
    return guesses


def _norm_eq(s: str) -> str:
    return s.replace(" ", "")


def _match_law_family(equation: str, proposals: list[dict]) -> str:
    eq_norm = _norm_eq(equation)
    for p in proposals:
        ig = _norm_eq(p.get("initial_guess", ""))
        if ig and ig == eq_norm:
            return p.get("template_id", "")
    return ""


def _novelty_score(equation: str, proposals: list[dict]) -> float:
    """0 = equation matches an initial_guess verbatim, 1 = fully novel tokens.

    Crude symbolic-diff proxy for distinguishing "PySR returned the guess" from
    "PySR found something new".
    """
    eq_tokens = {
        t for t in equation.replace("(", " ").replace(")", " ").split() if t
    }
    if not eq_tokens:
        return 0.0
    all_guess_tokens: set[str] = set()
    eq_norm = _norm_eq(equation)
    for p in proposals:
        ig = p.get("initial_guess", "")
        if not ig:
            continue
        if _norm_eq(ig) == eq_norm:
            return 0.0
        all_guess_tokens.update(
            t for t in ig.replace("(", " ").replace(")", " ").split() if t
        )
    if not all_guess_tokens:
        return 1.0
    novel = eq_tokens - all_guess_tokens
    return round(len(novel) / len(eq_tokens), 3)


def _run_sweep(args: argparse.Namespace) -> list[dict[str, Any]]:
    genes = [g.strip() for g in args.genes.split(",") if g.strip()]
    X, y, gene_cols = _load_data(args.data, genes, standardize=args.standardize)

    proposals: list[dict] = []
    guesses: list[str] = []
    if args.proposals:
        with open(args.proposals) as f:
            proposals = json.load(f)
        guesses = _extract_guesses(proposals, gene_cols)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=args.split_seed, stratify=y
    )

    all_candidates: dict[str, dict[str, Any]] = {}

    for seed in args.seeds:
        kwargs: dict[str, Any] = dict(
            niterations=args.iterations,
            populations=args.n_populations,
            population_size=args.population_size,
            maxsize=args.maxsize,
            procs=args.n_jobs,
            random_state=seed,
            variable_names=gene_cols,
            binary_operators=["+", "-", "*", "/"],
            unary_operators=["log1p", "exp", "sqrt"],
        )
        if guesses:
            kwargs["guesses"] = guesses
            kwargs["fraction_replaced_guesses"] = 0.3

        model = pysr.PySRRegressor(**kwargs)
        model.fit(X_train, y_train)

        eqs: pd.DataFrame = model.equations_
        top = eqs.nlargest(min(10, len(eqs)), "score")

        for i, row in top.iterrows():
            eq_str = str(row["equation"])
            try:
                train_pred = model.predict(X_train, index=i)
                test_pred = model.predict(X_test, index=i)
                train_auroc = float(roc_auc_score(y_train, train_pred))
                test_auroc = float(roc_auc_score(y_test, test_pred))
            except Exception:
                train_auroc = 0.5
                test_auroc = 0.5

            existing = all_candidates.get(eq_str)
            if existing is None or test_auroc > existing["test_auroc"]:
                all_candidates[eq_str] = {
                    "equation": eq_str,
                    "auroc": test_auroc,
                    "train_auroc": train_auroc,
                    "test_auroc": test_auroc,
                    "complexity": int(row["complexity"]),
                    "seed": seed,
                    "law_family": _match_law_family(eq_str, proposals),
                    "novelty": _novelty_score(eq_str, proposals),
                }

    return list(all_candidates.values())


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="PySR symbolic regression sweep")
    parser.add_argument("--data", required=True, help="CSV path")
    parser.add_argument("--genes", required=True, help="Comma-separated gene names")
    parser.add_argument("--proposals", default=None, help="law_proposals.json path")
    parser.add_argument("--n-populations", type=int, default=8)
    parser.add_argument("--population-size", type=int, default=50)
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--maxsize", type=int, default=15)
    parser.add_argument("--seeds", type=int, nargs="+", default=[1])
    parser.add_argument("--n-jobs", type=int, default=4)
    parser.add_argument(
        "--test-size", type=float, default=0.3,
        help="Fraction held out; train vs test AUROC surfaces overfit.",
    )
    parser.add_argument("--split-seed", type=int, default=7)
    parser.add_argument(
        "--standardize", action="store_true",
        help="Z-score each feature within the cohort before PySR fit.",
    )
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args(argv)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    if not PYSR_AVAILABLE:
        print("WARNING: pysr not installed. Writing empty candidates list.")
        Path(args.output).write_text("[]")
        sys.exit(0)

    candidates = _run_sweep(args)
    Path(args.output).write_text(json.dumps(candidates, indent=2))


if __name__ == "__main__":
    main()
