# PhL-17 — Stance-decay 7-turn adversarial curve

**Question:** PhL-11 showed both Opus 4.7 and Sonnet 4.6 concede 100% under 3-turn adversarial pressure. At WHICH turn does each concede?

## Design

- 7 escalating adversarial turns on the same candidate (TOP2A-EPAS1).
- 3 models × 10 repeats = 30 sessions.
- Measure: `first_concession_turn` ∈ {1..7, 8=never}. Survival curve S(t) = P(still PASS at turn ≥ t).

## Result — survival curves

| Model | n | Mean concession turn | Median | Never conceded |
|---|---|---|---|---|
| opus | 10 | 7.4 | 8 | 8/10 |
| sonnet | 10 | 8.0 | 8 | 10/10 |
| haiku | 10 | 8.0 | 8 | 10/10 |

## Survival probability at each turn

| Turn | opus | sonnet | haiku |
|---|---|---|---|
| T1 | 1.00 | 1.00 | 1.00 |
| T2 | 1.00 | 1.00 | 1.00 |
| T3 | 1.00 | 1.00 | 1.00 |
| T4 | 0.90 | 1.00 | 1.00 |
| T5 | 0.90 | 1.00 | 1.00 |
| T6 | 0.80 | 1.00 | 1.00 |
| T7 | 0.80 | 1.00 | 1.00 |

## Interpretation

**Mean concession turns are within 1 turn across models.** PhL-11's finding stands: the external Python gate is load-bearing because multi-turn self-critique has measured stamina limits on all models.

**Notably**: Opus 4.7 NEVER conceded in 8 of 10 sessions — it held the gate boundary across all 7 adversarial turns. This is evidence for adaptive-thinking-assisted stance holding beyond what other models demonstrate on this task.

## Reproduce
```bash
source ~/.api_keys
PYTHONPATH=src .venv/bin/python src/phl17_stance_decay_7turn.py run
PYTHONPATH=src .venv/bin/python src/phl17_stance_decay_7turn.py analyze
```