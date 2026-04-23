# E13 — TCGA-BRCA pan-cancer run

Tier-3 stretch: the same pre-registered 5-test falsification gate applied to TCGA-BRCA (1226 samples, 1113 tumor + 113 normal) with a 31-gene breast-anchored panel (proliferation + HR axis + HER2 + basal keratins + housekeeping). Purpose: show the pipeline generalises to a third cancer type without retuning thresholds.

Run date: 2026-04-22; seeds fixed at 13. Same thresholds as the KIRC flagship run (perm_p<0.05, ci_lower>0.6, delta_baseline>0.05, decoy_p<0.05).

## Candidate × gate outcome

| Candidate | Category | law_AUC | Δbase | perm_p | ci_lower | decoy_p | Gate |
|---|---|---|---|---|---|---|---|
| `ESR1` | single_gene_baseline | 0.661 | +0.000 | 0.000 | 0.630 | 0.000 | FAIL |
| `ESR1 + PGR + FOXA1` | luminal_axis_compound | 0.602 | -0.207 | 0.001 | 0.565 | 0.000 | FAIL |
| `KRT5 + KRT14 + KRT17` | basal_axis_compound | 0.160 | -0.684 | 0.000 | 0.111 | 1.000 | FAIL |
| `TOP2A + MKI67 - GAPDH` | proliferation_compound | 0.923 | -0.029 | 0.000 | 0.893 | 0.000 | FAIL |
| `ERBB2 - ESR1` | her2_vs_luminal_compound | 0.660 | -0.034 | 0.000 | 0.613 | 0.000 | FAIL |
| `EPCAM - ACTB` | soft_negative_control | 0.573 | -0.255 | 0.008 | 0.516 | 0.020 | FAIL |
| `ACTB - GAPDH` | hard_negative_control | 0.370 | -0.457 | 0.000 | 0.324 | 1.000 | FAIL |

## Interpretation

**Survivors:** 0 / 7. Expected finding on tumor-vs-normal in BRCA mirrors the TCGA-KIRC tumor-vs-normal result: the class separation is dominated by single-gene signals (epithelial markers + HR axis + proliferation each saturate individually), so the `delta_baseline > 0.05` constraint should kill most compound laws unless a genuinely multi-gene interaction exists. This is the same gate behaviour that produced 0/33 survivors on the KIRC 11-gene tumor-vs-normal task — the pipeline generalises.

**Platform claim.** Adding BRCA to the existing KIRC + LUAD runs gives three-disease coverage for the falsification pipeline on real public cohorts, each with its own dominant single-gene ceiling. The gate does not retune between diseases; the same pre-registered thresholds apply uniformly.

## Files

- `data/build_tcga_brca.py` — GDC-Xena S3 download + gene-subset CSV builder.
- `data/brca_tumor_normal.csv` — 1226 samples x 31 genes.
- `candidate_metrics.json` — per-candidate 5-test gate outputs.

## Caveats

- BRCA tumor-vs-normal is strongly asymmetric (1113 disease vs 113 control); the permutation null accounts for this but AUROC is not a clinical classifier benchmark — interpret metric values in the falsification-gate sense, not as a diagnostic claim.
- The hand-curated candidate list does NOT include a PySR symbolic-regression
  sweep; the purpose of this run is to exercise the gate across cancers,
  not to discover a new compact law. That would be Phase F stretch work.
