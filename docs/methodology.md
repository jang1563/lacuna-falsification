# Methodology

## Goal

This project operationalizes a workflow-first scientific discovery artifact.

The workflow is designed to answer one practical question:

**Can an Opus 4.7-centered loop propose compact law families, search over concrete equations, reject brittle candidates, and retain an interpretable law that survives holdout and falsification checks?**

## Workflow

1. **Dataset card**
   - Load a structured description of a disease-vs-normal dataset.
   - Keep the input contract simple: one CSV with sample labels, optional covariates, and numeric omics-derived features.
2. **Proposal layer**
   - Use an English prompt surface for law-family proposals, skeptic prompts, and final explanation prompts.
   - In this local scaffold the proposal layer is represented by `config/law_proposals.json`.
3. **Compact law search**
   - Enumerate low-order symbolic forms only.
   - Restrict the search to short equations so a judge can read the winning law directly.
4. **Ranking**
   - Rank by held-out AUROC first.
   - Break ties toward lower symbolic complexity.
5. **Falsification**
   - Run label-shuffle null checks.
   - Estimate bootstrap stability.
   - Compare against the best simpler single-feature baseline.
   - Compare against covariate-only signal.
6. **Promotion**
   - Select the highest-ranked surviving candidate.
   - Write a summary bundle with the equation, plot, top-candidate table, falsification report, session handoff, and replay command.
7. **Transfer check**
   - Run the same workflow on a second dataset.
   - Record whether the law family transfers, whether the workflow transfers, and where the second run is weak.

## Default Search Space

The scaffold uses compact templates only:

- `x`
- `x - y`
- `x + y`
- `x / (1 + y)`
- `(x - y) / (1 + x + y)`
- `log1p(x) - log1p(y)`

These are deliberately conservative. The goal is not to maximize fit at any cost but to preserve interpretability under demo conditions.

## Ranking And Reject Gates

The ranking priority is:

1. held-out AUROC
2. lower symbolic complexity
3. stronger bootstrap stability
4. lower confound dependence

A candidate is penalized or rejected when:

- its observed AUROC is too close to the label-shuffle null,
- bootstrap resampling frequently collapses or flips the effect,
- it adds little over the best single-feature baseline, or
- covariates alone explain nearly as much separation as the law.

## Local Validation Versus Final Hackathon Run

The repository includes deterministic synthetic datasets so the full workflow can run quickly and reproducibly offline.

For the judged hackathon artifact, replace `data/examples/*.csv` with public disease-vs-normal omics exports that match the same CSV contract. No code changes are required if the column names are updated in `config/datasets.json`.

## Safety And Framing

This repository defaults to the following scientific language:

- `candidate law`
- `empirical regularity`
- `mechanism hypothesis`
- `research-use-only`

It explicitly avoids claims about diagnosis, treatment recommendation, or universal biological laws.
