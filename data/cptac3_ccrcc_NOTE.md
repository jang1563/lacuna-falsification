# CPTAC-3 ccRCC replay — manual retrieval notes

Status: **stub** — PDC GraphQL unreachable from this session; see manual steps below

## How to complete this replay by hand

1. Go to <https://pdc.cancer.gov/pdc/study/S044-1> (CPTAC-3 CCRCC Discovery
   Proteome, Clark et al. Cell 2019, n=103 tumors).
2. Download the gene-level log2-ratio quantification matrix and the
   CPTAC-3 clinical metadata (contains `ajcc_pathologic_m`).
3. Join on `case_submitter_id` (tumor aliquot) → produce a wide CSV
   with columns: sample_id, label (M1|M0), tumor_stage, age,
   batch_index, patient_id, <TOP2A..VEGFA expression>.
4. Use RNA quantification from the matched CPTAC-3 RNA-seq study
   (`Clark_CCRCC_RNA_Transcriptome`) for head-to-head with the TCGA-KIRC
   RNA-seq readout.
5. Rerun `run_external_replay.py --cohort cptac3` to emit the gate
   verdict on M1 vs M0 for `TOP2A - EPAS1`.

## Why this matters

CPTAC-3 is the ONLY published ccRCC cohort that carries both the
proliferation + HIF-2α gene pair and patient-level M-stage. A pass
on this cohort would let `TOP2A - EPAS1` clear a proteogenomic
replay too; a fail here is the most informative negative result.
GSE53757 and GSE40435 both lack M-stage and therefore only serve
as tumor-vs-normal sanity checks for the same law.
