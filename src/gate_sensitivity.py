"""Track B (Gate Robustness) — threshold sensitivity analysis.

Re-applies the pre-registered 5-test falsification gate across a grid of
threshold values to the 60 existing candidates (26 flagship PySR + 27 tier2
PySR + 7 Opus ex-ante). No re-execution of the gate is needed — the raw
metrics (perm_p_fdr, ci_lower, delta_baseline, delta_confound, decoy_p) are
already present in the falsification reports.

Outputs land under ``results/track_b_gate_robustness/``:
  - ``threshold_grid.csv`` long-format (candidate_id, source, threshold_name,
    threshold_value, pass)
  - ``threshold_heatmap.png`` candidates × scenarios pass/fail grid

Usage:
    python src/gate_sensitivity.py \
        --out-dir results/track_b_gate_robustness
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Pre-registered thresholds encoded in src/theory_copilot/falsification.py.
CURRENT_THRESHOLDS: dict[str, float] = {
    "perm_p_fdr": 0.05,
    "ci_lower": 0.60,
    "delta_baseline": 0.05,
    "delta_confound": 0.03,
    "decoy_p": 0.05,
}

# Per-threshold directions encode whether "pass" is ``<`` or ``>`` the cutoff.
# For perm_p_fdr and decoy_p a pass requires being *below* the threshold
# (small p-value). For ci_lower / delta_baseline / delta_confound, pass
# requires being *above* the threshold.
PASS_DIRECTION: dict[str, str] = {
    "perm_p_fdr": "lt",
    "ci_lower": "gt",
    "delta_baseline": "gt",
    "delta_confound": "gt",
    "decoy_p": "lt",
}

# Grids from research/TRACK_B_gate_robustness.md §B1.
DEFAULT_GRIDS: dict[str, list[float]] = {
    "delta_baseline": [0.00, 0.01, 0.02, 0.025, 0.03, 0.035, 0.04, 0.05, 0.06, 0.08],
    "ci_lower": [0.50, 0.55, 0.60, 0.65, 0.70],
    "perm_p_fdr": [0.01, 0.05, 0.10],
    "delta_confound": [0.00, 0.01, 0.02, 0.03, 0.05],
    "decoy_p": [0.01, 0.05, 0.10],
}

# Sources to load and their source tag.
DEFAULT_SOURCES: list[tuple[str, str]] = [
    ("flagship_pysr", "results/flagship_run/falsification_report.json"),
    ("tier2_pysr", "results/tier2_run/falsification_report.json"),
    ("opus_exante_flagship", "results/opus_exante/kirc_flagship_report.json"),
    ("opus_exante_tier2", "results/opus_exante/kirc_tier2_report.json"),
]


def load_reports(sources: list[tuple[str, str]]) -> pd.DataFrame:
    """Load falsification reports, tag with source, assign stable candidate_id."""
    rows: list[dict[str, Any]] = []
    for source_tag, path in sources:
        p = Path(path)
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text())
        except json.JSONDecodeError:
            continue
        for idx, entry in enumerate(data):
            if not isinstance(entry, dict):
                continue
            eq = entry.get("equation", f"<unknown_{idx}>")
            rows.append(
                {
                    "candidate_id": f"{source_tag}::{idx:03d}",
                    "source": source_tag,
                    "equation": eq,
                    "law_family": entry.get("law_family", ""),
                    "perm_p_fdr": _safe_float(entry.get("perm_p_fdr")),
                    "perm_p": _safe_float(entry.get("perm_p")),
                    "ci_lower": _safe_float(entry.get("ci_lower")),
                    "delta_baseline": _safe_float(entry.get("delta_baseline")),
                    "delta_confound": _safe_float(entry.get("delta_confound")),
                    "decoy_p": _safe_float(entry.get("decoy_p")),
                    "law_auc": _safe_float(entry.get("law_auc")),
                    "baseline_auc": _safe_float(entry.get("baseline_auc")),
                    "passes_current": bool(entry.get("passes", False)),
                    "fail_reason_current": entry.get("fail_reason", ""),
                }
            )
    return pd.DataFrame(rows)


def _safe_float(value: Any) -> float:
    if value is None:
        return np.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def _pass_single_metric(metric_value: float, threshold: float, direction: str) -> bool:
    if np.isnan(metric_value):
        return False
    if direction == "lt":
        return metric_value < threshold
    if direction == "gt":
        return metric_value > threshold
    raise ValueError(f"unknown direction: {direction}")


def passes_with_thresholds(
    row: pd.Series | dict[str, Any], thresholds: dict[str, float]
) -> bool:
    """Apply all five gate tests with custom thresholds to a single row."""
    return all(
        _pass_single_metric(
            _get(row, name),
            thresholds[name],
            PASS_DIRECTION[name],
        )
        for name in CURRENT_THRESHOLDS
    )


def _get(row: pd.Series | dict[str, Any], key: str) -> float:
    if isinstance(row, pd.Series):
        return _safe_float(row.get(key))
    return _safe_float(row.get(key))


def threshold_grid_pass(
    df: pd.DataFrame, grids: dict[str, list[float]] | None = None
) -> pd.DataFrame:
    """Sweep each threshold one-at-a-time, keeping others at their current
    pre-registered value. Returns a long-format DataFrame with one row per
    (candidate_id, threshold_name, threshold_value)."""
    grids = grids or DEFAULT_GRIDS
    records: list[dict[str, Any]] = []

    # Baseline row: all-current (should replicate the existing verdict).
    for _, row in df.iterrows():
        records.append(
            {
                "candidate_id": row["candidate_id"],
                "source": row["source"],
                "equation": row["equation"],
                "threshold_name": "current_all",
                "threshold_value": float("nan"),
                "pass": passes_with_thresholds(row, CURRENT_THRESHOLDS),
            }
        )

    for name, values in grids.items():
        for v in values:
            scenario = {**CURRENT_THRESHOLDS, name: float(v)}
            for _, row in df.iterrows():
                records.append(
                    {
                        "candidate_id": row["candidate_id"],
                        "source": row["source"],
                        "equation": row["equation"],
                        "threshold_name": name,
                        "threshold_value": float(v),
                        "pass": passes_with_thresholds(row, scenario),
                    }
                )
    return pd.DataFrame.from_records(records)


def smallest_flip_threshold(
    grid_df: pd.DataFrame, threshold_name: str
) -> tuple[float | None, int]:
    """Return the smallest threshold value at which at least one candidate
    passes, and the count of candidates passing at that value. Returns
    (None, 0) if no value in the grid yields any survivor."""
    sub = grid_df[grid_df["threshold_name"] == threshold_name].copy()
    if sub.empty:
        return None, 0
    # For "gt" directions, relaxing means lowering threshold; for "lt",
    # relaxing means raising. Either way, iterate values in the order that
    # produces progressive relaxation and stop on first flip.
    direction = PASS_DIRECTION.get(threshold_name, "gt")
    pivoted = (
        sub.groupby("threshold_value")["pass"].sum().sort_index(
            ascending=(direction == "gt")
        )
    )
    for value, count in pivoted.items():
        if count > 0:
            return float(value), int(count)
    return None, 0


def build_heatmap(
    grid_df: pd.DataFrame, out_path: Path, title: str = "Gate threshold sensitivity"
) -> None:
    """Render a candidates × scenarios pass/fail heatmap."""
    sub = grid_df.copy()
    sub["scenario"] = sub.apply(
        lambda r: r["threshold_name"]
        if r["threshold_name"] == "current_all"
        else f"{r['threshold_name']}={r['threshold_value']:g}",
        axis=1,
    )
    pivot = sub.pivot_table(
        index="candidate_id",
        columns="scenario",
        values="pass",
        aggfunc="first",
    ).astype(float)

    scenario_order = ["current_all"]
    for name in DEFAULT_GRIDS:
        for v in DEFAULT_GRIDS[name]:
            label = f"{name}={v:g}"
            if label in pivot.columns:
                scenario_order.append(label)
    scenario_order = [c for c in scenario_order if c in pivot.columns]
    pivot = pivot[scenario_order]

    pivot = pivot.sort_index()

    fig_height = max(6.0, 0.18 * len(pivot.index))
    fig_width = max(10.0, 0.4 * len(pivot.columns))
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    cmap = plt.get_cmap("RdYlGn")
    im = ax.imshow(pivot.values, aspect="auto", cmap=cmap, vmin=0.0, vmax=1.0)

    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=75, ha="right", fontsize=7)
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=6)
    ax.set_xlabel("Threshold scenario")
    ax.set_ylabel("Candidate (source::idx)")
    ax.set_title(title)

    cbar = fig.colorbar(im, ax=ax, shrink=0.5)
    cbar.set_ticks([0.0, 1.0])
    cbar.set_ticklabels(["FAIL", "PASS"])

    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def summarize_flips(grid_df: pd.DataFrame) -> dict[str, Any]:
    """Aggregate per-threshold flip diagnostics and the full flip curve
    (survivors by threshold value, split by source)."""
    out: dict[str, Any] = {"current_all_survivors": int(
        grid_df.loc[grid_df["threshold_name"] == "current_all", "pass"].sum()
    )}
    for name in DEFAULT_GRIDS:
        value, count = smallest_flip_threshold(grid_df, name)
        sub = grid_df[grid_df["threshold_name"] == name]
        by_value = (
            sub.groupby("threshold_value")["pass"].sum().astype(int).to_dict()
        )
        by_value_by_source: dict[str, dict[str, int]] = {}
        for (tv, src), grp in sub.groupby(["threshold_value", "source"]):
            by_value_by_source.setdefault(f"{tv:g}", {})[src] = int(grp["pass"].sum())
        out[name] = {
            "smallest_flip_value": value,
            "survivors_at_that_value": count,
            "flip_curve": {f"{k:g}": int(v) for k, v in sorted(by_value.items())},
            "flip_curve_by_source": by_value_by_source,
        }
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out-dir",
        default="results/track_b_gate_robustness",
        help="Output directory (default: results/track_b_gate_robustness)",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_reports(DEFAULT_SOURCES)
    print(f"Loaded {len(df)} candidates across {df['source'].nunique()} sources")
    print(df["source"].value_counts().to_string())

    grid_df = threshold_grid_pass(df)
    csv_path = out_dir / "threshold_grid.csv"
    grid_df.to_csv(csv_path, index=False)
    print(f"Wrote {csv_path} ({len(grid_df)} rows)")

    heatmap_path = out_dir / "threshold_heatmap.png"
    build_heatmap(grid_df, heatmap_path, title="Gate threshold sensitivity (60 candidates)")
    print(f"Wrote {heatmap_path}")

    summary = summarize_flips(grid_df)
    summary_path = out_dir / "threshold_grid_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"Wrote {summary_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
