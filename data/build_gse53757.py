"""Build data/gse53757_ccrcc.csv from the GEO GSE53757 series matrix.

GSE53757 is an Affymetrix HG-U133 Plus 2.0 (GPL570) profiling of 143 samples
(72 ccRCC + 71 matched normal kidney) from Mayo Clinic. It provides
*stage* metadata (Stage 1-4) but NOT patient-level M-stage, so the best
available replay for TOP2A - EPAS1 on this cohort is tumor-vs-normal
and (as a secondary task) advanced-stage (III-IV vs I-II).

Input (gitignored): .tmp_geo/GSE53757_series_matrix.txt.gz (auto-downloaded
here if missing; ~31 MB).
Output: data/gse53757_ccrcc.csv  (rows = samples, columns = sample_id, label,
m_stage, tumor_stage, age, batch_index, patient_id, <gene expression...>).

Gene symbols are resolved from Affymetrix probes using a fixed probe->symbol
map (see _PROBE_MAP) covering the genes used by the metastasis_expanded panel.
If multiple probes map to one gene we pick the canonical one flagged in
comments below; no averaging (picks are hard-coded and reviewable).

Public data, MIT-safe. No institutional identifiers enter the CSV.
"""
from __future__ import annotations

import gzip
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
GEO_URL = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE53nnn/GSE53757/matrix/GSE53757_series_matrix.txt.gz"
LOCAL_GZ = REPO / ".tmp_geo" / "GSE53757_series_matrix.txt.gz"
OUT_CSV = REPO / "data" / "gse53757_ccrcc.csv"

# Affymetrix HG-U133 Plus 2.0 probe -> gene symbol mapping for genes in the
# metastasis_expanded panel. Canonical probes chosen by literature / Affymetrix
# design documentation. Missing genes (ALDOA, CCNB1, etc.) can be added later.
_PROBE_MAP: dict[str, str] = {
    # Proliferation / survivor partners
    "201291_s_at": "TOP2A",  # canonical TOP2A probe
    "201292_at":   "TOP2A_alt",
    "212020_s_at": "MKI67",
    "212022_s_at": "MKI67_alt",
    "203418_at":   "CCNA2",
    "214710_s_at": "CCNB1",
    "203213_at":   "CDK1",
    "201202_at":   "PCNA",
    # HIF axis / hypoxia
    "200878_at":   "EPAS1",
    "210512_s_at": "VEGFA",
    "205199_at":   "CA9",
    "201313_at":   "ENO2",
    "200801_x_at": "ACTB",
    "212581_x_at": "GAPDH",
    "200715_x_at": "RPL13A",
    "202910_s_at": "LDHA",
    # Tubule / differentiation
    "206075_s_at": "AGXT",
    "211298_s_at": "ALB",
    "207828_s_at": "CUBN",
    "208367_x_at": "PTGER3",
    "205509_at":   "SLC12A3",
    # Warburg / glycolysis
    "201250_s_at": "SLC2A1",
    "202022_at":   "ALDOA",
    "201250_at":   "SLC2A1_alt",
    "204348_s_at": "ANGPTL4",
    "219682_s_at": "BHLHE40",
    "202887_s_at": "DDIT4",
    "201231_s_at": "ENO1",
    "202934_at":   "HK2",
    "201250_at":   "SLC2A1_alt2",
    "201465_s_at": "JUN",
}

# Genes we emit into the CSV (after probe dedup). Preference order: canonical
# probe first, fall back to _alt if the canonical row is missing.
_PREFERENCE: dict[str, list[str]] = {
    "TOP2A":  ["201291_s_at", "201292_at"],
    "EPAS1":  ["200878_at"],
    "MKI67":  ["212020_s_at", "212022_s_at"],
    "CCNA2":  ["203418_at"],
    "CCNB1":  ["214710_s_at"],
    "CDK1":   ["203213_at"],
    "PCNA":   ["201202_at"],
    "VEGFA":  ["210512_s_at"],
    "CA9":    ["205199_at"],
    "ENO2":   ["201313_at"],
    "ACTB":   ["200801_x_at"],
    "GAPDH":  ["212581_x_at"],
    "RPL13A": ["200715_x_at"],
    "LDHA":   ["202910_s_at"],
    "AGXT":   ["206075_s_at"],
    "ALB":    ["211298_s_at"],
    "CUBN":   ["207828_s_at"],
    "PTGER3": ["208367_x_at"],
    "SLC12A3":["205509_at"],
    "SLC2A1": ["201250_s_at"],
    "ALDOA":  ["202022_at"],
    "ANGPTL4":["204348_s_at"],
    "BHLHE40":["219682_s_at"],
    "DDIT4":  ["202887_s_at"],
    "ENO1":   ["201231_s_at"],
    "HK2":    ["202934_at"],
}


def _download_if_needed() -> Path:
    if LOCAL_GZ.exists() and LOCAL_GZ.stat().st_size > 1_000_000:
        print(f"[build_gse53757] cached {LOCAL_GZ}")
        return LOCAL_GZ
    LOCAL_GZ.parent.mkdir(parents=True, exist_ok=True)
    print(f"[build_gse53757] downloading {GEO_URL}")
    urllib.request.urlretrieve(GEO_URL, LOCAL_GZ)
    return LOCAL_GZ


