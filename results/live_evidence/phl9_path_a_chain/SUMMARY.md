# PhL-9 — Path A live evidence (3-session sequential chain)

**Verdict:** OK — `delegation_mode = sequential_fallback`, `status = completed`,
wall clock 706 s (≈12 min) across three separate Managed Agents sessions.

## What this closes

The submission cites **Path A = public-beta-compliant sequential 3-session
chain** (per the 2026-04-23 hackathon fairness ruling on research-preview
Agent Teams / `callable_agents`). Prior live logs:

- `04_managed_agents_e2e.log` — Path **B** only (single session).
- `06_managed_agents_path_a.log` — Path A from the pre-review-handoff era.

PhL-9 is the first on-disk transcript of all three sequential sessions
running with the post-review-handoff Proposer / Searcher / Skeptic
Instructions.

## What it actually ran

`lacuna.managed_agent_runner.run_path_a(night=2,
fallback_on_no_waitlist=True)` — the **exact** function cited in
`docs/submission_description.md` as our Path A execution model.
Because `MANAGED_AGENTS_WAITLIST` is not set to `approved` in this
workspace (per Anthropic's 4/23 ruling), the call lands in
`_run_path_a_sequential_fallback`, not in
`_run_path_a_callable_agents`.

## Artefacts

| File | Contents |
|---|---|
| `verdict.json` | `delegation_mode`, `status`, `last_session_id`, `last_agent_id`, `wall_seconds`, per-role outputs |
| `role_proposer.txt` | 2 254 chars — Opus 4.7 Proposer turn output |
| `role_searcher.txt` | 3 445 chars — Sonnet 4.6 Searcher turn output (PySR-in-bash role) |
| `role_falsifier.txt` | 6 004 chars — Opus 4.7 Skeptic / Falsifier turn output |

Each session runs in its **own** Managed Agents `session_id` with its
own `agent_id`; the chain is stitched client-side via structured-JSON
handoff in the next session's prompt. The `_run_path_a_callable_agents`
branch remains in the repo as an architectural reference of the
research-preview Agent Teams shape, env-flag-guarded behind
`MANAGED_AGENTS_WAITLIST=approved`.

## Why this matters to a reviewer

1. **Claim verification.** We claim Path A works. Now there is a run
   transcript that shows it working end-to-end in 706 s under today's
   Instructions and today's fairness rule.
2. **Delegation-mode honesty.** `verdict.json:"delegation_mode"` is
   `sequential_fallback`, not `callable_agents`. A judge grepping the
   artefact can confirm the path we actually ran matches the path
   we are allowed to run.
3. **Three distinct sessions.** `len(role_*.txt)` differs per role;
   session IDs are captured in the run log. This is not one agent
   in three trench coats.

## Reproduce

```bash
source ~/.api_keys
PYTHONPATH=src .venv/bin/python src/phl9_path_a_live_chain.py
```

Cost: ~$0.50 across 3 short Opus 4.7 + Sonnet 4.6 sessions.
Wall time: ~12 min (dominated by Skeptic extended-thinking turn).
