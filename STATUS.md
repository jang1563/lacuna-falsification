# STATUS — lacuna-falsification

**Last updated:** 2026-04-26 13:55 EDT (multi-cancer platform expansion complete; submission QA pass)
**Submit window:** 2026-04-26 20:00 ET (deadline is today)
**Judging:** 2026-04-28 12:00 ET final round
**Repo:** https://github.com/jang1563/lacuna-falsification (public since 2026-04-23 19:32 ET)
**Console script:** `lacuna` (post-`pip install -e .`)

---

## 🎯 Submission-ready snapshot

- **24 PhL artefacts** (PhL-1 to PhL-19 + PhL-9v2 + PhL-8b/8c/8d + PhL-10 oracle) all live, all committed. Newest 5 (PhL-15 to PhL-19) are capability-overhang measurements — aggregated at `docs/capability_overhang_measurements.md`.
- **QA pass complete:** 12 of 20 internal review findings resolved (all blocking + friction items); 8 deferred post-hackathon (non-blocking, rationale in commit messages).
- **`make all`** one-command reproduction of tests + audit + prereg-audit + rejection-log + paper PDF (no API key required).
- **`.devcontainer/devcontainer.json`** — one-click dev container (VS Code Dev Containers or GitHub Codespaces); `make test` green in ~2 min after container start.
- **`.claude/skills/falsification-gate/SKILL.md`** — Claude Code skill wrapping the gate as a discoverable, deterministic verification primitive.
- GitHub repo renamed to **`jang1563/lacuna-falsification`** on 2026-04-26; old Theory Copilot URL redirects.
- 107/107 local-runnable tests in the current `make test` target · 2026-04-26 `make smoke` OK · GitHub public, `make all` runnable end-to-end without credentials.

## 🧪 Phase L artefact ledger (this hackathon's contributions)

