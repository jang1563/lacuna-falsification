# Public data provenance

**Scope:** every CSV in `data/*.csv` that the submission code reads.
**Compliance framing:** open-source code + **public / no-login data**.
No institutional access, no credential-gated cohort, no dbGaP, no
PRS-tier controlled access.

This file exists so a reviewer can verify each dataset without hunting.
Every row below is re-derivable by running the listed builder script
against the upstream source; every CSV hash is in `data/SHA256SUMS`
(re-verify offline with `shasum -a 256 -c data/SHA256SUMS`).

---

## Provenance table

| CSV | Upstream source | Access | Builder | Role in submission |
|---|---|---|---|---|
| `kirc_metastasis.csv` | TCGA-KIRC (STAR TPM) via **GDC-Xena Hub** (`xenabrowser.net`) | public, no login | `data/build_tcga_kirc_metastasis.py` | Track A metastasis M0 vs M1 task (n=505, 11-gene HIF-axis panel). Source of 100+ rejections. |
| `kirc_metastasis_expanded.csv` | same as above, 45-gene panel | public, no login | `data/build_tcga_kirc_expanded.py` | **Flagship survivor cohort.** TOP2A − EPAS1 discovered here; 9 / 30 survive the gate. |
| `kirc_tumor_normal.csv` | same TCGA-KIRC STAR TPM | public, no login | `data/build_tcga_kirc.py` | Track A tumor-vs-normal task (n=609). CA9 single-gene saturates. |
| `kirc_stage.csv` | same TCGA-KIRC + clinical XML | public, no login | `data/build_tcga_kirc_stage.py` | Track A stage I-II vs III-IV task (n=534). |
| `kirc_survival.csv` | same TCGA-KIRC + clinical XML | public, no login | `data/build_tcga_kirc_survival.py` | Track A 5-yr survival task (n=301). |
| `kirc_survival_expanded.csv` | same, 45-gene panel | public, no login | `data/build_tcga_kirc_survival.py` + expanded gene-list | Track A survival with expanded panel — still fails threshold. |
| `gse40435_kirc.csv` | **GEO GSE40435** (Affymetrix HG-U133 Plus 2.0; Wozniak et al. 2013, PMID 23894363) | public, no login | `data/build_gse40435_expanded.py` (original 8-gene build) | Phase D internal replay cohort (101 paired tumor/normal). 8-gene subset lacks TOP2A/EPAS1 + M-status → sanity only. |
| `gse40435_expanded.csv` | same GSE40435 | public, no login | `data/build_gse40435_expanded.py` | Expanded microarray subset — still platform-saturated on single gene. |
| `gse53757_ccrcc.csv` | **GEO GSE53757** (Affymetrix HG-U133 Plus 2.0; von Roemeling et al. 2014, PMID 24571782) | public, no login | `data/build_gse53757.py` | **PhL-6 third independent cohort.** Stage 1-2 vs 3-4 AUROC 0.714 (PASS); tumor-vs-normal platform saturation (FAIL). |
| `brca_tumor_normal.csv` | TCGA-BRCA (STAR TPM) via GDC-Xena Hub | public, no login | `data/build_tcga_brca.py` | **PhL-5 cross-cancer negative control.** TOP2A − EPAS1 fails on BRCA as predicted → ccRCC-specificity confirmed. |
| `luad_tumor_normal.csv` | TCGA-LUAD (STAR TPM) via GDC-Xena Hub | public, no login | `data/build_tcga_luad.py` | Phase E platform-generalisation evidence (lung adenocarcinoma). 0 survivors as expected for tumor-vs-normal single-gene-dominated task. |
| `immotion150_ccrcc.csv` | **IMmotion150 Phase-2 trial** RNA-seq companion data via Gene Expression Omnibus / supplementary (McDermott et al. 2018, PMID 29867230) | public supplementary data | `data/build_immotion150.py` | **Headline external replay.** n=263, PFS endpoint, log-rank p=0.0003, HR=1.36, C=0.601. Same TOP2A − EPAS1 score passes. |
| `cptac3_ccrcc.csv` | **CPTAC-3 ccRCC proteogenomic** via PDC (Clark et al. 2019, PMID 31675502) | public, no login (PDC open tier) | `data/build_cptac3_ccrcc.py` | Phase E proteomic probe. Protein-level TOP2A − EPAS1 sanity check. |

## Sanity / integrity

Every CSV listed above is hashed in `data/SHA256SUMS` (committed SHA-256
over the file contents). A reviewer can run:

```bash
cd data && shasum -a 256 -c SHA256SUMS
```

and any byte-level modification will show `FAILED`. Each pre-registration
YAML in `preregistrations/*.yaml` binds to the repo state at commit time
via `emitted_git_sha` — which commits `data/SHA256SUMS` atomically with
the YAML — so any data edit *without* a matching YAML revision is
detectable via `make prereg-audit`.

## What this is NOT

- **Not protected or controlled-access data.** No dbGaP, no TCGA
  controlled-access subset, no Sentieon-licensed VCFs, no patient
  identifiers. All CSVs here are derived from publicly downloadable
  summarised expression matrices and phenotype tables.
- **Not original cohort data.** Every row is a re-packaging of
  publicly available primary sources (TCGA STAR-TPM via GDC-Xena, GEO
  series matrices, IMmotion150 supplementary RNA-seq). This submission
  does not collect, generate, or distribute any de novo biological
  data.
- **Not a redistribution of copyrighted material.** Authorship +
  citation attribution for the upstream publications is in
  `docs/methodology.md §1` and `docs/survivor_narrative.md §Citations`.
  The CSVs themselves are derived summaries; the primary source
  publications are the citeable works.

## How to rebuild any CSV from scratch

```bash
# Example: rebuild kirc_metastasis_expanded.csv from the upstream Xena release
python data/build_tcga_kirc_expanded.py \
    --out data/kirc_metastasis_expanded.csv

# Sanity check against the committed hash
shasum -a 256 -c <(grep 'kirc_metastasis_expanded' data/SHA256SUMS)
```

Each `data/build_*.py` script is self-contained and uses only `pandas`,
`requests`, `numpy`. Offline-runnable if the upstream file is cached
locally.

## Cross-references

- `README.md §Hackathon compliance` — the submission-level statement.
- `docs/methodology.md §1` — the dataset-strategy narrative.
- `data/SHA256SUMS` — the hash manifest.
- `preregistrations/*.yaml` — every hypothesis binds its
  `emitted_git_sha` to a repo state that commits `data/SHA256SUMS`
  atomically with the YAML.
- `Makefile` target `prereg-audit` — machine-verifies the tamper-
  evidence chain across all 28 YAMLs.
