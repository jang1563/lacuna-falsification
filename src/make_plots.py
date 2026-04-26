#!/usr/bin/env python3
"""Generate judge-facing plots from the committed falsification reports.

Writes:
  results/plots/separation_top3_tier1.png  Top-3 Tier-1 PySR candidates,
                                            disease-vs-control score histogram.
  results/plots/falsification_panel_all.png
                                            Side-by-side AUROC bar chart with
                                            Opus ex-ante + PySR tier-1 + PySR
                                            tier-2, coloured pass/fail.
  results/plots/delta_baseline_hist.png    Histogram of delta_baseline across
                                            all 67 evaluated candidates, with
                                            the 0.05 threshold marked.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from lacuna.visualize import plot_separation  # noqa: F401 (kept for parity)


ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
PLOTS = RESULTS / "plots"
DATA = ROOT / "data"

KIRC_GENES = [
    "CA9", "VEGFA", "LDHA", "NDUFA4L2", "SLC2A1", "ENO2",
    "AGXT", "ALB", "CUBN", "PTGER3", "SLC12A3",
    "ACTB", "GAPDH", "RPL13A", "MKI67",
]
_NP_FUNCS = ["log", "log1p", "exp", "abs", "sqrt", "sin", "cos"]


def _build_fn(equation: str, col_names: list[str]):
    ns_funcs = {k: getattr(np, k) for k in _NP_FUNCS}

    def fn(X: np.ndarray) -> np.ndarray:
        ns = {col_names[i]: X[:, i] for i in range(len(col_names))}
        ns.update({f"x{i}": X[:, i] for i in range(X.shape[1])})
        ns.update(ns_funcs)
        return eval(equation, {"__builtins__": {}}, ns)

    return fn


def plot_separation_top3_tier1() -> Path:
    report = json.loads((RESULTS / "flagship_run" / "falsification_report.json").read_text())
    named = json.loads((RESULTS / "flagship_run" / "candidates_named.json").read_text())
    by_eq = {c["equation_original"]: c for c in named}

    # Pick the three highest-AUROC candidates that did NOT numerically error.
    ranked = sorted(
        (r for r in report if not r.get("numeric_error")),
        key=lambda r: -r.get("law_auc", 0.0),
    )[:3]

    df = pd.read_csv(DATA / "kirc_tumor_normal.csv")
    y = (df["label"] == "disease").astype(int).values
    present = [g for g in KIRC_GENES if g in df.columns]
    X = df[present].fillna(0).values.astype(float)

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
    for ax, r in zip(axes, ranked):
        eq = r["equation"]
        try:
            fn = _build_fn(eq, present)
            scores = fn(X)
            scores = np.asarray(scores, dtype=float)
            scores = np.where(np.isfinite(scores), scores, np.nanmedian(scores))
        except Exception:
            continue

        disease = scores[y == 1]
        control = scores[y == 0]
        bins = np.linspace(np.nanmin(scores), np.nanmax(scores), 30)
        ax.hist(disease, bins=bins, alpha=0.55, density=True, color="tab:red",
                label=f"tumor (n={len(disease)})")
        ax.hist(control, bins=bins, alpha=0.55, density=True, color="tab:blue",
                label=f"normal (n={len(control)})")

        pooled = np.sqrt((np.std(disease, ddof=1) ** 2 + np.std(control, ddof=1) ** 2) / 2)
        cohens_d = (np.mean(disease) - np.mean(control)) / pooled if pooled > 0 else 0.0

        named_entry = by_eq.get(r.get("equation"), {})
        pretty = named_entry.get("equation", r["equation"])
        title = pretty if len(pretty) <= 55 else pretty[:52] + "..."
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("law score")
        ax.set_ylabel("density")
        ax.legend(fontsize=8)
        ax.text(0.02, 0.95,
                f"AUROC={r.get('law_auc', 0):.3f}\nΔbase={r.get('delta_baseline', 0):+.3f}\nd={cohens_d:.2f}",
                transform=ax.transAxes, va="top", fontsize=9,
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.85))

    fig.suptitle(
        "Tier-1 top-3 PySR candidates — all fail gate on delta_baseline",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = PLOTS / "separation_top3_tier1.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_falsification_panel_all() -> Path:
    rows: list[dict] = []

    def _load(path: Path, source: str):
        if not path.exists():
            return
        for r in json.loads(path.read_text()):
            rows.append({
                "source": source,
                "label": r.get("law_family") or r.get("equation", "")[:28],
                "auc": float(r.get("law_auc", 0.5) or 0.5),
                "passes": bool(r.get("passes", False)),
                "fail_reason": r.get("fail_reason", ""),
                "delta_baseline": float(r.get("delta_baseline", 0.0) or 0.0),
            })

    # Load from every report currently tracked, including Option A6's
    # metastasis_expanded run where the gate first accepted (9 / 30).
    _load(RESULTS / "opus_exante" / "kirc_flagship_report.json", "Opus ex-ante (tumor)")
    _load(RESULTS / "opus_exante" / "kirc_tier2_report.json", "Opus ex-ante (stage)")
    _load(RESULTS / "opus_exante" / "gse40435_report.json", "Opus ex-ante (GSE40435)")
    _load(RESULTS / "flagship_run" / "falsification_report.json", "PySR tumor/normal (11-gene)")
    _load(RESULTS / "tier2_run" / "falsification_report.json", "PySR stage (11-gene)")
    _load(RESULTS / "track_a_task_landscape" / "survival" / "falsification_report.json",
          "PySR survival (11-gene)")
    _load(RESULTS / "track_a_task_landscape" / "metastasis" / "falsification_report.json",
          "PySR metastasis (11-gene)")
    _load(RESULTS / "track_a_task_landscape" / "survival_expanded" / "falsification_report.json",
          "PySR survival (45-gene)")
    _load(RESULTS / "track_a_task_landscape" / "metastasis_expanded" / "falsification_report.json",
          "PySR metastasis (45-gene)")

    sources = sorted({r["source"] for r in rows})
    colours = {s: f"C{i}" for i, s in enumerate(sources)}

    fig, ax = plt.subplots(figsize=(11, 7))
    for i, r in enumerate(rows):
        ax.barh(i, r["auc"], color=colours[r["source"]],
                alpha=0.9 if r["passes"] else 0.45,
                edgecolor="black" if r["passes"] else "none",
                linewidth=1.0 if r["passes"] else 0.0)
    ax.axvline(x=0.5, color="gray", linestyle="--", linewidth=1)
    ax.set_yticks([])
    ax.set_xlabel("AUROC")
    ax.set_xlim(0.0, 1.05)

    n_total = len(rows)
    n_pass = sum(1 for r in rows if r["passes"])
    ax.set_title(
        "Pre-registered 5-test gate across every tracked falsification run\n"
        f"{n_pass} survivors of {n_total} candidates "
        "(solid-edge bars = pass; transparent bars = fail)"
    )
    from matplotlib.patches import Patch
    handles = [Patch(color=c, label=s) for s, c in colours.items()]
    handles.append(plt.Line2D([0], [0], color="gray", linestyle="--", label="chance (0.5)"))
    ax.legend(handles=handles, loc="lower right", fontsize=7, ncol=2)
    fig.tight_layout()
    out = PLOTS / "falsification_panel_all.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_delta_baseline_hist() -> Path:
    deltas: list[tuple[str, float]] = []

    def _load(path: Path, source: str):
        if not path.exists():
            return
        for r in json.loads(path.read_text()):
            d = r.get("delta_baseline")
            if d is None:
                continue
            deltas.append((source, float(d)))

    _load(RESULTS / "opus_exante" / "kirc_flagship_report.json", "Opus ex-ante × tumor/normal")
    _load(RESULTS / "flagship_run" / "falsification_report.json", "PySR × tumor/normal (11-gene)")
    _load(RESULTS / "opus_exante" / "kirc_tier2_report.json", "Opus ex-ante × stage")
    _load(RESULTS / "tier2_run" / "falsification_report.json", "PySR × stage (11-gene)")
    _load(RESULTS / "track_a_task_landscape" / "survival" / "falsification_report.json",
          "PySR × survival (11-gene)")
    _load(RESULTS / "track_a_task_landscape" / "metastasis" / "falsification_report.json",
          "PySR × metastasis (11-gene)")
    _load(RESULTS / "track_a_task_landscape" / "survival_expanded" / "falsification_report.json",
          "PySR × survival (45-gene)")
    _load(RESULTS / "track_a_task_landscape" / "metastasis_expanded" / "falsification_report.json",
          "PySR × metastasis (45-gene) — SURVIVORS")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    sources = {}
    for src, val in deltas:
        sources.setdefault(src, []).append(val)

    edges = np.linspace(-0.25, 0.12, 31)
    for src, vals in sources.items():
        ax.hist(vals, bins=edges, alpha=0.55, label=f"{src} (n={len(vals)})")

    ax.axvline(x=0.05, color="black", linestyle="--", linewidth=1.5,
               label="pre-registered threshold (+0.05)")
    ax.set_xlabel("delta_baseline  (law_AUROC − best single gene)")
    ax.set_ylabel("number of candidates")
    n_total = sum(len(v) for v in sources.values())
    ax.set_title(
        f"Compound-law incremental AUROC across {n_total} candidates and 6 task-panel combinations\n"
        "The pre-registered +0.05 bar (dashed) is only cleared by the\n"
        "metastasis 45-gene run (TOP2A − EPAS1 cluster at Δ = +0.069)"
    )
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    out = PLOTS / "delta_baseline_hist.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def main() -> None:
    p1 = plot_separation_top3_tier1()
    print(f"wrote {p1}")
    p2 = plot_falsification_panel_all()
    print(f"wrote {p2}")
    p3 = plot_delta_baseline_hist()
    print(f"wrote {p3}")


if __name__ == "__main__":
    main()
