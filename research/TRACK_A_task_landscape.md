# Research Track A — Task Landscape

**Goal:** find the ccRCC classification task (or cohort) where compound
multi-gene laws genuinely beat single-gene baselines by more than the
pre-registered +0.05 `delta_baseline` threshold.

**Scientific question:** is the +0.029 incremental ceiling observed on
tumor-vs-normal and stage (Tier 1 + Tier 2) a property of the *task*
or a property of *ccRCC*? If we pick a task that is neither saturated
by CA9 nor linear in one gene, can the 5-test gate find a survivor?

**Why this matters:** A single positive survivor turns the artifact
from "falsification worked on degenerate tasks" into "falsification
worked, and when a task is solvable we report the law that won." The
narrative wins either way, but a survivor is a much stronger demo.

---

## File ownership (exclusive write)

| Path | Role |
|---|---|
| `data/build_tcga_kirc_survival.py` | Survival (alive ≥5yr vs dead) task builder |
| `data/build_tcga_kirc_metastasis.py` | M0 vs M1 task builder |
| `data/kirc_survival.csv`, `data/kirc_metastasis.csv`, `data/kirc_*.csv` for new tasks | Derived task CSVs |
| `src/task_landscape.py` | Per-task AUROC driver |
| `src/track_a_*.py` | Any Track-A-specific helpers |
| `config/task_definitions.json` | Task registry (id, csv, label column, genes) |
| `research/TRACK_A_*.md` | This brief + progress notes |
| `results/track_a_task_landscape/**` | All Track A outputs |

**Read-only for this track:** everything under `src/lacuna/**`,
`src/pysr_sweep.py`, `src/falsification_sweep.py`, `data/kirc_tumor_normal.csv`,
`data/kirc_stage.csv`, `data/gse40435_kirc.csv`. If a change in those is needed,
open `HANDOFF_to_shared.md` rather than editing directly.

---

## Task list (priority order)

1. **Survival (5-year overall survival)** — TCGA-KIRC clinical phenotype
   has `days_to_death`, `days_to_last_follow_up`, `vital_status`. Label
   as disease (dead before 5yr) vs control (alive ≥5yr; censored <5yr
   excluded). Known ccRCC survival signatures (ClearCode34, 11-gene
   proliferation panels, m6A risk score) beat single-gene AUROC by
   +0.08–0.15 in published validation. This is the most likely survivor.
2. **Metastasis M0 vs M1** — `pathologic_M.tnm_edition7` in the phenotype
   table. Smaller cohort (~60 M1 samples in TCGA-KIRC) but published
   7-gene collagen signature shows AUROC 0.74 vs CA9 ~0.62.
3. **Stage I-II vs III-IV** — already done in Tier 2 (see
   `results/tier2_run/`). Included here for reference; no new work unless
   the gene set expands.
4. **Grade (Fuhrman)** — *attempted earlier, TCGA star_tpm clinical has
   `tumor_grade.diagnoses = "Not Reported"` for all rows*. Skip unless
   a replacement grade source is located (cBioPortal TCGA-KIRC clinical,
   or UCSC Xena TCGA-KIRC.grade.tsv if available).
5. **Expanded gene set** — Give PySR the HIF hallmark gene set (~200
   genes) instead of 11. This is a feature-space expansion rather than
   a new task, but changes the search behaviour materially. Run
   alongside task 1.

---

## Execution steps (for this track's session)

### Step A1 — Pull latest + verify tool chain
```bash
cd lacuna-falsification
git pull --rebase origin main
git status --short         # expect: nothing under src/task_* or data/kirc_survival*
make audit                 # must pass
```

### Step A2 — Download + build survival CSV

Write `data/build_tcga_kirc_survival.py`:

- Reuse the LinkedOmics / GDC-Xena download in `data/build_tcga_kirc.py`
  for the expression matrix. Merge with the already-downloaded
  `.tmp_geo/gdc/TCGA-KIRC.clinical.tsv.gz` phenotype file that has
  `days_to_death`, `days_to_last_follow_up`, `vital_status`.
