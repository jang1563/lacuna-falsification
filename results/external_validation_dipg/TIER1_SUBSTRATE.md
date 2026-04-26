# Tier-1 Statistical Substrate — DIPG Rescue Engine

**Run dir:** `runs/2026-04-24_run01`
**Pre-reg SHA:** `8a4ecc5`  (locked before any engine run)
**Test kind:** prognostic_under_SOC  (PBTA cohort received standard-of-care; the proposed therapeutic agents were NOT administered in this cohort)
**Pre-reg deviations:** KPS substituted by extent_of_tumor_resection (KPS not in PBTA schema); HLA-A2 dimension reduced for candidate 13 (data-access blocker)

## Substrate verdict per candidate

| Candidate | Verdict | n+ | n− | HR (95% CI) | perm p | bootstrap_lower_coef | decoy p | flags |
|---|---|---|---|---|---|---|---|---|
| 02_avapritinib_PDGFRA | **FAIL** | 11 | 181 | 0.99 (0.35-2.77) | 0.8706 | -0.649 | 0.890 | - |
| 06_ACVR1i_H31_comut | **FAIL** | 19 | 173 | 1.18 (0.57-2.45) | 0.2160 | -0.041 | 0.240 | STRATIFIER_SURROGATE_ACVR1_FOR_H31_DUE_TO_PBTA_SNV_LACKS_H3 |
| 12_pembrolizumab_CMMRD | **UNDERPOWERED** | 3 | 189 | n/a | n/a | n/a | n/a | STAT_TIER_VIOLATION_UNDERPOWERED_SUBSTRATE |
| 13_H3K27M_peptide_dual_ICB | **UNDERPOWERED** | 188 | 4 | n/a | n/a | n/a | n/a | STRATIFIER_REDUCED_BY_DATA_ACCESS, STRATIFIER_SURROGATE_ACVR1_WT_FOR_H33_DUE_TO_PBTA_SNV_LACKS_H3, STAT_TIER_VIOLATION_UNDERPOWERED_SUBSTRATE |

## Per-candidate detail

### 02_avapritinib_PDGFRA: FAIL
- prevalence: 0.057
- n_strat: pos=11, neg=181, meets_min_per_arm=True
- Cox HR: 0.990, 95% CI [0.354, 2.772], p=0.9848
- permutation null p (10000 perms): 0.8706129387061294
- bootstrap 95% CI lower bound on coefficient: -0.648809895670154
- decoy stratifier p (100 random): 0.89
- confound incremental delta (c-index full vs covariates-only): 0.000956937799043045
- pre_reg_deviations: ['KPS_substituted_by_extent_of_tumor_resection']
- notes: Failed gate checks: perm_p=0.8706129387061294; cox_p=0.9848278671619114; bootstrap_ci_lower=-0.648809895670154

### 06_ACVR1i_H31_comut: FAIL
- prevalence: 0.099
- n_strat: pos=19, neg=173, meets_min_per_arm=True
- Cox HR: 1.180, 95% CI [0.567, 2.455], p=0.6581
- permutation null p (10000 perms): 0.21597840215978403
- bootstrap 95% CI lower bound on coefficient: -0.04093740026176036
- decoy stratifier p (100 random): 0.24
- confound incremental delta (c-index full vs covariates-only): -0.0052631578947368585
- flags: ['STRATIFIER_SURROGATE_ACVR1_FOR_H31_DUE_TO_PBTA_SNV_LACKS_H3']
- pre_reg_deviations: ['KPS_substituted_by_extent_of_tumor_resection']
- notes: Failed gate checks: perm_p=0.21597840215978403; cox_p=0.6580879424889363; bootstrap_ci_lower=-0.04093740026176036; confound_delta=-0.0052631578947368585

### 12_pembrolizumab_CMMRD: UNDERPOWERED
- prevalence: 0.016
- n_strat: pos=3, neg=189, meets_min_per_arm=False
- permutation null p (10000 perms): None
- bootstrap 95% CI lower bound on coefficient: None
- decoy stratifier p (100 random): None
- confound incremental delta (c-index full vs covariates-only): None
- TMB distribution: median=0.50, max=566.47, n_hypermutator=316
- flags: ['STAT_TIER_VIOLATION_UNDERPOWERED_SUBSTRATE']
- pre_reg_deviations: ['KPS_substituted_by_extent_of_tumor_resection']
- notes: n_strat_pos=3, n_strat_neg=189; pre-reg minimum per arm = 8. Substrate test cannot proceed; this is the engine's intended falsifier output for under-powered substrate hypotheses.

### 13_H3K27M_peptide_dual_ICB: UNDERPOWERED
- prevalence: 0.979
- n_strat: pos=188, neg=4, meets_min_per_arm=False
- permutation null p (10000 perms): None
- bootstrap 95% CI lower bound on coefficient: None
- decoy stratifier p (100 random): None
- confound incremental delta (c-index full vs covariates-only): None
- flags: ['STRATIFIER_REDUCED_BY_DATA_ACCESS', 'STRATIFIER_SURROGATE_ACVR1_WT_FOR_H33_DUE_TO_PBTA_SNV_LACKS_H3', 'STAT_TIER_VIOLATION_UNDERPOWERED_SUBSTRATE']
- pre_reg_deviations: ['KPS_substituted_by_extent_of_tumor_resection']
- notes: n_strat_pos=188, n_strat_neg=4; pre-reg minimum per arm = 8. Substrate test cannot proceed; this is the engine's intended falsifier output for under-powered substrate hypotheses.
