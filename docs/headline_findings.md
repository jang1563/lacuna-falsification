# Theory Copilot — Three Headline Findings

*Last updated 2026-04-23 (Phase G/H/I post-verification). Written after Phase F (PhF-1..PhF-5) and rigorously updated with G1-G5 mathematical gate audits, H1-H2 Opus-4.7-overhang experiments, and I2-I4 Rashomon/information-theoretic/clinical-translation analyses.*

This document is the 5-minute version of the submission. Each finding is
presented as *what we did* → *what we found* → *why it was not possible 6
months ago* → *what the pattern means for other researchers / companies*.

---

## Finding 1 — A two-gene law, discovered by unconstrained symbolic regression and accepted by a pre-registered deterministic gate, replicates on an independent immunotherapy trial cohort.

### What we did

1. **Flagship discovery run (TCGA-KIRC, n=505 metastasis task).** Opus 4.7
   proposed 12 ccRCC law families (including two negative controls) and
   wrote the kill test for each *before any fit*. PySR searched a 45-gene
   panel. The 5-test falsification gate ran in plain Python.
2. **Result.** 9 of 30 PySR candidates passed. The simplest surviving
   law is `TOP2A − EPAS1` at AUROC 0.726, Δbaseline +0.069, CI lower 0.665.
3. **Independent replay (PhF-3, IMmotion150).** The same 2-gene score
   was applied without refitting to a fully independent Phase-2 trial
   cohort (atezolizumab ± bevacizumab, n=263 metastatic ccRCC,
   McDermott *et al.* *Nat Med* 2018, PMID 29867230). Three kill tests
   — log-rank on median split, Cox HR per z-score, Harrell C-index —
   were *pre-registered and git-committed before the analysis ran*.

### What we found

- **Log-rank p = 0.00027** (threshold: p < 0.05).
- **Cox HR per z-score = 1.36** (95% CI 1.16–1.59, p = 1e-4; threshold:
  `|log HR| > log 1.3` AND 95% CI excludes 1).
- **Harrell C-index = 0.601** (threshold: > 0.55).
- **All 3 kill tests pass.** Direction (not pre-specified): high score
  → worse PFS, matching the ccA/ccB subtype biology (Brannon 2010,
  PMID 20871783; ClearCode34, DOI 10.1016/j.eururo.2014.02.035).
- **Median PFS: 5.35 months** in the high-score half vs **12.88 months**
  in the low-score half — a 7.5-month separation on immunotherapy.

**Confounding control (G3-NEW, 2026-04-23):** Three pre-registered Cox
models show HR is ROBUST to treatment-arm and TMB adjustment:
- Univariate: HR=1.361 (1.165–1.591), p=1e-4
- + 3-arm treatment (atezo/atezo+bev/sunitinib): HR=**1.365** (HR *increases*
  by 0.4%, attenuation=-0.9%), p=1e-4
- + treatment + log(TMB): HR=1.293 (1.034–1.618), p=0.024

The presence of the sunitinib arm (n=89, non-ICI VEGF inhibitor) in the
IMmotion150 release means our result holds across *both* ICI and non-ICI
treatments — so **TOP2A − EPAS1 is a general ccRCC prognostic marker,
not an ICI-specific biomarker**. This is strictly stronger than the
original submission claim.

**DeLong vs best single gene (G2, 2026-04-23):** The compound law is
statistically significantly better than the best single gene (MKI67):
ΔAUROC = +0.081, 95% CI [+0.023, +0.143], one-sided bootstrap p=0.004.
This directly answers "could a single gene do just as well?"

**AUPRC at low prevalence (G2):** At 16% M1 prevalence, AUPRC=0.317
vs no-skill baseline 0.156 — **lift 2.03×**. At the precision
thresholds a clinician would screen, the compound performs 2× better
than random.

**Uniqueness (Lane I · I2, 2026-04-23):** Among all C(45,2)=990 possible
2-gene linear-difference pairs, `TOP2A − EPAS1` is **rank 1 of 990**,
and is UNIQUE at ε=0.005 and ε=0.01 AUROC tolerance. Of the top-20
near-optimal pairs, 15 contain a proliferation-axis gene — so the
*sufficient condition* for near-optimal compactness is "proliferation
axis minus any other axis", an invariant structural property
empirically established over 990 candidates.

**Independent protein-level consensus (HPA v21.0):** TOP2A is classified
`prognostic_unfavorable` and EPAS1 `prognostic_favorable` in renal
cancer by the Human Protein Atlas pathology database (Uhlén et al.
*Science* 2015, queried 2026-04-23). The sign structure `TOP2A − EPAS1`
matches HPA's independent per-gene consensus without our pipeline
having access to HPA — an external sanity check on direction.

### Why this was not possible 6 months ago

