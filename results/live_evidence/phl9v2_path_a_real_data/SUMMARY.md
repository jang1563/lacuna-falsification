# PhL-9 v2 — Path A live chain on REAL TCGA-KIRC data

**Verdict:** OK — 3-session sequential chain completed in 300 s with
substantive ccRCC-grounded outputs at every role. Closes the PhL-9 v1
evidence weakness (v1 ran on a synthetic physics toy because no data
was mounted into the Managed Agents environment).

## What v2 fixed

PhL-9 v1 Proposer reported *"The expected `config/law_proposals.json`
file does not exist in this environment"* and fell back to generic
physics law families (power_law, exponential_decay, simple_harmonic).
The surviving law was `y = 3.67 * x^1.40` on a 600-row synthetic
dataset the Skeptic reconstructed from scratch. Narrative disconnect.

PhL-9 v2 uploads the real CSV + law-template JSON via
`client.beta.files.upload()` and mounts them into each session's
working tree via `resources=[{"type":"file","file_id":...,"mount_path":
"/workspace/..."}]` at session creation.

## What the chain produced on real data

**Session A (Proposer, Opus 4.7):** read 505-row TCGA-KIRC metastasis
cohort (M0=426, M1=79), log-normalized genes, confirmed label alignment,
emitted 5 ccRCC law families centred on real biology:

- `LF-PROLIF-minus-HIF2A` — `mean(log1p(TOP2A,MKI67,CDK1)) − log1p(EPAS1)` — the ccA/ccB subtype axis family
- `LF-WARBURG-vs-OXPHOS` — glycolytic trio vs oxidative anchor (LDHA, SLC2A1, PDK1, LDHB, AGXT)
- `LF-HIF-ANGIO-SHIFT` — VEGFA + ANGPTL4 − EPAS1 − CA9
- `LF-EMT-STROMA` — MMP9 + SPP1 + CXCR4 + S100A4 − PAX8
- `LF-HOUSEKEEPING-NULL` — housekeeping negative control (ACTB/GAPDH/RPL13A)

Each candidate carries an ex-ante skeptic test written BEFORE the fit.
Negative control explicitly `expected_verdict:"FAIL"` with dataset-audit
escape clause.

**Session B (Searcher, Sonnet 4.6):** fitted each family on the real
data, emitted per-candidate `law_auroc` + `best_single_gene_sign_invariant_auroc` + `delta_baseline`.

**Session C (Skeptic, Opus 4.7):** applied pre-registered
`delta_baseline > 0.05` threshold strictly, quoting specific TCGA-KIRC
metrics per candidate:

| Candidate | law_auroc | best-single | delta_baseline | verdict |
|---|---|---|---|---|
| `LF-PROLIF-minus-HIF2A` | 0.7157 | CDK1=0.6570 | **+0.0587** | NEEDS_MORE_TESTS (perm / CI / decoy pending) |
| `LF-WARBURG-vs-OXPHOS` | 0.5138 | PDK1=0.5914 | −0.0776 | FAIL (under-performs own best constituent) |
| `LF-HIF-ANGIO-SHIFT` | 0.5837 | EPAS1=0.6556 | −0.0718 | FAIL (subtracting EPAS1 destroys informative component) |
| `LF-EMT-STROMA` | 0.5331 | MMP9=0.5725 | −0.0394 | FAIL |
| `LF-HOUSEKEEPING-NULL` | 0.5016 | ACTB=0.5758 | −0.0742 | FAIL (intended negative control; "no special exemption is granted") |

**Aggregate line Skeptic emitted verbatim:**
> *"On TCGA-KIRC (n=505), 1 of 5 candidates meet the delta_baseline threshold; 1 is NEEDS_MORE_TESTS pending permutation / bootstrap / decoy."*

This is verdict quality a reviewer can audit: real cohort, real gene
names, real numeric margins, correct application of the pre-reg
threshold (including refusal to exempt the negative control just
because its AUC~0.5 is "intended behavior" — it still fails
`delta_baseline > 0.05`).

## Architecture details

- `delegation_mode = sequential_fallback` (per 2026-04-23 fairness
  rule; research-preview `callable_agents` not available to hackathon
  participants).
- Three distinct `session_id`s in one `environment_id`; three distinct
  `agent_id`s (one per persona).
- Two files uploaded via `client.beta.files.upload()`, attached via
  `resources=[{"type":"file","file_id":...,"mount_path":"/workspace/..."}]`
  at each session's creation.
- Environment pre-installs `pandas>=2.0`, `numpy>=1.24`, `scikit-learn>=1.3`
  so the Searcher can `sklearn.metrics.roc_auc_score` in bash.

## Artefacts

| File | Contents |
|---|---|
| `verdict.json` | session_ids, agent_ids, env_id, file_ids, wall, narrative |
| `role_proposer.txt` | 2 823 chars — full Opus 4.7 Proposer turn |
| `role_searcher.txt` | 3 910 chars — full Sonnet 4.6 Searcher turn |
| `role_skeptic.txt` | 1 933 chars — full Opus 4.7 Skeptic turn (ended promptly after strict-JSON verdict) |

## Reproduce

```bash
source ~/.api_keys
PYTHONPATH=src .venv/bin/python src/phl9v2_path_a_real_data.py
```

Cost: ~$1.50. Wall: 300 s.

## Why this is stronger evidence than PhL-9 v1

v1 showed Path A's **architecture** runs end-to-end (session chain,
delegation_mode flag, artefact shape). v2 shows the architecture
running the **actual scientific task the submission is about**, with
Skeptic verdicts that cite TCGA-KIRC numbers and apply pre-registered
thresholds strictly. A judge opening `role_skeptic.txt` now sees
ccRCC biology, not `y = 3.67 * x^1.40`.
