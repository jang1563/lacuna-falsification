# Rashomon Set Analysis — 2-gene linear-difference laws

**Question**: How unique is `TOP2A − EPAS1`? Of C(45,2)=990 gene pairs,
how many achieve sign-invariant AUROC within ε of 0.7256 on TCGA-KIRC
metastasis (M0 vs M1, n=505)?

## Cohort
- n = 505, M1 prevalence = 15.6%
- Gene panel: 45 genes
- Pairs evaluated: 990

## Where does TOP2A − EPAS1 rank?
- **Rank 1 / 990**  (AUROC = 0.7256)
- Best observed pair: **EPAS1-TOP2A** at AUROC = 0.7256

## Rashomon set size vs ε

| ε | Threshold AUROC | Set size |
|---|---|---|
| 0.005 | 0.7206 | 1 |
| 0.01 | 0.7156 | 1 |
| 0.02 | 0.7056 | 3 |
| 0.03 | 0.6956 | 6 |
| 0.05 | 0.6756 | 21 |
| 0.1 | 0.6256 | 141 |

**Interpretation**: The size of the Rashomon set at each ε quantifies
how many *structurally distinct* 2-gene laws achieve comparable
discrimination. A small set at tight ε = more unique; a large set = more
redundant alternatives exist.

## Pathway-combo distribution in top 20 pairs

Are all top pairs `(Proliferation − HIF_axis)`, or do other pathway
combinations also land in the Rashomon set? This is the sufficient
condition test the H2 1M-context synthesis predicted.

| Pathway combo | Count in top 20 |
|---|---|
| ('HIF_axis', 'Proliferation') | 5 |
| ('Proliferation', 'Warburg') | 5 |
| ('Proliferation', 'other') | 3 |
| ('Proliferation', 'Tubule_normal') | 3 |
| ('HIF_axis', 'Housekeeping') | 2 |
| ('EMT_metastasis', 'HIF_axis') | 1 |
| ('Proliferation', 'Proliferation') | 1 |

## Files
- `rashomon_full.json` — top-50 rows + rashomon set sizes + pathway distribution
- `rashomon_top50.csv` — top 50 pairs with annotations

## Reproduce
```bash
PYTHONPATH=src .venv/bin/python src/rashomon_analysis.py
```