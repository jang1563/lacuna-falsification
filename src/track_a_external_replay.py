"""E3 external-cohort replay for the TOP2A - EPAS1 survivor.

Applies the same law to three independent ccRCC cohorts, in priority order:
  1. GEO GSE53757   (Affymetrix GPL570, 72 ccRCC + 72 normal, no M-stage)
  2. GEO GSE40435   (Illumina GPL10558, 101 paired, no M-stage; expanded panel)
  3. CPTAC-3 ccRCC  (proteogenomic, has M-stage but stub-only without API token)

The plan: "first cohort with TOP2A + EPAS1 + M-status wins." Neither GSE53757
nor GSE40435 carry M-status at the patient level, so the replay on those
cohorts runs tumor-vs-normal (the law's score should separate tumor from
normal because TOP2A-EPAS1 reflects the proliferation-over-HIF-2α program;
AUROC on tumor-vs-normal is flagged explicitly as *not* a metastasis replay).

If CPTAC-3 is accessible (PDC GraphQL on this machine), it's the only cohort
that can run the full 5-test gate on M0-vs-M1.

If ALL 3 cohorts fail the metastasis replay, the honest outcome is that the
internal 5-fold CV on TCGA-KIRC (AUROC 0.722 +- 0.078) stays the flagship
internal replay and the SUMMARY documents the three negatives verbatim.

Output: results/track_a_task_landscape/external_replay/SUMMARY.md
        results/track_a_task_landscape/external_replay/per_cohort.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from theory_copilot.falsification import run_falsification_suite  # noqa: E402

OUT_DIR = REPO / "results" / "track_a_task_landscape" / "external_replay"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _law_fn(X: np.ndarray) -> np.ndarray:
    """TOP2A - EPAS1 (first column minus second column)."""
    return X[:, 0] - X[:, 1]


def _zscore(a: np.ndarray) -> np.ndarray:
    sd = a.std(axis=0, ddof=0)
    sd[sd == 0] = 1.0
    return (a - a.mean(axis=0)) / sd


def _parse_labels(col: pd.Series, disease_tokens: tuple[str, ...]) -> np.ndarray:
    toks = {t.lower() for t in disease_tokens}
    return col.astype(str).str.strip().str.lower().isin(toks).astype(int).values


def _run_cohort(
    cohort_id: str,
    csv_path: Path,
    disease_tokens: tuple[str, ...],
    task_label: str,
    have_m_stage: bool,
    m_stage_col: str | None = None,
    log_transform: bool = False,
) -> dict:
    if not csv_path.exists():
        return {
            "cohort_id": cohort_id,
            "status": "csv_missing",
            "csv_path": str(csv_path),
            "task_label": task_label,
            "message": f"{csv_path} does not exist — run the build script first.",
        }
    df = pd.read_csv(csv_path)
    if len(df) == 0:
        return {
            "cohort_id": cohort_id,
            "status": "csv_empty",
            "csv_path": str(csv_path),
            "task_label": task_label,
            "message": "CSV is a header-only stub (see NOTE file).",
        }
    missing = [g for g in ("TOP2A", "EPAS1") if g not in df.columns]
    if missing:
        return {
            "cohort_id": cohort_id,
            "status": "genes_missing",
            "missing": missing,
            "task_label": task_label,
        }

    # Decide task: metastasis if M-stage in CSV, else tumor-vs-normal
    if have_m_stage and m_stage_col and m_stage_col in df.columns and df[m_stage_col].notna().any():
        # Metastasis M1 vs M0
        mask = df[m_stage_col].isin(["M0", "M1"])
        sub = df[mask].copy()
        if len(sub) < 20 or sub[m_stage_col].nunique() < 2:
            return {
                "cohort_id": cohort_id,
                "status": "insufficient_m_stage",
                "task_label": "metastasis",
                "n_M0": int((sub[m_stage_col] == "M0").sum()),
                "n_M1": int((sub[m_stage_col] == "M1").sum()),
            }
        y = (sub[m_stage_col] == "M1").astype(int).values
        X_raw = sub[["TOP2A", "EPAS1"]].fillna(0).values.astype(float)
        if log_transform:
            X_raw = np.log1p(X_raw)
        X = _zscore(X_raw)
        result = run_falsification_suite(_law_fn, X, y, X_covariates=None, include_decoy=True)
        return {
            "cohort_id": cohort_id,
            "status": "ran_metastasis",
            "task_label": "metastasis_M1_vs_M0",
            "n": int(len(sub)),
            "n_M1": int(y.sum()),
            "metrics": result,
            "gate_verdict": "pass" if result["passes"] else "attenuated_or_fail",
            "honest_caveat": None if result["passes"] else (
                "5-test gate did not pass on this cohort; report as honest negative."
            ),
        }

    # Tumor-vs-normal sanity check
    y = _parse_labels(df["label"], disease_tokens)
    if y.sum() == 0 or y.sum() == len(y):
        return {
            "cohort_id": cohort_id,
            "status": "no_class_balance",
            "task_label": task_label,
        }
    X_raw = df[["TOP2A", "EPAS1"]].fillna(0).values.astype(float)
    if log_transform:
        X_raw = np.log1p(X_raw)
    X = _zscore(X_raw)
    result = run_falsification_suite(_law_fn, X, y, X_covariates=None, include_decoy=True)
    # law_auc directly; report a sign-invariant version too.
    auc = float(result["law_auc"])
    auc_si = max(auc, 1.0 - auc)
    return {
        "cohort_id": cohort_id,
        "status": "ran_tumor_vs_normal",
        "task_label": "tumor_vs_normal_SANITY",
        "n": int(len(df)),
        "n_disease": int(y.sum()),
        "metrics": result,
        "auc_sign_invariant": auc_si,
        "honest_caveat": (
            "This is NOT a metastasis replay — the cohort lacks M-stage. "
            "The AUROC here reflects how well TOP2A-EPAS1 separates tumor from "
            "normal, which is expected to be high given the proliferation gradient "
            "and the HIF-2α program both differ across tumor/normal. Interpret as "
            "a sanity check, not as evidence for the metastasis claim."
        ),
    }


def main() -> None:
    cohorts = [
        dict(
            cohort_id="gse53757",
            csv_path=REPO / "data" / "gse53757_ccrcc.csv",
            disease_tokens=("disease",),
            task_label="tumor_vs_normal",
            have_m_stage=False,
            log_transform=True,  # raw Affymetrix intensities, apply log1p
        ),
        dict(
            cohort_id="gse40435_expanded",
            csv_path=REPO / "data" / "gse40435_expanded.csv",
            disease_tokens=("disease",),
            task_label="tumor_vs_normal",
            have_m_stage=False,
            log_transform=False,  # Illumina series matrix already in log2 space
        ),
        dict(
            cohort_id="cptac3_ccrcc",
            csv_path=REPO / "data" / "cptac3_ccrcc.csv",
            disease_tokens=("m1", "disease"),
            task_label="metastasis_preferred",
            have_m_stage=True,
            m_stage_col="m_stage",
            log_transform=False,
        ),
    ]

    per_cohort = []
    for c in cohorts:
        print(f"\n=== {c['cohort_id']} ===", flush=True)
        rec = _run_cohort(**c)
        per_cohort.append(rec)
        metrics = rec.get("metrics")
        status = rec.get("status")
        if metrics:
            print(
                f"  status={status} task={rec.get('task_label')} "
                f"law_auc={metrics['law_auc']:.3f} perm_p={metrics['perm_p']:.3f} "
                f"ci_lower={metrics['ci_lower']:.3f} delta_base={metrics['delta_baseline']:+.3f} "
                f"passes={metrics['passes']}",
                flush=True,
            )
        else:
            print(f"  status={status}", flush=True)

    (OUT_DIR / "per_cohort.json").write_text(json.dumps(per_cohort, default=str, indent=2))

    # Compose SUMMARY.md
    lines = []
    lines.append("# E3 — Independent-cohort replay for TOP2A − EPAS1")
    lines.append("")
    lines.append("Three ccRCC cohorts evaluated in priority order. The plan:")
    lines.append("first cohort with `TOP2A + EPAS1 + M-status` wins the metastasis")
    lines.append("replay. If none supply M-stage, tumor-vs-normal AUROC is reported")
    lines.append("as a sanity check and flagged as *not* a metastasis replay.")
    lines.append("")
    lines.append("Flagship internal replay remains 5-fold stratified CV on TCGA-KIRC")
    lines.append("(AUROC 0.722 ± 0.078; permutation null 0.509).")
    lines.append("")
    lines.append("## Per-cohort table")
    lines.append("")
    header = (
        "| Cohort | Platform | N | Task | TOP2A+EPAS1 present | M-stage | law_AUROC "
        "| perm_p | ci_lower | Δbase | Gate verdict | Honest caveat |"
    )
    sep = (
        "|---|---|---|---|---|---|---|---|---|---|---|---|"
    )
    lines.append(header)
    lines.append(sep)
    platforms = {
        "gse53757": "Affymetrix HG-U133 Plus 2.0 (GPL570)",
        "gse40435_expanded": "Illumina HumanHT-12 v4 (GPL10558)",
        "cptac3_ccrcc": "CPTAC-3 proteogenomic (PDC)",
    }
    for rec in per_cohort:
        cid = rec.get("cohort_id", "?")
        plat = platforms.get(cid, "?")
        n = rec.get("n", "—")
        task = rec.get("task_label", "—")
        status = rec.get("status", "?")
        has_genes = "yes" if status in ("ran_metastasis", "ran_tumor_vs_normal") else (
            "stub" if status in ("csv_empty",) else "?"
        )
        has_m = "yes" if "ran_metastasis" in status else ("no" if "ran_tumor" in status else "—")
        metrics = rec.get("metrics") or {}
        auc = f"{metrics['law_auc']:.3f}" if metrics else "—"
        perm_p = f"{metrics['perm_p']:.3f}" if metrics else "—"
        ci_l = f"{metrics['ci_lower']:.3f}" if metrics else "—"
        delta = f"{metrics['delta_baseline']:+.3f}" if metrics else "—"
        verdict = rec.get("gate_verdict", "—") or "—"
        if not metrics and status in ("csv_empty", "csv_missing"):
            verdict = "stub (see NOTE)"
        caveat = rec.get("honest_caveat") or ""
        lines.append(
            f"| {cid} | {plat} | {n} | {task} | {has_genes} | {has_m} | {auc} | "
            f"{perm_p} | {ci_l} | {delta} | {verdict} | {caveat[:80]}{'…' if len(caveat) > 80 else ''} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    # Decide headline outcome
    metastasis_pass = any(r.get("gate_verdict") == "pass" for r in per_cohort if r.get("status") == "ran_metastasis")
    tn_records = [r for r in per_cohort if r.get("status") == "ran_tumor_vs_normal"]
    if metastasis_pass:
        lines.append("A cohort with M-stage metadata replicated the metastasis gate —")
        lines.append("TOP2A − EPAS1 passes the 5-test gate on an independent platform.")
    elif tn_records:
        tn_aucs = [float(r["metrics"]["law_auc"]) for r in tn_records]
        tn_ids = [r["cohort_id"] for r in tn_records]
        lines.append(
            "No M-stage cohort was available in this session. The tumor-vs-normal "
            "sanity checks (flagged *not* as metastasis replay) gave law_AUROC "
            f"values of {', '.join(f'{a:.3f}' for a in tn_aucs)} on cohorts "
            f"{', '.join(tn_ids)}."
        )
        lines.append("")
        lines.append(
            "These values test a different thing than the survivor claim: they "
            "ask whether a proliferation-over-HIF-2α score separates tumor from "
            "normal (expected to be high on any ccRCC cohort). They do NOT test "
            "whether the same score separates M1 from M0 patients, which is "
            "what the survivor narrative claims."
        )
    else:
        lines.append("No cohort ran end-to-end. See per-cohort details above.")
    lines.append("")
    lines.append(
        "**Flagship internal replay** (TCGA-KIRC 5-fold CV, AUROC 0.722 ± 0.078) "
        "remains the strongest within-cohort replay evidence. The three external "
        "cohorts map the infrastructure of an independent-cohort metastasis replay "
        "and identify CPTAC-3 as the natural next step once a PDC-API token is available."
    )
    lines.append("")
    lines.append("## Files")
    lines.append("")
    lines.append("- `data/build_gse53757.py` — builder for Affymetrix GSE53757 (72T + 72N).")
    lines.append("- `data/build_gse40435_expanded.py` — Illumina GSE40435 with the 44-gene")
    lines.append("  panel (the existing 8-gene `gse40435_kirc.csv` omits TOP2A/EPAS1).")
    lines.append("- `data/build_cptac3_ccrcc.py` — PDC GraphQL probe; falls back to a")
    lines.append("  header-only stub + `cptac3_ccrcc_NOTE.md` manual-retrieval notes when")
    lines.append("  the public endpoint is unreachable from the current environment.")
    lines.append("- `per_cohort.json` — machine-readable per-cohort metric bundle.")
    (OUT_DIR / "SUMMARY.md").write_text("\n".join(lines) + "\n")
    print(f"\n[replay] wrote {OUT_DIR / 'SUMMARY.md'}", flush=True)


if __name__ == "__main__":
    main()
