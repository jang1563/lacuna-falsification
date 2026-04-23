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
    """Fetch treatment arm, immune subtype, and TMB from cBioPortal."""
    ici_rx = _fetch_attr("ICI_RX", scope="PATIENT")      # Atezolizumab | None
    non_ici = _fetch_attr("NON_ICI_RX", scope="SAMPLE")  # Bevacizumab | Sunitinib | absent
    tmb = _fetch_attr("TMB_NONSYNONYMOUS", scope="SAMPLE")
    immune_subtype = _fetch_attr("IMMUNE_SUBTYPE", scope="SAMPLE")  # TGF-beta | Inflamed | Desert

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
        imm_sub = immune_subtype.get(sid, None)
        rows.append({"sample_id": sid, "treatment_arm": arm,
                     "TMB": float(tmb_val) if tmb_val is not None else np.nan,
                     "immune_subtype": imm_sub})

    return pd.DataFrame(rows)


def _cox_row(cph, df_fit: pd.DataFrame, covar_names: list[str]) -> dict:
    """Extract score_z HR + CI + p from a fitted CoxPHFitter."""
    return {
        "n": len(df_fit),
        "covariates": covar_names,
        "score_z_hr": float(np.exp(cph.params_["score_z"])),
        "score_z_hr_ci_low": float(np.exp(cph.confidence_intervals_.loc["score_z", "95% lower-bound"])),
        "score_z_hr_ci_high": float(np.exp(cph.confidence_intervals_.loc["score_z", "95% upper-bound"])),
        "score_z_p": float(cph.summary.loc["score_z", "p"]),
    }


