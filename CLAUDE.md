# CLAUDE.md — Lacuna Falsification

**TL;DR.** Falsification-aware biological law discovery built around Opus 4.7.
Opus proposes compact law families (and the skeptic test for each, *before* any fit);
PySR searches concrete candidates; a deterministic 5-test Python gate attacks them;
only survivors get an Opus interpretation. On real TCGA-KIRC the gate rejects 100+
candidates across four tasks (each already solved by one gene) **and** accepts
9/30 candidates on metastasis with a 45-gene panel, led by the two-gene law
`TOP2A − EPAS1` that reproduces the published ccA/ccB ccRCC subtype axis from
unconstrained symbolic regression.

## Before you touch anything here

Run `make audit` first (pattern list in `.audit-patterns`; excludes itself +
`Makefile`). Any commit that introduces an institutional / cluster / user
string will fail the audit and block `git push`.

## Repo map

- `src/lacuna/` — library: `falsification.py` (5-test gate),
  `opus_client.py` (Opus 4.7 streaming wrapper), `cli.py` (`compare` + `replay`
  + `loop`), `managed_agent_runner.py` (Path B public beta + Path A waitlist
  + Path C Routine driver), `data_loader.py` (DatasetCard abstraction — E4),
  `bench.py` (Lacuna-Bench v1 rediscovery scorer — post-hackathon),
  `failure_atlas.py` (failure-mode labeller — post-hackathon),
  `rl_readiness.py` (RL/RLVR readiness diagnostic — post-hackathon).
- `src/` (top-level) — runnable scripts: `pysr_sweep.py`, `falsification_sweep.py`,
  `make_plots.py`, `plot_track_a.py`, `track_a_survivor_*.py`,
  `track_a_model_ablation.py` (E2), `mcp_biology_validator.py` (E8).
- `data/` — CSVs + build scripts (`build_tcga_kirc.py`, `build_tcga_luad.py`, etc.)
- `results/` — committed artefacts: `flagship_run/`, `tier2_run/`,
  `track_a_task_landscape/` (4-task matrix + metastasis_expanded survivors),
  `track_b_gate_robustness/`, `live_evidence/`, `ablation/`, `qa/`,
  `lacuna_bench_v1/` (post-hackathon rediscovery benchmark audit),
  `failure_atlas_v1/` (post-hackathon labelled failure memory),
  `rl_readiness_v1/` (post-hackathon RL/RLVR readiness diagnostic).
- `docs/` — judge-facing docs (all ≤ 400 lines): `methodology.md`,
  `why_opus_4_7.md`, `submission_description.md`, `survivor_narrative.md`,
  `loom_script.md`, `submission_form_draft.md`. (`docs/paper/` is local-only,
  gitignored — paper drafts are excluded from the public repo for
  conference double-blind review.)
- `prompts/` — JSON-schema-enforced Opus 4.7 prompts.
- `config/` — `datasets.json`, `law_proposals.json`, `dataset_cards/` (E4).
- `.claude/agents/` — Claude Code subagents (below).
- `.mcp.json` — MCP server registrations. The `biology-validator`
  server (stdio transport, `src/mcp_biology_validator.py`) exposes two
  tools to the Skeptic subagent: `validate_law(gene_symbols, disease?)`
  runs a PubMed co-mention E-utilities search; `fetch_cohort_summary
  (project_id)` returns TCGA GDC project metadata. The MCP SDK is an
  optional install — without it, the tools can still be exercised
  directly: `python src/mcp_biology_validator.py --tool validate_law
  --genes TOP2A,EPAS1 --disease ccRCC`.

## Agent roles (who does what)

| Agent | Role | Model | Tools |
|---|---|---|---|
| Proposer | Emit 3-5 law families + skeptic test per family, *before* any fit. | Opus 4.7 | Read, Bash |
| Skeptic | Adversarially review a candidate's metric bundle. Must cite specific values; reject if unconvincing. | Opus 4.7 | Read, Grep, Bash, WebFetch |
| Interpreter | For a passed survivor, emit mechanism + prediction + hypothesis. | Opus 4.7 | Read, WebFetch |
| QA validator | On every incoming commit, run `make test` + `make audit`. | Opus 4.7 | Read, Bash |

See `.claude/agents/{proposer,skeptic-reviewer,interpreter,qa-validator}.md`
for the individual prompts.

