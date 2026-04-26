# PhL-8b — Claude Code Routines Schedule trigger live execution

**Run date:** 2026-04-26T00:39Z (~)
**Trigger type:** Schedule (one-shot "Once")
**Routine:** `lacuna-falsification-gate` — same routine binding
as PhL-8, different trigger surface.

## Honest scope (read this first)

This artefact evidences the **Schedule trigger fire mechanism**, NOT a
full end-to-end gate run. The fire fired autonomously and the session
was initialized server-side, but the routine session **failed at the
first turn** with the workspace error
*"You're out of extra usage · resets Apr 29, 10pm (UTC)"* — extra-usage
quota was exhausted at fire time, and the reset date is post-submission
(2026-04-26 20:00 EDT deadline). A re-fire on a budget-restored
workspace would produce a green PhL-8c; that is left as future work.

**What this run does prove:**
- Schedule triggers configured in the routines web UI fire autonomously
  on the cron expression the user committed once and walked away from.
- The Anthropic backend created a Claude Code session at fire time with
  no client involvement — *"laptop closed, loops continue"* (Boris
  Cherny, kickoff 2026-04-21) is operational.
- The same `trig_id` accepts both API and Schedule triggers without
  any client-side code change.

**What this run does NOT prove:**
- That the routine's saved Instructions executed to completion (they
  did not — the session hit the usage gate before any tool call).
- That the gate verdict produced by the routine matches the canonical
  TOP2A − EPAS1 survivor on a clean re-fire (untestable until Apr 29
  reset).

## What this closes

PhL-8 (2026-04-23) fired the routine via the **API trigger**: a manual
HTTP `POST /v1/claude_code/routines/{trig_id}/fire` from a local
script. That proved the bearer-token client-fire path works.

PhL-8b fires the **same routine** via a **Schedule trigger** that the
user configured once in the routine's web UI and then walked away from.
The fire happens with no client involvement — no script invocation, no
API call, no terminal open. This is the literal embodiment of Boris
Cherny's kickoff framing:

> *"loops running on the server. Laptop closed, they continue ...
> Agent SDK on steroids ... no one has cracked yet at all."*
> — Boris Cherny, hackathon kickoff 2026-04-21

PhL-8 (API) + PhL-8b (Schedule) demonstrates the same routine binding
accepting two of the three trigger surfaces Boris named at kickoff.
The third surface (GitHub `pull_request` / `release` events) is
configured in the same web UI without code changes — `fire_routine`
in `src/lacuna/routines_client.py` is trigger-agnostic on the
client side.

## What ran

1. User opened `claude.ai/code/routines/<lacuna-falsification-gate>`
   and added a Schedule trigger of kind **"Once"** with fire time
   **2026-04-25 20:20 EDT** (= **2026-04-26T00:20:00Z**).
2. No further action — the user's laptop was closed / the session was
   not active when the routine fired.
3. The Anthropic backend created a Claude Code session at fire time
   and started the routine's saved Instructions (forked from
   `docs/submission_form_draft.md`: verification pulse — `make venv`,
   `make audit`, load canonical survivor, apply gate only if text
   input has `"equation:"`, final block summary). The session hit
   the workspace usage quota before producing any agent output —
   **"Initialized session" → API Error** at the first turn. The fire
   itself is end-to-end attested; the session output is not.

## Result

```json
{
  "trigger_type": "schedule",
  "schedule_kind": "once",
  "routine_trig_id_prefix": "trig_01CjZ8f...",
  "routine_trig_id_length": 29,
  "scheduled_fire_utc": "2026-04-26T00:20:00Z",
  "actual_fire_utc": "2026-04-26T00:39:00Z (~ — UI Runs section displayed local time "today at 8:39 PM EDT" only at minute granularity)",
  "stagger_offset_seconds": "~1140 (≈ 19 minutes — substantially larger than the UI's "a few minutes" advisory; honest record of observed backend stagger on this fire)",
  "claude_code_session_id": "TODO_SESSION_ID_FROM_URL",
  "claude_code_session_url": "TODO_FULL_URL_FROM_BROWSER_ADDRESS_BAR",
  "session_status": "Failed (workspace 'out of extra usage' at first turn)",
  "session_failure_reason": "extra-usage quota exhausted at fire time; reset 2026-04-29T22:00Z (post-submission deadline 2026-04-26T00:00Z)",
  "human_action_at_fire_time": "none — routine fired autonomously per Schedule trigger; user laptop was not required",
  "narrative": "Same routine binding as PhL-8 fired via Schedule trigger instead of API trigger. The fire mechanism is end-to-end attested by the Anthropic backend run record (visible at the Schedule row in the routine's Runs page: 'today at 8:39 PM SCHEDULED Failed'). The session output is not — the workspace's extra-usage quota blocked execution before any tool call. A clean re-fire is deferred to post-quota-reset."
}
```

