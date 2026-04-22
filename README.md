# Theory Copilot: Falsification-Aware Biological Law Discovery

Theory Copilot Discovery is a falsification-aware biological law discovery workflow built around Opus 4.7. Instead of celebrating the first high-scoring equation, the system proposes compact law families, searches for concrete candidates, attacks them with a five-test statistical gate, and only reports what survives. In the current judged core, the survivor discovered on TCGA-KIRC is replayed on GSE40435 as an independent cohort check.

Built for the Built with Opus 4.7 Hackathon · April 2026

---

## Workflow (5 stages)

```
Proposal → Search → Falsification → Survivor → Replay
```

| Stage | What happens | Model |
|---|---|---|
| **Proposal** | Opus 4.7 emits 3–5 compact law families *and* the skeptic test for each, **before any fit**. Required to include at least one negative control. | Opus 4.7 (extended thinking) |
| **Search** | PySR symbolic regression instantiates candidates with `variable_names=gene_cols` so equations come back in biological names. | Local (no API) |
| **Falsification** | Pure Python gate: two-sided permutation, bootstrap CI lower-bound, sign-invariant baseline, incremental-covariate confound, decoy-feature null, BH-FDR. Opus does **not** run this. | Python (deterministic) |
| **Survivor** | Opus 4.7 reviews each candidate's metric pattern and writes a biological mechanism hypothesis for the survivors. | Opus 4.7 (extended thinking) |
| **Replay** | Survivors replayed on an independent cohort with per-cohort z-score standardization. Three-way verdict: law_transfers / workflow_transfers / neither. | Opus 4.7 spot-check |

---

## Key Modules

| File | Role |
|---|---|
| [`src/theory_copilot/falsification.py`](src/theory_copilot/falsification.py) | 5-test statistical gate |
| [`src/theory_copilot/opus_client.py`](src/theory_copilot/opus_client.py) | Opus 4.7 three-role wrapper + JSON-fence-tolerant parser |
| [`src/theory_copilot/managed_agent_runner.py`](src/theory_copilot/managed_agent_runner.py) | Path B (single agent, public beta) + Path A (3-agent chain, waitlist) |
| [`src/theory_copilot/cli.py`](src/theory_copilot/cli.py) | `theory-copilot compare` + `replay` commands |
| [`src/pysr_sweep.py`](src/pysr_sweep.py) | PySR sweep with law-family injection, train/test split, novelty scoring |
| [`src/falsification_sweep.py`](src/falsification_sweep.py) | Batch falsification runner + BH-FDR |
| [`prompts/`](prompts/) | JSON-schema-enforced Opus 4.7 prompts |
| [`config/law_proposals.json`](config/law_proposals.json) | KIRC law families (pathway + anchor + negative controls) |
| [`data/examples/make_kirc_demo.py`](data/examples/make_kirc_demo.py) | Synthetic KIRC-compatible CSV generator |

---

## Quick Start

```bash
# Install (Python 3.10+, Julia 1.10.0 for PySR)
pip install -e .

# Run tests (no API key needed — all mocked)
python -m pytest tests/ -v

# Generate synthetic KIRC-compatible demo data
python data/examples/make_kirc_demo.py

# Smoke test: 4 candidates (2 strong + 2 negative controls) → 1 survivor expected
cat > /tmp/candidates.json <<EOF
[
  {"equation": "log1p(CA9) + log1p(VEGFA) - log1p(AGXT)", "complexity": 8},
  {"equation": "log1p(LDHA) - log1p(ALB)",                "complexity": 5},
  {"equation": "log1p(ACTB) - log1p(GAPDH)",              "complexity": 5},
  {"equation": "log1p(MKI67) - log1p(RPL13A)",            "complexity": 5}
]
EOF
python src/falsification_sweep.py \
  --candidates /tmp/candidates.json \
  --data data/examples/flagship_kirc_demo.csv \
  --genes CA9,VEGFA,LDHA,SLC2A1,NDUFA4L2,AGXT,ALB,ACTB,GAPDH,RPL13A,MKI67 \
  --covariate-cols age,batch_index \
  --output /tmp/report.json
# → "4 candidates → 1 survived falsification"

# Full pipeline with Opus 4.7 (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=sk-ant-...
theory-copilot compare --config config/datasets.json \
  --proposals config/law_proposals.json \
  --flagship-dataset kirc --output-root artifacts/
# → prints the PySR + falsification commands to run next
```

