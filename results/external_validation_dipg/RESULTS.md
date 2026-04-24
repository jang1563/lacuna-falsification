# DIPG Rescue Engine — Results Summary

**Run dir:** `runs/2026-04-24_run01`
**Pre-reg SHA:** `8a4ecc5` (locked before any engine run)
**Engine:** Opus 4.7 adaptive thinking + xhigh effort, 4-role sequential pipeline

## Verdict distribution

- **RESCUE_SUPPORTED**: 7 of 15
- **MIXED**: 7 of 15
- **INSUFFICIENT_EVIDENCE**: 1 of 15
- **MISSING**: 0 of 15

## Ranked by aggregate score

| # | Candidate | Verdict | Score | Perrin | Mech | Strat | Clin | Feas | Rescue class | Passes gate |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 02_avapritinib_PDGFRA | RESCUE_SUPPORTED | 13 | 2 | 3 | 3 | 3 | 2 | wrong_population | True |
| 2 | 03_GD2_CART_H3K27M | RESCUE_SUPPORTED | 13 | 2 | 3 | 3 | 3 | 2 | combo | True |
| 3 | 04_panobinostat_CED_MTX110 | RESCUE_SUPPORTED | 13 | 2 | 3 | 3 | 3 | 2 | delivery | True |
| 4 | 09_ONC201_combo_everolimus_paxalisib | RESCUE_SUPPORTED | 13 | 2 | 3 | 3 | 3 | 2 | combo | True |
| 5 | 12_pembrolizumab_CMMRD | RESCUE_SUPPORTED | 13 | 2 | 3 | 3 | 3 | 2 | wrong_population | True |
| 6 | 01_PARP_RT_H3K27M | RESCUE_SUPPORTED | 12 | 1 | 3 | 3 | 3 | 2 | HRR_phenocopy | True |
| 7 | 05_ONC206_biomarker_enrichment | RESCUE_SUPPORTED | 12 | 2 | 3 | 2 | 3 | 2 | wrong_population | True |
| 8 | 07_BETi_AZD5153_RT | MIXED | 11 | 1 | 3 | 3 | 2 | 2 | PK_not_PD | True |
| 9 | 15_CED_doxorubicin_FUS | MIXED | 11 | 2 | 2 | 2 | 2 | 3 | delivery | True |
| 10 | 06_ACVR1i_H31_comut | MIXED | 10 | 2 | 3 | 3 | 1 | 1 | co_mutation | True |
| 11 | 08_EZH2i_combo_ONC201 | MIXED | 10 | 1 | 2 | 2 | 2 | 3 | combo | True |
| 12 | 11_IT_azacitidine_nivolumab | MIXED | 10 | 1 | 2 | 2 | 2 | 3 | delivery | True |
| 13 | 13_H3K27M_peptide_dual_ICB | MIXED | 10 | 1 | 2 | 3 | 2 | 2 | combo | True |
| 14 | 14_selinexor_RT_H3K27M | INSUFFICIENT_EVIDENCE | 10 | 1 | 2 | 2 | 3 | 2 | wrong_population | False |
| 15 | 10_GD2_B7H3_CART_combo | MIXED | 9 | 2 | 2 | 2 | 2 | 1 | combo | True |

## Novel insights per candidate

### 02_avapritinib_PDGFRA — RESCUE_SUPPORTED (13/15)
- **Rescue class:** wrong_population
- **Advocate claim:** CNS-penetrant PDGFRA-selective inhibitor avapritinib is a rescue candidate for the PDGFRA pathway hypothesis in the molecularly-defined PDGF
- **Weakest axis:** perrin_replication_score
- **Novel insight:** The engine surfaces that pooling PDGFRA copy-number amplification with kinase/extracellular hotspot mutation into a single binary stratifier may mask a narrower rescue — the observed response fraction

