#!/usr/bin/env python3
"""PhL-8c — Scientific Oracle Routine live execution.

Fires the `lacuna-scientific-oracle` Routine via API trigger with
an equation for autonomous falsification.

Pre-requisites:
  - `CLAUDE_ROUTINE_TRIG_ID` and `CLAUDE_ROUTINE_TOKEN` in env:
      export CLAUDE_ROUTINE_TRIG_ID=trig_01XXXXXXXXXXXXXXXXXXXXXXXXXX
      export CLAUDE_ROUTINE_TOKEN=sk-ant-...
  - Or store them in ~/.api_keys and source that file first.

Usage:
    cd theory_copilot_discovery/
    export CLAUDE_ROUTINE_TRIG_ID=trig_01...
    export CLAUDE_ROUTINE_TOKEN=sk-ant-...
    PYTHONPATH=src .venv/bin/python src/phl8c_scientific_oracle_fire.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from lacuna.routines_client import fire_routine_from_env

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "results" / "live_evidence" / "phl8c_scientific_oracle"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    trig_id = os.environ.get("CLAUDE_ROUTINE_TRIG_ID", "").strip()
    token = os.environ.get("CLAUDE_ROUTINE_TOKEN", "").strip()
    if not trig_id or not token:
        print(
            "ERROR: Set CLAUDE_ROUTINE_TRIG_ID and CLAUDE_ROUTINE_TOKEN in env.\n"
            "  export CLAUDE_ROUTINE_TRIG_ID=trig_01XXXXX...\n"
            "  export CLAUDE_ROUTINE_TOKEN=sk-ant-...\n"
            "Do NOT hardcode tokens in this file.",
            file=sys.stderr,
        )
        return 2

    # CDK1 - EPAS1: Rashomon-set rank 2 (AUROC 0.7192, delta_baseline expected PASS)
    # Same proliferation-minus-HIF2a axis as canonical TOP2A - EPAS1 survivor.
    text_body = "equation: CDK1 - EPAS1"

    print(f">>> Firing scientific oracle routine  trig_id={trig_id[:12]}...")
    print(f">>> Equation: {text_body}")
    t0 = time.time()
    result = fire_routine_from_env(text=text_body)
    elapsed = time.time() - t0

    print(f">>> Fire returned in {elapsed:.2f}s")
    print(f"    http_status  = {result.http_status}")
    print(f"    session_id   = {result.session_id}")
    print(f"    session_url  = {result.session_url}")
    print(f"    status       = {result.status}")

    artefact = {
        "hypothesis_id": "phl8c_scientific_oracle",
        "fire_timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "routine_name": "lacuna-scientific-oracle",
        "routine_trig_id_prefix": trig_id[:12] + "...",
        "routine_trig_id_length": len(trig_id),
        "trigger_type": "api",
        "equation_submitted": text_body,
        "http_status": result.http_status,
        "claude_code_session_id": result.session_id,
        "claude_code_session_url": result.session_url,
        "normalized_status": result.status,
        "fire_elapsed_seconds": round(elapsed, 3),
        "narrative": (
            "API-triggered fire of lacuna-scientific-oracle routine. "
            "Routine runs make venv + make audit + falsification_sweep.py "
            "on the submitted equation, then reports PASS/FAIL verdict "
            "with all 5 test metrics. Session output is the first "
            "autonomous scientific falsification run by a Claude Code Routine."
        ),
    }

    out_path = OUT_DIR / "fire_response.json"
    out_path.write_text(json.dumps(artefact, indent=2))
    print(f"\n>>> Wrote {out_path}")
    print(f"\n>>> Open session in browser:")
    print(f"    {result.session_url}")
    print(f"\n>>> Wait ~4-5 min for the routine to complete, then:")
    print(f"    Copy the session URL above and paste back here.")

    return 0 if result.status in ("completed", "running") else 1


if __name__ == "__main__":
    raise SystemExit(main())
