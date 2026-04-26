# Loom demo script — shot list (pre-narration planning)

> **Canonical narration lives in [`docs/loom_narration_final_90s.md`](loom_narration_final_90s.md)**
> (333 words, ~143–167 s at 120–140 WPM, eight segments including DIPG + IPF generalization tags).
> This file is the earlier 210-word shot-list / rehearsal asset — kept for
> screen-cue + timing reference. When the two diverge, the narration file wins.
> The Karpathy hook below is the *alternative* opener; the canonical final cut
> uses the biomedical-pain hook instead.

Target length (full cut): **~167 s (2:47) at 120 WPM · 143 s (2:23) at 140 WPM · well under 3-min hard cap.**
Tier-3 fallback (90 s target): drop DIPG + IPF segments → ≤210 words.
Voice: one take, first-person, no B-roll, plain walkthrough.
Screen: single 1920 × 1080 terminal + browser split, no fancy overlays.

## Shot list (timing + screen content + spoken)

### 0 : 00 – 0 : 10 — Hook

**Screen:** `results/RESULTS.md` open at the top in editor.
**Narration (≈ 30 words):**

> "Karpathy's autoresearch — 700 experiments, no humans, training loss
> as judge — but in biology the judge has to be the data. A loop that
> cannot reject is not a loop. Here's what the biology version looks
> like."

### 0 : 10 – 0 : 25 — The setup

**Screen:** `config/law_proposals.json` → scroll to KIRC entries.
**Narration (≈ 40 words):**

> "Opus 4.7 proposes seven compact law families for ccRCC, including
> two negative controls it expects to fail. A five-test statistical
> gate — permutation, bootstrap, baseline, confound, decoy — runs in
> plain Python. Opus cannot rationalise its own laws into passing."

### 0 : 25 – 0 : 45 — The reject cycle

