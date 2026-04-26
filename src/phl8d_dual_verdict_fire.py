#!/usr/bin/env python3
"""PhL-8d — Dual Verdict Oracle: FAIL + PASS in one autonomous session.

Fires the `lacuna-scientific-oracle` Routine with two equations:
  - Eq1 (expected FAIL): log1p(CA9)+log1p(VEGFA)-log1p(AGXT) on tumor_vs_normal
    CA9 alone = AUROC 0.965; delta_baseline ≈ +0.019 < 0.05 threshold.
  - Eq2 (expected PASS): CDK1 - EPAS1 on metastasis_expanded
    Rashomon rank 2 (AUROC 0.719); delta_baseline ≈ +0.062 > 0.05.

One API call → one session URL → the entire Lacuna narrative:
textbook HIF-axis rejected AND proliferation contrast accepted, same gate,
same thresholds, same 4-minute session.

Pre-requisites:
  - Update the `lacuna-scientific-oracle` Routine Instructions in the web UI
    to the dual-equation version from:
      routines/2026_04_26/lacuna_oracle_dual_instructions.md
  - Set env vars:
      export CLAUDE_ROUTINE_TRIG_ID=trig_01...
      export CLAUDE_ROUTINE_TOKEN=sk-ant-...

Usage:
    cd theory_copilot_discovery/
    export CLAUDE_ROUTINE_TRIG_ID=trig_01...
    export CLAUDE_ROUTINE_TOKEN=sk-ant-...
    PYTHONPATH=src .venv/bin/python src/phl8d_dual_verdict_fire.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from lacuna.routines_client import fire_routine_from_env

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "results" / "live_evidence" / "phl8d_dual_verdict"

# Eq1: textbook HIF-axis (expected FAIL — CA9 saturates delta_baseline)
# Eq2: Rashomon rank 2 (expected PASS — proliferation-minus-HIF2a axis)
DUAL_TRIGGER = (
    "eq1: task=tumor_vs_normal, data=kirc_tumor_normal.csv, "
    "equation=log1p(CA9) + log1p(VEGFA) - log1p(AGXT)\n"
    "eq2: task=metastasis_expanded, data=kirc_metastasis_expanded.csv, "
    "equation=CDK1 - EPAS1"
)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    trig_id = os.environ.get("CLAUDE_ROUTINE_TRIG_ID", "").strip()
    token = os.environ.get("CLAUDE_ROUTINE_TOKEN", "").strip()
    if not trig_id or not token:
        print(
            "ERROR: Set CLAUDE_ROUTINE_TRIG_ID and CLAUDE_ROUTINE_TOKEN in env.\n"
            "  export CLAUDE_ROUTINE_TRIG_ID=trig_01XXXXX...\n"
            "  export CLAUDE_ROUTINE_TOKEN=sk-ant-...\n"
            "Do NOT hardcode tokens in this file.\n\n"
            "Also: ensure the Routine Instructions in claude.ai/code/routines\n"
            "match the dual-equation version in:\n"
            "  routines/2026_04_26/lacuna_oracle_dual_instructions.md",
            file=sys.stderr,
        )
        return 2

    print(">>> Firing dual-verdict oracle")
    print(">>> Eq1 (expected FAIL): log1p(CA9)+log1p(VEGFA)-log1p(AGXT)  [tumor_vs_normal]")
    print(">>> Eq2 (expected PASS): CDK1 - EPAS1  [metastasis_expanded]")
    print()

    t0 = time.time()
    result = fire_routine_from_env(text=DUAL_TRIGGER)
    elapsed = time.time() - t0

    print(f">>> Fire returned in {elapsed:.2f}s")
    print(f"    http_status  = {result.http_status}")
    print(f"    session_id   = {result.session_id}")
    print(f"    session_url  = {result.session_url}")
    print(f"    status       = {result.status}")

    artefact = {
        "hypothesis_id": "phl8d_dual_verdict",
        "fire_timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "routine_name": "lacuna-scientific-oracle",
        "routine_trig_id_prefix": trig_id[:12] + "...",
        "routine_trig_id_length": len(trig_id),
        "trigger_type": "api",
        "trigger_text": DUAL_TRIGGER,
        "http_status": result.http_status,
        "claude_code_session_id": result.session_id,
        "claude_code_session_url": result.session_url,
        "normalized_status": result.status,
        "fire_elapsed_seconds": round(elapsed, 3),
        "eq1": {
            "task": "tumor_vs_normal",
            "data": "kirc_tumor_normal.csv",
            "equation": "log1p(CA9) + log1p(VEGFA) - log1p(AGXT)",
            "expected_gate": "FAIL",
            "expected_fail_reason": "delta_baseline (CA9 alone = AUROC 0.965; delta ≈ +0.019 < 0.05)",
        },
        "eq2": {
            "task": "metastasis_expanded",
            "data": "kirc_metastasis_expanded.csv",
            "equation": "CDK1 - EPAS1",
            "expected_gate": "PASS",
            "expected_metrics": "perm_p≈0.0, ci_lower≈0.664, delta_baseline≈+0.062",
        },
        "narrative": (
            "Dual-verdict API fire of lacuna-scientific-oracle routine. "
            "Eq1 (textbook HIF-axis) expected FAIL on tumor_vs_normal "
            "(CA9 saturates delta_baseline). "
            "Eq2 (CDK1-EPAS1, Rashomon rank 2) expected PASS on metastasis_expanded. "
            "One session URL = the entire Lacuna narrative: pre-registered gate "
            "rejects textbook law AND accepts proliferation contrast, same thresholds."
        ),
    }

    out_path = OUT_DIR / "fire_response.json"
    out_path.write_text(json.dumps(artefact, indent=2))
    print(f"\n>>> Wrote {out_path}")
    print(f"\n>>> Open session in browser (wait ~6-8 min for both gates to complete):")
    print(f"    {result.session_url}")
    print(f"\n>>> After session completes:")
    print(f"    1. Copy the full session output (both ===GATE VERDICT=== blocks)")
    print(f"    2. Update results/live_evidence/phl8d_dual_verdict/SUMMARY.md")
    print(f"       with the session output and update artefact session_gate fields")

    return 0 if result.status in ("completed", "running") else 1


if __name__ == "__main__":
    raise SystemExit(main())
