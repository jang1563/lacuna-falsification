# Demo Walkthrough

End-to-end reproduction steps. Every step is fully reproducible on a
laptop; the offline test section at the end runs with no API key.

## Prerequisites

- Python 3.10+
- Julia 1.10.0 (PySR installs a compatible Julia on first run)
- `ANTHROPIC_API_KEY` in the environment for Opus 4.7 stages

```bash
cd theory_copilot_discovery
pip install -e .
python -c "import pysr"   # first run: 5–15 min Julia compilation
export ANTHROPIC_API_KEY=sk-ant-...
```

## Step 1 — Propose (Opus 4.7, Scientist role)

Opus 4.7 reads the dataset card + feature list and returns 3–5 compact
law families with biological rationale and pre-registered skeptic
tests.

```python
from theory_copilot.opus_client import OpusClient

client = OpusClient()
result = client.propose_laws(
    dataset_card={"name": "TCGA-KIRC", "n_samples": 606, "platform": "RNA-seq"},
    features=["CA9", "VEGFA", "LDHA", "AGXT", "ALB", "SLC2A1", "NDUFA4L2"],
    context="VHL-HIF axis in kidney renal clear cell carcinoma",
)
for f in result["families"]:
    print(f["name"], "->", f["form"])
```

Expected output (abbreviated):

```text
HIF/angiogenesis vs normal kidney -> log1p(CA9) + log1p(VEGFA) - log1p(AGXT)
Warburg vs liver-like normal       -> log1p(LDHA) - log1p(ALB)
Glycolysis + hypoxia vs normal     -> log1p(SLC2A1) + log1p(NDUFA4L2) - log1p(AGXT)
Angiogenic ratio                   -> log1p(VEGFA) - log1p(ALB)
```

`result["raw_thinking"]` contains the summarized extended-thinking
trace (non-empty because `display="summarized"` is set).

## Step 2 — Search (PySR, local)

PySR instantiates concrete equations, seeded by the Opus-proposed
templates via `guesses=` and `fraction_replaced_guesses=0.3`.

```bash
python -m theory_copilot.pysr_sweep \
    --data data/examples/flagship_demo.csv \
    --label-col label \
    --feature-cols CA9 VEGFA LDHA AGXT ALB \
    --proposals config/law_proposals.json \
    --out artifacts/kirc_candidates.jsonl
```

Expected JSONL row (abbreviated):

```json
{"template_id": "kirc_hif_angiogenesis_log",
 "equation": "log1p(CA9) + 0.87*log1p(VEGFA) - 1.02*log1p(AGXT)",
 "auroc_holdout": 0.91, "complexity": 11, "loss": 0.18}
```

## Step 3 — Falsify (Opus 4.7, Skeptic role)

Each candidate passes through the 5-test gate. Opus 4.7 reads the
equation + metrics and emits PASS / FAIL / NEEDS_MORE_TESTS with an
explicit reason. Gate thresholds are enforced statistically; Opus 4.7
cannot override them.

```bash
python -m theory_copilot.falsification_sweep \
    --candidates artifacts/kirc_candidates.jsonl \
    --data data/examples/flagship_demo.csv \
    --label-col label \
    --fdr 0.05 \
    --out artifacts/kirc_survivors.jsonl
```

Expected output:

```text
[FAIL] log1p(CA9) single-gene anchor
       delta_baseline = 0.00  (< 0.05 threshold)
       reason: law collapses to a single feature; no multi-gene benefit
[PASS] log1p(CA9) + log1p(VEGFA) - log1p(AGXT)
       perm_p = 0.002, ci_width = 0.07, delta_baseline = 0.09, delta_confound = 0.06
[FAIL] log1p(VEGFA) - log1p(ALB)
       ci_width = 0.14  (> 0.10 threshold)
       reason: bootstrap resampling unstable
Survivors after BH-FDR(0.05): 1 / 3
```

## Step 4 — Interpret (Opus 4.7, Interpreter role)

