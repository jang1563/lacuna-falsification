"""Build data/brca_tumor_normal.csv from the real TCGA-BRCA star_tpm matrix.

E13 pan-cancer stretch: exercise the DatasetCard + falsification pipeline
on a second cancer beyond KIRC and LUAD, so the "platform generalizes"
claim has three-disease coverage.

Input (gitignored):  .tmp_geo/gdc/TCGA-BRCA.star_tpm.tsv.gz  (~340 MB,
  auto-downloaded from the GDC-Xena hub S3 mirror if missing).
Output: data/brca_tumor_normal.csv

Label is derived from the TCGA sample barcode (same convention as KIRC/LUAD):
  TCGA-AA-BBBB-01X-... -> '01'/'06'  Primary Tumor / Metastatic -> label=disease
  TCGA-AA-BBBB-11X-... -> '11'       Solid Tissue Normal        -> label=control

Gene panel: BRCA-anchored (32 genes) covering:
  - Proliferation (TOP2A, MKI67, CDK1, CCNB1, PCNA, MCM2)
  - HR (ER/PR) luminal axis (ESR1, PGR, FOXA1, GATA3, XBP1)
  - HER2 / ERBB axis (ERBB2, ERBB3)
  - Basal / triple-negative markers (KRT5, KRT14, KRT17, FOXC1, SOX10)
  - Epithelial lineage (EPCAM, CDH1)
  - Housekeeping controls (ACTB, GAPDH, RPL13A)
  - ccRCC-common genes for cross-cancer interpretability (EPAS1, VEGFA)
  - Warburg / metabolism (LDHA, ALDOA, HK2)
  - EMT (VIM, SNAI2, CXCR4)
"""
from __future__ import annotations

import gzip
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
XENA_URL = "https://gdc-hub.s3.us-east-1.amazonaws.com/download/TCGA-BRCA.star_tpm.tsv.gz"
LOCAL_TSV = REPO / ".tmp_geo" / "gdc" / "TCGA-BRCA.star_tpm.tsv.gz"
OUT_CSV = REPO / "data" / "brca_tumor_normal.csv"

# BRCA-anchored 32-gene panel (Ensembl versionless IDs).
TARGET_GENES: dict[str, str] = {
    # Proliferation
    "TOP2A":  "ENSG00000131747",
    "MKI67":  "ENSG00000148773",
    "CDK1":   "ENSG00000170312",
    "CCNB1":  "ENSG00000134057",
    "PCNA":   "ENSG00000132646",
    "MCM2":   "ENSG00000073111",
    # HR / luminal axis
    "ESR1":   "ENSG00000091831",
    "PGR":    "ENSG00000082175",
    "FOXA1":  "ENSG00000129514",
    "GATA3":  "ENSG00000107485",
    "XBP1":   "ENSG00000100219",
    # HER2 family
    "ERBB2":  "ENSG00000141736",
    "ERBB3":  "ENSG00000065361",
    # Basal / TNBC markers
    "KRT5":   "ENSG00000186081",
    "KRT14":  "ENSG00000186847",
    "KRT17":  "ENSG00000128422",
    "FOXC1":  "ENSG00000054598",
    "SOX10":  "ENSG00000100146",
    # Epithelial
    "EPCAM":  "ENSG00000119888",
    "CDH1":   "ENSG00000039068",
    # Housekeeping
    "ACTB":   "ENSG00000075624",
    "GAPDH":  "ENSG00000111640",
    "RPL13A": "ENSG00000142541",
    # Hypoxia (shared with KIRC panel)
    "EPAS1":  "ENSG00000116016",
    "VEGFA":  "ENSG00000112715",
    # Warburg / metabolism
    "LDHA":   "ENSG00000134333",
    "ALDOA":  "ENSG00000149925",
    "HK2":    "ENSG00000159399",
    # EMT
    "VIM":    "ENSG00000026025",
    "SNAI2":  "ENSG00000019549",
    "CXCR4":  "ENSG00000121966",
}


def _sample_type(barcode: str) -> str | None:
    parts = barcode.split("-")
    if len(parts) < 4:
        return None
    code = parts[3][:2]
    if code in ("01", "06"):
        return "disease"
    if code == "11":
        return "control"
    return None


def _patient_id(barcode: str) -> str | None:
    parts = barcode.split("-")
    return "-".join(parts[:3]) if len(parts) >= 3 else None


def _download_if_needed() -> Path:
    if LOCAL_TSV.exists() and LOCAL_TSV.stat().st_size > 100_000_000:
        return LOCAL_TSV
    LOCAL_TSV.parent.mkdir(parents=True, exist_ok=True)
    print(f"[build_tcga_brca] downloading {XENA_URL} (~340 MB)...")
    urllib.request.urlretrieve(XENA_URL, LOCAL_TSV)
    return LOCAL_TSV


def build(src: Path = LOCAL_TSV, out: Path = OUT_CSV) -> pd.DataFrame:
    src = _download_if_needed()
    targets = {v: k for k, v in TARGET_GENES.items()}
    data_rows: list[tuple[str, np.ndarray]] = []
    with gzip.open(src, "rt") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            cols = line.rstrip("\n").split("\t")
            ensg = cols[0].split(".")[0]
            if ensg in targets:
                gene = targets[ensg]
                values = np.array(
                    [float(x) if x not in ("", "NA") else np.nan for x in cols[1:]],
                    dtype=float,
                )
                data_rows.append((gene, values))
                if len(data_rows) == len(TARGET_GENES):
                    break

    if not data_rows:
        raise RuntimeError("no target genes matched in TCGA-BRCA matrix")

    barcodes = header[1:]
    gene_names = [g for g, _ in data_rows]
    mat = np.vstack([v for _, v in data_rows])
    df = pd.DataFrame(mat.T, index=barcodes, columns=gene_names)

    df["label"] = [_sample_type(b) for b in df.index]
    df["patient_id"] = [_patient_id(b) for b in df.index]
    df = df.dropna(subset=["label"]).copy()
    df.index.name = "sample_id"
    df = df.reset_index()

    batch = df["sample_id"].str.extract(r"-(\w{2})$", expand=False)
    df["batch_index"] = batch.fillna("0")
    df["age"] = np.nan

    ordered = ["sample_id", "label", "age", "batch_index", "patient_id"] + gene_names
    df = df[ordered]
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return df


if __name__ == "__main__":
    df = build()
    print(f"[build_tcga_brca] wrote {OUT_CSV}: {df.shape[0]} samples x {df.shape[1]} cols")
    print(f"  labels = {df['label'].value_counts().to_dict()}")
    print(f"  unique patients = {df['patient_id'].nunique()}")
    paired = df.groupby("patient_id")["label"].nunique().eq(2).sum()
    print(f"  paired tumor+normal patients = {paired}")
    print(f"  genes recovered: {sorted([g for g in TARGET_GENES if g in df.columns])}")
