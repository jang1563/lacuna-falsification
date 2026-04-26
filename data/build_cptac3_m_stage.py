"""Build CPTAC-3 ccRCC RNA expression + M-staging dataset and run TOP2A-EPAS1 gate.

Strategy:
- Step 1: Fetch sample IDs and TPM expression for TOP2A (7153) and EPAS1 (2034)
  from cBioPortal study rcc_cptac_gdc via molecular-data endpoint.
- Step 2: Fetch M-staging from GDC API (CPTAC-3 kidney cases).
  Use pathologic M first; fall back to clinical M if pathologic is MX/missing.
- Step 3: Merge on case_id (strip -NN suffix from sample IDs).
- Step 4: Run falsification gate: AUROC, permutation p, bootstrap CI,
  delta vs best single gene.
- Step 5: Save JSON result and print honest report.

Data sources:
- cBioPortal: https://www.cbioportal.org/api/ (public, no auth)
- GDC: https://api.gdc.cancer.gov/cases (public, no auth)

Clinical notes:
- Pathologic M: directly staged from primary surgery specimen
- Clinical M: pre-op imaging-based staging
- MX = "cannot be assessed" — excluded from analysis
- Stage IV can be T4/N0/M0 (not metastatic) — not used as M1 proxy

Gate pre-registration reference:
  preregistrations/ (see falsification.py for thresholds)
  Original TCGA-KIRC: AUROC 0.726, perm_p < 0.001, ci_lower 0.665, delta +0.069
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO / "results" / "track_a_task_landscape" / "external_replay" / "cptac3"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

RESULT_JSON = REPO / "results" / "track_a_task_landscape" / "external_replay" / "cptac3_gate_result.json"

CBIO_BASE = "https://www.cbioportal.org/api"
GDC_BASE = "https://api.gdc.cancer.gov"
STUDY_ID = "rcc_cptac_gdc"
PROFILE_TPM = "rcc_cptac_gdc_mrna_seq_tpm"
SAMPLE_LIST = "rcc_cptac_gdc_tpm"

TOP2A_ENTREZ = 7153
EPAS1_ENTREZ = 2034

# Pre-registered gate thresholds (matching falsification.py)
PERM_P_THRESH = 0.05
CI_LOWER_THRESH = 0.60
DELTA_BASELINE_THRESH = 0.05
N_M1_MIN = 10
N_PERM = 500
N_BOOT = 500


def _fetch_json(url: str, payload: dict | None = None, timeout: int = 30) -> dict | list:
    """Fetch JSON from URL with optional POST payload."""
    if payload is not None:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
    else:
        req = urllib.request.Request(url)

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def step1_fetch_expression() -> dict[str, dict]:
    """Fetch TOP2A and EPAS1 TPM expression from cBioPortal.

    Returns dict: sample_id -> {TOP2A: float, EPAS1: float}
    """
    print("[Step 1] Fetching TOP2A and EPAS1 TPM expression from cBioPortal...")

    expr: dict[str, dict] = {}

    for gene_name, entrez_id in [("TOP2A", TOP2A_ENTREZ), ("EPAS1", EPAS1_ENTREZ)]:
        url = (
            f"{CBIO_BASE}/molecular-profiles/{PROFILE_TPM}/molecular-data"
            f"?sampleListId={SAMPLE_LIST}&entrezGeneId={entrez_id}"
        )
        try:
            data = _fetch_json(url, timeout=60)
        except Exception as e:
            print(f"  ERROR fetching {gene_name}: {e}")
            return {}

        print(f"  {gene_name}: {len(data)} samples")
        for row in data:
            sid = row["sampleId"]
            val = row["value"]
            if sid not in expr:
                expr[sid] = {}
            expr[sid][gene_name] = float(val)

    # Keep only samples with both genes
    complete = {sid: vals for sid, vals in expr.items()
                if "TOP2A" in vals and "EPAS1" in vals}
    print(f"  Samples with both genes: {len(complete)}")
    return complete


def step2_fetch_m_staging() -> dict[str, str]:
    """Fetch M-staging for CPTAC-3 kidney cases from GDC.

    Strategy: use pathologic M first; fall back to clinical M if MX/None.
    Returns dict: case_id -> 'M0' | 'M1' (only known M-stage cases)
    """
    print("[Step 2] Fetching M-staging from GDC API...")

    payload = {
        "filters": {
            "op": "and",
            "content": [
                {"op": "in", "content": {"field": "project.project_id", "value": ["CPTAC-3"]}},
                {"op": "=", "content": {"field": "primary_site", "value": "Kidney"}}
            ]
        },
        "fields": (
            "submitter_id,diagnoses.ajcc_pathologic_m,"
            "diagnoses.ajcc_clinical_m,diagnoses.ajcc_pathologic_stage"
        ),
        "format": "JSON",
        "size": 500
    }

    try:
        result = _fetch_json(f"{GDC_BASE}/cases", payload=payload, timeout=60)
    except Exception as e:
        print(f"  ERROR fetching GDC cases: {e}")
        return {}

    hits = result.get("data", {}).get("hits", [])
    print(f"  Total CPTAC-3 kidney cases from GDC: {len(hits)}")

    m_stage_map: dict[str, str] = {}
    m_sources: list[str] = []
    m_counts: dict[str, int] = Counter()

    for case in hits:
        case_id = case.get("submitter_id", "")
        diags = case.get("diagnoses", [{}])
        d = diags[0] if diags else {}

        pm = d.get("ajcc_pathologic_m")  # pathologic M (more reliable)
        cm = d.get("ajcc_clinical_m")    # clinical M (imaging-based)

        # Priority: pathologic M > clinical M > unknown
        if pm and pm not in [None, "MX"]:
            m_final = pm
            m_sources.append("pathologic")
        elif cm and cm not in [None, "MX"]:
            m_final = cm
            m_sources.append("clinical")
        else:
            m_final = None
            m_sources.append("missing")

        m_counts[str(m_final)] += 1

        if m_final in ("M0", "M1"):
            m_stage_map[case_id] = m_final

    print(f"  M-stage distribution: {dict(m_counts)}")
    print(f"  M-source breakdown: {dict(Counter(m_sources))}")
    print(f"  Cases with known M-stage (M0 or M1): {len(m_stage_map)}")
    print(f"  M1: {sum(1 for v in m_stage_map.values() if v == 'M1')}, "
          f"M0: {sum(1 for v in m_stage_map.values() if v == 'M0')}")

    return m_stage_map


def _extract_case_id(sample_id: str) -> str:
    """Extract case_id from sample_id by stripping aliquot suffix.

    C3L-00004-01 -> C3L-00004
    C3N-01803-03 -> C3N-01803
    """
    parts = sample_id.split("-")
    if len(parts) >= 3:
        return "-".join(parts[:2])
    return sample_id


def step3_merge(
    expr: dict[str, dict],
    m_stage: dict[str, str]
) -> list[dict]:
    """Merge expression and M-staging on case_id, one sample per patient.

    cBioPortal sample IDs: C3L-00004-01 -> case_id = C3L-00004
    GDC case IDs: C3L-00004

    Multi-sample patients: select the sample with the lowest aliquot suffix
    to ensure exactly one row per patient (avoids inflating M1 count).
    """
    print("[Step 3] Merging expression and M-staging (one sample per patient)...")

    # Build case_id -> list of (sample_id, vals) pairs
    from collections import defaultdict
    case_to_samples: dict[str, list] = defaultdict(list)
    for sample_id, vals in expr.items():
        case_id = _extract_case_id(sample_id)
        case_to_samples[case_id].append((sample_id, vals))

    # For each case, pick the representative sample (lowest aliquot number)
    def aliquot_num(sample_id: str) -> int:
        parts = sample_id.rsplit("-", 1)
        try:
            return int(parts[-1]) if parts[-1].isdigit() else 999
        except Exception:
            return 999

    merged = []
    unmatched_expr_cases = 0
    unmatched_clinical = 0
    multi_sample_cases = 0

    for case_id, sample_list in case_to_samples.items():
        if case_id not in m_stage:
            unmatched_expr_cases += 1
            continue

        # Sort by aliquot suffix, pick lowest
        sample_list_sorted = sorted(sample_list, key=lambda x: aliquot_num(x[0]))
        if len(sample_list) > 1:
            multi_sample_cases += 1
        rep_sample_id, vals = sample_list_sorted[0]

        merged.append({
            "sample_id": rep_sample_id,
            "case_id": case_id,
            "n_samples_for_patient": len(sample_list),
            "TOP2A_tpm": vals["TOP2A"],
            "EPAS1_tpm": vals["EPAS1"],
            "m_stage_raw": m_stage[case_id],
            "m_stage": 1 if m_stage[case_id] == "M1" else 0
        })

    # Clinical cases without any expression sample
    matched_cases = set(r["case_id"] for r in merged)
    for case_id in m_stage:
        if case_id not in matched_cases:
            unmatched_clinical += 1

    print(f"  Unique patients with expression data: {len(case_to_samples)}")
    print(f"  Patients with M-staging matched: {len(merged)}")
    print(f"  Multi-sample patients (representative selected): {multi_sample_cases}")
    print(f"  Patients with expression but no M-staging: {unmatched_expr_cases}")
    print(f"  Clinical cases without expression: {unmatched_clinical}")

    m1_count = sum(r["m_stage"] for r in merged)
    m0_count = sum(1 - r["m_stage"] for r in merged)
    print(f"  M1 patients: {m1_count}, M0 patients: {m0_count}")

    return merged


def step4_run_gate(merged: list[dict]) -> dict:
    """Run the TOP2A-EPAS1 gate on merged data.

    Applies log1p(TPM + 0.001) transform, computes score = TOP2A - EPAS1,
    runs permutation null, bootstrap CI, and delta vs best single gene.
    """
    print("[Step 4] Running falsification gate...")

    m1_count = sum(r["m_stage"] for r in merged)
    m0_count = sum(1 - r["m_stage"] for r in merged)
    n_total = len(merged)

    if m1_count < N_M1_MIN:
        msg = (
            f"INSUFFICIENT M1 CASES: n(M1)={m1_count} < {N_M1_MIN} minimum. "
            "Gate cannot be run. Report as DATA_INSUFFICIENT."
        )
        print(f"  {msg}")
        return {
            "verdict": "DATA_INSUFFICIENT",
            "reason": msg,
            "n_total": n_total,
            "n_m1": m1_count,
            "n_m0": m0_count,
        }

    # Log1p transform: log1p(TPM + 0.001) to handle zeros
    top2a = np.log1p(np.array([r["TOP2A_tpm"] for r in merged]) + 0.001)
    epas1 = np.log1p(np.array([r["EPAS1_tpm"] for r in merged]) + 0.001)
    y = np.array([r["m_stage"] for r in merged])

    # Score: TOP2A - EPAS1
    score = top2a - epas1

    # Compute AUROC
    def auroc(y_true, scores):
        from sklearn.metrics import roc_auc_score
        try:
            return roc_auc_score(y_true, scores)
        except Exception:
            return 0.5

    try:
        from sklearn.metrics import roc_auc_score
        from sklearn.utils import resample
    except ImportError:
        print("  ERROR: sklearn not available")
        return {"verdict": "ERROR", "reason": "sklearn not installed"}

    auc_raw = roc_auc_score(y, score)
    auc = max(auc_raw, 1.0 - auc_raw)
    direction_preserved = auc_raw > 0.5  # True if high score -> more M1
    print(f"  AUROC (raw): {auc_raw:.3f}, sign-invariant: {auc:.3f}")
    print(f"  Direction preserved (high TOP2A-EPAS1 -> M1): {direction_preserved}")

    # Permutation null (two-sided: |null - 0.5| >= |observed - 0.5|)
    print(f"  Running {N_PERM} permutation shuffles...")
    rng = np.random.RandomState(42)
    null_aucs = []
    obs_excess = abs(auc - 0.5)
    n_exceeds = 0
    for _ in range(N_PERM):
        y_shuf = rng.permutation(y)
        a_raw = roc_auc_score(y_shuf, score)
        a = max(a_raw, 1.0 - a_raw)
        null_aucs.append(a)
        if abs(a - 0.5) >= obs_excess:
            n_exceeds += 1
    perm_p = n_exceeds / N_PERM
    null_aucs_arr = np.array(null_aucs)
    print(f"  Permutation p: {perm_p:.4f} (threshold < {PERM_P_THRESH})")

    # Bootstrap CI (500 resamples)
    print(f"  Running {N_BOOT} bootstrap resamples...")
    boot_aucs = []
    n_samples = len(y)
    for i in range(N_BOOT):
        idx = rng.choice(n_samples, size=n_samples, replace=True)
        y_b = y[idx]
        s_b = score[idx]
        if len(np.unique(y_b)) < 2:
            continue
        a_raw = roc_auc_score(y_b, s_b)
        a = max(a_raw, 1.0 - a_raw)
        boot_aucs.append(a)

    ci_lower = np.percentile(boot_aucs, 2.5) if boot_aucs else 0.5
    ci_upper = np.percentile(boot_aucs, 97.5) if boot_aucs else 0.5
    print(f"  Bootstrap 95% CI: [{ci_lower:.3f}, {ci_upper:.3f}] (lower threshold > {CI_LOWER_THRESH})")

    # Best single gene (sign-invariant)
    auc_top2a_raw = roc_auc_score(y, top2a)
    auc_top2a = max(auc_top2a_raw, 1.0 - auc_top2a_raw)
    auc_epas1_raw = roc_auc_score(y, epas1)
    auc_epas1 = max(auc_epas1_raw, 1.0 - auc_epas1_raw)
    best_single = max(auc_top2a, auc_epas1)
    delta_baseline = auc - best_single
    print(f"  TOP2A single: {auc_top2a:.3f}, EPAS1 single: {auc_epas1:.3f}")
    print(f"  Best single: {best_single:.3f}, Delta: {delta_baseline:+.3f} (threshold > {DELTA_BASELINE_THRESH})")

    # Determine verdict
    fails = []
    passes = []

    if perm_p < PERM_P_THRESH:
        passes.append(f"perm_p={perm_p:.4f} < {PERM_P_THRESH}")
    else:
        fails.append(f"perm_p={perm_p:.4f} >= {PERM_P_THRESH}")

    if ci_lower > CI_LOWER_THRESH:
        passes.append(f"ci_lower={ci_lower:.3f} > {CI_LOWER_THRESH}")
    else:
        fails.append(f"ci_lower={ci_lower:.3f} <= {CI_LOWER_THRESH}")

    if delta_baseline > DELTA_BASELINE_THRESH:
        passes.append(f"delta_baseline={delta_baseline:+.3f} > {DELTA_BASELINE_THRESH}")
    else:
        fails.append(f"delta_baseline={delta_baseline:+.3f} <= {DELTA_BASELINE_THRESH}")

    if len(fails) == 0:
        verdict = "PASS"
    elif len(passes) >= 2 and len(fails) == 1:
        verdict = "ATTENUATED"
    else:
        verdict = "FAIL"

    print(f"\n  VERDICT: {verdict}")
    print(f"  PASSES: {passes}")
    print(f"  FAILS: {fails}")

    return {
        "verdict": verdict,
        "n_total": n_total,
        "n_m1": int(m1_count),
        "n_m0": int(m0_count),
        "auroc": round(float(auc), 4),
        "auroc_raw": round(float(auc_raw), 4),
        "direction_preserved": bool(direction_preserved),
        "perm_p": round(float(perm_p), 4),
        "perm_p_pass": bool(perm_p < PERM_P_THRESH),
        "ci_lower": round(float(ci_lower), 4),
        "ci_upper": round(float(ci_upper), 4),
        "ci_lower_pass": bool(ci_lower > CI_LOWER_THRESH),
        "delta_baseline": round(float(delta_baseline), 4),
        "delta_baseline_pass": bool(delta_baseline > DELTA_BASELINE_THRESH),
        "best_single_gene_auroc": round(float(best_single), 4),
        "top2a_single_auroc": round(float(auc_top2a), 4),
        "epas1_single_auroc": round(float(auc_epas1), 4),
        "null_auroc_mean": round(float(null_aucs_arr.mean()), 4),
        "null_auroc_95th": round(float(np.percentile(null_aucs_arr, 95)), 4),
        "passes": passes,
        "fails": fails,
        "n_boot_valid": len(boot_aucs),
    }


def main():
    print("=" * 60)
    print("CPTAC-3 ccRCC RNA + M-staging: TOP2A-EPAS1 gate")
    print("=" * 60)

    # Step 1: Expression
    expr = step1_fetch_expression()
    if not expr:
        result = {
            "verdict": "DATA_FETCH_ERROR",
            "reason": "Failed to fetch expression data from cBioPortal",
            "cohort": "CPTAC-3 ccRCC (rcc_cptac_gdc)",
            "law": "TOP2A - EPAS1",
        }
        _save_and_print(result)
        return

    # Step 2: M-staging
    m_stage = step2_fetch_m_staging()
    if not m_stage:
        result = {
            "verdict": "DATA_FETCH_ERROR",
            "reason": "Failed to fetch M-staging data from GDC",
            "cohort": "CPTAC-3 ccRCC (rcc_cptac_gdc)",
            "law": "TOP2A - EPAS1",
        }
        _save_and_print(result)
        return

    # Step 3: Merge
    merged = step3_merge(expr, m_stage)

    if not merged:
        result = {
            "verdict": "DATA_INSUFFICIENT",
            "reason": "No samples matched between expression and clinical",
            "n_expression": len(expr),
            "n_clinical": len(m_stage),
        }
        _save_and_print(result)
        return

    # Step 4: Gate
    gate_result = step4_run_gate(merged)

    # Combine into final result
    result = {
        "cohort": "CPTAC-3 ccRCC (rcc_cptac_gdc via cBioPortal)",
        "law": "TOP2A - EPAS1",
        "transform": "log1p(TPM + 0.001)",
        "m_staging_strategy": (
            "GDC pathologic M preferred; fall back to clinical M if pathologic is MX/missing. "
            "MX excluded from analysis."
        ),
        "reference_tcga_kirc": {
            "auroc": 0.726,
            "perm_p": "<0.001",
            "ci_lower": 0.665,
            "delta_baseline": 0.069,
            "n_m1": 81,
            "n_m0": 424,
            "n_total": 505
        },
        "gate_thresholds": {
            "perm_p": f"< {PERM_P_THRESH}",
            "ci_lower": f"> {CI_LOWER_THRESH}",
            "delta_baseline": f"> {DELTA_BASELINE_THRESH}",
            "n_m1_min": N_M1_MIN
        },
        **gate_result
    }

    _save_and_print(result)


def _save_and_print(result: dict):
    """Save result to JSON and print summary."""
    RESULT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULT_JSON, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nResult saved to: {RESULT_JSON}")

    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
