#!/usr/bin/env python3
"""Lane I · I2 — Rashomon set analysis for 2-gene linear-difference laws.

Question: how unique is TOP2A − EPAS1? Of C(45, 2) = 990 possible 2-gene
linear-difference pairs in the 45-gene panel on TCGA-KIRC metastasis,
how many achieve sign-invariant AUROC within ε of the headline 0.726?

This is the Rashomon set at ε-tolerance — a direct empirical measure of
"model multiplicity" for the 2-gene compact-law family, which the NeurIPS
2024 proceedings (Semenova & Rudin; arXiv:2402.00728) argues is more
actionable than theoretical capacity bounds at n=505.

Output: results/science_depth/rashomon_top50.csv,
        results/science_depth/rashomon_SUMMARY.md,
        results/science_depth/rashomon_full.json
"""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score


ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "kirc_metastasis_expanded.csv"
OUT = ROOT / "results" / "science_depth"
HEADLINE_AUC = 0.7256  # TOP2A − EPAS1 sign-invariant AUROC (G2 bootstrap)


def _gene_pathway_map() -> dict:
    return {
        "HIF_axis":       {"CA9", "VEGFA", "EPAS1", "NDUFA4L2", "ANGPTL4", "BHLHE40", "DDIT4"},
        "Warburg":        {"LDHA", "LDHB", "SLC2A1", "HK2", "PFKP", "PKM", "PDK1", "ENO1", "ENO2", "ALDOA"},
        "Proliferation":  {"TOP2A", "MKI67", "CDK1", "CCNB1", "PCNA", "MCM2"},
        "Tubule_normal":  {"CUBN", "AGXT", "ALB", "PTGER3", "SLC12A1", "SLC12A3", "SLC22A8", "LRP2", "CALB1", "PAX2", "PAX8"},
        "Housekeeping":   {"ACTB", "GAPDH", "RPL13A"},
        "EMT_metastasis": {"COL4A2", "CXCR4", "MMP9", "S100A4", "SPP1", "KRT7"},
        "Carbonic":       {"CA12"},
    }


