"""Build data/ipf_bal_gse93606.csv and data/ipf_bal_gse70867.csv.

IPF BAL (bronchoalveolar lavage) transcriptomics with survival/composite endpoint.

GSE93606 — primary discovery cohort
  Affymetrix microarray, BAL fluid, n=60 IPF + 20 controls
  Platform: GPL17930 (Affymetrix Human Gene ST 2.1)
  Endpoint: composite (death OR FVC decline >10% at 6 months)
  Key paper: 10.3389/fgene.2023.1246983

GSE70867 — replication cohort
  Multi-platform (Affymetrix), BAL cells, n=176 IPF from 3 centres
  Platform: GPL17586 (Affymetrix Human Transcriptome Array 2.0)
  Endpoint: overall survival, 100/176 died during follow-up
  Access: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE70867

Task: composite endpoint (death OR FVC decline >10%) binary in GSE93606,
      overall survival above/below median in GSE70867.

Hypothesis: SPP1 − CCL20 compound law (fibrotic macrophage minus aberrant
epithelial signalling) predicts composite endpoint above GAP-score baseline.

Run:
    pip install GEOparse
    python3 data/build_ipf_bal.py

Output: data/ipf_bal_gse93606.csv, data/ipf_bal_gse70867.csv
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
TMP = REPO / ".tmp_geo"
TMP.mkdir(exist_ok=True)

OUT_93606 = REPO / "data" / "ipf_bal_gse93606.csv"
OUT_70867 = REPO / "data" / "ipf_bal_gse70867.csv"

# Gene panel — IPF BAL progression markers
# Hypothesis axes:
#   Fibrotic/macrophage drive: SPP1, CTHRC1, COL1A1, MMP7, CCL18
#   Aberrant epithelial (poor outcome): CCL20, KRT17, KRT5, MUC5B
#   Protective/anti-fibrotic: AGER, SFTPC, CAV1
#   Inflammatory: TGFB1, IL6, CXCL12
#   Myofibroblast: ACTA2, PDGFRA
TARGET_GENE_SYMBOLS = [
    "SPP1",    # secreted phosphoprotein 1 — macrophage activation, MVI-like pattern
    "CTHRC1",  # collagen triple helix repeat — fibroblast activation
    "COL1A1",  # collagen 1A1 — fibrosis marker
    "MMP7",    # matrix metalloproteinase 7 — IPF-specific, FDA-endorsed
    "CCL18",   # chemokine ligand 18 — M2 macrophage, poor prognosis
    "CCL20",   # chemokine ligand 20 — aberrant epithelial cell signal
    "KRT17",   # keratin 17 — epithelial injury / ABCs
    "KRT5",    # keratin 5 — aberrant basal cell (ABC) marker
    "MUC5B",   # mucin 5B — genetic risk variant, high expression
    "AGER",    # RAGE receptor — alveolar type 1 cell protective
    "SFTPC",   # surfactant C — alveolar type 2 cell marker
    "CAV1",    # caveolin-1 — anti-fibrotic
    "TGFB1",   # TGF-beta 1 — canonical fibrosis driver
    "IL6",     # interleukin 6 — systemic inflammation
    "CXCL12",  # SDF-1 — FVC decline correlate
    "ACTA2",   # alpha-smooth muscle actin — myofibroblast
    "PDGFRA",  # platelet-derived growth factor receptor alpha — fibroblast
]


def _characteristics_lines(meta: dict) -> list[str]:
    raw = meta.get("characteristics_ch1", [])
    if isinstance(raw, dict):
        values = raw.values()
    else:
        values = raw
    return [
        item[0] if isinstance(item, list) and item else str(item)
        for item in values
    ]


def _load_geoparse(accession: str) -> object:
    try:
        import GEOparse
    except ImportError:
        print("ERROR: GEOparse not installed. Run: pip install GEOparse")
        sys.exit(1)
    cache = TMP / f"{accession}_series_matrix.txt.gz"
    gse = GEOparse.get_GEO(accession, destdir=str(TMP), silent=True)
    return gse


def _probe_to_gene_mean(gse: object, target_genes: list[str]) -> pd.DataFrame:
    """Map probe intensities to gene symbols; average multi-probe genes."""
    gpl = list(gse.gpls.values())[0]
    ann = gpl.table

    # Find gene symbol column (GPL annotations vary)
    sym_col = None
    for col in ["Gene Symbol", "gene_assignment", "GB_ACC", "GENE_SYMBOL", "Symbol"]:
        if col in ann.columns:
            sym_col = col
            break
    if sym_col is None:
        avail = list(ann.columns)
        raise RuntimeError(f"Gene symbol column not found in GPL. Available: {avail[:10]}")

    ann = ann[["ID", sym_col]].copy()
    ann["ID"] = ann["ID"].astype(str)

    # Get expression matrix
    gsms = gse.gsms
    expr_data: dict[str, dict[str, float]] = {}
    for gsm_id, gsm in gsms.items():
        t = gsm.table
        if "VALUE" not in t.columns:
            continue
        t = t.copy()
        t["ID"] = t["ID_REF"].astype(str) if "ID_REF" in t.columns else t.index.astype(str)
        merged = t.merge(ann, on="ID", how="left")
        merged["VALUE"] = pd.to_numeric(merged["VALUE"], errors="coerce")
        expr_data[gsm_id] = {}
        for gene in target_genes:
            rows = merged[merged[sym_col].str.contains(
                rf"\b{re.escape(gene)}\b", na=False, regex=True
            )]
            if not rows.empty:
                expr_data[gsm_id][gene] = float(rows["VALUE"].mean())

    df = pd.DataFrame(expr_data).T
    df.index.name = "gsm_id"
    return df.reset_index()


def _parse_metadata_93606(gse: object) -> pd.DataFrame:
    """Extract composite endpoint and control/IPF label from GSE93606 metadata."""
    records = []
    for gsm_id, gsm in gse.gsms.items():
        meta = gsm.metadata
        char_lines = _characteristics_lines(meta)
        char_str = " ".join(char_lines)
        # Disease vs control
        source = (meta.get("source_name_ch1", [""])[0] if isinstance(
            meta.get("source_name_ch1"), list) else meta.get("source_name_ch1", ""))
        is_ipf = "ipf" in str(source).lower() or "idiopathic pulmonary fibrosis" in char_str.lower()
        disease_type = "IPF" if is_ipf else "control"

        # Composite endpoint: look for clinical outcome keywords in characteristics
        # GSE93606 embeds FVC decline and survival in sample characteristics
        composite = None
        fvc_decline = None
        survival_months = None

        for line in char_lines:
            l = line.lower()
            if "fvc" in l and "decline" in l:
                # e.g. "fvc decline at 6 months: 15.2"
                m = re.search(r"fvc.*?decline.*?:\s*([-\d.]+)", l)
                if m:
                    fvc_decline = float(m.group(1))
            if "survival" in l or "death" in l or "composite" in l:
                m = re.search(r":\s*(yes|no|1|0|true|false)", l)
                if m:
                    composite = 1 if m.group(1) in {"yes", "1", "true"} else 0

        records.append({
            "gsm_id": gsm_id,
            "disease_type": disease_type,
            "composite_endpoint": composite,
            "fvc_decline_pct": fvc_decline,
            "survival_months": survival_months,
        })

    df = pd.DataFrame(records)
    print(f"  GSE93606 samples: {len(df)} total, {(df['disease_type']=='IPF').sum()} IPF")
    print(f"  Composite endpoint annotated: {df['composite_endpoint'].notna().sum()}")
    print(f"  FVC decline annotated: {df['fvc_decline_pct'].notna().sum()}")
    return df


def _parse_metadata_70867(gse: object) -> pd.DataFrame:
    """Extract overall survival from GSE70867 metadata."""
    records = []
    for gsm_id, gsm in gse.gsms.items():
        meta = gsm.metadata
        char_lines = _characteristics_lines(meta)
        survival_months = None
        vital_status = None
        disease_type = "IPF"  # GSE70867 is all IPF

        for line in char_lines:
            l = line.lower()
            if "survival" in l and "month" in l:
                m = re.search(r":\s*([\d.]+)", l)
                if m:
                    survival_months = float(m.group(1))
            if "vital" in l or "death" in l or "status" in l:
                m = re.search(r":\s*(\w+)", l)
                if m:
                    v = m.group(1).lower()
                    vital_status = 1 if v in {"dead", "deceased", "died", "1"} else 0

        records.append({
            "gsm_id": gsm_id,
            "disease_type": disease_type,
            "survival_months": survival_months,
            "vital_status": vital_status,
        })

    df = pd.DataFrame(records)
    print(f"  GSE70867 samples: {len(df)} total")
    print(f"  Survival months annotated: {df['survival_months'].notna().sum()}")
    print(f"  Vital status annotated: {df['vital_status'].notna().sum()}")
    return df


def build_gse93606() -> pd.DataFrame | None:
    print("\n=== GSE93606 IPF BAL (discovery cohort) ===")
    gse = _load_geoparse("GSE93606")
    meta = _parse_metadata_93606(gse)
    expr = _probe_to_gene_mean(gse, TARGET_GENE_SYMBOLS)
    merged = meta.merge(expr, on="gsm_id", how="inner")

    # Task 1: IPF composite endpoint (if annotated)
    ipf_rows = merged[merged["disease_type"] == "IPF"].copy()
    comp_annotated = ipf_rows[ipf_rows["composite_endpoint"].notna()]
    print(f"  IPF rows with composite endpoint: {len(comp_annotated)}")

    if len(comp_annotated) < 20:
        print("  [fallback] Composite endpoint not in metadata — using FVC decline >10% as proxy")
        # Fallback: FVC decline > 10% → disease, <= 10% → control
        ipf_rows = ipf_rows[ipf_rows["fvc_decline_pct"].notna()].copy()
        ipf_rows["label"] = (ipf_rows["fvc_decline_pct"].abs() > 10).astype(int)
        print(f"  Rows with FVC decline: {len(ipf_rows)}")
    else:
        ipf_rows = comp_annotated.copy()
        ipf_rows["label"] = ipf_rows["composite_endpoint"].astype(int)

    gene_cols = [g for g in TARGET_GENE_SYMBOLS if g in ipf_rows.columns]
    out = ipf_rows[["gsm_id", "label"] + gene_cols].rename(columns={"gsm_id": "sample_id"})
    out = out.dropna(subset=["label"] + gene_cols[:3])  # require at least 3 genes present
    out.to_csv(OUT_93606, index=False)
    print(f"  Written: {OUT_93606} ({len(out)} rows, label dist: {out['label'].value_counts().to_dict()})")
    return out


def build_gse70867() -> pd.DataFrame | None:
    print("\n=== GSE70867 IPF BAL (replication cohort) ===")
    gse = _load_geoparse("GSE70867")
    meta = _parse_metadata_70867(gse)
    expr = _probe_to_gene_mean(gse, TARGET_GENE_SYMBOLS)
    merged = meta.merge(expr, on="gsm_id", how="inner")

    # Task: OS above/below median
    survival_rows = merged[merged["survival_months"].notna()].copy()
    if len(survival_rows) >= 20:
        median_os = survival_rows["survival_months"].median()
        survival_rows["label"] = (survival_rows["survival_months"] > median_os).astype(int)
        print(f"  Median OS: {median_os:.1f} months; dichotomised to {survival_rows['label'].value_counts().to_dict()}")
        gene_cols = [g for g in TARGET_GENE_SYMBOLS if g in survival_rows.columns]
        out = survival_rows[["gsm_id", "label"] + gene_cols].rename(columns={"gsm_id": "sample_id"})
        out = out.dropna(subset=["label"] + gene_cols[:3])
        out.to_csv(OUT_70867, index=False)
        print(f"  Written: {OUT_70867} ({len(out)} rows)")
        return out
    else:
        print(f"  [warn] Only {len(survival_rows)} rows with survival — check metadata parsing.")
        print("  Saving all IPF rows with label=IPF for exploratory use.")
        merged["label"] = 1
        gene_cols = [g for g in TARGET_GENE_SYMBOLS if g in merged.columns]
        merged[["gsm_id", "label"] + gene_cols].rename(
            columns={"gsm_id": "sample_id"}
        ).to_csv(OUT_70867, index=False)
        return None


if __name__ == "__main__":
    build_gse93606()
    build_gse70867()
    print("\n=== Done. Check data/ipf_bal_gse93606.csv and data/ipf_bal_gse70867.csv ===")
    print("If label distribution is skewed, revisit metadata parsing — GEO sample")
    print("characteristics vary significantly between series. Check GSM metadata with:")
    print("  import GEOparse; gse = GEOparse.get_GEO('GSE93606')")
    print("  list(gse.gsms.values())[0].metadata['characteristics_ch1']")