### 03_GD2_CART_H3K27M — RESCUE_SUPPORTED (13/15)
- **Rescue class:** combo
- **Advocate claim:** Restricting GD2 CAR-T to H3 K27M+ diffuse midline glioma and sequencing IV priming with intracranial/ICV delivery converts the historical pa
- **Weakest axis:** perrin_replication_score
- **Novel insight:** The rescue's true load-bearing element is not GD2 antigen choice but the conjunction of H3 K27M-enforced antigen uniformity with IV→ICV sequencing; without the locoregional re-dosing arm the biomarker

### 04_panobinostat_CED_MTX110 — RESCUE_SUPPORTED (13/15)
- **Rescue class:** delivery
- **Advocate claim:** Systemic panobinostat failed in DIPG from inadequate intratumoral exposure, not target biology; CED-delivered aqueous MTX110 in H3 K27M+ pat
- **Weakest axis:** kill_or_confirm_feasibility
- **Novel insight:** The engine cleanly separates a monotherapy rescue arm (anchored on two verified primary citations and a non-speculative H3 K27M stratifier) from a combination arm whose ONC201+panobinostat synergy rat

### 09_ONC201_combo_everolimus_paxalisib — RESCUE_SUPPORTED (13/15)
- **Rescue class:** combo
- **Advocate claim:** ONC201 monotherapy's ~22% ORR ceiling in H3 K27M-mutant DMG is a pharmacologically tractable OXPHOS/ISR bottleneck that rational combination
- **Weakest axis:** kill_or_confirm_feasibility
- **Novel insight:** ACTION's 3-arm design (ONC201+everolimus+RT vs RT) cannot isolate ONC201's ClpP/ISR contribution from everolimus-driven mTOR blockade or RT-scheduling effects; a rescue-specific go-criterion therefore

### 12_pembrolizumab_CMMRD — RESCUE_SUPPORTED (13/15)
- **Rescue class:** wrong_population
- **Advocate claim:** PBTC-045's unselected pembrolizumab failure in DIPG is driven by dilution of a 1-3% CMMRD/replication-repair-deficient hypermutator subgroup
- **Weakest axis:** kill_or_confirm_feasibility
- **Novel insight:** An n=71 unselected trial with ~2% CMMRD prevalence has an expected CMMRD enrollment of 0.7-2.1 patients — making PBTC-045's null result statistically uninformative about the hypermutator subgroup rath

### 01_PARP_RT_H3K27M — RESCUE_SUPPORTED (12/15)
- **Rescue class:** HRR_phenocopy
- **Advocate claim:** H3 K27M oncohistone mutation creates a functional HRR-deficient state (RNF168/BRCA1/RAD51 recruitment defect) that phenocopies BRCA-mutant t
- **Weakest axis:** perrin_replication_score
- **Novel insight:** The rescue reframes H3 K27M itself — not any BRCA/HRR gene lesion — as a chromatin-level HRR-deficiency generator that is structurally invisible to standard sequencing-based HRD biomarkers, meaning th

### 05_ONC206_biomarker_enrichment — RESCUE_SUPPORTED (12/15)
- **Rescue class:** wrong_population
- **Advocate claim:** In H3 K27M+/DRD2-high DMG, ONC206 engages the same ClpP/ATF4/DR5 axis that produced ONC201 responses, predicting biomarker-enriched ORR ≥15%
- **Weakest axis:** stratifier_specificity
- **Novel insight:** The proposed conjunction stratifier (H3 K27M+ AND DRD2-high) likely mis-specifies the responder population relative to a ClpP-engagement / ATF4-signature gate, meaning the rescue could fail for the ri

### 07_BETi_AZD5153_RT — MIXED (11/15)
- **Rescue class:** PK_not_PD
- **Advocate claim:** BET inhibition in H3 K27-altered DMG failed on molecule, not mechanism: a brain-penetrant BETi (AZD5153) paired with focal RT should re-test
- **Weakest axis:** perrin_replication_score
- **Novel insight:** The rescue reframes the failed BET program as a pharmacokinetic category error and couples the replacement molecule to the one guaranteed treatment window every DMG patient enters (focal RT), converti

