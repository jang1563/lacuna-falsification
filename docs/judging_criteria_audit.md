# Lacuna — Judging Criteria Audit

**Purpose:** Single source of truth for Cerebral Valley × Anthropic
*Built with Opus 4.7* hackathon judging criteria. Built from
(a) official rules page (`cerebralvalley.ai/e/built-with-4-7-hackathon/details`,
extracted 2026-04-25), (b) Kickoff 2026-04-21 (Ivan Porollo),
(c) Live sessions 4/22-4/23 (Tharik, Michael Cohen), (d) Discord
Q&A 4/22-4/25 (Ado Kukic, Eli Benveniste), (e) 4.6 winner pattern
analysis. This document is **re-checked at every stage** of the
submission finalisation push.

**Submission deadline:** 2026-04-26 (Sun) 20:00 ET
**Final round:** 2026-04-28 (Tue) 12:00 ET — top-6 panel (Boris + Jason)

---

## 1. Official rules (verbatim, from cerebralvalley.ai/e/built-with-4-7-hackathon/details)

### 1.1 Prize structure (confirmed verbatim)

| Tier | Prize | Amount |
|---|---|---|
| 1st | Grand Prize | **$50,000** in API credits |
| 2nd | | **$30,000** in API credits |
| 3rd | | **$10,000** in API credits |
| Special | "**Most Creative Opus 4.7 Exploration**" | $5,000 in API credits |
| Special | "**The 'Keep Thinking' Prize**" | $5,000 in API credits |
| Special | "**Best use of Claude Managed Agents**" | $5,000 in API credits |

**Five (5) finalists may receive prizes.**

### 1.2 Marketing copy (= judging signal)

The official page's three calls-to-action are the most authoritative
free-text statement of what judges value:

> 1. **"Show us what you can build in one week with Claude Code"**
> 2. **"Show us the thing only you'd know to build — the problem in your work or community that takes weeks but should take hours"**
> 3. **"Show us something that's easier to demo than to explain, an idea that doesn't exist yet but should"**

Maps to: (1) Claude Code use; (2) domain-expert + impact; (3)
demo-able novelty.

### 1.3 Submission requirements (verbatim + Discord clarification)

| Item | Spec |
|---|---|
| Demo video | **≤ 3 minute hard cap** (Discord 4/25) |
| GitHub repo | URL; **public during judging**; OSS license required |
| Written description | Length **uncapped** but **100-200 words recommended** (Discord 4/25); 4-beat: what / problem / how-built / how-Claude |

**Open source.** Every component must be under an approved OSS
license. Repo must be 100% public for judging window. Can flip to
private after 4/28. Third-party APIs (e.g. ElevenLabs) are OK as
long as integration code is OSS.

---

## 2. Judging axes — confirmed weights (Kickoff 4/21 + Discord 4/25)

| Axis | Weight | Source | Notes |
|---|---|---|---|
| **Impact** | **30%** | Kickoff 4/21 | Real people's real time/cost saved; problem-statement fit |
| **Demo** ⭐ | **25%** | Kickoff 4/21 | Ivan: "most invest time here". Ado 4/23: **"Demo video is THE PRIMARY source we'll use for judging"** — only after shortlist do judges look at code |
| **Opus 4.7 use** | **25%** | Discord 4/25 confirmation | Creative, beyond basic, surprises. **Single axis equal in weight to Demo** — same load as the most-invested axis |
| **Depth & execution** | **20%** | Discord 4/25 confirmation | "Push past first idea, real craft" |
| **Sum** | **100%** | | |

**Implication for narrative balance:** Opus 4.7 Use is 1.0× the
weight of Depth, equal to Demo. Our Managed Agents + Skills + Memory
paragraph in the submission form **must carry the same weight as
the demo video itself**. Underweighting it costs ¼ of total score.

### 2.1 Ado Discord articulation (4/24, JXavierH)

> "How clearly it articulates the **problem**, what the participant **built**,
> how it compares to **what else is out there**, and how applicable the
> solution is a **wide audience**."

Maps to: (1) problem clarity, (2) build, (3) comparison vs alternatives,
(4) wide-audience applicability. This is the **rubric inside Impact axis**.

---

## 3. Judges — confirmed panel + their stated priorities

