from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

try:
    import pysr
    PYSR_AVAILABLE = True
except ImportError:
    pysr = None  # type: ignore[assignment]
    PYSR_AVAILABLE = False


def _load_data(csv_path: str, genes: list[str]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    df = pd.read_csv(csv_path)
    raw = df["label"].astype(str).str.lower()
    y = raw.map(lambda v: 1 if v in ("disease", "tumor") else 0).values.astype(float)
    gene_cols = [g for g in genes if g in df.columns]
    X = df[gene_cols].values.astype(float)
    return X, y, gene_cols


def _extract_guesses(proposals: list[dict], genes: list[str]) -> list[str]:
    gene_set = set(genes)
    guesses: list[str] = []
    for p in proposals:
        ig = p.get("initial_guess", "")
        if not ig:
            continue
        tf = p.get("target_features", [])
        if tf and gene_set.isdisjoint(tf):
            continue
        guesses.append(ig)
    return guesses


def _match_law_family(equation: str, proposals: list[dict]) -> str:
    for p in proposals:
        if p.get("initial_guess", "") == equation:
            return p.get("template_id", "")
    return ""


def _run_sweep(args: argparse.Namespace) -> list[dict[str, Any]]:
    genes = [g.strip() for g in args.genes.split(",")]
    X, y, _gene_cols = _load_data(args.data, genes)

    proposals: list[dict] = []
    guesses: list[str] = []
    if args.proposals:
        with open(args.proposals) as f:
            proposals = json.load(f)
        guesses = _extract_guesses(proposals, genes)

    all_candidates: dict[str, dict[str, Any]] = {}

    for seed in args.seeds:
        kwargs: dict[str, Any] = dict(
            niterations=args.iterations,
            populations=args.n_populations,
            population_size=args.population_size,
            maxsize=args.maxsize,
            procs=args.n_jobs,
            random_state=seed,
        )
        if guesses:
            kwargs["guesses"] = guesses
            kwargs["fraction_replaced_guesses"] = 0.3

        model = pysr.PySRRegressor(**kwargs)
        model.fit(X, y)

        eqs: pd.DataFrame = model.equations_
        top = eqs.nlargest(min(10, len(eqs)), "score")

        for i, row in top.iterrows():
            eq_str = str(row["equation"])
            try:
                pred = model.predict(X, index=i)
                auroc = float(roc_auc_score(y, pred))
            except Exception:
                auroc = 0.5

            if eq_str not in all_candidates or auroc > all_candidates[eq_str]["auroc"]:
                all_candidates[eq_str] = {
                    "equation": eq_str,
                    "auroc": auroc,
                    "complexity": int(row["complexity"]),
                    "seed": seed,
                    "law_family": _match_law_family(eq_str, proposals),
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