| ID | Verdict | Anchor |
|---|---|---|
| **PhL-1** | FAIL — gate killed our own H1 SLC22A8 extension on IMmotion150 | `results/.../external_replay/immotion150_slc22a8/SUMMARY.md` |
| **PhL-2** | OK — MCP biology validator live (PubMed co-mention 0 = independent rediscovery signal) | `results/live_evidence/09_mcp_biology_validator_live.log` |
| **PhL-3** | PASS — Managed Agents Memory public-beta integrated day-of (Rakuten pattern) | `results/live_evidence/phl3_memory_smoke/SUMMARY.md` |
| **PhL-4** | PASS — `events.list` persist + replay across fresh session | `results/live_evidence/phl4_persist_replay/SUMMARY.md` |
| **PhL-5** | FAIL as predicted — TCGA-BRCA cross-cancer negative control (ccRCC-specificity confirmed) | `results/.../external_replay/brca_cross_cancer/SUMMARY.md` |
| **PhL-6** | T-vs-N FAIL (platform saturation); stage 1-2 vs 3-4 PASS AUC 0.714 — 4th cohort + 1st platform shift | `results/.../external_replay/gse53757/SUMMARY.md` |
| **PhL-7** | PASS — compound orchestrator (MCP + Memory + 5-test gate in ONE Managed Agents session, cross-substrate reasoning) | `results/live_evidence/phl7_compound_orchestrator/SUMMARY.md` |
| **PhL-8** | 200 OK — Claude Code Routines `/fire` LIVE; clickable session URL committed (first proof-of-life) | `results/live_evidence/phl8_routine_fire/SUMMARY.md` |
| **PhL-8b** | PARTIAL — Schedule trigger fired autonomously (no client action, laptop closed); blocked by workspace extra-usage quota at turn 1; mechanism layer evidenced | `results/live_evidence/phl8b_routine_schedule/SUMMARY.md` |
| **PhL-8c** | PASS — Upgraded `lacuna-scientific-oracle` Routine autonomously runs full falsification_sweep (1000/1000/100, n=505); structured PASS/FAIL verdict; `session_015ot5hkJgSiBoWNA51fjZ1k` | `results/live_evidence/phl8c_scientific_oracle/SUMMARY.md` |
| **PhL-8d** | **FAIL+PASS** — Dual-verdict oracle: Eq1 `CA9−AGXT` FAIL (delta_baseline=0.0145) + Eq2 `CDK1−EPAS1` PASS (delta_baseline=0.0622, ci_lower=0.662) in one session; methodology proof in one URL; `session_01CgsJYAPdvhJJwTuBt7QZLZ` | `results/live_evidence/phl8d_dual_verdict/SUMMARY.md` |
| **PhL-9** | OK — Path A sequential 3-session chain live (`delegation_mode=sequential_fallback`, 706 s) | `results/live_evidence/phl9_path_a_chain/SUMMARY.md` |
| **PhL-10 (mem)** | PASS — Memory chain extended 3 → 5 lessons; ceiling-effect rule generalizes KIRC→LUAD | `results/live_evidence/phl10_memory_chain_extended/SUMMARY.md` |
| **PhL-10 (oracle)** | **FAIL+PASS** — Stage oracle (second Routine, new per-disease): `CCNB1/PGK1` FAIL + `CXCR4/EPAS1` PASS (AUROC 0.696, ci_lower=0.649, Δbase=+0.051, n=512); `session_01XGse8XYFtv3C1aKLZeMH9t` | `results/live_evidence/phl10_stage_oracle/SUMMARY.md` |
| **PhL-9v2** | OK — Path A on **real TCGA-KIRC** via `files.upload()` mount; Skeptic quotes `delta_baseline=+0.0587` on LF-PROLIF-minus-HIF2A | `results/live_evidence/phl9v2_path_a_real_data/SUMMARY.md` |
| **PhL-11** | Mixed — Opus 4.7 vs Sonnet 4.6 3-turn adversarial: Opus literal per-attack rule following (5 vs 1 CRISPR KO); both 100% concede (Petri-2.0 consistent) | `results/live_evidence/phl11_adversarial_critique/SUMMARY.md` |
| **PhL-12** | PASS — Memory chain deepened 5 → **8** lessons; agent quoted + applied prior meta-rules across 3 edge cases | `results/live_evidence/phl12_memory_chain_deepen/SUMMARY.md` |
| **PhL-13** | **DISCOVERY SIGNAL** — TOP2A-EPAS1 in 0/10 Opus 4.7 zero-shot top picks; refutes LLM-SRBench memorization concern | `results/live_evidence/phl13_memorization_audit/SUMMARY.md` |
| **PhL-14** | HONEST NULL — 10-iter × 2-model × 6-variant sweep: 18 post-seed LLM-proposed skeleton families, 0 clear the gate; gate is the binding constraint (not the LLM proposer) | `results/overhang/llm_sr_10iter/SUMMARY.md` |
| **PhL-15** | HONEST NULL (3-run instrumentation log) — thinking causal ablation on Opus 4.7: v2 final (adaptive_max 19.6s vs no_thinking 7.7s — thinking confirmed active) both 0/60 PASS. E2 confound discovered: Opus 4.7 E2 calls all hit 400 on "enabled" and ran WITHOUT thinking (8s latency). E2 10/60 PASS = base calibration (no thinking) beats Sonnet 0/60 WITH thinking. Gap is RLHF property, not thinking-dependent | `results/live_evidence/phl15_adaptive_thinking/SUMMARY.md` |
| **PhL-16** | **0/48 gated proposals PASS** (Opus 0/30, Sonnet 0/18) — combined with PhL-14, ~66 consecutive LLM-proposed laws rejected across 5+ model/iteration combos. Gate model-independent. Format compliance: Opus 30/30, Sonnet 18/30, Haiku 0/30 | `results/live_evidence/phl16_proposer_quality/SUMMARY.md` |
| **PhL-17** | Stance-decay 7-turn on TOP2A-EPAS1 (30 sessions, 210 turns): Opus 4.7 conceded 2/10 only on valid Rashomon arguments (calibrated update); Sonnet 4.6 held PASS 10/10; Haiku 4.5 errored 10/10. **Pre-registered-gate citation rate**: Opus 78.6%, Sonnet 75.7% (both strong models cite gate authority to hold stance) | `results/live_evidence/phl17_stance_decay/SUMMARY.md` |
| **PhL-18** | Pre-registration YAML writing: Opus 5/5 valid (100% schema coverage, compact 3.7k chars), Sonnet 5/5 valid (verbose 7.4k chars, 2× numeric values, not more kill tests), Haiku 0/5 (adaptive-thinking + YAML ceiling) | `results/live_evidence/phl18_prereg_writing/SUMMARY.md` |
| **PhL-19** | Interpreter structured-JSON mechanism hypothesis: Opus 3/3 valid (100%), Sonnet 0/3 (1 truncated + 2 empty), Haiku 0/3 (empty). Direct instruction-following + token-budget-management capability gap under adaptive thinking | `results/live_evidence/phl19_interpreter_depth/SUMMARY.md` |

