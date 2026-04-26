# Loom narration — verbatim recording script

**Purpose**: word-for-word script user reads on Sat to eliminate ad-lib
risk. Companion to `docs/loom_script.md` (shot-list framing). This file
is the spoken text only, with timing markers + breath / cue marks.

**Target**: 90 s total · ≤ 210 words · 140 WPM (avg).

**Style notes**:
- Read steady, not fast. 140 WPM = comfortable lecture pace.
- Pauses written as `…` (≈300 ms) and `[breath]` (≈600 ms).
- Numbers spoken plainly: "0.726" → "zero point seven-two-six";
  "194" → "one hundred ninety-four"; "TOP2A" → "top-two-A".
- "cc-A" / "cc-B" → "see-see-A" / "see-see-B".
- Two pronunciation aids inline: "EPAS1" = "EE-pass-one";
  "ccRCC" = "see-see-R-C-C".

---

## Pre-flight (before camera rolls)

In a clean terminal, with browser tab open to `loom.com/new`:

```bash
cd ~/path/to/lacuna-falsification
make audit          # confirm OK before recording
git rev-parse HEAD  # note current SHA for the commit caption
```

Open these tabs / panes ahead of time so cuts are instant:

1. **Editor pane A** — `results/RESULTS.md` open, scrolled to top
2. **Editor pane B** — `results/track_a_task_landscape/SUMMARY.md`
   scrolled to the 4-task matrix
3. **Editor pane C** — `results/overhang/sr_loop_run.json` collapsed
   to show `"survivors":` array
4. **Image viewer A** — `results/track_a_task_landscape/plots/survivor_scatter_top2a_vs_epas1.png`
   (1050×825) full-screen
5. **Image viewer B** — `results/track_a_task_landscape/external_replay/immotion150_pfs/km_median_split.png`
   (900×675) full-screen
6. **Editor pane D** — `results/track_a_task_landscape/external_replay/immotion150_slc22a8/verdict.json`
   scrolled so `"verdict": "FAIL"` and
   `"score_formula": "TOP2A - (EPAS1 + SLC22A8)"` are both visible
7. **Slide window 1** — Architecture (Claude Design slide 1 PNG, full-screen)
8. **Slide window 2** — Headline findings (Claude Design slide 2 PNG)
9. **Terminal pane** — empty `bash` prompt with cursor visible,
   ready for `make audit` typing

---

## Verbatim narration (DEFAULT close — "six experiments once")

### 0:00 – 0:10 (Hook · 30 words)

**Cue: editor pane A — `results/RESULTS.md` open at top.**

> "Karpathy's autoresearch [breath] seven hundred experiments,
> no humans, training loss as judge. … But in biology, the judge has
> to be the data. A loop that cannot reject … is not a loop. Here's
> what the biology version looks like."

### 0:10 – 0:25 (Setup · 40 words)

**Cut to slide window 1 — Architecture diagram.**

> "Opus four-point-seven proposes seven compact law families for
> see-see-R-C-C, including two negative controls it expects to fail.
> A five-test statistical gate — permutation, bootstrap, baseline,
> confound, decoy — runs in plain Python. [breath] Opus cannot
> rationalise its own laws into passing."

### 0:25 – 0:45 (The reject cycle · 52 words)

**Cut to editor pane B — Track A SUMMARY 4-task matrix.**

> "On real T-C-G-A kidney clear cell, the gate rejects one hundred
> ninety-four of two hundred three candidates across eleven
> task-by-panel combinations. … Even the textbook HIF-axis law that
> Opus itself proposed — log one plus C-A-9, plus log one plus
> V-E-G-F-A, minus log one plus A-G-X-T — fails. [breath] C-A-9
> alone already reaches A-U-R-O-C zero point nine-six-five. The gate
> catches its own side."

### 0:45 – 1:10 (The accept cycle · 62 words)

**Cut to editor pane C — `sr_loop_run.json` survivors array,
then full-screen image viewer A — survivor_scatter PNG.**

> "Then we expand the panel from eleven to forty-five genes. Same
> gate. Same thresholds. … Nine of thirty candidates pass on
> metastasis. The simplest — top-two-A minus EE-pass-one — says:
> [breath] when a tumour's proliferation program runs ahead of its
> HIF-two-alpha program, it's more likely to be metastatic. That's
> the published see-see-A versus see-see-B subtype axis. PySR
> re-derived it from scratch. The gate accepted it."

### 1:10 – 1:25 (Cross-cohort + own-output kill · 40 words)

**Cut to image viewer B — IMmotion150 KM curve, then editor pane D
— PhL-1 verdict JSON FAIL line, then slide window 2 — Headline
findings overlay.**

> "Cross-cohort replay on Im-motion one-fifty, the Phase-2
> immunotherapy trial: same equation, different cohort, hazard
> ratio one point three-six. … Then our own H-one LLM-S-R loop
> proposed a three-gene extension. Same gate. On independent data.
> [breath] Killed it."

### 1:25 – 1:30 (Close · 22 words)

**Cut to terminal pane. Type `make audit` slowly. Output prints `OK`.
Cursor sits on the OK line.**

> "Six experiments once, not one experiment six times — because laws
> that survive only one kind of test … aren't laws. That's the gate.
> That's the point."