**Screen:** `results/track_a_task_landscape/SUMMARY.md` scrolled to
the 4-task matrix (gene-name equations, explicit rejection rationale)
— followed by a brief `jq` peek at
`results/flagship_run/falsification_report.json` (positional vars
from the first pass — useful to show the raw output the gate rejected,
but keep the spoken focus on the SUMMARY's gene-named rationale). **Do
not linger on the raw JSON; the SUMMARY is the narrative anchor.**
**Narration (≈ 52 words):**

> "On real TCGA-KIRC, the gate rejects 100-plus candidates across
> four tasks. Even the textbook HIF-axis law that Opus itself
> proposed — `log1p(CA9) plus log1p(VEGFA) minus log1p(AGXT)` —
> fails, because CA9 alone already reaches AUROC 0.965 and a
> compound needs plus 0.05 incremental. The gate catches its own
> side."

### 0 : 45 – 1 : 10 — The accept cycle

**Screen:** `results/overhang/sr_loop_run.json` (H1 v2 — survivors in
gene-name form: `TOP2A − EPAS1` variants, `(EPAS1 + SLC22A8)` member
visible), then full-screen
`results/track_a_task_landscape/plots/survivor_scatter_top2a_vs_epas1.png`.
**Avoid** `metastasis_expanded/falsification_report.json` —
earlier-pass PySR with positional variables (`x4`, `x31`) that do not
read aloud as TOP2A/EPAS1; the narrative anchor is the H1 v2 result
which uses gene names natively.
**Narration (≈ 62 words):**

> "Then we expand the panel from 11 to 45 genes. Same gate. Same
> thresholds. Nine of thirty candidates pass on metastasis. The
> simplest — `TOP2A minus EPAS1` — says: when a tumour's
> proliferation program runs ahead of its HIF-2α program, it's more
> likely to be metastatic. That's the published ccA-vs-ccB subtype
> axis. PySR re-derived it from scratch. The gate accepted it."

### 1 : 10 – 1 : 25 — Cross-cohort replay + the own-output kill

**Screen (0:10 split):** Kaplan–Meier curve from
`results/track_a_task_landscape/external_replay/immotion150_pfs/km_median_split.png`
(red vs blue, 7.5-month gap), then cut to the PhL-1 verdict at
`results/track_a_task_landscape/external_replay/immotion150_slc22a8/verdict.json`
with `"verdict": "FAIL"` visible, plus **Slide 2 — Headline findings**
overlay.
**Narration (≈ 40 words):**

> "Cross-cohort replay on IMmotion150, the Phase-2 immunotherapy
> trial: same equation, different cohort, HR 1.36, log-rank p=0.0003,
> seven-and-a-half-month PFS gap. Then our own H1 LLM-SR loop proposed
> a 3-gene extension. Same gate. On independent data. Killed it."

### 1 : 25 – 1 : 30 — The close

**Screen:** single terminal with `make audit` → `OK`, then git log
one line: `TOP2A - EPAS1`. (Alternate option: Slide 3 — Opus
overhang pathway evolution.)
**Narration (≈ 22 words):**

> "Six experiments once, not one experiment six times — because laws
> that survive only one kind of test aren't laws. That's the gate.
> That's the point."

### ALTERNATIVE close — PhL-3/PhL-4 Memory + persist-replay (trade off: cuts 2s from 1:10-1:25 IMmotion beat to make room)

If the rehearsal clock shows ~3s of slack, use this variant instead.
It surfaces the two 2026-04-23-shipped durability primitives (Memory
public beta integrated day-of; event-log persist+replay as working
code) which are the strongest "Best Managed Agents" signal the repo
carries.

**Screen (1:20-1:30):** `results/live_evidence/phl3_memory_smoke/SUMMARY.md`
scrolled past the "server-side verification" section (shows 2 memory
entries appended across sessions), then cut to `make audit` → `OK`.
**Narration (≈ 25 words):**

> "And the Skeptic writes every rejection pattern to a memory store
> that persists across sessions — public beta shipped the day of
> this submission, integrated day-of. Six experiments once."

## Total

- Narration: ~ 210 spoken words / 90 seconds at ~140 WPM
- Screens: 6 cuts, all local files, no browser sign-in required
- No patient data, no institutional identifiers (`make audit`
  confirms the repo is clean before recording)

## Backup GIF fallback (if Loom upload fails on 4/26)

1. A 6-second GIF of the terminal running `make demo-kirc` and
   printing the survivor row, looped 4x.
2. Embedded in README.md under the "Read first" section with a
   `[demo_gif]` caption.
3. The full static walkthrough in `docs/demo_walkthrough.md` remains
   the long-form reference.

## Rehearsal checklist

Walked end-to-end 2026-04-23 (Fri-5). All 8 screen assets verified
present on disk; all reshoot gotchas listed below.

- [x] `make audit` passes before rolling camera (confirmed clean post
      PhL-4 sanitize, 2026-04-23 21:xx ET).
- [x] `results/RESULTS.md` first paragraph reads as hook-able (gene
      names + pre-registered gate framing in opening).
- [x] `results/track_a_task_landscape/SUMMARY.md` 4-task matrix uses
      **gene names** (CA9, CUBN, MKI67, TOP2A, EPAS1). Use THIS as
      the reject-cycle anchor, NOT the raw
      `flagship_run/falsification_report.json` which still has
      positional `x4/x31` variables from an earlier PySR pass.
- [x] `results/overhang/sr_loop_run.json` H1-v2 survivors ARE in
      gene-name form (`TOP2A − EPAS1` variants). Use THIS for the
      accept-cycle anchor, NOT `metastasis_expanded/falsification_report.json`
      (positional vars).
- [x] `survivor_scatter_top2a_vs_epas1.png` is 1050×825 (displays
      cleanly inside a 1920×1080 frame; some margin around it — fine).
- [x] `immotion150_pfs/km_median_split.png` is 900×675 — same frame
      sizing as the scatter; both look OK at ~90% Loom crop.
- [x] `immotion150_slc22a8/verdict.json` `"verdict": "FAIL"` +
      `"score_formula": "TOP2A - (EPAS1 + SLC22A8)"` are both visible
      at the top of the file without scrolling.
- [x] `results/live_evidence/phl3_memory_smoke/SUMMARY.md` scrolls
      past "server-side verification" cleanly (for the alternative
      close).
      1920 × 1080
- [ ] Narration cleared for institutional references (only "TCGA-KIRC",
      "GSE40435", "PySR", "Opus 4.7", "Managed Agents", "ccA",
      "ccB")
- [ ] Clock check: script rehearsed under 90 s without cutting