def run_adjusted_cox(df: pd.DataFrame, out_dir: Path) -> dict:
    from lifelines import CoxPHFitter

    df = df.copy()
    df["score"] = df["TOP2A"] - df["EPAS1"]
    df["score_z"] = (df["score"] - df["score"].mean()) / df["score"].std()

    # Dummy-encode treatment arm (reference = sunitinib)
    arm_dummies = pd.get_dummies(df["treatment_arm"], prefix="arm", drop_first=False)
    df["arm_atezo"] = arm_dummies.get("arm_atezo", pd.Series(0, index=df.index)).astype(int)
    df["arm_atezo_bev"] = arm_dummies.get("arm_atezo_bev", pd.Series(0, index=df.index)).astype(int)

    # Check immune subtype variance — cBioPortal IMmotion150 returns 'C4' for all
    # samples (TCGA immune subtype, not the TGF-beta/Inflamed/Desert from McDermott 2018).
    # If constant, immune-subtype-adjusted models are infeasible.
    immune_unique = df["immune_subtype"].dropna().unique()
    immune_feasible = len(immune_unique) > 1

    results = {}

    # --- Model 0: unadjusted (reference) ---
    df0 = df[["PFS_MONTHS", "pfs_event", "score_z"]].rename(
        columns={"PFS_MONTHS": "T", "pfs_event": "E"}
    ).dropna()
    cph0 = CoxPHFitter()
    cph0.fit(df0, duration_col="T", event_col="E")
    r0 = _cox_row(cph0, df0, [])
    results["model0_unadjusted"] = r0

    # --- Model 1: score_z + treatment arm (pre-reg kill test 1) ---
    arm_dummies = pd.get_dummies(df["treatment_arm"], prefix="arm", drop_first=False)
    df["arm_atezo"] = arm_dummies.get("arm_atezo", pd.Series(0, index=df.index)).astype(int)
    df["arm_atezo_bev"] = arm_dummies.get("arm_atezo_bev", pd.Series(0, index=df.index)).astype(int)

    df1 = df[["PFS_MONTHS", "pfs_event", "score_z", "arm_atezo", "arm_atezo_bev"]].rename(
        columns={"PFS_MONTHS": "T", "pfs_event": "E"}
    ).dropna()
    cph1 = CoxPHFitter()
    cph1.fit(df1, duration_col="T", event_col="E")
    r1 = _cox_row(cph1, df1, ["treatment_arm"])
    r1["arm_atezo_hr"] = float(np.exp(cph1.params_["arm_atezo"]))
    r1["arm_atezo_bev_hr"] = float(np.exp(cph1.params_["arm_atezo_bev"]))
    results["model1_treatment_adjusted"] = r1

    # --- Model 2: score_z + treatment + TMB (legacy; kept for continuity) ---
    df2 = df[["PFS_MONTHS", "pfs_event", "score_z", "arm_atezo", "arm_atezo_bev", "TMB"]].rename(
        columns={"PFS_MONTHS": "T", "pfs_event": "E"}
    ).dropna()
    cph2 = CoxPHFitter()
    cph2.fit(df2, duration_col="T", event_col="E")
    results["model2_treatment_tmb_adjusted"] = _cox_row(cph2, df2, ["treatment_arm", "TMB"])

    _INFEASIBLE_NOTE = (
        f"NOT_FEASIBLE: cBioPortal IMMUNE_SUBTYPE attribute for study "
        f"rcc_iatlas_immotion150_2018 returns a single category "
        f"({immune_unique[0] if len(immune_unique)==1 else 'N/A'}) for all samples. "
        "McDermott 2018 TGF-beta/Inflamed/Desert subtype data not publicly available "
        "via cBioPortal API as of 2026-04-23."
    )

    if immune_feasible:
        imm_dummies = pd.get_dummies(df["immune_subtype"], prefix="imm", drop_first=False)
        df["imm_inflamed"] = imm_dummies.get("imm_Inflamed", pd.Series(0, index=df.index)).astype(int)
        df["imm_tgfbeta"] = imm_dummies.get("imm_TGF-beta", pd.Series(0, index=df.index)).astype(int)

        df3 = df[["PFS_MONTHS", "pfs_event", "score_z", "imm_inflamed", "imm_tgfbeta"]].rename(
            columns={"PFS_MONTHS": "T", "pfs_event": "E"}
        ).dropna()
        cph3 = CoxPHFitter()
        cph3.fit(df3, duration_col="T", event_col="E")
        r3 = _cox_row(cph3, df3, ["immune_subtype"])
        r3["imm_inflamed_hr"] = float(np.exp(cph3.params_["imm_inflamed"]))
        r3["imm_tgfbeta_hr"] = float(np.exp(cph3.params_["imm_tgfbeta"]))
        results["model3_immune_subtype_adjusted"] = r3

        df4 = df[["PFS_MONTHS", "pfs_event", "score_z",
                  "arm_atezo", "arm_atezo_bev",
                  "imm_inflamed", "imm_tgfbeta",
                  "TMB"]].rename(columns={"PFS_MONTHS": "T", "pfs_event": "E"}).dropna()
        cph4 = CoxPHFitter()
        cph4.fit(df4, duration_col="T", event_col="E")
        r4 = _cox_row(cph4, df4, ["treatment_arm", "immune_subtype", "TMB"])
        results["model4_fully_adjusted"] = r4
    else:
        results["model3_immune_subtype_adjusted"] = {"status": "NOT_FEASIBLE", "note": _INFEASIBLE_NOTE}
        results["model4_fully_adjusted"] = {"status": "NOT_FEASIBLE", "note": _INFEASIBLE_NOTE}
        r3 = None
        r4 = None

    # --- Pre-registration kill-test verdicts (g3_adjusted_cox_immotion150.yaml) ---
    def _ci_excludes_1(r: dict | None) -> bool:
        if r is None or "status" in r:
            return False
        return r["score_z_hr_ci_low"] > 1.0

    results["prereg_kill_test_verdicts"] = {
        "adjusted_cox_hr_treatment": {
            "pass": _ci_excludes_1(r1),
            "hr": r1["score_z_hr"],
            "ci_low": r1["score_z_hr_ci_low"],
            "ci_high": r1["score_z_hr_ci_high"],
            "p": r1["score_z_p"],
        },
        "adjusted_cox_hr_immune_subtype": (
            {
                "pass": _ci_excludes_1(r3),
                "hr": r3["score_z_hr"],
                "ci_low": r3["score_z_hr_ci_low"],
                "ci_high": r3["score_z_hr_ci_high"],
                "p": r3["score_z_p"],
            } if r3 else {"status": "NOT_FEASIBLE", "note": _INFEASIBLE_NOTE}
        ),
        "adjusted_cox_hr_full": (
            {
                "pass": _ci_excludes_1(r4),
                "hr": r4["score_z_hr"],
                "ci_low": r4["score_z_hr_ci_low"],
                "ci_high": r4["score_z_hr_ci_high"],
                "p": r4["score_z_p"],
            } if r4 else {"status": "NOT_FEASIBLE", "note": _INFEASIBLE_NOTE}
        ),
        "overall_verdict": (
            "PASS_PARTIAL" if (not immune_feasible and _ci_excludes_1(r1))
            else "PASS" if all([_ci_excludes_1(r1), _ci_excludes_1(r3), _ci_excludes_1(r4)])
            else "PARTIAL" if any([_ci_excludes_1(r1), _ci_excludes_1(r3), _ci_excludes_1(r4)])
            else "FAIL"
        ),
        "feasibility_note": "" if immune_feasible else _INFEASIBLE_NOTE,
    }

    # --- Legacy verdict field (backward compatible) ---
    unadj_hr = r0["score_z_hr"]
    adj_hr = r1["score_z_hr"]
    results["verdict"] = {
        "unadjusted_hr": unadj_hr,
        "treatment_adjusted_hr": adj_hr,
        "hr_attenuation_pct": 100 * (unadj_hr - adj_hr) / (unadj_hr - 1.0) if unadj_hr > 1 else None,
        "ci_still_excludes_1": _ci_excludes_1(r1),
        "conclusion": (
            "HR robust to treatment-arm adjustment: CI still excludes 1.0"
            if _ci_excludes_1(r1)
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
    immune_uniq = covariates["immune_subtype"].dropna().unique()
    print(f"Immune subtype unique values ({len(immune_uniq)}): {immune_uniq}")
    print(f"TMB non-null: {covariates['TMB'].notna().sum()}/{len(covariates)}")

    df = df.merge(covariates, on="sample_id", how="left")
    print(f"\nMerged: n={len(df)}, "
          f"treatment_arm non-null: {df['treatment_arm'].notna().sum()}, "
          f"immune_subtype non-null: {df['immune_subtype'].notna().sum()}")

    print("\nRunning adjusted Cox models...")
    results = run_adjusted_cox(df, out_dir)

    print("\n" + "="*60)
    print("[G3] Adjusted Cox Results — TOP2A − EPAS1 score_z")
    print("="*60)
    m0 = results["model0_unadjusted"]
    m1 = results["model1_treatment_adjusted"]
    m2 = results["model2_treatment_tmb_adjusted"]
    m3 = results["model3_immune_subtype_adjusted"]
    m4 = results["model4_fully_adjusted"]
    kt = results["prereg_kill_test_verdicts"]

    def _fmt(m: dict) -> str:
        if "status" in m:
            return f"  [{m['status']}]"
        return (f"HR={m['score_z_hr']:.3f} "
                f"(95%CI {m['score_z_hr_ci_low']:.3f}-{m['score_z_hr_ci_high']:.3f}) "
                f"p={m['score_z_p']:.4f}  n={m['n']}")

    print(f"\nUnadjusted              {_fmt(m0)}")
    print(f"+ treatment arm         {_fmt(m1)}")
    print(f"+ immune subtype        {_fmt(m3)}")
    print(f"+ treatment+imm+TMB     {_fmt(m4)}")
    print(f"+ treatment + TMB only  {_fmt(m2)}")
    print(f"\nPre-reg kill-test verdicts:")
    for test_name, tv in kt.items():
        if test_name in ("overall_verdict", "feasibility_note"):
            continue
        if "status" in tv:
            print(f"  {test_name}: ⚠ {tv['status']}")
        else:
            status = "✅ PASS" if tv["pass"] else "❌ FAIL"
            print(f"  {test_name}: {status} HR={tv['hr']:.3f} "
                  f"(95%CI {tv['ci_low']:.3f}-{tv['ci_high']:.3f}) p={tv['p']:.4f}")
    print(f"\nOverall pre-reg verdict: {kt['overall_verdict']}")
    if kt.get("feasibility_note"):
        print(f"Feasibility note: {kt['feasibility_note']}")
    print(f"\nResults written to: {out_dir}/adjusted_cox.json")


if __name__ == "__main__":
    main()