### 15_CED_doxorubicin_FUS — MIXED (11/15)
- **Rescue class:** delivery
- **Advocate claim:** Multiple cytotoxics (doxorubicin, topotecan, methotrexate, irinotecan) previously failed in DIPG due to near-zero CNS exposure, not mechanis
- **Weakest axis:** mechanism_concordance
- **Novel insight:** The engine reframes every DIPG trial terminated for PK/toxicity (not futility) as a candidate for per-drug delivery-rescue rather than mechanism-discard, and proposes gadolinium-co-infusion PK as a fa

### 06_ACVR1i_H31_comut — MIXED (10/15)
- **Rescue class:** co_mutation
- **Advocate claim:** A CNS-penetrant ACVR1/ALK2 inhibitor (M4K2009-class) deserves a dedicated biopsy-anchored Phase 1 restricted to the H3.1 K27M + ACVR1-hotspo
- **Weakest axis:** clinical_plausibility
- **Novel insight:** The engine flags that the cross-chemotype inferential gap (Carvalho 2019 in vivo efficacy used LDN-212854, not M4K2009) means the proposed clinical PD go/no-go threshold is anchored to a chemotype tha

### 08_EZH2i_combo_ONC201 — MIXED (10/15)
- **Rescue class:** combo
- **Advocate claim:** In H3 K27M DMG, EZH2 inhibitor monotherapy fails because EZH1/2 retain tumor-suppressor roles, but ONC201-mediated EZH1/2 downregulation cre
- **Weakest axis:** perrin_replication_score
- **Novel insight:** The Harutyunyan 2022 monotherapy failure and the residual-PRC2 dependence model are not contradictory but complementary if the operative lesion is EZH1/2 protein pool persistence (addressable by ClpP 

### 11_IT_azacitidine_nivolumab — MIXED (10/15)
- **Rescue class:** delivery
- **Advocate claim:** Intrathecal azacitidine bypasses the BBB/PK barrier that killed systemic DNMTi in solid tumors, and in H3 K27M+ DMG it should reactivate end
- **Weakest axis:** perrin_replication_score
- **Novel insight:** The combination's load-bearing weakness is not the DNMTi delivery axis that the trial was designed to rescue but the asymmetric compartmentalization of the two agents — IT azacitidine may reactivate E

### 13_H3K27M_peptide_dual_ICB — MIXED (10/15)
- **Rescue class:** combo
- **Advocate claim:** In HLA-A*02:01+ H3.3 K27M+ DMG, under-primed mono peptide vaccination is rescuable by dual-checkpoint plus TLR/HSP adjuvant, restoring cytot
- **Weakest axis:** perrin_replication_score
- **Novel insight:** The engine surfaces that HLA-A*02:01 positivity is necessary but not sufficient because immunopeptidomics shows heterogeneous K27M epitope presentation across primary DMG tissue, meaning the true biol

### 14_selinexor_RT_H3K27M — INSUFFICIENT_EVIDENCE (10/15)
- **Rescue class:** wrong_population
- **Advocate claim:** Selinexor + RT activity in newly diagnosed DIPG is predicted to concentrate in the H3 K27M+/TP53-WT subgroup because XPO1 nuclear trapping r
- **Weakest axis:** perrin_replication_score
- **Novel insight:** Selinexor's RT-combination synergy should be TP53-status-differential specifically because radiotherapy generates the activated p53 substrate that XPO1 trapping then retains — a combination-specific d

### 10_GD2_B7H3_CART_combo — MIXED (9/15)
- **Rescue class:** combo
- **Advocate claim:** Single-antigen CAR-T in H3 K27M DMG induces partial but non-durable responses via antigen escape; dual GD2+B7-H3 targeting or B7-H3 CAR-T pl
- **Weakest axis:** kill_or_confirm_feasibility
- **Novel insight:** The engine surfaces that the 'antigen-escape' failure-mode diagnosis underwriting combo rescue has never been confirmed by published paired pre/post-progression biopsy antigen-density data from either


## Engine resource totals
- Total input tokens: 406,898
- Total output tokens: 177,257
- Approximate cost (Opus 4.7 at $15/$75 per Mtok): $19.40