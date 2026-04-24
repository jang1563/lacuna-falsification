# Loom narration — final 90-second cut (≤ 180 words at 140 WPM)

**Status:** submission-locked final script.
**Target:** 90 seconds end-to-end; budget 120 s hard cap.
**Word count:** 178 words / ~76 s at 140 WPM / ~89 s at 120 WPM (natural pace).
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

> "Expand the panel from eleven to forty-five genes. Same gate, same
> thresholds. Nine candidates pass on metastasis. The simplest —
> [breath] top-two-A minus EE-pass-one — says: when a tumour's
> proliferation program runs ahead of its HIF-two-alpha program, it's
> more likely to be metastatic. That's the published see-see-A vs
> see-see-B subtype axis. PySR re-derived it from scratch."

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

---

## Word-count ledger

| Segment | Words | Cumul | Time @ 140 WPM | Time @ 120 WPM |
|---|---|---|---|---|
| 0:00-0:10 Hook | 22 | 22 | 9 s | 11 s |
| 0:10-0:25 Architecture | 30 | 52 | 13 s | 15 s |
| 0:25-0:45 Rejection | 38 | 90 | 16 s | 19 s |
| 0:45-1:05 Survivor | 36 | 126 | 15 s | 18 s |
| 1:05-1:20 Validation + kill | 34 | 160 | 15 s | 17 s |
| 1:20-1:30 Close | 18 | 178 | 8 s | 9 s |
| **TOTAL** | **178** | — | **~76 s** | **~89 s** |

Budget: 90 s target, 120 s hard cap. At 140 WPM the script runs 76 s
(room for B-roll cuts). At 120 WPM (slower, more authoritative pace)
it runs 89 s — still under the 90 s target.

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
