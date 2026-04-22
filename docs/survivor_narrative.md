# The survivor narrative — TOP2A − EPAS1

On 2026-04-22, the pre-registered 5-test gate in this repo rejected
100+ candidates across four ccRCC tasks and then — on the same
infrastructure, same gate, same thresholds — accepted nine candidates
on the metastasis task when the gene panel was expanded from 11 to
45 features. The simplest of those survivors is

```
score = TOP2A − EPAS1
```

This document walks through what that one-line law is, why it passed,
why 100+ other candidates did not, and — most importantly — what it
is *not*.

## One-minute version

**Claim.** On TCGA-KIRC (n = 505, 16% M1), tumours with high TOP2A
(topoisomerase IIα; a direct marker of proliferating cells) relative
to EPAS1 (HIF-2α; the canonical well-differentiated hypoxic ccRCC
driver) are more likely to be metastatic at diagnosis. Measured as
a pre-registered compound law, the equation `TOP2A − EPAS1` reaches
AUROC 0.726 with a lower 95% CI bound of 0.665 and a permutation
null `p < 0.001`; the improvement over the best sign-invariant
single-gene classifier is `Δ = +0.069`, clearing the +0.05
threshold that was fixed before any fit.

**How surprising is this?** It is the published ccA-vs-ccB ccRCC
subtype axis (Brannon et al., Brooks et al., ClearCode34), so the
biology is not new. What is new is that unconstrained symbolic
regression rediscovered it without being seeded with it, and that
the pre-registered falsification gate accepted the compact 2-gene
form on merits written down before the search.

**How robust is this?** The survivor passes five of six robustness
axes (threshold grid, two-sided permutation stability, bootstrap
seed variance, feature scaling, cohort-size subsample) and a 5-fold
held-out CV (0.722 ± 0.078). The one caveat is that a logistic
regression on the same pair *with an interaction term* reaches
AUROC 0.722 on the same cohort — so against that specific
engineered baseline the compound wins by only +0.004. The
survivor's distinctive contribution is therefore interpretable
compactness plus pre-registered falsification, not an AUROC ceiling
that no other 2-gene model reaches.

**What it is not.** Not a diagnostic biomarker. Not novel biology.
Not a replacement for prospective validation. Research use only.

## Why 100+ other candidates failed

Four ccRCC tasks were run with the same pipeline before the 45-gene
panel was tried:

| Task | Dominant single gene (sign-inv AUROC) | Survivors |
|---|---|---|
| Tumor vs Normal | CA9 = 0.965 | 0 / 33 |
| Stage I-II vs III-IV | CUBN = 0.610 | 0 / 34 |
| 5-yr Survival | CUBN = 0.696 | 0 / 36 |
| Metastasis (11-gene panel) | MKI67 = 0.645 | 0 / 37 |

Each task is dominated by a different single gene. On tumor-vs-
normal, CA9 alone saturates classification at AUROC 0.965, which
makes +0.05 mathematically unreachable for any compound
(`law_AUROC` would have to exceed 1.015). On stage and survival,
CUBN — a proximal-tubule marker lost during tumor dedifferentiation
— already carries most of the separation signal. On metastasis
with the 11-gene HIF-axis panel, the panel simply does not
contain genes that encode the aggressive proliferation program.

On the 45-gene expanded panel (which adds TOP2A, MKI67, CDK1,
CCNB1, PCNA, MCM2, plus HIF-2α partners and EMT markers), the
signal that was absent in the 11-gene run becomes available and
the gate starts accepting. The nine surviving laws cluster into
three shapes, all centred on `proliferation − HIF-2α`:

- `TOP2A − EPAS1` (5 laws at AUROC 0.726)
- `MKI67 − EPAS1` (2 laws at AUROC 0.708)
- a 5-gene compound (`MKI67 / EPAS1 / LRP2 / PTGER3 / RPL13A`) at
  the same AUROC 0.726 as the simpler pair

