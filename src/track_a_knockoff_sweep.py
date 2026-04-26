"""G1 knockoff v2 sweep: run KnockoffFilter on kirc_metastasis_expanded.

Compares v1 decoy gate survivors against v2 knockoff-selected genes.
Pre-registered in preregistrations/20260425T170647Z_g1_knockoff_v2.yaml.

Usage:
    cd lacuna_discovery
    source .venv/bin/activate
    python src/track_a_knockoff_sweep.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data/kirc_metastasis_expanded.csv"
RESULTS_DIR = REPO / "results/track_a_task_landscape/knockoff_v2"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# v1 survivors from metastasis_expanded (9/30, pre-registered 5-test gate)
# Gene constituents extracted from results/track_a_task_landscape/metastasis_expanded/
V1_SURVIVOR_LAWS = [
    {"equation": "TOP2A - EPAS1",        "genes": ["TOP2A", "EPAS1"],  "auroc": 0.726},
    {"equation": "MKI67 - EPAS1",        "genes": ["MKI67", "EPAS1"],  "auroc": 0.708},
    {"equation": "0.099*(TOP2A-EPAS1)+0.161", "genes": ["TOP2A", "EPAS1"], "auroc": 0.726},
]

# v1 clean rejects (decoy_p >= 0.05 in falsification report)
V1_REJECT_LAWS = [
    {"equation": "log1p(CA9)+log1p(VEGFA)-log1p(AGXT)", "genes": ["CA9", "VEGFA", "AGXT"], "auroc": 0.521},
    {"equation": "log1p(ACTB)-log1p(GAPDH)", "genes": ["ACTB", "GAPDH"], "auroc": 0.505},
]


def main():
    from lacuna.knockoff_gate import run_knockoff_gate, check_compound_law

    df = pd.read_csv(DATA)
    print(f"Loaded {len(df)} samples, {df.shape[1]} columns")
    label_dist = df["label"].value_counts().to_dict()
    print(f"Label distribution: {label_dist}")

    # Identify gene columns (all numeric non-label/sample_id cols)
    non_gene_cols = {"sample_id", "label", "age", "batch_index", "sex"}
    gene_cols = [c for c in df.columns if c not in non_gene_cols and
                 pd.api.types.is_numeric_dtype(df[c])]
    print(f"Gene columns: {len(gene_cols)}")

    X_full = df[gene_cols].to_numpy(dtype=float)
    X = (X_full - X_full.mean(axis=0)) / (X_full.std(axis=0) + 1e-9)
    y = (df["label"] == "disease").astype(int).to_numpy()
    print(f"M1 prevalence: {y.mean():.3f}  n={len(y)}")

    print("\nRunning 25-replicate knockoff sweep (q=0.10)...")
    knockoff_result = run_knockoff_gate(
        X, y,
        gene_names=gene_cols,
        fdr_target=0.10,
        n_replicates=25,
        seed=0,
        verbose=True,
    )

    selected = knockoff_result["selected_genes"]
    rates = knockoff_result["selection_rates"]
    mean_W = knockoff_result["mean_W_statistic"]
    print(f"\n=== Knockoff selected genes (rate >= 50%) ===")
    top_genes = sorted(rates.items(), key=lambda kv: kv[1], reverse=True)
    for gene, rate in top_genes:
        if rate > 0:
            print(f"  {gene}: {rate:.2f}")

    print(f"\nTotal selected: {len(selected)}")
    print(f"Sigma condition number: {knockoff_result['sigma_condition_number']:.1f}")

    # W-statistic ranking — verifies the filter ranks signal genes correctly
    # even when none cross the q=0.10 threshold.
    print(f"\n=== Top 10 genes by mean W statistic (across {knockoff_result['n_replicates']} replicates) ===")
    for entry in knockoff_result["top_genes_by_W"][:10]:
        print(f"  {entry['gene']:8s}  mean_W={entry['mean_W']:+.4f}")
    top2a_w = mean_W.get("TOP2A", float("nan"))
    epas1_w = mean_W.get("EPAS1", float("nan"))
    top2a_rank = next(
        (i + 1 for i, e in enumerate(knockoff_result["top_genes_by_W"])
         if e["gene"] == "TOP2A"), None,
    )
    epas1_rank = next(
        (i + 1 for i, e in enumerate(knockoff_result["top_genes_by_W"])
         if e["gene"] == "EPAS1"), None,
    )
    print(f"\n  TOP2A mean_W = {top2a_w:+.4f}  rank = {top2a_rank}/{len(mean_W)}")
    print(f"  EPAS1 mean_W = {epas1_w:+.4f}  rank = {epas1_rank}/{len(mean_W)}")

    # Check v1 survivors
    print("\n=== V1 survivor concordance (conjunction rule) ===")
    survivor_checks = []
    for law in V1_SURVIVOR_LAWS:
        check = check_compound_law(law["genes"], knockoff_result)
        status = "CONCORDANT" if check["law_genes_selected"] else "DISCORDANT"
        print(f"  {law['equation'][:40]:40s}  {status}  (bottleneck={check['bottleneck_gene']} rate={check['min_rate']:.2f})")
        survivor_checks.append({**law, **check, "v1_verdict": "pass", "concordance": status})

    # Check v1 rejects
    print("\n=== V1 reject concordance ===")
    reject_checks = []
    for law in V1_REJECT_LAWS:
        check = check_compound_law(law["genes"], knockoff_result)
        status = "CONCORDANT_NEG" if not check["law_genes_selected"] else "DISCORDANT_NEG"
        print(f"  {law['equation'][:40]:40s}  {status}  (bottleneck={check['bottleneck_gene']} rate={check['min_rate']:.2f})")
        reject_checks.append({**law, **check, "v1_verdict": "fail", "concordance": status})

    # Pre-registered hypotheses
    h1_top2a = rates.get("TOP2A", 0.0)
    h1_epas1 = rates.get("EPAS1", 0.0)
    h1_pass = h1_top2a >= 0.50 and h1_epas1 >= 0.50
    print(f"\n=== Pre-registered hypothesis checks ===")
    print(f"H1 (TOP2A+EPAS1 selected): TOP2A={h1_top2a:.2f} EPAS1={h1_epas1:.2f} -> {'PASS' if h1_pass else 'FAIL'}")

    concordant_survivors = sum(1 for c in survivor_checks if c.get("concordance") == "CONCORDANT")
    h2_pass = concordant_survivors >= min(2, len(V1_SURVIVOR_LAWS))
    print(f"H2 (survivor overlap >= threshold): {concordant_survivors}/{len(V1_SURVIVOR_LAWS)} concordant -> {'PASS' if h2_pass else 'FAIL'}")

    concordant_negs = sum(1 for c in reject_checks if c.get("concordance") == "CONCORDANT_NEG")
    h3_pass = concordant_negs / max(len(V1_REJECT_LAWS), 1) >= 0.80
    print(f"H3 (reject concordance >= 80%): {concordant_negs}/{len(V1_REJECT_LAWS)} -> {'PASS' if h3_pass else 'FAIL'}")

    # Build output
    out = {
        "dataset": "kirc_metastasis_expanded",
        "n_samples": int(len(y)),
        "n_genes": int(len(gene_cols)),
        "m1_prevalence": float(y.mean()),
        "fdr_target": knockoff_result["fdr_target"],
        "n_replicates": knockoff_result["n_replicates"],
        "seed": knockoff_result["seed"],
        "sigma_condition_number": knockoff_result["sigma_condition_number"],
        "selected_genes": knockoff_result["selected_genes"],
        "top_selection_rates": {g: r for g, r in top_genes if r >= 0.20},
        "mean_W_statistic": knockoff_result["mean_W_statistic"],
        "top_genes_by_W": knockoff_result["top_genes_by_W"],
        "top2a_W_rank": top2a_rank,
        "epas1_W_rank": epas1_rank,
        "hypotheses": {
            "H1_top2a_epas1_selected": {
                "pass": h1_pass,
                "top2a_rate": h1_top2a,
                "epas1_rate": h1_epas1,
            },
            "H2_survivor_concordance": {
                "pass": h2_pass,
                "concordant_n": concordant_survivors,
                "total_survivors": len(V1_SURVIVOR_LAWS),
            },
            "H3_reject_concordance": {
                "pass": h3_pass,
                "concordant_n": concordant_negs,
                "total_rejects": len(V1_REJECT_LAWS),
            },
        },
        "survivor_law_checks": survivor_checks,
        "reject_law_checks": reject_checks,
    }

    out_path = RESULTS_DIR / "kirc_metastasis_expanded_knockoff.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote: {out_path}")


if __name__ == "__main__":
    main()
