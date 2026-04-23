#!/usr/bin/env python3
"""G5: PySR comparison — fraction_replaced_guesses=0 vs 0.3.

Research question: Does PySR rediscover TOP2A − EPAS1 WITHOUT Opus-seeded
guesses (fraction=0)? If yes, the survivor is not an artifact of seeding.
If no, it shows Opus guidance provides genuine search-space advantage.

Strategy:
  1. Load the existing "seeded" run results (fraction=0.3, 9 survivors).
  2. Run a new PySR search with the same settings but NO guesses (fraction=0).
  3. Run the same 5-test falsification gate on the new candidates.
  4. Compare: survivor overlap, AUROC distribution, gene usage.

Uses reduced niterations=500 (vs 1000 in flagship) for speed.

Lane G, commit prefix [G].
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parent))
from theory_copilot.falsification import run_falsification_suite

try:
    import pysr
    PYSR_AVAILABLE = hasattr(pysr, "PySRRegressor")
except (ImportError, Exception):
    pysr = None  # type: ignore[assignment]
    PYSR_AVAILABLE = False


GENE_COLS_EXPANDED = [
    "HIF1A", "EPAS1", "BHLHE40", "DDIT4", "PGK1",
    "CA9", "CA12", "VEGFA", "LDHA", "SLC2A1",
    "AGXT", "ALB", "CUBN", "LRP2", "CALB1", "PTGER3",
    "TOP2A", "MKI67", "CDK1", "CCNB1", "PCNA", "MCM2",
    "VIM", "FN1", "CXCR4", "COL4A2", "SNAI1", "ANGPTL4",
    "ALDOA", "CA12", "ACTB", "RPL13A", "GAPDH",
]
# Deduplicate
GENE_COLS_EXPANDED = list(dict.fromkeys(GENE_COLS_EXPANDED))


def _parse_labels(series: pd.Series) -> np.ndarray:
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(int).values
    s = series.astype(str).str.strip().str.lower()
    return s.map(lambda v: 1 if v in {"disease", "tumor", "case", "1", "true"} else 0).values.astype(int)


def _zscore(X: np.ndarray) -> np.ndarray:
    mu = X.mean(0); sigma = X.std(0)
    return (X - mu) / np.where(sigma < 1e-8, 1.0, sigma)


def run_pysr_fraction_zero(repo_root: Path) -> dict:
    out_dir = repo_root / "results" / "track_a_task_landscape" / "g5_fraction_zero"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    df = pd.read_csv(repo_root / "data" / "kirc_metastasis_expanded.csv")
    gene_cols = [g for g in GENE_COLS_EXPANDED if g in df.columns]
    y = _parse_labels(df["label"])
    X = df[gene_cols].values.astype(float)
    X = _zscore(X)

    print(f"Dataset: n={len(y)}, disease={y.sum()}, genes={len(gene_cols)}")
    print(f"PySR available: {PYSR_AVAILABLE}")

    # --- Load existing seeded results (fraction=0.3) for comparison ----------
    seeded_path = (
        repo_root / "results" / "track_a_task_landscape"
        / "metastasis_expanded" / "falsification_report.json"
    )
    seeded_results = json.loads(seeded_path.read_text()) if seeded_path.exists() else []
    seeded_survivors = [r for r in seeded_results if r.get("passes")]
    seeded_genes = set()
    for s in seeded_survivors:
        seeded_genes.update(s.get("genes_used", []))
    print(f"\nSeeded run (fraction=0.3): {len(seeded_survivors)}/{len(seeded_results)} survivors")
    print(f"Seeded survivor genes: {sorted(seeded_genes)}")

    if not PYSR_AVAILABLE:
        print("\nPySR not available — generating stub result for comparison table.")
        candidates = []
        result = {
            "status": "stub_pysr_unavailable",
            "seeded_run": {
                "total_candidates": len(seeded_results),
                "survivors": len(seeded_survivors),
                "survivor_genes": sorted(seeded_genes),
            },
            "fraction_zero_run": {
                "status": "skipped — PySR unavailable",
                "note": "Re-run this script in the .venv with Julia configured",
            },
        }
        (out_dir / "fraction_zero_comparison.json").write_text(json.dumps(result, indent=2))
        return result

    # --- Run PySR without guesses (fraction=0) --------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, stratify=y, random_state=42
    )

    model = pysr.PySRRegressor(
        niterations=500,           # shorter than flagship for speed
        populations=8,
        population_size=50,
        maxsize=15,
        binary_operators=["+", "-", "*", "/"],
        unary_operators=["log1p", "exp", "sqrt"],
        variable_names=gene_cols,
        # NO guesses, NO fraction_replaced_guesses
        verbosity=0,
        random_state=999,         # different seed from seeded run
        progress=False,
    )

    print("\nRunning PySR without seeded guesses (fraction=0)...")
    model.fit(X_train, y_train)

    pareto_df = model.get_hof()
    candidates = []
    for _, row in pareto_df.iterrows():
        eq = str(row.get("sympy_format", row.get("equation", "")))
        try:
            fn = model.get_best()
            scores = model.predict(X_test, index=row.name if hasattr(row, "name") else None)
        except Exception:
            continue
        if scores is None:
            continue
        scores = np.asarray(scores).reshape(-1)
        if np.any(~np.isfinite(scores)):
            continue

        # Quick AUROC check
        from sklearn.metrics import roc_auc_score
        try:
            auroc = float(roc_auc_score(y_test, scores))
        except Exception:
            continue

        # Genes used
        genes_in_eq = [g for g in gene_cols if g in eq]

        candidates.append({
            "equation": eq,
            "auroc": max(auroc, 1 - auroc),
            "genes_used": genes_in_eq,
            "complexity": int(row.get("complexity", 0)),
        })

    print(f"PySR fraction=0 produced {len(candidates)} candidates")

    # Run falsification gate on top candidates by AUROC
    candidates_sorted = sorted(candidates, key=lambda c: c["auroc"], reverse=True)[:30]
    gate_results = []
    for cand in candidates_sorted:
        eq_str = cand["equation"]
        try:
            _local_gene_cols = gene_cols
            _df_full = df
            _gene_list = gene_cols

            def make_fn(eq_s, gc):
                def _fn(X_arr):
                    local = {g: X_arr[:, i] for i, g in enumerate(gc)}
                    local.update({"np": np, "log1p": np.log1p, "exp": np.exp, "sqrt": np.sqrt})
                    return eval(eq_s, {"__builtins__": {}}, local)
                return _fn

            fn = make_fn(eq_str, gene_cols)
            gate = run_falsification_suite(fn, X, y, n_decoys=50)
            cand.update({
                "passes": bool(gate["passes"]),
                "perm_p": gate["perm_p"],
                "ci_lower": gate["ci_lower"],
                "delta_baseline": gate["delta_baseline"],
            })
        except Exception as exc:
            cand["passes"] = False
            cand["gate_error"] = str(exc)
        gate_results.append(cand)

    fraction_zero_survivors = [c for c in gate_results if c.get("passes")]
    fraction_zero_genes = set()
    for s in fraction_zero_survivors:
        fraction_zero_genes.update(s.get("genes_used", []))

    # Overlap analysis
    seeded_top_genes = {"TOP2A", "EPAS1"}
    overlap_found = bool(seeded_top_genes & fraction_zero_genes)

    result = {
        "seeded_run_fraction_0_3": {
            "total_candidates": len(seeded_results),
            "survivors": len(seeded_survivors),
            "survivor_genes": sorted(seeded_genes),
        },
        "fraction_zero_run": {
            "total_candidates": len(gate_results),
            "survivors": len(fraction_zero_survivors),
            "survivor_genes": sorted(fraction_zero_genes),
            "survivors_detail": fraction_zero_survivors[:5],
        },
        "comparison": {
            "top2a_epas1_rediscovered": overlap_found,
            "survivor_count_seeded": len(seeded_survivors),
            "survivor_count_unseeded": len(fraction_zero_survivors),
            "interpretation": (
                f"PySR {'rediscovers' if 'EPAS1' in fraction_zero_genes and 'TOP2A' in fraction_zero_genes else 'does NOT rediscover'} "
                f"TOP2A/EPAS1 without Opus seeding. "
                f"Seeded: {len(seeded_survivors)} survivors, Unseeded: {len(fraction_zero_survivors)} survivors."
            ),
        },
    }

    (out_dir / "fraction_zero_comparison.json").write_text(json.dumps(result, indent=2))
    return result


def main():
    repo_root = Path(__file__).resolve().parent.parent

    print("="*65)
    print("[G5] PySR fraction=0 vs fraction=0.3 comparison")
    print("="*65)

    result = run_pysr_fraction_zero(repo_root)

    out_dir = repo_root / "results" / "track_a_task_landscape" / "g5_fraction_zero"

    if "comparison" in result:
        c = result["comparison"]
        print(f"\nSeeded   (fraction=0.3): {c['survivor_count_seeded']} survivors")
        print(f"Unseeded (fraction=0.0): {c['survivor_count_unseeded']} survivors")
        print(f"TOP2A/EPAS1 rediscovered: {c['top2a_epas1_rediscovered']}")
        print(f"\n{c['interpretation']}")
    else:
        s0 = result.get("seeded_run", result.get("seeded_run_fraction_0_3", {}))
        f0 = result.get("fraction_zero_run", {})
        print(f"\nSeeded run: {s0.get('survivors')}/{s0.get('total_candidates')} survivors")
        print(f"Fraction-0 run: {f0.get('status', 'N/A')}")

    print(f"\nResults written to: {out_dir}/fraction_zero_comparison.json")


if __name__ == "__main__":
    main()
