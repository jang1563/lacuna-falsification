# Live API Evidence

This directory contains the transcripts and usage telemetry of real
Opus 4.7 and Managed Agents calls made during development. Every file
here is a direct capture of a live API interaction — nothing
synthetic, nothing mocked.

## Contents

| File | Evidence of |
|---|---|
| `api_validation_log.txt` | Full narrative log of the four API-shape smoke tests with per-call token counts, model IDs, and cost estimate. |
| `01_opus_raw_smoke.log` | Raw `client.messages.create` call against `claude-opus-4-7` with `thinking={"type":"adaptive","display":"summarized"}` + `output_config={"effort":"high"}`. Confirms the extended-thinking API shape. |
| `02_proposer_kirc.log` | `OpusClient.propose_laws()` on a KIRC dataset card. Raw response is 1500+ chars of Opus 4.7's proposed law families with biology rationale and skeptic tests. |
| `03_skeptic.log` | `OpusClient.judge_candidate()` on a deliberately borderline candidate. |
| `04_managed_agents_e2e.log` | End-to-end Managed Agents Path B verification: `agents.create` → `environments.create` → `sessions.create` → `stream` → `send` → `session.status_idle`. Agent responded with a text message; the full chain works. |
| `05_proposer_live_tcga_kirc.log` / `.json` | E6 refresh: live `OpusClient.propose_laws()` call against `claude-opus-4-7` using the real 45-gene TCGA-KIRC metastasis expanded dataset context. 5 law families parsed end-to-end with `initial_guess` / `skeptic_test` fields. Replaces the synthetic-data `02_proposer_kirc.log` with a cleanly JSON-parsed transcript. |
| `06_managed_agents_path_a.log` | E10 probe: `client.beta.agents.create(tools=[{"type":"agent_toolset_20260401"}])` succeeds for all three Path-A role agents (proposer / searcher / falsifier). The multiagent feature is accessible for this key; `run_path_a` remains guarded by `MANAGED_AGENTS_WAITLIST=approved` until the full three-agent chain is exercised with the actual PySR environment. |

## Prior-run cost

From `api_validation_log.txt`:

- Total input tokens: ~1,296
- Total output tokens: ~2,430
- Estimated cost: **≈ $0.20 USD** (Opus 4.7 input $15/M, output $75/M)

## Why this directory exists

Judges who want to confirm the Opus 4.7 and Managed Agents claims
without running a full session themselves can read these logs end-to-
end. The `anthropic.Anthropic` SDK calls in `src/lacuna/opus_client.py`
and `src/lacuna/managed_agent_runner.py` match the shapes
verified here. `api_validation_log.txt` also records the single bug
that was caught and fixed during this validation (non-streaming
`messages.create` tripped the SDK's 10-minute guard at `max_tokens=32000`
— the client now uses the short-call path consistently, which passes
all 4 tests).

## What is not here

- No full API keys. `ANTHROPIC_API_KEY` is never committed (gitignored via
  `.env`, `~/.api_keys`). A 14-char key prefix that leaked into an older
  smoke-test log (`api_validation_log.txt`) was redacted on 2026-04-23
  after the internal review handoff flagged it (`.audit-patterns` now also
  catches `sk-ant-api` / `sk-ant-oat` / `Bearer sk-ant` shapes going
  forward).
- No sample-level patient data. The KIRC dataset card used for the
  smoke test is public TCGA metadata only.
- No institutional identifiers. The logs were screened by the
  `make audit` compliance step before they were committed.