All three clusters encode the same biology. Parsimony preference
picks the 2-gene form.

## Why this is interesting *as a discovery artefact*

Three properties matter:

1. **Pre-registration actually bites on both sides.** The same +0.05
   threshold that rejected the textbook Opus-proposed HIF-axis law
   on tumor-vs-normal (`log1p(CA9) + log1p(VEGFA) − log1p(AGXT)`,
   AUROC 0.984 — but +0.019 over CA9 alone, so FAIL) accepts an
   unseeded 2-gene law on metastasis. Neither decision was made
   after the fact.
2. **The accept doesn't collapse under stress.** The 6-axis
   robustness profile (see
   [`survivor_robustness/SUMMARY.md`](../results/track_a_task_landscape/survivor_robustness/SUMMARY.md))
   matches the specific toolkit Sci-B used to harden the *reject*
   verdict. Same methodology, same toolkit, opposite direction.
3. **The caveat is named explicitly.** A 2-gene LR with interaction
   on the same pair reaches AUROC 0.722. The survivor's value is
   not that nothing else could pass — it's that it passed a
   pre-registered gate while staying readable in one line.

## What would make this claim stronger

1. **Independent-cohort replay** on a ccRCC dataset with TOP2A +
   EPAS1 measurements and M-staging at the patient level. GSE40435
   (our current transfer cohort) has neither. Candidate cohorts:
   - **CPTAC-3 ccRCC** (proteogenomic, has M-staging)
   - **cBioPortal MSKCC-IMPACT metastatic ccRCC**
2. **Larger panel** (200-gene Hallmark HYPOXIA or the full
   transcriptome). Hypothesis: the +0.069 incremental gap holds
   but the survivor count grows; alternatively, the
   pair-interaction baseline ceiling also rises to match the
   compound, which would narrow the compactness claim.
3. **Prospective held-out sample** (TCGA-KIRC freshly accessed via
   GDC rather than the cached star_tpm release).

Each of the three is scoped in the live `STATUS.md` "What's left"
section.

## Short version for the demo / Loom

> We pre-registered a five-test statistical gate before touching
> data. Opus 4.7 proposed seven KIRC law families. PySR searched
> the space. The gate rejected every one of the textbook HIF-axis
> compounds — including the law Opus 4.7 itself most wanted to
> survive. Then we expanded the panel, re-ran the same gate, and
> nine compact laws passed on metastasis. The simplest is
> **TOP2A − EPAS1**: when a ccRCC tumour's proliferation program
> runs ahead of its HIF-2α differentiation program, it's more
> likely to be metastatic. This is the published ccA-vs-ccB
> subtype axis. We didn't put it there. The gate accepted it
> because the numbers pre-registered before the fit said "accept
> if it clears +0.05 over the best single gene" and it cleared by
> +0.069.

## Related reading

- [`docs/methodology.md`](methodology.md) — Section 6 has the full
  accept/reject table.
- [`docs/why_opus_4_7.md`](why_opus_4_7.md) — Section 4 walks the
  accept + reject cycle in Opus-role terms.
- [`results/track_a_task_landscape/SUMMARY.md`](../results/track_a_task_landscape/SUMMARY.md)
  — cross-task matrix.
- [`results/track_a_task_landscape/survivor_robustness/SUMMARY.md`](../results/track_a_task_landscape/survivor_robustness/SUMMARY.md)
  — 6-axis stress test.
- [`results/track_a_task_landscape/survivor_robustness/INTERPRETATION_top2a_epas1.md`](../results/track_a_task_landscape/survivor_robustness/INTERPRETATION_top2a_epas1.md)
  — Opus-4.7-authored mechanism + caveat statement.
- [`results/track_b_gate_robustness/SUMMARY.md`](../results/track_b_gate_robustness/SUMMARY.md)
  — robustness of the *reject* verdict on the 11-gene panel.
