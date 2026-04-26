# Submission Form Draft

## ⚡ Final submission checklist (fill at form open time)

- [ ] Open the submission form: https://cerebralvalley.ai/e/built-with-4-7-hackathon/hackathon/submit
- [ ] Paste final Loom / YouTube / Google Drive URL into the submission form's "Demo video" field; hard cap is **3:00**, and shorter is allowed.
- [ ] Select problem statement: **"Build From What You Know"**
- [ ] Select prize category (if field exists): **"Best Use of Claude Managed Agents"**
- [ ] Copy unified 200-word summary below into the description field
- [ ] Verify repo is public for review: `https://github.com/jang1563/lacuna-falsification` (can be made private after the event)
- [ ] Verify click-through demo does not require judges to enter their own Anthropic API key
- [ ] If the video uses free/stock assets, mention the source/license in README when linking the video; avoid unlicensed copyrighted assets/fonts
- [ ] Submit before **2026-04-26 20:00 ET**

---

**Verified 2026-04-24** against the official Cerebral Valley × Anthropic
[Built with Opus 4.7 participant resources page](https://cerebralvalley.ai/e/built-with-4-7-hackathon/details).
**Updated 2026-04-26 from Discord announcements / mod answers.**
**Submission form URL saved 2026-04-26**:
https://cerebralvalley.ai/e/built-with-4-7-hackathon/hackathon/submit
Per official rules, the actual submission requires **only three items**:

| Required item | Cap |
|---|---|
| Demo video link (YouTube / Loom / Google Drive) | **3 minute maximum; shorter is fine** |
| Public GitHub repository | URL; public for review, may be private after event |
| Written description / summary | **100–200 words** |

Latest Discord clarifications:
- Submissions are due **2026-04-26 20:00 ET**.
- Demo video should show what was built and must not exceed 3 minutes.
- Judges should not need to enter their own Anthropic API key to test a click-through demo; set up a capped/limited demo environment if needed.
- Non-copyrighted / properly licensed stock or free assets are fine in the demo video. If the README includes the video link, mention the asset source/license there.
- Commercial fonts/assets should only be used when licensed / permitted; do not include copyrighted content without rights.

The actual submission form may include additional sub-fields (e.g.
prize-category select, problem-statement select, project name, team
info). The detailed sub-section drafts below (one-line pitch, Opus 4.7
usage, Managed Agents usage, prize-category justification) are
**inferred from the 4.6 hackathon precedent** and should be adapted at
submit time once the live form fields are visible:

| Inferred sub-section | Length cap (4.6 precedent) |
|---|---|
| Project name | 60 characters |
| One-line pitch | 140 characters |
| Project summary | 150 words |
| Claude Opus 4.7 usage | 150 words |
| Claude Managed Agents usage | 150 words |
| Prize category justification | 100 words |
| Team | name / role / contact |

**Problem statement alignment.** Per the official rules, two problem
statements are offered: *Build From What You Know* (domain expertise →
real-world workflow acceleration) and *Build For What's Next* (a
workflow that doesn't have a name yet). This submission targets
**Build From What You Know**: a biomedical postdoc's domain question
about confirmation bias in AI-for-Science → a verification harness
that any researcher can re-run on any disease CSV in 30 minutes.

**Judging criteria mapping** (Stage 1 async, 4/26-27, weights from
Discord update; Top 6 advance to final panel review on **2026-04-28
12:00 ET**):

| Criterion | Weight | Our load-bearing evidence |
|---|---|---|
| Impact (problem-statement fit, real-world potential) | 30% | **Platform generalization (2026-04-26, same gate + thresholds):** COAD (colon) 15/22 survivors (Δ+0.107 — highest of any run); LGG (brain glioma) 2/25 survivors (**AUROC 0.840** — TWIST1×MKI67 interaction term); LIHC (liver) 0/26 (designed negative, gate refuses correctly); KIRC (kidney) Stage 23/28 survivors. 7 disease contexts total. DIPG (pediatric brain cancer) generalization (7/15 Tier-2 supported, panobinostat-CED-MTX110 lead); Tier-1 prognostic-substrate gate on PBTA v15 (pediatric brain tumor atlas, n=192, 182 events) refuses to mint substrate-PASS on 0/4 — cross-disease falsification consistent with KIRC's 194/203 reject pattern; **IPF (lung fibrosis) Run #1 (2026-04-25): same engine, 1/5 SUPPORTED + 4 INSUFFICIENT, Skeptic caught two Advocate fabrications about prior trial design (RAINIER + Raghu 2017) — runtime demonstration of dual-role context isolation; $58, 32 min**; DatasetCard CLI = 30-min plug-in for any disease cohort |
| Demo (working, holds up live, cool to watch) | 25% | 3-minute Loom (current 2:23-2:47 cut with KIRC + DIPG + IPF tags), 24 reproducible plots, `make smoke` no-API health check + `make demo` guided Opus handoff, **2 live Routine session URLs** (PhL-8d `session_01CgsJYAP…` + PhL-10 `session_01XGse8X…`) |
| Opus 4.7 use (creative, beyond basic, surprises) | 25% | 180-call cross-model ablation (10/60 vs 0/60 PASS gap); **Opus 4.6 vs 4.7 ACR: 53.3%→66.7% (+13.3pp, G6)** — 4.7 PASS 10/10 clean survivors, NEEDS_MORE_TESTS 10/10 stress-test, zero over-commitment; **prospective meta-calibration (PhI-1): Opus wrote kill-tests for 4 skeletons before gate; 0/4 survived; all 4 predicted failures confirmed**; PhL-15 thinking-mode confound resolution; PhL-13 memorization audit (0/10 zero-shot retrieval); 1M-context cross-reasoning synthesis on full failure history |
| Depth & execution (push past first idea, real craft) | 20% | Self-killed our own H1 3-gene extension (PhL-1) on a separately pre-registered survival gate; ICP causal-invariance + anchor regression + Knockoffs + Westfall-Young + AUPRC stack; 107/107 current `make test` target + audit clean on package review; **IMmotion150 treatment-arm confound control: HR 1.361 (unadjusted) → 1.365 after controlling for immunotherapy vs VEGF-inhibitor arm — signal increases, confirming therapy-independence** |

---

## Project name (60 char)

```
Lacuna: Falsification-First Biological Law Discovery
```
(60 chars exactly.)

---

## One-line pitch (140 char)

```
AI for Science that says no: pre-registered gate rejects 194 of 203 cancer laws, Opus 4.7's own included. Survivor validates cross-cohort.
```
(139 chars.)

---

## Unified 100–200 word summary (official spec — single field)

The official rules require **one written description / summary
(100–200 words)**. Use this version if the live form has only a
single summary box. (Word count: ~189 space-split; cap 200. Technical
notation like `n=505` counts as 1 word in form counters, so the
space-split total is the authoritative count.)
**4-beat structure (what / problem / how-built / how-Claude) — trimmed 2026-04-26 to fit 200-word cap.**

```
Lacuna is a pre-registered falsification gate for biological law
discovery, built with Claude Code and Opus 4.7 Managed Agents. Opus
plays Proposer (emits law families + kill-tests before any fit),
Skeptic (reviews gate output in an isolated session — never the
Proposer's reasoning), and Interpreter (explains only survivors).

Existing AI-for-Science pipelines (Sakana AI Scientist, POPPER)
optimize for hypothesis generation, not rejection. The result:
automated confirmation bias.

A deterministic 5-test Python gate rejected 194 of 203 candidates
on TCGA kidney cancer data (n=505). The simplest survivor —
TOP2A − EPAS1 (proliferation vs hypoxia) — maps to the known
kidney-cancer growth-program axis. This is not a new discovery: it is
a methodology proof. The survivor passed a separately pre-registered
survival gate on IMmotion150 (a kidney cancer clinical trial;
HR=1.36, p=0.0003). Our own 3-gene extension? Killed by that same gate.

Claude Code Managed Agents hold the Skeptic stance without collapse
— Opus 4.7 10/60 PASS where Sonnet 4.6 = 0/60. IPF Run #1
(lung fibrosis, $58, 32 min): Skeptic caught two Advocate fabrications
about prior trial design. Same engine, 7 disease contexts: kidney
cancer, colon, brain glioma, liver (2 tasks), pancreatic cancer, pediatric glioma, lung fibrosis.
```

---

## Project summary (150 words, ~153 counted — trim if form rejects)

Lacuna is a pre-registered falsification discipline for biological
law discovery, built on Opus 4.7 Managed Agents. Opus plays
Proposer (emits compact law families + kill-test per family,
before any fit), Skeptic (reviews gate output in an isolated
session), and Interpreter (explains only what survived).

AI-for-Science tools accelerate hypothesis generation — not
rejection. The result: automated confirmation bias.

A deterministic 5-test Python gate rejected 194 of 203 candidates
on kidney cancer data (TCGA-KIRC, n=505). The survivor — `TOP2A − EPAS1` — is the
published kidney-cancer subtype axis (Brannon 2010), re-derived from
unconstrained symbolic regression. **This is not a new discovery:
it is a methodology proof.** A methodology that finds known truth
under a gate it cannot rationalize past proves it can find unknown
truth. The survivor passed a separately pre-registered survival gate
on IMmotion150 (a kidney cancer clinical trial; HR=1.36, p=0.0003);
our own 3-gene extension? Killed by that same survival gate. Claude Code
Routines run this discipline on every commit — pre-registration without being asked.

---

## Claude Opus 4.7 usage (~210 words — trim at form open if field has 150-word hard cap)

Four Opus 4.7 calls per loop with
`thinking={"type":"adaptive","display":"summarized"}` and
`output_config={"effort":"high"}`. (1) Proposer emits 3-5 compact law
families and the ex-ante skeptic test for each, before any fit. (2)
The test is executed by plain Python, not Opus. (3) Skeptic reviews
the specific metric pattern (`perm_p=0.049` is weaker than `0.001`;
`ci_lower=0.61` is marginal) and emits PASS / FAIL / NEEDS_MORE_TESTS.
(4) Interpreter writes the mechanism hypothesis and the "what this is
not" paragraph. **180-call cross-model ablation: Sonnet 4.6 = 0/60 PASS on gate-PASS candidates (full dissent collapse); Opus 4.7 = 10/60. Confound-resolved: Opus ran WITHOUT extended thinking (HTTP 400 on `enabled` type; retried base) vs Sonnet WITH extended thinking — Opus wins anyway. Gap is pre-training calibration, not thinking budget.**. **Memorization audit (PhL-13): 0/10 zero-shot retrieval of TOP2A−EPAS1 — rebuts
memorization concern.** **IPF Run #1 (2026-04-25): Skeptic caught
two Advocate fabrications about prior trial design — RAINIER + Raghu
2017 prespecified stratifiers Advocate claimed "never tested". Context
isolation working at runtime.** **1M-context synthesis + adversarial ablation (PhL-17) — Most Creative
+ Keep Thinking secondary prize candidates.** **Opus 4.6 vs 4.7 (60
calls each): abstention-calibration rate 53.3%→66.7% (+13.3pp); 4.7 PASS 10/10 on clean survivors, NEEDS_MORE_TESTS 10/10 on 5-gene stress-test (zero over-commitment vs 4.6's 20%) — gap is in graded abstention, not binary correctness. Prospective meta-calibration (PhI-1): Opus wrote kill-tests for 4 new skeletons before gate run; 0/4 survived; all 4 predicted failures confirmed (examples: VEGFA redundancy on #1, CCNB1 insufficiency on #4).**

---

## Claude Managed Agents usage (150 words, ~148 counted)

**Falsification discipline, not automated discovery.** Lacuna uses
three public-beta sessions (Proposer, Skeptic, Interpreter) with
structured-JSON handoff. The Skeptic never sees the Proposer's
reasoning tokens — context isolation is the load-bearing design
choice. Path B proves single-agent `agent_toolset_20260401`
end-to-end. Path A proves a sequential three-session chain on real kidney cancer
data (TCGA-KIRC; PhL-9v2: Skeptic quotes `delta_baseline=+0.0587`). Path
C proves Claude Code Routines as the **methodology persistence
layer**: `lacuna-scientific-oracle` receives an equation via API
trigger, autonomously runs `make venv` + `make audit` +
`falsification_sweep.py` (1000 perm/bootstrap, n=505), emits
structured PASS/FAIL verdict — pre-registered kill-tests firing
without being asked (PhL-8d: `session_01CgsJYAPdvhJJwTuBt7QZLZ`; PhL-10 stage: `session_01XGse8XYFtv3C1aKLZeMH9t` — static evidence in SUMMARY.md if URLs expire). Durability:
`persist_session_events` → `replay_session_from_log` (brain/body
decoupling). Memory stores accumulate rejection lessons cross-session.
IPF Run #1 ($58, 32 min): Skeptic caught two fabricated trial-design
claims — what a single-context harness cannot catch.

---

## Prize category justification (100 words, **106 counted** — ~6 over inferred cap; trim at paste time)

**Best use of Claude Managed Agents ($5K).** Public-beta-only Managed
Agents orchestration with isolated sessions: three live paths — B
(single-agent `agent_toolset_20260401`), A (PhL-9 sequential
three-session chain on real kidney cancer data, structured-JSON handoff), C
(PhL-8d metastasis FAIL+PASS `session_01CgsJYAP…`; PhL-10 stage FAIL+PASS `session_01XGse8X…` — 2 live sessions). Plus Memory public beta (integrated
2026-04-23 day-of): Skeptic writes rejection lessons; fresh sessions
read, quote, refine them; server-side persistence verified via raw
`/v1/memory_stores/*` API. Our own H1 LLM-SR extension was killed by
the separately pre-registered IMmotion150 survival replay (PhL-1).
**IPF Run #1: Skeptic caught two Advocate fabrications about RAINIER
+ Raghu 2017 — single-harness pipelines cannot catch this.**
Verification as working code.

---

## GitHub

```
https://github.com/jang1563/lacuna-falsification
```

Repo has been public since 2026-04-23 19:32 ET. Per Discord update,
public GitHub is required for review, but the repo may be made private
after the event.

---

## Demo video

```
Paste the final Loom / YouTube / Google Drive URL into the external submission form.
README links the interactive demo companion and discovery story for reviewers who click through from GitHub.
```

Discord constraints: upload to Loom, YouTube, or Google Drive; show
what was built; keep the video at or under **3:00**. A 1:37 video is
fine per mod answer as long as it does not exceed 3 minutes.

Canonical narration: `docs/loom_narration_final_90s.md` (333 words,
~143 s at 140 WPM / ~167 s at 120 WPM, **eight segments** incl. DIPG
+ IPF generalization tags, opens with problem-first "AI-for-science...
built to say no" hook and closes with the IPF dual-fabrication-catch
demonstration of 4-role context isolation). Shot-list / rehearsal
assets: `docs/loom_script.md` (pre-narration shot list) +
`docs/loom_visual_cue_map.md` (8-segment asset cue map).

---

## Broader Program Context (optional, 90 words, 89 counted)

Opus 4.7 proof-of-concept of a larger program (NegBioDB + failure
network + rescue engine for prematurely-rejected clinical hypotheses).
Same 4-role engine re-run on 15 H3 K27M DMG (pediatric brainstem cancer) rescue hypotheses
(locked-before-output git SHA 8a4ecc5): 7 supported, 7 mixed, 1
insufficient; top lead: panobinostat via CED (direct brain tumor drug delivery, 13/15
delivery class). Tier-1 prognostic-substrate gate then re-tested 4
candidates on PBTA v15 (pediatric brain tumor atlas, n=192 survival-evaluable, 182 events): 0
PASS, 2 FAIL, 2 UNDERPOWERED — intended falsifier output. **IPF (lung fibrosis) Run
#1: 1/5 supported, two Advocate fabrications caught (2026-04-25).**
Research-grade hypotheses; prospective validation required.
