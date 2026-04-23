#!/usr/bin/env python3
"""H2 — 1M Context Synthesis via Opus 4.7.

Lane H: Opus 4.7 capability overhang demonstration.

Design:
  - Load all rejection records across every run + the 9 known survivors.
  - Append key published paper abstracts (ccA/ccB axis, ClearCode34, POPPER, AI Scientist v2).
  - Send the entire corpus to Opus 4.7 in a single 1M-context prompt.
  - Question: "Given 100+ rejections and these 9 survivors, propose 5 equation
    skeletons NOT yet tried, plus mathematical structure invariant conditions
    that any valid ccRCC law must satisfy."
  - Writes a structured JSON report to results/overhang/synthesis_1m.json.

Requires: ANTHROPIC_API_KEY in environment.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from theory_copilot.cost_ledger import log_usage

try:
    import anthropic
    _HAS_ANTHROPIC = True
except ImportError:
    _HAS_ANTHROPIC = False


# ---------------------------------------------------------------------------
# Published abstracts (embedded; these are published prior art, not novel text)
# ---------------------------------------------------------------------------

PAPER_ABSTRACTS = [
    {
        "title": "Molecular stratification of clear cell renal cell carcinoma by consensus clustering reveals distinct subtypes and survival patterns (Brannon et al. 2010, PMID 20871783)",
        "abstract": (
            "Clear cell renal cell carcinoma (ccRCC) tumors were stratified by consensus "
            "clustering into two major subtypes: ccA (differentiated, HIF-2α high, VHL "
            "mutant, better prognosis) and ccB (dedifferentiated, proliferative, aggressive, "
            "worse prognosis). The ccB subtype is characterized by elevated TOP2A, MKI67, "
            "CCNB1 (proliferation program) and reduced EPAS1 (HIF-2α) relative expression. "
            "The ccA/ccB axis is a reproducible transcriptomic partition of ccRCC that "
            "predicts cancer-specific survival."
        ),
    },
    {
        "title": "ClearCode34 classifier for clear cell renal cell carcinoma subtypes (Brooks et al. 2014, DOI 10.1016/j.eururo.2014.02.035)",
        "abstract": (
            "A 34-gene classifier (ClearCode34) was developed to assign ccRCC tumors to "
            "ccA and ccB subtypes. Genes upregulated in ccB include TOP2A, MKI67, PCNA, "
            "CDK1 (proliferation). Genes upregulated in ccA include EPAS1 and downstream "
            "HIF-2α targets. The ClearCode34 classifier was validated in independent TCGA "
            "cohorts and its prognostic value was confirmed. The ccB subtype is associated "
            "with a higher rate of metastasis at diagnosis."
        ),
    },
    {
        "title": "TOP2A overexpression predicts poor prognosis in ccRCC (2024, PMID 38730293)",
        "abstract": (
            "Topoisomerase IIα (TOP2A) expression is significantly elevated in ccRCC "
            "compared to adjacent normal kidney tissue. High TOP2A expression correlates "
            "with advanced tumor stage, lymph node metastasis, and shorter overall survival. "
            "TOP2A promotes tumor cell proliferation, invasion, and metastasis. The prognostic "
            "value of TOP2A is independent of EPAS1 / HIF-2α expression status."
        ),
    },
    {
        "title": "POPPER: Falsification-oriented AI hypothesis testing (arXiv 2502.09858)",
        "abstract": (
            "POPPER is a framework for AI-driven hypothesis testing that explicitly operationalizes "
            "Popperian falsification. It constructs probabilistic null hypotheses, generates "
            "adversarial test cases, and rejects hypotheses that fail across multiple "
            "perturbations. Key insight: LLM-generated hypotheses routinely survive "
            "confirmation-oriented tests but fail when subjected to adversarial falsification. "
            "Pre-registration of falsification criteria before observing data is essential "
            "to prevent p-hacking by the proposer model."
        ),
    },
    {
        "title": "Sakana AI Scientist v2 (arXiv 2504.08066)",
        "abstract": (
            "The AI Scientist v2 automates the full cycle of scientific discovery: hypothesis "
            "generation, experiment design, result analysis, and paper writing. Key improvement "
            "over v1: multi-step verification loops that include adversarial review of each "
            "result before it advances. The system demonstrates that iterative falsification "
            "within the discovery loop reduces spurious findings compared to single-shot "
            "hypothesis generation. The architecture separates the Proposer agent (hypothesis "
            "generation) from the Verifier agent (adversarial review) to prevent confirmation "
            "bias cascade."
        ),
    },
]


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

def load_all_rejections_and_survivors(repo_root: Path) -> tuple[list[dict], list[dict]]:
    """Aggregate rejection and survivor records across all result directories."""
    rejections: list[dict] = []
    survivors: list[dict] = []

    for report_path in repo_root.glob("results/*/falsification_report.json"):
        try:
            records = json.loads(report_path.read_text())
        except Exception:
            continue
        source = report_path.parent.name
        for r in records:
            r["_source"] = source
            if r.get("passes"):
                survivors.append(r)
            else:
                rejections.append(r)

    # Also check QA runs
    for report_path in repo_root.glob("results/qa/*.json"):
        try:
            records = json.loads(report_path.read_text())
        except Exception:
            continue
        if not isinstance(records, list):
            continue
        source = f"qa/{report_path.stem}"
        for r in records:
            r["_source"] = source
            if r.get("passes"):
                survivors.append(r)
            else:
                rejections.append(r)

    return rejections, survivors


def _fmt(v: Any) -> str:
    return f"{v:.3f}" if isinstance(v, float) else str(v)


def _summarize_rejection(r: dict) -> str:
    eq = r.get("equation", "?")[:60]
    fail = r.get("fail_reason", r.get("passes", "?"))
    auc = _fmt(r.get("law_auc", r.get("auroc", "?")))
    delta = _fmt(r.get("delta_baseline", "?"))
    src = r.get("_source", "?")
    return f"  eq={eq} | fail={fail} | auc={auc} | delta_base={delta} | src={src}"


def _summarize_survivor(s: dict) -> str:
    eq = s.get("equation", "?")[:80]
    auc = _fmt(s.get("law_auc", s.get("auroc", "?")))
    delta = _fmt(s.get("delta_baseline", "?"))
    src = s.get("_source", "?")
    return f"  eq={eq} | auc={auc} | delta_base={delta} | src={src}"


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

_SYSTEM_1M_SYNTHESIS = """\
You are Opus 4.7 performing a large-context synthesis over a complete biological law discovery campaign.

