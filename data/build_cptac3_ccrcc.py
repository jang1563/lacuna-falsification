"""Build data/cptac3_ccrcc.csv — CPTAC-3 ccRCC proteogenomic cohort replay
for TOP2A - EPAS1.

Status: best-effort documentation path. The CPTAC-3 discovery ccRCC study
(Clark et al. Cell 2019, N = 103 tumors with matched NATs, proteogenomic)
is the highest-value independent replay because it has BOTH TOP2A + EPAS1
expression AND patient-level M-stage in the clinical data. However, bulk
RNA / protein matrices are distributed via the Proteomic Data Commons (PDC)
and require either:
  1. cBioPortal mirror (`ccrcc_ccrcc_pdc_2022`) — simple web scrape +
     CSV export, no auth required, but metadata shape varies; OR
  2. Direct PDC GraphQL API — requires `PDC_API_TOKEN` env var and
     an interactive consent flow for protected clinical fields (M-stage
     is in the open set, so this path is usable without auth).

This script prefers path (2) via an unauthenticated GraphQL call to the
public PDC endpoint. If the endpoint is unreachable (airgapped environment
or API schema drift), it writes a stub CSV with the header only and a
`NOTE.md` describing the manual retrieval steps.

Public data (NCI PDC / cBioPortal), MIT-safe. No institutional identifiers.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT_CSV = REPO / "data" / "cptac3_ccrcc.csv"
NOTE_MD = REPO / "data" / "cptac3_ccrcc_NOTE.md"

PDC_GRAPHQL_URL = "https://pdc.cancer.gov/graphql"
STUDY_ID = "Clark_CCRCC_PRO_Proteome"  # CPTAC-3 discovery ccRCC proteome study

# Target genes in the metastasis_expanded panel
WANTED_GENES: list[str] = [
    "TOP2A", "EPAS1", "MKI67", "CA9", "VEGFA", "AGXT", "ACTB", "GAPDH",
    "RPL13A", "LRP2", "PTGER3",
]


def _try_pdc(study_id: str) -> pd.DataFrame | None:
    """Try to fetch protein quantification from the PDC GraphQL API.

    Returns a long-form DataFrame [aliquot, gene_symbol, log2_ratio, m_stage]
    on success or None on network/schema failure.
    """
    query = {
        "query": f"""
        {{
          quantDataMatrix(study_id: \"{study_id}\", data_type: \"log2_ratio\") {{
            gene_symbol
            aliquot_run_metadata_id
            quant_value
          }}
        }}
        """
    }
    req = urllib.request.Request(
        PDC_GRAPHQL_URL,
        data=json.dumps(query).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"[build_cptac3_ccrcc] PDC GraphQL unreachable: {e}")
        return None
    if "errors" in body:
        print(f"[build_cptac3_ccrcc] PDC returned errors: {body['errors'][:1]}")
        return None
    rows = (body.get("data") or {}).get("quantDataMatrix") or []
    if not rows:
        return None
    df = pd.DataFrame(rows)
    df = df[df["gene_symbol"].isin(WANTED_GENES)].copy()
    return df


def _write_note(msg: str) -> Path:
    NOTE_MD.parent.mkdir(parents=True, exist_ok=True)
    NOTE_MD.write_text(
        "# CPTAC-3 ccRCC replay — manual retrieval notes\n\n"
        f"Status: **stub** — {msg}\n\n"
        "## How to complete this replay by hand\n\n"
        "1. Go to <https://pdc.cancer.gov/pdc/study/S044-1> (CPTAC-3 CCRCC Discovery\n"
        "   Proteome, Clark et al. Cell 2019, n=103 tumors).\n"
        "2. Download the gene-level log2-ratio quantification matrix and the\n"
        "   CPTAC-3 clinical metadata (contains `ajcc_pathologic_m`).\n"
        "3. Join on `case_submitter_id` (tumor aliquot) → produce a wide CSV\n"
        "   with columns: sample_id, label (M1|M0), tumor_stage, age,\n"
        "   batch_index, patient_id, <TOP2A..VEGFA expression>.\n"
        "4. Use RNA quantification from the matched CPTAC-3 RNA-seq study\n"
        "   (`Clark_CCRCC_RNA_Transcriptome`) for head-to-head with the TCGA-KIRC\n"
        "   RNA-seq readout.\n"
        "5. Rerun `run_external_replay.py --cohort cptac3` to emit the gate\n"
        "   verdict on M1 vs M0 for `TOP2A - EPAS1`.\n\n"
        "## Why this matters\n\n"
        "CPTAC-3 is the ONLY published ccRCC cohort that carries both the\n"
        "proliferation + HIF-2α gene pair and patient-level M-stage. A pass\n"
        "on this cohort would let `TOP2A - EPAS1` clear a proteogenomic\n"
        "replay too; a fail here is the most informative negative result.\n"
        "GSE53757 and GSE40435 both lack M-stage and therefore only serve\n"
        "as tumor-vs-normal sanity checks for the same law.\n"
    )
    return NOTE_MD


def build(out_path: Path = OUT_CSV) -> Path:
    df = _try_pdc(STUDY_ID)
    if df is None:
        _write_note("PDC GraphQL unreachable from this session; see manual steps below")
        header = ["sample_id", "label", "m_stage", "tumor_stage", "age", "batch_index", "patient_id"] + WANTED_GENES
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=header).to_csv(out_path, index=False)
        print(f"[build_cptac3_ccrcc] wrote stub {out_path}; NOTE at {NOTE_MD}")
        return out_path

    # Cross-tabulate into wide form. M-stage join would need additional
    # metadata which the current GraphQL query does not retrieve; if we
    # only got quantification, still emit a wide table for inspection.
    pivot = df.pivot_table(
        index="aliquot_run_metadata_id",
        columns="gene_symbol",
        values="quant_value",
        aggfunc="first",
    )
    pivot = pivot.reset_index().rename(columns={"aliquot_run_metadata_id": "sample_id"})
    pivot["label"] = ""  # requires clinical join to assign M1/M0
    pivot["m_stage"] = ""
    pivot["tumor_stage"] = ""
    pivot["age"] = np.nan
    pivot["batch_index"] = 0
    pivot["patient_id"] = ""
    cols = ["sample_id", "label", "m_stage", "tumor_stage", "age", "batch_index", "patient_id"] + [
        g for g in WANTED_GENES if g in pivot.columns
    ]
    pivot = pivot[cols]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pivot.to_csv(out_path, index=False)
    print(f"[build_cptac3_ccrcc] wrote {out_path}: n={len(pivot)} aliquots")
    _write_note(
        "PDC GraphQL returned quant rows but clinical join for M-stage was not "
        "performed in-band (requires a second GraphQL query to `clinicalMetadata`). "
        "See manual steps below."
    )
    return out_path


if __name__ == "__main__":
    build()
