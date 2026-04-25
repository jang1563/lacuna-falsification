# Loom recording — single-page cheatsheet

Print this. Tape it next to your monitor. Single source of truth at
recording time. Full script in `docs/loom_narration_final_90s.md`,
visual cues in `docs/loom_visual_cue_map.md` — but at the moment of
recording you only need this page.

---

## Plan: Option A (KIRC + DIPG + IPF, all 8 segments)

**Target**: 333 words / 2:23 at 140 WPM / 2:47 at 120 WPM (3-min hard
cap with 13–37 s margin).

**Segments**: Hook → Architecture → Rejection → Survivor → Validation
+ kill → Routine + close → DIPG → IPF.

**2-take strategy** (recommended):
1. **Take 1 = Option A (full)**. If IPF segment lands clean → use Take 1.
2. **Take 2 = Option C fallback** (drop IPF segment, 265w / 2:14)
   only if Take 1 stumbled repeatedly on IPF lines. Form retains IPF
   evidence as written text regardless of which take you ship.

Don't over-take. 2 attempts is enough; 5+ takes degrades performance.

---

## Pronunciation aids (the things that trip people up)

| Term | Say |
|---|---|
| TOP2A | "top-two-A" |
| EPAS1 | "EE-pass-one" |
| ccRCC | "see-see-R-C-C" |
| ccA / ccB | "see-see-A vs see-see-B" |
| IMmotion150 | "Im-motion one-fifty" |
| RAINIER | **"RAY-near"** (NOT "rain-ee-er") |
| Raghu 2017 | **"RAH-goo twenty-seventeen"** |
| LOXL2 | **"L-O-X-L-two"** (spelled out) |
| IPF | **"I-P-F"** (spelled out, NOT "ipf" as a word) |
| D+Q | "dee-plus-cue" |
| periostin | "PEH-ree-ah-stin" |
| H3 K27M | "H-three K-twenty-seven-M" |
| PBTC-047 | "P-B-T-C zero-forty-seven" |
| 0.726 | "zero point seven-two-six" |
| 194 of 203 | "one hundred ninety-four of two hundred three" |
| 0.0003 | "zero point zero-zero-zero-three" |
| 1.36 | "one point three-six" |

`…` = ~300 ms pause. `[breath]` = ~600 ms pause.

---

## IPF segment (densest 30 s — practice 2-3× before Take 1)

**Cut**: Pane G = `results/external_validation_ipf/RESULTS.md` verdict
row (1/0/4) visible. Pane H = Skeptic JSON `confounds_flagged` field.

Verbatim:

> "And one more — same engine, adult lung. Idiopathic pulmonary
> fibrosis. Five rescue candidates. Thirty-two minutes. Fifty-eight
> dollars. **[breath]** One survives. Four rejected. But here's the
> moment that matters: the Skeptic role caught two Advocate claims
> that prior trials *never* tested a stratifier — both empirically
> false. **RAY-near** pre-specified periostin. **RAH-goo
> twenty-seventeen** pre-specified **L-O-X-L-two** co-primaries.
> **The engine catches its own near-misses because the roles don't
> share context.** Adversarial review at runtime."

**Three landmines**:
1. "RAY-near" — say it once correctly the first time, the rest follows.
2. "RAH-goo twenty-seventeen pre-specified L-O-X-L-two co-primaries" —
   the longest unbroken phrase. Try once: *RAH-goo / twenty-seventeen /
   pre-specified / L-O-X-L-two / co-primaries.* Five beats.
3. The closing line — *"because the roles don't share context"* — is
   the punch line. Slow down 10% on it. Don't rush into "Adversarial
   review at runtime."

If you stumble twice on RAY-near or RAH-goo, drop the segment (Option
C fallback). Don't fight it past 2 stumbles.

---

## Pre-flight: what to have open before camera rolls

**3-pane layout** (recommended):

