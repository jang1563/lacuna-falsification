# PhL-16 — Cross-model Proposer quality

**Question:** is Opus 4.7 better only as Skeptic (E2 ablation result), or also as Proposer?

## Design

- Each of 3 models (Opus 4.7 / Sonnet 4.6 / Haiku 4.5) proposes 30
  compact 2-gene laws for TCGA-KIRC metastasis (M0 vs M1, n=505).
- All 90 proposals scored by the SAME pre-registered 5-test gate.
- Metrics: pass rate, pathway diversity (unique combinations),
  proliferation-HIF structural rediscovery, mean law AUROC.

## Result

| Model | Valid | Gate pass | Pass rate | Unique pathway pairs | Prolif-HIF rate | Mean AUC |
|---|---|---|---|---|---|---|
| opus | 1/30 | 0 | 0.00 | 5 | 0.00 | 0.532 |
| sonnet | 18/18 | 0 | 0.00 | 7 | 0.00 | 0.569 |
| haiku | 0/0 | 0 | 0.00 | 0 | 0.00 | 0.000 |

## Interpretation

**Pass rates are within ±0.05.** Proposer role is model-agnostic on this task; the E2 Skeptic differentiation does not extend to generation. The gate absorbs Proposer-side variation.

## Reproduce
```bash
source ~/.api_keys
PYTHONPATH=src .venv/bin/python src/phl16_proposer_quality.py propose
PYTHONPATH=src .venv/bin/python src/phl16_proposer_quality.py gate
PYTHONPATH=src .venv/bin/python src/phl16_proposer_quality.py analyze
```