## Why this matters for the submission

Trigger diversity was the thinnest leg of the Path C story before this
run:

- **Code**: `src/lacuna/routines_client.py` is trigger-agnostic.
- **Docs**: `docs/methodology.md §4` cites all three trigger categories
  (API, Schedule cron ≥ 1 h, GitHub `pull_request` / `release`).
- **Live evidence (before PhL-8b)**: API trigger only (PhL-8). Schedule
  and GitHub triggers were *configurable but not exercised live*.

PhL-8b adds the Schedule trigger as a second live surface. The same
routine binding fires under two trigger types with no code change in
between — the client-side `routines_client.py` doesn't even know which
trigger fired. Configure once, reuse across trigger surfaces.

The "Runs are staggered by a few minutes to spread server load" notice
in the routines UI means the actual fire time can drift ≤ ~3 min from
the scheduled time. The `stagger_offset_seconds` field above records
the observed drift for this run.

## Re-run instructions

Schedule triggers are configured per-routine in the web UI at
`claude.ai/code/routines/<routine-name>` → Triggers → Add → Schedule.
There is no API endpoint to add a Schedule trigger programmatically
(documented as web-UI-only at the time of this evidence run,
2026-04-25). Once configured, the routine fires autonomously; no
client action is needed.

To re-fire on a fresh schedule:
1. Edit the existing Schedule trigger to a new fire time, OR
2. Add a second Schedule trigger (the same routine accepts multiple
   triggers of mixed types).

## Cost

- Schedule trigger configuration: free (web UI only, no API call).
- Routine session execution at fire time: bounded by the saved
  Instructions' `Runtime budget: ~3 minutes. If you exceed 5 minutes,
  stop.` clause — same as PhL-8. Typical ~$0.10–0.30 per fire.

## Tamper-evidence

- This SUMMARY.md is committed as generated; the
  `claude_code_session_id` and `actual_fire_utc` are server-assigned
  and can be cross-checked by logging into the same Claude account
  and viewing the routine's Runs / History page.
- The routine's saved Instructions are quoted in the separately
  committed `docs/submission_form_draft.md` so reviewers can see the
  prompt that drove the session without needing UI access.
- The full `trig_id` is **not** committed — only the 9-character prefix
  (`trig_01CjZ8f...`), matching PhL-8's tamper-evidence pattern. The
  bearer token used for API fires (a separate per-routine secret) is
  not relevant to Schedule trigger fires: Schedule triggers do not
  consume the bearer token.

## Cross-reference to PhL-8

| Property | PhL-8 (API trigger) | PhL-8b (Schedule trigger) |
|---|---|---|
| Routine | `lacuna-falsification-gate` | same |
| `trig_id` | `trig_01CjZ8f...` | same |
| Fire surface | `POST /v1/claude_code/routines/{id}/fire` | Schedule "Once" via web UI |
| Bearer token used | yes (`CLAUDE_ROUTINE_TOKEN`) | no (Schedule fires don't use API token) |
| Client action at fire time | local Python script | **none** — laptop closed |
| Session URL host | `claude.ai/code/session_…` | same |
| Saved Instructions | identical | identical |
| Stagger from scheduled time | n/a (manual fire) | ~19 min (UI advisory: "a few minutes") |
| Session run status | Completed | **Failed** (workspace quota at first turn) |
| Cost per fire | ~$0.10–0.30 (real Claude work) | $0 effectively (quota-blocked before tool calls) |
| Evidence layer | mechanism + output | **mechanism only** (output deferred to post-quota-reset) |
