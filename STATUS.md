# STATUS — theory-copilot-falsification

**Last updated:** 2026-04-22 12:30 ET (Phase A kickoff)
**Days to submit:** T-4d 7h30m
**Submit window:** 2026-04-26 20:00 ET
**Judging:** 2026-04-28 12:00 ET

---

## 🟢🟡🔴 Deliverable Dashboard

| # | Deliverable | Owner | Status | Last artifact | Notes |
|---|---|---|---|---|---|
| D1 | E2E `make demo` + flagship_run artifacts | S1 | 🔴 | — | blocker; HPC sweep pending |
| D2 | 90s Loom demo | S3 | 🔴 | — | 4/25 녹화 예정 |
| D3 | README (quickstart + 4 personas) | S3 | 🟡 | a193713 | persona 섹션 미추가 (BP-10) |
| D4 | methodology.md (5-test pre-reg) | S3 | 🟢 | a193713 | polished in uncommitted |
| D5 | Managed Agents evidence | S1 | 🟡 | part4b log | live run 필요 (BP-8) |
| D6 | Extended-thinking transcript | S2 | 🔴 | — | BP-8 live smoke 후 |

## 🛡️ Backup Plan Dashboard

| BP | State | Trigger status | 비고 |
|---|---|---|---|
| BP-1 Template fallback | 🟢 pre-built | not triggered | 14 law_proposals.json |
| BP-2 Scaffold excision | 🟢 done | .gitignore로 pre-hackathon scaffold 제외 + cli.py 워킹트리 institutional-name-free | `make audit` 통과 확인 예정 |
| BP-3 Freeze artifacts | ⚪ script 미생성 | — | E2E 성공 후 |
| BP-5 Cost ledger | 🟡 in progress | 누적 spend $0 | hard cap $350 |
| BP-6 ND2 audit | 🟢 clean | — | prompts/docs 0 matches |
| BP-7 HPC naming | 🟢 tracked 0 | — | audit target 추가됨 |
| BP-8 Live smoke | ⚪ pending | 4/25 22:00 ET cutoff | transcripts 미수집 |
| BP-9 Loom backup | ⚪ pending | — | Plan C GIF 먼저 |
| BP-10 Judge personas | ⚪ pending | — | README 상단 추가 |
| BP-11 Leakage audit | ⚪ pending | — | audit_leakage.py |
| BP-12 Scope freeze | ⚪ pending | **4/24 24:00 ET 강제** | hard gate |
| BP-NULL Honest null | ⚪ pending | 4+0 survivors 시 trigger | null_narrative.md |
| ~~BP-4 MA de-scope~~ | 해제 | Claude 팀 공식 답변 | Path A 메인 경로 |

## 💰 Cost Ledger

| Date | Opus 4.7 USD | Sonnet USD | Cumulative | % of $500 |
|---|---|---|---|---|
| 4/22 | — | — | $0 | 0% |

**Kill-switch trigger:** ≥$350 (70%) OR 24h 윈도우 $150

## 🔄 Session Ownership (current 14h window)

- **S1 "Flagship"** (pending): HPC ControlMaster → full PySR sweep kick off
- **S2 "Guardrails"** (current session): prompts fix ✅ Makefile ✅ STATUS.md ✅ → cost ledger → commit
- **S3 "Narrative"** (pending): judge-persona README, null_narrative.md

**Branch state:**
- `main`: committed + dirty (ready to re-commit with Phase A changes)
- No feature branches needed (BP-2 Path A excision 불필요 확인됨)

**Merge window:** 매일 22:00 ET

## 🚦 Go/No-Go Gates

- [ ] **G1** 4/23 22:00 — flagship_run ≥1 artifact
- [ ] **G2** 4/24 22:00 — full E2E + replay done
- [ ] **G3** 4/25 18:00 — ≥1 survivor OR null-narrative swap-ready
- [ ] **G4** 4/25 22:00 — live-API smoke pass
- [ ] **G5** 4/26 12:00 — Loom rendered
- [ ] **G6** 4/26 18:00 — public push-ready, `make audit` pass
- [ ] **G7** 4/26 20:00 — SUBMIT

## 📝 Decision Log (latest on top)

- 2026-04-22 12:30 ET · [S2] · Phase A 실행 시작. `make audit` target 추가, `.gitignore`가 이미 scaffold 제외 중이라 BP-2 pre-hackathon excision 불필요 확인.
- 2026-04-22 12:00 ET · [S2] · HPC compute approved for heavy PySR sweeps; Managed Agents public-beta confirmed usable (Claude team reply).
- 2026-04-22 (earlier) · [planning] · soft-sniffing-starlight backup plan 작성 완료.
