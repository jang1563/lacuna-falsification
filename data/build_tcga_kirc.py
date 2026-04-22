"""Build data/kirc_tumor_normal.csv from the real TCGA-KIRC star_tpm matrix.

Input:  .tmp_geo/gdc/TCGA-KIRC.star_tpm.tsv.gz   (from GDC-Xena hub S3)
Output: data/kirc_tumor_normal.csv

Label is derived from the TCGA sample barcode:
  TCGA-AA-BBBB-01X-... → '01'/'02'/'06' → Primary Tumor   → label=disease
  TCGA-AA-BBBB-11X-... → '11'            → Solid Tissue Normal → label=control
Other types (metastatic, cell line, etc.) are dropped.
"""

from __future__ import annotations

import gzip
import re
from pathlib import Path

import numpy as np
import pandas as pd


TARGET_GENES: dict[str, str] = {
    # Tumor-up (VHL/HIF axis + Warburg metabolism)
    "CA9":      "ENSG00000107159",
    "VEGFA":    "ENSG00000112715",
    "LDHA":     "ENSG00000134333",
    "NDUFA4L2": "ENSG00000185633",
    "SLC2A1":   "ENSG00000117394",
    "ENO2":     "ENSG00000111674",
    # Normal-kidney denominators
    "AGXT":     "ENSG00000172482",
    "ALB":      "ENSG00000163631",
    "CUBN":     "ENSG00000107611",
    "PTGER3":   "ENSG00000050628",
    "SLC12A3":  "ENSG00000070031",
}

# Additional genes referenced by law_proposals.json negative/positive controls.
EXTRA_GENES: dict[str, str] = {
    "ACTB":    "ENSG00000075624",
    "GAPDH":   "ENSG00000111640",
    "RPL13A":  "ENSG00000142541",
    "MKI67":   "ENSG00000148773",
}

TUMOR_CODES = {"01", "02", "06"}
NORMAL_CODES = {"11"}

BARCODE_RE = re.compile(r"^TCGA-[A-Z0-9]{2}-[A-Z0-9]{4}-(\d{2})[A-Z]?")


def _sample_type(barcode: str) -> str | None:
    m = BARCODE_RE.match(barcode)
    if not m:
        return None
    code = m.group(1)
    if code in TUMOR_CODES:
        return "disease"
    if code in NORMAL_CODES:
        return "control"
    return None


def _patient_id(barcode: str) -> str | None:
    parts = barcode.split("-")
    if len(parts) >= 3:
        return "-".join(parts[:3])
    return None


def build(
    src: Path,
    out: Path,
    genes: dict[str, str],
) -> pd.DataFrame:
    targets_versionless = {v: k for k, v in genes.items()}

    header_line: list[str]
    data_rows: list[tuple[str, np.ndarray]] = []

    opener = gzip.open if src.suffix == ".gz" else open
    with opener(src, "rt") as f:
        header = f.readline().rstrip("\n").split("\t")
        # First column is Ensembl_ID; rest are TCGA barcodes.
        for line in f:
            cols = line.rstrip("\n").split("\t")
            ensg = cols[0].split(".")[0]
            if ensg in targets_versionless:
                gene = targets_versionless[ensg]
                # Convert values to float; empty strings → NaN.
                values = np.array(
                    [float(x) if x not in ("", "NA") else np.nan for x in cols[1:]],
                    dtype=float,
                )
                data_rows.append((gene, values))
                if len(data_rows) == len(genes):
                    break

    if not data_rows:
        raise RuntimeError("No target genes matched in input file.")

    barcodes = header[1:]
    gene_names = [g for g, _ in data_rows]
    mat = np.vstack([vals for _, vals in data_rows])  # genes × samples
    df = pd.DataFrame(mat.T, index=barcodes, columns=gene_names)

    # Attach label + patient + sample type from barcode.
    df["label"] = [_sample_type(b) for b in df.index]
    df["patient_id"] = [_patient_id(b) for b in df.index]

    df = df.dropna(subset=["label"]).copy()
    df.index.name = "sample_id"
    df = df.reset_index()

    # Order columns: id, label, covariates, genes.
    # TCGA barcode encodes the collection center ("batch") in positions 26-28.
    batch = df["sample_id"].str.extract(r"-(\w{2})$", expand=False)
    df["batch_index"] = batch.fillna("0")
    df["age"] = np.nan  # age not carried in star_tpm; leave NaN (gate tolerates)

    ordered = ["sample_id", "label", "age", "batch_index", "patient_id"] + list(genes.keys())
    df = df[ordered]

    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return df


if __name__ == "__main__":
    src = Path(".tmp_geo/gdc/TCGA-KIRC.star_tpm.tsv.gz")
    out = Path("data/kirc_tumor_normal.csv")

    all_genes = {**TARGET_GENES, **EXTRA_GENES}
    df = build(src, out, all_genes)

    print(f"Wrote {out}: {df.shape[0]} samples × {df.shape[1]} cols")
    print(f"Label counts: {df['label'].value_counts().to_dict()}")
    print(f"Unique patients: {df['patient_id'].nunique()}")
    paired = (
        df.groupby("patient_id")["label"].nunique().eq(2).sum()
    )
    print(f"Paired tumor+normal patients: {paired}")
    print(f"Genes recovered: {[g for g in all_genes if g in df.columns]}")