- Derive the binary label:
  - `disease` (dead at ≤ 5yr): `vital_status == "Dead"` AND `days_to_death
    <= 1825`
  - `control` (alive ≥ 5yr): `vital_status == "Alive"` AND
    `days_to_last_follow_up >= 1825`
  - Exclude everyone else (right-censored before 5yr).
- Output: `data/kirc_survival.csv` with the same column contract as
  `kirc_tumor_normal.csv`: `sample_id, label, age, batch_index,
  <gene columns...>`.
- Expected shape: ~300–400 samples after exclusions.

### Step A3 — Sanity check per-gene AUROC on survival task

- Use the existing inline pattern (see `results/RESULTS.md` Tier 1
  table) to report sign-invariant AUROC per gene on the survival task.
- Expected: the max single-gene AUROC will be substantially lower than
  CA9 on tumor-vs-normal (roughly 0.55–0.65). If that holds, compound
  laws have room to pass the +0.05 threshold.

### Step A4 — PySR sweep on survival task

Run on the same remote compute host as the Tier 1/2 sweep:

```bash
python src/pysr_sweep.py \
  --data data/kirc_survival.csv \
  --genes CA9,VEGFA,LDHA,NDUFA4L2,SLC2A1,ENO2,AGXT,ALB,CUBN,PTGER3,SLC12A3 \
  --proposals config/law_proposals.json \
  --standardize \
  --iterations 800 --n-populations 12 --population-size 40 \
  --seeds 1 2 3 --n-jobs 12 --maxsize 15 \
  --output results/track_a_task_landscape/survival_candidates.json
```

### Step A5 — Falsification + rename + ex-ante comparison

```bash
python src/rename_candidates.py \
  --input results/track_a_task_landscape/survival_candidates.json \
  --genes CA9,VEGFA,LDHA,NDUFA4L2,SLC2A1,ENO2,AGXT,ALB,CUBN,PTGER3,SLC12A3 \
  --proposals config/law_proposals.json \
  --output results/track_a_task_landscape/survival_candidates_named.json

python src/falsification_sweep.py \
  --candidates results/track_a_task_landscape/survival_candidates.json \
  --data data/kirc_survival.csv \
  --genes CA9,VEGFA,LDHA,NDUFA4L2,SLC2A1,ENO2,AGXT,ALB,CUBN,PTGER3,SLC12A3 \
  --covariate-cols batch_index \
  --n-permutations 500 --n-resamples 500 --n-decoys 100 \
  --output results/track_a_task_landscape/survival_falsification_report.json

# Also run Opus ex-ante laws on the survival task
python src/falsification_sweep.py \
  --candidates results/opus_exante/kirc_candidates.json \
  --data data/kirc_survival.csv \
  --genes CA9,VEGFA,LDHA,NDUFA4L2,SLC2A1,ENO2,AGXT,ALB,CUBN,PTGER3,SLC12A3,ACTB,GAPDH,RPL13A,MKI67 \
  --covariate-cols batch_index \
  --n-permutations 500 --n-resamples 500 --n-decoys 100 \
  --output results/track_a_task_landscape/survival_opus_exante_report.json
```

### Step A6 — Same pipeline on metastasis task (lower priority)

Use same tooling on `data/kirc_metastasis.csv` once built.

### Step A7 — Report

Write `results/track_a_task_landscape/SUMMARY.md` with:
- Per-task per-gene AUROC table
- Per-task survivor count
- Any genuine survivor's equation, metrics, and biological reading
- Compare the +0.029 ceiling across tumor/normal, stage, survival,
  metastasis: is it a constant, or does it shift with task?

---

## Commit rules

- Prefix commit messages with `[Sci-A]` or `[T-A]`.
- Commit within one hour of starting a work block.
- `make audit` before every push.
- Never touch the other track's directories.
- Never touch `src/lacuna/**` without a `HANDOFF_to_shared.md`
  request.
