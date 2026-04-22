"""Build data/gse40435_expanded.csv — GSE40435 with the 44-gene expanded panel
(including TOP2A and EPAS1) used by the metastasis_expanded survivor run.

Context: the existing `data/gse40435_kirc.csv` was built from GSE40435 with
only the 8 HIF-axis genes + 3 housekeeping. To replay TOP2A - EPAS1 on this
cohort the wider panel must be re-extracted.

Input (gitignored):
  .tmp_geo/GSE40435_series_matrix.txt.gz  (Illumina HumanHT-12 v4, GPL10558)
  .tmp_geo/GPL10558_annot.txt.gz          (probe -> gene annotation)

Output:
  data/gse40435_expanded.csv
    columns: sample_id, label (disease|control), age, batch_index, patient_id,
             grade, tissue_type, <44 gene expression columns>

Metastasis note: GSE40435 has tumor grade (I-IV) but no patient-level
M-stage, so this cohort only supports a tumor-vs-normal replay for
TOP2A - EPAS1 (plus a secondary high-grade vs low-grade analysis).

Public data (GEO), MIT-safe. No institutional identifiers.
"""
from __future__ import annotations

import gzip
import io
import re
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MATRIX_GZ = REPO / ".tmp_geo" / "GSE40435_series_matrix.txt.gz"
ANNOT_GZ = REPO / ".tmp_geo" / "GPL10558_annot.txt.gz"
MATRIX_URL = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE40nnn/GSE40435/matrix/GSE40435_series_matrix.txt.gz"
ANNOT_URL = "https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPL10nnn/GPL10558/annot/GPL10558.annot.gz"
OUT_CSV = REPO / "data" / "gse40435_expanded.csv"

WANTED_GENES: list[str] = [
    "ACTB", "AGXT", "ALB", "ALDOA", "ANGPTL4", "BHLHE40", "CA12", "CA9",
    "CALB1", "CCNB1", "CDK1", "COL4A2", "CUBN", "CXCR4", "DDIT4", "ENO1",
    "ENO2", "EPAS1", "GAPDH", "HK2", "KRT7", "LDHA", "LDHB", "LRP2",
    "MCM2", "MKI67", "MMP9", "NDUFA4L2", "PAX2", "PAX8", "PCNA", "PFKP",
    "PGK1", "PKM", "PTGER3", "RPL13A", "S100A4", "SLC12A1", "SLC12A3",
    "SLC22A8", "SLC2A1", "SPP1", "TOP2A", "VEGFA",
]


def _ensure(path: Path, url: str) -> Path:
    if path.exists() and path.stat().st_size > 1_000_000:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[build_gse40435_expanded] downloading {url}")
    urllib.request.urlretrieve(url, path)
    return path


def _probe_map() -> dict[str, str]:
    """Return gene_symbol -> ILMN_* probe (first-encountered probe per gene)."""
    annot = _ensure(ANNOT_GZ, ANNOT_URL)
    result: dict[str, str] = {}
    with gzip.open(annot, "rt") as f:
        for line in f:
            parts = line.split("\t")
            if len(parts) > 3 and parts[0].startswith("ILMN_"):
                gene = parts[2].strip()
                if gene in WANTED_GENES and gene not in result:
                    result[gene] = parts[0]
    return result


