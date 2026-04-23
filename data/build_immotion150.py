#!/usr/bin/env python3
"""Build data/immotion150_ccrcc.csv from cBioPortal IMmotion150 Phase-2 trial.

Source: rcc_iatlas_immotion150_2018 (Nat Med 2018, atezolizumab +/- bevacizumab
in metastatic ccRCC, n=263). Public cBioPortal REST API.

Unlike TCGA, this cohort is metastatic-only — so it cannot serve as an
M0-vs-M1 external replay. Instead we test a different, also-clinically-
interesting question: **does `TOP2A − EPAS1` stratify progression-free
survival (PFS) in metastatic ccRCC under immunotherapy + anti-VEGF?**

Output CSV:
    sample_id, pfs_months, pfs_status (1=progressed, 0=censored),
    clinical_stage, TOP2A, EPAS1, plus any extra genes listed below.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd


CBIOPORTAL = "https://www.cbioportal.org/api"
STUDY = "rcc_iatlas_immotion150_2018"
PROFILE = f"{STUDY}_rna_seq_mrna"
SAMPLE_LIST = f"{STUDY}_all"

# Entrez IDs for the survivor pair + a few proliferation/HIF partners so
# the CSV can support sensitivity analyses later.
GENES = {
    "TOP2A":   7153,
    "EPAS1":   2034,
    "MKI67":   4288,
    "CDK1":    983,
    "CCNB1":   891,
    "HIF1A":   3091,
    "VEGFA":   7422,
    "CA9":     768,
    "LRP2":    4036,
    "PTGER3":  5733,
    "RPL13A":  23521,
}


def _post_json(url: str, body: dict) -> list:
    req = Request(
        url,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        data=json.dumps(body).encode(),
    )
    with urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def _get_json(url: str) -> list:
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def fetch_expression() -> pd.DataFrame:
    entrez_ids = list(GENES.values())
    rows = _post_json(
        f"{CBIOPORTAL}/molecular-profiles/{PROFILE}/molecular-data/fetch",
        {"entrezGeneIds": entrez_ids, "sampleListId": SAMPLE_LIST},
    )
    entrez_to_sym = {v: k for k, v in GENES.items()}
    records: dict[str, dict] = {}
    for r in rows:
        sid = r["sampleId"]
        sym = entrez_to_sym.get(r["entrezGeneId"])
        if not sym:
            continue
        records.setdefault(sid, {"sample_id": sid})[sym] = r.get("value")
    return pd.DataFrame(records.values())


def fetch_clinical(attribute_ids: list[str]) -> pd.DataFrame:
    frames = []
    for attr in attribute_ids:
        url = (
            f"{CBIOPORTAL}/studies/{STUDY}/clinical-data"
            f"?clinicalDataType=SAMPLE&attributeId={attr}&pageSize=2000"
        )
        data = _get_json(url)
        if not data:
            continue
        df = pd.DataFrame(
            [{"sample_id": d["sampleId"], attr: d.get("value")} for d in data]
        )
        frames.append(df)
    # Also try PATIENT scope where sample attrs miss (PFS often stored per-patient).
    patient_attrs = []
    for attr in attribute_ids:
        url = (
            f"{CBIOPORTAL}/studies/{STUDY}/clinical-data"
            f"?clinicalDataType=PATIENT&attributeId={attr}&pageSize=2000"
        )
        data = _get_json(url)
        if not data:
            continue
        df = pd.DataFrame(
            [{"patient_id": d["patientId"], attr: d.get("value")} for d in data]
        )
        patient_attrs.append(df)

    # Map patient -> sample: cBioPortal samples endpoint gives both IDs.
    samples = _get_json(f"{CBIOPORTAL}/studies/{STUDY}/samples")
    sid_to_pid = {s["sampleId"]: s["patientId"] for s in samples}
    sample_to_patient_df = pd.DataFrame(
        [{"sample_id": s, "patient_id": p} for s, p in sid_to_pid.items()]
    )

    if frames:
        sample_frame = frames[0]
        for f in frames[1:]:
            sample_frame = sample_frame.merge(f, on="sample_id", how="outer")
    else:
        sample_frame = sample_to_patient_df[["sample_id"]].copy()
    out = sample_frame.merge(sample_to_patient_df, on="sample_id", how="left")
    for pf in patient_attrs:
        out = out.merge(pf, on="patient_id", how="left")
    return out


def build(out_path: Path = Path("data/immotion150_ccrcc.csv")) -> pd.DataFrame:
    expr = fetch_expression()
    clin = fetch_clinical([
        "METASTASIZED", "CLINICAL_STAGE",
        "PFS_MONTHS", "PFS_STATUS",
        "OS_MONTHS", "OS_STATUS",
    ])
    df = expr.merge(clin, on="sample_id", how="inner")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return df


if __name__ == "__main__":
    df = build()
    print(f"Wrote data/immotion150_ccrcc.csv: {df.shape[0]} samples x {df.shape[1]} cols")
    print(f"Columns: {list(df.columns)}")
    print(f"PFS non-null: {df['PFS_MONTHS'].notna().sum() if 'PFS_MONTHS' in df else 'N/A'}")
    print(f"TOP2A non-null: {df['TOP2A'].notna().sum() if 'TOP2A' in df else 'N/A'}")
    print(f"EPAS1 non-null: {df['EPAS1'].notna().sum() if 'EPAS1' in df else 'N/A'}")