**Pane A** (editor, left):
- `results/RESULTS.md` (Hook segment)
- `results/track_a_task_landscape/survivor_robustness/INTERPRETATION_top2a_epas1.md` (Survivor segment)
- `results/external_validation_dipg/RESULTS.md` (DIPG segment)
- `results/external_validation_ipf/RESULTS.md` (IPF segment, Pane G)
- `results/flagship_run/falsification_report.json` (Rejection segment)
- `results/external_validation_ipf/top_lead_DandQ_telomere_short/05_DandQ_telomere_short_IPF.skeptic.json` (IPF segment, Pane H — `confounds_flagged` scrolled into view)

**Pane B** (image viewer / browser, center):
- `results/track_a_task_landscape/plots/survivor_scatter_top2a_vs_epas1.png`
- `results/track_a_task_landscape/plots/task_auroc_comparison.png`
- `results/track_a_task_landscape/external_replay/immotion150_pfs/km_median_split.png`
- `results/track_a_task_landscape/external_replay/immotion150_slc22a8/km_median_split.png` (PhL-1 kill segment)
- Incognito browser on https://claude.ai/code/session_01NyS541H3qZfJgqFVgWDcoM (Routine segment)

**Pane C** (terminal, right):
- repo root, `make audit` typed but not pressed (Routine segment last 2 s)

---

## Architecture diagram (0:10–0:25 segment) — fallback decision

`docs/architecture.png` does NOT exist. Two options:

- **A. Use ASCII fallback**: scroll Pane A to `CLAUDE.md` execution-flow
  block (lines ~83-90). Reads cleanly on screen, no slide needed.
- **B. Skip image, narration carries the architecture verbally**: keep
  Pane A on `results/RESULTS.md` (Hook image) for an extra 15 s; the
  voice describes the architecture without a corresponding visual.

Both options are honest. Pick A if scrolling is smooth; pick B if
scrolling distracts. Don't try to make a slide at recording time.

---

## Recording mechanics

- 1080p, 30 fps, single take preferred per attempt.
- Loom title: `Theory Copilot — verification-first biological law discovery`.
- Description: paste the one-line pitch + GitHub URL.
- Trim leading silence aggressively (≤ 1 s).
- Trim trailing silence aggressively (no dead space after "Adversarial
  review at runtime.").
- Set link **public** (no sign-in required to view).
- Paste share URL into `docs/submission_form_draft.md` Demo video field
  AND the live submission form on 2026-04-26 evening.

---

## Honest-framing triggers (do NOT deviate)

If you find yourself about to say any of these, **stop and re-read**:

- ❌ "194 of 204" → ✅ "194 of 203"
- ❌ "10 survivors" → ✅ "9 survived"
- ❌ "novel kidney cancer biology" → ✅ rediscovery / ccA-vs-ccB axis
- ❌ "novel discovery" anywhere → use *rediscovery* or *empirical regularity*
- ❌ "Sonnet works just as well" → cite the 0/60 vs 10/60 ablation
- ❌ "the engine caught fabrications" alone → ✅ "the **Skeptic role** caught two **Advocate** claims" (role-separation is the load-bearing claim)
- ❌ "always" / "never" causal claims → ✅ caveat with "in this run" / "for this task"

Stumble on any of these → stop the take, re-read this section, restart.

---

## After recording — checklist

1. Watch Loom playback once at 1× speed. If anything mispronounced
   beyond clarity, retake.
2. Trim silence at both ends.
3. Set to public.
4. Copy share URL.
5. Paste URL into `docs/submission_form_draft.md` Demo video field.
6. Commit message: `[N] Loom URL embed`. Push.
7. On 2026-04-26 evening, paste the same URL into the live submission
   form Demo video field.
8. Done. Submit.

---

## If something goes catastrophically wrong

The submission still works without a perfect Loom. Form's written
description (176-word unified summary) carries the same evidence:
KIRC 194/203 + IPF dual-fabrication catch + DIPG 7/15. GitHub repo
contains all reproducible artifacts. **A 2:30 Loom that lands the
KIRC + DIPG core cleanly, even if IPF is dropped, is a stronger
submission than a 2:47 Loom with stumbles.** Ship the cleaner take.
