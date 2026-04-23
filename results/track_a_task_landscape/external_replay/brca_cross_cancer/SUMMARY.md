# PhL-5 — BRCA cross-cancer generalization probe (pre-registered negative control)

**Pre-registration:** `preregistrations/20260423T224229Z_phl5_brca_cross_cancer_generalization.yaml`
(committed at `3c8345f`, 2026-04-23 22:42 UTC, **BEFORE** this probe ran).

**Predicted outcome:** FAIL.
**Observed outcome:** FAIL. ✅ Prediction confirmed.

## Question

Does the ccRCC-validated 2-gene law `TOP2A − EPAS1` classify TCGA-BRCA
tumor-vs-normal as a pre-registered negative control? The biological
prediction was NO: EPAS1 / HIF-2α is a canonical ccRCC driver
(VHL-loss → HIF stabilization), but it is NOT a lineage-defining
driver in breast cancer. TOP2A is a general proliferation marker
elevated in virtually all tumors.

## Result

On TCGA-BRCA (n=1226, 1113 tumor / 113 normal):

| Gate test | Value | Threshold | Pass |
|---|---|---|---|
| Law AUROC (`TOP2A − EPAS1`) | 0.978 | — | — |
| Best single-gene AUROC (sign-invariant) | 0.969 | — | — |
| `delta_baseline` | **+0.009** | **> +0.05** | ❌ |
| `perm_p` | < 0.001 | < 0.05 | ✅ |
| `ci_lower` | 0.964 | > 0.6 | ✅ |
| `decoy_p` | < 0.001 | < 0.05 | ✅ |

**Verdict: FAIL on `delta_baseline` — matches the pre-registered prediction.**

The compound score carries negligible (+0.009) incremental AUC over
the best single gene. On BRCA, this best single gene is most likely
TOP2A itself (elevated in virtually all tumors), meaning the
"compound" is essentially TOP2A with EPAS1 contributing noise. The
+0.05 threshold was set before any fit and it binds exactly as
designed: the gate rejects "compound laws that are secretly
single-gene classifiers".

## Interpretation

This is the **pre-registered negative control at the cross-cancer
level**. If the 2-gene law had passed BRCA as easily as it passes
ccRCC metastasis, that would have been evidence the law was generic
proliferation (elevated-TOP2A-in-any-tumor), not the ccA/ccB ccRCC
subtype axis. The gate failing BRCA with `delta_baseline = +0.009`
**reinforces** the ccRCC-specific interpretation in
`docs/survivor_narrative.md`: the biology is specifically the
proliferation-vs-HIF-2α axis of Brannon 2010 / ClearCode34, not a
universal tumor signal.

## Why this counts as a pre-registered artefact

The prereg YAML was committed at `3c8345f` before
`src/phl5_phl6_generalization_probes.py` was written or run. The
YAML explicitly stated `expected_verdict: FAIL` and labelled this as
`negative_control: true`. The outcome matches. Git log proves the
order. This is the same tamper-evidence discipline as PhL-1's SLC22A8
cross-cohort FAIL, just at a different level: PhL-1 kills the
pipeline's own downstream proposal on a same-disease cohort; PhL-5
confirms the law does not overgeneralize across disease boundaries.

## Submission narrative use

- **Finding 1 of `docs/headline_findings.md`**: add PhL-5 as the
  "cross-cancer specificity" validation alongside IMmotion150
  (same-disease cross-cohort replay). The 2-gene law now has four
  committed pre-registered verdicts:
  - TCGA-KIRC metastasis (PASS, AUROC 0.726, +0.069)
  - IMmotion150 Phase-2 PFS (PASS, HR 1.36, log-rank p=0.0003)
  - TCGA-BRCA T-vs-N (**FAIL** — PhL-5, ccRCC-specific)
  - GSE53757 T-vs-N + stage secondary (**mixed** — see PhL-6)
