# PhL-18 — Pre-registration writing quality

**Question:** how rigorously can each model write a scientific
pre-registration that BINDS before the fit?

## Design

- 5 hypotheses (ccRCC metastasis, IMmotion, BRCA cross-cancer,
  SLC22A8 extension, PRAD generalization).
- 3 models × 5 = **15 pre-registration YAMLs**.
- Two scoring dimensions:
  - **Programmatic structural** (rater-independent): required keys
    coverage, numeric-value density, kill-test list items, biology
    grounding term count.
  - **Blind-rated rubric** (Opus 4.7 meta-rater, model labels
    hidden): threshold specificity, kill-test coverage,
    falsifiability, biology grounding, scope discipline. Each 0-10.

**Self-preference-bias caveat**: the Opus rater could favour Opus
YAMLs. Mitigation: (a) labels hidden behind `Candidate_A/B/C` with
random order, (b) programmatic structural metrics reported
alongside as rater-independent signal.

## Rubric scores (blind-rated)

| Model | Threshold | Kill-test | Falsifiability | Biology | Scope |
|---|---|---|---|---|---|
| opus | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| sonnet | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| haiku | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

## Structural metrics (rater-independent)

| Model | Key coverage % | Mean numeric values | Mean kill tests | Mean biology terms |
|---|---|---|---|---|
| opus | 100.0 | 58.8 | 5.8 | 5.4 |
| sonnet | 100.0 | 110.8 | 5.6 | 5.0 |
| haiku | 0.0 | 0.0 | 0.0 | 0.0 |

## Interpretation

**Rubric winner**: opus. Honest finding — pre-reg writing quality is not uniformly Opus-dominant.

## Reproduce
```bash
source ~/.api_keys
PYTHONPATH=src .venv/bin/python src/phl18_prereg_writing_quality.py write
PYTHONPATH=src .venv/bin/python src/phl18_prereg_writing_quality.py rate
PYTHONPATH=src .venv/bin/python src/phl18_prereg_writing_quality.py analyze
```