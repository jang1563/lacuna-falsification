"""Build data/kirc_stage.csv for the Tier 2 prognostic task.

Merges the expression-level kirc_tumor_normal.csv (tumor samples only) with
TCGA-KIRC AJCC pathologic stage. The binary target is:

  label = disease  -> Stage III or IV (advanced disease)
  label = control  -> Stage I  or II  (localised disease)

This is an *intra-tumor* task: every sample is a ccRCC tumor and the question
is whether a compact gene law separates advanced-stage from localised-stage
biology. Unlike tumor-vs-normal, CA9 alone does NOT saturate this task, so the
5-test falsification gate has genuine headroom for multi-gene integration to
demonstrate incremental value.

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
OUT_CSV = Path("data/kirc_stage.csv")

STAGE_COLUMN = "ajcc_pathologic_stage.diagnoses"
SAMPLE_COLUMN = "sample"  # full TCGA barcode, e.g. "TCGA-B0-5695-01A"

LOW_STAGE = {"Stage I", "Stage II"}
HIGH_STAGE = {"Stage III", "Stage IV"}


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

    if STAGE_COLUMN not in pheno.columns or SAMPLE_COLUMN not in pheno.columns:
        raise RuntimeError(
            f"Expected columns missing. Need {STAGE_COLUMN!r} and {SAMPLE_COLUMN!r}. "
            f"Available sample/stage columns: "
            f"{[c for c in pheno.columns if 'sample' in c.lower() or 'stage' in c.lower()]}"
        )

    pheno = pheno[[SAMPLE_COLUMN, STAGE_COLUMN]].dropna()
    pheno.columns = ["sample_id", "stage"]
    pheno["label"] = pheno["stage"].map(
        lambda s: "disease" if s in HIGH_STAGE else ("control" if s in LOW_STAGE else None)
    )
    pheno = pheno.dropna(subset=["label"])
    print(f"Samples with usable stage: {pheno.shape[0]}")
    print(f"Stage distribution: {pheno['stage'].value_counts().to_dict()}")

    expr = pd.read_csv(EXPRESSION_CSV)
    expr_tumor = expr[expr["label"] == "disease"].copy()
    expr_tumor = expr_tumor.drop(columns=["label"])

    merged = expr_tumor.merge(
        pheno[["sample_id", "stage", "label"]], on="sample_id", how="inner"
    )

    # Order columns: id, label, stage, covariates, genes
    gene_cols = [
        c for c in expr_tumor.columns
        if c not in {"sample_id", "age", "batch_index", "patient_id"}
    ]
    ordered = (
        ["sample_id", "label", "stage", "age", "batch_index", "patient_id"] + gene_cols
    )
    ordered = [c for c in ordered if c in merged.columns]
    merged = merged[ordered]

    merged.to_csv(OUT_CSV, index=False)
    print(f"\nWrote {OUT_CSV}: {merged.shape[0]} samples x {merged.shape[1]} cols")
    print(f"Final label counts: {merged['label'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
