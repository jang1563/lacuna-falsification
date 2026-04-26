# Loom narration — final cut (includes DIPG + IPF generalization tags)

**Status:** submission-locked final script (updated 2026-04-25 post-IPF-run; DIPG generalization tag added 2026-04-24; hook refined 2026-04-24 per Session 3 video advice).
**Target:** ≤ 180 seconds (3-min hard cap per official rules); 2:30 acceptable; 120 s soft cap formally exceeded by IPF segment but well under hard cap.
**Word count:** 333 words / ~143 s (2:23) at 140 WPM / ~167 s (2:47) at 120 WPM (see ledger below for per-segment breakdown).
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
- "RAINIER" = "RAY-near"; "Raghu twenty-seventeen" = "RAH-goo
  twenty-seventeen"; "L-O-X-L-two" spelled out; "I-P-F" spelled out;
  "D-plus-Q" = "dee-plus-cue"; "periostin" = "PEH-ree-ah-stin".

---

## 0:00 – 0:10 — Hook (21 words)

**Cue: editor pane A — `results/RESULTS.md` open at top.**

> "AI-for-science tools help you confirm almost anything.
> This one was built to say no. … One hundred ninety-four rejected.
> Nine survived."

## 0:10 – 0:25 — Architecture (30 words)

**Cut to slide 1 — Architecture diagram.**

> "Opus four-point-seven proposes seven compact law families for
> kidney cancer, including a housekeeping negative control. A
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
> thirty-four. Our symbolic regression rediscovered it unprompted."

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

## 1:30 – 2:05 — DIPG generalization (~71 words, ~30 s)

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
> failure, score thirteen of fifteen. [breath] Same engine, separate
> substrate gate on real P-B-T-A cohort: zero of four passed —
> falsification working. Same rejection-as-product pattern across
> diseases."

## 2:05 – 2:35 — IPF dual-fabrication catch (~68 words, ~29 s)

**Cut to editor pane G — `results/external_validation_ipf/RESULTS.md`
verdict distribution row visible (1 RESCUE_SUPPORTED / 0 MIXED /
4 INSUFFICIENT_EVIDENCE), mirrored from `dipg_rescue/` Run #1 commit
`3af3a67`, lock SHA `88eaca3`; then pane H — Skeptic JSON for one of
the two fabrication-catches (e.g. `results/external_validation_ipf/top_lead_DandQ_telomere_short/05_DandQ_telomere_short_IPF.skeptic.json`
or the parallel simtuzumab/tralokinumab Skeptic outputs) with
`kill_attempts` field showing the empirically-false advocate claim
caught by Skeptic.**

> "And one more — same engine, adult lung. Idiopathic pulmonary
> fibrosis. Five rescue candidates. Thirty-two minutes. Fifty-eight
> dollars. [breath] One survives. Four rejected. But here's the moment
> that matters: the Skeptic role caught two Advocate claims that prior
> trials *never* tested a stratifier — both empirically false. RAY-near
> pre-specified periostin. RAH-goo twenty-seventeen pre-specified
> L-O-X-L-two co-primaries. **The engine catches its own near-misses
> because the roles don't share context.** Adversarial review at runtime."

---

## Word-count ledger

| Segment | Words | Cumul | Time @ 140 WPM | Time @ 120 WPM |
|---|---|---|---|---|
| 0:00-0:10 Hook | 21 | 21 | 9 s | 11 s |
| 0:10-0:25 Architecture | 31 | 52 | 13 s | 16 s |
| 0:25-0:45 Rejection | 38 | 90 | 16 s | 19 s |
| 0:45-1:07 Survivor (with citation emphasis) | 52 | 142 | 22 s | 26 s |
| 1:07-1:22 Validation + kill | 34 | 176 | 15 s | 17 s |
| 1:22-1:30 Routine + close | 18 | 194 | 8 s | 9 s |
| 1:30-2:05 DIPG + Tier-1 substrate | 71 | 265 | 30 s | 36 s |
| **2:05-2:35 IPF dual-fab catch (NEW 2026-04-25)** | **68** | **333** | **29 s** | **34 s** |
| **TOTAL** | **333** | — | **~143 s (2:23)** | **~167 s (2:47)** |