---

## The 5-Test Falsification Gate

Every candidate must clear all five tests before being called a survivor.
Thresholds pre-registered in [`falsification.py`](src/theory_copilot/falsification.py).

| Test | Statistic | Threshold |
|---|---|---|
| `label_shuffle_null` | Two-sided permutation p (1000 shuffles) | `p < 0.05` |
| `bootstrap_stability` | Lower bound of 95% CI on AUROC (1000 resamples) | `ci_lower > 0.6` |
| `baseline_comparison` | `law_AUROC − max_i max(AUROC(x_i), 1 − AUROC(x_i))` | `delta > 0.05` |
| `confound_only` | `AUROC(LR(cov + law)) − AUROC(LR(cov))` | `delta > 0.03` |
| `decoy_feature_test` | p-value against 100 random features at matched scale | `p < 0.05` |

Multiple candidates are tested per run → permutation p-values are adjusted with
Benjamini-Hochberg FDR across the family, and **the gate uses the FDR-adjusted p**.

---

## Example Output (synthetic KIRC demo)

A representative flagship run, with Opus 4.7 emitting 2 pathway laws + 2 explicit
negative controls:

```text
Candidates (Opus 4.7, Proposer role):
  C1  log1p(CA9) + log1p(VEGFA) - log1p(AGXT)    [HIF-axis vs normal]
  C2  log1p(LDHA) - log1p(ALB)                   [Warburg vs liver-like normal]
  C3  log1p(ACTB) - log1p(GAPDH)                 [Housekeeping NEGATIVE CONTROL]
  C4  log1p(MKI67) - log1p(RPL13A)               [Proliferation NEGATIVE CONTROL]

Falsification gate (Python — Opus does not execute this):
  C1  auc=0.83  ci_lo=0.79  p_fdr=0.000  Δbase=+0.11  Δconf=+0.31  decoy=0.00  PASS
  C2  auc=0.74  ci_lo=0.69  p_fdr=0.000  Δbase=+0.02  Δconf=+0.22  decoy=0.00  FAIL (delta_baseline)
  C3  auc=0.52  ci_lo=0.46  p_fdr=0.520  Δbase=-0.21  Δconf=+0.00  decoy=0.50  FAIL (all 5)
  C4  auc=0.54  ci_lo=0.49  p_fdr=0.179  Δbase=-0.18  Δconf=+0.03  decoy=0.12  FAIL (4/5)

1 / 4 survives. Both Opus-planted negative controls are killed by the gate,
and one pathway-grounded law (Warburg contrast) is killed because LDHA alone
is nearly as discriminative.
```

This is the "shock moment": the gate is rigorous enough to kill a textbook
Warburg law when LDHA alone does nearly the same job. The surviving HIF-axis
law earned that survival by genuinely adding 0.11 over any single gene.

---

## Demo Data

`data/examples/flagship_kirc_demo.csv` and `transfer_kirc_demo.csv` are
generated by `make_kirc_demo.py`. Columns share the gene-name contract with
real TCGA-KIRC + GSE40435 data (CA9, VEGFA, LDHA, AGXT, ALB, SLC2A1,
NDUFA4L2, ACTB, GAPDH, RPL13A, MKI67) + `age` + `batch_index` covariates.
No patient data. No private identifiers.

CSV contract:

```
sample_id, label (disease/control or 0/1), age, batch_index, <gene columns...>
```

---

## Broader Program

This artifact is the Opus 4.7-centered proof-of-concept of a larger research
program — **NegBioDB**, a structured database of ~32.8M confirmed negative
biomedical results (drug–target inactives, failed clinical trials, protein
non-interactions, non-essential genes, benign variants) paired with benchmarks
for publication-bias propagation into ML/LLM predictions. Theory Copilot
operationalizes NegBioDB's core thesis — falsification as the expensive,
neglected half of scientific inference — on real cancer-genomics data. The
public NegBioDB repository will be linked here at release.

---

## License

Code: MIT
Data artifacts: CC-BY-4.0
