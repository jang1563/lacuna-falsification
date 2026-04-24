# External validation / generalization — DIPG rescue engine

**Purpose:** mirror of key artefacts from the sibling `dipg_rescue/`
project showing the same Theory Copilot 4-role engine (Proposer /
Searcher / Skeptic / Interpreter) re-applied to a structurally
distant second disease: H3 K27M-mutant diffuse intrinsic pontine
glioma (DIPG / diffuse midline glioma). This mirror exists so
submission materials (Loom narration, submission form) can reference
the result without leaving the `theory_copilot_discovery` tree.

## Source

- Sibling repo: `../dipg_rescue/` (separate git repo, commit
  `0a9e154` as of 2026-04-24).
- Pre-registration lock commit: `8a4ecc5` — "PREREG LOCK: 15 DIPG
  rescue candidates, 4-role engine, 5-axis falsification gate"
  (locked before any engine run).
- Full run directory: `../dipg_rescue/runs/2026-04-24_run01/`
  (1.3 MB, 15 candidates × 4 roles × JSON + raw + usage).

## What is included here

- `RESULTS.md` — verdict distribution summary (15 candidates, 7
  supported, 7 mixed, 1 insufficient, 0 missing) + ranked-by-score
  table.
- `top_lead_panobinostat_CED_MTX110/` — the #3-tied top lead
  (aggregate score 13 / 15, rescue-class **delivery**):
  - `04_panobinostat_CED_MTX110.verdict.json` — final pipeline verdict
  - `*.advocate.json`, `*.skeptic.json`, `*.interpreter.json` — per-role
    structured output (4-role engine; `advocate` is the DIPG-specific
    Proposer variant)
  - `*.usage.json` — per-role token + cost accounting
  - `prereg.yaml` — candidate pre-registration YAML from
    `../dipg_rescue/prereg/04_panobinostat_CED_MTX110.yaml`

## What is NOT included here (why)

The full `dipg_rescue/` tree (data, scripts, all 15 candidates' per-
role outputs) is **not** mirrored — it is 10+ MB and lives as a
separate git repo intended for post-hackathon AI-for-Science work.
This directory carries only what a reviewer needs to verify:
(1) the pre-registration SHA was committed before the engine ran,
and (2) the top-lead verdict structure.

## Honest scoping

- **Same engine, different disease.** The DIPG rescue engine
  re-implements the 4-role pattern from `theory_copilot_discovery`
  (see `../dipg_rescue/prompts_kirc_reference/` for the KIRC prompts
  used as templates). It is not a literal re-run of
  `theory_copilot_discovery/src/` — the DIPG variant adds clinical-
  rescue-specific grading axes (mechanism, stratification, clinical
  feasibility, Perrin-criteria translation).
- **Research-grade hypotheses, not clinical advice.** All 15 candidates
  including the #1 top lead are research-use-only. The "pharmacokinetic-
  not-pharmacodynamic rescue of PBTC-047" framing is a published
  *hypothesis* about why the original trial failed, not a claim about
  what will work in Phase II.
- **Deployment pathway is background, not a submission claim.** Dr.
  Mark Souweidane's convection-enhanced delivery work (MTX110 clinical
  translation, pioneering pediatric brainstem-tumor CED) is the
  clinical-context backdrop; no endorsement or collaboration commitment
  is claimed here.
- **Not a replacement for the Theory Copilot flagship narrative.** The
  ccRCC TOP2A − EPAS1 result + IMmotion150 replay + SLC22A8 own-output
  kill remain the primary falsification-loop evidence. DIPG is a
  **generalization tag** showing the pattern transfers to a
  structurally distant disease context.

## Referenced from

- `docs/loom_narration_final_90s.md` §"1:30 – 2:00 — DIPG generalization"
- `docs/submission_form_draft.md` §"Broader Program Context"