def _parse_matrix(matrix: Path, wanted_probes: set[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows_meta: dict[str, list[str]] = {}
    sample_ids: list[str] = []
    expr_lines: list[str] = []
    expr_header = None
    in_expr = False

    with gzip.open(matrix, "rt") as f:
        for line in f:
            if line.startswith("!series_matrix_table_begin"):
                in_expr = True
                continue
            if line.startswith("!series_matrix_table_end"):
                break
            if not in_expr:
                if line.startswith("!Sample_geo_accession"):
                    sample_ids = [p.strip('"') for p in line.rstrip().split("\t")[1:]]
                elif line.startswith("!Sample_source_name_ch1"):
                    rows_meta["source"] = [p.strip('"') for p in line.rstrip().split("\t")[1:]]
                elif line.startswith("!Sample_characteristics_ch1"):
                    parts = [p.strip('"') for p in line.rstrip().split("\t")[1:]]
                    existing = rows_meta.setdefault("characteristics", [""] * len(parts))
                    for i, v in enumerate(parts):
                        if v:
                            existing[i] = (existing[i] + " | " + v).strip(" |")
                elif line.startswith("!Sample_title"):
                    rows_meta["title"] = [p.strip('"') for p in line.rstrip().split("\t")[1:]]
            else:
                if line.startswith('"ID_REF"'):
                    expr_header = line.rstrip()
                    continue
                head = line.split("\t", 1)[0].strip('"')
                if head in wanted_probes:
                    expr_lines.append(line.rstrip())

    if expr_header is None:
        raise RuntimeError("no expression header found")
    if not expr_lines:
        raise RuntimeError("no target probes found")

    expr = pd.read_csv(
        io.StringIO("\n".join([expr_header] + expr_lines)),
        sep="\t",
        index_col=0,
    )
    expr.columns = [c.strip('"') for c in expr.columns]

    meta = pd.DataFrame({
        "sample_id": sample_ids,
        "title": rows_meta.get("title", [""] * len(sample_ids)),
        "source": rows_meta.get("source", [""] * len(sample_ids)),
        "characteristics": rows_meta.get("characteristics", [""] * len(sample_ids)),
    })
    return meta, expr


def _derive(meta: pd.DataFrame) -> pd.DataFrame:
    labels: list[str] = []
    grades: list[str] = []
    tissues: list[str] = []
    ages: list[float] = []
    patients: list[str] = []
    for _, row in meta.iterrows():
        src = (row["source"] or "").lower()
        chars = (row["characteristics"] or "").lower()
        if "non-tumour" in src or "normal" in src or "non-tumour" in chars:
            labels.append("control")
        elif "ccrcc" in src or "ccrcc" in chars or "tumour" in src:
            labels.append("disease")
        else:
            labels.append("unknown")
        m_grade = re.search(r"grade[: ]+([ivx1234]+)", chars)
        grades.append(m_grade.group(1).upper() if m_grade else "")
        m_tissue = re.search(r"tissue type[: ]+([^|]+)", chars)
        tissues.append(m_tissue.group(1).strip() if m_tissue else "")
        m_age = re.search(r"age[: ]+(\d+)", chars)
        ages.append(float(m_age.group(1)) if m_age else np.nan)
        m_patient = re.search(r"(\d+)", row["title"] or "")
        patients.append(m_patient.group(1) if m_patient else "")
    meta = meta.copy()
    meta["label"] = labels
    meta["grade"] = grades
    meta["tissue_type"] = tissues
    meta["age"] = ages
    meta["batch_index"] = 0
    meta["patient_id"] = patients
    return meta


def build(out_path: Path = OUT_CSV) -> Path:
    matrix = _ensure(MATRIX_GZ, MATRIX_URL)
    probe_map = _probe_map()
    wanted_probes = set(probe_map.values())
    meta, expr = _parse_matrix(matrix, wanted_probes)
    meta = _derive(meta)

    # Reverse map ILMN probe -> gene symbol, pull expression per gene
    rev = {v: k for k, v in probe_map.items()}
    gene_df = expr.rename(index=rev).T  # samples x genes
    gene_df = gene_df[[g for g in WANTED_GENES if g in gene_df.columns]]

    gene_df = gene_df.reindex(meta["sample_id"].values)
    out = pd.concat(
        [
            meta[["sample_id", "label", "age", "batch_index", "patient_id", "grade", "tissue_type"]].reset_index(drop=True),
            gene_df.reset_index(drop=True),
        ],
        axis=1,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    print(
        f"[build_gse40435_expanded] wrote {out_path}: n={len(out)}, "
        f"labels={out['label'].value_counts().to_dict()}, "
        f"grades={out['grade'].value_counts().to_dict()}, "
        f"genes resolved: {sorted(set(gene_df.columns))}"
    )
    return out_path


if __name__ == "__main__":
    build()
