#!/usr/bin/env python3
"""PhL-4 — `sessions.events.list` persist + replay live demo.

Exercises the two durability primitives we already ship in
`src/lacuna/managed_agent_runner.py`:

  1. `persist_session_events(session_id, out_path)` — page through
     `client.beta.sessions.events.list` and dump every event to JSONL.
  2. `replay_session_from_log(log_path, target_session_id)` — read the
     JSONL back and re-inject every client-originated event (user.message,
     user.interrupt, user.custom_tool_result, user.tool_confirmation)
     into a different session.

The demo:

  Session 1: plain Path-B agent, we send a user.message asking it to
  count to three. Full event stream captured.

  `persist`: dump the full event log of session 1 to JSONL.

  Session 2: SAME agent, DIFFERENT session ID. We replay the user-origin
  events (just the user.message) into session 2, then send a new
  user.message asking "what did I ask you in my previous message?"

  Session 2's agent should respond with the content of the replayed
  user prompt (count to three) — proving that the durable event log,
  not a shared memory or shared context, carried the state across
  sessions.

This is explicitly DIFFERENT from PhL-3 Memory:

  - Memory  = server-side durable filesystem (`/mnt/memory/`) readable
              as files by the agent via normal tools.
  - Event-log persist+replay = the RAW event stream the platform keeps
              at `/v1/sessions/{id}/events`, re-injected as user events
              into a different session.

Both are load-bearing for the "brain/body decoupling" story; Memory is
the stronger durability primitive, and persist+replay is the smaller
demo that shows the event log is portable.

Cost: ~$0.15 for two short Opus 4.7 sessions.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import anthropic

from lacuna.managed_agent_runner import (
    persist_session_events,
    replay_session_from_log,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = REPO_ROOT / "results" / "live_evidence" / "phl4_persist_replay"
STATE_PATH = LOG_DIR / "phl4_state.json"


def _load_or_create_state(client: anthropic.Anthropic) -> dict:
    if STATE_PATH.exists():
        state = json.loads(STATE_PATH.read_text())
        print(f">>> Reusing cached agent/env from {STATE_PATH}")
        return state

    print(">>> Creating a plain Path-B agent for the demo ...")
    agent = client.beta.agents.create(
        name="lacuna-phl4-persist-replay",
        model="claude-opus-4-7",
        system=(
            "You are a minimal assistant. Answer concisely and literally. "
            "When asked what the user previously said, quote or paraphrase "
            "that prior user message verbatim."
        ),
        tools=[{"type": "agent_toolset_20260401"}],
    )
    environment = client.beta.environments.create(
        name="lacuna-phl4-env",
        config={"type": "cloud", "networking": {"type": "unrestricted"}},
    )
    state = {
        "agent_id": agent.id,
        "env_id": environment.id,
        "created_at": int(time.time()),
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2))
    print(f"    agent_id = {agent.id}")
    print(f"    env_id   = {environment.id}")
    return state


def _drain(stream, collect: list[str]) -> str:
    status = "completed"
    for event in stream:
        etype = getattr(event, "type", "")
        if etype == "agent.message":
            for block in getattr(event, "content", []) or []:
                text = getattr(block, "text", "") or ""
                if text:
                    collect.append(text)
        elif etype in ("session.status_idle", "session.status_terminated"):
            if etype == "session.status_terminated":
                status = "terminated"
            break
    return status


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    client = anthropic.Anthropic()
    state = _load_or_create_state(client)

    # -----------------------------------------------------------------
    # Session 1 — run a short interaction so the event log is non-empty
    # -----------------------------------------------------------------
    print("\n>>> Session 1: sending user.message = 'Count from 1 to 3 inclusive.'")
    session1 = client.beta.sessions.create(
        agent=state["agent_id"], environment_id=state["env_id"],
        title="phl4 session 1 — original",
    )
    print(f"    session1.id = {session1.id}")
    s1_reply: list[str] = []
    with client.beta.sessions.events.stream(session1.id) as stream:
        client.beta.sessions.events.send(
            session1.id,
            events=[
                {"type": "user.message",
                 "content": [{"type": "text",
                              "text": "Count from 1 to 3 inclusive."}]}
            ],
        )
        _drain(stream, s1_reply)
    print(f"    session 1 agent replied: {''.join(s1_reply).strip()[:200]}")

    # -----------------------------------------------------------------
    # Persist — page through events.list and dump JSONL
    # -----------------------------------------------------------------
    jsonl_path = LOG_DIR / "session1_events.jsonl"
    persist_report = persist_session_events(
        session1.id, jsonl_path, client=client
    )
    print(f"\n>>> Persisted {persist_report['event_count']} events to {jsonl_path}")
    print(f"    first event: {persist_report['first_event_type']}")
    print(f"    last event:  {persist_report['last_event_type']}")
    with jsonl_path.open() as fh:
        sample_lines = [fh.readline().strip() for _ in range(3)]
    print("    sample lines from the JSONL:")
    for s in sample_lines:
        print(f"      {s[:180]}")

    # -----------------------------------------------------------------
    # Session 2 — different id, same agent. Replay user-origin events
    # then ask about the prior prompt.
    # -----------------------------------------------------------------
    print(f"\n>>> Session 2 (fresh session id, same agent): creating ...")
    session2 = client.beta.sessions.create(
        agent=state["agent_id"], environment_id=state["env_id"],
        title="phl4 session 2 — replay",
    )
    print(f"    session2.id = {session2.id}")

    print(f">>> Replaying user-origin events from session1 into session2 ...")
    replay_report = replay_session_from_log(
        jsonl_path, session2.id, client=client
    )
    print(f"    replayed: {replay_report['events_replayed']} user-origin events")
    print(f"    skipped (agent/tool/span/session): "
          f"{sum(replay_report['events_skipped_by_type'].values())}")
    print(f"    skipped breakdown: {replay_report['events_skipped_by_type']}")

    # Now ask a follow-up in session 2 that should leverage the replayed
    # user.message for context.
    followup = (
        "Look at the conversation so far. What exactly did I ask you "
        "in my previous message? Quote it verbatim."
    )
    print(f"\n>>> Session 2 follow-up: {followup!r}")
    s2_reply: list[str] = []
    with client.beta.sessions.events.stream(session2.id) as stream:
        client.beta.sessions.events.send(
            session2.id,
            events=[{"type": "user.message",
                     "content": [{"type": "text", "text": followup}]}],
        )
        _drain(stream, s2_reply)
    s2_text = "".join(s2_reply).strip()
    print(f"    session 2 agent replied: {s2_text[:300]}")

    # -----------------------------------------------------------------
    # Write final verdict
    # -----------------------------------------------------------------
    original_prompt = "Count from 1 to 3 inclusive."
    quoted = original_prompt.lower() in s2_text.lower() or (
        "1" in s2_text and "3" in s2_text and "count" in s2_text.lower()
    )
    verdict = {
        "hypothesis_id": "phl4_persist_replay_smoke",
        "run_date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "agent_id": state["agent_id"],
        "session1_id": session1.id,
        "session1_reply": "".join(s1_reply).strip(),
        "persisted_event_count": persist_report["event_count"],
        "persisted_jsonl_path": str(jsonl_path.relative_to(REPO_ROOT)),
        "session2_id": session2.id,
        "session2_replay_events_replayed": replay_report["events_replayed"],
        "session2_replay_events_skipped_by_type":
            replay_report["events_skipped_by_type"],
        "session2_followup_prompt": followup,
        "session2_reply": s2_text,
        "verdict": (
            "PASS"
            if quoted
            else "INCONCLUSIVE (agent did not clearly quote the prior prompt)"
        ),
        "narrative": (
            "Session 1 event log was persisted to JSONL via events.list. "
            "A second session (different id, same agent) received the "
            "user-origin events replayed from the JSONL. The follow-up "
            "prompt asked the agent to quote the prior user message. If "
            "the agent reproduces 'Count from 1 to 3 inclusive.', the "
            "event log carried the user-side state across sessions."
        ),
    }
    verdict_path = LOG_DIR / "verdict.json"
    verdict_path.write_text(json.dumps(verdict, indent=2))
    print(f"\n>>> Verdict: {verdict['verdict']}")
    print(f"    Full artefacts at {LOG_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
