# Loom visual cue map — segment ↔ asset

Companion to `docs/loom_narration_final_90s.md`. For each of the 8
narration segments, this file lists the **primary on-screen asset** to
display, the **fallback** if the primary isn't ready, and the **exact
file path** to keep open in the recording window.

(Updated 2026-04-25: 8th IPF dual-fabrication-catch segment added
post-IPF-Run-#1; total cut now ~2:23-2:47 at 140-120 WPM, well under
3-min hard cap.)

Loom multi-pane setup (recommended): three side-by-side windows —
**Pane A** (editor), **Pane B** (image viewer / browser), **Pane C**
(terminal). Cue rows below say which pane.

---

## 0:00 – 0:10 — Hook (21 words)

| Slot | Asset | Path | Fallback |
|---|---|---|---|
| Pane A | `results/RESULTS.md` open at top with the "194/203 rejected" headline visible | `results/RESULTS.md` | `README.md` line 3 (the same headline blockquote) |

**Audio**: hook line. **No cuts during these 10 s.**

---

## 0:10 – 0:25 — Architecture (30 words)

| Slot | Asset | Path | Fallback |
|---|---|---|---|
| Pane A | **Architecture diagram** (4-role agent loop + gate + 3 paths) | ⚠️ **NOT YET CREATED** — needs `docs/architecture.png` | `CLAUDE.md` ASCII execution-flow block (visible if window scrolls there) |

**⚠️ ACTION REQUIRED before recording**: create `docs/architecture.png`
showing Proposer → Searcher (PySR) → Falsification gate → Skeptic →
Interpreter, with the three Managed Agents paths (A/B/C) on the side.
Source data: `CLAUDE.md` execution-flow ASCII + `docs/methodology.md
§4` Managed Agents architecture. Keynote 1 slide; export 1920×1080.

---

## 0:25 – 0:45 — Rejection surface (38 words)

| Slot | Asset | Path | Fallback |
|---|---|---|---|
| Pane A (cross-task matrix) | `task_auroc_comparison.png` | `results/track_a_task_landscape/plots/task_auroc_comparison.png` | `results/plots/falsification_panel_all.png` |
| Pane C (terminal cut, ~3 s) | `jq` query that surfaces the HIF-axis failing row live from the report JSON — proves the report is real, not a screenshot | repo root, command in §Pane C terminal cut below | drop terminal cut, fall through to Pane B static view |
| Pane B (rejection log row) | `falsification_report.json` scrolled to a CA9-anchor failing row | `results/flagship_run/falsification_report.json` (or `track_a_task_landscape/tumor_normal/falsification_report.json`) | `delta_baseline_by_task.png` |

**Cut sequence**:
- 0:25–0:32 (matrix) → narrator says "194 of 203 ... across four tasks" (Pane A on screen)
- 0:32–0:36 (**NEW terminal flash**) → narrator says "Even the textbook HIF-axis law Opus itself proposed — log CA9 plus log VEGFA minus log AGXT — fails" (Pane C terminal output of the `jq` command appears)
- 0:36–0:45 (JSON) → narrator says "because CA9 alone already reaches AUROC 0.965" (Pane B with the row pre-scrolled)

**Pane C terminal cut command** (paste, hit enter once recording starts; output ≤ 5 lines, fits one terminal frame):
```bash
jq '.candidates[] | select(.equation | contains("CA9") and contains("VEGFA") and contains("AGXT")) | {equation, fail_reason, delta_baseline}' \
  results/track_a_task_landscape/tumor_normal/falsification_report.json
```
Expected output (must verify before recording — actual key names depend on the schema in this run):
```json
{
  "equation": "log1p(CA9) + log1p(VEGFA) - log1p(AGXT)",
  "fail_reason": "delta_baseline",
  "delta_baseline": 0.019
}
```
**Verify before recording**: run the command once at the repo root; if the schema differs, fall back to a simpler form `jq '.candidates[0] | {equation, fail_reason}' <path>` or drop the cut entirely (no narration changes needed).

