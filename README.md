# Theory Copilot: Falsification-Aware Biological Law Discovery

An Opus 4.7-centered workflow that makes theory-space search in biology **loopable** — Opus 4.7 proposes compact law families, symbolic regression instantiates them, falsification removes brittle candidates, and the surviving law transfers to a second disease dataset.

Built for the Built with Opus 4.7 Hackathon · April 2026

---

## Workflow (5 stages)

```
Proposal → Search → Judgment → Survivor → Transfer
```

| Stage | What happens | Model |
|---|---|---|
| **Proposal** | Opus 4.7 proposes 3–5 compact law families + skeptic tests | Opus 4.7 (extended thinking) |
| **Search** | PySR symbolic regression instantiates candidate equations | Local (no API) |
| **Judgment** | Opus 4.7 falsifies each candidate: permutation, bootstrap, baseline, confound | Opus 4.7 (extended thinking) |
| **Survivor** | Surviving law → separation plot + biological mechanism hypothesis | Opus 4.7 |
| **Transfer** | Same workflow replayed on a second dataset | Sonnet 4.6 + Opus spot-check |

---

## Key Modules

| File | Role |
|---|---|
| [`src/theory_copilot/falsification.py`](src/theory_copilot/falsification.py) | 4-test statistical falsification gate (permutation, bootstrap, baseline, confound) |
| [`src/theory_copilot/opus_client.py`](src/theory_copilot/opus_client.py) | Opus 4.7 three-role wrapper: Scientist, Skeptic, Interpreter |
| [`src/theory_copilot/visualize.py`](src/theory_copilot/visualize.py) | Separation histogram + falsification panel plots |
| [`prompts/`](prompts/) | Opus 4.7 prompts for each role |
| [`config/law_proposals.json`](config/law_proposals.json) | 14 KIRC/LUAD candidate law families |

---

## Quick Start

```bash
# Install (Python 3.10+)
pip install -e .

# Run tests (no API key needed — all mocked)
python -m pytest tests/ -v

# Run the Proposal stage (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=sk-ant-...
python - <<'EOF'
from theory_copilot.opus_client import OpusClient
client = OpusClient()
result = client.propose_laws(
    dataset_card={"name": "KIRC", "n_samples": 100},
    features=["CA9", "VEGFA", "LDHA", "AGXT", "ALB"],
    context="VHL-HIF axis in kidney renal clear cell carcinoma",
)
for f in result["families"]:
    print(f["name"], "->", f["form"])
EOF
```

---

## Falsification Gate

Each candidate equation must pass four tests to survive:

```python
from theory_copilot.falsification import run_falsification_suite

result = run_falsification_suite(equation_fn, X, y, X_covariates=None)
# result["passes"]          True / False
# result["perm_p"]          < 0.05   (not just noise)
# result["ci_width"]        < 0.10   (stable across resamples)
# result["delta_baseline"]  > 0.05   (better than best single feature)
# result["delta_confound"]  > 0.03   (not explained by covariates, if provided)
```

---

## Demo Data

`data/examples/` contains synthetic disease-vs-normal matrices for offline validation.
No patient data. No private identifiers.

For the full run, replace with public GEO-derived exports matching the same CSV contract:
```
sample_id, label (disease/control), [optional covariates], [numeric features...]
```

---

## License

Code: MIT
Data artifacts: CC-BY-4.0