**Agent execution sequence (for new hypotheses on a new dataset):**
1. **Proposer** — reads dataset card + gene list → emits 3-5 law families + one kill-test per family (before any fit).
2. **PySR** (no LLM) — symbolic regression produces concrete equation candidates from the seeded families.
3. **5-test Python gate** (no LLM) — deterministic: permutation null, bootstrap CI, baseline comparison, confound incremental, decoy-feature null. BH-FDR across candidates.
4. **Skeptic** — receives gate metric bundle only (never the Proposer's rationale); emits PASS / FAIL / NEEDS_MORE_TESTS with cited values.
5. **Interpreter** — for gate-PASS survivors only: mechanism hypothesis + testable prediction + explicit "what this is not" caveat.

Context isolation is load-bearing: steps 4 and 5 run in separate Managed Agents sessions from step 1. The Skeptic can never see the Proposer's reasoning tokens.

## Key commands

| Command | What it does |
|---|---|
| `make install` | Editable install into `.venv` (Python 3.10-3.13, Julia 1.10 for PySR). |
| `make test` | pytest with pre-hackathon scaffold tests ignored. Current local-runnable suite: 115/115. |
| `make audit` | Compliance grep. Must print `OK`. |
| `make demo` | Guided synthetic proposer handoff; requires API key and prints PySR/gate commands. |
| `make demo-kirc` | KIRC-flavoured guided handoff. |
| `make status` | Branch + last 5 commits + cost-ledger tail. |

## Execution flow

```
┌──────────────────────────────────────────────────────────────┐
│   Opus 4.7  ┃  PySR            ┃  Python gate     ┃  Opus 4.7 │
│   Proposer  ┃  Search          ┃  Falsification   ┃  Interpret│
│   + Skeptic ┃  (variable_names)┃  5-test + BH-FDR ┃  survivor │
│   test      ┃                  ┃                  ┃           │
└──────────────────────────────────────────────────────────────┘
       │            │                    │                 │
    law_family   candidates           verdicts          mechanism
    (JSON)       (JSON)               (JSON)            (JSON)
```

## Phase handshake protocol (N / Q / E)

The repo runs under concurrent sessions during the hackathon push:

- **Phase N** (Narrative) — docs in `docs/`, `STATUS.md`, `README.md`.
  Commit prefix `[N]`.
- **Phase Q** (QA) — `make test`, `make audit`, `make demo*`, plot
  sanity, live-transcript coherence. Commit prefix `[QA]`.
- **Phase E** (Enhancement, current) — AI-for-Science / discovery /
  platform upgrades. Commit prefix `[E]`. Split across 3 lanes:
  - Lane 1 = Platform (CLAUDE.md, DatasetCard, LUAD, MCP, paper)
  - Lane 2 = Experiments (cross-model ablation, cohort replay, BRCA)
  - Lane 3 = Narrative + stretch (citations, parallel sub-agent harness)

Cross-phase / cross-lane messages use `HANDOFF_to_<target>.md` at the
repo root (gitignored via `.gitignore` `HANDOFF_to_*.md`). Every commit
passes `make test` + `make audit` before `git push`.

## Imports

@docs/methodology.md
@docs/survivor_narrative.md
@docs/why_opus_4_7.md

## Lessons

One-liner notes on non-obvious learnings (compounding-engineering loop).

- 2026-04-22 · Opus 4.7 `thinking={"type":"adaptive","display":"summarized"}` +
  `output_config={"effort":"high"}` with `max_tokens=32000` trips the SDK
  10-minute guard on non-streaming `.messages.create`. Must use
  `.messages.stream()` context manager (see `src/lacuna/opus_client.py`).
- 2026-04-22 · PySR 0.19.4 on older Julia lacks `guesses=` kwarg. Wrap the
  fit call in `try / except TypeError` and drop `guesses` + `fraction_replaced_guesses`
  on fallback (see `src/pysr_sweep.py`).
- 2026-04-22 · Falsification gate must broadcast scalar law scores:
  `if arr.ndim == 0: arr = np.full(X.shape[0], float(arr))` — symbolic
  regression can emit constants for degenerate candidates.
- 2026-04-22 · Path C Routine driver (`run_path_c_routine`) is the shippable
  answer to Boris Cherny's "no one has cracked server-side Routines yet"
  (4/21 kickoff). Keep it local: inject `invoke_fn` + `sleeper` for testability
  and leave the native Routines API swap-in as a single function pointer.
  Watch-dir uses `(name, size, mtime)` fingerprint — deterministic and no
  external watcher daemon.
