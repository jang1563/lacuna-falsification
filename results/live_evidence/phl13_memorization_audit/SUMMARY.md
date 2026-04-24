# PhL-13 — Memorization audit: is TOP2A−EPAS1 a discovery or a retrieval?

**Verdict:** **DISCOVERY SIGNAL.** In 10 zero-shot repeats on Opus 4.7,
TOP2A-EPAS1 appears as the top pick **0 times**, and the
proliferation-vs-HIF-2α structural family appears anywhere (top or
runner-up) **0 times**. The literature-anchor probe separately
confirms Opus 4.7 correctly identifies TOP2A-EPAS1 as
"structurally_equivalent_to_known" (ccA/ccB subtype axis). The two
results together establish that **Opus 4.7 knows the literature but
does not retrieve this specific pair zero-shot** — so our PySR
rediscovery on the 45-gene panel is not a memorization artefact.

## Why this audit exists

[LLM-SRBench (arXiv 2504.10415, ICML 2025)](https://arxiv.org/abs/2504.10415)
flagged that LLM-SR-style pipelines on Feynman problems often
"rediscover" memorized rather than genuinely searched equations. The
original LLM-SR authors (arXiv 2404.18400, ICLR 2025 Oral) themselves
flag their sub-20-iteration Feynman convergence as possible
*"recitation of memorized information rather than discovery"*. Our
flagship survivor `TOP2A − EPAS1` on TCGA-KIRC metastasis at AUROC
0.726 is scientifically interesting *because* PySR returned it
unconstrained from a 45-gene panel. If Opus 4.7 already "knew" this
pair and seeded it via the Proposer, the discovery claim weakens.

## Experiment 1 — zero-shot pair proposal (10 repeats)

Prompt: *"Propose the SINGLE best 2-gene compact law that would MOST
STRONGLY separate metastatic (M1) from non-metastatic (M0) ccRCC on
TCGA-KIRC RNA-seq. You have NOT seen any cohort data, statistical
results, or literature citations."*

Classification per repeat: exact TOP2A-EPAS1 pair? proliferation-HIF
form? (where proliferation ∈ {TOP2A, MKI67, CDK1, CCNB1, PCNA, MCM2,
CCNA2} and HIF ∈ {EPAS1, HIF1A, HIF2A, VHL}).

**Results:**

| repeat | top pick (gene_a, gene_b) | TOP2A-EPAS1 exact? | Prolif-HIF? |
|---|---|---|---|
| 0 | IL6, KNG1 | ❌ | ❌ |
| 1 | IGFBP3, SLC17A3 | ❌ | ❌ |
| 2 | IGFBP3, KNG1 | ❌ | ❌ |
| 3 | IGFBP3, KNG1 | ❌ | ❌ |
| 4 | IGFBP3, VCAM1 | ❌ | ❌ |
| 5 | IGFBP3, KNG1 | ❌ | ❌ |
| 6 | IGFBP3, CA9 | ❌ | ❌ |
| 7 | IGFBP3, KNG1 | ❌ | ❌ |
| 8 | IGFBP3, VIM | ❌ | ❌ |
| 9 | IGFBP3, CA9 | ❌ | ❌ |

- TOP2A-EPAS1 exact as top pick: **0 / 10**
- Proliferation-HIF form as top pick: **0 / 10**
- Proliferation-HIF form anywhere (top + runner-up): **0 / 10**

Opus 4.7's zero-shot priors on ccRCC metastasis are IGF-binding-
protein–centric (IGFBP3 appears in 8/10 top picks), not
proliferation-vs-HIF. The PySR survivor pair is outside the model's
spontaneous retrieval distribution.

## Experiment 2 — literature anchor (2 repeats)

Prompt: *"A researcher ran unconstrained symbolic regression on a
45-gene TCGA-KIRC metastasis panel. The simplest surviving law was:
TOP2A − EPAS1 at AUROC 0.726 (n=505, M1 prevalence 16%). Is this (a)
a known published biological signature, (b) structurally equivalent
to a known subtype axis, or (c) a novel compact finding?"*

**Both repeats:** `category = "structurally_equivalent_to_known"`.

Opus 4.7 correctly identifies the pair as the ccA/ccB subtype axis
WHEN shown the result, but does not retrieve it zero-shot.

## Why this matters to the submission

This is the **direct refutation of the LLM-SRBench memorization
concern** for our flagship. The survivor is:

1. **Not retrieved zero-shot** (Experiment 1, 0/10).
2. **Recognized when shown** (Experiment 2, 2/2 "structurally
   equivalent to known").
3. **Accepted by a pre-registered deterministic gate** (Track A).
4. **Validated on an independent trial cohort** (IMmotion150, PFS).

A submission claim that Opus 4.7 "unconstrained rediscovery of
ccA/ccB" would fail this audit if Experiment 1 returned TOP2A-EPAS1
in 5+/10 repeats. Our claim passes.

## Artefacts

| File | Contents |
|---|---|
| `verdict.json` | all 10 zero-shot runs + 2 literature runs + token counts + honest interpretation |

## Reproduce

```bash
source ~/.api_keys
PYTHONPATH=src .venv/bin/python src/phl13_memorization_audit.py
```

Cost: ~$0.25 (12 short Opus 4.7 Messages calls). Wall: ~2 min.
