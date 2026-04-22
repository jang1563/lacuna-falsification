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

## Prior-run cost

From `api_validation_log.txt`:

- Total input tokens: ~1,296
- Total output tokens: ~2,430
- Estimated cost: **≈ $0.20 USD** (Opus 4.7 input $15/M, output $75/M)

## Why this directory exists

Judges who want to confirm the Opus 4.7 and Managed Agents claims
without running a full session themselves can read these logs end-to-
end. The `anthropic.Anthropic` SDK calls in `src/theory_copilot/opus_client.py`
and `src/theory_copilot/managed_agent_runner.py` match the shapes
verified here. `api_validation_log.txt` also records the single bug
that was caught and fixed during this validation (non-streaming
`messages.create` tripped the SDK's 10-minute guard at `max_tokens=32000`
— the client now uses the short-call path consistently, which passes
all 4 tests).

## What is not here

- No secrets. `ANTHROPIC_API_KEY` does not appear in any of these logs.
- No sample-level patient data. The KIRC dataset card used for the
  smoke test is public TCGA metadata only.
- No institutional identifiers. The logs were screened by the
  `make audit` compliance step before they were committed.