**Why this matters**: addresses the 4.6 hackathon "Remotion UI recreation" failure mode by making the rejection a live computation visible on screen — same JSON shown in Pane B, but produced by a real query in Pane C, three seconds before. Bumps terminal-execution coverage from ~7% (only the closing `make audit`) to ~12%, with no narration rewrite required.

---

## 0:45 – 1:05 — Survivor (52 words, with citation emphasis)

| Slot | Asset | Path | Fallback |
|---|---|---|---|
| Pane B (survivor scatter) | `survivor_scatter_top2a_vs_epas1.png` | `results/track_a_task_landscape/plots/survivor_scatter_top2a_vs_epas1.png` | `results/plots/separation_top3_tier1.png` |
| Pane A (interpretation md) | Opus-authored mechanism doc | `results/track_a_task_landscape/survivor_robustness/INTERPRETATION_top2a_epas1.md` | `docs/survivor_narrative.md` "One-minute version" |

**Cut at**: "The simplest — top-two-A minus EE-pass-one —" → scatter
appears. **Hold scatter through the Brannon/ClearCode citation.**

---

## 1:05 – 1:20 — External validation + own-output kill (34 words)

| Slot | Asset | Path | Fallback |
|---|---|---|---|
| Pane B (KM curve) | IMmotion150 PFS Kaplan–Meier | `results/track_a_task_landscape/external_replay/immotion150_pfs/km_median_split.png` | `g4_anchor_regression/anchor_trajectory.png` |
| Pane A (PhL-1 verdict JSON) | 3-gene extension SLC22A8 verdict — must show `"verdict": "FAIL"` | `results/track_a_task_landscape/external_replay/immotion150_slc22a8/km_median_split.png` (KM) + the SUMMARY.md or verdict JSON in the same dir | `results/track_a_task_landscape/external_replay/immotion150_slc22a8/SUMMARY.md` |

**Cut at**: "Then our own three-gene extension. Same survival gate.
Killed it." — verdict JSON shown here.

---

## 1:20 – 1:30 — Routine + close (18 words)

| Slot | Asset | Path | Fallback |
|---|---|---|---|
| Pane B (browser, Path C) | PhL-8 Routine session URL live in incognito tab | `https://claude.ai/code/session_01NyS541H3qZfJgqFVgWDcoM` | `results/live_evidence/04_managed_agents_e2e.log` opened in editor |
| Pane C (terminal) | `make audit` → wait for `OK` line | `make audit` | n/a (terminal always available) |

**Cut at**: "A Claude Code Routine fires this audit server-side." —
browser tab visible. **Last 2 s**: terminal `OK` flash.

---

## 1:30 – 2:05 — DIPG generalization (71 words)

| Slot | Asset | Path | Fallback |
|---|---|---|---|
| Pane A (RESULTS row) | `results/external_validation_dipg/RESULTS.md` with the 7-7-1 verdict distribution row highlighted | `results/external_validation_dipg/RESULTS.md` | `docs/headline_findings.md` DIPG paragraph |
| Pane B (top-lead JSON) | Panobinostat-CED-MTX110 verdict — must show aggregate score 13/15 | `results/external_validation_dipg/top_lead_panobinostat_CED_MTX110/04_panobinostat_CED_MTX110.verdict.json` | n/a — this asset is essential |

**Cut at**: "Top lead: CED-delivered MTX110 panobinostat" — JSON shown
with score 13/15 visible.

---

## 2:05 – 2:35 — IPF dual-fabrication catch (68 words)