You have been given:
1. A full list of REJECTED equation candidates (across all runs, with their gate failure reasons and metrics).
2. A list of SURVIVOR equations (those that passed all falsification gates).
3. Abstracts from key published papers about the biology (ccRCC subtypes) and AI-for-Science methodology.
4. A description of the falsification gate thresholds.

Your task — answer in two parts:

PART 1 — "Next 5 equation skeletons to explore":
Propose 5 equation skeletons NOT yet tried in the rejection corpus above.
For each, specify:
- The symbolic expression (using gene names)
- Which pathway boundary it crosses
- Why it might beat the delta_baseline gate (the dominant failure mode)
- An ex-ante skeptic test: what pattern of gate metrics would falsify it

PART 2 — "Mathematical structure invariant conditions":
Based on the rejection pattern (all failing on delta_baseline, survivors using Proliferation − HIF-2α),
identify 3-5 mathematical invariant conditions that any valid ccRCC law MUST satisfy to have a
realistic chance of passing the gate. These are structural conditions, not biological hypotheses.
Example format: "The compound must involve at least one Proliferation marker and one HIF/tubule
anti-marker, since CA9-alone saturates at AUROC 0.965 and any purely-HIF compound cannot clear +0.05."

Gate thresholds (pre-registered):
- perm_p < 0.05 (two-sided permutation null, 1000 shuffles)
- ci_lower > 0.60 (bootstrap 95% CI lower bound on AUROC)
- delta_baseline > 0.05 (compound AUROC minus best single-gene AUROC, sign-invariant)
- delta_confound > 0.03 (incremental over covariates)
- decoy_p < 0.05 (must beat 95th percentile of 100 random gene AUROCs)

