#!/usr/bin/env python3
"""G6 — Opus 4.6 vs 4.7 calibration on the Skeptic biology task.

Anthropic's published claim (Opus 4.7 model card, 2026-04-16):
    abstention on unknowns 61% (4.6 Adaptive) → 36% (4.7 Adaptive)
    accuracy ~unchanged.

We test whether this improvement transfers to our specific biology
skeptic task. E2 already has 60 Opus 4.7 calls on 6 candidates
(results/ablation/skeptic_model_sweep.jsonl). This script:

  1. Runs 60 matched calls on claude-opus-4-6 (same 6 candidates × 10 repeats).
  2. Compares verdict-calibration:
     - On gate=PASS candidates (strong_survivor): does 4.7 agree more confidently?
     - On gate=FAIL candidates (clean_reject): does 4.7 dissent (FAIL) more reliably?
     - On borderline candidates (borderline_reject, stress_test): does 4.7
       abstain (NEEDS_MORE_TESTS) more often where 4.6 over-commits?
  3. Writes results/ablation/opus_46_vs_47/ with SUMMARY.md + verdict JSONL.

This directly measures whether Opus 4.7's marketed calibration improvement
shows up on biology-reasoning tasks, not just the MMLU-style benchmarks
Anthropic cites.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Reuse the infrastructure from track_a_model_ablation
import track_a_model_ablation as aba

OUT = REPO / "results" / "ablation" / "opus_46_vs_47"
OUT.mkdir(parents=True, exist_ok=True)
JSONL_46 = OUT / "opus_46_sweep.jsonl"

MODEL_46 = "claude-opus-4-6"


def run_sweep(repeats: int = 10, workers: int = 4) -> None:
    """Run 60 calls: 6 candidates × 10 repeats on Opus 4.6."""
    # Opus 4.6 supports budget_tokens (only 4.7 removed it)
    # Inject the 4.6 thinking config into the shared module
    aba.THINKING_CONFIG[MODEL_46] = {"type": "enabled", "budget_tokens": 8000}

    # Load candidate metrics bundle (already precomputed by E2).
    # Structure: dict keyed by candidate name, each value is the bundle.
    candidate_metrics = json.loads(aba.METRICS_PATH.read_text())
    # Ensure each bundle has 'name' key matching its dict key (for _one_call).
    candidates = {}
    for name, bundle in candidate_metrics.items():
        # _one_call expects candidate_name + all the metric keys already present.
        candidates[name] = bundle

    # Work queue
    work = []
    for name, bundle in candidates.items():
        for r in range(repeats):
            work.append((MODEL_46, bundle, r))

    print(f"[G6] dispatching {len(work)} calls on {MODEL_46} (workers={workers})")
    rows = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(aba._one_call, m, b, r) for (m, b, r) in work]
        for i, f in enumerate(as_completed(futures), 1):
            row = f.result()
            rows.append(row)
            # Progress ping every 10 calls
            if i % 10 == 0 or i == len(futures):
                print(f"[G6]   completed {i}/{len(futures)}")

    # Write JSONL
    with JSONL_46.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, default=str) + "\n")
    total_cost = sum(float(r.get("cost_usd") or 0) for r in rows)
    print(f"[G6] sweep complete. total cost ≈ ${total_cost:.2f}")


def analyze() -> None:
    """Compare Opus 4.6 vs 4.7 verdict calibration and write SUMMARY.md."""
    # Load 4.7 rows from E2
    sweep_47 = REPO / "results" / "ablation" / "skeptic_model_sweep.jsonl"
    rows_47 = [json.loads(l) for l in sweep_47.open() if json.loads(l).get("model") == "claude-opus-4-7"]
    rows_46 = [json.loads(l) for l in JSONL_46.open()]

    # Candidate ground truth (gate's own verdict)
    gate_truth = {r["candidate_name"]: r["gate_verdict"] for r in rows_47}
    categories = {r["candidate_name"]: r["candidate_category"] for r in rows_47}

    def analyze_rows(rows, model_name):
        by_candidate = {}
        for r in rows:
            by_candidate.setdefault(r["candidate_name"], []).append(r["verdict"])
        results = {}
        for cand, verdicts in by_candidate.items():
            c = Counter(verdicts)
            gate = gate_truth.get(cand, "?")
            cat = categories.get(cand, "?")
            agree = c.get(gate, 0)
            abstain = c.get("NEEDS_MORE_TESTS", 0)
            opposite = sum(v for k, v in c.items()
                           if k not in {gate, "NEEDS_MORE_TESTS", "UNPARSED", "UNCERTAIN"})
            n = len(verdicts)
            results[cand] = {
                "category": cat,
                "gate_verdict": gate,
                "n": n,
                "counts": dict(c),
                "agree_with_gate_pct": 100 * agree / n if n else 0,
                "abstain_pct": 100 * abstain / n if n else 0,
                "oppose_gate_pct": 100 * opposite / n if n else 0,
            }
        return results

    r46 = analyze_rows(rows_46, "4.6")
    r47 = analyze_rows(rows_47, "4.7")

    # Calibration score: for PASS gate, we want model to agree (PASS) or
    # abstain (NEEDS_MORE_TESTS). "Bad miscalibration" = FAIL verdict on
    # gate=PASS, or PASS verdict on gate=FAIL.
    def miscalibration_rate(per_cand):
        bad = 0
        total = 0
        for c, d in per_cand.items():
            gate = d["gate_verdict"]
            counts = d["counts"]
            n = d["n"]
            if gate == "PASS":
                # Bad = FAIL
                bad += counts.get("FAIL", 0)
            elif gate == "FAIL":
                # Bad = PASS
                bad += counts.get("PASS", 0)
            total += n
        return 100 * bad / total if total else 0

    miscal_46 = miscalibration_rate(r46)
    miscal_47 = miscalibration_rate(r47)

    out = {
        "claim_from_anthropic": "Opus 4.7 improves abstention calibration 61%→36% incorrect on unknowns (Adaptive mode, model card 2026-04-16).",
        "test_setup": "Same 6 candidates, 10 repeats each (60 calls per model). Thinking: Opus 4.6 type=enabled budget=8000; Opus 4.7 type=enabled budget=8000 (gracefully falls back to adaptive on bad_request).",
        "opus_4_6": {
            "per_candidate": r46,
            "miscalibration_rate_pct": miscal_46,
            "total_calls": sum(d["n"] for d in r46.values()),
        },
        "opus_4_7": {
            "per_candidate": r47,
            "miscalibration_rate_pct": miscal_47,
            "total_calls": sum(d["n"] for d in r47.values()),
        },
        "delta": {
            "miscalibration_46_minus_47_pp": miscal_46 - miscal_47,
            "interpretation": (
                "Positive value = 4.7 more calibrated than 4.6 on biology task "
                "(consistent with Anthropic's published improvement). Negative "
                "or near-zero = claimed improvement does not transfer to this "
                "domain (honest null finding)."
            ),
        },
    }
    (OUT / "calibration_report.json").write_text(json.dumps(out, indent=2))

    # Human-readable SUMMARY
    md = [
        "# G6 — Opus 4.6 vs 4.7 Calibration on Biology Skeptic Task",
        "",
        "## Research question",
        "",
        "Anthropic's Opus 4.7 model card (2026-04-16) claims adaptive-thinking",
        "calibration improvement: abstention on unknowns went **61% → 36% incorrect**",
        "from 4.6 to 4.7 (accuracy approximately unchanged). Does this transfer",
        "to biology skeptic reasoning, or is it confined to benchmark tasks?",
        "",
        "## Setup",
        "",
        "- 6 candidates, 10 repeats each, 60 calls per model",
        "- Same prompt (`prompts/skeptic_review.md`) and metric bundles as E2",
        "- Opus 4.7 data reused from E2 skeptic_model_sweep.jsonl",
        "- Opus 4.6 data fresh (this script)",
        "",
        "## Headline — miscalibration rate",
        "",
        "Miscalibration counted as: FAIL verdict on gate=PASS candidate, OR",
        "PASS verdict on gate=FAIL candidate. NEEDS_MORE_TESTS and UNPARSED",
        "are treated as non-miscalibrated abstentions.",
        "",
        "| Model | Miscalibration rate | Δ vs 4.6 |",
        "|---|---|---|",
        f"| claude-opus-4-6 | **{miscal_46:.1f}%** | — |",
        f"| claude-opus-4-7 | **{miscal_47:.1f}%** | {miscal_47 - miscal_46:+.1f}pp |",
        "",
        f"**Absolute delta: {miscal_46 - miscal_47:+.1f}pp improvement (4.7 vs 4.6).**",
        "",
    ]
    if miscal_46 > miscal_47 + 5:
        md.append("→ **CLAIM CONFIRMED**: Opus 4.7's published calibration improvement "
                  "transfers to biology skeptic reasoning (≥5pp improvement observed).")
    elif miscal_46 > miscal_47:
        md.append("→ **PARTIAL TRANSFER**: Opus 4.7 calibrates better than 4.6, but the "
                  "magnitude is smaller than Anthropic's published benchmark (61→36 = 25pp).")
    else:
        md.append("→ **HONEST NULL**: Opus 4.7's published calibration delta does NOT "
                  "transfer to this biology skeptic task. Either the task doesn't "
                  "stress the same capability, or the improvement is benchmark-specific. "
                  "Both interpretations are valuable pre-registration outcomes.")

    md += [
        "",
        "## Per-candidate verdict distribution",
        "",
        "| Candidate | Category | Gate | 4.6 verdicts | 4.7 verdicts |",
        "|---|---|---|---|---|",
    ]
    for c in sorted(r46.keys()):
        d46 = r46[c]
        d47 = r47.get(c, {"counts": {}})
        v46 = ", ".join(f"{k}={v}" for k, v in sorted(d46["counts"].items()))
        v47 = ", ".join(f"{k}={v}" for k, v in sorted(d47["counts"].items()))
        md.append(f"| {c} | {d46['category']} | {d46['gate_verdict']} | {v46} | {v47} |")

    md += [
        "",
        "## Why this matters",
        "",
        "The 'Rejection-as-Product' thesis of Lacuna claims that the",
        "core competence we elevate is *disciplined abstention* — the model",
        "refusing to claim a law survives when the evidence is ambiguous.",
        "Opus 4.7's published calibration delta (61→36% on unknowns) is the",
        "Anthropic-sanctioned instantiation of exactly that competence at the",
        "model level; the 5-test gate is our externally-verifiable instantiation",
        "at the *pipeline* level.",
        "",
        "This comparison tests whether the two instantiations agree on biology:",
        "does a model that's better at abstaining on MMLU-style unknowns also",
        "abstain better on borderline symbolic-regression survivors?",
        "",
        "## Files",
        "- `calibration_report.json` — machine-readable per-candidate + delta",
        "- `opus_46_sweep.jsonl` — raw 60 Opus 4.6 API response rows",
        "- E2 4.7 data: `results/ablation/skeptic_model_sweep.jsonl`",
        "",
        "## Reproduce",
        "```bash",
        "# Requires ANTHROPIC_API_KEY in environment.",
        "PYTHONPATH=src .venv/bin/python src/g6_calibration_4_6_vs_4_7.py sweep --repeats 10",
        "PYTHONPATH=src .venv/bin/python src/g6_calibration_4_6_vs_4_7.py analyze",
        "```",
    ]
    (OUT / "SUMMARY.md").write_text("\n".join(md))
    print(f"[G6] wrote {OUT}/SUMMARY.md")
    print(f"  Opus 4.6 miscalibration: {miscal_46:.1f}%")
    print(f"  Opus 4.7 miscalibration: {miscal_47:.1f}%")
    print(f"  Δ: {miscal_46 - miscal_47:+.1f}pp")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sw = sub.add_parser("sweep")
    sw.add_argument("--repeats", type=int, default=10)
    sw.add_argument("--workers", type=int, default=4)
    sub.add_parser("analyze")
    args = p.parse_args()

    if args.cmd == "sweep":
        run_sweep(repeats=args.repeats, workers=args.workers)
    elif args.cmd == "analyze":
        analyze()


if __name__ == "__main__":
    main()
