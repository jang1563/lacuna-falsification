---
name: pre-register-claim
description: "Locks a falsifiable biological-law claim and its kill-test thresholds into a SHA-tagged YAML pre-registration BEFORE any fit runs, by wrapping `src/preregistration.py emit-one`. TRIGGER when: the user says 'pre-register this', 'lock this claim', 'commit the fail criteria', 'what would falsify this?', 'write a pre-reg YAML for X', or hands you a candidate law family that has not yet been written to `preregistrations/`; the user is about to run PySR / falsification_sweep and wants the contract committed first; the user is replicating onto a new cohort and needs a separately-pre-registered survival or replay gate (use `kill_tests_override`). SKIP when: a YAML for this `hypothesis_id` already exists in `preregistrations/` (the script is idempotent — re-emit is a no-op, just report the existing path); the user wants to RUN the gate (that is `falsification-gate`); the user wants to PROPOSE a new law family from scratch (that is the Proposer subagent in `.claude/agents/proposer.md`)."
allowed-tools: Read, Grep, Bash, Write
---

# Pre-register a claim — emit a tamper-evident YAML before the fit

You are invoking the Lacuna pre-registration emitter. A pre-registration
is a committed YAML in `preregistrations/` that pins the hypothesis, its kill
tests, and the active git SHA *before* any data is touched. Once committed,
any subsequent edit shows up in `git log -p` on the file — that is the
tamper-evidence audit trail.

## What this skill does

Given a candidate law family, write **one** YAML to `preregistrations/` via
`python src/preregistration.py emit-one --family-json <tmp>.json --out
preregistrations/`. The YAML pins the 5-test gate thresholds (or a
hypothesis-specific override), the analyst, the data cutoff date, and the
current `emitted_git_sha`.

You do NOT run the gate itself. That is `falsification-gate`. Pre-registration
is the contract step; gating is the verdict step. Keeping them in separate
skills is what prevents the gate's thresholds from being silently re-tuned to
match observed metrics.

## Contract

### Input — family JSON shape

The invoking turn must hand you a Python `dict` (or describe the fields and
let you assemble one). Required fields:

```json
{
  "template_id": "top2a_minus_epas1",
  "name": "Proliferation minus HIF-2alpha",
  "symbolic_template": "TOP2A - EPAS1",
  "initial_guess": "TOP2A - EPAS1",
  "biological_rationale": "Proliferation running ahead of HIF-2alpha differentiation predicts metastasis (ccA/ccB axis).",
  "target_features": ["TOP2A", "EPAS1"],
  "expected_verdict": "PASS",
  "dataset": "tcga_kirc_metastasis_45g"
}
```

Optional — used when the hypothesis is NOT a binary classification:

```json
{
  "kill_tests_override": [
    {"name": "logrank_median_split", "statistic": "two_sided_logrank_p", "threshold": "< 0.05"},
    {"name": "cox_hr_per_z", "statistic": "cox_hazard_ratio_per_z", "threshold": "> 1.2 OR < 0.83"},
    {"name": "harrell_c_index", "statistic": "concordance_index_test", "threshold": "> 0.55"}
  ]
}
```

If the user gives you a natural-language hypothesis (e.g. "high TOP2A relative
to EPAS1 should predict ccRCC metastasis"), assemble the JSON yourself, then
**confirm every field with the user before writing**. Never invent
`expected_verdict` — ask. A pre-reg with a guessed expected verdict is not a
pre-reg.

### Algorithm

1. Read the schema in `src/preregistration.py::_emit_yaml` to confirm field
   names match this SKILL.md. If the schema has drifted, STOP and report.
2. Check `preregistrations/` for an existing YAML with the same
   `hypothesis_id` (= the slugified `template_id` or `name`). If one exists,
   the script is idempotent — return the existing path and STOP. Do not
   overwrite.
3. Write the assembled family dict to a temp file (`/tmp/<hid>.json`).
4. Run, from the repo root:

   ```bash
   python src/preregistration.py emit-one \
     --family-json /tmp/<hid>.json \
     --out preregistrations/ \
     --analyst "<user-supplied analyst label>" \
     --data-cutoff "<YYYY-MM-DD of the data snapshot>"
   ```

5. Capture stdout (JSON), parse the `written` path, and run
   `git log -1 --format=%H -- <yaml_path>` to confirm the file is
   under git tracking. If not yet committed, instruct the user to
   `git add <yaml_path> && git commit -m "[N] pre-register <hid>"` so the
   tamper-evidence chain is closed.
6. Append a one-line entry to `results/live_evidence/skill_verdicts.jsonl`
   with `{"event": "preregistered", "hypothesis_id": ..., "yaml_path": ...,
   "emitted_git_sha": ..., "timestamp_utc": ...}`. Use the same JSONL the
   `falsification-gate` skill writes to — one log, two event types.

### Output

Return to the caller a single JSON object:

```json
{
  "hypothesis_id": "top2a_minus_epas1",
  "yaml_path": "preregistrations/20260425T180000Z_top2a_minus_epas1.yaml",
  "emitted_git_sha": "<12-char sha>",
  "kill_tests": ["label_shuffle_null", "bootstrap_stability",
                 "baseline_comparison", "confound_only", "decoy_feature_test"],
  "next_step": "Run falsification-gate on this hypothesis once you have the metric bundle."
}
```

## Role boundary (important)

This skill writes the contract. It does NOT:

- Decide pass/fail (that is `falsification-gate`).
- Choose the hypothesis (that is the Proposer subagent
  `.claude/agents/proposer.md`).
- Modify thresholds in `src/lacuna/falsification.py`. If the user
  wants different thresholds, they must use `kill_tests_override` and accept
  that the override is hypothesis-specific — it does not retroactively change
  the binary-classification 5-test gate.

The `falsification-gate` skill reads the YAML this skill emits via the
`prereg_id` field. Composition: invoke `pre-register-claim` first, capture
the returned `hypothesis_id`, then invoke `falsification-gate` with that id.

## Why this skill exists

> *Pre-registration must bite on both sides.*

The same gate that rejected the textbook HIF-axis law and the negative-control
housekeeping contrast also accepted `TOP2A − EPAS1`. Both decisions cite a
YAML in `preregistrations/` whose `emitted_git_sha` predates the fit. Without
this skill, that contract is a manual ritual; with it, it is a single
natural-language command.

## Example invocation

User: *"Pre-register this: high MKI67 relative to EPAS1 should predict ccRCC
metastasis. I expect this to PASS. Use the default 5-test gate. Data cutoff
2026-04-22, analyst 'lacuna-team'."*

Skill response (after one confirmation round):

```json
{
  "hypothesis_id": "mki67_minus_epas1",
  "yaml_path": "preregistrations/20260425T180000Z_mki67_minus_epas1.yaml",
  "emitted_git_sha": "<sha>",
  "next_step": "Run falsification-gate once metrics are computed."
}
```

## References

- `src/preregistration.py` — emitter implementation. CLI: `emit`, `emit-one`,
  `validate`, `audit`.
- `docs/methodology.md §3` — what each kill test measures and why thresholds
  were set where they were.
- `preregistrations/*.yaml` — every existing pre-reg, one file per hypothesis.
- `.claude/skills/falsification-gate/SKILL.md` — the verdict skill that
  consumes these YAMLs.
