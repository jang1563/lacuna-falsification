# External validation / generalization — IPF rescue engine

**Purpose:** mirror of key artefacts from the sibling `dipg_rescue/`
project showing the same Lacuna 4-role agent pattern re-applied
to a third structurally distant disease: idiopathic pulmonary fibrosis
(IPF). The IPF variant uses the same rescue-claim role prompts as the
DIPG variant — **Advocate / Evidence Retriever / Skeptic / Interpreter**
— with disease-context biology updated for IPF (UIP histology, FVC
slope, AE-IPF, MMP-7 / CXCL13 / KL-6 / CTGF / LOXL2 / CCL18 / TNIK /
PDE4B mechanism map). This mirror exists so submission materials
(Loom narration, submission form, judge_faq) can reference the result
without leaving the public `lacuna-falsification` checkout.

## Source

- Sibling repo: `../dipg_rescue/` (separate git repo, results commit
  `3af3a67` 2026-04-25, post-registration-edit commit `2764002` for
  the Nambiar 2023 review).
- Pre-registration lock commit: `88eaca34` (full SHA
  `88eaca342b5f7fcf9dd9210a7a6e4721053826c4`) — "PREREG: IPF Run #1
  (5 candidates, Tier-2 LLM-adjudication only)" — locked before any
  engine run; `prereg_lock_utc: 2026-04-25T04:16:59Z`.
- **`registered_at_commit` convention:** every IPF pre-reg YAML
  is stamped with the lock SHA via a separate post-lock commit
  (`88c2802` "PREREG: stamp registered_at_commit SHA + actual
  prereg_utc for IPF Run #1") — consistent with the DIPG pattern of
  YAML SHA-stamping post-lock.
- Full run directory: `../dipg_rescue/runs/2026-04-25_ipf_run01/`
  (5 candidates × 4 roles × JSON + raw + usage). Not mirrored here.

## What is included here

- `RESULTS.md` — verdict distribution summary (5 candidates, **1
  RESCUE_SUPPORTED + 0 MIXED + 4 INSUFFICIENT_EVIDENCE**) + ranked-by-
  score table + per-candidate novel-insight rows.
- `RESULTS.csv` and `RESULTS.json` — same content, machine-readable.
- `run_manifest.json` — run metadata: model, total tokens, cost
  ($58.28 / $100 cap), wall-clock (32 min sequential local), per-
  candidate verdict + cost breakdown, **two engine-caught Advocate
  fabrications** (candidates 03 simtuzumab and 04 tralokinumab),
  cross-disease consistency table (KIRC + DIPG + IPF).
- `top_lead_DandQ_telomere_short/` — engine output for the single
  RESCUE_SUPPORTED candidate (D+Q senolytics in telomere-short IPF,
  aggregate score 12/15).
  - `05_DandQ_telomere_short_IPF.verdict.json` — final pipeline
    verdict (with `interpreter_verdict=MIXED vs gate=RESCUE_SUPPORTED`
    warning preserved as honest-framing evidence)
  - `*.advocate.json`, `*.evidence.json`, `*.skeptic.json`,
    `*.interpreter.json` — per-role structured output
  - `prereg.yaml` — pre-registration YAML (operator_id scrubbed for
    public mirror; original at sibling repo lock SHA `88eaca34`)
  - `one_pager.md` — single-page outreach-evidence framing of the
    SUPPORTED verdict, with the **seven Skeptic critical caveats**
    laid out explicitly (engine self-flagging on its own output)

## What this run demonstrates that DIPG and KIRC do not

The IPF run's distinctive contribution is **Skeptic adversarial
review catching Advocate fabrications at runtime**. Across 5
candidates × 4 roles = 20 separate Managed Agents sessions, the
Skeptic role caught two empirically false Advocate claims:

- **Candidate 03 (simtuzumab + LOXL2-high):** Advocate claimed
  "Raghu 2017 never tested LOXL2-stratified subgroup." Skeptic
  reply: *"Raghu 2017 already pre-specified LOXL2-stratified
  co-primary endpoints with the highest-tertile arm tested."*
  False premise → INSUFFICIENT (4/15).
- **Candidate 04 (tralokinumab + CCL18-high Th2):** Advocate
  claimed "no IPF IL-13 trial prespecified Th2 stratifier."
  Skeptic reply: *"RAINIER itself prespecified periostin
  (canonical IL-13-induced epithelial Th2 marker) subgroup."*
  False premise → INSUFFICIENT (7/15).

Single-session pipelines (Skill, ChatGPT-like, single-harness
tool-use) cannot catch this pattern because the Advocate's
confident-sounding rationale tokens prime the Skeptic's continuation.
The Managed Agents architecture — three separate sessions with
structured-JSON-only handoff and no shared context — is the
load-bearing primitive that catches it.

## What is NOT included here (why)

The full sibling `dipg_rescue/` tree (per-candidate per-role JSONs
for candidates 01-04, the IPF brief, prompts directory, trial
graveyard CSV, six IPF research markdown files for plan / outreach /
dbGaP reality-check) is **not** mirrored — it is intentionally
isolated to the post-hackathon AI-for-Science work track. This
directory carries only what a reviewer needs to verify:

1. The pre-registration SHA was committed before the engine ran.
2. The verdict distribution (1/0/4) is reproducible from the
   per-role JSONs in `top_lead_DandQ_telomere_short/`.
3. The two Advocate-fabrication catches are real (visible in the
   `confounds_flagged` and `kill_attempts` fields of the parallel
   candidates' Skeptic JSONs in the sibling repo).
4. The honest-framing trail — the SUPPORTED verdict's seven
   critical caveats are surfaced in `one_pager.md`, not buried.

## Honest scope

This run is **post-hackathon stretch** (executed 2026-04-25, after
the KIRC + DIPG core submission scope was locked) demonstrating engine
portability to a third structurally distant disease. The single
SUPPORTED rescue (D+Q telomere-short IPF) is **research-grade
hypothesis with engine-flagged caveats**, not a treatment
recommendation. Recommended pre-prospective-trial step (per the
engine's own Interpreter): ex-vivo IPF lung explant validation, not a
Phase 2 trial.
