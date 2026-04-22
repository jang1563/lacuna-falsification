"""Build data/kirc_metastasis.csv for the M0 vs M1 task.

Merges the expression-level kirc_tumor_normal.csv (tumor samples only) with
TCGA-KIRC AJCC pathologic M staging. The binary target is:

  label = disease -> M1 (distant metastasis present)
  label = control -> M0 (no distant metastasis)
  excluded       -> MX (not assessable) or missing

Known published ccRCC metastasis signatures (7-gene collagen panel,
sarcomatoid-transition score) beat best single-gene AUROC in the 0.60-0.75
range, so this task is a plausible survivor candidate for the 5-test
falsification gate.

Source: TCGA-KIRC clinical TSV on the GDC-Xena hub.
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
OUT_CSV = Path("data/kirc_metastasis.csv")

SAMPLE_COLUMN = "sample"
M_COLUMN = "ajcc_pathologic_m.diagnoses"


def _download_phenotype() -> Path:
    PHENO_LOCAL.parent.mkdir(parents=True, exist_ok=True)
    if PHENO_LOCAL.exists() and PHENO_LOCAL.stat().st_size > 1_000_000:
        return PHENO_LOCAL
    print(f"Downloading {PHENO_URL} -> {PHENO_LOCAL}")
    urllib.request.urlretrieve(PHENO_URL, PHENO_LOCAL)
    return PHENO_LOCAL


def main() -> None:
    pheno_path = _download_phenotype()
    pheno = pd.read_csv(pheno_path, sep="\t", low_memory=False)
    print(f"Phenotype table: {pheno.shape}")

    if SAMPLE_COLUMN not in pheno.columns or M_COLUMN not in pheno.columns:
        raise RuntimeError(
            f"Required columns missing. Need {SAMPLE_COLUMN!r} and {M_COLUMN!r}."
        )

    pheno = pheno[[SAMPLE_COLUMN, M_COLUMN]].dropna()
    pheno.columns = ["sample_id", "m_stage"]
    pheno["label"] = pheno["m_stage"].map(
        lambda v: "disease" if v == "M1" else ("control" if v == "M0" else None)
    )
    pheno = pheno.dropna(subset=["label"])
    print(f"Samples with usable M stage: {pheno.shape[0]}")
    print(f"M distribution: {pheno['m_stage'].value_counts().to_dict()}")

    expr = pd.read_csv(EXPRESSION_CSV)
    expr_tumor = expr[expr["label"] == "disease"].copy()
    expr_tumor = expr_tumor.drop(columns=["label"])

    merged = expr_tumor.merge(
        pheno[["sample_id", "m_stage", "label"]], on="sample_id", how="inner"
    )

    gene_cols = [
        c for c in expr_tumor.columns
        if c not in {"sample_id", "age", "batch_index", "patient_id"}
    ]
    ordered = (
        ["sample_id", "label", "m_stage", "age", "batch_index", "patient_id"]
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
