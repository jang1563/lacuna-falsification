"""Build data/kirc_survival.csv for the 5-year overall-survival task.

Merges the expression-level kirc_tumor_normal.csv (tumor samples only) with
TCGA-KIRC vital-status + time-to-event fields. The binary target is:

  label = disease -> dead at or before day 1825 (5 years from diagnosis)
  label = control -> alive with days_to_last_follow_up >= 1825
  excluded       -> alive with follow-up < 1825 (right-censored before 5yr)

This is an intra-tumor *prognostic* task: every sample is a ccRCC tumor and
the question is whether a compact multi-gene law separates the sub-5-year-
fatal cohort from the long-term survivors. Published ccRCC survival
signatures (ClearCode34, 11-gene proliferation panels, m6A risk score) beat
best single-gene AUROC by +0.08 to +0.15, so this task has real headroom for
the 5-test falsification gate to find a survivor.

Source: TCGA-KIRC clinical TSV on the GDC-Xena hub (no login, open access).
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

import pandas as pd


PHENO_URL = (
    "https://gdc-hub.s3.us-east-1.amazonaws.com/download/"
    "TCGA-KIRC.clinical.tsv.gz"
)
PHENO_LOCAL = Path(".tmp_geo/gdc/TCGA-KIRC.clinical.tsv.gz")

EXPRESSION_CSV = Path("data/kirc_tumor_normal.csv")
OUT_CSV = Path("data/kirc_survival.csv")

SAMPLE_COLUMN = "sample"  # full TCGA barcode, e.g. "TCGA-B0-5695-01A"
VITAL_COLUMN = "vital_status.demographic"
DAYS_TO_DEATH_COLUMN = "days_to_death.demographic"
DAYS_TO_FU_COLUMN = "days_to_last_follow_up.diagnoses"

FIVE_YEARS_DAYS = 5 * 365


def _download_phenotype() -> Path:
    PHENO_LOCAL.parent.mkdir(parents=True, exist_ok=True)
    if PHENO_LOCAL.exists() and PHENO_LOCAL.stat().st_size > 1_000_000:
        return PHENO_LOCAL
    print(f"Downloading {PHENO_URL} -> {PHENO_LOCAL}")
    urllib.request.urlretrieve(PHENO_URL, PHENO_LOCAL)
    return PHENO_LOCAL


def _label_row(row: pd.Series) -> str | None:
    vital = row.get(VITAL_COLUMN)
    d_death = row.get(DAYS_TO_DEATH_COLUMN)
    d_fu = row.get(DAYS_TO_FU_COLUMN)
    if vital == "Dead":
        if pd.notna(d_death) and float(d_death) <= FIVE_YEARS_DAYS:
            return "disease"  # sub-5yr mortality
        # Died AFTER 5 years -> long-term survivor for our purposes.
        if pd.notna(d_death) and float(d_death) > FIVE_YEARS_DAYS:
            return "control"
        return None
    if vital == "Alive":
        if pd.notna(d_fu) and float(d_fu) >= FIVE_YEARS_DAYS:
            return "control"
        return None  # right-censored before 5yr — cannot be labelled
    return None


def main() -> None:
    pheno_path = _download_phenotype()
    pheno = pd.read_csv(pheno_path, sep="\t", low_memory=False)
    print(f"Phenotype table: {pheno.shape}")

    required = {SAMPLE_COLUMN, VITAL_COLUMN, DAYS_TO_DEATH_COLUMN, DAYS_TO_FU_COLUMN}
    missing = required - set(pheno.columns)
    if missing:
        raise RuntimeError(f"Phenotype columns missing: {missing}")

    pheno["label"] = pheno.apply(_label_row, axis=1)
    labeled = pheno.dropna(subset=["label"]).copy()
    labeled = labeled[[SAMPLE_COLUMN, VITAL_COLUMN, DAYS_TO_DEATH_COLUMN,
                       DAYS_TO_FU_COLUMN, "label"]]
    labeled.columns = ["sample_id", "vital_status", "days_to_death",
                       "days_to_last_fu", "label"]
    print(f"Labelable rows: {labeled.shape[0]}")
    print(f"Label distribution: {labeled['label'].value_counts().to_dict()}")

    expr = pd.read_csv(EXPRESSION_CSV)
    expr_tumor = expr[expr["label"] == "disease"].copy()
    expr_tumor = expr_tumor.drop(columns=["label"])

    merged = expr_tumor.merge(
        labeled[["sample_id", "label", "vital_status", "days_to_death",
                 "days_to_last_fu"]],
        on="sample_id",
        how="inner",
    )

    gene_cols = [
        c for c in expr_tumor.columns
        if c not in {"sample_id", "age", "batch_index", "patient_id"}
    ]
    ordered = (
        ["sample_id", "label", "vital_status", "days_to_death",
         "days_to_last_fu", "age", "batch_index", "patient_id"]
        + gene_cols
    )
    ordered = [c for c in ordered if c in merged.columns]
    merged = merged[ordered]

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUT_CSV, index=False)
    print(f"\nWrote {OUT_CSV}: {merged.shape[0]} samples x {merged.shape[1]} cols")
    print(f"Final label counts: {merged['label'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
