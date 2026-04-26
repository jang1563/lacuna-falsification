# Artifact Index — judge navigation (60-second tour)

This is the canonical 1-page navigation for evaluators. Every claim in
the README / submission docs is backed by exactly one of the
artefacts listed below. If a claim is not in this index, it is not in
the submission.

## 60-second tour (read in order)

1. **README.md (sub-hook + opening paragraph)** — what we built, the
   one-liner, the verification framing.
2. **`docs/headline_findings.md`** — three findings (TOP2A−EPAS1
   discovery + replication; rejection log as product including the
   PhL-1 own-output kill; pre-registration at LLM speed + Path C
   Routine).
3. **`results/live_evidence/phl8_routine_fire/SUMMARY.md`** — Path C
   `/fire` LIVE proof (clickable `claude_code_session_url` to a
   real Claude Code cloud session).
4. **`results/live_evidence/phl7_compound_orchestrator/SUMMARY.md`** —
   the flagship Best-Managed-Agents demo: MCP + Memory + 5-test gate
   composed in a single Managed Agents session with cross-substrate
   reasoning.

## Phase L artefacts (this hackathon's own contributions)

| ID | What | Files | Verdict |
|---|---|---|---|
| **PhL-1** | SLC22A8 3-gene cross-cohort kill (gate killed our own H1 output on IMmotion150) | `preregistrations/20260423T181322Z_phl1_*.yaml`, `src/phl1_slc22a8_cross_cohort.py`, `results/track_a_task_landscape/external_replay/immotion150_slc22a8/SUMMARY.md` | **FAIL** (UNDERPERFORMS 2-gene) |
| **PhL-2** | MCP biology validator live demo (PubMed co-mention + GDC cohort) | `src/mcp_biology_validator.py`, `.mcp.json`, `results/live_evidence/09_mcp_biology_validator_live.log` | OK (0 co-mentions for TOP2A∧EPAS1∧ccRCC — independent rediscovery signal) |
| **PhL-3** | Managed Agents Memory public-beta (announced same day) — 2 sessions, lesson chain accumulates | `src/phl3_memory_smoke.py`, `results/live_evidence/phl3_memory_smoke/SUMMARY.md` | PASS — Rakuten "distill lessons" pattern verified |
| **PhL-4** | `sessions.events.list` persist + replay — brain/body decouple | `src/phl4_persist_replay_smoke.py`, `results/live_evidence/phl4_persist_replay/SUMMARY.md` | PASS — replayed user.message quoted verbatim by fresh session |
| **PhL-5** | TCGA-BRCA cross-cancer negative control (TOP2A−EPAS1 ccRCC-specificity check) | `preregistrations/20260423T224229Z_phl5_*.yaml`, `src/phl5_phl6_generalization_probes.py`, `results/track_a_task_landscape/external_replay/brca_cross_cancer/SUMMARY.md` | **FAIL as predicted** (Δbase +0.009, ccRCC-specific reinforced) |
| **PhL-6** | GSE53757 third independent cohort (microarray platform shift) | `preregistrations/20260423T224229Z_phl6_*.yaml`, same probe script, `results/track_a_task_landscape/external_replay/gse53757/SUMMARY.md` | T-vs-N: FAIL (platform saturation); stage 1-2 vs 3-4: **PASS** AUROC 0.714 |
| **PhL-7** | Compound orchestrator: MCP + Memory + 5-test gate in ONE session, cross-substrate reasoning | `src/phl7_compound_orchestrator.py`, `results/live_evidence/phl7_compound_orchestrator/SUMMARY.md` | PASS with explicit substrate citations + memory chain → 3 entries |
| **PhL-8** | Claude Code Routines `/fire` LIVE — Path C proof-of-life with clickable session URL | `src/phl8_routine_fire_live.py`, `routines_client.py`, `results/live_evidence/phl8_routine_fire/SUMMARY.md` | 200 OK + live `claude.ai/code/session_*` URL |
| **PhL-9** | Path A live: sequential 3-session chain under 2026-04-23 hackathon-fairness rule | `src/phl9_path_a_live_chain.py`, `results/live_evidence/phl9_path_a_chain/SUMMARY.md` + `role_{proposer,searcher,falsifier}.txt` | OK — `delegation_mode=sequential_fallback`, 706 s wall, 3 distinct session IDs |
| **PhL-10** | Extended Skeptic Memory chain (sessions 4+5) — 3 lessons → 5, cross-cancer rule transfer | `src/phl10_memory_chain_extended.py`, `results/live_evidence/phl10_memory_chain_extended/SUMMARY.md` | PASS — MKI67−EPAS1 KIRC PASS (structural twin); SFTPC−MKI67 LUAD FAIL (ceiling rule generalises across cancers) |
| **PhL-9v2** | Path A sequential 3-session chain on **real TCGA-KIRC** (via `files.upload()` + `resources=[{"type":"file",...}]` mount) | `src/phl9v2_path_a_real_data.py`, `results/live_evidence/phl9v2_path_a_real_data/SUMMARY.md` | OK — Proposer emits ccRCC proliferation-vs-HIF family, Skeptic quotes `delta_baseline=+0.0587` on LF-PROLIF-minus-HIF2A, 4 FAIL incl. negative control. 300 s wall. |
| **PhL-11** | Adversarial self-critique 3-turn role-separated harness across Opus 4.7 + Sonnet 4.6 (6 sessions total) | `src/phl11_adversarial_critique.py`, `results/live_evidence/phl11_adversarial_critique/SUMMARY.md` | Mixed — Opus followed "one CRISPR KO per attack" literally (5 vs Sonnet's 1); both models 100% concede under pushback. Honest Petri-2.0-consistent finding. |
| **PhL-12** | Memory chain deepened 5 → 8 lessons (template saturation + cross-cancer PRAD + pre-reg strictness edge) | `src/phl12_memory_chain_deepen.py`, `results/live_evidence/phl12_memory_chain_deepen/SUMMARY.md` | PASS — agent quoted & applied prior lessons 4 (template saturation) and 5 (cross-cancer rule incl. PRAD/KLK3), refused to invent "marginal" verdict at decoy_p=0.048 |
| **PhL-13** | Memorization audit — 10-repeat zero-shot + literature-anchor probe on Opus 4.7 | `src/phl13_memorization_audit.py`, `results/live_evidence/phl13_memorization_audit/SUMMARY.md` | **DISCOVERY SIGNAL** — TOP2A-EPAS1 exact top pick 0/10; proliferation-HIF form anywhere 0/10; but literature probe 2/2 "structurally_equivalent_to_known". Refutes LLM-SRBench memorization concern for the flagship. |
| **PhL-14** | LLM-SR 10-iteration convergence — Opus 4.7 vs Sonnet 4.6 with DrSR-style outcome tracking, held-out 70/30 split, per-iter train/held-out AUROC, pathway-diversity staircase | `src/phl14_llm_sr_10iter.py`, `results/overhang/llm_sr_10iter/SUMMARY.md` + `convergence_plot.png` | **HONEST NULL** — 18 post-seed skeleton families across 2 models × 10 iter, 0 clear the gate. Gate is the binding constraint. Peak non-seed AUCs: Opus 0.608 (`TOP2A*CA9/EPAS1` novel cross), Sonnet 0.646 (`TOP2A − AGXT`). Opus 0/9 library fallbacks vs Sonnet 4/9 (structured-output reliability gap). |
| **PhL-15** | Adaptive-thinking causal ablation on Opus 4.7 Skeptic — 120 calls × 2 thinking modes × 6 candidates × 10 repeats | `src/phl15_adaptive_thinking_ablation.py`, `results/live_evidence/phl15_adaptive_thinking/SUMMARY.md` + `mode_comparison.png` | **HONEST NULL** — adaptive ON/OFF identical verdict distribution (both 0/60 PASS, 100% dissent). why_opus_4_7.md §0 "adaptive thinking is the mechanism" causal claim honestly weakened. |
| **PhL-16** | Cross-model Proposer quality — each of 3 models proposes 30 ccRCC metastasis laws; all pass through the same pre-registered gate | `src/phl16_proposer_quality.py`, `results/live_evidence/phl16_proposer_quality/SUMMARY.md` + `proposer_comparison.png` | **0 / 48 gated proposals PASS** (Opus 0/30, Sonnet 0/18, Haiku N/A). Combined with PhL-14 → **~66 consecutive LLM-proposed laws rejected** across 5+ model/iteration combos. Format compliance: Opus 30/30, Sonnet 18/30, Haiku 0/30. Max AUC Opus 0.615, Sonnet 0.678 (both in gate's rejection zone, single-gene ceiling 0.657). Gate is model-independent binding. |
| **PhL-17** | 7-turn adversarial stance-decay curve — Opus 4.7 / Sonnet 4.6 / Haiku 4.5 × 10 repeats × 7 escalating challenges on TOP2A-EPAS1 | `src/phl17_stance_decay_7turn.py`, `results/live_evidence/phl17_stance_decay/SUMMARY.md` + `decay_curve.png` | **Gate-authority substrate finding**: Opus 78.6% + Sonnet 75.7% cite "pre-registered" across 70 turns each. Opus calibrated (2/10 concede on valid Rashomon), Sonnet stubborn (10/10 hold), Haiku errored 10/10. |
| **PhL-18** | Pre-registration YAML writing rubric — 5 hypotheses × 3 models, structural metrics + blind Opus rubric | `src/phl18_prereg_writing_quality.py`, `results/live_evidence/phl18_prereg_writing/SUMMARY.md` + `quality_heatmap.png` | Opus 5/5 valid YAML (100% schema), Sonnet 5/5 (2× verbose, same kill-test count), Haiku 0/5 (adaptive+YAML ceiling). Rubric blocked on Haiku non-output. |
| **PhL-19** | Interpreter mechanism hypothesis structured-JSON quality — 3 survivors × 3 models | `src/phl19_interpreter_depth.py`, `results/live_evidence/phl19_interpreter_depth/SUMMARY.md` + `quality_heatmap.png` | **Opus 3/3 valid JSON, Sonnet 0/3 (1 truncated + 2 empty), Haiku 0/3 (empty).** Direct instruction-following + token-budget-management gap under adaptive thinking at default `max_tokens`. Only model to complete task as spec'd. |

## Earlier-phase scientific artefacts

| Phase | What | Anchor |
|---|---|---|
| Flagship | TCGA-KIRC metastasis_expanded survivor `TOP2A−EPAS1` AUROC 0.726 | `results/track_a_task_landscape/metastasis_expanded/falsification_report.json` (9 / 30 pass) |
| Track-A reject | 11-gene panel: 0 / 100+ on tumor-vs-normal / stage / 5-yr survival / metastasis | `results/track_a_task_landscape/SUMMARY.md` |
| Track-B robustness | 6-axis stress test of the metastasis reject verdict | `results/track_b_gate_robustness/SUMMARY.md` |
| Survivor robustness | 6-axis stress test of the TOP2A−EPAS1 accept verdict | `results/track_a_task_landscape/survivor_robustness/SUMMARY.md` |
| **PhF-3** | IMmotion150 Phase-2 trial external replay — 2-gene form passes 3 survival kill tests | `preregistrations/20260423T044446Z_phf3_*.yaml`, `src/phf3_immotion150_replay.py`, `results/track_a_task_landscape/external_replay/immotion150_pfs/` |
| **DIPG generalization** | Same 4-role engine re-run on 15 pre-registered K27M diffuse-midline-glioma rescue hypotheses (prereg SHA `8a4ecc5` locked before engine output): 7 supported, 7 mixed, 1 insufficient. Top lead: CED-delivered MTX110 panobinostat, score 13/15 (delivery-class rescue of PBTC-047). Lives as separate git repo; mirrored artefacts in `results/external_validation_dipg/` | `results/external_validation_dipg/README.md` + `RESULTS.md` + `top_lead_panobinostat_CED_MTX110/` |
| **IPF generalization** | Same 4-role engine re-run on 5 pre-registered idiopathic pulmonary fibrosis rescue hypotheses (prereg lock SHA `88eaca34` in sibling `dipg_rescue/`, locked before engine output, 2026-04-25): 1 supported (D+Q telomere-short, with engine-flagged Nambiar 2023 omission caveat), 4 insufficient. **Engine caught two Advocate fabrications via Skeptic adversarial review — claims that prior trials "never tested" a stratifier were empirically false (RAINIER prespecified periostin; Raghu 2017 prespecified LOXL2-stratified co-primaries). Runtime demonstration of dual-role context isolation.** Mirrored at `results/external_validation_ipf/`. Post-hackathon stretch, $58 / 32 min sequential local. | `results/external_validation_ipf/README.md` + `RESULTS.md` + `top_lead_DandQ_telomere_short/` (incl. `one_pager.md`) |
| G3 | Adjusted Cox — TOP2A−EPAS1 HR robust to treatment + TMB | `src/g3_adjusted_cox.py`, `results/.../g3_adjusted_cox/` |
| G4 | Anchor regression cross-cohort stability (Rothenhäusler 2021) | `src/g4_anchor_regression.py`, `results/.../g4_anchor_regression/` |
| G6 | Opus 4.6 vs 4.7 calibration ablation (60 calls each) | `src/g6_calibration_4_6_vs_4_7.py`, `results/ablation/opus_46_vs_47/` |
| H1 | Falsification-Guided SR Loop on HPC (5 iter, Opus-steered, 5 survivors at iter 1) | `src/falsification_sr_loop.py`, `results/overhang/sr_loop_run.json` |
| H2 | Opus 4.7 adaptive-thinking synthesis over 74 rejections + 9 survivors (14k-char prompt; 1M context available but not exercised — honest scoping at `docs/headline_findings.md`) | `src/opus_1m_synthesis.py`, `results/overhang/synthesis_1m.json` |
| I2 | Rashomon set analysis — TOP2A−EPAS1 is rank 1 / 990 pairs | `src/rashomon_analysis.py`, `results/track_a_task_landscape/rashomon_set/SUMMARY.md` |
| I3 | Clinical utility translation (Cohen's d, NNS, OR) | `src/i3_clinical_utility.py`, `results/track_a_task_landscape/clinical_utility/SUMMARY.md` |
| I4 | Information-theoretic synergy (mutual info, MDL) | `src/i4_information_theory.py`, `results/track_a_task_landscape/information_theory/SUMMARY.md` |
| **Platform** | KIRC Stage I-II vs III-IV (45-gene, n=512): **23 / 28 survivors**, top AUROC 0.689 | `results/track_a_task_landscape/stage_expanded/SUMMARY.md` |
| **Platform** | TCGA-COAD Stage I-II vs III-IV (31-gene, n=484): **15 / 22 survivors**, Δ+0.107 (highest of any run) | `results/track_a_task_landscape/coad_msi/SUMMARY.md` |
| **Platform** | LGG Grade II vs III (30-gene, n=384): **2 / 25 survivors**, top AUROC **0.840** (TWIST1×MKI67 interaction) | `results/track_a_task_landscape/gbm_idh/SUMMARY.md` |
| **Platform** | TCGA-LIHC Tumor vs Normal (31-gene, n=424): **0 / 26 survivors** (designed negative — ALB saturates ~0.985) | `results/track_a_task_landscape/lihc/SUMMARY.md` |
| PhI-1 | Opus's own H2 proposals fail gate per Opus's own ex-ante skeptic tests | `results/overhang/phi1_h2_prospective/SUMMARY.md` |
| PhI-2 | Auditable thinking trace — 4.7 display="omitted" → "summarized" change | `src/phi2_thinking_artefact.py`, `results/overhang/phi2_auditable_thinking/VERIFY.md` |
| PhI-3 | LAB-Bench LitQA2 reproduction on 4.6 vs 4.7 (honest reversal: -10.5pp on closed-book recall — narrower task than the gate's output surface; intentionally excluded from main narrative with rationale in SUMMARY.md; included here for transparency) | `src/phi3_labbench_reproduce.py`, `results/overhang/phi3_labbench/SUMMARY.md` |
| PhK | `events.list` thinking-content preservation probe — content NOT preserved | `src/phk_events_list_thinking_probe.py`, `results/overhang/phk_events_list_probe/SUMMARY.md` |

## Architecture / engineering surfaces

| Surface | File | Purpose |
|---|---|---|
| **Path B (single agent + agent_toolset_20260401)** | `src/lacuna/managed_agent_runner.py::run_path_b` | Public-beta Managed Agents single-agent driver; live trace `results/live_evidence/04_managed_agents_e2e.log` |
| **Path A (sequential chain — public-beta only)** | `src/lacuna/managed_agent_runner.py::_run_path_a_sequential_fallback` | 3 Managed Agents sessions chained with structured-JSON handoff; the `_run_path_a_callable_agents` branch is reference code only (research-preview Agent Teams disabled for hackathon participants per 2026-04-23 fairness rule) |
| **Path C (Claude Code Routines)** | `src/lacuna/routines_client.py`, `src/lacuna/managed_agent_runner.py::run_path_c_routine` | `POST /v1/claude_code/routines/{trig_id}/fire`; local watch-dir loop fallback when no token configured. **PhL-8d** (dual-verdict oracle) + **PhL-10 oracle** (stage task) are the primary live evidence; PhL-8 is the first proof-of-life fire. |
| **Memory primitives** | `src/lacuna/managed_agent_runner.py::persist_session_events`, `replay_session_from_log` | Brain/body decouple primitives — pages `events.list` to JSONL; re-injects user-origin events into a different session. PhL-4 is the live evidence. |
| **5-test falsification gate** | `src/lacuna/falsification.py` | Deterministic Python; pre-registered thresholds; sign-invariant + seed-controllable since 2026-04-23 P1 fix |
| **Pre-registration framework** | `preregistrations/*.yaml` (28 files), `src/preregistration.py` | Tamper-evidence — every YAML is committed once, bound to a `emitted_git_sha`; `make prereg-audit` machine-verifies the chain |
| **MCP biology validator** | `src/mcp_biology_validator.py`, `.mcp.json` | PubMed E-utilities + GDC REST tools, exercisable both via MCP and direct CLI |
| **Console script** | `pyproject.toml [project.scripts]`, `src/lacuna/cli.py` | `lacuna` CLI with `compare` / `replay` / `loop` / `persist-events` / `replay-events` / `plug-in-dataset` subcommands |
| **`make` targets** | `Makefile` | `make venv`, `make smoke` (~1 min fast judge-visible confidence check on this laptop), `make test` (107 local-runnable tests in the current target), `make audit`, `make h1`, `make h2`, `make paper`, `make prereg-audit`, `make rejection-log`, `make skeptic-review` |
| **Data provenance** | `data/SHA256SUMS` + `docs/public_data_provenance.md` | 13 CSVs hashed; every CSV's upstream source / access tier / builder script / submission role listed in the provenance doc; reviewer can `shasum -c data/SHA256SUMS` offline |
| **Managed Agents observability** | `docs/managed_agents_evidence_card.md` | Per-artefact event + wall-clock table: 17 sessions, 8-lesson shared memory_store, 706 s Path-A chain (PhL-9) + 300 s real-data Path-A (PhL-9v2), 21-event compound orchestrator (PhL-7), **2 live Routine sessions** (PhL-8d dual-verdict + PhL-10 stage oracle) |
| **Compliance** | `.audit-patterns`, `make audit` | Catches institutional identifiers + API key shapes (`sk-ant-api{2}-{6+}`); blocks commits that introduce leaks |

## Doc reading order for technical reviewers

1. `README.md` — what + 60-sec hook
2. `docs/headline_findings.md` — three findings deep
3. `docs/methodology.md` — falsification gate spec, including
   task-dependent active legs, in-sample confound caveat,
   external-replay separate gate
4. `docs/why_opus_4_7.md` — orchestrator framing, Karpathy +
   Sakana citations, Michael Cohen `outcomes` parallel
5. `docs/survivor_narrative.md` — TOP2A − EPAS1 in plain language
6. `docs/paper/paper.pdf` — 6-page workshop-paper-form write-up
7. `docs/submission_description.md` + `docs/submission_form_draft.md` —
   what we submit
8. This file — back-reference for any claim → artefact lookup

## Doc reading order for non-technical reviewers

1. `README.md` opening paragraph
2. `docs/headline_findings.md` Finding 1 (the survivor story)
3. PhL-8d SUMMARY.md (live dual-verdict Routine oracle — open + watch; `results/live_evidence/phl8d_dual_verdict/SUMMARY.md`)
4. `docs/loom_script.md` (90-second video transcript)