| Judge | Role | What they reward | Source |
|---|---|---|---|
| **Boris Cherny** | Head of Claude Code | parallel sub-agents, CLAUDE.md institutional memory, validation loops, MCP, "build for the next model not this one", "compounding engineering" | Pragmatic Engineer interview, InfoQ |
| **Jason Bigman** | Head of Community | domain-expertise, accessibility (non-engineer), community impact | LinkedIn / 4.6 winner picks |
| **Lydia Hallie** | MTS, Claude Code | DX quality, visual + interface polish | Bun → Vercel → Anthropic background |
| **Ado Kukic** | DevRel | docs, practical utility, "would a developer actually use this" | adocomplete.com / Advent of Claude |

**Final round panel (4/28 noon ET):** Boris + Jason confirmed.

---

## 4. 4.6 winner patterns (5 — meta signal, applied 5/5 by all 3 podium)

1. **Domain expertise > engineering credentials** — 4 of 5 winners non-pro-SWE (lawyer, cardiologist, road engineer, musician)
2. **Real lived-experience pain + named end-user** (lawyer→ADU permit; cardiologist→patient summary)
3. **Agentic architecture** (parallel sub-agents)
4. **Human-meaningful metrics** ("$30K saved", "weeks→20 min")
5. **Demo narrative**: human → pain → before → after, 3-min cut

## 5. 4.6 common mistakes (4 — Discord Eli Benveniste 4/22 + Ado 4/22)

| Mistake | Description | Our status |
|---|---|---|
| **#1** | Remotion-replicated UI in demo (no actual product screen recording) | ✅ AVOIDED — `loom_visual_cue_map.md` uses real editor panes + real terminal cuts; verified 2026-04-25 by parallel-session audit |
| **#2** | Breadth > depth | ✅ AVOIDED — pivot freeze in effect since 4/24; same engine recursively applied (KIRC → IMmotion150 → DIPG → IPF) |
| **#3** | Feature creep, not knowing when to stop | ⚠️ MONITOR — IPF 8th segment added 2026-04-25; total 2:23-2:47 still under 3-min cap; segment density at limit |
| **#4** | Insufficient time invested in demo video | ✅ AVOIDED — 5 Loom artefacts (script, narration verbatim, narration final 90s, cue map, cheatsheet) totalling 1022 lines of preparation |

**Verdict (4.6 traps):** all four either AVOIDED ✅ or MONITORED ⚠️.

---

## 6. Discord Q&A (4/22-4/25) — direct submission impact items

### 6.1 ⭐⭐ Critical (must have direct narrative reflection)

- **(Ado 4/23)** "Demo video is THE PRIMARY source we'll use for judging
  your project. For the shortlist of finalists we will go and dive
  deeper into the code." → **Demo carries entry decision; code carries
  finals decision.** Stage 7 is non-negotiable.

- **(Ado 4/22)** "putting enough effort into your demo video. We only
  have the video and description to go off of, so if the demo video
  doesn't represent the project in the best light it will hurt your
  chances." → reinforces Demo as PRIMARY.

- **(Eli 4/23)** "Tons of people replicated their product/UI in
  Remotion for their demo... Judges want to see the actual product
  work in the video... They use the video/demo to judge, so that's
  the most important part." → **screen-record real CLI / real
  artefacts, not mocked UI.** ✅ verified compliant.

### 6.2 ⭐ Strategic (should reflect)

- **(Eli 4/24, Memory stores)** Anthropic Memory designed for
  concurrent multi-agent access; documented use case. Our PhL-3
  demo follows the documented pattern, not ad-hoc design. → cite
  in Best-MA paragraph.

- **(Ado 4/23)** Managed Agents = Anthropic-hosted endpoint, no
  server expose needed. → confirms Path C Routine driver narrative.

- **(Ado 4/23)** "Production-level systems vs strong simulation":
  prefer the latter. "Tough to build both in one week." → Lacuna
  framed as **capability demo on real public data**, not deployable
  SaaS. No overclaim needed.

### 6.3 N/A (don't apply to Lacuna)

PHI/HIPAA, non-English demo, ElevenLabs, Claude.ai visualizer API,
inter-agent channels, $500 cap overage. None apply.

---

## 7. Self-audit checklist (Stage 1 fills this)

### 7.1 Compact axis-by-axis table

