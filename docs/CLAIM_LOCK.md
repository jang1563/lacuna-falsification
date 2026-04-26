# CLAIM LOCK — authoritative phrasing for the submission

**Last locked:** 2026-04-26 (platform generalization numbers + 107/107 test count + PAAD/LIHC-MVI/disease-count-7 added).
**Scope:** every judge-facing surface (README, submission form, Loom
narration, demo script, paper, STATUS). Any rewrite in the final 48 hours
must cross-check this file first.

This file exists so that the video narration, submission form text, and
README do not drift from the committed evidence when written in parallel.

---

## 140-character pitch (canonical)

> Opus 4.7 proposes compact cancer laws; a Python gate rejects 194 / 203
> candidate evaluations, validates TOP2A − EPAS1 on IMmotion150, then kills
> its own SLC22A8 extension.

## One-paragraph summary (canonical)

> Lacuna Discovery is a verification-first biological law discovery
> workflow built around Opus 4.7. Opus proposes compact law families and
> ex-ante skeptic tests; PySR instantiates equations; a deterministic
> Python 5-test classification gate rejects weak candidates before any LLM
> judgement. On public TCGA-KIRC data the gate rejects 194 of 203 candidate
> evaluations and accepts 9 on the expanded metastasis panel. The simplest
> survivor, TOP2A − EPAS1, rediscovered the published ccA/ccB ccRCC subtype
> axis. The same score then passed a separately pre-registered three-test
> survival replay gate on the independent IMmotion150 Phase-2 cohort, while
> the system's own SLC22A8 3-gene extension failed that survival replay.
> The artifact publishes the survivor, the rejection log, the
> pre-registrations, and Managed Agents / Routines traces showing the
> verification loop running as code.

---

## Locked numbers (do NOT vary)

| Claim | Number | Source |
|---|---|---|
| TCGA classification gate: candidate evaluations | **203** | `results/track_a_task_landscape/SUMMARY.md` |
| TCGA classification gate: rejections | **194** | same |
| TCGA classification gate: survivors | **9** | `results/track_a_task_landscape/metastasis_expanded/falsification_report.json` |
| Flagship survivor | `TOP2A − EPAS1` | `results/track_a_task_landscape/metastasis_expanded/falsification_report.json` |
| Flagship full-train AUROC | **0.726** | same (on 505-sample TCGA-KIRC M0 vs M1) |
| 5-fold stratified CV AUROC | **0.722 ± 0.078** | `results/track_a_task_landscape/survivor_robustness/SUMMARY.md` |
| IMmotion150 replay cohort n | **263** | `results/.../immotion150_pfs/` |
| IMmotion150 log-rank p | **0.0003** | same |
| IMmotion150 Cox HR | **1.36** | same |
| IMmotion150 Harrell C-index | **0.601** | same |
| SLC22A8 extension kill C-index | **0.566** | `results/.../immotion150_slc22a8/SUMMARY.md` |
| Cross-model ablation calls | **180** (60/model × 3 models) | `results/ablation/SUMMARY.md` |
| Opus 4.7 PASS / 60 | **10 / 60** | same |
| Haiku 4.5 PASS / 60 | **14 / 60** | same |
| Sonnet 4.6 PASS / 60 | **0 / 60** | same |
| Memory chain lessons (PhL-12) | **8** | `results/live_evidence/phl12_memory_chain_deepen/SUMMARY.md` |
| Local tests | **107 / 107** | `make test`, current local-runnable target; review/staging suites intentionally excluded |
| PhL artefact count | **24** (PhL-1 to PhL-19 + PhL-9v2 + PhL-8b/8c/8d + PhL-10 oracle) | `STATUS.md` |
| Memorization audit (PhL-13): zero-shot TOP2A-EPAS1 exact top | **0 / 10** | `results/live_evidence/phl13_memorization_audit/SUMMARY.md` |
| Memorization audit: literature-anchor rediscovery | **2 / 2** structurally-equivalent | same |
| PhL-14 LLM-SR 10-iter: post-seed skeleton families tested | **18** (9 Opus + 9 Sonnet) | `results/overhang/llm_sr_10iter/SUMMARY.md` |
| PhL-14 LLM-SR 10-iter: survivors beyond seed | **0** | same |

## Locked platform generalization numbers (added 2026-04-26)