def _parse_series_matrix(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (sample_metadata_df, expression_df[probes_x_samples])."""
    rows_meta: dict[str, list[str]] = {}
    sample_ids: list[str] = []
    expr_lines: list[str] = []
    in_expr = False
    wanted_probes = set()
    for probes in _PREFERENCE.values():
        wanted_probes.update(probes)

    with gzip.open(path, "rt") as f:
        for line in f:
            if line.startswith("!series_matrix_table_begin"):
                in_expr = True
                continue
            if line.startswith("!series_matrix_table_end"):
                break
            if not in_expr:
                if line.startswith("!Sample_title"):
                    parts = [p.strip('"') for p in line.rstrip().split("\t")[1:]]
                    rows_meta["title"] = parts
                elif line.startswith("!Sample_geo_accession"):
                    sample_ids = [p.strip('"') for p in line.rstrip().split("\t")[1:]]
                elif line.startswith("!Sample_source_name_ch1"):
                    rows_meta["source"] = [p.strip('"') for p in line.rstrip().split("\t")[1:]]
                elif line.startswith("!Sample_characteristics_ch1"):
                    # Multiple _characteristics_ rows: accumulate per-sample joined
                    parts = [p.strip('"') for p in line.rstrip().split("\t")[1:]]
                    existing = rows_meta.setdefault("characteristics", [""] * len(parts))
                    for i, v in enumerate(parts):
                        if v:
                            existing[i] = (existing[i] + " | " + v).strip(" |")
            else:
                if line.startswith('"ID_REF"'):
                    expr_header = line.rstrip()
                    continue
                # Fast pre-filter: only keep rows whose probe is in wanted_probes
                head = line.split("\t", 1)[0].strip('"')
                if head in wanted_probes:
                    expr_lines.append(line.rstrip())

    meta = pd.DataFrame(
        {
            "sample_id": sample_ids,
            "title": rows_meta.get("title", [""] * len(sample_ids)),
            "source": rows_meta.get("source", [""] * len(sample_ids)),
            "characteristics": rows_meta.get("characteristics", [""] * len(sample_ids)),
        }
    )

    # Build expression dataframe (probes as rows, samples as cols)
    if not expr_lines:
        raise RuntimeError("no target probes found in series matrix")
    import io
    expr = pd.read_csv(
        io.StringIO("\n".join([expr_header] + expr_lines)),
        sep="\t",
        index_col=0,
    )
    # Rename columns (drop surrounding quotes)
    expr.columns = [c.strip('"') for c in expr.columns]
    return meta, expr


def _derive_labels(meta: pd.DataFrame) -> pd.DataFrame:
    """Add disease / control label + stage columns from characteristics."""
    labels = []
    stages = []
    m_stage = []  # not present in GSE53757
    for _, row in meta.iterrows():
        src = (row["source"] or "").lower()
        chars = (row["characteristics"] or "").lower()
        if "normal" in src or "normal" in chars:
            labels.append("control")
        elif "ccrcc" in src or "carcinoma" in chars:
            labels.append("disease")
        else:
            labels.append("unknown")
        # Stage
        stage = ""
        for tok in ("stage 4", "stage iv", "stage 3", "stage iii", "stage 2", "stage ii", "stage 1", "stage i"):
            if tok in chars:
                stage = tok
                break
        stages.append(stage)
        m_stage.append("")  # unavailable
    meta = meta.copy()
    meta["label"] = labels
    meta["tumor_stage"] = stages
    meta["m_stage"] = m_stage
    meta["age"] = np.nan  # not in series matrix
    meta["batch_index"] = 0
    meta["patient_id"] = meta["title"].str.extract(r"(\d+)", expand=False)
    return meta


def build(out_path: Path = OUT_CSV) -> Path:
    gz = _download_if_needed()
    meta, expr = _parse_series_matrix(gz)
    meta = _derive_labels(meta)

    # Resolve probe -> gene: prefer canonical, fall back to _alt if missing.
    gene_rows: dict[str, pd.Series] = {}
    for gene, probes in _PREFERENCE.items():
        for probe in probes:
            if probe in expr.index:
                vals = expr.loc[probe].astype(float)
                # If multiple rows per probe (rare), take the mean.
                if isinstance(vals, pd.DataFrame):
                    vals = vals.mean(axis=0)
                gene_rows[gene] = vals
                break

    if not gene_rows:
        raise RuntimeError("no genes could be resolved from probes")

    expr_df = pd.DataFrame(gene_rows)  # samples x genes
    # Align on sample order
    expr_df = expr_df.reindex(meta["sample_id"].values)

    csv = pd.concat(
        [
            meta[["sample_id", "label", "m_stage", "tumor_stage", "age", "batch_index", "patient_id"]].reset_index(drop=True),
            expr_df.reset_index(drop=True),
        ],
        axis=1,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    csv.to_csv(out_path, index=False)
    print(
        f"[build_gse53757] wrote {out_path}: n={len(csv)} samples, "
        f"labels={csv['label'].value_counts().to_dict()}, "
        f"genes resolved: {sorted(gene_rows.keys())}"
    )
    return out_path


if __name__ == "__main__":
    build()
