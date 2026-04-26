# Lacuna

> *Rejects 194 of 203 candidate laws — including its own.*

<img src="https://img.shields.io/badge/Python-3.10+-1E3A8A?style=flat-square" alt="Python 3.10+" />
<img src="https://img.shields.io/badge/Built_with-Claude_Opus_4.7-1E3A8A?style=flat-square" alt="Built with Claude Opus 4.7" />
<img src="https://img.shields.io/badge/Hackathon-Cerebral_Valley_2026-faf9f5?labelColor=141413&style=flat-square" alt="Cerebral Valley Hackathon 2026" />

Lacuna is a **falsification-first** pipeline for biological law discovery, built around Opus 4.7. A verification-isolated three-session loop (Proposer / Skeptic / Interpreter, each in its own Managed Agents session with separate context windows) proposes compact symbolic laws; a pre-registered five-test Python gate — running **before** any LLM judgement — rejects the ones that can't survive contact with held-out biology. On real TCGA-KIRC the gate **rejects 194 of 203 candidate evaluations under the 5-test classification gate** across 11 task × panel combinations; **9 candidates pass on metastasis** (45-gene expanded panel), led by `TOP2A − EPAS1` — the published ccA/ccB ccRCC subtype axis, rediscovered from unconstrained symbolic regression. The 2-gene law then **replicates on the independent IMmotion150 Phase-2 trial cohort** (n=263, log-rank p=0.0003, Cox HR=1.36, 7.5-month median-PFS gap) under **three separately pre-registered survival kill tests** (log-rank on median split, Cox HR per z-score, Harrell C-index) — a different gate, not the same 5-test classification gate, committed before the survival analysis ran. When the system's own H1 LLM-SR loop later proposed a 3-gene extension (adding `SLC22A8`), that **extension failed the same separately pre-registered IMmotion150 survival replay** ([PhL-1, commit 60d3952](results/track_a_task_landscape/external_replay/immotion150_slc22a8/SUMMARY.md)) — **our own downstream best output, killed by our own gate on independent data**. That is what a verification loop looks like when the judgment function is outside the model.

> **Honest scoping note.** The 9 metastasis survivors clear 4 active tests of the 5-test gate — the `delta_confound` leg is null for all 9 because the metastasis task has no non-degenerate covariates after filtering. The gate design specifies this as "run the confound leg when covariates vary; otherwise skip." So "5-test gate" here is the *framework*; the *active* legs for metastasis are permutation, bootstrap CI lower-bound, sign-invariant single-feature baseline, and decoy null. See `docs/methodology.md §3` for the exact specification.

