"""I2 Rashomon set analysis.

Enumerate every two-gene difference g_i − g_j on the 45-gene
metastasis_expanded panel and report how many reach AUROC within ε of
TOP2A − EPAS1's 0.726. Pre-registered in
preregistrations/20260425T185717Z_i2_rashomon_set.yaml.

Usage:
    cd lacuna-falsification
    source .venv/bin/activate
    python src/track_a_rashomon_set.py
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data/kirc_metastasis_expanded.csv"
RESULTS = REPO / "results/track_a_task_landscape/rashomon_set"
RESULTS.mkdir(parents=True, exist_ok=True)

ANCHOR_AUROC = 0.726  # TOP2A − EPAS1 survivor (rounded; raw is 0.7275)
TIGHT_EPSILON = 0.02
LOOSE_EPSILON = 0.05

PROLIFERATION_MARKERS = {"TOP2A", "MKI67", "CDK1", "CCNB1", "PCNA", "MCM2"}


def sign_invariant_auc(y, score):
    a = float(roc_auc_score(y, score))
    return max(a, 1.0 - a)


def main():
    df = pd.read_csv(DATA)
    non_gene = {"sample_id", "label", "age", "batch_index", "sex"}
    gene_cols = sorted(
        c for c in df.columns
        if c not in non_gene and pd.api.types.is_numeric_dtype(df[c])
    )
    print(f"Loaded {len(df)} samples, {len(gene_cols)} genes")
    y = (df["label"] == "disease").astype(int).to_numpy()
    print(f"Prevalence: {y.mean():.3f}  n={len(y)}")

    # z-score per gene
    X = df[gene_cols].to_numpy(dtype=float)
    X = (X - X.mean(0)) / (X.std(0) + 1e-9)

    rows = []
    n_pairs = 0
    for i, j in combinations(range(len(gene_cols)), 2):
        # Symmetric: (g_i − g_j) is sign-invariantly equivalent to (g_j − g_i)
        # under max(AUC, 1−AUC), so enumerate unordered pairs only.
        score = X[:, i] - X[:, j]
        auc = sign_invariant_auc(y, score)
        rows.append({
            "gene_a": gene_cols[i],
            "gene_b": gene_cols[j],
            "auroc": auc,
        })
        n_pairs += 1
    print(f"Evaluated {n_pairs} unordered pairs (C(45,2) = {len(gene_cols)*(len(gene_cols)-1)//2})")

    df_rs = pd.DataFrame(rows).sort_values("auroc", ascending=False).reset_index(drop=True)
    df_rs.to_csv(RESULTS / "all_pairs.csv", index=False)

    # Rashomon sets
    tight_mask = df_rs["auroc"] >= ANCHOR_AUROC - TIGHT_EPSILON
    loose_mask = df_rs["auroc"] >= ANCHOR_AUROC - LOOSE_EPSILON
    tight = df_rs[tight_mask].reset_index(drop=True)
    loose = df_rs[loose_mask].reset_index(drop=True)

    # TOP2A−EPAS1 rank
    pair_top2a_epas1 = df_rs[
        ((df_rs["gene_a"] == "TOP2A") & (df_rs["gene_b"] == "EPAS1"))
        | ((df_rs["gene_a"] == "EPAS1") & (df_rs["gene_b"] == "TOP2A"))
    ]
    top2a_epas1_rank = (
        int(pair_top2a_epas1.index[0]) + 1 if len(pair_top2a_epas1) else None
    )
    top2a_epas1_auc = (
        float(pair_top2a_epas1["auroc"].iloc[0]) if len(pair_top2a_epas1) else None
    )
    print(f"\nTOP2A−EPAS1 rank: {top2a_epas1_rank}/{n_pairs}, AUROC={top2a_epas1_auc:.4f}")

    print(f"\nTight Rashomon set (ε={TIGHT_EPSILON}, AUROC ≥ {ANCHOR_AUROC - TIGHT_EPSILON:.3f}):")
    print(f"  {len(tight)} pairs")
    print("  Top 10:")
    for r in tight.head(10).itertuples():
        print(f"    {r.gene_a:8s} − {r.gene_b:8s}  AUROC={r.auroc:.4f}")

    # P3 verdict — gene composition of the tight set
    contains_proliferation_or_epas1 = sum(
        1 for r in tight.itertuples()
        if "EPAS1" in (r.gene_a, r.gene_b)
        or r.gene_a in PROLIFERATION_MARKERS
        or r.gene_b in PROLIFERATION_MARKERS
    )
    p3_pct = contains_proliferation_or_epas1 / max(len(tight), 1) * 100

    # Pre-registered prediction verdicts
    p1 = top2a_epas1_rank is not None and top2a_epas1_rank <= 5
    p2 = len(tight) <= 20
    p3 = p3_pct >= 80.0  # treat "dominated by" as ≥ 80%

    summary = {
        "n_samples": int(len(y)),
        "n_genes": len(gene_cols),
        "n_pairs": n_pairs,
        "anchor_law": "TOP2A − EPAS1",
        "anchor_auroc_rounded": ANCHOR_AUROC,
        "anchor_auroc_actual": top2a_epas1_auc,
        "anchor_rank": top2a_epas1_rank,
        "tight_set": {
            "epsilon": TIGHT_EPSILON,
            "threshold_auroc": ANCHOR_AUROC - TIGHT_EPSILON,
            "n_pairs": int(len(tight)),
            "pairs": tight.to_dict(orient="records"),
            "contains_proliferation_or_epas1_pct": p3_pct,
        },
        "loose_set": {
            "epsilon": LOOSE_EPSILON,
            "threshold_auroc": ANCHOR_AUROC - LOOSE_EPSILON,
            "n_pairs": int(len(loose)),
            "pairs": loose.head(50).to_dict(orient="records"),
        },
        "predictions": {
            "p1_top2a_epas1_in_top_5": {
                "pass": bool(p1),
                "rank": top2a_epas1_rank,
                "threshold": 5,
            },
            "p2_tight_rashomon_le_20": {
                "pass": bool(p2),
                "n_pairs": int(len(tight)),
                "threshold": 20,
            },
            "p3_dominated_by_proliferation_or_epas1": {
                "pass": bool(p3),
                "pct": p3_pct,
                "threshold_pct": 80.0,
            },
        },
    }

    with open(RESULTS / "rashomon_tight.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nPre-registered prediction verdicts:")
    print(f"  P1 (TOP2A−EPAS1 in top 5):              {'PASS' if p1 else 'FAIL'}  (rank {top2a_epas1_rank})")
    print(f"  P2 (tight Rashomon ≤ 20):               {'PASS' if p2 else 'FAIL'}  ({len(tight)} pairs)")
    print(f"  P3 (≥80% prolif/EPAS1 in tight set):    {'PASS' if p3 else 'FAIL'}  ({p3_pct:.0f}%)")
    print(f"\nWrote: {RESULTS}/all_pairs.csv  +  rashomon_tight.json")


if __name__ == "__main__":
    main()
