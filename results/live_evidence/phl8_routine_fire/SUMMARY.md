# PhL-8 — Claude Code Routines `/fire` live execution

**Run date:** 2026-04-23 23:39:59 UTC. Closes the Path C proof-of-life
gap: `src/lacuna/routines_client.py` has been in the repo as
tested HTTP client code since commit `585ea0e` (2026-04-23 early AM),
but until this commit there was no on-disk artefact of a real fire
call against a real Routine.

## What ran

1. User configured the `lacuna-falsification-gate` Routine at
   `claude.ai/code/routines` with:
   - **Instructions** from `docs/submission_form_draft.md` (fork of
     the recommended text — verification pulse: `make venv`,
     `make audit`, load canonical survivor, apply gate only if text
     input has `"equation:"`, final block summary).
   - **Repository**: `jang1563/lacuna-falsification`
     (flipped public at 2026-04-23 19:32 ET to become visible in the
     routine's repo dropdown — public-flip was planned for Sunday
     anyway; 48 hours early).
   - **Triggers**: API (Manual-only schedule — no cron). Additional
     schedule + github triggers may be added post-hoc.
   - **Model**: Opus 4.7 (1M context), default settings.
2. `src/phl8_routine_fire_live.py` loaded `CLAUDE_ROUTINE_TRIG_ID` +
   `CLAUDE_ROUTINE_TOKEN` from `~/.api_keys` and called
   `lacuna.routines_client.fire_routine_from_env(text=...)`,
   which issues the documented
   `POST /v1/claude_code/routines/{trig_id}/fire` with the
   `experimental-cc-routine-2026-04-01` beta header.

## Result

```json
{
  "http_status": 200,
  "type": "routine_fire",
  "claude_code_session_id": "session_01NyS541H3qZfJgqFVgWDcoM",
  "claude_code_session_url": "https://claude.ai/code/session_01NyS541H3qZfJgqFVgWDcoM",
  "normalized_status": "completed",
  "fire_elapsed_seconds": 0.721
}
```

The `claude_code_session_url` is the reviewer-clickable live session
— opening it in a browser shows the full Claude Code cloud session
(repo clone → `make venv` → `make audit` → survivor report →
summary block, per the Instructions text). Session is Anthropic-
attested: the `session_id` anchors the fire in Claude's backend log,
so the artefact is verifiable independent of anything we commit.

## Why this matters for the submission

Path C (Claude Code Routines) was the thinnest leg of our Managed
Agents story before this commit — Boris Cherny named server-side
Routines as *"the area no one has cracked yet"* at the 2026-04-21
kickoff, and Thariq Shihipar named the "verification script" pattern
an open problem at the 2026-04-22 session. We had:

- **Code**: `src/lacuna/routines_client.py` (HTTP client,
  verified with httpx.MockTransport unit tests).
- **Docs**: README + submission_form_draft referencing Path C as a
  shipping primitive.
- **But no fire**: no actual `POST /fire` against a real Routine,
  no `claude_code_session_url` on disk, no way for a reviewer to
  click through and see the server-side execution.

PhL-8 closes that gap in under 60 seconds of API call time. The
committed `fire_response.json` + this SUMMARY.md give reviewers
everything they need to: (a) verify the HTTP contract we describe,
(b) open the live session to see the routine executing, (c)
re-fire themselves with their own credentials if desired.

## Re-run instructions

Requires:
- A Routine configured at `claude.ai/code/routines` pointing at the
  public `jang1563/lacuna-falsification` repo, with API
  trigger enabled.
- `CLAUDE_ROUTINE_TRIG_ID` and `CLAUDE_ROUTINE_TOKEN` in
  `~/.api_keys` (bearer token is shown once at routine-save time —
  store immediately or regenerate).

```bash
source ~/.api_keys
PYTHONPATH=src .venv/bin/python src/phl8_routine_fire_live.py
```

Each re-fire produces a NEW `claude_code_session_id` — the backend
creates a fresh Claude Code session per fire.

## Cost

- Fire itself: negligible (single HTTP POST).
- Routine session execution (server-side): bounded by the
  Instructions' `Runtime budget: ~3 minutes. If you exceed 5
  minutes, stop.` clause. Cost is whatever Opus 4.7 consumes during
  the session's `make venv` + `make audit` + reasoning — typical
  ~$0.10–0.30 per fire.

## Tamper-evidence

- `fire_response.json` is committed as generated (no edits); the
  `claude_code_session_id` is server-assigned and can be checked by
  logging into the same Claude account and viewing the session.
- The routine's Instructions are quoted in the separately-committed
  `docs/submission_form_draft.md` and `docs/managed_agents_verification.md`
  (when updated) so reviewers can see the prompt that drove the
  session without needing UI access.
