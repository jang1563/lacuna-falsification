import matplotlib
matplotlib.use("Agg")

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import gaussian_kde


def plot_separation(
    scores: np.ndarray,
    labels: np.ndarray,
    equation_str: str,
    output_path: str | Path,
    disease_label: str = "disease",
    control_label: str = "control",
) -> Path:
    disease_scores = scores[labels == 1]
    control_scores = scores[labels == 0]

    pooled_std = np.sqrt(
        (np.std(disease_scores, ddof=1) ** 2 + np.std(control_scores, ddof=1) ** 2) / 2
    )
    cohens_d = (np.mean(disease_scores) - np.mean(control_scores)) / pooled_std if pooled_std > 0 else 0.0

    fig, ax = plt.subplots(figsize=(8, 5))

    all_scores = np.concatenate([disease_scores, control_scores])
    bins = np.linspace(all_scores.min(), all_scores.max(), 30)

    ax.hist(disease_scores, bins=bins, alpha=0.5, density=True, color="tab:red",
            label=f"{disease_label} (n={len(disease_scores)})")
    ax.hist(control_scores, bins=bins, alpha=0.5, density=True, color="tab:blue",
            label=f"{control_label} (n={len(control_scores)})")

    x_range = np.linspace(all_scores.min(), all_scores.max(), 300)
    for group, color in [(disease_scores, "tab:red"), (control_scores, "tab:blue")]:
        if len(group) > 1:
            kde = gaussian_kde(group)
            ax.plot(x_range, kde(x_range), color=color, linewidth=2)

    title = equation_str if len(equation_str) <= 60 else equation_str[:60]
    ax.set_title(title)
    ax.set_xlabel("law score")
    ax.set_ylabel("density")
    ax.legend()
    ax.text(0.98, 0.97, f"Cohen's d = {cohens_d:.2f}",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=10, color="black")

    fig.tight_layout()
    out = Path(output_path)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_falsification_panel(
    candidates: list[dict],
    output_path: str | Path,
) -> Path:
    sorted_candidates = sorted(candidates, key=lambda c: c["law_auc"], reverse=True)

    names = [c["name"] for c in sorted_candidates]
    aucs = [c["law_auc"] for c in sorted_candidates]
    passes = [c["passes"] for c in sorted_candidates]
    fail_reasons = [c["fail_reason"] for c in sorted_candidates]

    n_total = len(candidates)
    n_survived = sum(1 for c in candidates if c["passes"])

    fig, ax = plt.subplots(figsize=(9, max(3, 0.6 * n_total + 1.5)))

    colors = ["tab:green" if p else "tab:red" for p in passes]
    y_pos = range(len(names))
    ax.barh(list(y_pos), aucs, color=colors)

    ax.axvline(x=0.5, color="gray", linestyle="--", linewidth=1.2, label="chance (0.5)")
    ax.axvline(x=0.7, color="black", linestyle="--", linewidth=1.2, label="threshold (0.7)")

    for i, (auc, passed, reason) in enumerate(zip(aucs, passes, fail_reasons)):
        if not passed and reason:
            ax.text(auc + 0.005, i, reason, va="center", ha="left",
                    fontsize=8, color="tab:red")

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(names, fontsize=9)
    ax.set_xlim(0.4, 1.0)
    ax.set_xlabel("AUROC")
    ax.set_title(f"Falsification Panel — {n_total} candidates ({n_survived} survived)")
    ax.legend(loc="lower right", fontsize=8)

    fig.tight_layout()
    out = Path(output_path)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out