> **On rediscovery as evaluation.** Re-deriving the published ccA/ccB axis under a pre-registered gate — without seeding the law family — is the evaluation paradigm formalised by FIRE-Bench ([arXiv 2602.02905](https://arxiv.org/abs/2602.02905)), where current SOTA agents score <50 F1 on rediscovering established findings. The contribution here is the workflow that produces that recovery deterministically, not a claim of novel biology.

Built by a biomedical postdoc for the *Built with Opus 4.7* Hackathon · April 2026 · Claude Code did the plumbing; domain knowledge did the framing.

---

## Read first (by persona)

- **If you are evaluating the agentic / Claude-Code architecture:**
  start with [`docs/methodology.md §4`](docs/methodology.md) (three
  Managed Agents sessions with verification isolation and a verified
  Path B run) and
  [`src/lacuna/managed_agent_runner.py`](src/lacuna/managed_agent_runner.py).
  Live agent / environment / session / stream trace is at
  [`results/live_evidence/04_managed_agents_e2e.log`](results/live_evidence/04_managed_agents_e2e.log).
  Submission run uses public-beta features only: Path B (single agent,
  `agent_toolset_20260401`), Path A as a sequential chain of three Path
  B sessions with structured-JSON handoff, Path C via Claude Code
  Routines `/fire` with local watch-dir fallback.
  Brain/body-decouple demo: `lacuna persist-events` +
  `replay-events` CLI two-liner.
  Two Agent Skills wrap the methodology as natural-language entry
  points: [`.claude/skills/falsification-gate/SKILL.md`](.claude/skills/falsification-gate/SKILL.md)
  applies the pre-registered 5-test gate to a candidate, and
  [`.claude/skills/pre-register-claim/SKILL.md`](.claude/skills/pre-register-claim/SKILL.md)
  locks a claim's kill-tests into a tamper-evident YAML before any
  fit runs. Compose them as `pre-register-claim` → `falsification-gate`;
  the second skill reads the YAML the first emits.
- **If you are evaluating developer experience and reproducibility:** `make
  venv && make test && make audit` is the local-runnable happy path
  (105 tests, ~90 s, no API key needed). The `make demo` / `make
  demo-kirc` targets are scaffolding for the full pipeline (Opus call
  + PySR sweep + falsification sweep + replay) and require an
  ANTHROPIC_API_KEY plus the multi-step manual handoff that `compare`
  prints; treat them as a guided walkthrough of the Night-2 / Night-3
  / Night-4 sequence rather than a single one-shot end-to-end target.
  all judge-facing docs in `docs/` are ≤ 400 lines, all figures in
  `results/plots/` and `results/track_a_task_landscape/plots/` are
  reproducible from `src/make_plots.py`, `src/plot_track_a.py`,
  `src/track_a_survivor_plots.py`. `make audit` returns `OK` on
  every commit — the compliance check runs against a pattern file
  in `.audit-patterns`.
- **If you are evaluating real-world impact and accessibility:**
  the project started as a bioinformatics-postdoc
  question about confirmation bias in AI-for-Science and ends with
  a concrete engineering artefact that rejects textbook biology the
  researcher had expected to survive and accepts a 2-gene subtype
  axis the researcher had *not* planted. The user-side workflow for
  a new task is "drop a CSV with a label column and a gene-name
  columns, run `lacuna compare --dataset-card <your_card>.json`,
  read the pass/fail table." See
  [`docs/demo_walkthrough.md`](docs/demo_walkthrough.md) for the
  full reproducible steps and [`docs/paper/paper.pdf`](docs/paper/paper.pdf)
  for the 6-page methodology + results write-up in workshop-paper
  form.
- **If you are evaluating the science (domain-expert):** start with
  [`results/track_a_task_landscape/SUMMARY.md`](results/track_a_task_landscape/SUMMARY.md)
  (4-task cross-matrix, both panel sizes), then
  [`results/track_a_task_landscape/survivor_robustness/SUMMARY.md`](results/track_a_task_landscape/survivor_robustness/SUMMARY.md)
  (6-axis stress test of the `TOP2A − EPAS1` survivor, with the
  explicit caveat on the pair-with-interaction baseline), then
  [`results/track_b_gate_robustness/SUMMARY.md`](results/track_b_gate_robustness/SUMMARY.md)
  (6-axis robustness of the reject verdict). The Phase G + I rigor
  extensions add five pre-registered analyses on the same survivor
  (12/13 of their own predictions PASS, 1 honest FAIL):
  [`rigor_extension/SUMMARY.md`](results/track_a_task_landscape/rigor_extension/SUMMARY.md)
  (G2: AUPRC 0.321 / 2.05× lift, Brier 0.122, calibration slope 0.979),
  [`knockoff_v2/SUMMARY.md`](results/track_a_task_landscape/knockoff_v2/SUMMARY.md)
  (G1: 0/45 individually selected — signal is genuinely compound),
  [`rashomon_set/SUMMARY.md`](results/track_a_task_landscape/rashomon_set/SUMMARY.md)
  (I2: rank 1/990 in 2-gene-difference class, tight set = 3 pairs),
  [`clinical_utility/SUMMARY.md`](results/track_a_task_landscape/clinical_utility/SUMMARY.md)
  (I3: Cohen's d 0.856, OR 2.07/SD; honest screening-FAIL on P3),
  [`information_theory/SUMMARY.md`](results/track_a_task_landscape/information_theory/SUMMARY.md)
  (I4: simple difference captures 98.1% of bivariate joint MI).
  Every reported number has a JSON file behind it in the same directory.
- **If you are time-boxed (5 minutes) and want to challenge the claims:**
  read [`docs/judge_faq.md`](docs/judge_faq.md). It consolidates the
  12 most-likely reviewer challenges (rediscovery vs discovery,
  AUROC ceiling, cohort independence, Sonnet drop-in, memorisation
  audit, `delta_confound` null caveat) with 30-second answers and
  direct links to the load-bearing evidence file for each.

---

## Workflow (5 stages)

```
Proposal → Search → Falsification → Survivor → Replay
```

| Stage | What happens | Model |
|---|---|---|
| **Proposal** | Opus 4.7 emits 3–5 compact law families *and* the skeptic test for each, **before any fit**. Required to include at least one negative control. | Opus 4.7 (extended thinking) |
| **Search** | PySR symbolic regression instantiates candidates with `variable_names=gene_cols` so equations come back in biological names. | Local (no API) |
| **Falsification** | Pure Python gate: two-sided permutation, bootstrap CI lower-bound, sign-invariant baseline, incremental-covariate confound, decoy-feature null, BH-FDR. Opus does **not** run this. | Python (deterministic) |
| **Survivor** | Opus 4.7 reviews each candidate's metric pattern and writes a biological mechanism hypothesis for the survivors. | Opus 4.7 (extended thinking) |
| **Replay** | Survivors replayed on an independent cohort with per-cohort z-score standardization. Three-way verdict: law_transfers / workflow_transfers / neither. | Opus 4.7 spot-check |

![Lacuna — 5-stage discovery pipeline](docs/architecture.png)

---

## Key Modules

| File | Role |
|---|---|
| [`src/lacuna/falsification.py`](src/lacuna/falsification.py) | 5-test statistical gate |
| [`src/lacuna/opus_client.py`](src/lacuna/opus_client.py) | Opus 4.7 three-role wrapper + JSON-fence-tolerant parser |
| [`src/lacuna/managed_agent_runner.py`](src/lacuna/managed_agent_runner.py) | Path B (single agent, public beta) + Path A (sequential chain of 3 Path B sessions) + Path C Routine driver + event-log persistence/replay |
| [`src/lacuna/routines_client.py`](src/lacuna/routines_client.py) | Claude Code Routines `/fire` HTTP client (research-preview beta header) |
| [`src/lacuna/cli.py`](src/lacuna/cli.py) | `lacuna compare` + `replay` commands |
| [`src/pysr_sweep.py`](src/pysr_sweep.py) | PySR sweep with law-family injection, train/test split, novelty scoring |
| [`src/falsification_sweep.py`](src/falsification_sweep.py) | Batch falsification runner + BH-FDR |
| [`prompts/`](prompts/) | JSON-schema-enforced Opus 4.7 prompts |
| [`config/law_proposals.json`](config/law_proposals.json) | KIRC law families (pathway + anchor + negative controls) |
| [`data/examples/make_kirc_demo.py`](data/examples/make_kirc_demo.py) | Synthetic KIRC-compatible CSV generator |

---

## Quick Start

**Python ≥ 3.10 required** (`pyproject.toml` needs `X | Y` union syntax; `match` statements in `src/lacuna/managed_agent_runner.py` also require 3.10+). macOS default `/usr/bin/python3` is 3.9.x — use a venv. `make install` creates `.venv/` and points the Makefile at it by default.

```bash
# Install into .venv (Python ≥ 3.10, Julia 1.10.0 for PySR)
python3 -m venv .venv && .venv/bin/pip install -e .

# Run tests (no API key needed — all mocked)
python -m pytest tests/ -v

# Generate synthetic KIRC-compatible demo data
python data/examples/make_kirc_demo.py

# Smoke test: 4 candidates (2 strong + 2 negative controls) → 1 survivor expected
cat > /tmp/candidates.json <<EOF
[
  {"equation": "log1p(CA9) + log1p(VEGFA) - log1p(AGXT)", "complexity": 8},
  {"equation": "log1p(LDHA) - log1p(ALB)",                "complexity": 5},
  {"equation": "log1p(ACTB) - log1p(GAPDH)",              "complexity": 5},
  {"equation": "log1p(MKI67) - log1p(RPL13A)",            "complexity": 5}
]
EOF
python src/falsification_sweep.py \
  --candidates /tmp/candidates.json \
  --data data/examples/flagship_kirc_demo.csv \
  --genes CA9,VEGFA,LDHA,SLC2A1,NDUFA4L2,AGXT,ALB,ACTB,GAPDH,RPL13A,MKI67 \
  --covariate-cols age,batch_index \
  --output /tmp/report.json
# → "4 candidates → 1 survived falsification"

# Full pipeline with Opus 4.7 (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=sk-ant-...
lacuna compare --config config/datasets.json \
  --proposals config/law_proposals.json \
  --flagship-dataset kirc --output-root artifacts/
# → prints the PySR + falsification commands to run next
```

---

## The 5-Test Falsification Gate

Every candidate must clear all five tests before being called a survivor.
Thresholds pre-registered in [`falsification.py`](src/lacuna/falsification.py).

| Test | Statistic | Threshold |
|---|---|---|
| `label_shuffle_null` | Two-sided permutation p (1000 shuffles) | `p < 0.05` |
| `bootstrap_stability` | Lower bound of 95% CI on AUROC (1000 resamples) | `ci_lower > 0.6` |
| `baseline_comparison` | `law_AUROC − max_i max(AUROC(x_i), 1 − AUROC(x_i))` | `delta > 0.05` |
| `confound_only` | `AUROC(LR(cov + law)) − AUROC(LR(cov))` | `delta > 0.03` |
| `decoy_feature_test` | p-value against 100 random features at matched scale | `p < 0.05` |

Multiple candidates are tested per run → permutation p-values are adjusted with
Benjamini-Hochberg FDR across the family, and **the gate uses the FDR-adjusted p**.

![Rejection landscape — 194/203 candidate evaluations rejected across 11 task × panel combinations](docs/figures/rejection_landscape.png)

---

## Example Output (synthetic KIRC demo)

A representative flagship run, with Opus 4.7 emitting 2 pathway laws + 2 explicit
negative controls:

```text
Candidates (Opus 4.7, Proposer role):
  C1  log1p(CA9) + log1p(VEGFA) - log1p(AGXT)    [HIF-axis vs normal]
  C2  log1p(LDHA) - log1p(ALB)                   [Warburg vs liver-like normal]
  C3  log1p(ACTB) - log1p(GAPDH)                 [Housekeeping NEGATIVE CONTROL]
  C4  log1p(MKI67) - log1p(RPL13A)               [Proliferation NEGATIVE CONTROL]

Falsification gate (Python — Opus does not execute this):
  C1  auc=0.83  ci_lo=0.79  p_fdr=0.000  Δbase=+0.11  Δconf=+0.31  decoy=0.00  PASS
  C2  auc=0.74  ci_lo=0.69  p_fdr=0.000  Δbase=+0.02  Δconf=+0.22  decoy=0.00  FAIL (delta_baseline)
  C3  auc=0.52  ci_lo=0.46  p_fdr=0.520  Δbase=-0.21  Δconf=+0.00  decoy=0.50  FAIL (all 5)
  C4  auc=0.54  ci_lo=0.49  p_fdr=0.179  Δbase=-0.18  Δconf=+0.03  decoy=0.12  FAIL (4/5)

1 / 4 survives. Both Opus-planted negative controls are killed by the gate,
and one pathway-grounded law (Warburg contrast) is killed because LDHA alone
is nearly as discriminative.
```

This is the "shock moment": the gate is rigorous enough to kill a textbook
Warburg law when LDHA alone does nearly the same job. The surviving HIF-axis
law earned that survival by genuinely adding 0.11 over any single gene.

---

## Running as a Routine (Path C)

Boris Cherny in the 2026-04-21 *Built with Opus 4.7* kickoff flagged server-side
Routines — Claude sessions that wake on a schedule and outlive the laptop — as
the feature space "no one has cracked yet." Path C is Lacuna's answer:
a replication-watchdog driver that re-runs the Managed Agent on a cadence or
when a watched directory changes.

```bash
# Fire once (equivalent to Path B, but with a JSONL verdict log)
lacuna loop --night 3 --interval-seconds 0 --max-iterations 1

# Poll every 30 minutes, 10 times, logging to a dated JSONL
lacuna loop --night 3 --interval-seconds 1800 --max-iterations 10

# Watch an input directory — only invoke when a new cohort CSV lands
lacuna loop \
    --night 3 \
    --watch-dir inputs/new_cohorts \
    --interval-seconds 600 \
    --max-iterations 0       # unbounded, exit with SIGINT
```

Each iteration appends a verdict to `results/routine/verdicts.jsonl`
(`iteration`, `timestamp`, `night`, `watch_fingerprint`, `session_id`,
`status`, `output_chars`). The implementation in
`src/lacuna/managed_agent_runner.py::run_path_c_routine` exposes an
`invoke_fn` hook so a native Routines API can be swapped in once the public
interface stabilizes — today's loop driver is intentionally local so the repo
ships without a dependency on an unreleased API.

For the best long-running experience, use **Claude Code's Auto permission
mode** (shift+tab ×3 from the CLI) so the loop does not stall on permission
prompts. Max-plan or API-credit users only; Pro plan does not support it.

---

## Demo Data

`data/examples/flagship_kirc_demo.csv` and `transfer_kirc_demo.csv` are
generated by `make_kirc_demo.py`. Columns share the gene-name contract with
real TCGA-KIRC + GSE40435 data (CA9, VEGFA, LDHA, AGXT, ALB, SLC2A1,
NDUFA4L2, ACTB, GAPDH, RPL13A, MKI67) + `age` + `batch_index` covariates.
No patient data. No private identifiers.

CSV contract:

```
sample_id, label (disease/control or 0/1), age, batch_index, <gene columns...>
```

---

## Broader Program

This artifact is the Opus 4.7-centered proof-of-concept of a larger research
program — **NegBioDB**, a structured database of ~32.8M confirmed negative
biomedical results (drug–target inactives, failed clinical trials, protein
non-interactions, non-essential genes, benign variants) paired with benchmarks
for publication-bias propagation into ML/LLM predictions. Lacuna
operationalizes NegBioDB's core thesis — falsification as the expensive,
neglected half of scientific inference — on real cancer-genomics data. The
public NegBioDB repository will be linked here at release.

A companion analysis strand applies the same falsification posture to the
audit framework itself — validating it against clinical trial outcomes across
ccRCC, DIPG, and IPF (104 drug-target pairs across three diseases, 9,943
Phase 3 trials). The
honest result: the framework discriminates curated panels from random targets
(16/42 null-sampling tests BY-FDR significant at q < 0.10), but it does NOT
predict trial failure (trial-level GEE NULL after Bonferroni × 5). The initial
4.6× enrichment claim was a Track-1 selection-bias artifact — corrected by the
framework itself via proper failure-mode stratification (Track 1 futility-
terminated OR = 6.41 vs Track 2 completed-missed-primary OR = 0.13, Woolf
homogeneity Z = 19.97, p ≪ 10⁻⁸⁷). Rejection-as-product applied to the
tool's own validation claims. See [`docs/failure_network_v3_appendix.md`](docs/failure_network_v3_appendix.md).

---

## Hackathon compliance notes

Per the *Built with Opus 4.7* rules and the 2026-04-23 / 2026-04-24
Discord Q&A clarifications:

**Code provenance.** Every commit in `git log` has a timestamp from
2026-04-22 04:01 ET or later (the earliest commit in the repo). All
code in the submitted tree was written during the hackathon. Pre-
hackathon scaffold files (`src/lacuna/contracts.py`, `qc.py`,
`reuse_inventory.py`, `reuse_plan.py`, `staging.py`, `workflow_data.py`
plus a few config / docs / test files) are explicitly excluded via
`.gitignore` and are not part of the submission — `git ls-files` does
not include any of them. The hackathon-built code is the artefact; no
pre-existing project serves as "underlying infrastructure" in the
git-lex sense.

**Managed Agents features.** Per Anthropic's 2026-04-23 response to
our Agent Teams waitlist request, research-preview features are
disabled for hackathon participants to keep evaluation fair. This
submission uses public-beta features only: Path B (single agent +
`agent_toolset_20260401`), Path A as a sequential chain of three
Path B sessions, Path C via Claude Code Routines `/fire` HTTP client.
The orchestrator-with-`callable_agents` code path exists in
`_run_path_a_callable_agents` as an architectural reference, guarded
by an env flag that is not set during the submitted run.

**Data access.** Every dataset used in the pipeline is publicly
accessible without authentication or email registration:

| Dataset | Source | Access |
|---|---|---|
| TCGA-KIRC (STAR TPM + clinical) | GDC (gdc.cancer.gov) open-access | `data/build_tcga_kirc*.py` |
| GSE40435, GSE53757 | NCBI GEO | `data/build_gse*.py` |
| IMmotion150 Phase-2 (Nat Med 2018, PMID 29867230) | cBioPortal REST API (`rcc_iatlas_immotion150_2018`) | `data/build_immotion150.py` |
| CPTAC-3 ccRCC proteogenomic (Clark Cell 2019) | PDC GraphQL + cBioPortal mirror | `data/build_cptac3_ccrcc.py` |
| TCGA-BRCA, TCGA-LUAD | GDC open-access | `data/build_tcga_brca.py`, `build_tcga_luad.py` |

No dataset requires an institutional-email login, dbGaP controlled-
access application, or any other gate that would fail the Q&A test
*"this isn't accessible to everyone."* Published-research knowledge
cited in the prompts is open-access per PubMed / arXiv / DOI.

**Repo visibility.** Public during the judging window (`git remote -v`
→ `github.com/jang1563/lacuna-falsification`). MIT licensed.

---

## License

Code: MIT
Data artifacts: CC-BY-4.0
