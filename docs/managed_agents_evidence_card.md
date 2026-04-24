# Managed Agents / Routines — Judge Evidence Card

*One-page navigation of every committed artefact that exercises
Anthropic's Managed Agents public beta (`managed-agents-2026-04-01`,
shipped 2026-04-08), Memory public beta (shipped 2026-04-23), and
Claude Code Routines research preview (`experimental-cc-routine-2026-04-01`,
shipped 2026-04-14).*

## Compliance note

- **Public-beta features only** in the submitted live run, per the
  2026-04-23 hackathon-fairness ruling that `callable_agents` /
  multi-agent coordination is research-preview-gated.
- `_run_path_a_callable_agents` retained only as reference code,
  env-flag-guarded behind `MANAGED_AGENTS_WAITLIST=approved`.
- No Routine bearer token, per-trigger ID, or API key is exposed in
  tracked files (`make audit` enforces).
- Memory public beta uses the standard
  `managed-agents-2026-04-01` header — no separate access request.

## Evidence table

| # | Evidence | What it proves | Artefact |
|---|---|---|---|
| **Path B** | Single public-beta agent + `agent_toolset_20260401`, end-to-end trace | `agents.create → environments.create → sessions.create → stream → send → status_idle` | [`results/live_evidence/04_managed_agents_e2e.log`](../results/live_evidence/04_managed_agents_e2e.log) |
| **Path A v1 (PhL-9)** | Sequential 3-session chain, `delegation_mode=sequential_fallback`, public-beta-compliant | 3 distinct `session_id`s in 706 s on a synthetic-physics smoke | [`results/live_evidence/phl9_path_a_chain/SUMMARY.md`](../results/live_evidence/phl9_path_a_chain/SUMMARY.md) |
| **Path A v2 (PhL-9v2)** | Sequential 3-session chain on **real TCGA-KIRC data** via `files.upload()` + `resources=[{"type":"file",...}]` mount. Proposer emits proliferation-vs-HIF family, Skeptic quotes `delta_baseline=+0.0587` in its verdict. | 300 s, 5 candidates, 1 NEEDS_MORE_TESTS, 4 FAIL incl. negative control | [`results/live_evidence/phl9v2_path_a_real_data/SUMMARY.md`](../results/live_evidence/phl9v2_path_a_real_data/SUMMARY.md) |
| **Path C (PhL-8)** | Claude Code Routine `/fire` live HTTP 200 + clickable `claude_code_session_url` | `https://claude.ai/code/session_01NyS541H3qZfJgqFVgWDcoM` | [`results/live_evidence/phl8_routine_fire/SUMMARY.md`](../results/live_evidence/phl8_routine_fire/SUMMARY.md) |
| **Event log persist + replay (PhL-4)** | `sessions.events.list` paged to JSONL; `replay_session_from_log` re-injects user-origin events into a fresh session | `session1_events.jsonl` + verbatim quote of replayed user.message by fresh Session 2 | [`results/live_evidence/phl4_persist_replay/SUMMARY.md`](../results/live_evidence/phl4_persist_replay/SUMMARY.md) |
| **Memory store (PhL-3)** | Memory public-beta integrated same day (2026-04-23). Skeptic writes rejection lessons; fresh sessions read + quote verbatim. | 2 sessions, 2 lessons, server-side verified via raw `/v1/memory_stores/*` | [`results/live_evidence/phl3_memory_smoke/SUMMARY.md`](../results/live_evidence/phl3_memory_smoke/SUMMARY.md) |
| **Compound orchestrator (PhL-7)** | Single Managed Agents session composes MCP biology validator + Memory load/write + 5-test gate rubric with cross-substrate reasoning | Agent read prior ceiling-effect lesson, correctly distinguished current metastasis task, appended refined lesson | [`results/live_evidence/phl7_compound_orchestrator/SUMMARY.md`](../results/live_evidence/phl7_compound_orchestrator/SUMMARY.md) |
| **Memory chain deepen (PhL-10 + PhL-12)** | Memory chain grew 3 → 5 → **8 lessons** across sessions. Agent quotes prior lessons by number and refines them — including ceiling-effect rule generalizing KIRC/CA9 → LUAD/SFTPC → PRAD/KLK3 across cancers. | Server-side verification via raw `/v1/memory_stores/{store_id}/memories` | [PhL-10 SUMMARY](../results/live_evidence/phl10_memory_chain_extended/SUMMARY.md) + [PhL-12 SUMMARY](../results/live_evidence/phl12_memory_chain_deepen/SUMMARY.md) |
| **Adversarial self-critique (PhL-11)** | 3-turn role-separated 2-model harness (Opus 4.7 + Sonnet 4.6, 6 sessions). Measured metrics: Opus followed per-attack instruction literally (5 CRISPR KOs vs Sonnet's 1); both models concede 100% under pushback. | Honest mixed result reported | [`results/live_evidence/phl11_adversarial_critique/SUMMARY.md`](../results/live_evidence/phl11_adversarial_critique/SUMMARY.md) |
| **MCP biology validator (PhL-2)** | PubMed E-utilities + GDC REST cohort metadata exposed as MCP tools for the Skeptic subagent | `validate_law(["TOP2A","EPAS1"], disease="ccRCC") → 0 co-mentions` (independent rediscovery signal) | [`results/live_evidence/09_mcp_biology_validator_live.log`](../results/live_evidence/09_mcp_biology_validator_live.log) |

## 3-minute judge reading path

1. This card.
2. PhL-9v2 SUMMARY — Path A on real TCGA-KIRC, Skeptic quotes real
   delta_baseline numbers.
3. PhL-8 SUMMARY — Open the clickable `claude.ai/code/session_*`
   URL in a browser. Watch server-side execution.
4. PhL-10 + PhL-12 combined — Memory chain across 8 lessons with
   cross-cancer rule transfer.
5. (Optional) PhL-7 compound orchestrator — the single strongest
   "multi-product composition in one session" artefact.

## Architectural diagram

```
┌─────────────── Managed Agents (public beta, platform.claude.com) ───────────────┐
│                                                                                  │
│  agents.create  ──▶  environments.create  ──▶  sessions.create                   │
│      │                     │                          │                          │
│      │                     │                          ├─ resources: memory_store │
│      │                     │                          ├─ resources: file mount   │
│      │                     │                          │    (type:"file",         │
│      │                     │                          │     file_id,mount_path)  │
│      ▼                     ▼                          ▼                          │
│  agent_id              env_id                    session_id                      │
│                                                                                  │
│  [Path B: one session w/ agent_toolset_20260401]                                 │
│  [Path A: 3 sequential sessions, structured-JSON handoff, one env]               │
│  [PhL-4: sessions.events.list → JSONL → replay_session_from_log]                 │
│  [PhL-3/7/10/12: shared memory_store across sessions, /lessons.md, 8 entries]    │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
                                    ▲
                                    │ cross-product composition
                                    │ (PhL-7 compound orchestrator)
                                    │
┌─────────────── Claude Code Routines (research preview, code.claude.com) ─────┐
│                                                                               │
│  POST /v1/claude_code/routines/{trig_id}/fire                                 │
│      └─▶  HTTP 200 + {claude_code_session_id, claude_code_session_url}        │
│                                                                               │
│  [PhL-8: Routine fired live; browser-openable session URL committed]          │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

## Why composing the two products is load-bearing

Managed Agents live on `platform.claude.com`; Routines live on
`code.claude.com`. Bridging them requires a Routine bearer token,
a distinct beta header, and a separate session-event surface. Most
implementations we've seen pick one and ignore the other. Theory
Copilot uses both in the same pipeline: the Skeptic runs in Managed
Agents sessions (durable event log + memory); the nightly audit
runs in a Routine (`make audit` + rejection-log regen server-side).
`invoke_fn=make_routine_invoke_fn(...)` in `managed_agent_runner.py`
is the one-line swap point.
