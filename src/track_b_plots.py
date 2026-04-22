"""Track B — plot helpers for B2/B4/B5/B6 summary figures.

Reads the JSON/CSV artifacts already committed and renders PNGs into
``results/track_b_gate_robustness/``. Intended as a judge-facing visual
supplement to SUMMARY.md.

Figures:
  - b2_baseline_ablation.png
  - b4_bootstrap_seed_variance.png
  - b5_scaling_ablation.png
  - b6_cohort_size_curve.png

Usage:
    python src/track_b_plots.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


OUT_DIR = Path("results/track_b_gate_robustness")


def plot_b2_baseline_ablation() -> Path:
    df = pd.read_csv(OUT_DIR / "baseline_ablation.csv")
    # Max delta per (task, baseline_kind)
    agg = (
        df.groupby(["task", "baseline_kind"])["delta_baseline"].max().reset_index()
    )
    tasks = sorted(agg["task"].unique())
    kinds = ["sign_invariant_max", "lr_single", "lr_pair_interaction"]
    positions = np.arange(len(kinds))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    for i, task in enumerate(tasks):
        values = [
            float(agg.loc[(agg["task"] == task) & (agg["baseline_kind"] == k), "delta_baseline"].iloc[0])
            for k in kinds
        ]
        offset = (i - (len(tasks) - 1) / 2.0) * width
        bars = ax.bar(positions + offset, values, width, label=task)
        for bar, v in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                v + 0.002 if v >= 0 else v - 0.004,
                f"{v:+.3f}",
                ha="center",
                va="bottom" if v >= 0 else "top",
                fontsize=9,
            )
    ax.axhline(0.05, color="red", linestyle="--", linewidth=1, label="gate threshold (0.05)")
    ax.axhline(0.0, color="gray", linewidth=0.5)
    ax.set_xticks(positions)
    ax.set_xticklabels(kinds, rotation=10)
    ax.set_ylabel("Max delta_baseline across 67 candidates")
    ax.set_title("B2 — Baseline definition ablation")
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    out = OUT_DIR / "b2_baseline_ablation.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


def plot_b4_bootstrap_variance() -> Path:
    data = json.loads((OUT_DIR / "bootstrap_seed_variance.json").read_text())
    records = data["records"]
    df = pd.DataFrame(records)
    df = df.sort_values(["source", "candidate_id"])

    fig, ax = plt.subplots(figsize=(10, 6))
    for i, row in enumerate(df.itertuples(index=False)):
        cil_vals = np.array(row.ci_lower_per_seed)
        ax.scatter(
            np.full_like(cil_vals, i, dtype=float),
            cil_vals,
            alpha=0.6,
            s=30,
            edgecolors="black",
            linewidths=0.3,
        )
    ax.axhline(0.60, color="red", linestyle="--", linewidth=1, label="gate threshold (0.60)")
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(df["candidate_id"], rotation=75, ha="right", fontsize=7)
    ax.set_ylabel("ci_lower (bootstrap 5 seeds)")
    ax.set_title("B4 — ci_lower seed variance across 20 top candidates")
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    out = OUT_DIR / "b4_bootstrap_seed_variance.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


def plot_b5_scaling_ablation() -> Path:
    summary = json.loads((OUT_DIR / "scaling_ablation_summary.json").read_text())
    df = pd.DataFrame(summary["per_task_per_scaling"])
    tasks = sorted(df["task"].unique())
    scalings = ["raw", "zscore", "rank", "minmax"]
    positions = np.arange(len(scalings))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    for i, task in enumerate(tasks):
        values = [
            float(df.loc[(df["task"] == task) & (df["scaling"] == s), "max_delta_baseline"].iloc[0])
            for s in scalings
        ]
        offset = (i - (len(tasks) - 1) / 2.0) * width
        bars = ax.bar(positions + offset, values, width, label=task)
        for bar, v in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                v + 0.002,
                f"{v:+.3f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )
    ax.axhline(
        summary["threshold"],
        color="red",
        linestyle="--",
        linewidth=1,
        label=f"gate threshold ({summary['threshold']:.2f})",
    )
    ax.set_xticks(positions)
    ax.set_xticklabels(scalings)
    ax.set_ylabel("Max delta_baseline")
    ax.set_title("B5 — Feature-scaling ablation")
    ax.legend(loc="upper left", fontsize=9)
    fig.tight_layout()
    out = OUT_DIR / "b5_scaling_ablation.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


def plot_b6_cohort_size_curve() -> Path:
    data = json.loads((OUT_DIR / "cohort_size_curve.json").read_text())
    df = pd.DataFrame([r for r in data["records"] if "law_auc" in r])
    agg = (
        df.groupby("n")
        .agg(
            law_auc=("law_auc", "mean"),
            ci_lower_mean=("ci_lower", "mean"),
            ci_lower_min=("ci_lower", "min"),
            ci_lower_max=("ci_lower", "max"),
            delta=("delta_baseline", "mean"),
        )
        .reset_index()
        .sort_values("n")
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    ns = agg["n"].values
    ax1.errorbar(
        ns,
        agg["ci_lower_mean"],
        yerr=[
            agg["ci_lower_mean"] - agg["ci_lower_min"],
            agg["ci_lower_max"] - agg["ci_lower_mean"],
        ],
        fmt="o-",
        label="ci_lower (mean, seed range)",
        capsize=4,
    )
    ax1.plot(ns, agg["law_auc"], "s--", label="law_auc (mean)", alpha=0.7)
    ax1.axhline(0.60, color="red", linestyle="--", linewidth=1, label="ci_lower gate (0.60)")
    ax1.set_xlabel("cohort size n")
    ax1.set_ylabel("AUROC / ci_lower")
    ax1.set_title("B6 — law_auc + ci_lower vs n")
    ax1.legend(loc="lower right", fontsize=9)
    ax1.grid(alpha=0.3)

    ax2.plot(ns, agg["delta"], "o-")
    ax2.axhline(0.05, color="red", linestyle="--", linewidth=1, label="delta gate (0.05)")
    ax2.set_xlabel("cohort size n")
    ax2.set_ylabel("delta_baseline (mean)")
    ax2.set_title("B6 — delta_baseline vs n")
    ax2.legend(loc="lower right", fontsize=9)
    ax2.grid(alpha=0.3)

    fig.suptitle(
        f"B6 — Cohort-size subsampling of Opus ex-ante HIF law (full n={data['full_n']})",
        fontsize=11,
    )
    fig.tight_layout()
    out = OUT_DIR / "b6_cohort_size_curve.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.parse_args()
    for fn in (
        plot_b2_baseline_ablation,
        plot_b4_bootstrap_variance,
        plot_b5_scaling_ablation,
        plot_b6_cohort_size_curve,
    ):
        try:
            path = fn()
            print(f"Wrote {path}")
        except Exception as exc:  # pylint: disable=broad-except
            print(f"FAIL {fn.__name__}: {exc}")


if __name__ == "__main__":
    main()