```python
survivor = "log1p(CA9) + log1p(VEGFA) - log1p(AGXT)"
result = client.interpret_survivor(
    equation=survivor,
    dataset_context={"name": "TCGA-KIRC", "tissue": "kidney"},
)
print(result["hypothesis"])
```

Expected hypothesis (abbreviated):

```text
The surviving law reads as a HIF-axis contrast: CA9 (HIF-1α target,
membrane-bound carbonic anhydrase upregulated under hypoxia) and VEGFA
(HIF-2α target, angiogenic driver of VHL-null kidney tumors) on the
positive side, against AGXT (peroxisomal alanine-glyoxylate
aminotransferase, a marker of normal proximal-tubule oxidative
metabolism suppressed on VHL loss). Mechanism hypothesis: the law
captures the HIF-stabilization-driven switch from oxidative metabolism
to angiogenesis + hypoxic survival. Research use only.
```

## Step 5 — Transfer (GSE40435)

Replay the same pipeline on the independent cohort. Sonnet 4.6 drives
the replay; Opus 4.7 does the interpretation spot-check.

```bash
python -m theory_copilot.pysr_sweep \
    --data data/examples/transfer_demo.csv \
    --label-col label \
    --feature-cols CA9 VEGFA LDHA AGXT ALB \
    --proposals config/law_proposals.json \
    --out artifacts/gse40435_candidates.jsonl

python -m theory_copilot.falsification_sweep \
    --candidates artifacts/gse40435_candidates.jsonl \
    --data data/examples/transfer_demo.csv \
    --label-col label \
    --fdr 0.05 \
    --out artifacts/gse40435_survivors.jsonl
```

AUROC comparison (example run):

```text
log1p(CA9) + log1p(VEGFA) - log1p(AGXT)
  TCGA-KIRC  AUROC = 0.91  (survived gate)
  GSE40435   AUROC = 0.88  (survived gate)
  Verdict: law_transfers
```

## Managed Agents (Path B)

Fully public-beta; no waitlist required. Path B drives the same
pipeline through a single agent with `agent_toolset_20260401`.

```python
from theory_copilot.managed_agent_runner import run_path_b

result = run_path_b(
    dataset_csv="data/examples/flagship_demo.csv",
    proposals_json="config/law_proposals.json",
    out_dir="artifacts/managed_agents_run/",
)
print(result["survivors"])
```

Expected delegation log (abbreviated):

```text
[Agent] pysr-sweep-agent (id=agt_01H...) created
[Env]   pysr-compute-env (id=env_01H...) created
[Session] title="theory_copilot_flagship" started
  [Tool: bash] python -m theory_copilot.pysr_sweep ...
  [Tool: bash] python -m theory_copilot.falsification_sweep ...
  [Tool: read] artifacts/kirc_survivors.jsonl
  [agent.message] Pipeline complete. 1 survivor after FDR. Details written to artifacts/.
[session.status_idle]
```

Path A (`callable_agents` multi-agent delegation) is implemented and
gated behind the `MANAGED_AGENTS_MULTIAGENT=1` environment variable;
it activates once the research-preview waitlist is granted.

## Offline Demo (no API key)

The full pipeline is tested against synthetic disease-vs-normal data
so judges can reproduce without credentials or compute:

```bash
python -m pytest tests/ -v

python - <<'PY'
import numpy as np
from theory_copilot.falsification import run_falsification_suite

rng = np.random.default_rng(42)
X = rng.normal(size=(200, 3))
y = (X[:, 0] - X[:, 1] > 0).astype(int)

def equation_fn(X):
    return X[:, 0] - X[:, 1]

result = run_falsification_suite(equation_fn, X, y, X_covariates=None)
print(result)
PY
```

Expected (abbreviated):

```text
{'passes': True, 'perm_p': 0.001, 'ci_width': 0.06,
 'delta_baseline': 0.08, 'delta_confound': None,
 'law_auc': 0.94, 'baseline_auc': 0.86}
```
