# PhL-15 — Adaptive thinking causal ablation (Opus 4.7)

**Question:** is adaptive thinking the *mechanism* behind Opus 4.7's Skeptic calibration?

## Design

- Opus 4.7 only (single model isolates mechanism)
- 6 candidates (same as E2 ablation, pass/borderline/fail spread)
- 10 repeats × 2 modes = **120 API calls**
- Modes:
  - `adaptive`: `thinking={'type':'adaptive','display':'summarized'}`
  - `disabled`: `thinking={'type':'disabled'}`

## Result

| Mode | PASS | FAIL | NEEDS_MORE_TESTS | UNPARSED |
|---|---|---|---|---|
| `adaptive` | 0 | 30 | 30 | 0 |
| `disabled` | 0 | 30 | 30 | 0 |

**Dissent rate on gate-PASS candidates** (TOP2A-EPAS1, MKI67-EPAS1, 5-gene compound):

- `adaptive`: 100.0% dissent (30 gate-PASS calls)
- `disabled`: 100.0% dissent (30 gate-PASS calls)

**Mean metric citations per response**:

- `adaptive`: 6.63
- `disabled`: 6.43

**Mean thinking content length (chars)**:

- `adaptive`: 0
- `disabled`: 0

## Interpretation

**Honest null — adaptive thinking is NOT the differentiator.** Adaptive ON and OFF both produce 0/60 PASS, 100% dissent on gate-PASS candidates, and nearly identical metric-citation specificity (6.63 vs 6.43). Within Opus 4.7, adaptive thinking ON/OFF does not measurably change Skeptic verdict behavior on this narrow-context prompt.

**Important scoping caveat**: the 0/60 PASS here differs from E2 ablation's 10/60 PASS for Opus 4.7. The difference is likely **prompt specificity** — E2 used pre-computed metrics with full dataset annotation (PySR-tuned coefficients, `category` field, "TCGA-KIRC metastasis M1 vs M0 n=505 45 genes"), while PhL-15 uses compact metrics ("TCGA-KIRC metastasis_expanded n=505"). Opus appears more calibrated with richer prompt context — Opus-vs-Sonnet calibration gap in E2 is real, but the isolated cause is not adaptive thinking.

**Implication for `docs/why_opus_4_7.md §0`**: the causal claim that "adaptive thinking keeps the Skeptic from collapsing" should be softened to "Opus 4.7 calibration" without attributing the mechanism specifically to adaptive thinking.

**Thinking content length**: `thinking_chars_mean_by_mode` is 0 in both — the `display=summarized` blocks in the API stream were not captured as `type=thinking` in my extraction code. Instrumentation limitation, not capability finding.

**Raw data**: `sweep.jsonl` (120 rows)

**Reproduce**:
```bash
source ~/.api_keys
PYTHONPATH=src .venv/bin/python src/phl15_adaptive_thinking_ablation.py run
PYTHONPATH=src .venv/bin/python src/phl15_adaptive_thinking_ablation.py analyze
```