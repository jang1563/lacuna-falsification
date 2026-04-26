# Managed Agents / Routines — Judge Evidence Card

**TL;DR for a judge with 2 minutes:** Three live execution paths —
- **Path B** (single Managed Agent + `agent_toolset_20260401`): running now, Path B log is committed.
- **Path A** (sequential 3-session chain: Proposer → Skeptic → Interpreter on real TCGA-KIRC kidney cancer data): PhL-9v2, structured-JSON handoff, no shared context between sessions.
- **Path C** (Claude Code Routines `/fire`): two live clickable sessions (PhL-8d, PhL-10) — the falsification oracle fires on demand without a human pressing a button.

Plus **Memory** (server-side lesson chain, 8 entries across 5 sessions) and **MCP** (`validate_law` + `fetch_cohort_summary` tools, PhL-2). All committed, all with wall-clock times and API costs.

---

> Boris Cherny (Claude Code, kickoff 2026-04-21):
> *"Loops running on the server. Laptop closed, they continue ...
> Agent SDK on steroids ... no one has cracked yet at all."*
>
> Michael Cohen (Managed Agents, live session 2026-04-23):
> *"Building agents is difficult and is only getting more difficult
> over time."* / *"Effectively a self-verification loop ... in order
> for you to think of this task as done, these things have to be true."*
>
> This card lists every committed artefact that turns those two
> framings into running code in a single pipeline — Managed Agents
> for the durable Proposer / Searcher / Skeptic chain, Claude Code
> Routines for the laptop-closed nightly audit, both products
> composed in one repo.

*One-page navigation of every committed artefact that exercises
Anthropic's Managed Agents public beta (`managed-agents-2026-04-01`,
shipped 2026-04-08), Memory public beta (shipped 2026-04-23), and
Claude Code Routines research preview (`experimental-cc-routine-2026-04-01`,
shipped 2026-04-14).*

## Why this maps to the Managed Agents engineering posture

