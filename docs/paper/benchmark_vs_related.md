---
title: "Lacuna in context — benchmark vs. SPOT / Sakana v2 / POPPER"
subtitle: "What Lacuna is, and what it is not, with respect to the
three live AI-for-Science rigor benchmarks of April 2026."
date: "2026-04-23"
---

## Why this section exists

Three rigor-benchmark conversations are live in AI-for-Science as of
April 2026. Lacuna sits *between* the problems these benchmarks
target; the contribution is a specific niche, not a universal claim.
This note states the niche precisely so a reviewer can decide whether the
pipeline fits their use case.

## SPOT (arXiv [2505.11855](https://arxiv.org/abs/2505.11855))

**What SPOT measures.** Given a set of retracted or errata-marked papers,
can an LLM detect the specific error that caused the retraction?
Current SOTA (o3, Gemini-2.5-Pro, Claude-3.7-Sonnet:Thinking) sits at
**recall ≤ 21 %, precision ≤ 6 %** across 83 papers × 8 repeat runs.

**What Lacuna does differently.** SPOT is *post-hoc error
detection on already-published claims*. Lacuna is
*pre-registered error prevention at generation time.* The 5-test gate
is applied **before a candidate is ever called a finding**, so by
construction it cannot miss an error that the SPOT set later reports —
the candidate either cleared the pre-registered gate or it did not.
Our analogous "recall" is 100 % against our two explicit negative
controls (housekeeping contrast `log1p(ACTB) − log1p(GAPDH)` and
proliferation-over-ribosomal `log1p(MKI67) − log1p(RPL13A)`), both of
which the gate rejects on TCGA-KIRC. Our "false-accept rate" on those
controls is 0 / 2.

**Take-away.** These are complementary, not competing. SPOT measures
what happens when verification is post-hoc; Lacuna measures
what happens when verification is pre-registered.

## Sakana AI Scientist v2 (arXiv [2504.08066](https://arxiv.org/abs/2504.08066))

**What Sakana v2 claims.** An autonomous LLM pipeline that proposes
hypotheses, runs experiments, and writes peer-review-passable papers —
with one paper reported as clearing an ICLR workshop review.

**What external review found.** The peer-review-passing paper had
hallucinated experimental details, faked numerical results, and
overestimated its own novelty. The community reaction, visible in the
arXiv comments and the Sakana blog response, has shifted the central
question from *"can an AI write a paper?"* to *"can an AI reject its
own bad paper?"*

**What Lacuna does differently.** Our Skeptic role does not
decide whether to accept; the **deterministic 5-test gate does**. Opus
4.7 in the Skeptic role reviews metric values and produces a
`PASS / FAIL / NEEDS_MORE_TESTS` verdict *against* the gate, not
*instead of* it. The cross-model ablation in
[`results/ablation/SUMMARY.md`](../../results/ablation/SUMMARY.md)
shows explicitly that model verdict distributions differ across Opus
4.7 / Sonnet 4.6 / Haiku 4.5 on the same gate output — the
Skeptic is not rubber-stamping because the gate's numbers are
external-to-the-model and immutable.

**Take-away.** Lacuna does not try to write papers autonomously.
It tries to reject autonomously. The 100+ rejected candidates (see
[Rejection Log](../../results/rejection_log.html)) are the central
artefact; the one accepted law (`TOP2A − EPAS1`) is the remainder.

## POPPER (arXiv [2502.09858](https://arxiv.org/abs/2502.09858))

**What POPPER does.** Sequential e-values for Type-I error control on
LLM-generated scientific hypotheses. Targets hypothesis *validation*
against a held-out evidence stream.

**Where Lacuna overlaps.** Our two-sided permutation null +
Benjamini-Hochberg FDR is a simpler, classical-statistics analog of
POPPER's sequential-e-value approach. For small hypothesis families
(≤ ~30 candidates per gate run) the BH-FDR bound is tight enough that
POPPER's sequential machinery is overkill; for larger families a
POPPER-style e-value controller would be a natural swap into the
`_gate_test_results()` aggregation.

**Where Lacuna differs.** POPPER covers the validation leg.
Lacuna covers the generation + rejection loop on a single
dataset, with a biology-specific five-test gate (permutation,
bootstrap CI, sign-invariant single-gene baseline, incremental-
covariate confound, decoy-feature null). The two could compose: POPPER
runs over the cross-cohort replay step; our 5-test gate runs within
cohort.

**Take-away.** POPPER is a statistical-primitives benchmark.
Lacuna is a domain-biased discovery pipeline that uses
BH-FDR where POPPER would use sequential e-values — a pragmatic
choice for small hypothesis families.

## Regulatory context

The January 2026 [FDA-EMA Common Principles for AI Medicine Development](https://www.ema.europa.eu/en/news/ema-fda-set-common-principles-ai-medicine-development-0)
specify a *credibility assessment plan* with independent-data
validation. The EU AI Act's high-risk-system provisions take effect
on 2026-08-02. Pre-registered kill tests committed to a git-tracked
YAML, plus an independent-cohort replay (here: IMmotion150 PFS), is a
concrete template for both requirements — and it is machine-verifiable
via `make prereg-audit`.

## What Lacuna will not give you

- **A universal replacement for peer review.** The gate is biology-
  specific (5 tests defined for binary-classification + compound laws
  on gene expression). Ports to e.g. astronomy or materials would
  re-use the pre-registration machinery, not the gate thresholds.
- **A hypothesis generator.** Opus 4.7's Proposer role is a seeded
  brainstorming step; the space of compact candidates is enumerated
  by PySR symbolic regression, not by the LLM alone.
- **An autopilot.** Every commit passes `make test` + `make audit`
  by human convention, not by CI-enforcement. A production deployment
  would add those gates.

## Minimal citation set

- **SPOT**: arXiv:2505.11855
- **Sakana AI Scientist v2**: arXiv:2504.08066
- **POPPER**: arXiv:2502.09858 (code at github.com/snap-stanford/POPPER)
- **Brannon 2010 ccRCC subtypes (ccA/ccB)**: PMID 20871783
- **Brooks 2014 ClearCode34**: DOI 10.1016/j.eururo.2014.02.035
- **TOP2A in ccRCC metastasis**: PMID 38730293
- **FDA-EMA Common Principles (2026-01)**: ema.europa.eu (press release)
- **EU AI Act high-risk provisions (2026-08-02)**: eur-lex Regulation 2024/1689
- **IMmotion150 (McDermott 2018, source of PhF-3 replay cohort)**: PMID 29867230