| Axis (weight) | Sub-criterion | Status | Evidence file |
|---|---|---|---|
| **Impact (30%)** | Real-world problem articulated | _Stage 1_ | _TBD_ |
| | "Built from what you know" — domain-expert credible | _Stage 1_ | _TBD_ |
| | Wide-audience applicability | _Stage 1_ | _TBD_ |
| | Time/cost saved (human-meaningful metric) | _Stage 1_ | _TBD_ |
| | Comparison vs existing alternatives | _Stage 1_ | _TBD_ |
| **Demo (25%)** | Demo ≤ 3:00 | _Stage 1_ | _TBD_ |
| | Real product screen recording (not Remotion-replicated UI) | _Stage 1_ | _TBD_ |
| | "Easier to demo than to explain" | _Stage 1_ | _TBD_ |
| | Human → pain → before → after narrative arc | _Stage 1_ | _TBD_ |
| | Visible Claude Code / Opus 4.7 in action | _Stage 1_ | _TBD_ |
| **Opus 4.7 use (25%)** | Beyond basic prompting | _Stage 1_ | _TBD_ |
| | Creative / surprising integration | _Stage 1_ | _TBD_ |
| | Adaptive thinking / 1M context / extended-thinking demonstrated | _Stage 1_ | _TBD_ |
| | Managed Agents (Best-MA special prize candidacy) | _Stage 1_ | _TBD_ |
| | Skills / Memory / Routines used per documented pattern | _Stage 1_ | _TBD_ |
| **Depth (20%)** | "Push past first idea" — multiple iterations visible | _Stage 1_ | _TBD_ |
| | Real craft (tests, audits, validation) | _Stage 1_ | _TBD_ |
| | Pre-registration discipline | _Stage 1_ | _TBD_ |
| | Honest negative results / self-falsification | _Stage 1_ | _TBD_ |

### 7.2 Submission requirements compliance

| Requirement | Status |
|---|---|
| Demo video URL | ❌ Not yet recorded (Stage 7 = 4/26 AM) |
| GitHub repo URL | ⏳ Lacuna rename committed locally (f5bb417); awaiting GitHub UI rename + push |
| Written description (100-200w) | ✅ submission_form_draft.md unified summary 176/200w |
| Description 4-beat (what / problem / how-built / how-Claude) | ⚠️ Stage 6 needs to verify |
| Public repo during judging window | ⏳ Stage 9 |
| OSS license on all code | ✅ MIT (verify per pyproject) |
| 3rd-party API integration code public | ✅ Anthropic API only |

### 7.3 Special-prize candidacy

| Prize | Our claim | Justification status |
|---|---|---|
| Best use of Claude Managed Agents ($5K) | **Primary target** | submission_form_draft.md Prize justification 96/100w drafted; covers Path A/B/C + Memory PhL-3 |
| Most Creative Opus 4.7 Exploration ($5K) | Secondary candidate (1M context cross-reasoning) | Not currently called out — Stage 6 decide |
| Keep Thinking ($5K) | Secondary candidate (extended-thinking ablation PhL-15 + adversarial PhL-17) | Not currently called out — Stage 6 decide |

---

## 8. Stage history

| Stage | Date | Result |
|---|---|---|
| Stage 0 — audit doc | 2026-04-25 | This doc shipped |
| Stage 1 — self-audit | 2026-04-25 | `docs/stage1_self_audit.md` — compact table + Demo/Opus 4.7 deep dive + top-3 gaps |
| Stage 2 — gap discussion | 2026-04-25 | Top-3 confirmed; deep research for Gap #3 metric narrative; additional gap found (secondary prizes not called out) |
| Stages 3-5 — gap fixes | 2026-04-25 | Gap #1: 4-beat restructure (what / problem / how-built / how-Claude); Gap #3: "$58, 32 min" fabrication-catch embedded in Beat 4; Gap #4: Most Creative + Keep Thinking secondary prize sentence added to Opus 4.7 usage |
| Stage 6 — submission form 4-beat restructure + final QA | _pending_ | Verify word counts, special-prize coverage, Lacuna rename consistency |
| Stage 7 — Loom recording | 2026-04-26 AM (planned) | _TBD_ |
| Stage 8 — final audit | _pending_ | _TBD_ |
| Stage 9 — submit window | 2026-04-26 18:00-20:00 ET | _TBD_ |
| Stage 10 — social package post-submit | _pending_ | _TBD_ |
