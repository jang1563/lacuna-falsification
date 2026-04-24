# Loom narration — final ≤2:00 cut (includes DIPG generalization tag)

**Status:** submission-locked final script (updated 2026-04-24 post-DIPG-run).
**Target:** ≤ 120 seconds end-to-end; soft 100 s target; hard 180 s cap.
**Word count:** 254 words / ~109 s at 140 WPM / ~127 s at 120 WPM (see ledger below for per-segment breakdown).
**Parent:** `docs/loom_narration_verbatim.md` (longer 246-word "six
experiments once" variant). Use this file as the primary script for the
final recording. Revert to the parent only if the user wants to restore
the Karpathy opening.

**Style notes:**
- Read steady, declarative. Postdoc presenting a method paper.
- Pauses as `…` (≈300 ms) and `[breath]` (≈600 ms).
- Numbers spoken plainly: "0.726" = "zero point seven-two-six";
  "194 of 203" = "one hundred ninety-four of two hundred three".
- "TOP2A" = "top-two-A"; "EPAS1" = "EE-pass-one";
  "ccRCC" = "see-see-R-C-C"; "ccA/ccB" = "see-see-A vs see-see-B";
  "IMmotion150" = "Im-motion one-fifty".

---

## 0:00 – 0:10 — Hook (22 words)

**Cue: editor pane A — `results/RESULTS.md` open at top.**

> "Most AI-for-Science demos celebrate the first high-scoring result.
> This one starts with rejection. … A loop that cannot reject is not
> a loop."

## 0:10 – 0:25 — Architecture (30 words)

**Cut to slide 1 — Architecture diagram.**

> "Opus four-point-seven proposes seven compact law families for
> see-see-R-C-C, including a housekeeping negative control. A
> deterministic five-test Python gate rejects weak candidates
> [breath] before any LLM judgement."

## 0:25 – 0:45 — Rejection surface (38 words)

**Cut to editor pane B — Track A cross-task matrix, then pane C —
rejection log scrolled to CA9 row.**

> "On real T-C-G-A kidney clear cell, the gate rejects one hundred
> ninety-four of two hundred three candidate evaluations across four
> tasks. [breath] Even the textbook HIF-axis law Opus itself proposed
> — log C-A-9 plus log V-E-G-F-A minus log A-G-X-T — fails, because
> C-A-9 alone already reaches A-U-R-O-C zero point nine-six-five."

## 0:45 – 1:05 — Survivor (36 words)

**Cut to image viewer A — survivor_scatter PNG, then pane D —
interpretation markdown.**

> "Expand the panel from eleven to forty-five genes. Same gate. Nine
> candidates pass on metastasis. The simplest — top-two-A minus
> EE-pass-one — says proliferation running ahead of HIF-two-alpha
> predicts metastasis. [breath] **That is the published see-see-A vs
> see-see-B ccRCC subtype axis — Brannon twenty-ten, ClearCode
> thirty-four. Our symbolic regression re-derived it unseeded."

## 1:05 – 1:20 — External validation + own-output kill (34 words)

**Cut to image viewer B — IMmotion150 KM curve, then pane E — PhL-1
verdict JSON with `"verdict": "FAIL"` visible.**

> "Cross-cohort replay on Im-motion one-fifty — a separately
> pre-registered survival gate. Hazard ratio one point three-six,
> log-rank p zero point zero-zero-zero-three. [breath] Then our own
> three-gene extension. Same survival gate. Killed it."

## 1:20 – 1:30 — Routine + close (18 words)

**Cut to browser showing PhL-8 `claude.ai/code/session_01NyS...` URL
live, then terminal — type `make audit`, wait for `OK`.**

> "A Claude Code Routine fires this audit server-side. … The system
> publishes the law, the graveyard, and the kill-switch."

## 1:30 – 2:00 — DIPG generalization (~60 words, ~26 s)

**Cut to editor pane F — `results/external_validation_dipg/RESULTS.md`
with verdict distribution row highlighted (mirrored from `dipg_rescue/`
git repo, SHA `8a4ecc5`); then image viewer C — top-lead panobinostat-CED
candidate verdict JSON at `results/external_validation_dipg/top_lead_panobinostat_CED_MTX110/04_panobinostat_CED_MTX110.verdict.json`
with aggregate score 13/15.**

> "Same engine on a structurally distant second disease. Pediatric
> brainstem cancer — H-three K-twenty-seven-M diffuse midline glioma.
> Fifteen pre-registered rescue hypotheses locked at git SHA
> eight-A-four-E-C-C-five. Seven supported. Seven mixed. One rejected.
> Top lead: CED-delivered MTX110 panobinostat — the
> pharmacokinetic-not-pharmacodynamic rescue of the P-B-T-C-047
> failure, score thirteen of fifteen. [breath] Same engine. Different
> disease. Same rejection-as-product pattern."

---

## Word-count ledger

| Segment | Words | Cumul | Time @ 140 WPM | Time @ 120 WPM |
|---|---|---|---|---|
| 0:00-0:10 Hook | 22 | 22 | 9 s | 11 s |
| 0:10-0:25 Architecture | 30 | 52 | 13 s | 15 s |
| 0:25-0:45 Rejection | 38 | 90 | 16 s | 19 s |
| 0:45-1:07 Survivor (with citation emphasis) | 52 | 142 | 22 s | 26 s |
| 1:07-1:22 Validation + kill | 34 | 176 | 15 s | 17 s |
| 1:22-1:30 Routine + close | 18 | 194 | 8 s | 9 s |
| 1:30-2:00 DIPG generalization (NEW) | 60 | 254 | 26 s | 30 s |
| **TOTAL** | **254** | — | **~109 s** | **~127 s** |

Budget (post-DIPG-tag): 120 s soft target, 180 s hard cap. At 140 WPM
the full cut with the DIPG generalization tag runs 109 s (under the
120 s soft cap — 11 s margin). At 120 WPM (slower, authoritative
pace) it runs 127 s — 7 s over soft cap, 53 s under hard cap.

**Budget controls at recording time:**
- If the 120 s soft cap must be held at slow pace: drop the "Brannon
  twenty-ten, ClearCode thirty-four" citation line from the survivor
  segment (5 words / 2 s). Citation lives in `docs/survivor_narrative.md
  §Prior art` for pause-viewers.
- If 90 s target is required (pre-DIPG scope): drop the entire DIPG
  generalization tag (1:30-2:00, 60 words / 26 s). Back to 194 words /
  83 s at 140 WPM.

## Pre-flight (before camera rolls)

Same 9-pane layout as `loom_narration_verbatim.md §Pre-flight`. The
only differences for this cut:

- **Slide 1** is the Architecture diagram (required).
- **No Karpathy screenshot** — the hook is the pipe-shaped "rejection
  celebrates first" line, no citation frame.
- **Browser tab** pre-loaded to the PhL-8 `claude.ai/code/session_...`
  URL in an incognito window so the Routine-session screenshot is clean.

## Honest-framing triggers (do NOT deviate at recording time)

Pulled from `docs/CLAIM_LOCK.md`:

- Never say "same gate on IMmotion150" alone — always add "separately
  pre-registered survival replay" or equivalent.
- Never say "full five-test pass" without the `delta_confound = null`
  caveat — "nine candidates pass" is correct; "pass the full five-test"
  is not.
- Never say "novel kidney cancer biology" — this is rediscovery.
- Never say "194 of 204" — it is 194 of 203.

If the recording stumbles on any of these phrases: stop the take,
re-read this section, start over.

## Fallback backup hook (if main hook stumbles)

> "A Python gate rejects one hundred ninety-four of two hundred three
> candidate compact cancer laws. That is the product."

15 words / ~6 s at 140 WPM. Replaces the 22-word "Most AI-for-Science"
hook. Gains 3 s of budget.

## Recording mechanics (Loom)

Unchanged from `loom_narration_verbatim.md §Recording mechanics`:

- 1080p, 30 fps, single take preferred.
- Title: `Theory Copilot — verification-first biological law discovery`
- Description: one-line pitch from `docs/submission_form_draft.md`
  + GitHub URL.
- Trim leading/trailing silence aggressively.
- Set link to **public** (no sign-in required to view).
- Paste share URL into `docs/submission_form_draft.md` Loom field.
