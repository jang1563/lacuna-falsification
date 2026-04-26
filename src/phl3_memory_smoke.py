#!/usr/bin/env python3
"""PhL-3 — Managed Agents Memory (public beta, launched 2026-04-23) smoke test.

Memory moved from research preview to public beta on 2026-04-23 (same day
as this commit cycle). Per the Cerebral Valley × Anthropic hackathon
fairness rule (public-beta features ARE allowed; only research-preview
features are disabled for participants), we can use Memory in the
submission.

This smoke test demonstrates the exact Rakuten-style "agents distill
lessons from every session" pattern, applied to our falsification
pipeline: a Skeptic agent in session 1 writes a rejection-pattern lesson
to `/mnt/memory/skeptic-lessons/lessons.md`; a separate session 2 (same agent,
same memory store, different session id) reads the lesson and applies it
to a new candidate.

Why this matters for the submission:
- It is the Cat Wu 2026-04-23 Lenny's-Newsletter pattern: "model
  introspects on its own mistakes" — literally as a durable file.
- It is the Boris Cherny "skill that ships" pattern: the Skeptic's
  `skeptic_lessons.md` is a shareable artefact, not prompt state.
- It is the direct answer to Thariq Shihipar's 2026-04-22 open question
  on verification loops — memory is how the loop closes across sessions.

Implementation notes:
- The installed `anthropic==0.96.0` SDK (2026-04-16) does NOT yet expose
  `client.beta.memory_stores`. Resources at session.create are forwarded
  as raw JSON dicts (`resources=[{"type": "memory_store", ...}]`) so the
  runtime API accepts them despite the SDK type-checker complaint.
- Memory CRUD uses raw httpx against `/v1/memory_stores/*` with the
  standard `managed-agents-2026-04-01` beta header.
- First run creates + caches the agent, env, and memory store IDs to
  `results/live_evidence/phl3_state.json` so the second invocation
  reuses them. Pass `--clean` to wipe state and start fresh.

Cost: ~$0.30 for two Opus 4.7 sessions + $0.08/session-hour runtime.
Usage:
    python src/phl3_memory_smoke.py write   # session 1: write lesson
    python src/phl3_memory_smoke.py read    # session 2: read + apply
    python src/phl3_memory_smoke.py verify  # server-side dump of memories
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx
import anthropic

API_BASE = "https://api.anthropic.com"
BETA_HEADER = "managed-agents-2026-04-01"
MODEL = "claude-opus-4-7"

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = REPO_ROOT / "results" / "live_evidence" / "phl3_state.json"
LOG_DIR = REPO_ROOT / "results" / "live_evidence" / "phl3_memory_smoke"


def _headers() -> dict[str, str]:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise SystemExit("ANTHROPIC_API_KEY not set")
    return {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": BETA_HEADER,
        "content-type": "application/json",
    }


def _load_or_create_state(client: anthropic.Anthropic) -> dict:
    if STATE_PATH.exists():
        state = json.loads(STATE_PATH.read_text())
        print(f">>> Reusing cached agent/env/store from {STATE_PATH}")
        print(f"    agent_id    = {state['agent_id']}")
        print(f"    env_id      = {state['env_id']}")
        print(f"    store_id    = {state['store_id']}")
        return state

    print(">>> First run — creating agent / environment / memory store ...")

    agent = client.beta.agents.create(
        name="lacuna-skeptic-memory",
        model=MODEL,
        system=(
            "You are a falsification-first scientific Skeptic. The memory store "
            "is MOUNTED AT `/mnt/memory/skeptic-lessons/` — files you create "
            "under THAT directory persist across sessions; files outside it are "
            "ephemeral container scratch. Before judging any new candidate law "
            "you MUST read "
            "`/mnt/memory/skeptic-lessons/lessons.md` (create it if absent). "
            "When you finish judging, APPEND a 1-2 line lesson to "
            "`/mnt/memory/skeptic-lessons/lessons.md` summarising the pattern "
            "you encountered, so the next session benefits. Always cite "
            "specific prior rejections by their exact equation text when "
            "applying prior lessons to a new candidate."
        ),
        tools=[{"type": "agent_toolset_20260401"}],
    )
    print(f"    agent_id    = {agent.id}")

    environment = client.beta.environments.create(
        name="lacuna-phl3-env",
        config={"type": "cloud", "networking": {"type": "unrestricted"}},
    )
    print(f"    env_id      = {environment.id}")

    # Memory store creation — raw httpx since SDK 0.96.0 lacks memory_stores.
    with httpx.Client(timeout=30.0) as cli:
        resp = cli.post(
            f"{API_BASE}/v1/memory_stores",
            headers=_headers(),
            json={
                "name": "skeptic-lessons",
                "description": (
                    "Rejection-pattern lessons the Lacuna Skeptic agent "
                    "accumulates across sessions — each entry cites the specific "
                    "equation + fail_reason so future Skeptic sessions can apply "
                    "the same bar."
                ),
            },
        )
        resp.raise_for_status()
        store = resp.json()
    print(f"    store_id    = {store['id']}")

    state = {
        "agent_id": agent.id,
        "env_id": environment.id,
        "store_id": store["id"],
        "created_at": int(time.time()),
    }
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2))
    return state


def _run_session(
    client: anthropic.Anthropic,
    state: dict,
    prompt: str,
    title: str,
) -> dict:
    session = client.beta.sessions.create(
        agent=state["agent_id"],
        environment_id=state["env_id"],
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": state["store_id"],
                "access": "read_write",
                "instructions": (
                    "Accumulated rejection-pattern lessons from prior Skeptic "
                    "sessions. Read /mnt/memory/skeptic-lessons/lessons.md BEFORE "
                    "judging the new candidate; APPEND a 1-2 line lesson "
                    "summary AFTER judging, so this memory compounds across "
                    "sessions."
                ),
            }
        ],
        title=title,
    )
    print(f">>> Session created: {session.id}")

    transcript: list[dict] = []
    tool_uses: list[dict] = []
    agent_text_parts: list[str] = []

    try:
        with client.beta.sessions.events.stream(session.id) as stream:
            client.beta.sessions.events.send(
                session.id,
                events=[
                    {
                        "type": "user.message",
                        "content": [{"type": "text", "text": prompt}],
                    }
                ],
            )
            for event in stream:
                etype = getattr(event, "type", "")
                # Best-effort serialize
                try:
                    dump = event.model_dump()
                except Exception:
                    dump = {"type": etype}
                transcript.append(dump)

                if etype == "agent.message":
                    for block in getattr(event, "content", []) or []:
                        text = getattr(block, "text", "") or ""
                        if text:
                            agent_text_parts.append(text)
                elif etype == "agent.tool_use":
                    tool_uses.append(dump)
                elif etype in ("session.status_idle",
                               "session.status_terminated",
                               "session.error"):
                    break
    except Exception as exc:
        print(f"  Stream exception: {exc!r}")

    return {
        "session_id": session.id,
        "agent_text": "".join(agent_text_parts),
        "tool_uses": tool_uses,
        "event_count": len(transcript),
        "transcript": transcript,
    }


def _dump_memory_server_side(state: dict) -> list[dict]:
    """List + fetch every memory in the store — independent verification."""
    with httpx.Client(timeout=30.0) as cli:
        resp = cli.get(
            f"{API_BASE}/v1/memory_stores/{state['store_id']}/memories",
            headers=_headers(),
            params={"path_prefix": "/"},
        )
        resp.raise_for_status()
        listing = resp.json()
        entries = listing.get("data", [])

        full: list[dict] = []
        for entry in entries:
            r = cli.get(
                f"{API_BASE}/v1/memory_stores/{state['store_id']}/memories/{entry['id']}",
                headers=_headers(),
            )
            r.raise_for_status()
            detail = r.json()
            full.append(
                {
                    "id": detail.get("id"),
                    "path": detail.get("path"),
                    "content_sha256": detail.get("content_sha256"),
                    "content": detail.get("content", ""),
                }
            )
        return full


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "write"
    if "--clean" in sys.argv:
        if STATE_PATH.exists():
            STATE_PATH.unlink()
            print(f"Cleaned {STATE_PATH}")
        return 0

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    client = anthropic.Anthropic()
    state = _load_or_create_state(client)

    if mode == "write":
        candidate_eq = "log1p(CA9) + log1p(VEGFA) - log1p(AGXT)"
        metrics = {
            "law_auc": 0.984,
            "baseline_auc_best_single_gene": 0.965,  # CA9 alone
            "delta_baseline": 0.019,   # < threshold 0.05
            "perm_p": 0.001,
            "ci_lower": 0.95,
            "decoy_p": 0.01,
            "cohort": "TCGA-KIRC tumor-vs-normal",
        }
        prompt = (
            "## Task\n"
            "Judge this candidate biological law against the pre-registered "
            "5-test falsification gate. After judging, APPEND a 1-2 line "
            "lesson to /mnt/memory/skeptic-lessons/lessons.md summarising the pattern "
            "so the next Skeptic session can apply it.\n\n"
            f"## Candidate equation\n`{candidate_eq}`\n\n"
            f"## Gate metrics\n```json\n{json.dumps(metrics, indent=2)}\n```\n\n"
            "## Gate thresholds\n"
            "- perm_p < 0.05\n"
            "- ci_lower > 0.6\n"
            "- delta_baseline > 0.05 (compound must beat best single gene by +0.05)\n"
            "- decoy_p < 0.05\n\n"
            "Return PASS / FAIL / NEEDS_MORE_TESTS with a short reason, then "
            "append the lesson."
        )
        result = _run_session(client, state, prompt, "PhL-3 session 1 — write lesson")
        out = LOG_DIR / "session1_write.json"

    elif mode == "read":
        candidate_eq = "log1p(LDHA) + log1p(SLC2A1) - log1p(ALB)"
        metrics = {
            "law_auc": 0.978,
            "baseline_auc_best_single_gene": 0.959,  # LDHA dominant
            "delta_baseline": 0.019,  # same pattern — just under threshold
            "perm_p": 0.001,
            "ci_lower": 0.94,
            "decoy_p": 0.02,
            "cohort": "TCGA-KIRC tumor-vs-normal",
        }
        prompt = (
            "## Task\n"
            "Judge this NEW candidate law. BEFORE judging, READ "
            "/mnt/memory/skeptic-lessons/lessons.md and cite any prior lesson that "
            "applies. After judging, append a new lesson if this candidate "
            "reveals a pattern the memory did not yet capture.\n\n"
            f"## Candidate equation\n`{candidate_eq}`\n\n"
            f"## Gate metrics\n```json\n{json.dumps(metrics, indent=2)}\n```\n\n"
            "## Gate thresholds\n"
            "- perm_p < 0.05\n"
            "- ci_lower > 0.6\n"
            "- delta_baseline > 0.05\n"
            "- decoy_p < 0.05\n\n"
            "Return PASS / FAIL / NEEDS_MORE_TESTS. If you invoke a prior "
            "lesson from memory, QUOTE the exact lesson text. Then append."
        )
        result = _run_session(client, state, prompt, "PhL-3 session 2 — read + apply")
        out = LOG_DIR / "session2_read.json"

    elif mode == "verify":
        dump = _dump_memory_server_side(state)
        out = LOG_DIR / "server_dump.json"
        out.write_text(json.dumps(dump, indent=2))
        print(f"\n>>> Memory store {state['store_id']} contains "
              f"{len(dump)} memory file(s):")
        for m in dump:
            print(f"    {m['path']}  ({m['content_sha256'][:16]}...)")
            print("    ---")
            print("    " + (m["content"] or "").strip().replace("\n", "\n    "))
            print()
        return 0

    else:
        print(f"Unknown mode: {mode}", file=sys.stderr)
        return 2

    # Save transcript + print agent text summary.
    out.write_text(json.dumps(result, indent=2, default=str))
    print(f"\n>>> Session complete. {result['event_count']} events captured.")
    print(f">>> {len(result['tool_uses'])} tool-use events.")
    print(f">>> Transcript: {out}")
    print(f"\n=== Agent response (first 2000 chars) ===\n")
    print(result["agent_text"][:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
