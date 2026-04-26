#!/usr/bin/env python3
"""PhI-2 — Auditable thinking traces as falsification artefacts.

Opus 4.7 made a breaking change: `thinking.display` default shifted from
`summarized` (4.5/4.6) to `omitted` (4.7). Developers must explicitly set
`display: "summarized"` to retain the model's reasoning trace — otherwise
it is silently discarded.

This is directly aligned with Lacuna's pre-registration thesis:
a verdict is stronger when its *reasoning* is also committed to disk,
not just the final decision. This script shows the pattern on one
concrete Skeptic judgement of the TOP2A − EPAS1 survivor:

  1. Call Opus 4.7 Skeptic with `display: "summarized"` set explicitly.
  2. Save the verdict JSON + the FULL summarized thinking trace.
  3. Compute SHA-256 of the thinking trace — filename is hash-keyed so
     any subsequent edit invalidates the reference.
  4. Write a small VERIFY.md showing how a reviewer would audit the chain:
     (prereg YAML hash) → (verdict JSON hash) → (thinking trace hash).

The output directory mirrors the pre-registration convention: files are
committed once and never modified.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

OUT = REPO / "results" / "overhang" / "phi2_auditable_thinking"
OUT.mkdir(parents=True, exist_ok=True)


def _sha256_16(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run() -> dict:
    import anthropic

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[PhI-2] ANTHROPIC_API_KEY not set; aborting.", file=sys.stderr)
        sys.exit(2)

    metrics = json.loads((REPO / "results" / "ablation" / "candidate_metrics.json").read_text())
    bundle = metrics["top2a_minus_epas1"]
    prompt_system = (REPO / "prompts" / "skeptic_review.md").read_text()

    metric_fields = (
        "perm_p", "ci_width", "ci_lower", "law_auc", "baseline_auc",
        "delta_baseline", "delta_confound", "confound_auc",
        "decoy_p", "decoy_q95", "original_auc", "n_samples", "n_disease", "passes",
    )
    metrics_for_prompt = {k: v for k, v in bundle.items() if k in metric_fields}
    # Open-ended scientific review prompt that invites extended thinking
    # (4.7 adaptive mode decides when thinking is warranted by task difficulty;
    # short JSON-constrained prompts often skip thinking entirely).
    prompt_system = (
        "You are a rigorous scientific reviewer for a pre-registered "
        "biological law discovery pipeline. Think step by step through "
        "biology, statistics, and confounding before reaching a verdict.\n\n"
        + prompt_system
    )
    user_msg = (
        f"Candidate equation: {bundle['equation']}\n"
        f"Dataset: {bundle['dataset']}\n"
        f"Falsification metrics: {json.dumps(metrics_for_prompt, default=str)}\n\n"
        "Take time to reason carefully about: (a) whether the underlying "
        "biology makes mechanistic sense, (b) whether the metric values are "
        "marginal or robust, (c) what the most likely failure mode would be "
        "if this law did not generalize. Then output the JSON described "
        "in the system prompt."
    )

    ac = anthropic.Anthropic()
    print("[PhI-2] Calling Opus 4.7 Skeptic with thinking.display=summarized explicitly set...")

    # Opus 4.7 requires adaptive thinking. Crucially, `display: "summarized"`
    # must be set EXPLICITLY — 4.7 default is "omitted" (breaking change from
    # 4.5/4.6). This is the whole point of this script: 4.7 silently discards
    # reasoning traces unless the developer asks for them.
    with ac.messages.stream(
        model="claude-opus-4-7",
        max_tokens=16000,
        thinking={"type": "adaptive", "display": "summarized"},
        system=prompt_system,
        messages=[{"role": "user", "content": user_msg}],
    ) as stream:
        final = stream.get_final_message()

    text = ""
    thinking_text = ""
    for block in final.content:
        if block.type == "text":
            text += block.text
        elif block.type == "thinking":
            thinking_text += block.thinking

    # Persist thinking trace FIRST — before parsing verdict
    ts = _utc_now()
    thinking_bytes = thinking_text.encode("utf-8")
    thinking_hash = _sha256_16(thinking_bytes)
    thinking_path = OUT / f"{ts}_thinking_{thinking_hash}.md"
    thinking_path.write_text(thinking_text)

    # Parse verdict JSON
    start = text.find("{")
    end = text.rfind("}") + 1
    verdict = json.loads(text[start:end]) if start >= 0 and end > start else {"raw": text}

    # Record verdict with hash-chain pointer
    audit = {
        "timestamp_utc": ts,
        "candidate_equation": bundle["equation"],
        "dataset": bundle["dataset"],
        "model": "claude-opus-4-7",
        "thinking_display": "summarized (explicitly set; 4.7 default is 'omitted')",
        "verdict": verdict,
        "thinking_trace_file": thinking_path.name,
        "thinking_trace_sha256_16": thinking_hash,
        "thinking_trace_char_count": len(thinking_text),
        "reasoning_tokens": getattr(getattr(final, "usage", None), "input_tokens", None),
    }
    audit_path = OUT / f"{ts}_audit_{thinking_hash}.json"
    audit_path.write_text(json.dumps(audit, indent=2, default=str))

    # Write a VERIFY.md demonstrating the audit chain
    verify_path = OUT / "VERIFY.md"
    verify_path.write_text(_make_verify_md(audit, thinking_path.name, audit_path.name))

    print(f"[PhI-2] thinking trace ({len(thinking_text)} chars) → {thinking_path.name}")
    print(f"[PhI-2] SHA-256 prefix: {thinking_hash}")
    print(f"[PhI-2] verdict: {verdict.get('verdict', '?')}")
    print(f"[PhI-2] wrote audit chain to {OUT}")
    return audit


def _make_verify_md(audit: dict, thinking_name: str, audit_name: str) -> str:
    return f"""# PhI-2 audit chain — how a reviewer verifies a Skeptic call

This directory demonstrates the pattern: **the Skeptic's reasoning
trace is part of the pre-registration artefact**, not a discarded
summary. Opus 4.7 made `thinking.display: "omitted"` the default;
this pipeline explicitly sets `"summarized"` so the reasoning is
retained and hashed.

## This specific call

- **Candidate**: `{audit["candidate_equation"]}`
- **Dataset**: {audit["dataset"]}
- **Timestamp (UTC)**: {audit["timestamp_utc"]}
- **Model**: {audit["model"]}
- **Thinking display**: {audit["thinking_display"]}
- **Verdict**: {audit["verdict"].get("verdict", "?")}
- **Thinking trace**: [`{thinking_name}`]({thinking_name})
- **SHA-256 (first 16 hex)**: `{audit["thinking_trace_sha256_16"]}`
- **Thinking char count**: {audit["thinking_trace_char_count"]:,}

## How to verify

```bash
# 1. Inspect the audit manifest — verdict + hash pointer
jq . {audit_name}

# 2. Recompute the thinking-trace hash locally
python3 -c "import hashlib; print(hashlib.sha256(open('{thinking_name}','rb').read()).hexdigest()[:16])"
# → should match the SHA-256 prefix above

# 3. Confirm the git log shows this file has never been modified:
git log -p {thinking_name}   # should show exactly one commit (initial)
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
"""


if __name__ == "__main__":
    run()