Anthropic's engineering blog
[*Scaling Managed Agents*](https://www.anthropic.com/engineering/managed-agents)
defines the product abstraction as *"decoupling the brain from the
hands,"* virtualising the agent into three components: *"a session (the
append-only log of everything that happened), a harness (the loop that
calls Claude and routes Claude's tool calls to the relevant
infrastructure), and a sandbox."* Lacuna exercises each of
those three substrates as scientific-audit surfaces:

- **Session (append-only log)** — PhL-4 `persist_session_events` pages
  `events.list` to JSONL and `replay_session_from_log` re-injects
  user-origin events into a fresh session. The event log becomes the
  reproducibility object: a survivor claim has to be derivable from
  the committed events, not only from the committed source code.
- **Harness (loop + tool routing)** — Path A sequential three-session
  chain (PhL-9 + PhL-9v2 on real TCGA-KIRC) with structured-JSON
  handoff isolates the Skeptic's context from the Proposer's
  reasoning tokens. The per-session harness boundary is the mechanism
  that keeps the Skeptic from rationalising its own proposal into
  passing.
- **Sandbox (tool substrate)** — public-beta `agent_toolset_20260401`
  (Path B) + `beta.files.upload()` mounts (PhL-9v2) + MCP biology
  validator (PhL-2) — every tool call is logged as an event, every
  uploaded file is referenceable by `file_id`, every memory write is
  immutable-versioned.

The AAR paper ([Leike et al.,
2026-04-14](https://www.anthropic.com/research/automated-alignment-researchers))
requires *"evaluations that the AARs can't tamper with"* — the sessions,
harnesses, and sandboxes here are the tamper-resistant substrate;
the pre-registered 5-test gate is the tamper-resistant evaluation;
together they make human inspection (`make audit`, `make smoke`,
`make prereg-audit`, the rejection log) *scalable*, not obsolete.

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
| **Path C — API trigger (PhL-8)** | Claude Code Routine `/fire` live HTTP 200 + clickable `claude_code_session_url` | `https://claude.ai/code/session_01NyS541H3qZfJgqFVgWDcoM` | [`results/live_evidence/phl8_routine_fire/SUMMARY.md`](../results/live_evidence/phl8_routine_fire/SUMMARY.md) |
| **Path C — Schedule trigger (PhL-8b)** | Same routine binding fired autonomously by Schedule trigger — no client action at fire time; laptop closed; session created server-side 2026-04-26T00:39Z (19-min stagger). Session failed at first turn (workspace extra-usage quota); mechanism layer evidenced, output deferred. | `trig_id: trig_01CjZ8f…`; fire confirmed in routine Runs page: "today at 8:39 PM SCHEDULED Failed" | [`results/live_evidence/phl8b_routine_schedule/SUMMARY.md`](../results/live_evidence/phl8b_routine_schedule/SUMMARY.md) |
| **Path C — Scientific Oracle (PhL-8c)** | Upgraded routine `lacuna-scientific-oracle` receives equation via API trigger text, autonomously runs `make venv` + `make audit` + `falsification_sweep.py` (1000 perm + 1000 bootstrap + 100 decoys, n=505), emits structured PASS/FAIL verdict. **First autonomous scientific falsification by a Claude Code Routine.** | `gate: PASS`, `perm_p=0.0`, `ci_lower=0.664`, `delta_baseline=+0.062`, `decoy_p=0.0` on `CDK1 − EPAS1` | [`results/live_evidence/phl8c_scientific_oracle/SUMMARY.md`](../results/live_evidence/phl8c_scientific_oracle/SUMMARY.md) |
| **Path C — Dual Verdict Oracle (PhL-8d)** | Same oracle fires with **two equations** in one trigger: Eq1 (`CA9 − AGXT` on tumor_vs_normal, FAIL) + Eq2 (`CDK1 − EPAS1` on metastasis_expanded, PASS). One session URL = full Lacuna narrative: pre-registered gate rejects AND accepts, same thresholds, same autonomous run. | Eq1: **FAIL**, delta_baseline=0.0145 < 0.05 (CA9 alone AUROC 0.965); Eq2: **PASS**, delta_baseline=0.0622, ci_lower=0.662, perm_p=0.0 | [`results/live_evidence/phl8d_dual_verdict/SUMMARY.md`](../results/live_evidence/phl8d_dual_verdict/SUMMARY.md) |
| **Path C — Stage Oracle (PhL-10 oracle)** | **Second autonomous Routine session.** New Routine per disease (provenance principle — existing Instructions are the PhL-8d audit record). New task: Stage I-II vs III-IV, n=512. Eq1 `CCNB1/PGK1` FAIL (delta_baseline=0.007, <0.05) + Eq2 `CXCR4/EPAS1` PASS (AUROC 0.696, ci_lower=0.649, Δbase=+0.051). | `session_01XGse8XYFtv3C1aKLZeMH9t` · FAIL + PASS · same gate · same Skills · different Routine | [`results/live_evidence/phl10_stage_oracle/SUMMARY.md`](../results/live_evidence/phl10_stage_oracle/SUMMARY.md) |
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
3. **PhL-8d** — Open `session_01CgsJYAPdvhJJwTuBt7QZLZ` in a browser.
   Watch the oracle autonomously run the 5-test gate on TWO equations:
   Eq1 `CA9−AGXT` FAIL (gate refuses textbook HIF law) + Eq2
   `CDK1−EPAS1` PASS — the full Lacuna narrative in one session.
   PhL-8c (`session_015ot5hkJgSiBoWNA51fjZ1k`) remains as prior
   step: single-equation PASS, simpler to follow.
4. **PhL-10 stage oracle** — `session_01XGse8XYFtv3C1aKLZeMH9t`.
   Second autonomous Routine session, new task (Stage I-II vs III-IV),
   new Routine (provenance principle — editing existing Instructions
   breaks audit chain). CCNB1/PGK1 FAIL + CXCR4/EPAS1 PASS.
5. PhL-10 + PhL-12 combined — Memory chain across 8 lessons with
   cross-cancer rule transfer.
6. (Optional) PhL-7 compound orchestrator — the single strongest
   "multi-product composition in one session" artefact.

## Observability: per-artefact event + wall-clock table

The table below is derived programmatically from each artefact's
`verdict.json` / `fire_response.json`. Numbers are not editorially
chosen — they come directly from server-side Managed Agents state. This
turns "we used agents" into measured observability.

| PhL | run UTC | session count | session id prefix | events / lessons / tool-calls | wall time | verdict |
|---|---|---|---|---|---|---|
| **PhL-3** | 2026-04-23 ~20:42 | 2 sessions (shared memory_store) | `sesn_…CaMMg…` | 2 lesson writes persisted + verified server-side via `/memory_stores/{id}/memories` | n/a (smoke) | PASS |
| **PhL-4** | 2026-04-23 20:46 Z | 2 sessions (persist + replay) | `agent_…CaMMgN7…` | 6 events persisted to JSONL + replayed in fresh session | n/a (smoke) | PASS |
| **PhL-7** | 2026-04-23 22:53 Z | 1 session (compound) | `sesn_…CaMXHE…` | 21 total events · 3 tool-calls · 1 memory write (cross-substrate reasoning) | n/a (smoke) | PASS |
| **PhL-8** | 2026-04-23 ~23:10 | 1 Routine `/fire` (API trigger) | `session_01NyS541…` | HTTP 200 + clickable `claude.ai/code/session_01NyS541H3qZfJgqFVgWDcoM` | fire + fork, no wait | 200 OK |
| **PhL-8b** | 2026-04-26 00:39 Z | 1 Routine Schedule trigger (autonomous) | NOT_RECORDED (failed at turn 1) | Schedule trigger fired server-side with no client action; session created; blocked by workspace extra-usage quota before any tool call. Mechanism layer evidenced. | n/a (quota-blocked) | PARTIAL (mechanism ✓ / output ✗) |
| **PhL-8c** | 2026-04-26 15:05 Z | 1 Routine API trigger (scientific oracle) | `session_015ot5hkJgSiBoWNA51fjZ1k` | make venv + make audit + falsification_sweep.py (1000/1000/100, n=505) → GATE VERDICT block | ~4 min | **PASS — CDK1−EPAS1: perm_p=0.0, ci_lower=0.664, Δbase=+0.062** |
| **PhL-8d** | 2026-04-26 16:21 Z | 1 Routine API trigger (dual verdict oracle) | `session_01CgsJYAPdvhJJwTuBt7QZLZ` | 2 equations in 1 trigger: Eq1 CA9−AGXT (FAIL, delta_baseline=0.0145) + Eq2 CDK1−EPAS1 (PASS, delta_baseline=0.0622); same gate, same thresholds | ~8 min | **FAIL + PASS** — methodology proof in one session |
| **PhL-9** | 2026-04-24 02:20 Z | 3 sessions (sequential Path A) | `sesn_…CaMnnL4…` last | sequential_fallback mode · structured-JSON handoff | **706.1 s** | OK |
| **PhL-9v2** | 2026-04-24 04:32 Z | 3 sessions (sequential Path A on real TCGA-KIRC) | `sesn_…CaMxrYQ…` proposer, `CaMy52X` searcher, `CaMyCzw` skeptic | 1 environment · 3 agents · 2 `files.upload()` mounts (`file_…CaMxrPd…` CSV, `file_…CaMxrSN…` law_proposals.json) | **300.4 s** | OK — Skeptic quoted `delta_baseline=+0.0587` on real data |
| **PhL-10 (mem)** | 2026-04-24 02:17 Z | 2 sessions (sessions 4-5 extending PhL-3 chain) | `agent_…CaMLDBC…` | Memory chain **3 → 5 lessons** server-side verified | n/a | PASS |
| **PhL-10 (oracle)** | 2026-04-26 (stage oracle) | 1 Routine API trigger (stage oracle, new Routine) | `session_01XGse8XYFtv3C1aKLZeMH9t` | 2 equations: CCNB1/PGK1 (FAIL, delta_baseline=0.007) + CXCR4/EPAS1 (PASS, AUROC 0.696, ci_lower=0.649, Δbase=+0.051); n=512 Stage I-II vs III-IV. Note: CLAIM_LOCK locks "KIRC Stage top AUROC = 0.689" (from stage_expanded local PySR run); 0.696 is the Routine oracle run result on the same equation — two different executions of the same law. | ~6 min | **FAIL + PASS** — second live oracle session |
| **PhL-12** | 2026-04-24 04:36 Z | 3 sessions (sessions 6-8 deepening PhL-10 chain) | same `store_id` | Memory chain **5 → 8 lessons** server-side verified | n/a | PASS |

**Cumulative across the Managed Agents evidence set:** 17 sessions
observed, 1 memory_store shared across 5 artefacts (PhL-3 → PhL-7 →
PhL-10 mem → PhL-12), 1 environment shared across 3 Path-A sequential
runs (PhL-9 + PhL-9v2), **2 Routine `/fire` sessions** inspectable
via browser (PhL-8d `session_01CgsJYAP…` + PhL-10 oracle
`session_01XGse8X…`), 2 public TCGA-KIRC files uploaded into an MA
environment and re-read across three sequential sessions. The longest
single Path-A chain is **706 s** end-to-end (PhL-9); the real-data
replication is **300 s** (PhL-9v2, smaller cohort, sharper prompts).

**Durability check (auditable).** Each of the 17 `sesn_…` / `agent_…`
/ `env_…` / `file_…` / `mem_…` ids listed above is server-side-retained
by Managed Agents and dereferenceable via `beta.sessions.events.list` /
`beta.environments.retrieve` / `beta.files.download` / raw
`/v1/memory_stores/{id}/memories` GET, so a reviewer with the
workspace's API key can replay any of them; the token/prefix-only
surface here does not expose credentials. See also the safety/compliance
note in the opening block.

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
│  [PhL-8d: dual-verdict FAIL+PASS, session_01CgsJYAPdvhJJwTuBt7QZLZ]           │
│  [PhL-10 oracle: stage FAIL+PASS, session_01XGse8XYFtv3C1aKLZeMH9t]           │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

## Why composing the two products is load-bearing

Managed Agents live on `platform.claude.com`; Routines live on
`code.claude.com`. Bridging them requires a Routine bearer token,
a distinct beta header, and a separate session-event surface. Most
implementations we've seen pick one and ignore the other. Lacuna uses both in the same pipeline: the Skeptic runs in Managed
Agents sessions (durable event log + memory); the nightly audit
runs in a Routine (`make audit` + rejection-log regen server-side).
`invoke_fn=make_routine_invoke_fn(...)` in `managed_agent_runner.py`
is the one-line swap point.