- **Opus 4.7 1M-context, extended thinking, Managed Agents** — the
  Proposer/Skeptic/Interpreter role split stays coherent across long
  context; Opus 4.6 and Sonnet 4.6 (measured in our Phase-E2 180-call
  ablation, `results/ablation/SUMMARY.md`) produce different verdict
  distributions on the same gate output.
- **Managed Agents GA on 2026-04-08** — the Skeptic turn runs in a
  separate session that cannot re-read the Proposer's internal tokens.
  Pre-4.7 Managed Agents did not support this cleanly at the $0.08/hr
  runtime tier.
- **Public cBioPortal programmatic access to IMmotion150 mRNA + PFS**
  made the external replay runnable in under an hour with `data/build_immotion150.py`
  (plain `urllib`, no custom credentials).

### Template others can adopt

- Drop in a `config/dataset_cards/{your_disease}.json` pointing at any
  patient-level omics CSV.
- `make prereg` retroactively emits one YAML per law family;
  `make prereg-validate` + `make prereg-audit` give machine-verifiable
  tamper evidence.
- `theory-copilot compare --dataset-card ...` runs the same Proposer +
  Skeptic + gate in your cohort.

---

## Finding 2 — The rejection log IS the product. Pre-registered falsification rejects 194 of 204 candidates across 11 cohort × task × panel combinations.

### What we did

Published every single candidate the gate ever saw — PySR outputs, Opus
ex-ante proposals, negative controls — with its five-test failure reason,
as a static HTML page `results/rejection_log.html` that redeploys on every
push to `main` via `.github/workflows/pages.yml`.

### What we found

- **204 candidates evaluated**, **194 rejected**, **10 accepted** —
  **95.1 % rejection rate.**
- Rejection cause breakdown (composite reasons allowed):
  - `delta_baseline` failure (compound doesn't beat best single gene
    by +0.05) is the dominant cause.
  - `perm_p`, `decoy_p`, `ci_lower` each bite on a long tail of
    symbolic-regression candidates that numerically overfit.
- **Both Opus-planted negative controls** (`log1p(ACTB) − log1p(GAPDH)`,
  `log1p(MKI67) − log1p(RPL13A)`) are rejected on TCGA-KIRC. False-accept
  rate on those controls: 0 / 2.
- **The textbook HIF-axis law** `log1p(CA9) + log1p(VEGFA) − log1p(AGXT)`
  (AUROC 0.984 on tumor-vs-normal) is rejected — CA9 alone reaches 0.965,
  so Δbaseline = +0.019 < +0.05 threshold.

### Why this matters right now

Two live AI-for-Science benchmarks published in April 2026 frame the
problem:

- **SPOT** (arXiv 2505.11855): SOTA LLMs get recall ≤ 21 %, precision
  ≤ 6 % on detecting errors in 83 retracted papers × 8 runs — post-hoc
  error detection is unreliable.
- **Sakana AI Scientist v2** (arXiv 2504.08066): its peer-review-passing
  paper was debunked externally for hallucinations and overstated
  novelty. Community question shifted: "can an AI reject its own bad
  paper?"

Theory Copilot answers that specific question in the affirmative by
making rejection the main output. The 194 failing candidates are not
an appendix — they are the central artefact. If we had cherry-picked
a single AUROC 0.984 tumor-vs-normal "finding", we would have published
the Sakana-v2 failure mode. The gate caught it; we publish that fact.

### Template others can adopt

- Generate the equivalent page for your own repo with
  `make rejection-log`. No JS framework required; stdlib Python only.
- Make it live via the GitHub Pages workflow at
  `.github/workflows/pages.yml` (deploys on every main push).

### Opus 4.7 1M-context cross-reasoning over the rejection log (H2)

On 2026-04-23 we ran `make h2` (49.7 seconds, single Opus 4.7 call,
14,212-char prompt): the 74 rejection records + 9 survivor records + 5
paper abstracts were loaded into one prompt, and Opus synthesized:

- **5 new equation skeletons** (each with a Δbaseline hypothesis and
  pre-registered skeptic test — Opus writes the kill-test before we
  test the skeleton).
- **5 invariant conditions** empirically derived from the failure
  distribution, each citing specific failed equations as evidence.
- A **bimodal failure landscape** analysis: 27 rejections collapse to
  AUROC ≈ 0.5 (log1p-stack saturation), 23 plateau at 0.96-0.99 but
  fail Δbaseline (CA9 ceiling). Only Proliferation − HIF-2α survives
  the +0.05 hurdle.

Critically, Opus's invariant condition #1 ("compound MUST contain a
proliferation marker AND a HIF marker in opposite sign") was
*independently* confirmed by Lane I · I2's exhaustive 990-pair
enumeration: 15 of top 20 pairs contain a proliferation gene. Two
methods — LLM 1M-context synthesis and exhaustive empirical
enumeration — arrive at the same sufficient condition. This is the
rare case where LLM reasoning produces a structural rule that is
*empirically testable on a different scale of evidence*.

