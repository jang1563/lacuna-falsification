# STATUS — theory-copilot-falsification

**Last updated:** 2026-04-23 01:20 ET (Phase F content-depth pass closed)
**Days to submit:** T-3d 18h40m
**Submit window:** 2026-04-26 20:00 ET
**Judging:** 2026-04-28 12:00 ET

---

## 🎯 Headline artifact state

Scientific payload is complete. Phase E (Enhancement) Lane 1 has landed
Platform / AI-for-Science / Discovery upgrades locally — commits await
user authorization for `git push` to `origin/main` (default-branch
protection blocks automated push). Lanes 2 (Experiments) and 3 (Narrative
+ stretch) are available in parallel Claude Code sessions per the Phase E
plan file under `~/.claude/plans/`.

- **Flagship (11-gene panel, 4 ccRCC tasks):** 0 / 100+ candidates
  survive the pre-registered 5-test gate. `delta_baseline` ceiling at
  +0.029.
- **45-gene expanded panel:** 9 / 30 candidates pass on the metastasis
  task; simplest surviving law is `TOP2A − EPAS1` (proliferation minus
  HIF-2α) at AUROC 0.726, `delta_baseline = +0.069`.
- **Survivor robustness (6 axes + 5-fold CV):** passes 5 / 6 axes;
  single honest caveat is the LR pair-with-interaction baseline
  (`Δ = +0.004`, indicating the survivor is a compact monotone form
  of the `(TOP2A, EPAS1)` interaction rather than a multi-gene
  discovery beyond that pair).
- **Track B gate robustness (flagship 0-survivor verdict):** robust to
  threshold grid, baseline definition, permutation count, bootstrap
  seed, and cohort size; soft along feature-scaling (1/34 crosses a
  reduced-gate threshold).

---

## 🟢🟡🔴 Deliverable Dashboard

| # | Deliverable | Owner | Status | Last artifact | Notes |
|---|---|---|---|---|---|
| D1 | E2E `make demo` + flagship_run artifacts | N | 🟢 | results/flagship_run/, results/tier2_run/, results/track_a_task_landscape/, results/track_b_gate_robustness/ | Phase Q Q3/Q4 re-verified streaming fix |
| D2 | 90s Loom demo | N | 🔴 | — | Loom recording 4/25 |
| D3 | README (quickstart + persona + paper link) | N | 🟢 | b6d041a | E9 added paper link, persona pass done |
| D4 | methodology.md (5-test pre-reg + survivor section) | N | 🟢 | f758857 | §6 positive-survivor + 4-task reject table |
| D5 | Managed Agents evidence | N | 🟢 | results/live_evidence/04_managed_agents_e2e.log | Path B end-to-end verified |
| D6 | Extended-thinking transcript | N | 🟢 | results/live_evidence/{01,02,03}.log | all live, $0.20 cost |
| D7 | Survivor finding + interpretation | N | 🟢 | results/track_a_task_landscape/survivor_robustness/{SUMMARY.md, INTERPRETATION_top2a_epas1.md} | Sci-A phase output |
| D8 | Gate robustness finding | N | 🟢 | results/track_b_gate_robustness/SUMMARY.md | Sci-B phase output |
| D9 | Submission form draft (≤150 w) | N | 🟢 | 5e0f489 | docs/submission_form_draft.md ready, Loom URL slot 대기 |
| D10 | CLAUDE.md + .claude/agents/ subagent tree | E | 🟢 | 94b3d5e | Boris-style Claude Code onboarding (E1) |
| D11 | DatasetCard + `plug-in-dataset` CLI | E | 🟢 | 18a1763 | 4 committed cards + auto-inference subcommand (E4) |
| D12 | TCGA-LUAD second-disease run | E | 🟢 | 6a0963f | data/build_tcga_luad.py + opus-exante report (E5) |
| D13 | MCP biology-validator server | E | 🟢 | fe3fb62 | validate_law + fetch_cohort_summary (E8) |
| D14 | docs/paper/paper.pdf | E | 🟢 | b6d041a → 0f3ce58 | 6-page workshop-paper via pandoc (E9) + PhF-2 benchmark section |
| D15 | Pre-registration YAML artifact (PhF-1) | F | 🟢 | 0444629 | 17 committed YAMLs + make prereg/validate/audit + tamper-evidence audit chain |
| D16 | External-cohort survival replay (PhF-3) | F | 🟢 | f9c88d1 | IMmotion150 PFS: 3/3 pre-reg kill tests PASS (log-rank p=0.0003, HR=1.36, C=0.601) |
| D17 | Benchmark vs SPOT / Sakana-v2 / POPPER (PhF-2) | F | 🟢 | 0f3ce58 | docs/paper/benchmark_vs_related.md + paper §4.2 |
| D18 | Rejection Log static HTML + GitHub Pages (PhF-4) | F | 🟢 | 3ce8a6b | 204 candidates / 194 rejected; `.github/workflows/pages.yml` |
| D19 | Path C Routine + Nightly Falsifier (PhF-5) | F | 🟢 | e81b8e6 | `theory-copilot loop` + `.github/workflows/nightly_falsifier.yml` |
| D20 | Headline findings master-narrative doc | F | 🟢 | e81b8e6 | docs/headline_findings.md — 3 findings × before/after/"6 months ago" |

