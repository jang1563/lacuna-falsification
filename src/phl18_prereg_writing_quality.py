#!/usr/bin/env python3
"""PhL-18 — Pre-registration writing quality across models.

Question: how does each model perform on a structured design task —
writing a pre-registration YAML that BINDS before the fit?

Design:
- 5 hypotheses (pre-specified scientific scenarios).
- 3 models (Opus 4.7, Sonnet 4.6, Haiku 4.5) write a full pre-reg YAML
  for each hypothesis.
- 5 × 3 = 15 YAMLs.
- Blind rubric rating by Opus 4.7 meta-rater + programmatic structural
  checks (schema compliance, threshold specificity, kill-test coverage).

Self-preference-bias caveat: the Opus meta-rater COULD favour Opus YAMLs.
We mitigate by (a) hiding model labels in rater prompt (shown as
`candidate_A/B/C` with randomized order), and (b) reporting BOTH the
rater's rubric scores AND programmatic (rater-independent) structural
scores.

Outputs:
  results/live_evidence/phl18_prereg_writing/yamls.jsonl
  results/live_evidence/phl18_prereg_writing/ratings.jsonl
  results/live_evidence/phl18_prereg_writing/verdict.json
  results/live_evidence/phl18_prereg_writing/SUMMARY.md
  results/live_evidence/phl18_prereg_writing/quality_heatmap.png
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results" / "live_evidence" / "phl18_prereg_writing"
OUT.mkdir(parents=True, exist_ok=True)

YAMLS_PATH = OUT / "yamls.jsonl"
RATINGS_PATH = OUT / "ratings.jsonl"
VERDICT_PATH = OUT / "verdict.json"
SUMMARY_PATH = OUT / "SUMMARY.md"
PLOT_PATH = OUT / "quality_heatmap.png"

MODELS = ["claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5"]

HYPOTHESES = [
    {
        "id": "H1_ccRCC_metastasis",
        "title": "Compact 2-gene law predicts metastasis in TCGA-KIRC",
        "context": ("TCGA-KIRC metastasis_expanded (n=505, 16% M1). "
                    "45-gene panel spanning HIF, Warburg, Proliferation, "
                    "Housekeeping, Renal_tubule, Metastasis_EMT. Goal: "
                    "find a 2-gene compact law that clears +0.05 above "
                    "best single-gene baseline."),
    },
    {
        "id": "H2_IMmotion_survival",
        "title": "TOP2A-EPAS1 replicates on IMmotion150 PFS",
        "context": ("Independent Phase-2 cohort IMmotion150 (n=263, "
                    "PFS endpoint under Atezo ± Beva vs Sunitinib). Test "
                    "whether score = TOP2A-EPAS1 from TCGA stratifies "
                    "PFS on median split."),
    },
    {
        "id": "H3_BRCA_cross_cancer",
        "title": "TOP2A-EPAS1 does NOT transfer to TCGA-BRCA",
        "context": ("Pre-register the HYPOTHESIZED FAILURE of TOP2A-EPAS1 "
                    "on breast cancer, as a ccRCC-specificity control. "
                    "What would constitute the falsification, and what "
                    "metric would make the reject 'as predicted'?"),
    },
    {
        "id": "H4_SLC22A8_extension",
        "title": "SLC22A8 3-gene extension of TOP2A-EPAS1",
        "context": ("The H1 LLM-SR loop proposed TOP2A - (EPAS1 + SLC22A8) "
                    "as an extension. Pre-register the IMmotion150 survival "
                    "replay gate that would either accept or reject this "
                    "extension. C-index thresholds must be specified."),
    },
    {
        "id": "H5_PRAD_generalization",
        "title": "Proliferation-vs-lineage pattern in TCGA-PRAD",
        "context": ("Test whether the ceiling-effect pattern (single-gene "
                    "saturation prevents compound laws) generalises from "
                    "ccRCC/CA9 to prostate cancer/KLK3. Pre-register the "
                    "expected failure mode and what metric would confirm."),
    },
]

PROPOSER_SYSTEM = """\
You are a scientific pre-registration author. Given a hypothesis, write
a COMPLETE pre-registration YAML that BINDS the falsification criteria
BEFORE any fit is attempted.

