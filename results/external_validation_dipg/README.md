# External validation / generalization — DIPG rescue engine

**Purpose:** mirror of key artefacts from the sibling `dipg_rescue/`
project showing the same Theory Copilot 4-role agent pattern re-applied
to a structurally distant second disease: H3 K27M-mutant diffuse
intrinsic pontine glioma (DIPG / diffuse midline glioma). The DIPG
variant uses rescue-claim-specific role prompts — **Advocate /
Evidence Retriever / Skeptic / Interpreter** — the clinical-rescue
analogue of the KIRC flagship's Proposer / Searcher / Skeptic /
Interpreter pipeline. This mirror exists so submission materials
(Loom narration, submission form) can reference the result without
leaving the `theory_copilot_discovery` tree.

## Source

- Sibling repo: `../dipg_rescue/` (separate git repo, commit
  `0a9e154` as of 2026-04-24).
- Pre-registration lock commit: `8a4ecc5` — "PREREG LOCK: 15 DIPG
  rescue candidates, 4-role engine, 5-axis falsification gate"
  (locked before any engine run).
- **`registered_at_commit` convention:** every pre-reg YAML contains
  the placeholder string `PENDING_COMMIT_SHA` in this field; the
  authoritative registration SHA is `8a4ecc5` as recorded in the
  sibling repo's `git log`. A YAML cannot self-reference its own
  future commit hash, so the placeholder is the honest form of
  "this YAML was committed at the SHA you see in git log" — no
  post-commit field edit has occurred.
- Full run directory: `../dipg_rescue/runs/2026-04-24_run01/`
  (1.3 MB, 15 candidates × 4 roles × JSON + raw + usage).

## What is included here

- `RESULTS.md` — verdict distribution summary (15 candidates, 7
  supported, 7 mixed, 1 insufficient, 0 missing) + ranked-by-score
  table.
- `top_lead_panobinostat_CED_MTX110/` — the integrator-selected top
  lead among five candidates tied at aggregate score 13 / 15 (tie-break
  prefers `rescue_class = delivery`, which is the cleanest
  dordaviprone-pattern match in the 15-candidate set; the other four
  at 13/15 were: avapritinib-PDGFRA, GD2-CAR-T-H3K27M,
  ONC201+everolimus+paxalisib, pembrolizumab-CMMRD). Rescue-class
  **delivery**.
  - `04_panobinostat_CED_MTX110.verdict.json` — final pipeline verdict
  - `*.advocate.json`, `*.skeptic.json`, `*.interpreter.json` — per-role
    structured output (4-role engine: Advocate / Evidence Retriever /
    Skeptic / Interpreter — DIPG-rescue prompts, NOT the KIRC flagship
    Proposer/Searcher/Skeptic/Interpreter prompts)
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

- **Same role-separation pattern, different gate type.** The DIPG
  rescue engine reuses the role-isolated 4-agent pattern from
  `theory_copilot_discovery` (see `../dipg_rescue/prompts_kirc_reference/`
  for the KIRC prompts used as templates) and the same pre-reg
  discipline (YAMLs frozen at SHA `8a4ecc5` before any engine run).
  But the gates are functionally different by design: KIRC's gate is a
  deterministic 5-test Python gate on statistical fits (permutation,
  bootstrap, baseline, confound, decoy), and the LLM cannot renegotiate
  the criterion mid-session. The DIPG gate cannot be statistical
  because rescue claims have no fittable features, so it is LLM-scored
  on five Skeptic axes (`perrin_replication_score`,
  `mechanism_concordance`, `stratifier_specificity`,
  `clinical_plausibility`, `kill_or_confirm_feasibility`) with the
  thresholds and AMX0035 hedging-language check still committed in
  plain Python. The Skeptic-Interpreter separation enforces the same
  role-isolation that makes KIRC gate-renegotiation impossible.
- **Tier-1 statistical substrate is deferred.** Four candidates
  (`02_avapritinib_PDGFRA`, `06_ACVR1i_H31_comut`,
  `12_pembrolizumab_CMMRD`, `13_H3K27M_peptide_dual_ICB`) were
  pre-registered as Tier-1 = OpenPedCan-v15-testable, intending a
  retrospective subgroup-stratifier check on the public PBTA cohort
  (~85-130 H3 K27M biospecimens). This 2026-04-24 run executed in
  literature-only adjudication mode (`--skip-evidence-tools`) and the
  Tier-1 statistical substrate was not actually queried. The next
  run-tier deploys the OpenPedCan integration in
  `../dipg_rescue/src/dmg_rescue/dipg_card.py` for the four Tier-1
  candidates.
- **Citation-error transparency.** Across all 15 candidates the
  Skeptic logged citation-quality `perrin_flags` (wrong-PMID
  attribution, unverified DOIs, originating-group-only replication).
  These flags do not prevent a `RESCUE_SUPPORTED` verdict because the
  gate's `perrin_replication_score` axis indexes lab-independence
  rather than per-citation correctness; a future gate revision should
  add a separate bibliographic-accuracy axis. The flagged citations
  are recoverable in each candidate's `*.skeptic.json`
  `perrin_flags` array.
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