## 🛡️ Backup Plan Dashboard

| BP | State | Trigger status | 비고 |
|---|---|---|---|
| BP-1 Template fallback | 🟢 pre-built | not triggered | 7+ KIRC law families |
| BP-2 Scaffold excision | 🟢 done | .gitignore로 pre-hackathon scaffold 제외, cli.py rewritten institutional-name-free | `make audit` pass |
| BP-3 Freeze artifacts | 🟢 done | results/ under version control | flagship + tier2 + track_a + track_b + plots |
| BP-5 Cost ledger | 🟡 in progress | 누적 spend ≈ $0.20 | hard cap $350, well under |
| BP-6 ND2 audit | 🟢 clean | — | prompts/docs 0 matches |
| BP-7 HPC naming | 🟢 clean | — | `make audit` via .audit-patterns external pattern file |
| BP-8 Live smoke | 🟢 done | 4/22 early; api_validation_log.txt recorded | transcripts in results/live_evidence/ |
| BP-9 Loom backup | ⚪ pending | 4/26 12:00 ET cutoff | Phase N7 |
| BP-10 Judge personas | ⚪ pending | — | Phase N5 |
| BP-11 Leakage audit | 🟡 deferred | — | implicit in train/test split + CV replay; doc N-task TBD |
| BP-12 Scope freeze | 🟢 held | **4/24 24:00 ET 강제** | research additions stopped; Phase N/Q is narrative + QA only |
| BP-NULL Honest null | 🟢 morphed | converted to "accept+reject narrative" after 9-survivor finding | survivor_narrative.md (N6) replaces null_narrative |
| ~~BP-4 MA de-scope~~ | 해제 | Claude 팀 공식 답변 | Path B verified |

## 💰 Cost Ledger

| Date | Opus 4.7 USD | Sonnet USD | Cumulative | % of $500 |
|---|---|---|---|---|
| 4/22 | $0.20 | — | $0.20 | 0.04% |

**Kill-switch trigger:** ≥$350 (70%) OR 24h 윈도우 $150

## 🔄 Session Ownership (current phase)

- **Phase N (this session, formerly Sci-A)** — Narrative:
  STATUS / README / docs / prompts / submission form.
- **Phase Q (other session, formerly Sci-B)** — QA:
  `make test` / `make audit` / `make demo*` / plot sanity / doc
  consistency / live-transcript coherence.

Cross-phase handoffs: `HANDOFF_to_N.md` and `HANDOFF_to_Q.md` at repo
root (gitignored). Read before committing.

**Branch state:** `main` is the only branch. Latest origin/main
commit: `7a70919 [N] Restamp coordination contract header`.

## 🚦 Go/No-Go Gates

- [x] **G1** 4/23 22:00 — flagship_run ≥ 1 artifact (met early: flagship + tier2 + track_a + track_b)
- [x] **G2** 4/24 22:00 — full E2E + replay done (5-fold CV stands in for GSE40435; documented limitation)
- [x] **G3** 4/25 18:00 — ≥ 1 survivor OR null-narrative swap-ready (9 survivors on metastasis_expanded)
- [x] **G4** 4/25 22:00 — live-API smoke pass (done 4/22)
- [ ] **G5** 4/26 12:00 — Loom rendered (Phase N7)
- [ ] **G6** 4/26 18:00 — public push-ready, `make audit` pass (Phase Q validates)
- [ ] **G7** 4/26 20:00 — SUBMIT

## 📝 Decision Log (latest on top)

