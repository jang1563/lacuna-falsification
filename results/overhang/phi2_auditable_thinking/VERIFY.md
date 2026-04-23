# PhI-2 audit chain — how a reviewer verifies a Skeptic call

This directory demonstrates the pattern: **the Skeptic's reasoning
trace is part of the pre-registration artefact**, not a discarded
summary. Opus 4.7 made `thinking.display: "omitted"` the default;
this pipeline explicitly sets `"summarized"` so the reasoning is
retained and hashed.

## This specific call

- **Candidate**: `0.0986*(TOP2A - EPAS1) + 0.1606`
- **Dataset**: TCGA-KIRC metastasis M1 vs M0 (n=505, 45 genes)
- **Timestamp (UTC)**: 20260423T150624Z
- **Model**: claude-opus-4-7
- **Thinking display**: summarized (explicitly set; 4.7 default is 'omitted')
- **Verdict**: PASS
- **Thinking trace**: [`20260423T150624Z_thinking_099035e0c3ef5310.md`](20260423T150624Z_thinking_099035e0c3ef5310.md)
- **SHA-256 (first 16 hex)**: `099035e0c3ef5310`
- **Thinking char count**: 803

## How to verify

```bash
# 1. Inspect the audit manifest — verdict + hash pointer
jq . 20260423T150624Z_audit_099035e0c3ef5310.json

# 2. Recompute the thinking-trace hash locally
python3 -c "import hashlib; print(hashlib.sha256(open('20260423T150624Z_thinking_099035e0c3ef5310.md','rb').read()).hexdigest()[:16])"
# → should match the SHA-256 prefix above

# 3. Confirm the git log shows this file has never been modified:
git log -p 20260423T150624Z_thinking_099035e0c3ef5310.md   # should show exactly one commit (initial)
```

If the hash matches AND git history shows a single commit, the
reasoning trace a reviewer is reading is the same one Opus 4.7
emitted at inference time.

## Why this matters for AI-for-Science

Anthropic's Opus 4.7 launch calls out *"devises ways to verify its
own outputs before reporting back"* as the load-bearing capability.
For scientific provenance, that claim is only useful if the
verification *reasoning* itself can be read by a later reviewer.

Without explicit `display: "summarized"` (4.7 default is `"omitted"`),
the model's reasoning trace is silently discarded after inference.
This pipeline restores it, hashes it, and commits it as an artefact
alongside the verdict — extending the tamper-evidence chain from
data → decision to data → decision → **decision's reasoning**.

The pattern generalises: any Skeptic call in the falsification loop
can be wrapped with the same persistence; the thinking trace then
becomes a first-class citizen of the pre-registration artefact set.