---

## Verbatim narration (ALTERNATIVE close — Memory + persist+replay)

Use this variant if the rehearsal clock has 3+ seconds of slack and
you want to surface the 2026-04-23-shipped Memory primitive in the
90-second window. Trade-off: shave 2 s from the 1:10-1:25 IMmotion
beat by speaking it slightly faster.

### 1:25 – 1:30 (ALT close · 25 words)

**Cut to editor pane — `results/live_evidence/phl3_memory_smoke/SUMMARY.md`
scrolled to the "server-side verification" section (memory chain
visible), then `make audit` → `OK`.**

> "And the Skeptic writes every rejection pattern to a memory store
> that persists across sessions — public beta shipped the day of
> this submission, integrated day-of. [breath] Six experiments
> once."

---

## Word-count tally

| Segment | Words | Cumulative | Time @ 140 WPM |
|---|---|---|---|
| 0:00-0:10 Hook | 30 | 30 | 13 s |
| 0:10-0:25 Setup | 40 | 70 | 17 s |
| 0:25-0:45 Reject | 52 | 122 | 22 s |
| 0:45-1:10 Accept | 62 | 184 | 27 s |
| 1:10-1:25 Cross-cohort | 40 | 224 | 17 s |
| 1:25-1:30 Close (default) | 22 | 246 | 9 s |
| **TOTAL (default)** | **246** | — | **105 s** |

Over the 210-word budget by 36 words / 90 s budget by 15 s. Two
options to fix at recording time:
- Speak at 165 WPM in the 0:25-1:25 segment (still fluent)
- Cut breath markers in 0:45-1:10 (the densest accept-cycle beat)

If using the ALTERNATIVE close instead of the default close: total
words = 249, total time @ 140 WPM = 107 s. Same compression strategy.

---

## Terminal command pre-script (for the close)

The 1:25 close shows live `make audit`. Pre-script:

```bash
# In the terminal pane, CLEAR the prompt before recording:
clear

# When the cue hits 1:25, slowly type (do not paste):
make audit
# Wait for output. Should print:
# >>> Scanning tracked files for sensitive strings...
# >>> OK — no sensitive strings in tracked files (binary assets excluded).

# Optional: if there's a 1-2s gap, also type:
git log --oneline -1
# Should print the latest commit SHA + subject
```

If `make audit` fails at recording time: STOP, fix the leak, re-run
the entire take from 0:00.

---

## Voice direction (one paragraph)

Speak in a quiet, declarative tone. Not pitching, not selling.
Like a postdoc presenting a method paper at a 30-person workshop.
The story is "here is what the gate did, here is what it accepted,
here is what it rejected." The line *"That's the gate. That's the
point."* lands harder if you read it slower than the rest, with a
breath before "That's the gate."

Pronunciation aids:
- **TOP2A**: "top-two-A" (not "top-twenty-A")
- **EPAS1**: "EE-pass-one" (or "epaz-one"; pick one and be consistent)
- **ccRCC**: "see-see-R-C-C"
- **ccA / ccB subtype**: "see-see-A / see-see-B subtype"
- **AUROC**: "ay-you-rock" (one word, common ML pronunciation)
- **MIcromotion150 → IMmotion150**: "Im-motion one-fifty"
- **HIF-2α**: "hif-two-alpha"
- **SLC22A8**: "S-L-C-twenty-two-A-eight" (only spoken if using
  the alternative close that mentions the H1 extension)

---

## Recording mechanics (Loom-specific)

1. Loom → New recording → Screen + cam (cam optional; default off
   keeps focus on screen)
2. 1080p, 30 fps
3. **Single take preferred**. Don't pause-and-resume — Loom's pause
   is fine for breaks but a clean single take of 90 s reads better
   than a stitched take.
4. After recording, in Loom UI:
   - Title: "Lacuna — falsification-first biological law discovery"
   - Description: paste the one-line pitch from
     `docs/submission_form_draft.md` plus the GitHub URL
   - Trim leading/trailing silence aggressively (target: video
     starts within 1 s of the spoken hook)
5. Set link to **public** (no sign-in required to view)
6. Copy share URL → paste into `docs/submission_form_draft.md` Loom
   field

---

## Backup take strategies

If the first take exceeds 95 s: do a second take. The script is
within 5 % of budget, so a faster second pass should land.

If the spoken hook stumbles (Karpathy line is the hardest): rewrite
the hook to:

> "Most A-I-for-Science loops automate confirmation bias. This one
> rejects one hundred ninety-four of its two hundred three
> candidates. Here's how."

That's a 25-word backup hook (8 s vs the original 13 s) that buys
budget for the rest of the script.

---

## Final pre-record checklist

- [ ] `make audit` clean (no leaked patterns)
- [ ] Microphone tested (no compression artefacts, no fan noise)
- [ ] All 9 tabs/panes pre-loaded (see Pre-flight section above)
- [ ] Browser tab strips hidden (no email previews / GitHub usernames
      visible)
- [ ] Terminal pane prompt clean (no `~/.local/...` or
      `(.venv) <username>@<host>` visible — use `PS1="$ "` if
      needed)
- [ ] Loom set to 1080p
- [ ] One full silent rehearsal under 95 s before camera rolls
