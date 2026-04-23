#!/usr/bin/env python3
"""G3-NEW: Adjusted Cox model for TOP2A − EPAS1 on IMmotion150.

Adds treatment arm (atezo / atezo+bev / sunitinib) and TMB as covariates.
Reports adjusted HR for score_z after controlling for these variables.

Research question: Does HR 1.36 (unadjusted) survive confounding adjustment?

Lane G, commit prefix [G].
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd


CBIOPORTAL = "https://www.cbioportal.org/api"
STUDY = "rcc_iatlas_immotion150_2018"


def _get_json(url: str) -> list:
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def _fetch_attr(attr_id: str, scope: str = "SAMPLE") -> dict:
    """Return {sampleId: value} or {patientId: value} dict."""
    url = (
        f"{CBIOPORTAL}/studies/{STUDY}/clinical-data"
        f"?clinicalDataType={scope}&attributeId={attr_id}&pageSize=2000"
    )
    data = _get_json(url)
    id_key = "sampleId" if scope == "SAMPLE" else "patientId"
    return {d[id_key]: d["value"] for d in data}


def fetch_covariates() -> pd.DataFrame:
    """Fetch treatment arm (ICI_RX + NON_ICI_RX) and TMB from cBioPortal."""
    ici_rx = _fetch_attr("ICI_RX", scope="PATIENT")      # Atezolizumab | None
    non_ici = _fetch_attr("NON_ICI_RX", scope="SAMPLE")  # Bevacizumab | Sunitinib | absent
    tmb = _fetch_attr("TMB_NONSYNONYMOUS", scope="SAMPLE")

    # Patient→sample mapping (1:1 in this cohort)
    samples = _get_json(f"{CBIOPORTAL}/studies/{STUDY}/samples")
    rows = []
    for s in samples:
        sid = s["sampleId"]
        pid = s["patientId"]
        ici = ici_rx.get(pid, "None")
        nonici = non_ici.get(sid, None)

        # Derive 3-level treatment arm
        if ici == "Atezolizumab" and nonici == "Bevacizumab":
            arm = "atezo_bev"
        elif ici == "Atezolizumab":
            arm = "atezo"
        else:
            arm = "sunitinib"

        tmb_val = tmb.get(sid, None)
        rows.append({"sample_id": sid, "treatment_arm": arm,
                     "TMB": float(tmb_val) if tmb_val is not None else np.nan})

    return pd.DataFrame(rows)


def run_adjusted_cox(df: pd.DataFrame, out_dir: Path) -> dict:
    from lifelines import CoxPHFitter

    df = df.copy()
    df["score"] = df["TOP2A"] - df["EPAS1"]
    df["score_z"] = (df["score"] - df["score"].mean()) / df["score"].std()

    # Dummy-encode treatment arm (reference = sunitinib)
    arm_dummies = pd.get_dummies(df["treatment_arm"], prefix="arm", drop_first=False)
    # Keep atezo and atezo_bev as binary indicators; sunitinib = reference
    df["arm_atezo"] = arm_dummies.get("arm_atezo", 0).astype(int)
    df["arm_atezo_bev"] = arm_dummies.get("arm_atezo_bev", 0).astype(int)

    results = {}

    # --- Model 1: score_z + treatment arm (all 263 samples) ----------
    cols1 = ["T", "E", "score_z", "arm_atezo", "arm_atezo_bev"]
    df1 = df[["PFS_MONTHS", "pfs_event", "score_z", "arm_atezo", "arm_atezo_bev"]].rename(
        columns={"PFS_MONTHS": "T", "pfs_event": "E"}
    ).dropna()

    cph1 = CoxPHFitter()
    cph1.fit(df1, duration_col="T", event_col="E")

    row1 = cph1.summary.loc["score_z"]
    results["model1_treatment_adjusted"] = {
        "n": len(df1),
        "covariates": ["treatment_arm"],
        "score_z_hr": float(np.exp(cph1.params_["score_z"])),
        "score_z_hr_ci_low": float(np.exp(cph1.confidence_intervals_.loc["score_z", "95% lower-bound"])),
        "score_z_hr_ci_high": float(np.exp(cph1.confidence_intervals_.loc["score_z", "95% upper-bound"])),
        "score_z_p": float(row1["p"]),
        "arm_atezo_hr": float(np.exp(cph1.params_["arm_atezo"])),
        "arm_atezo_bev_hr": float(np.exp(cph1.params_["arm_atezo_bev"])),
    }

    # --- Model 2: score_z + treatment + TMB (158 samples with TMB) ---
    df2 = df[["PFS_MONTHS", "pfs_event", "score_z", "arm_atezo", "arm_atezo_bev", "TMB"]].rename(
        columns={"PFS_MONTHS": "T", "pfs_event": "E"}
    ).dropna()

    cph2 = CoxPHFitter()
    cph2.fit(df2, duration_col="T", event_col="E")

    row2 = cph2.summary.loc["score_z"]
    results["model2_treatment_tmb_adjusted"] = {
        "n": len(df2),
        "covariates": ["treatment_arm", "TMB"],
        "score_z_hr": float(np.exp(cph2.params_["score_z"])),
        "score_z_hr_ci_low": float(np.exp(cph2.confidence_intervals_.loc["score_z", "95% lower-bound"])),
        "score_z_hr_ci_high": float(np.exp(cph2.confidence_intervals_.loc["score_z", "95% upper-bound"])),
        "score_z_p": float(row2["p"]),
    }

    # --- Unadjusted (reference) ---
    df0 = df[["PFS_MONTHS", "pfs_event", "score_z"]].rename(
        columns={"PFS_MONTHS": "T", "pfs_event": "E"}
    ).dropna()
    cph0 = CoxPHFitter()
    cph0.fit(df0, duration_col="T", event_col="E")
    results["model0_unadjusted"] = {
        "n": len(df0),
        "covariates": [],
        "score_z_hr": float(np.exp(cph0.params_["score_z"])),
        "score_z_hr_ci_low": float(np.exp(cph0.confidence_intervals_.loc["score_z", "95% lower-bound"])),
        "score_z_hr_ci_high": float(np.exp(cph0.confidence_intervals_.loc["score_z", "95% upper-bound"])),
        "score_z_p": float(cph0.summary.loc["score_z", "p"]),
    }

    # --- Verdict ---
    adj_hr = results["model1_treatment_adjusted"]["score_z_hr"]
    adj_ci_low = results["model1_treatment_adjusted"]["score_z_hr_ci_low"]
    unadj_hr = results["model0_unadjusted"]["score_z_hr"]

    results["verdict"] = {
        "unadjusted_hr": unadj_hr,
        "treatment_adjusted_hr": adj_hr,
        "hr_attenuation_pct": 100 * (unadj_hr - adj_hr) / (unadj_hr - 1.0) if unadj_hr > 1 else None,
        "ci_still_excludes_1": adj_ci_low > 1.0,
        "conclusion": (
            "HR robust to treatment-arm adjustment: CI still excludes 1.0"
            if adj_ci_low > 1.0
            else "HR attenuated to non-significance after treatment-arm adjustment"
        ),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "adjusted_cox.json").write_text(json.dumps(results, indent=2))
    return results


def main():
    repo_root = Path(__file__).resolve().parent.parent
    base_csv = repo_root / "data" / "immotion150_ccrcc.csv"
    out_dir = (
        repo_root / "results" / "track_a_task_landscape" / "external_replay"
        / "immotion150_pfs" / "g3_adjusted_cox"
    )

    df = pd.read_csv(base_csv)
    raw_status = df["PFS_STATUS"].astype(str)
    df["pfs_event"] = raw_status.str.startswith("1").astype(int)
    df = df.dropna(subset=["TOP2A", "EPAS1", "PFS_MONTHS", "pfs_event"]).copy()

    print("Fetching covariates from cBioPortal...")
    covariates = fetch_covariates()
    print(f"Treatment arm distribution:\n{covariates['treatment_arm'].value_counts()}")
    print(f"TMB non-null: {covariates['TMB'].notna().sum()}/{len(covariates)}")

    df = df.merge(covariates, on="sample_id", how="left")
    print(f"\nMerged: n={len(df)}, treatment_arm non-null: {df['treatment_arm'].notna().sum()}")

    print("\nRunning adjusted Cox models...")
    results = run_adjusted_cox(df, out_dir)

    print("\n" + "="*60)
    print("[G3-NEW] Adjusted Cox Results — TOP2A − EPAS1 score_z")
    print("="*60)
    m0 = results["model0_unadjusted"]
    m1 = results["model1_treatment_adjusted"]
    m2 = results["model2_treatment_tmb_adjusted"]
    v  = results["verdict"]

    print(f"\nUnadjusted         HR={m0['score_z_hr']:.3f} "
          f"(95%CI {m0['score_z_hr_ci_low']:.3f}-{m0['score_z_hr_ci_high']:.3f}) "
          f"p={m0['score_z_p']:.4f}  n={m0['n']}")
    print(f"+ treatment arm    HR={m1['score_z_hr']:.3f} "
          f"(95%CI {m1['score_z_hr_ci_low']:.3f}-{m1['score_z_hr_ci_high']:.3f}) "
          f"p={m1['score_z_p']:.4f}  n={m1['n']}")
    print(f"+ treatment + TMB  HR={m2['score_z_hr']:.3f} "
          f"(95%CI {m2['score_z_hr_ci_low']:.3f}-{m2['score_z_hr_ci_high']:.3f}) "
          f"p={m2['score_z_p']:.4f}  n={m2['n']}")
    print(f"\nConclusion: {v['conclusion']}")
    print(f"HR attenuation: {v['hr_attenuation_pct']:.1f}%" if v['hr_attenuation_pct'] else "HR attenuation: N/A")
    print(f"\nResults written to: {out_dir}/adjusted_cox.json")


if __name__ == "__main__":
    main()
