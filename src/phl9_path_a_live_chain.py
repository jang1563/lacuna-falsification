#!/usr/bin/env python3
"""PhL-9 — Path A live evidence: 3-session sequential chain transcript.

Closes a real gap in the submission's evidence chain. The submission
docs claim Path A as a sequential 3-session chain (per the
2026-04-23 hackathon-fairness rule on research-preview Agent Teams),
but `results/live_evidence/04_managed_agents_e2e.log` only exercises
Path B (single session) and `06_managed_agents_path_a.log` is from
the pre-fix era. PhL-9 produces an on-disk full transcript of all
three sequential sessions running with the latest agent code +
post-review-handoff Instructions.

Calls `lacuna.managed_agent_runner.run_path_a(
night=2, fallback_on_no_waitlist=True)` which exercises the
`_run_path_a_sequential_fallback` branch — the actual public-beta-
compliant code path our submission claims uses.

Cost: ~$0.50 across 3 short Opus 4.7 sessions.
Usage:
    PYTHONPATH=src .venv/bin/python src/phl9_path_a_live_chain.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# Reuse the same managed_agent_runner.run_path_a entry point our
# submission cites — do not duplicate logic here.
from lacuna.managed_agent_runner import run_path_a

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "results" / "live_evidence" / "phl9_path_a_chain"


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY required (load via ~/.api_keys).",
              file=sys.stderr)
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(">>> Running Path A sequential 3-session chain (night=2)...")
    print(">>> This exercises _run_path_a_sequential_fallback — the")
    print(">>> public-beta-compliant code path our submission claims.")
    print(">>> Estimated wall time: ~3-5 minutes total across 3 sessions.")
    print()
    t0 = time.time()
    result = run_path_a(night=2, fallback_on_no_waitlist=True)
    elapsed = time.time() - t0

    print(f"\n>>> Chain complete in {elapsed:.1f}s.")
    print(f"    delegation_mode = {result.get('delegation_mode')}")
    print(f"    status          = {result.get('status')}")
    print(f"    last session_id = {result.get('session_id')}")
    print(f"    output (chars)  = {len(result.get('output', ''))}")

    # The output field is JSON dict of {role: agent_text} per the
    # _run_path_a_sequential_fallback code; preserve verbatim.
    try:
        per_role = json.loads(result.get("output", "{}"))
    except Exception:
        per_role = {"raw": result.get("output", "")}

    artefact = {
        "hypothesis_id": "phl9_path_a_live_chain",
        "run_date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "delegation_mode": result.get("delegation_mode"),
        "status": result.get("status"),
        "last_session_id": result.get("session_id"),
        "last_agent_id": result.get("agent_id"),
        "wall_seconds": round(elapsed, 1),
        "per_role_outputs": per_role,
        "narrative": (
            "Live execution of run_path_a(fallback_on_no_waitlist=True), "
            "the public-beta-compliant sequential 3-session chain "
            "(Proposer -> Searcher -> Skeptic) that our submission "
            "describes as Path A. Each session runs in its own Managed "
            "Agents session_id with its own agent_id; the chain is "
            "stitched on the client side via structured-JSON handoff "
            "in the prompt. NOT the research-preview callable_agents "
            "Agent Teams primitive (disabled for hackathon participants "
            "per 2026-04-23 fairness rule). The "
            "_run_path_a_callable_agents code path remains in the "
            "repo as architectural reference, env-flag-guarded."
        ),
    }
    (OUT_DIR / "verdict.json").write_text(json.dumps(artefact, indent=2, default=str))

    # Per-role full text (separate files for grep-ability)
    for role, text in per_role.items():
        (OUT_DIR / f"role_{role}.txt").write_text(str(text))

    print(f"\n>>> Artefacts written to {OUT_DIR}")
    print(f"    verdict.json + role_*.txt (per-role transcripts)")

    return 0 if result.get("status") == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