| Claim | Number | Source |
|---|---|---|
| Platform expansion evaluations | **101** | KIRC Stage 28 + COAD 22 + LGG 25 + LIHC 26 |
| New disease track evaluations (2026-04-26) | **81** | LIHC-MVI 29 + IPF-LGRC 25 + PAAD 27 |
| Total evaluations (all tasks + all panels + new tracks) | **385** | 203 + 101 + 81 |
| Disease contexts covered (all public evidence layers) | **7** | Expression gate: ccRCC, COAD, LGG (GBM IDH cohort), LIHC (2 tasks: T-vs-N designed-negative + MVI 6/29), PAAD. Role-separated review engine: DIPG, IPF |
| Cross-disease survivors (platform expansion only, excl. original KIRC 9) | **40** | KIRC Stage 23 + COAD 15 + LGG 2 + LIHC 0 |
| New disease track survivors | **20** | LIHC-MVI 6 + IPF-LGRC 6 + PAAD 8 |
| Cross-disease survivors total (excl. original KIRC 9) | **60** | 40 platform expansion + 20 new disease tracks |
| KIRC Stage I-II vs III-IV (45-gene): survivors | **23 / 28** | `results/track_a_task_landscape/stage_expanded/SUMMARY.md` |
| KIRC Stage top AUROC | **0.689** | same (CXCR4/EPAS1) |
| COAD Stage I-II vs III-IV (31-gene, n=484): survivors | **15 / 22** | `results/track_a_task_landscape/coad_msi/SUMMARY.md` |
| COAD best AUROC | **0.658** | same |
| COAD Δ-baseline | **+0.107** | same (highest Δbaseline of any run) |
| LGG Grade II vs III (30-gene, n=384): survivors | **2 / 25** | `results/track_a_task_landscape/gbm_idh/SUMMARY.md` |
| LGG top survivor AUROC | **0.840** | same (TWIST1×MKI67+VIM − CDH2/NES) |
| LIHC Tumor vs Normal (31-gene, n=424): survivors | **0 / 26** | `results/track_a_task_landscape/lihc/SUMMARY.md` |
| LIHC designed-negative reason | **ALB saturation ~0.985** | same |
| LIHC MVI Micro vs None (19-gene, n=144): survivors | **6 / 29** | `results/track_a_task_landscape/lihc_mvi/SUMMARY.md` |
| LIHC MVI top AUROC | **0.702** | same (`(TOP2A/CDH2/SOX9)/sqrt(SNAI1)` cluster) |
| PAAD OS ≤15 vs >15 mo (19-gene, n=183): survivors | **8 / 27** | `results/track_a_task_landscape/paad_survival/SUMMARY.md` |
| PAAD best AUROC | **0.707** | same |

| IPF Composite Endpoint / GSE93606 (17-gene, n=57): survivors | **6 / 25** | `results/track_a_task_landscape/ipf_lgrc/SUMMARY.md` |
| IPF-LGRC top AUROC | **0.757** | same (`(CXCL12−PDGFRA)×SPP1/MUC5B`) |
| DIPG top-lead (panobinostat-CED-MTX110) aggregate score | **13 / 15** | `results/external_validation_dipg/top_lead_panobinostat_CED_MTX110/04_panobinostat_CED_MTX110.verdict.json` |

**Arithmetic cross-check:** 28 + 22 + 25 + 26 = 101 ✓ | 29 + 25 + 27 = 81 ✓ | 203 + 101 + 81 = 385 ✓ | 23 + 15 + 2 + 0 = 40 ✓ | 6 + 6 + 8 = 20 ✓ | 40 + 20 = 60 ✓

**HR rounding note:** `1.36` is the canonical rounded value locked above. Precise values: **1.361** (unadjusted Cox HR) and **1.365** (treatment-arm-adjusted Cox HR — signal increases after controlling for immunotherapy vs VEGF-inhibitor arm, confirming therapy-independence). Both round to 1.36; all three forms may appear in docs without contradiction.

**6-verdict replication chain (locked 2026-04-26):** 3 PASS · 2 pre-registered FAIL · 1 honest FAIL.

| Verdict | Cohort | Key metric | Label |
|---|---|---|---|
| PASS | TCGA-KIRC metastasis | AUROC 0.726 | flagship |
| PASS | IMmotion150 PFS | HR 1.36 p=0.0003 | survival replay |
| PASS | GSE53757 stage | AUROC 0.714 | microarray platform |
| informative FAIL | GSE53757 T-vs-N | CA9 saturates 0.995 | designed negative |
| pre-reg FAIL | TCGA-BRCA | Δbase +0.009 | cross-cancer control |
| honest FAIL | CPTAC-3 metastasis | ci_lower=0.542; Δbase=−0.007; direction p=0.006 | cross-platform (n=155, M1=20) |

CPTAC-3 canonical numbers: **n=155** (M1=20), **AUROC 0.683**, **ci_lower=0.542**, **Δbase=−0.007**, **perm_p=0.006**. Gate refuses; direction preserved.

---

## Locked gate semantics