Output valid YAML inside ``` fences, with these required keys:
- hypothesis_id: (use the id from the prompt)
- claim: (one sentence describing what would count as confirmation)
- null_hypothesis: (what the claim specifically denies)
- primary_metric: (which statistic decides pass/fail)
- pass_threshold: (SPECIFIC numeric threshold the metric must exceed)
- fail_threshold: (SPECIFIC numeric threshold below which the claim is rejected)
- kill_tests: (LIST of specific pre-registered tests, each with a
  numeric threshold and rationale)
- active_legs: (list of which test legs are active vs null, with reasoning)
- falsifiability_statement: (one sentence describing what observation
  would falsify the claim — MUST be specific enough to evaluate)
- scope_limits: (list of what the claim does NOT say; research-use-only
  caveats)
- emitted_git_sha: "TBD_AT_COMMIT"  (placeholder for the commit SHA)
- emitted_at_utc: "TBD_AT_COMMIT"

Every threshold and test must be CONCRETE and NUMERIC. Avoid vague
language like "strongly" or "sufficient". Use specific numbers.

Output ONLY the YAML inside ``` fences. No prose before or after.
"""


def _extract_yaml(text: str) -> str:
    m = re.search(r"```(?:yaml)?\n([\s\S]*?)```", text)
    if m:
        return m.group(1).strip()
    return text.strip()


def _one_yaml(client: Any, model: str, hypothesis: dict) -> dict[str, Any]:
    user_msg = (
        f"Hypothesis ID: {hypothesis['id']}\n"
        f"Title: {hypothesis['title']}\n\n"
        f"Context:\n{hypothesis['context']}\n\n"
        "Write the pre-registration YAML now."
    )
    try:
        with client.messages.stream(
            model=model,
            max_tokens=4000,
            thinking={"type": "adaptive", "display": "summarized"},
            system=PROPOSER_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        ) as stream:
            final = stream.get_final_message()
        text = ""
        for block in final.content:
            if getattr(block, "type", "") == "text":
                text += getattr(block, "text", "")
        yaml_str = _extract_yaml(text)
        return {
            "model": model,
            "hypothesis_id": hypothesis["id"],
            "hypothesis_title": hypothesis["title"],
            "yaml_text": yaml_str,
            "full_response_length": len(text),
        }
    except Exception as e:
        return {"model": model, "hypothesis_id": hypothesis["id"], "err": str(e)[:200]}


def run_write() -> None:
    import anthropic
    client = anthropic.Anthropic()
    rows: list[dict] = []
    for model in MODELS:
        print(f"[PhL-18] writing 5 pre-regs with {model}...")
        for h in HYPOTHESES:
            r = _one_yaml(client, model, h)
            rows.append(r)
    with YAMLS_PATH.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"[PhL-18] wrote {len(rows)} YAMLs to {YAMLS_PATH}")


# ---------------------------------------------------------------------------
# Programmatic structural checks (rater-independent)
# ---------------------------------------------------------------------------

REQUIRED_KEYS = {
    "hypothesis_id", "claim", "null_hypothesis", "primary_metric",
    "pass_threshold", "fail_threshold", "kill_tests", "active_legs",
    "falsifiability_statement", "scope_limits",
}

NUMBER_RE = re.compile(r"-?\d+\.?\d*")


def structural_check(yaml_text: str) -> dict[str, Any]:
    """Rater-independent structural metrics on a YAML string."""
    lines = yaml_text.split("\n")
    text = yaml_text.lower()
    present = sum(1 for k in REQUIRED_KEYS if k.lower() in text)
    numbers = NUMBER_RE.findall(yaml_text)
    numeric_count = len(numbers)
    kill_tests = yaml_text.lower().count("kill_test")
    # Count bullet list items under kill_tests
    in_kt = False
    kt_items = 0
    for line in lines:
        ll = line.lower().lstrip()
        if ll.startswith("kill_tests"):
            in_kt = True
            continue
        if in_kt:
            if line.startswith("  - ") or line.startswith("    - "):
                kt_items += 1
            elif line and not line.startswith(" "):
                in_kt = False
    has_falsifiability = "falsifiability_statement" in text
    has_scope = "scope_limits" in text
    has_legs = "active_legs" in text
    # Biology grounding: mention of specific gene symbols or cohort IDs
    bio_terms = ["tcga", "immotion", "top2a", "epas1", "mki67", "ca9", "kirc",
                 "brca", "prad", "ccrcc", "ccrcc"]
    bio_count = sum(1 for term in bio_terms if term in text)
    return {
        "required_keys_present": present,
        "required_keys_total": len(REQUIRED_KEYS),
        "numeric_values_count": numeric_count,
        "kill_test_items": kt_items,
        "has_falsifiability": has_falsifiability,
        "has_scope_limits": has_scope,
        "has_active_legs": has_legs,
        "biology_grounding_count": bio_count,
        "total_lines": len(lines),
    }


# ---------------------------------------------------------------------------
# Rubric rating by Opus 4.7 (blind — labels hidden)
# ---------------------------------------------------------------------------

RATER_SYSTEM = """\
You are a blind rubric rater for pre-registration quality. You will see
THREE candidate YAMLs labelled Candidate_A, Candidate_B, Candidate_C
(order randomized). Do NOT guess model identity; rate on rubric only.