Plus pre-Phase-L artefacts (Flagship + Tier 2 + Track A/B + Phase F preregs + G/H/I depth + IMmotion150 PhF-3 replay + paper) — full index at `docs/ARTIFACT_INDEX.md`.

## 📊 Numbers (corrected per review handoff)

- **5-test classification gate (TCGA, 7 task × panel configurations, pre-2026-04-26):** 194 / 203 rejected; 9 survivors all on metastasis_expanded with `delta_confound = null` (4 active legs + decoy + BH-FDR for that task).
- **Flagship survivor:** `TOP2A − EPAS1`, AUROC 0.726 on TCGA-KIRC metastasis (n=505).
- **IMmotion150 Phase-2 external replay (separately pre-registered 3-test survival gate, n=263):** PASS — log-rank p=0.0003, Cox HR=1.36, C-index=0.601, robust to treatment arm + TMB adjustment.
- **PhL-1 cross-cohort kill of own H1 extension:** the SLC22A8-augmented form failed the same survival replay (C dropped 0.601 → 0.566).
- **PhL-6 third cohort (microarray):** TOP2A − EPAS1 stratifies stage 1-2 vs 3-4 with AUROC 0.714.
- **Cross-cancer negative control (PhL-5 BRCA):** FAIL on `delta_baseline` as predicted; ccRCC-specificity reinforced.

### 🌐 Platform generalization (2026-04-26, same gate + thresholds)

All tracks complete. Same pre-registered +0.05 delta_baseline threshold across all diseases.

| Task | Cancer | Panel | n | Top law | AUROC | Survivors |
|---|---|---|---|---|---|---|
| Stage I-II vs III-IV | KIRC | 11-gene (ref) | 534 | — (CUBN ceiling) | — | 0/34 |
| Stage I-II vs III-IV | KIRC | **45-gene** | 512 | `CXCR4 / EPAS1` | 0.689 | **23/28 ✅** |
| Tumor vs Normal | LIHC | 31-gene | 424 | — (ALB/TTR ~0.985 saturates) | — | **0/26** |
| Stage I-II vs III-IV | COAD | 31-gene | 484 | `SLC2A1 + PDCD1LG2 + VIM − MYC` | 0.658 | **15/22 ✅** |
| Grade II vs III | LGG | 30-gene | 384 | `log1p(TWIST1×MKI67+VIM) − CDH2/NES` | 0.840 | **2/25 ✅** |

Pattern: gate accepts when panel has distributed features (no single-gene saturator, moderate ceiling).
Gate refuses when one gene dominates (LIHC: hepatic function marker ~0.985, same as KIRC CA9 ~0.965).
Results: `results/track_a_task_landscape/{stage_expanded,lihc,coad_msi,gbm_idh}/`

## 🔧 Architecture surfaces (judge-facing)