- **TCGA classification gate** and **IMmotion150 survival replay gate** are
  two *different* pre-registered gates. Both appear in the story — never
  say "same gate both cohorts".
- Classification gate active legs depend on task. For `metastasis_expanded`
  the `delta_confound` leg is **null** because no non-degenerate covariate
  survives cohort filtering. Survivors clear the 4 active legs + BH-FDR.
  Say "the active legs of the 5-leg gate clear on this task", not "full
  5-test pass".
- `delta_baseline` is the key gate threshold that kills textbook laws
  (CA9 + VEGFA − AGXT on tumor-vs-normal fails because CA9 alone saturates
  at AUROC 0.965).

## Locked IMmotion150 phrasing

- `IMmotion150` is an **independent Phase-2 immunotherapy cohort** (Atezo ±
  Beva vs Sunitinib, McDermott et al., *Nat Med* 2018, PMID 29867230).
- The replay tests **PFS (progression-free survival)**, not metastasis
  M0 vs M1 classification.
- The replay uses a **separately pre-registered three-test survival gate**
  (log-rank on median split, Cox HR per z-score, Harrell C-index) — *not*
  the TCGA classification gate.
- PhL-1 runs the **same survival replay gate** on the 3-gene SLC22A8
  extension and fails it — that is the "own-output kill".

## Locked GSE40435 / GSE53757 phrasing

- Neither is the headline validation. Both are supporting sanity cohorts.
- `GSE40435` (101 paired ccRCC, microarray) — 8-gene subset, lacks
  TOP2A/EPAS1 and M-status; used only for HIF-axis pattern replication.
- `GSE53757` (72 ccRCC + 72 normal, PhL-6) — stage 1-2 vs 3-4 AUROC 0.714
  (PASS); tumor-vs-normal platform-saturates (FAIL).

## Locked Opus 4.7 phrasing

Use:
- long-horizon agentic work
- instruction-following
- verification before reporting
- adaptive thinking, effort xhigh
- `thinking={"type":"adaptive","display":"summarized"}`
- `output_config={"effort":"high"}`
- Memory + event persist/replay

Avoid:
- "extended thinking budget"
- `budget_tokens`
- non-default sampling params (temperature/top_p/top_k)
- "Managed Agents changed API for 4.7"
- "smaller models collapse" as a factual claim
  (the 180-call ablation falsified the strong form; the honest finding is
  that Sonnet 4.6 collapses into *permanent dissent* 0/60 PASS, not
  rubber-stamp agreement)

## Locked Managed Agents phrasing

- **Path B** — public-beta single Managed Agent + `agent_toolset_20260401`.
  Live. `results/live_evidence/04_managed_agents_e2e.log`.
- **Path A** — public-beta **sequential 3-session chain** with structured-
  JSON handoff. `delegation_mode=sequential_fallback`. PhL-9 + PhL-9v2
  (real TCGA-KIRC via `files.upload()` mount). The
  `_run_path_a_callable_agents` branch is **reference code only** — do NOT
  say "one flag-flip away" or imply the multi-agent research preview is
  active.
- **Path C** — Claude Code Routines `/fire` **LIVE**. HTTP 200 + clickable
  `claude_code_session_url`. PhL-8.
- **Memory** — `memory_store` resources on sessions, 8-lesson chain across
  PhL-3 + PhL-7 + PhL-10 + PhL-12.
- **Events** — `sessions.events.list` / persist + `replay_session_from_log`
  (PhL-4). Durable log is conclusion + output substrate with attested
  timing; thinking tokens themselves NOT preserved (PhK probe).
- **MCP biology validator** — `validate_law` + `fetch_cohort_summary`, PhL-2.

## Forbidden phrases (triggers a stop-and-rephrase)

Triggered by `rg` in P0.1:

| Forbidden | Why | Replacement |
|---|---|---|
| `194 of 204` / `194/204` / `204 candidates` | 204 is outdated count that mixed IMmotion replay rows in | `194 of 203 candidate evaluations` |
| `10 survivor` / `10 survivors` | survivors = 9 on metastasis_expanded | `9 survivors` |
| `full five-test pass` (without caveat) | confound leg null for current flagship | `active legs of the 5-leg gate clear` or `4 active legs + BH-FDR` |
| `same gate on IMmotion150` (alone) | classification vs survival gates are different | `separately pre-registered IMmotion150 survival replay` |
| `repo private` | public since 2026-04-23 19:32 ET | `repo public since 2026-04-23` |
| `5-session` (Path A) | PhL-9 = 3 sessions, not 5 | `sequential 3-session chain` |
| `one flag-flip away` (Path A) | PhL-9 is LIVE | `live sequential Path A` |
| `smaller models collapse to rubber-stamp` | strong form falsified by ablation | `Sonnet 4.6 dissents on 100% of gate-PASS candidates (0/60 PASS) while Opus 4.7 draws the gate's line (10/60 PASS)` |
| `47/47` / `90/90` / `101/101` / `105/105` / `118/118` / `120/120` tests | current `make test` target collects 107 local-runnable tests | `107/107 local tests` |
| `ci_width` as gate metric | replaced by `ci_lower > 0.6` | `ci_lower` |
| `open-source data` | publicly available but not always open-source licensed | `public/no-login data` or `publicly accessible data` |
| `diagnostic tool` | research-use only | `research-use-only compact law` |
| `treatment recommendation` | never | — |
| `universal biological law` | overclaim | `ccRCC-specific empirical regularity` |
| `new kidney cancer biology` | rediscovery, not new | `rediscovered published ccA/ccB subtype axis` |

## Judge reading path (3 minutes)

1. `README.md` opening paragraph + sub-hook.
2. `docs/ARTIFACT_INDEX.md` — 60-second tour section.
3. `docs/managed_agents_evidence_card.md` — Best Managed Agents evidence.
4. `results/live_evidence/phl8_routine_fire/SUMMARY.md` — click the live
   session URL.
5. `results/track_a_task_landscape/external_replay/immotion150_pfs/SUMMARY.md`
   — IMmotion150 validation.
6. `results/track_a_task_landscape/external_replay/immotion150_slc22a8/SUMMARY.md`
   — SLC22A8 own-output kill.

## Cross-check command

Before every submission-bound commit, run from repo root. Two passes:

**Pass 1 — forbidden phrases:**
```bash
rg -n "194 of 204|194/204|204 candidates|10 survivor|full five-test pass|same gate on IMmotion|same gate.*survival|repo private|5-session|one flag-flip|smaller models collapse to rubber|47/47|90/90|90 / 90|101/101|101 / 101|118/118|118 / 118|120/120|120 / 120|ci_width|open.source data|diagnostic tool|universal biological law" \
  README.md docs STATUS.md CLAUDE.md results -g '*.md' \
  -g '!docs/CLAIM_LOCK.md' \
  -g '!docs/loom_narration_final_90s.md' \
  -g '!docs/loom_narration_final_v3.md' \
  -g '!results/qa/SUMMARY_qa.md' \
  | rg -v "(historical|was the pre-registered|previously|previous why_opus|not rubber|pre-registered strong form|rubber-stamp agreement. This ablation|This is NOT the same gate|Not \"194|Not \"10|❌|perm_p_fdr, ci_lower, ci_width, delta)"
```
*Excludes: `CLAIM_LOCK.md` (documents the forbidden list), and loom
narration files (`loom_narration_final_90s.md`, `loom_narration_final_v3.md`)
whose honest-framing sections cite the forbidden phrases as rules not-to-say. The `same gate`
regex is scoped to IMmotion / survival context — "same gate" applied
to TCGA panels/tasks/models is legitimate (cross-model ablation, the
11→45-gene expansion, etc.) and does NOT trigger.*

**Pass 2 — stale numbers (catches lock-table drift):**
```bash
# Memory chain must say 8 entries (not 3 or 5 — those are intermediate snapshots)
rg -n "chain to (3|5) entries|(3|5) lesson entries|memory.chain.*(3|5)[^0-9]" \
  README.md docs STATUS.md -g '*.md' \
  | rg -v "(grew|extended|deepened|→)"
# PhL-9 wall-time must be 706 s (PhL-9v2 is 300 s; do not swap)
rg -n "PhL-9[^v0-9].*[0-9]+\s*s\b|sequential_fallback.*[0-9]+\s*s" \
  README.md docs STATUS.md -g '*.md' \
  | rg -v "706|300"
# IMmotion150 n must be 263 (not 150 or 245); HR must be 1.36; C-index 0.601
rg -n "IMmotion.*n\s*=\s*(?!263)" README.md docs -g '*.md'
rg -n "IMmotion.*HR\s*=?\s*(?!1\.36)" README.md docs -g '*.md'
# Flagship AUROC must be 0.726 (full-train) or 0.722 ± 0.078 (5-fold CV)
rg -n "TOP2A.*EPAS1.*AUROC\s*0\.(?!726|722)" README.md docs -g '*.md'
# G2 calibration slope must be the corrected OOF Platt diagnostic.
rg -n "calibration slope 0\.54|calibration_slope = 0\.540" README.md docs STATUS.md -g '*.md'
```

Both passes MUST return zero results before `git push` on any
submission-bound commit. If either fires, fix the drift rather than
suppress it.
