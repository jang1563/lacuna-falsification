#!/usr/bin/env python3
"""PhL-5 (BRCA cross-cancer) + PhL-6 (GSE53757 external replay) probes.

Pre-registrations:
  - preregistrations/20260423T224229Z_phl5_brca_cross_cancer_generalization.yaml
  - preregistrations/20260423T224229Z_phl6_gse53757_external_replay.yaml

Both were committed at git 8abbcfd BEFORE this script was written.

This single script handles both probes because the pipeline is identical:
compute `score = TOP2A − EPAS1`, apply the pre-registered 5-test gate, report.
The only difference is cohort + label column.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from theory_copilot.falsification import run_falsification_suite


REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "results" / "track_a_task_landscape" / "external_replay"


def _labels_to_int(series: pd.Series) -> np.ndarray:
    """Normalise a label column to int 0/1. 'disease' / 'tumor' / '1' / True → 1."""
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(int).values
    s = series.astype(str).str.strip().str.lower()
    return s.map(lambda v: 1 if v in {"disease", "tumor", "case", "1", "true"} else 0).values.astype(int)


def _run_gate_on_score(
    csv_path: Path,
    hypothesis_id: str,
    label_col: str = "label",
    covariate_cols: list[str] | None = None,
    gene_panel_for_baseline: list[str] | None = None,
    seed: int = 42,
) -> dict:
    """Compute score=TOP2A-EPAS1 on the CSV and run the 5-test falsification gate."""
    df = pd.read_csv(csv_path)

    # Ensure required columns.
    for col in ("TOP2A", "EPAS1", label_col):
        if col not in df.columns:
            raise SystemExit(f"{csv_path} missing required column: {col}")

    # Coerce numeric, drop NaN gene rows.
    df["TOP2A"] = pd.to_numeric(df["TOP2A"], errors="coerce")
    df["EPAS1"] = pd.to_numeric(df["EPAS1"], errors="coerce")
    df = df.dropna(subset=["TOP2A", "EPAS1", label_col]).copy()

    y = _labels_to_int(df[label_col])

    # Build the feature matrix for the baseline/confound tests. If the cohort
    # has a wider gene panel, include those in X for baseline; otherwise just
    # use TOP2A + EPAS1 as the baseline pool.
    if gene_panel_for_baseline:
        present = [g for g in gene_panel_for_baseline if g in df.columns]
        if not present:
            present = ["TOP2A", "EPAS1"]
    else:
        present = ["TOP2A", "EPAS1"]
    X = df[present].astype(float).values

    # Covariates, if any.
    cov = None
    if covariate_cols:
        usable = [c for c in covariate_cols if c in df.columns]
        if usable:
            cov_df = df[usable].copy()
            for c in usable:
                if not pd.api.types.is_numeric_dtype(cov_df[c]):
                    cov_df[c] = pd.Categorical(cov_df[c]).codes
            cov_df = cov_df.fillna(-1)
            cov = cov_df.astype(float).values

    # Score function: TOP2A − EPAS1. Indexes inside X correspond to `present`.
    ix_top = present.index("TOP2A") if "TOP2A" in present else 0
    ix_epas = present.index("EPAS1") if "EPAS1" in present else 1

    def score_fn(X: np.ndarray) -> np.ndarray:
        return X[:, ix_top] - X[:, ix_epas]

    # Run the 5-test gate.
    report = run_falsification_suite(
        equation_fn=score_fn,
        X=X,
        y=y,
        X_covariates=cov,
        include_decoy=True,
    )

    return {
        "hypothesis_id": hypothesis_id,
        "cohort_csv": str(csv_path.relative_to(REPO_ROOT)),
        "n": int(len(df)),
        "n_positive": int(y.sum()),
        "n_negative": int(len(y) - y.sum()),
        "gene_panel_used": present,
        "covariates_used": covariate_cols or [],
        "report": report,
    }


def _stage_probe_gse53757(csv_path: Path, seed: int = 42) -> dict:
    """Secondary PhL-6 endpoint: stage 1-2 vs 3-4 on the 72 tumor samples."""
    df = pd.read_csv(csv_path)
    df = df[df["label"].astype(str).str.strip().str.lower() == "disease"].copy()
    df["TOP2A"] = pd.to_numeric(df["TOP2A"], errors="coerce")
    df["EPAS1"] = pd.to_numeric(df["EPAS1"], errors="coerce")
    df = df.dropna(subset=["TOP2A", "EPAS1", "tumor_stage"]).copy()
    df["stage_norm"] = df["tumor_stage"].astype(str).str.strip().str.lower()
    early_mask = df["stage_norm"].isin({"stage 1", "stage 2"})
    late_mask = df["stage_norm"].isin({"stage 3", "stage 4"})
    df_binary = df[early_mask | late_mask].copy()
    df_binary["y_late"] = late_mask[early_mask | late_mask].astype(int).values

    if len(df_binary) < 20:
        return {"status": "insufficient_data", "n": int(len(df_binary))}

    score = df_binary["TOP2A"].values - df_binary["EPAS1"].values
    y = df_binary["y_late"].values

    from sklearn.metrics import roc_auc_score
    auc = float(roc_auc_score(y, score))
    auc_sign_inv = max(auc, 1 - auc)

    # Bootstrap 95% CI
    rng = np.random.default_rng(seed)
    n = len(y)
    boots = []
    for _ in range(1000):
        idx = rng.integers(0, n, size=n)
        y_b = y[idx]
        s_b = score[idx]
        if len(np.unique(y_b)) < 2:
            continue
        a = roc_auc_score(y_b, s_b)
        boots.append(max(a, 1 - a))
    ci_low = float(np.percentile(boots, 2.5))
    ci_high = float(np.percentile(boots, 97.5))

    return {
        "status": "run",
        "n": int(len(df_binary)),
        "n_early_stage12": int((~df_binary["y_late"].astype(bool)).sum()),
        "n_late_stage34": int(df_binary["y_late"].sum()),
        "auroc": auc,
        "auroc_sign_inv": auc_sign_inv,
        "ci_lower": ci_low,
        "ci_upper": ci_high,
        "pass_secondary": bool(auc_sign_inv > 0.6 and ci_low > 0.5),
    }


def run_phl5_brca() -> dict:
    out_dir = OUT_DIR / "brca_cross_cancer"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv = REPO_ROOT / "data" / "brca_tumor_normal.csv"
    print(f"\n=== PhL-5 — BRCA cross-cancer probe on {csv.name} ===")
    # BRCA panel has its own genes; we just need TOP2A/EPAS1 for the score,
    # plus a baseline pool for delta_baseline. Use all available numeric
    # gene-like columns from the CSV (patient_id / label / age / batch_index
    # excluded).
    df_cols = pd.read_csv(csv, nrows=1).columns.tolist()
    exclude = {"sample_id", "label", "age", "batch_index", "patient_id"}
    baseline_panel = [c for c in df_cols if c not in exclude]
    cov = ["age", "batch_index"] if all(c in df_cols for c in ["age", "batch_index"]) else None
    result = _run_gate_on_score(
        csv_path=csv,
        hypothesis_id="phl5_brca_cross_cancer_generalization",
        gene_panel_for_baseline=baseline_panel,
        covariate_cols=cov,
    )
    result["prereg_file"] = (
        "preregistrations/20260423T224229Z_phl5_brca_cross_cancer_generalization.yaml"
    )
    result["pre_registered_expected_verdict"] = "FAIL (ccRCC-specific negative control)"
    verdict = "PASS" if result["report"]["passes"] else "FAIL"
    result["verdict"] = verdict
    (out_dir / "verdict.json").write_text(json.dumps(result, indent=2, default=str))
    print(f"PhL-5 verdict: {verdict}")
    print(f"  n_tumor / n_normal = {result['n_positive']} / {result['n_negative']}")
    r = result["report"]
    if isinstance(r, dict):
        print(f"  law_auc      = {r.get('law_auc'):.4f}" if r.get('law_auc') is not None else "  law_auc      = N/A")
        print(f"  baseline_auc = {r.get('baseline_auc')}")
        print(f"  delta_base   = {r.get('delta_baseline')}")
        print(f"  perm_p       = {r.get('perm_p')}")
        print(f"  ci_lower     = {r.get('ci_lower')}")
        print(f"  decoy_p      = {r.get('decoy_p')}")
        print(f"  passes       = {r.get('passes')}")
    return result


def run_phl6_gse53757() -> dict:
    out_dir = OUT_DIR / "gse53757"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv = REPO_ROOT / "data" / "gse53757_ccrcc.csv"
    print(f"\n=== PhL-6 — GSE53757 external replay on {csv.name} ===")
    df_cols = pd.read_csv(csv, nrows=1).columns.tolist()
    exclude = {"sample_id", "label", "age", "batch_index", "patient_id",
               "m_stage", "tumor_stage"}
    baseline_panel = [c for c in df_cols if c not in exclude]
    cov = ["age", "batch_index"] if all(c in df_cols for c in ["age", "batch_index"]) else None

    # Primary endpoint: T-vs-N classification with 5-test gate.
    primary = _run_gate_on_score(
        csv_path=csv,
        hypothesis_id="phl6_gse53757_external_replay",
        gene_panel_for_baseline=baseline_panel,
        covariate_cols=cov,
    )
    primary["prereg_file"] = (
        "preregistrations/20260423T224229Z_phl6_gse53757_external_replay.yaml"
    )
    primary_verdict = "PASS" if primary["report"]["passes"] else "FAIL"
    primary["verdict_primary"] = primary_verdict
    print(f"PhL-6 primary (T-vs-N) verdict: {primary_verdict}")
    print(f"  n_tumor / n_normal = {primary['n_positive']} / {primary['n_negative']}")
    r = primary["report"]
    if isinstance(r, dict):
        print(f"  law_auc      = {r.get('law_auc'):.4f}" if r.get('law_auc') is not None else "  law_auc      = N/A")
        print(f"  baseline_auc = {r.get('baseline_auc')}")
        print(f"  delta_base   = {r.get('delta_baseline')}")
        print(f"  perm_p       = {r.get('perm_p')}")
        print(f"  ci_lower     = {r.get('ci_lower')}")
        print(f"  decoy_p      = {r.get('decoy_p')}")
        print(f"  passes       = {r.get('passes')}")

    # Secondary: stage1-2 vs stage3-4.
    secondary = _stage_probe_gse53757(csv)
    primary["secondary_endpoint_stage_stratification"] = secondary
    print(f"\nPhL-6 secondary (stage 1-2 vs 3-4) status: {secondary.get('status')}")
    if secondary.get("status") == "run":
        print(f"  n = {secondary['n']} (early {secondary['n_early_stage12']}, late {secondary['n_late_stage34']})")
        print(f"  AUROC (sign-inv) = {secondary['auroc_sign_inv']:.3f}, CI 95% [{secondary['ci_lower']:.3f}, {secondary['ci_upper']:.3f}]")
        print(f"  secondary PASS: {secondary['pass_secondary']}")

    (out_dir / "verdict.json").write_text(json.dumps(primary, indent=2, default=str))
    return primary


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"

    if mode in ("brca", "both"):
        try:
            run_phl5_brca()
        except Exception as exc:
            print(f"PhL-5 ERRORED: {exc}")
            import traceback
            traceback.print_exc()

    if mode in ("gse53757", "both"):
        try:
            run_phl6_gse53757()
        except Exception as exc:
            print(f"PhL-6 ERRORED: {exc}")
            import traceback
            traceback.print_exc()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