- 2026-04-23 01:20 ET · [F] · **Phase F content-depth closed.** 5 items shipped (PhF-1 pre-registration YAML artifact + 17 committed YAMLs; PhF-2 SPOT/Sakana-v2/POPPER benchmark section in docs/paper/benchmark_vs_related.md + paper §3.5/§4.2; PhF-3 IMmotion150 external replay — all 3 pre-registered kill tests PASS, log-rank p=0.0003, HR=1.36, C-index=0.601, 7.5-month median-PFS gap on independent immunotherapy cohort; PhF-4 rejection log HTML + GitHub Pages workflow — 204 candidates / 194 rejected / 10 accepted; PhF-5 Path C Routine driver + nightly GitHub Actions workflow). Commits 0444629, f9c88d1, 0f3ce58, 3ce8a6b, e81b8e6. `make test` 72/72; `make audit` clean. Headline findings doc at docs/headline_findings.md. Submission form draft rewritten for Phase F. Awaiting user push authorization + Tharik-quote doc review (still in working tree).
- 2026-04-22 19:05 ET · [E] · Phase E Lane 1 complete locally: E1 (CLAUDE.md + 4 subagents), E4 (DatasetCard + plug-in-dataset CLI + 3 tests), E5 (TCGA-LUAD build + ex-ante run + log1p-safe-eval bug fix), E8 (MCP biology-validator + 9 tests), E9 (docs/paper/paper.pdf via pandoc). Commits: 94b3d5e, 18a1763, 6a0963f, fe3fb62, b6d041a. `make test` 59/59 post-Lane-1; `make audit` clean. Awaiting user authorization to push to origin/main.
- 2026-04-22 16:45 ET · [E] · Phase E plan v3 signed off. User elected full Tier 1 + 2 + 3 with 2-3 parallel lanes. Plan file at `~/.claude/plans/vast-swimming-kitten.md`. Lane 1 (this session) owns Platform; Lanes 2 and 3 remain for future sessions.
- 2026-04-22 14:35 ET · [N] · Phase transition from Sci-A/B to Phase N/Q. N queue = narrative docs; Q queue = E2E tests + audit + plot sanity. SESSION_COORDINATION.md updated.
- 2026-04-22 ~14:00 ET · [Sci-A] · 🎯 9 survivors on metastasis_expanded with 45-gene panel. TOP2A − EPAS1 passes 6-axis robustness (5 / 6 axes; honest caveat on pair+interaction baseline). 5-fold CV AUROC 0.722 ± 0.078.
- 2026-04-22 ~13:00 ET · [Sci-B] · Track B B1-B7 complete. Flagship 0-survivor verdict robust along 5 of 6 axes; feature scaling is soft.
- 2026-04-22 12:30 ET · [S2] · Phase A 실행 시작. `make audit` target 추가, `.gitignore` 가 이미 scaffold 제외 중이라 BP-2 pre-hackathon excision 불필요 확인.
- 2026-04-22 12:00 ET · [S2] · HPC compute approved for heavy PySR sweeps; Managed Agents public-beta confirmed usable (Claude team reply).
- 2026-04-22 (earlier) · [planning] · soft-sniffing-starlight backup plan 작성 완료.

## 🧭 Phase N queue (all items closed)

1. **N1** STATUS.md refresh ✅
2. **N2** docs/methodology.md §6 positive-survivor section ✅
3. **N3** docs/why_opus_4_7.md §4 accept + reject demo moment ✅
4. **N4** docs/submission_description.md accept + reject rewrite ✅
5. **N5** README persona section (Boris / Lydia / Jason / domain view) ✅
6. **N6** docs/survivor_narrative.md ✅
7. **N7** docs/loom_script.md 90-second demo script ✅
8. **N8** docs/submission_form_draft.md — every form field length-capped ✅

Cross-phase emergency fixes committed on top:
- `[N] BLOCKER-1 fix` — opus_client._call to streaming API (9997b23)
- `[N] H1-H3 plot regeneration` — falsification_panel_all, delta_baseline_hist, task_auroc_comparison, delta_baseline_by_task updated with correct counts + metastasis_expanded inclusion (9b433e0)

## 🧭 Phase E Lane 1 queue (all items closed locally)

1. **E1** CLAUDE.md + `.claude/agents/{proposer,skeptic-reviewer,interpreter,qa-validator}.md` ✅ (94b3d5e)
2. **E4** `src/theory_copilot/data_loader.py` DatasetCard + `compare --dataset-card` + `plug-in-dataset` subcommand + 3 new tests ✅ (18a1763)
3. **E5** `data/build_tcga_luad.py` + LUAD Opus ex-ante falsification (0/4 survivors, SFTPC saturates) + `make_equation_fn` log1p-on-negative-z-score bug fix ✅ (6a0963f)
4. **E8** `src/mcp_biology_validator.py` (validate_law + fetch_cohort_summary) + `.mcp.json` + 9 unit tests ✅ (fe3fb62)
5. **E9** `docs/paper/paper.md` → `docs/paper/paper.pdf` via `make paper` + README link ✅ (b6d041a)
6. **E11** STATUS refresh (this commit)

## 🧭 Submit-window action list (4/25 - 4/26)

1. 4/25 12:00 – 18:00 ET — Record the Loom demo using `docs/loom_script.md`.
2. 4/25 22:00 ET — Paste the Loom URL into `docs/submission_form_draft.md` "Demo video" section. Commit as `[N] Loom URL embed`.
3. 4/26 12:00 ET — Full `make test` + `make audit`; review Phase Q `results/qa/SUMMARY_qa.md` for any last findings.
4. 4/26 18:00 ET — Copy `docs/submission_form_draft.md` contents into the Cerebral Valley × Anthropic form. Verify every length cap.
5. 4/26 19:30 ET — Flip GitHub repo `jang1563/theory-copilot-falsification` from private to public.
6. 4/26 20:00 ET — Submit.