For each candidate, rate 0-10 on each of these axes:
1. THRESHOLD_SPECIFICITY: are all thresholds concrete numbers (not "strong"
   or "sufficient")?
2. KILL_TEST_COVERAGE: are falsification tests listed with specific
   thresholds?
3. FALSIFIABILITY: is the falsifiability statement specific enough to
   actually disprove the claim?
4. BIOLOGY_GROUNDING: does it cite specific cohorts / gene names / prior
   literature?
5. SCOPE_DISCIPLINE: does it state what the claim does NOT mean
   (research-use-only, no diagnostic claims, etc.)?

Return valid JSON:
{
  "Candidate_A": {"threshold_specificity": 0-10, "kill_test_coverage": 0-10,
                  "falsifiability": 0-10, "biology_grounding": 0-10,
                  "scope_discipline": 0-10, "notes": "one sentence"},
  "Candidate_B": {...}, "Candidate_C": {...}
}

No markdown fences, just JSON.
"""


def _rate_triplet(client: Any, triplet: dict[str, str],
                  mapping: dict[str, str]) -> dict[str, Any]:
    """Rate a triple of YAMLs. Triplet: {Candidate_A: yaml, ...}. mapping:
    {Candidate_A: model_name} for post-analysis."""
    user_msg = (
        "Rate these three pre-registration YAMLs on the 5 rubric axes.\n\n"
        + "\n\n---\n\n".join(f"### {k}\n\n```yaml\n{v}\n```"
                              for k, v in triplet.items())
        + "\n\nReturn the JSON rubric now."
    )
    try:
        with client.messages.stream(
            model="claude-opus-4-7",
            max_tokens=2000,
            thinking={"type": "adaptive", "display": "summarized"},
            system=RATER_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        ) as stream:
            final = stream.get_final_message()
        text = ""
        for block in final.content:
            if getattr(block, "type", "") == "text":
                text += getattr(block, "text", "")
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return {"err": "no_json", "raw": text[:300], "mapping": mapping}
        try:
            parsed = json.loads(m.group(0))
        except Exception as e:
            return {"err": f"parse: {e}", "raw": text[:300], "mapping": mapping}
        return {"ratings": parsed, "mapping": mapping}
    except Exception as e:
        return {"err": str(e)[:300], "mapping": mapping}


def run_rate() -> None:
    import anthropic
    if not YAMLS_PATH.exists():
        print("ERROR: run write first.", file=sys.stderr)
        sys.exit(1)
    client = anthropic.Anthropic()
    rows = [json.loads(l) for l in YAMLS_PATH.read_text().splitlines() if l]
    # Group by hypothesis_id
    rng = random.Random(42)
    rating_rows: list[dict] = []
    hyp_ids = sorted({r["hypothesis_id"] for r in rows})
    for h_id in hyp_ids:
        subset = {r["model"]: r.get("yaml_text", "") for r in rows
                  if r["hypothesis_id"] == h_id and "yaml_text" in r}
        if len(subset) < 3:
            continue
        # Randomize order
        models_shuffled = list(subset.keys())
        rng.shuffle(models_shuffled)
        triplet_keys = ["Candidate_A", "Candidate_B", "Candidate_C"]
        triplet = {tk: subset[m] for tk, m in zip(triplet_keys, models_shuffled)}
        mapping = {tk: m for tk, m in zip(triplet_keys, models_shuffled)}
        print(f"[PhL-18] rating triplet for {h_id} (mapping hidden from rater)")
        result = _rate_triplet(client, triplet, mapping)
        result["hypothesis_id"] = h_id
        rating_rows.append(result)
    with RATINGS_PATH.open("w") as f:
        for r in rating_rows:
            f.write(json.dumps(r) + "\n")
    print(f"[PhL-18] ratings saved: {RATINGS_PATH}")


def analyze() -> None:
    if not YAMLS_PATH.exists() or not RATINGS_PATH.exists():
        print("ERROR: run write + rate first.", file=sys.stderr)
        sys.exit(1)
    yamls = [json.loads(l) for l in YAMLS_PATH.read_text().splitlines() if l]
    ratings = [json.loads(l) for l in RATINGS_PATH.read_text().splitlines() if l]

    # Structural scores per (model, hypothesis)
    struct_by_model: dict[str, list[dict]] = {m: [] for m in MODELS}
    # Track format compliance per model
    format_compliance: dict[str, dict] = {m: {"valid_yaml": 0, "total": 0, "empty": 0} for m in MODELS}
    for row in yamls:
        m = row.get("model", "unknown")
        if m in format_compliance:
            format_compliance[m]["total"] += 1
            if "yaml_text" in row and row["yaml_text"].strip():
                format_compliance[m]["valid_yaml"] += 1
            else:
                format_compliance[m]["empty"] += 1
        if "yaml_text" not in row or not row["yaml_text"].strip():
            continue
        s = structural_check(row["yaml_text"])
        s["hypothesis_id"] = row["hypothesis_id"]
        struct_by_model[m].append(s)

    # Aggregate structural
    summary: dict[str, Any] = {"structural": {}, "rubric": {}, "format_compliance": format_compliance, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    for m, items in struct_by_model.items():
        if not items:
            continue
        summary["structural"][m] = {
            "n": len(items),
            "required_keys_coverage_pct": round(
                100 * sum(i["required_keys_present"] for i in items)
                / (len(items) * len(REQUIRED_KEYS)), 1),
            "mean_numeric_values": round(
                sum(i["numeric_values_count"] for i in items) / len(items), 1),
            "mean_kill_test_items": round(
                sum(i["kill_test_items"] for i in items) / len(items), 1),
            "mean_biology_grounding": round(
                sum(i["biology_grounding_count"] for i in items) / len(items), 1),
            "falsifiability_present_pct": round(
                100 * sum(1 for i in items if i["has_falsifiability"]) / len(items), 1),
            "scope_limits_present_pct": round(
                100 * sum(1 for i in items if i["has_scope_limits"]) / len(items), 1),
        }

    # Rubric scores per model (averaged across hypotheses)
    rubric_scores: dict[str, dict[str, list[int]]] = {m: {} for m in MODELS}
    for r in ratings:
        if "ratings" not in r or "mapping" not in r:
            continue
        for cand_label, model in r["mapping"].items():
            cand_score = r["ratings"].get(cand_label, {})
            for axis, val in cand_score.items():
                if axis == "notes":
                    continue
                if not isinstance(val, (int, float)):
                    continue
                rubric_scores[model].setdefault(axis, []).append(val)
    for m, axes in rubric_scores.items():
        summary["rubric"][m] = {
            axis: round(sum(v)/len(v), 2) for axis, v in axes.items()
        }
    VERDICT_PATH.write_text(json.dumps(summary, indent=2))
    print(f"[PhL-18] verdict saved: {VERDICT_PATH}")
    print(json.dumps(summary, indent=2))
    _make_plot(summary)
    _write_summary(summary)


def _make_plot(summary: dict) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return
    rubric = summary["rubric"]
    struct = summary["structural"]
    # Use models that have structural data (subset of MODELS)
    available_models = [m for m in MODELS if m in struct]
    if not available_models:
        print("[PhL-18] no data to plot")
        return
    axes_names = ["threshold_specificity", "kill_test_coverage",
                  "falsifiability", "biology_grounding", "scope_discipline"]
    models = available_models
    short = [m.split("-")[1] for m in models]
    matrix = np.array([[rubric.get(m, {}).get(a, 0) for a in axes_names] for m in models])
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    im = axes[0].imshow(matrix, aspect="auto", cmap="YlGnBu", vmin=0, vmax=10)
    axes[0].set_xticks(range(len(axes_names)))
    axes[0].set_xticklabels([a.replace("_", "\n") for a in axes_names], fontsize=9)
    axes[0].set_yticks(range(len(short)))
    axes[0].set_yticklabels(short)
    for i in range(len(short)):
        for j in range(len(axes_names)):
            axes[0].text(j, i, f"{matrix[i,j]:.1f}", ha="center", va="center",
                         color="white" if matrix[i,j] > 5 else "black")
    plt.colorbar(im, ax=axes[0], label="Rubric score (0-10)")
    axes[0].set_title("(a) Blind-rated rubric scores (Opus meta-rater)")
    # Structural panel
    struct = summary["structural"]
    metrics = ["required_keys_coverage_pct", "mean_numeric_values",
               "mean_kill_test_items", "mean_biology_grounding"]
    metrics_short = ["Key coverage %", "Num values", "Kill tests", "Bio terms"]
    matrix2 = np.array([[struct[m].get(k, 0) for k in metrics] for m in models])
    # Normalize per column for heatmap readability
    max_per_col = matrix2.max(axis=0)
    max_per_col[max_per_col == 0] = 1
    matrix2_norm = matrix2 / max_per_col
    im2 = axes[1].imshow(matrix2_norm, aspect="auto", cmap="Oranges", vmin=0, vmax=1)
    axes[1].set_xticks(range(len(metrics_short)))
    axes[1].set_xticklabels(metrics_short)
    axes[1].set_yticks(range(len(short)))
    axes[1].set_yticklabels(short)
    for i in range(len(short)):
        for j in range(len(metrics)):
            axes[1].text(j, i, f"{matrix2[i,j]:.1f}", ha="center", va="center",
                         color="black")
    axes[1].set_title("(b) Programmatic structural metrics (rater-independent)")
    fig.suptitle("PhL-18 · Pre-registration writing quality",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(PLOT_PATH, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[PhL-18] plot saved: {PLOT_PATH}")


def _write_summary(summary: dict) -> None:
    md = ["# PhL-18 — Pre-registration writing quality", "",
          "**Question:** how rigorously can each model write a scientific",
          "pre-registration that BINDS before the fit?", "",
          "## Design", "",
          "- 5 hypotheses (ccRCC metastasis, IMmotion, BRCA cross-cancer,",
          "  SLC22A8 extension, PRAD generalization).",
          "- 3 models × 5 = **15 pre-registration YAMLs**.",
          "- Two scoring dimensions:",
          "  - **Programmatic structural** (rater-independent): required keys",
          "    coverage, numeric-value density, kill-test list items, biology",
          "    grounding term count.",
          "  - **Blind-rated rubric** (Opus 4.7 meta-rater, model labels",
          "    hidden): threshold specificity, kill-test coverage,",
          "    falsifiability, biology grounding, scope discipline. Each 0-10.",
          "",
          "**Self-preference-bias caveat**: the Opus rater could favour Opus",
          "YAMLs. Mitigation: (a) labels hidden behind `Candidate_A/B/C` with",
          "random order, (b) programmatic structural metrics reported",
          "alongside as rater-independent signal.",
          "",
          "## Rubric scores (blind-rated)", "",
          "| Model | Threshold | Kill-test | Falsifiability | Biology | Scope |",
          "|---|---|---|---|---|---|"]
    for m in MODELS:
        r = summary["rubric"].get(m, {})
        short = m.split("-")[1]
        md.append(f"| {short} | {r.get('threshold_specificity', 0):.1f} | "
                  f"{r.get('kill_test_coverage', 0):.1f} | "
                  f"{r.get('falsifiability', 0):.1f} | "
                  f"{r.get('biology_grounding', 0):.1f} | "
                  f"{r.get('scope_discipline', 0):.1f} |")
    md.extend(["", "## Structural metrics (rater-independent)", "",
               "| Model | Key coverage % | Mean numeric values | Mean kill tests | Mean biology terms |",
               "|---|---|---|---|---|"])
    for m in MODELS:
        s = summary["structural"].get(m, {})
        short = m.split("-")[1]
        md.append(f"| {short} | {s.get('required_keys_coverage_pct', 0):.1f} | "
                  f"{s.get('mean_numeric_values', 0):.1f} | "
                  f"{s.get('mean_kill_test_items', 0):.1f} | "
                  f"{s.get('mean_biology_grounding', 0):.1f} |")
    md.extend(["", "## Interpretation", ""])
    rubric = summary["rubric"]
    opus_rubric_sum = sum(rubric.get("claude-opus-4-7", {}).values())
    sonnet_rubric_sum = sum(rubric.get("claude-sonnet-4-6", {}).values())
    haiku_rubric_sum = sum(rubric.get("claude-haiku-4-5", {}).values())
    if opus_rubric_sum > max(sonnet_rubric_sum, haiku_rubric_sum):
        md.append(f"**Opus 4.7 scored highest on rubric** ({opus_rubric_sum:.1f}/50 vs "
                  f"Sonnet {sonnet_rubric_sum:.1f}, Haiku {haiku_rubric_sum:.1f}). "
                  "Confirmed on the structural side if structural metrics also show "
                  "higher key coverage + more numeric thresholds.")
    else:
        md.append(f"**Rubric winner**: "
                  f"{max(rubric, key=lambda m: sum(rubric[m].values())).split('-')[1]}. "
                  "Honest finding — pre-reg writing quality is not uniformly Opus-dominant.")
    md.extend(["", "## Reproduce", "```bash",
               "source ~/.api_keys",
               "PYTHONPATH=src .venv/bin/python src/phl18_prereg_writing_quality.py write",
               "PYTHONPATH=src .venv/bin/python src/phl18_prereg_writing_quality.py rate",
               "PYTHONPATH=src .venv/bin/python src/phl18_prereg_writing_quality.py analyze",
               "```"])
    SUMMARY_PATH.write_text("\n".join(md))


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("write")
    sub.add_parser("rate")
    sub.add_parser("analyze")
    args = p.parse_args()
    if args.cmd == "write":
        run_write()
    elif args.cmd == "rate":
        run_rate()
    elif args.cmd == "analyze":
        analyze()


if __name__ == "__main__":
    main()