Budget (post-IPF-tag): 180 s hard cap. At 140 WPM the full cut runs
143 s — 37 s under hard cap. At 120 WPM (slower, authoritative pace)
it runs 167 s — 13 s under hard cap. **The 120 s soft cap is now
formally exceeded** (~23-47 s over) but the 180 s hard cap is the
binding constraint per official rules; staying under 180 s is the
contract.

**Budget controls at recording time** (in order from least to most
narrative cost):
- **Tier 1 (5 words / 2 s saved):** drop the "Brannon twenty-ten,
  ClearCode thirty-four" citation line from the survivor segment.
  Citation lives in `docs/survivor_narrative.md §Prior art` for
  pause-viewers. Use this if a slow-pace take pushes runtime to
  ~3:00.
- **Tier 2 (drop IPF segment, 68 words / 29 s saved):** revert to
  pre-IPF 265-word / ~114-133 s narration. Use this if (a) the IPF
  segment stumbles 3+ times in a row, (b) the recording exceeds
  3:00, or (c) any audit-pattern concern arises with the IPF mirror
  at recording time. Back to "DIPG generalization is the closing
  tag." Submission form retains the IPF mention as written-text
  evidence.
- **Tier 3 (90-s target, drop both DIPG + IPF tags, 139 words /
  59 s saved):** revert to pre-generalization 194-word / 83 s
  narration. Only used if hard-cap risk emerges or the user
  intentionally targets a 90-s pitch. Back to "rejection-as-product
  is the closing tag."

## Pre-flight (before camera rolls)

Same 9-pane layout as `loom_narration_verbatim.md §Pre-flight`, plus
two additional editor panes for the IPF generalization tag. The
differences for this cut:

- **Slide 1** is the Architecture diagram (required).
- **No Karpathy screenshot** — the hook is the pipe-shaped "rejection
  celebrates first" line, no citation frame.
- **Browser tab** pre-loaded to the PhL-8 `claude.ai/code/session_...`
  URL in an incognito window so the Routine-session screenshot is clean.
- **Pane G (NEW for IPF)**: editor open at
  `results/external_validation_ipf/RESULTS.md` — verdict distribution
  row visible (1 SUPPORTED / 0 MIXED / 4 INSUFFICIENT_EVIDENCE).
- **Pane H (NEW for IPF)**: editor open at one of the two Skeptic
  fabrication-catch JSONs in
  `results/external_validation_ipf/top_lead_DandQ_telomere_short/`
  (or, for the actual Skeptic-vs-Advocate fabrication-catch surface,
  the per-candidate Skeptic JSONs from candidates 03 and 04 — these
  live in `dipg_rescue/runs/2026-04-25_ipf_run01/` privately; for
  the Loom, the public mirror's Skeptic JSON for candidate 05 with
  `confounds_flagged` showing Nambiar 2023 omission is acceptable).

## Honest-framing triggers (do NOT deviate at recording time)

Pulled from `docs/CLAIM_LOCK.md`:

- Never say "same gate on IMmotion150" alone — always add "separately
  pre-registered survival replay" or equivalent.
- Never say "full five-test pass" without the `delta_confound = null`
  caveat — "nine candidates pass" is correct; "pass the full five-test"
  is not.
- Never say "novel kidney cancer biology" — this is rediscovery.
- Never say "194 of 204" — it is 194 of 203.

**IPF segment specific (added 2026-04-25):**
- Never say "engine caught Advocate fabrications" alone — always say
  "**Skeptic role** caught" (the role-separation is the load-bearing
  claim; "engine caught" hides the architectural primitive).
- Never say "RAINIER and Raghu twenty-seventeen had errors" — say
  "the Advocate's *claims about* RAINIER and Raghu twenty-seventeen
  were empirically false" (the trials are fine; the engine's Advocate
  fabricated about them).
- Never say "IPF rescue confirmed" or "D-plus-Q is effective" — the
  one survivor is "with engine-flagged caveats" or simply "one
  survives" without elaboration in the Loom.
- Never name "Nambiar twenty-twenty-three" or "dbGaP" in the Loom —
  these are research-file details, not Loom material.

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
- Title: `Lacuna — falsification-first biological law discovery`
- Description: one-line pitch from `docs/submission_form_draft.md`
  + GitHub URL.
- Trim leading/trailing silence aggressively.
- Set link to **public** (no sign-in required to view).
- Paste share URL into `docs/submission_form_draft.md` Loom field.