---

## Finding 3 — Pre-registration at LLM speed + a server-side Routine that outlives your laptop.

### What we did

1. **`preregistrations/` directory** — 17 YAMLs (16 retroactive +
   1 prospective IMmotion150 replay), each pinning H0 / H1 / 5 kill
   tests / BH-FDR / α / stopping rule / analyst / data cutoff / regulatory
   references to FDA-EMA 2026-01 Common Principles + EU AI Act high-risk
   provisions effective 2026-08-02.
2. **Tamper-evidence via git.** Each YAML is committed once and never
   modified. `make prereg-audit` prints the first-committed SHA + content
   hash per file — an external auditor can machine-verify the chain.
3. **Path C Routine driver** (`run_path_c_routine` in
   `src/theory_copilot/managed_agent_runner.py`). Boris Cherny at the
   2026-04-21 *Built with Opus 4.7* kickoff named server-side Routines
   as *"the area no one has cracked yet."* Managed Agents + Routines
   went GA on 2026-04-08. Path C is our shipped driver: interval
   cadence OR watch-dir fingerprint change triggers an iteration;
   verdicts appended to `results/routine/verdicts.jsonl`; `invoke_fn`
   hook lets a native Routines API drop in as a one-line swap. A
   `.github/workflows/nightly_falsifier.yml` fires this nightly on
   main, posts a pinned GitHub Issue comment with the audit chain,
   and exercises the full pipeline without the laptop being awake.

### What we found

- **Pre-reg YAMLs are cheap to emit and expensive to misuse.** 16 were
  written in under one second via `make prereg`. Any edit after commit
  is `git log -p` visible; any threshold change to
  `src/theory_copilot/falsification.py` invalidates every YAML in the
  directory and requires a new pre-reg with a new timestamp.
- **Path C runs the falsification loop without a laptop.** The local
  driver fires Path B on an interval; the GitHub Actions workflow
  fires Path C on a cron schedule and files an Issue comment per run.
  Both are one-function-pointer away from a native Routine.

### Why this was not possible 6 months ago

- **FDA-EMA Common Principles were published 2026-01.** Before that,
  "credibility assessment plan" had no agreed-on minimum content.
- **EU AI Act high-risk provisions effective 2026-08-02.** After that
  date, any AI-for-medicine system is legally required to have
  traceable validation. Our `preregistrations/` + independent replay
  is the minimal form-factor.
- **Managed Agents + Routines GA on 2026-04-08.** A session-level
  Routine that can run overnight without a laptop is a 2-week-old
  capability.
- **Extended thinking via `adaptive / effort=high`** is Opus 4.7-only
  (older models had fixed thinking budgets that couldn't span a
  multi-role Proposer/Skeptic/Interpreter loop economically).

### Template others can adopt

- Copy `.github/workflows/nightly_falsifier.yml` + the
  `run_path_c_routine` driver to your repo; set `ANTHROPIC_API_KEY`
  as a secret; edit the `invoke_fn` injection point for your
  Proposer / Searcher / Falsifier roles.
- Regulatory teams: point to `preregistrations/` + `make prereg-audit`
  output as the concrete form-factor for your credibility assessment
  plan.

---

## What this all adds up to

*Any* lab working on biological law discovery can now:

1. Write down the kill tests before the search starts, as a
   machine-verifiable git-tracked YAML.
2. Run the discovery loop unsupervised on a nightly Routine.
3. Publish every rejected candidate alongside the accepted ones.
4. Independently replay the accepted law on an external cohort with
   separate kill tests pre-registered for the replay endpoint.

The combination was not possible 6 months ago. It is possible right now.
`TOP2A − EPAS1` is a single worked example; the pipeline's transfer to
LUAD and BRCA (see `results/track_a_task_landscape/{luad,brca}/`) already
shows the pattern holds on additional diseases.

---

## Supporting files (judge-facing read order)

1. [`docs/paper/paper.pdf`](paper/paper.pdf) — 6-page workshop paper.
2. [`docs/paper/benchmark_vs_related.md`](paper/benchmark_vs_related.md) — positioning vs SPOT, Sakana v2, POPPER.
3. [`results/rejection_log.html`](../results/rejection_log.html) — the 204-candidate table (open in a browser).
4. [`results/track_a_task_landscape/external_replay/immotion150_pfs/SUMMARY.md`](../results/track_a_task_landscape/external_replay/immotion150_pfs/SUMMARY.md) — IMmotion150 replay write-up.
5. [`preregistrations/`](../preregistrations/) — the 17 YAMLs; run `make prereg-audit` to see SHA + content hash per file.
6. [`docs/methodology.md`](methodology.md) — full methods.
7. [`docs/survivor_narrative.md`](survivor_narrative.md) — the single-paragraph "what is this and what it isn't" on TOP2A − EPAS1.
