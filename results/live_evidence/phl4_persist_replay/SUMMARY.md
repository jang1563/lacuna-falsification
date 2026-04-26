# PhL-4 — `sessions.events.list` persist + replay live demo

**Run date:** 2026-04-23. Exercises the two durability primitives
shipped in `src/lacuna/managed_agent_runner.py`:
`persist_session_events(session_id, out_path)` and
`replay_session_from_log(log_path, target_session_id)`.

## What this demonstrates (end-to-end live)

Two Managed Agents sessions, **same agent**, **different session IDs**,
with user-side state carried across by the raw event log — not by
Memory, not by shared context. This is the "brain/body decoupling"
primitive the 2026-04-08 Anthropic engineering post foregrounds.

| Session | ID | Role |
|---|---|---|
| Session 1 — origin | `sesn_011CaMMhgYZymDn1ij7k4tgS` | Received `user.message = "Count from 1 to 3 inclusive."`; agent replied `1, 2, 3`. 6 events captured. |
| **Persist step** | — | `persist_session_events(session1.id, events.jsonl)` paged through `client.beta.sessions.events.list` and dumped all 6 events to JSONL. |
| Session 2 — replay | `sesn_011CaMMjQ6uU6TJFYpSiUDXH` | Fresh session, same agent. `replay_session_from_log(events.jsonl, session2.id)` re-injected **1 user-origin event** (the `user.message`). 5 platform/agent events were correctly skipped. Agent then received the follow-up *"What exactly did I ask you in my previous message? Quote it verbatim."* and responded with `1, 2, 3 "Count from 1 to 3 inclusive."` — the replayed content quoted verbatim. |

Full transcripts + JSONL event log + verdict:
[`verdict.json`](verdict.json), [`session1_events.jsonl`](session1_events.jsonl).

## Why it matters for the submission

Three axes simultaneously:

1. **Boris Cherny — skills that ship.** The event log is a shareable
   artefact (JSONL on disk), not in-context state. A reviewer can
   `grep 'user.message' session1_events.jsonl` and see exactly what
   moved between sessions.

2. **Managed Agents brain/body decoupling (2026-04-08 engineering
   post).** The post describes exactly this shape: sessions are the
   durable brain, the harness (the environment container) is a
   disposable body. PhL-3 (Memory) and PhL-4 (event-log replay) are
   the two concrete primitives that make that claim operational — one
   for agent-written files, one for the client-originated turn log.

3. **Honest scope.** This demo does NOT claim that agent state is
   restored — replay only injects *user-origin* events (`user.message`,
   `user.interrupt`, `user.custom_tool_result`, `user.tool_confirmation`).
   Agent messages, tool uses, span events, and session status events
   are log-only (the platform owns those). This is documented in
   `replay_session_from_log`'s allowlist and flagged in the verdict's
   `events_skipped_by_type` breakdown.

## Files

- `verdict.json` — machine-readable verdict (PASS), both session IDs,
  persist/replay counts, replayed agent reply text.
- `session1_events.jsonl` — exactly the 6 events the platform returned
  from `events.list` for session 1. Reviewers can `jq` through this
  to verify the event shape matches the
  `platform.claude.com/docs/en/managed-agents/events` reference.
- `phl4_state.json` — agent/env IDs cached for re-runs. Gitignored
  (workspace-scoped; opaque to reviewers with different API keys).

## Reviewer re-run instructions

```bash
# From the repo root, with ANTHROPIC_API_KEY in ~/.api_keys or env:
PYTHONPATH=src .venv/bin/python src/phl4_persist_replay_smoke.py
```

First run creates the agent + environment and caches the IDs; second
run reuses them. Each run produces a fresh pair of sessions, so the
session IDs in `verdict.json` differ on re-run. The `PASS` criterion
is "session 2's reply contains either the verbatim prior prompt OR
the original answer (1,2,3 + 'count')" — see
[`src/phl4_persist_replay_smoke.py:main`](../../../src/phl4_persist_replay_smoke.py)
for the exact heuristic.

## Cost

~$0.15 across two Opus 4.7 sessions, ≤ 30 s each.
