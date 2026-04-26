#!/usr/bin/env python3
"""PhL-8 — Claude Code Routines `/fire` live execution.

Fires the `lacuna-falsification-gate` Routine (configured
2026-04-23 in the claude.ai/code/routines UI) via the documented
`POST /v1/claude_code/routines/{trig_id}/fire` endpoint. Commits the
response JSON (including `claude_code_session_url` — the reviewer-
clickable artefact) to `results/live_evidence/phl8_routine_fire/`.

This is the Path C proof-of-life: `src/lacuna/routines_client.py`
has been in the repo as working code since commit 585ea0e, but without
a real fire call against a real routine it was just a tested HTTP
client with no on-disk live artefact. PhL-8 closes that gap.

Pre-requisites:
  - `CLAUDE_ROUTINE_TRIG_ID` and `CLAUDE_ROUTINE_TOKEN` in env
    (recommended: in ~/.api_keys, auto-loaded by the submit_h1.sh
    pattern).
  - The routine set up in claude.ai/code/routines with the Instructions
    block from `docs/submission_form_draft.md` (or equivalent).

Usage:
    PYTHONPATH=src .venv/bin/python src/phl8_routine_fire_live.py

Cost: whatever the routine run consumes server-side; per fire is
bounded by the routine's own runtime budget (our Instructions cap at
~3 min).
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from lacuna.routines_client import fire_routine_from_env

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "results" / "live_evidence" / "phl8_routine_fire"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    trig_id = os.environ.get("CLAUDE_ROUTINE_TRIG_ID", "").strip()
    token = os.environ.get("CLAUDE_ROUTINE_TOKEN", "").strip()
    if not trig_id or not token:
        print("ERROR: CLAUDE_ROUTINE_TRIG_ID and CLAUDE_ROUTINE_TOKEN must be "
              "set in the environment (recommend ~/.api_keys).", file=sys.stderr)
        return 2

    text_body = (
        "Fire from PhL-8 live smoke test. No candidate equation passed; "
        "run the standard verification pulse only (make venv, make audit, "
        "report canonical survivor)."
    )

    print(f">>> Firing routine trig_id={trig_id[:12]}... with text body.")
    t0 = time.time()
    result = fire_routine_from_env(text=text_body)
    elapsed = time.time() - t0

    print(f">>> Fire returned in {elapsed:.2f}s.")
    print(f"    http_status        = {result.http_status}")
    print(f"    type               = {result.type}")
    print(f"    session_id         = {result.session_id}")
    print(f"    session_url        = {result.session_url}")
    print(f"    normalized status  = {result.status}")

    artefact = {
        "hypothesis_id": "phl8_routine_fire_live",
        "fire_timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "routine_trig_id_prefix": trig_id[:12] + "...",
        "routine_trig_id_length": len(trig_id),
        "http_status": result.http_status,
        "type": result.type,
        "claude_code_session_id": result.session_id,
        "claude_code_session_url": result.session_url,
        "normalized_status": result.status,
        "fire_elapsed_seconds": round(elapsed, 3),
        "text_body_sent": text_body,
        "narrative": (
            "Live fire of the claude.ai/code/routines/"
            "lacuna-falsification-gate Routine via "
            "POST /v1/claude_code/routines/{trig_id}/fire. The "
            "claude_code_session_url in this artefact is the reviewer-"
            "clickable live session; the claude_code_session_id anchors "
            "the fire in Claude's backend log."
        ),
    }

    out_path = OUT_DIR / "fire_response.json"
    out_path.write_text(json.dumps(artefact, indent=2))
    print(f"\n>>> Wrote {out_path}")

    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