Output format: valid JSON only, matching this schema:
{
  "next_skeletons": [
    {
      "rank": 1,
      "skeleton": "symbolic expression with gene names",
      "pathway_crossing": "e.g. Proliferation × Warburg",
      "delta_baseline_hypothesis": "why this should beat +0.05",
      "ex_ante_skeptic_test": "what failure pattern would falsify this"
    }
  ],
  "invariant_conditions": [
    {
      "rank": 1,
      "condition": "statement of the invariant",
      "supporting_evidence": "which rejections/survivors support this"
    }
  ],
  "synthesis_summary": "3-5 sentence synthesis of the campaign pattern"
}
"""


def build_1m_prompt(
    rejections: list[dict],
    survivors: list[dict],
    abstracts: list[dict],
) -> str:
    lines = [
        "=" * 70,
        "COMPLETE REJECTION CORPUS",
        f"({len(rejections)} total rejections across all runs)",
        "=" * 70,
        "",
    ]

    # Group by fail_reason for clarity
    from collections import Counter, defaultdict
    by_fail: dict[str, list] = defaultdict(list)
    for r in rejections:
        by_fail[r.get("fail_reason", "unknown")].append(r)

    for fail_reason, recs in sorted(by_fail.items(), key=lambda x: -len(x[1])):
        lines.append(f"\nFail reason: {fail_reason!r} ({len(recs)} rejections)")
        for r in recs[:20]:  # cap per category to avoid absurd lengths
            lines.append(_summarize_rejection(r))
        if len(recs) > 20:
            lines.append(f"  ... and {len(recs) - 20} more with the same failure")

    lines += [
        "",
        "=" * 70,
        "SURVIVORS (equations that passed all gates)",
        f"({len(survivors)} total survivors)",
        "=" * 70,
        "",
    ]
    for s in survivors:
        lines.append(_summarize_survivor(s))

    lines += [
        "",
        "=" * 70,
        "PUBLISHED PAPER ABSTRACTS (prior art + methodology context)",
        "=" * 70,
        "",
    ]
    for paper in abstracts:
        lines.append(f"\n## {paper['title']}")
        lines.append(paper["abstract"])

    lines += [
        "",
        "=" * 70,
        "TASK",
        "=" * 70,
        "",
        "Given the complete corpus above:",
        "1. Propose 5 equation skeletons not yet tried in the rejection corpus.",
        "2. Identify 3-5 mathematical invariant conditions any valid ccRCC law must satisfy.",
        "",
        "Output ONLY the JSON as specified in the system prompt.",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Opus 4.7 1M-context call
# ---------------------------------------------------------------------------

def call_opus_1m(prompt: str, dry_run: bool = False) -> dict[str, Any]:
    if dry_run or not _HAS_ANTHROPIC:
        return {
            "next_skeletons": [],
            "invariant_conditions": [],
            "synthesis_summary": "[dry-run: no API call made]",
            "_dry_run": True,
        }

    ac = anthropic.Anthropic()
    print("[H2] Calling Opus 4.7 with 1M-context prompt ...")
    print(f"[H2] Prompt length: {len(prompt):,} chars")

    t0 = time.time()
    try:
        with ac.messages.stream(
            model="claude-opus-4-7",
            max_tokens=8000,
            thinking={"type": "adaptive", "display": "summarized"},
            system=_SYSTEM_1M_SYNTHESIS,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            final = stream.get_final_message()
    except Exception as exc:
        print(f"[H2] API error: {exc}", file=sys.stderr)
        return {"error": str(exc), "next_skeletons": [], "invariant_conditions": []}

    elapsed = time.time() - t0
    log_usage("claude-opus-4-7", "synthesis_h2_1m", getattr(final, "usage", None))
    print(f"[H2] Done in {elapsed:.1f}s")

    text = ""
    thinking = ""
    for block in final.content:
        if block.type == "text":
            text += block.text
        elif block.type == "thinking":
            thinking += block.thinking

    # Parse JSON from response
    start = text.find("{")
    end = text.rfind("}") + 1
    result: dict[str, Any] = {}
    if start >= 0 and end > start:
        try:
            result = json.loads(text[start:end])
        except json.JSONDecodeError:
            result = {"raw_response": text}
    else:
        result = {"raw_response": text}

    result["_thinking_excerpt"] = thinking[:2000] if thinking else ""
    result["_elapsed_sec"] = round(elapsed, 1)
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="H2 — 1M Context Synthesis (Lane H)",
    )
    parser.add_argument("--repo-root", default=".",
                        help="Root of theory-copilot-falsification repo")
    parser.add_argument("--output", default="results/overhang/synthesis_1m.json")
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip API call, write prompt only")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if not (repo_root / "src").exists():
        repo_root = Path(__file__).parents[1]

    print(f"[H2] Repo root: {repo_root}")

    rejections, survivors = load_all_rejections_and_survivors(repo_root)
    print(f"[H2] Loaded {len(rejections)} rejections, {len(survivors)} survivors")

    prompt = build_1m_prompt(rejections, survivors, PAPER_ABSTRACTS)

    if args.dry_run:
        prompt_path = Path(args.output).with_suffix(".prompt.txt")
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt)
        print(f"[H2] Dry run: prompt written to {prompt_path}")
        result = {"_dry_run": True, "prompt_chars": len(prompt),
                  "rejections_loaded": len(rejections),
                  "survivors_loaded": len(survivors)}
    else:
        result = call_opus_1m(prompt, dry_run=False)

    result["_meta"] = {
        "rejections_loaded": len(rejections),
        "survivors_loaded": len(survivors),
        "papers_included": len(PAPER_ABSTRACTS),
        "prompt_chars": len(prompt),
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, default=str))
    print(f"[H2] Results written to {out_path}")

    # Print key outputs
    if "next_skeletons" in result:
        print("\n[H2] Proposed skeletons:")
        for sk in result["next_skeletons"]:
            print(f"  {sk.get('rank','?')}. {sk.get('skeleton','?')} | {sk.get('pathway_crossing','?')}")

    if "invariant_conditions" in result:
        print("\n[H2] Invariant conditions:")
        for ic in result["invariant_conditions"]:
            print(f"  {ic.get('rank','?')}. {ic.get('condition','?')[:100]}")

    if "synthesis_summary" in result:
        print(f"\n[H2] Synthesis summary: {result['synthesis_summary'][:300]}")


if __name__ == "__main__":
    main()
