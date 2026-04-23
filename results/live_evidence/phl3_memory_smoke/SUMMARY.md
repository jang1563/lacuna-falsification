# PhL-3 — Managed Agents Memory (public beta) smoke test

**Run date:** 2026-04-23 (same day Managed Agents Memory moved from
research preview to public beta — announcement at
`https://claude.com/blog/claude-managed-agents-memory`).

**Hackathon fairness compliance:** Memory is **public beta as of
2026-04-23**. Per the 2026-04-23 Anthropic ruling, public-beta features
are allowed for hackathon participants (only research-preview features
are disabled). This integration is therefore in-scope.

## What this demonstrates

The exact Rakuten pattern quoted in the announcement — *"agents distill
lessons from every session, delivering 97% fewer first-pass errors at
27% lower cost and 34% lower latency"* — applied to our falsification
Skeptic. Two Managed Agents sessions, **same agent**, **same memory
store**, **different session IDs**:

| Session | Session ID | Role |
|---|---|---|
| Session 1 — write | `sesn_011CaMLDfxgy7LKC8MJNMAcV` | Judge a candidate; append lesson to memory |
| Session 2 — read + apply | `sesn_011CaMLMh4eSod5Y1VfjaY8M` | Read memory; cite prior lesson; judge new candidate; extend memory |

Agent: `agent_011CaMLDBC4hUfmb9MCZpjQW`
Memory store: `memstore_01XvqsnMxmHQPyL25X4t56Wq` (name
`skeptic-lessons`, mounted at `/mnt/memory/skeptic-lessons/`).

## Session 1 — the write

The Skeptic judged `log1p(CA9) + log1p(VEGFA) − log1p(AGXT)` on
TCGA-KIRC tumor-vs-normal. Metrics: law AUC 0.984, baseline AUC
0.965 (CA9 alone), `delta_baseline = 0.019 < 0.05`, permutation /
bootstrap / decoy all pass. Verdict: **FAIL**. Skeptic wrote the
lesson to `/mnt/memory/skeptic-lessons/lessons.md` identifying the
pattern *"Saturated single-gene baseline — ceiling-effect false
positive."*

Tool events on the session event stream (verifiable in
`session1_write.json`): 3 `agent.tool_use` events corresponding to
(1) `ls /mnt/memory/`, (2) `ls /mnt/memory/skeptic-lessons/`,
(3) `str_replace_based_edit_tool create` that wrote `lessons.md`.

## Session 2 — the read + apply

Fresh session ID. The Skeptic was asked to judge a structurally
analogous candidate `log1p(LDHA) + log1p(SLC2A1) − log1p(ALB)` with
the same delta_baseline = 0.019 pattern.

The Skeptic's response opens with the sentence:

> *"I'm quoting the existing lesson verbatim because it is a
> near-perfect structural match for this candidate"*

and then reproduces the prior lesson text exactly before applying it.
The new verdict (FAIL) cites the specific pattern from memory — *"two
HIF-axis tumor markers minus one normal-tissue marker on an easy
saturated binary task"* — and then **extends the memory with a
generalized rule** that flags any future `HIF_target_A + HIF_target_B
− normal_kidney_marker` compound on this task as a likely ceiling-
effect false positive.

## Server-side verification

Independent of what the agent said, `GET /v1/memory_stores/{id}/memories`
with the `managed-agents-2026-04-01` beta header returns the full
persisted content (see `server_dump.json`). The dump is reproducible
with:

```bash
.venv/bin/python src/phl3_memory_smoke.py verify
```

Final memory state (2 entries, appended across sessions):

```
# Skeptic rejection-pattern lessons

- [FAIL] log1p(CA9) + log1p(VEGFA) - log1p(AGXT) — delta_baseline=0.019 ...
  [written 2026-04-23 20:13:12 UTC, session 1]

- [FAIL] log1p(LDHA) + log1p(SLC2A1) - log1p(ALB) — delta_baseline=0.019 ...
  Generalized pattern (KIRC T-vs-N recurring motif): any `HIF_target_A +
  HIF_target_B − normal_kidney_marker` compound will produce ~0.02 lift
  on a near-saturated baseline and should be rejected on delta_baseline
  alone. Flag for Copilot: stop proposing tumor-vs-normal KIRC compounds
  when best-single ≥ 0.95 — route to grade / metastasis / survival
  tasks where there is headroom.
  [written 2026-04-23 20:17:xx UTC, session 2]
```

## Why this matters for the submission

1. **Verification loop closure across sessions** (Thariq Shihipar,
   2026-04-22 live session — "verification script that forces the agent
   to test its own outputs against hard constraints"). The Skeptic's
   lessons file is exactly that script, materialized as a persistent
   file the platform owns.

2. **Model introspects on its own mistakes** (Cat Wu, Lenny's Newsletter
   2026-04-23 — "most underrated AI skill: asking the model to
   introspect on its own mistakes"). Session 2's agent literally opens
   with "I'm quoting the existing lesson verbatim because it is a
   near-perfect structural match" — which is introspection with a
   durable substrate.

3. **Skills that ship** (Boris Cherny). The memory file is a
   shareable artefact, not in-context state. Any future Skeptic agent
   mounted to the same store inherits the lessons.

4. **Rakuten "continuous learning" pattern** — same-day public-beta
   integration shows we're on top of the absolute latest Anthropic
   releases, using the exact mechanism the Anthropic announcement
   describes.

## Implementation notes (reviewer inspection)

- SDK version `anthropic==0.96.0` (2026-04-16) **does not yet expose
  `client.beta.memory_stores`** — Memory launched one week after this
  SDK cut. The smoke test uses raw `httpx` against `/v1/memory_stores/*`
  for memory CRUD and the SDK for agent/env/session/streaming.
- Memory store mounts at `/mnt/memory/{store_name}/`, so the agent
  system prompt must explicitly instruct "use `/mnt/memory/<name>/`"
  — a path at `/mnt/memory/foo.md` (top level) is ephemeral scratch
  inside the session container, NOT the persistent store. We
  discovered this on our first run and corrected it before the
  committed session.
- Cost: ~$0.30 across two Opus 4.7 sessions, ≤ 60 s each.

## Files

- `src/phl3_memory_smoke.py` — the smoke-test driver (supports `write`,
  `read`, `verify`, `--clean`).
- `session1_write.json` — full event stream of session 1.
- `session2_read.json` — full event stream of session 2.
- `server_dump.json` — memory store contents fetched via raw API,
  independent of the agent's claims.