| Slot | Asset | Path | Fallback |
|---|---|---|---|
| Pane G (verdict distribution) | `results/external_validation_ipf/RESULTS.md` with the 1-0-4 verdict distribution row highlighted (1 SUPPORTED + 4 INSUFFICIENT_EVIDENCE) | `results/external_validation_ipf/RESULTS.md` | `docs/judge_faq.md` IPF paragraph |
| Pane H (Skeptic kill-attempt JSON) | Skeptic JSON for the top lead with `confounds_flagged` field showing "Nambiar 2023 (PMID 36857968) … OMITTED by advocate" — verifies that the engine self-flags omissions even inside the SUPPORTED verdict | `results/external_validation_ipf/top_lead_DandQ_telomere_short/05_DandQ_telomere_short_IPF.skeptic.json` | `results/external_validation_ipf/top_lead_DandQ_telomere_short/one_pager.md` (Skeptic critical-caveats section) |

**Cut at**: "the Skeptic role caught two Advocate claims" — Skeptic
JSON shown with `confounds_flagged` field visible. The verbal claim
references the parallel candidates 03 (simtuzumab Raghu 2017
fabrication) and 04 (tralokinumab RAINIER fabrication); the on-screen
asset is candidate 05 because (a) it is the public-mirror top-lead,
(b) the same engine pattern (Skeptic catches Advocate omission) is
visible in its `confounds_flagged` field. The full per-candidate
Skeptic JSONs for 03 and 04 live in the private sibling repo
`dipg_rescue/runs/2026-04-25_ipf_run01/` and are not mirrored.

---

## Pre-flight checklist (before camera rolls)

1. **Architecture diagram** ready as `docs/architecture.png` (or
   accept ASCII-fallback in `CLAUDE.md`).
2. **Pane A editor** has `results/RESULTS.md`,
   `INTERPRETATION_top2a_epas1.md`,
   `external_validation_dipg/RESULTS.md` open in tabs.
3. **Pane B image viewer** has the four required PNGs preloaded:
   - `survivor_scatter_top2a_vs_epas1.png`
   - `task_auroc_comparison.png`
   - `immotion150_pfs/km_median_split.png`
   - `immotion150_slc22a8/km_median_split.png`
4. **Pane B incognito browser** preloaded to PhL-8 `claude.ai/code`
   session URL.
5. **Pane C terminal** in repo root with two commands pre-prepared:
   - **First (rejection-surface cut at 0:32):** the `jq` query from
     §"0:25–0:45 Rejection surface" pre-typed but not yet pressed.
     Verify it runs cleanly once before camera rolls — if the schema
     differs from the example output, fall back to the simpler form
     or drop the cut.
   - **Second (Routine + close cut at 1:22):** `make audit` typed
     but not pressed.
   Switch terminal history with up-arrow between cuts; do NOT clear
   the terminal between them (the `jq` output staying visible
   underneath is fine — the narration moves on to other panes).
6. Trim 1 s leading silence; trim trailing silence aggressively;
   1080p / 30 fps single take preferred.
7. **NEW for IPF segment (2026-04-25): Pane G editor** has
   `results/external_validation_ipf/RESULTS.md` open with the 1-0-4
   verdict distribution row visible.
8. **NEW for IPF segment: Pane H editor** has
   `results/external_validation_ipf/top_lead_DandQ_telomere_short/05_DandQ_telomere_short_IPF.skeptic.json`
   open with the `confounds_flagged` field scrolled into view (the
   Nambiar 2023 omission entry is the on-screen evidence that the
   Skeptic catches Advocate omissions even inside the SUPPORTED verdict).

## What is NOT shown (intentional omissions)

- Live API call traces — too noisy on screen, log file path
  referenced instead.
- Cross-model ablation histogram (`results/ablation/plots/model_specificity_histogram.png`)
  — load-bearing for the *write-up* but slows the demo flow. Reviewers
  who care will click `docs/judge_faq.md` Q5.
- Robustness 6-axis heatmaps — same reason; reviewers find them via
  the `survivor_robustness/SUMMARY.md` link if they want.
- Manuscript / paper PDF — judge_faq.md and methodology.md cover the
  same ground in shorter form.

This file is the single source of truth for which assets matter at
recording time. If a Loom-time question is "should I show X?", the
answer is "only if it's listed above."
