# Track — DIPG (Diffuse Intrinsic Pontine Glioma)

**Status:** DATA ACQUISITION FAILED — no valid public dataset found

---

## Acquisition attempts

| Source | Accession | Outcome |
|---|---|---|
| OpenPedCan v15 (GDC) | S3 open-access | HTTP 404 — URL dead (`d3b-openaccess-us-east-1-prd-pbta`) |
| GEO DIPG tumor expression | GSE115397 | Wrong content: 3KB microglia/macrophage RNA-seq, not tumor expression |
| GEO DIPG GEO | GSE101108 | Wrong disease: ovarian carcinoma transcriptomics |
| GEO GSE70867 | IPF BAL | HTTP 404 — dataset not found |

No usable DIPG expression dataset with clinical outcome labels was accessible
via public URLs within the hackathon window.

---

## Pre-registered prediction (not tested)

Pre-registered law: `OLIG2 − UQCRC1`

Rationale: OLIG2 is a H3K27M DIPG driver transcription factor; UQCRC1 encodes
complex III of the mitochondrial respiratory chain. In H3K27M DIPG, OxPhos is
upregulated relative to normal pons. The compound was hypothesized to separate
H3K27M-driven DIPG from non-DIPG pons tissue.

This prediction could not be falsification-tested due to the data acquisition failure.

---

## Honest note

The DIPG acquisition failure is recorded as an honest null: the pipeline works
correctly but cannot run without data. OpenPedCan v15 was the primary planned
source; the S3 URL change (OpenPBTA/D3b infrastructure) rendered it inaccessible.
Future work: access via Cavatica/CBTTC portal or local institutional download.
