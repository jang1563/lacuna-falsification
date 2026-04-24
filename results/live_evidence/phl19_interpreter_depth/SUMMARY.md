# PhL-19 — Interpreter mechanism hypothesis depth

**Question:** for a gate-accepted survivor, how deep / disciplined
is each model's biological interpretation?

## Design

- 3 survivors (TOP2A-EPAS1, MKI67-EPAS1, 5-gene compound).
- 3 models × 3 survivors = 9 mechanism hypotheses.
- Blind Opus rubric (model labels hidden) + programmatic checks.

## Rubric (blind-rated)

| Model | Specificity | Caveat | Testability | Prior art | Trust |
|---|---|---|---|---|---|
| opus | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| sonnet | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| haiku | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

## Structural metrics (rater-independent)

| Model | Caveat % | Prediction % | Mean citations | Mean pathway mentions |
|---|---|---|---|---|
| opus | 100% | 100% | 12.0 | 5.3 |
| sonnet | 0% | 0% | 0.0 | 1.3 |
| haiku | 0% | 0% | 0.0 | 0.0 |

## Reproduce
```bash
source ~/.api_keys
PYTHONPATH=src .venv/bin/python src/phl19_interpreter_depth.py interp
PYTHONPATH=src .venv/bin/python src/phl19_interpreter_depth.py rate
PYTHONPATH=src .venv/bin/python src/phl19_interpreter_depth.py analyze
```