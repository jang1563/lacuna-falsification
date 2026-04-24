#!/usr/bin/env python3
"""PhL-15 — Adaptive Thinking causal ablation on Opus 4.7.

Question: Is adaptive thinking the MECHANISM behind Opus 4.7's Skeptic
calibration, or does Opus 4.7 remain calibrated even without it?

Design: Opus 4.7 ONLY (single model isolates mechanism), 6 candidates,
10 repeats, 2 thinking modes:
  - Adaptive: thinking={"type":"adaptive","display":"summarized"}
  - Disabled: thinking={"type":"disabled"}
= 2 × 6 × 10 = 120 API calls total (~$15-20).

Metric: verdict distribution (PASS / FAIL / NEEDS_MORE_TESTS) per mode,
gate-PASS dissent rate per mode, metric-citation specificity per mode.

Hypothesis: if adaptive thinking IS the mechanism, disabled Opus drops
toward Sonnet-like collapse (0/60 PASS). If adaptive is decorative, both
modes should look similar (still 10+/60 PASS).

Falsifying risk: acknowledged. A null result would honestly weaken
why_opus_4_7.md §0's adaptive-thinking causal claim.

Outputs:
  results/live_evidence/phl15_adaptive_thinking/sweep.jsonl  (per-call rows)
  results/live_evidence/phl15_adaptive_thinking/verdict.json (summary)
  results/live_evidence/phl15_adaptive_thinking/SUMMARY.md
  results/live_evidence/phl15_adaptive_thinking/mode_comparison.png
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results" / "live_evidence" / "phl15_adaptive_thinking"
OUT.mkdir(parents=True, exist_ok=True)

SWEEP_PATH = OUT / "sweep.jsonl"
VERDICT_PATH = OUT / "verdict.json"
SUMMARY_PATH = OUT / "SUMMARY.md"
PLOT_PATH = OUT / "mode_comparison.png"

MODEL = "claude-opus-4-7"
MODES = {
    "adaptive": {"type": "adaptive", "display": "summarized"},
    "disabled": {"type": "disabled"},
}

# Reuse same 6 candidates from E2 ablation (pass/borderline/fail spread).
# These metrics are pre-computed by `track_a_model_ablation.py precompute`.
# If that file doesn't exist, fall back to embedded reference metrics.
METRICS_FILE = REPO / "results" / "ablation" / "candidate_metrics.json"
FALLBACK_METRICS = [
    {"id": "top2a_minus_epas1", "equation": "TOP2A - EPAS1",
     "dataset": "TCGA-KIRC metastasis_expanded (n=505)", "passes": True,
     "perm_p": 0.0, "ci_lower": 0.665, "ci_width": 0.122,
     "delta_baseline": 0.069, "delta_confound": None, "decoy_p": 0.001,
     "law_auc": 0.726, "baseline_auc": 0.657, "n_samples": 505, "n_disease": 79},
    {"id": "mki67_minus_epas1", "equation": "MKI67 - EPAS1",
     "dataset": "TCGA-KIRC metastasis_expanded (n=505)", "passes": True,
     "perm_p": 0.0, "ci_lower": 0.643, "ci_width": 0.130,
     "delta_baseline": 0.051, "delta_confound": None, "decoy_p": 0.003,
     "law_auc": 0.708, "baseline_auc": 0.657, "n_samples": 505, "n_disease": 79},
    {"id": "ca9_vegfa_minus_agxt", "equation": "log1p(CA9)+log1p(VEGFA)-log1p(AGXT)",
     "dataset": "TCGA-KIRC tumor_normal (n=609)", "passes": False,
     "perm_p": 0.0, "ci_lower": 0.975, "ci_width": 0.022,
     "delta_baseline": 0.019, "delta_confound": 0.008, "decoy_p": 0.0,
     "law_auc": 0.984, "baseline_auc": 0.965, "n_samples": 609, "n_disease": 537},
    {"id": "five_gene_stress", "equation": "MKI67 - (EPAS1 + LRP2 + PTGER3 + RPL13A)/4",
     "dataset": "TCGA-KIRC metastasis_expanded (n=505)", "passes": True,
     "perm_p": 0.0, "ci_lower": 0.654, "ci_width": 0.148,
     "delta_baseline": 0.069, "delta_confound": None, "decoy_p": 0.0,
     "law_auc": 0.726, "baseline_auc": 0.657, "n_samples": 505, "n_disease": 79},
    {"id": "actb_gapdh_null", "equation": "log1p(ACTB) - log1p(GAPDH)",
     "dataset": "TCGA-KIRC metastasis_expanded (n=505)", "passes": False,
     "perm_p": 0.412, "ci_lower": 0.487, "ci_width": 0.095,
     "delta_baseline": -0.071, "delta_confound": None, "decoy_p": 0.538,
     "law_auc": 0.528, "baseline_auc": 0.657, "n_samples": 505, "n_disease": 79},
    {"id": "mki67_rpl13a_null", "equation": "log1p(MKI67) - log1p(RPL13A)",
     "dataset": "TCGA-KIRC metastasis_expanded (n=505)", "passes": False,
     "perm_p": 0.0, "ci_lower": 0.592, "ci_width": 0.110,
     "delta_baseline": 0.021, "delta_confound": None, "decoy_p": 0.002,
     "law_auc": 0.647, "baseline_auc": 0.657, "n_samples": 505, "n_disease": 79},
]

SYSTEM = (REPO / "prompts" / "skeptic_review.md").read_text()

METRIC_RE = re.compile(
    r"(perm_p|perm_p_fdr|ci_lower|ci_width|delta_baseline|delta_confound|"
    r"decoy_p|law_auc|baseline_auc)\s*[=:≈]\s*[-+]?\d+\.\d+"
)


def _load_metrics() -> list[dict[str, Any]]:
    if METRICS_FILE.exists():
        data = json.loads(METRICS_FILE.read_text())
        if isinstance(data, list) and len(data) >= 6:
            return data[:6]
    return FALLBACK_METRICS


def _strip_json_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        lines = s.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        s = "\n".join(lines)
    return s


def _one_call(client: Any, mode: str, thinking: dict, cand: dict,
              repeat: int) -> dict[str, Any]:
    import anthropic  # noqa: F401
    metrics_clean = {k: v for k, v in cand.items()
                     if k in ("perm_p", "ci_lower", "ci_width",
                              "delta_baseline", "delta_confound", "decoy_p",
                              "law_auc", "baseline_auc", "passes")}
    user_msg = (
        f"Candidate equation: {cand['equation']}\n"
        f"Dataset: {cand['dataset']}\n"
        f"Falsification metrics: {json.dumps(metrics_clean, default=str)}\n\n"
        "Output only the JSON described in the system prompt."
    )
    t0 = time.time()
    response_text = ""
    thinking_text = ""
    err = None
    usage = None
    try:
        with client.messages.stream(
            model=MODEL,
            max_tokens=8000,
            thinking=thinking,
            system=SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        ) as stream:
            final = stream.get_final_message()
        usage = getattr(final, "usage", None)
        for block in final.content:
            t = getattr(block, "type", "")
            if t == "thinking":
                thinking_text += getattr(block, "thinking", "")
            elif t == "text":
                response_text += getattr(block, "text", "")
    except Exception as e:
        err = str(e)

    latency = time.time() - t0
    parsed = None
    try:
        parsed = json.loads(_strip_json_fences(response_text))
    except Exception:
        parsed = None

    if isinstance(parsed, dict):
        verdict = parsed.get("verdict", "UNPARSED")
        reason = parsed.get("reason", "")
    else:
        verdict = "UNPARSED"
        reason = response_text

    metric_cites = len(METRIC_RE.findall(reason))
    return {
        "mode": mode,
        "candidate_id": cand["id"],
        "repeat": repeat,
        "verdict": verdict,
        "reason_length_chars": len(reason),
        "thinking_length_chars": len(thinking_text),
        "metric_citations": metric_cites,
        "latency_sec": round(latency, 2),
        "input_tokens": int(getattr(usage, "input_tokens", 0) or 0) if usage else 0,
        "output_tokens": int(getattr(usage, "output_tokens", 0) or 0) if usage else 0,
        "err": err,
        "reason_snippet": reason[:240],
    }


def run_sweep(repeats: int = 10, workers: int = 6) -> None:
    import anthropic  # noqa
    client = anthropic.Anthropic()
    metrics = _load_metrics()
    tasks = []
    for mode_name, thinking in MODES.items():
        for cand in metrics:
            for r in range(repeats):
                tasks.append((mode_name, thinking, cand, r))
    print(f"[PhL-15] {len(tasks)} calls: 2 modes × 6 candidates × {repeats} repeats")
    rows: list[dict] = []
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(_one_call, client, m, th, c, r): (m, c['id'], r)
                   for (m, th, c, r) in tasks}
        for fut in as_completed(futures):
            row = fut.result()
            rows.append(row)
            done += 1
            if done % 10 == 0:
                print(f"  {done}/{len(tasks)} done", flush=True)
    with SWEEP_PATH.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"[PhL-15] saved {SWEEP_PATH}")


def analyze() -> None:
    if not SWEEP_PATH.exists():
        print(f"ERROR: {SWEEP_PATH} not found. Run `run` first.", file=sys.stderr)
        sys.exit(1)
    rows = [json.loads(line) for line in SWEEP_PATH.read_text().splitlines() if line]
    # Tally per mode × candidate → verdict counts
    by_mode: dict[str, dict[str, int]] = {}
    gate_pass_ids = {"top2a_minus_epas1", "mki67_minus_epas1", "five_gene_stress"}
    dissent_by_mode: dict[str, dict] = {}
    citations_by_mode: dict[str, list[int]] = {"adaptive": [], "disabled": []}
    thinking_lens: dict[str, list[int]] = {"adaptive": [], "disabled": []}
    for r in rows:
        m = r["mode"]
        v = r["verdict"]
        by_mode.setdefault(m, {"PASS": 0, "FAIL": 0, "NEEDS_MORE_TESTS": 0, "UNPARSED": 0, "total": 0})
        by_mode[m][v] = by_mode[m].get(v, 0) + 1
        by_mode[m]["total"] += 1
        citations_by_mode[m].append(r.get("metric_citations", 0))
        thinking_lens[m].append(r.get("thinking_length_chars", 0))
        if r["candidate_id"] in gate_pass_ids:
            dissent_by_mode.setdefault(m, {"gate_pass_calls": 0, "dissent": 0})
            dissent_by_mode[m]["gate_pass_calls"] += 1
            if v in ("FAIL", "NEEDS_MORE_TESTS"):
                dissent_by_mode[m]["dissent"] += 1
    # Summary dict
    summary = {
        "model": MODEL,
        "total_calls": len(rows),
        "by_mode": by_mode,
        "dissent_on_gate_pass": {
            m: {
                "rate": round(d["dissent"] / max(d["gate_pass_calls"], 1), 3),
                "n": d["gate_pass_calls"],
            } for m, d in dissent_by_mode.items()
        },
        "citations_mean_by_mode": {
            m: round(sum(v)/max(len(v),1), 2) for m, v in citations_by_mode.items()
        },
        "thinking_chars_mean_by_mode": {
            m: round(sum(v)/max(len(v),1), 0) for m, v in thinking_lens.items()
        },
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    VERDICT_PATH.write_text(json.dumps(summary, indent=2))
    print(f"[PhL-15] verdict saved to {VERDICT_PATH}")
    print(json.dumps(summary, indent=2))
    _make_plot(summary)
    _write_summary_md(summary)


def _make_plot(summary: dict) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib unavailable — skipping plot")
        return
    modes = ["adaptive", "disabled"]
    verdicts = ["PASS", "FAIL", "NEEDS_MORE_TESTS", "UNPARSED"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    # Panel 1: verdict distribution per mode
    import numpy as np
    x = np.arange(len(verdicts))
    w = 0.35
    for i, m in enumerate(modes):
        counts = [summary["by_mode"].get(m, {}).get(v, 0) for v in verdicts]
        ax1.bar(x + i*w - w/2, counts, w, label=f"thinking={m}",
                color="#1f77b4" if m == "adaptive" else "#ff7f0e")
    ax1.set_xticks(x)
    ax1.set_xticklabels(verdicts)
    ax1.set_ylabel("Count (out of 60 per mode)")
    ax1.set_title("Opus 4.7 Skeptic verdict distribution by thinking mode")
    ax1.legend()
    ax1.grid(axis="y", alpha=0.3)
    # Panel 2: dissent rate on gate-PASS + citation specificity
    dissent = summary["dissent_on_gate_pass"]
    cites = summary["citations_mean_by_mode"]
    labels = ["Dissent rate\n(on gate-PASS)", "Mean metric\ncitations"]
    adaptive_vals = [dissent.get("adaptive", {}).get("rate", 0), cites.get("adaptive", 0)]
    disabled_vals = [dissent.get("disabled", {}).get("rate", 0), cites.get("disabled", 0)]
    x2 = np.arange(len(labels))
    ax2.bar(x2 - w/2, adaptive_vals, w, label="adaptive", color="#1f77b4")
    ax2.bar(x2 + w/2, disabled_vals, w, label="disabled", color="#ff7f0e")
    ax2.set_xticks(x2)
    ax2.set_xticklabels(labels)
    ax2.set_title("Calibration proxies by thinking mode")
    ax2.legend()
    ax2.grid(axis="y", alpha=0.3)
    fig.suptitle("PhL-15 · Adaptive thinking causal ablation (Opus 4.7)",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(PLOT_PATH, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[PhL-15] plot saved: {PLOT_PATH}")


def _write_summary_md(summary: dict) -> None:
    md = ["# PhL-15 — Adaptive thinking causal ablation (Opus 4.7)",
          "", "**Question:** is adaptive thinking the *mechanism* behind Opus 4.7's Skeptic calibration?",
          "", "## Design",
          "", "- Opus 4.7 only (single model isolates mechanism)",
          "- 6 candidates (same as E2 ablation, pass/borderline/fail spread)",
          "- 10 repeats × 2 modes = **120 API calls**",
          "- Modes:",
          "  - `adaptive`: `thinking={'type':'adaptive','display':'summarized'}`",
          "  - `disabled`: `thinking={'type':'disabled'}`",
          "", "## Result",
          ""]
    md.append("| Mode | PASS | FAIL | NEEDS_MORE_TESTS | UNPARSED |")
    md.append("|---|---|---|---|---|")
    for m in ("adaptive", "disabled"):
        by = summary["by_mode"].get(m, {})
        md.append(f"| `{m}` | {by.get('PASS',0)} | {by.get('FAIL',0)} | "
                  f"{by.get('NEEDS_MORE_TESTS',0)} | {by.get('UNPARSED',0)} |")
    md.append("")
    md.append("**Dissent rate on gate-PASS candidates** (TOP2A-EPAS1, MKI67-EPAS1, 5-gene compound):")
    md.append("")
    for m, d in summary["dissent_on_gate_pass"].items():
        md.append(f"- `{m}`: {d['rate']*100:.1f}% dissent ({d['n']} gate-PASS calls)")
    md.append("")
    md.append("**Mean metric citations per response**:")
    md.append("")
    for m, c in summary["citations_mean_by_mode"].items():
        md.append(f"- `{m}`: {c:.2f}")
    md.append("")
    md.append("**Mean thinking content length (chars)**:")
    md.append("")
    for m, c in summary["thinking_chars_mean_by_mode"].items():
        md.append(f"- `{m}`: {int(c):,}")
    md.append("")
    md.append("## Interpretation")
    md.append("")
    a_pass = summary["by_mode"].get("adaptive", {}).get("PASS", 0)
    d_pass = summary["by_mode"].get("disabled", {}).get("PASS", 0)
    a_diss = summary["dissent_on_gate_pass"].get("adaptive", {}).get("rate", 0)
    d_diss = summary["dissent_on_gate_pass"].get("disabled", {}).get("rate", 0)
    if a_diss < d_diss - 0.1:
        interp = ("**Adaptive thinking is the mechanism.** Disabled-thinking "
                  "Opus 4.7 dissents more often on gate-PASS candidates, moving "
                  "toward the Sonnet 4.6 collapse pattern (0/60 PASS in E2). "
                  "why_opus_4_7.md §0's causal claim is supported.")
    elif abs(a_diss - d_diss) < 0.05:
        interp = ("**Adaptive thinking is NOT the differentiator.** Verdict "
                  "distribution is similar with and without adaptive thinking. "
                  "The Opus-vs-Sonnet gap in E2 ablation must come from other "
                  "model-internal capabilities (pre-training data, RLHF, "
                  "instruction-following). why_opus_4_7.md §0 should be "
                  "softened to 'Opus 4.7 calibration' rather than 'adaptive "
                  "thinking holds the stance'.")
    else:
        interp = ("**Mixed signal.** Adaptive thinking produces a calibration "
                  f"shift (dissent {a_diss:.1%} vs {d_diss:.1%}) but not as "
                  "sharp as the Opus-vs-Sonnet gap. Report both numbers.")
    md.append(interp)
    md.append("")
    md.append(f"**Raw data**: `sweep.jsonl` ({summary['total_calls']} rows)")
    md.append("")
    md.append("**Reproduce**:")
    md.append("```bash")
    md.append("source ~/.api_keys")
    md.append("PYTHONPATH=src .venv/bin/python src/phl15_adaptive_thinking_ablation.py run")
    md.append("PYTHONPATH=src .venv/bin/python src/phl15_adaptive_thinking_ablation.py analyze")
    md.append("```")
    SUMMARY_PATH.write_text("\n".join(md))
    print(f"[PhL-15] SUMMARY.md saved: {SUMMARY_PATH}")


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run").add_argument("--repeats", type=int, default=10)
    sub.add_parser("analyze")
    args, extra = p.parse_known_args()
    if args.cmd == "run":
        repeats = 10
        for i, a in enumerate(extra):
            if a == "--repeats" and i+1 < len(extra):
                repeats = int(extra[i+1])
        run_sweep(repeats=repeats)
    elif args.cmd == "analyze":
        analyze()


if __name__ == "__main__":
    main()
