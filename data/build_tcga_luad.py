"""Build data/luad_tumor_normal.csv from the real TCGA-LUAD star_tpm matrix.

Input:  .tmp_geo/gdc/TCGA-LUAD.star_tpm.tsv.gz
        (download from https://gdc-hub.s3.us-east-1.amazonaws.com/download/
        TCGA-LUAD.star_tpm.tsv.gz — same GDC-Xena hub used for KIRC.)
Output: data/luad_tumor_normal.csv

Label from TCGA barcode position 14-15:
  01/02/06 → Primary Tumor / Metastatic / Recurrent → label=disease
  11       → Solid Tissue Normal                    → label=control

Panel (23 genes): lung identity + proliferation + hypoxia + oncogene.
Matches config/dataset_cards/luad_tumor_normal.json.
"""

from __future__ import annotations

import gzip
import re
from pathlib import Path

import numpy as np
import pandas as pd


# Gene symbol → Ensembl (versionless). IDs from GENCODE v36 (GDC uses v36).
TARGET_GENES: dict[str, str] = {
    # Lung identity / alveolar / airway
    "SFTPC":    "ENSG00000168484",
    "NAPSA":    "ENSG00000131400",
    "SFTPB":    "ENSG00000168878",
    "SFTPA1":   "ENSG00000122852",
    "SFTPA2":   "ENSG00000185303",
    "EPCAM":    "ENSG00000119888",
    "KRT7":     "ENSG00000135480",
    "KRT18":    "ENSG00000111057",
    "KRT19":    "ENSG00000171345",
    "NKX2-1":   "ENSG00000136352",   # a.k.a. TTF1
    # Proliferation
    "CDK1":     "ENSG00000170312",
    "CCNB1":    "ENSG00000134057",
    "TOP2A":    "ENSG00000131747",
    "MKI67":    "ENSG00000148773",
    "PCNA":     "ENSG00000132646",
    "MCM2":     "ENSG00000073111",
    # Hypoxia / glycolysis
    "SLC2A1":   "ENSG00000117394",
    "LDHA":     "ENSG00000134333",
    "HK2":      "ENSG00000159399",
    "VEGFA":    "ENSG00000112715",
    # LUAD driver oncogenes
    "EGFR":     "ENSG00000146648",
    "KRAS":     "ENSG00000133703",
}

# "TTF1" is the common alias for NKX2-1; provide a convenience column.
ALIAS_COLUMNS: dict[str, str] = {"TTF1": "NKX2-1"}

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


def build(src: Path, out: Path, genes: dict[str, str]) -> pd.DataFrame:
    targets_versionless = {v: k for k, v in genes.items()}

    data_rows: list[tuple[str, np.ndarray]] = []
    opener = gzip.open if src.suffix == ".gz" else open
    with opener(src, "rt") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            cols = line.rstrip("\n").split("\t")
            ensg = cols[0].split(".")[0]
            if ensg in targets_versionless:
                gene = targets_versionless[ensg]
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
    mat = np.vstack([vals for _, vals in data_rows])
    df = pd.DataFrame(mat.T, index=barcodes, columns=gene_names)

    df["label"] = [_sample_type(b) for b in df.index]
    df["patient_id"] = [_patient_id(b) for b in df.index]
    df = df.dropna(subset=["label"]).copy()
    df.index.name = "sample_id"
    df = df.reset_index()

    batch = df["sample_id"].str.extract(r"-(\w{2})$", expand=False)
    df["batch_index"] = batch.fillna("0")
    df["age"] = np.nan

    for alias, source in ALIAS_COLUMNS.items():
        if source in df.columns:
            df[alias] = df[source]

    ordered = (
        ["sample_id", "label", "age", "batch_index", "patient_id"]
        + list(genes.keys())
        + [a for a in ALIAS_COLUMNS if a not in genes]
    )
    df = df[[c for c in ordered if c in df.columns]]

    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return df


if __name__ == "__main__":
    src = Path(".tmp_geo/gdc/TCGA-LUAD.star_tpm.tsv.gz")
    out = Path("data/luad_tumor_normal.csv")
    df = build(src, out, TARGET_GENES)
    print(f"Wrote {out}: {df.shape[0]} samples x {df.shape[1]} cols")
    print(f"Label counts: {df['label'].value_counts().to_dict()}")
    print(f"Unique patients: {df['patient_id'].nunique()}")
    paired = df.groupby("patient_id")["label"].nunique().eq(2).sum()
    print(f"Paired tumor+normal patients: {paired}")
    print(f"Genes recovered: {[g for g in TARGET_GENES if g in df.columns]}")