- **Path B — single agent + `agent_toolset_20260401`** (public beta, live).
- **Path A — sequential 3-session chain** (public-beta only; the `_run_path_a_callable_agents` branch is reference code per 2026-04-23 hackathon-fairness rule on research-preview Agent Teams).
- **Path C — Claude Code Routines `/fire` LIVE** (PhL-8 first proof-of-life; **PhL-8d dual-verdict oracle** `session_01CgsJYAPdvhJJwTuBt7QZLZ` + **PhL-10 stage oracle** `session_01XGse8XYFtv3C1aKLZeMH9t` — 2 live browser-inspectable sessions).
- **Memory primitives** — `persist_session_events` + `replay_session_from_log` shipping as working code (PhL-4) and as a same-day Memory-store integration (PhL-3).
- **MCP biology validator** — PubMed E-utilities + GDC REST tools, exercisable via MCP and direct CLI.
- **Pre-registration framework** — 28 YAMLs, tamper-evidence via git commit-SHA binding + `data/SHA256SUMS`.
- **Console script + `make` targets + `.devcontainer/`** — one-command reproduction surfaces.

## 🛠 Code health

- 107/107 local-runnable tests pass via `make test` (review/staging suites are intentionally ignored by that target).
- 2026-04-26 `make smoke` OK after final packaging review; the smoke target now runs critical imports, a tiny deterministic gate sanity check, compliance audit, and artefact-presence checks.
- `make audit` OK — institutional-identifier scan + API-key-shape regex (`sk-ant-api{2}-{6}`) clean.
- `make all` (no API key) reproduces: tests + audit + prereg-audit + rejection-log + paper PDF.
- Falsification gate verified sign-symmetric (`fn` and `-fn` produce identical verdicts post-2026-04-23 P1 fix) and deterministic (same seed → identical perm_p / ci_lower / decoy_p).

## 📝 Submission docs (final or near-final)

- `README.md` — corrected sub-hook + opening + honest scoping note + compliance section + `make venv && make smoke && make audit` quick path.
- `docs/headline_findings.md` — Finding 1/2/3 with PhL-1 own-output kill embedded in Finding 2.
- `docs/methodology.md` — task-dependent active legs + separate survival gate + in-sample confound caveat.
- `docs/why_opus_4_7.md` — orchestrator framing + Karpathy + Sakana + Tharik + Michael Cohen `outcomes` parallel.
- `docs/submission_description.md` — verification-first pipeline + Skeptic-as-subagent + own-output kill.
- `docs/submission_form_draft.md` — one-line pitch (134/140 char), summary (125/150 word), MA usage (140/150 word), prize justification (under cap).
- `docs/paper/paper.md` + `docs/paper/paper.pdf` — 7-item Limitations §4.5 + Industry-convergence §4.6.
- `docs/loom_script.md` — 90-second shot list with PhL-1 IMmotion150 beat + alternative PhL-3/PhL-4 close.
- `docs/ARTIFACT_INDEX.md` — 1-page judge navigation.

## 🎬 What's left (submission day)

| Time | Task | Owner |
|---|---|---|
| 2026-04-26 early AM | Record/upload Loom, then paste public URL into `docs/submission_form_draft.md` | user |
| 2026-04-26 after Loom | Run `make smoke` + `make audit`; verify GitHub URL and demo URL both open without sign-in | both |
| 2026-04-26 ~19:30 ET | Final pre-submit check: repo public, video public, 100-200 word summary pasted exactly | user |
| 2026-04-26 **20:00 ET** | Submit form | user |

## ⚠ Decisions deliberately NOT taken

- **Docker packaging skipped** — `make venv` + `.devcontainer/` cover 80% of value at 1/4 the time; 0/5 of the 4.6 winners shipped Docker; Anthropic public signals show 0 Docker mentions in any of the 3 sessions or Discord Q&A.
- **Multi-agent Agent Teams (`callable_agents`) skipped** in submission run per 2026-04-23 hackathon fairness ruling; reference code retained in `_run_path_a_callable_agents` behind env flag.
- **DatasetCard end-to-end refactor (review #13) deferred** — `compare` uses it; `replay` doesn't. Out of submission scope.
- **PySR import side-effect deferral (review #10) deferred** — slow first CLI invocation, not blocking.
- **Out-of-fold confound upgrade (review #20) deferred** — moot for current flagship survivor (`delta_confound=null`); flagged in methodology for plug-in dataset future.

---

*Pinned 2026-04-23 22:00 ET. Subsequent edits should be commit-message-tracked, not file-wide rewrites, until the 2026-04-26 20:00 ET submission.*