def _annotate(g1: str, g2: str) -> tuple[str, str]:
    groups = _gene_pathway_map()
    def lookup(g):
        for pw, genes in groups.items():
            if g in genes:
                return pw
        return "other"
    return lookup(g1), lookup(g2)


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(CSV)
    y = (df["label"] == "disease").astype(int).values
    genes = [c for c in df.columns
             if c not in {"sample_id", "label", "m_stage", "age",
                          "batch_index", "patient_id"}
             and pd.api.types.is_numeric_dtype(df[c])]

    print(f"n={len(y)} M1={y.sum()} ({y.mean():.1%})")
    print(f"Gene panel size: {len(genes)}")
    print(f"Pairs to enumerate: {len(genes) * (len(genes)-1) // 2}")

    X = df[genes].apply(pd.to_numeric, errors="coerce").fillna(0).values

    rows = []
    for i, j in combinations(range(len(genes)), 2):
        g1, g2 = genes[i], genes[j]
        score = X[:, i] - X[:, j]
        auc = roc_auc_score(y, score)
        if auc < 0.5:
            direction = "-"
            auc_sign_inv = 1 - auc
        else:
            direction = "+"
            auc_sign_inv = auc
        auprc = average_precision_score(
            y, score if direction == "+" else -score)
        pw1, pw2 = _annotate(g1, g2)
        rows.append({
            "gene1": g1, "gene2": g2,
            "pathway1": pw1, "pathway2": pw2,
            "pathway_combo": tuple(sorted([pw1, pw2])),
            "direction": direction,
            "auc_sign_inv": auc_sign_inv,
            "auprc": auprc,
        })

    df_r = pd.DataFrame(rows).sort_values(
        "auc_sign_inv", ascending=False).reset_index(drop=True)

    # Rashomon set sizes
    rashomon = {}
    for eps in [0.005, 0.01, 0.02, 0.03, 0.05, 0.10]:
        thr = HEADLINE_AUC - eps
        cnt = int((df_r["auc_sign_inv"] >= thr).sum())
        rashomon[f"eps_{eps}"] = {"threshold_auc": thr, "set_size": cnt}

    # Pathway combo distribution in top 20
    top20 = df_r.head(20).copy()
    pathway_dist = top20["pathway_combo"].astype(str).value_counts().to_dict()

    # Where does TOP2A-EPAS1 rank?
    hit = df_r[((df_r["gene1"] == "TOP2A") & (df_r["gene2"] == "EPAS1")) |
               ((df_r["gene1"] == "EPAS1") & (df_r["gene2"] == "TOP2A"))]
    topepas_rank = int(hit.index[0]) + 1 if len(hit) else None

    summary = {
        "dataset": "TCGA-KIRC metastasis M0 vs M1",
        "n_samples": int(len(y)),
        "prevalence": float(y.mean()),
        "gene_panel_size": len(genes),
        "pairs_evaluated": len(df_r),
        "top2a_epas1_auc": HEADLINE_AUC,
        "top2a_epas1_rank": topepas_rank,
        "best_pair_observed": f"{df_r.iloc[0]['gene1']}-{df_r.iloc[0]['gene2']}",
        "best_pair_auc": float(df_r.iloc[0]["auc_sign_inv"]),
        "rashomon_set_sizes": rashomon,
        "top20_pathway_combo_distribution": pathway_dist,
    }

    (OUT / "rashomon_full.json").write_text(json.dumps({
        **summary,
        "top50": df_r.head(50).to_dict(orient="records"),
    }, indent=2, default=str))
    df_r.head(50).to_csv(OUT / "rashomon_top50.csv", index=False)

    # Write human-readable SUMMARY.md
    md = [
        "# Rashomon Set Analysis — 2-gene linear-difference laws",
        "",
        "**Question**: How unique is `TOP2A − EPAS1`? Of C(45,2)=990 gene pairs,",
        "how many achieve sign-invariant AUROC within ε of 0.7256 on TCGA-KIRC",
        "metastasis (M0 vs M1, n=505)?",
        "",
        "## Cohort",
        f"- n = {len(y)}, M1 prevalence = {y.mean():.1%}",
        f"- Gene panel: {len(genes)} genes",
        f"- Pairs evaluated: {len(df_r)}",
        "",
        "## Where does TOP2A − EPAS1 rank?",
        f"- **Rank {topepas_rank} / {len(df_r)}**  (AUROC = {HEADLINE_AUC:.4f})",
        f"- Best observed pair: **{summary['best_pair_observed']}** at AUROC = {summary['best_pair_auc']:.4f}",
        "",
        "## Rashomon set size vs ε",
        "",
        "| ε | Threshold AUROC | Set size |",
        "|---|---|---|",
    ]
    for eps in [0.005, 0.01, 0.02, 0.03, 0.05, 0.10]:
        r = rashomon[f"eps_{eps}"]
        md.append(f"| {eps} | {r['threshold_auc']:.4f} | {r['set_size']} |")

    md += [
        "",
        "**Interpretation**: The size of the Rashomon set at each ε quantifies",
        "how many *structurally distinct* 2-gene laws achieve comparable",
        "discrimination. A small set at tight ε = more unique; a large set = more",
        "redundant alternatives exist.",
        "",
        "## Pathway-combo distribution in top 20 pairs",
        "",
        "Are all top pairs `(Proliferation − HIF_axis)`, or do other pathway",
        "combinations also land in the Rashomon set? This is the sufficient",
        "condition test the H2 1M-context synthesis predicted.",
        "",
        "| Pathway combo | Count in top 20 |",
        "|---|---|",
    ]
    for combo, cnt in sorted(pathway_dist.items(), key=lambda kv: -kv[1]):
        md.append(f"| {combo} | {cnt} |")

    md += [
        "",
        "## Files",
        "- `rashomon_full.json` — top-50 rows + rashomon set sizes + pathway distribution",
        "- `rashomon_top50.csv` — top 50 pairs with annotations",
        "",
        "## Reproduce",
        "```bash",
        "PYTHONPATH=src .venv/bin/python src/rashomon_analysis.py",
        "```",
    ]
    (OUT / "rashomon_SUMMARY.md").write_text("\n".join(md))

    print()
    print("Rashomon set sizes:")
    for eps, r in rashomon.items():
        print(f"  {eps}: threshold={r['threshold_auc']:.4f} set_size={r['set_size']}")
    print(f"\nTOP2A-EPAS1 rank: {topepas_rank} / {len(df_r)}")
    print(f"Best pair: {summary['best_pair_observed']} AUROC={summary['best_pair_auc']:.4f}")
    print(f"\nTop 20 pathway combo distribution:")
    for combo, cnt in sorted(pathway_dist.items(), key=lambda kv: -kv[1]):
        print(f"  {combo}: {cnt}")
    print(f"\nWrote: {OUT}/rashomon_SUMMARY.md")


if __name__ == "__main__":
    main()
