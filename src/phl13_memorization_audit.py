#!/usr/bin/env python3
"""PhL-13 — memorization audit on the TOP2A-EPAS1 survivor.

[LLM-SRBench, arXiv 2504.10415, ICML 2025](https://arxiv.org/abs/2504.10415)
flagged that LLM-SR-style pipelines on Feynman problems often
"rediscover" memorized rather than genuinely searched equations.
Our flagship survivor `TOP2A − EPAS1` on TCGA-KIRC metastasis is
scientifically interesting precisely because PySR returned it
unconstrained from a 45-gene panel. To distinguish discovery from
retrieval, we run a **zero-shot memorization probe**:

  Turn 1 — Opus 4.7 is asked to propose the top 2-gene pair for
    ccRCC metastasis prediction, WITHOUT access to any cohort data.
    We record how often TOP2A-EPAS1 (or its structural twin
    proliferation−HIF-2α) appears in its top picks across repeats.

  Turn 2 — Opus 4.7 is shown the PySR search result (TOP2A-EPAS1
    at AUROC 0.726) and asked: "Is this a known law or a discovery?"
    We record whether it cites ccA/ccB subtype literature unprompted.

If TOP2A-EPAS1 is the *first* zero-shot suggestion in ≥ 5/10 repeats:
strong memorization signal. If it appears in 0-1/10: strong discovery
signal. Anywhere in between: honest report of what we observed.

This is ONE API-call surface (Messages API, not Managed Agents), kept
deliberately tight so the audit cost is trivial and the result is
reproducible line-by-line.

Cost: ~$0.25 across ~12 short Opus 4.7 Messages calls.
Usage:
    source ~/.api_keys
    PYTHONPATH=src .venv/bin/python src/phl13_memorization_audit.py
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

import anthropic

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "results" / "live_evidence" / "phl13_memorization_audit"

N_REPEATS = 10
MODEL = "claude-opus-4-7"


ZERO_SHOT_PROMPT = (
    "You are a computational biologist. I have NOT shown you any "
    "cohort data, statistical results, or literature citations.\n\n"
    "Task: propose the SINGLE best 2-gene compact law (form `GENE_A "
    "− GENE_B` or `GENE_A + GENE_B` or `GENE_A × GENE_B`, using raw "
    "or log-transformed expression) that you predict would MOST "
    "STRONGLY separate metastatic (M1) from non-metastatic (M0) "
    "clear-cell renal cell carcinoma (ccRCC) tumors on TCGA-KIRC "
    "RNA-seq.\n\n"
    "Emit strict JSON: "
    '{"top_pick": {"gene_a": ..., "gene_b": ..., "operator": ..., '
    '"transform": ...}, '
    '"runner_up": {"gene_a": ..., "gene_b": ..., "operator": ..., '
    '"transform": ...}, '
    '"brief_reasoning": "≤ 30 words"}. '
    "No hedging. Pick the two genes you believe most strongly "
    "carry the metastasis signal."
)

LITERATURE_CHECK_PROMPT = (
    "A researcher ran unconstrained symbolic regression on a 45-gene "
    "TCGA-KIRC metastasis panel. The simplest surviving law was: "
    "`TOP2A − EPAS1` at AUROC 0.726 (n=505, M1 prevalence 16%).\n\n"
    "Question: is `TOP2A − EPAS1` on ccRCC metastasis (a) a known "
    "published biological signature, (b) structurally equivalent to "
    "a known subtype axis, or (c) a novel compact finding?\n\n"
    "Emit strict JSON: "
    '{"category": "known_signature|structurally_equivalent_to_known|'
    'novel", "cited_prior_work": [...], "explanation": "≤ 60 words"}.'
)


def _call_opus(client, prompt: str) -> dict:
    """One Messages call. Return parsed JSON + raw text."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(
        getattr(b, "text", "") for b in resp.content
        if getattr(b, "type", "") == "text"
    )
    parsed = None
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    candidate = m.group(1) if m else None
    if candidate is None:
        first, last = text.find("{"), text.rfind("}")
        if first != -1 and last > first:
            candidate = text[first:last + 1]
    if candidate:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            pass
    return {"raw_text": text, "parsed": parsed,
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens}


PROLIF_GENES = {"top2a", "mki67", "cdk1", "ccnb1", "pcna", "mcm2", "ccna2"}
HIF_GENES = {"epas1", "hif1a", "hif2a", "vhl"}


def _classify_pick(pick: dict) -> dict:
    if not pick:
        return {"is_top2a_epas1_exact": False,
                "is_prolif_minus_hif": False,
                "gene_a": None, "gene_b": None}
    a = (pick.get("gene_a") or "").strip().upper()
    b = (pick.get("gene_b") or "").strip().upper()
    exact = {a, b} == {"TOP2A", "EPAS1"}
    prolif_hif = (
        (a.lower() in PROLIF_GENES and b.lower() in HIF_GENES) or
        (b.lower() in PROLIF_GENES and a.lower() in HIF_GENES)
    )
    return {"is_top2a_epas1_exact": exact,
            "is_prolif_minus_hif": prolif_hif,
            "gene_a": a, "gene_b": b,
            "operator": pick.get("operator")}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = anthropic.Anthropic()

    # --------------------------------------------------------------
    # Zero-shot: ask Opus 4.7 the best 2-gene ccRCC metastasis law
    # WITHOUT showing any cohort data. Repeat N times for stability.
    # --------------------------------------------------------------
    print(f">>> Zero-shot probe: {N_REPEATS} repeats on {MODEL}")
    zero_shot_runs = []
    total_cost_tokens = 0
    for i in range(N_REPEATS):
        r = _call_opus(client, ZERO_SHOT_PROMPT)
        total_cost_tokens += r["input_tokens"] + r["output_tokens"]
        top_cls = _classify_pick((r["parsed"] or {}).get("top_pick"))
        runner_cls = _classify_pick((r["parsed"] or {}).get("runner_up"))
        zero_shot_runs.append({
            "repeat": i,
            "parsed_ok": r["parsed"] is not None,
            "top_pick_raw": (r["parsed"] or {}).get("top_pick"),
            "runner_up_raw": (r["parsed"] or {}).get("runner_up"),
            "top_pick_classification": top_cls,
            "runner_up_classification": runner_cls,
            "brief_reasoning": (r["parsed"] or {}).get("brief_reasoning"),
            "raw_text_preview": r["raw_text"][:400],
        })
        print(f"    repeat {i}: top=({top_cls['gene_a']}, "
              f"{top_cls['gene_b']}) exact_top2a_epas1="
              f"{top_cls['is_top2a_epas1_exact']} "
              f"prolif_minus_hif={top_cls['is_prolif_minus_hif']}")

    n_exact_top = sum(1 for r in zero_shot_runs
                      if r["top_pick_classification"]["is_top2a_epas1_exact"])
    n_prolif_hif_top = sum(
        1 for r in zero_shot_runs
        if r["top_pick_classification"]["is_prolif_minus_hif"]
    )
    n_prolif_hif_anywhere = sum(
        1 for r in zero_shot_runs
        if (r["top_pick_classification"]["is_prolif_minus_hif"]
            or r["runner_up_classification"]["is_prolif_minus_hif"])
    )

    print(f"\n    TOP2A-EPAS1 exact as top pick: {n_exact_top}/{N_REPEATS}")
    print(f"    Proliferation-HIF form as top: {n_prolif_hif_top}/{N_REPEATS}")
    print(f"    Proliferation-HIF form anywhere: {n_prolif_hif_anywhere}/{N_REPEATS}")

    # --------------------------------------------------------------
    # Literature anchor: ask Opus 4.7 whether TOP2A-EPAS1 is known
    # --------------------------------------------------------------
    print(f"\n>>> Literature anchor probe: 2 repeats on {MODEL}")
    lit_runs = []
    for i in range(2):
        r = _call_opus(client, LITERATURE_CHECK_PROMPT)
        total_cost_tokens += r["input_tokens"] + r["output_tokens"]
        lit_runs.append({
            "repeat": i,
            "parsed_ok": r["parsed"] is not None,
            "category": (r["parsed"] or {}).get("category"),
            "cited_prior_work": (r["parsed"] or {}).get("cited_prior_work"),
            "explanation": (r["parsed"] or {}).get("explanation"),
            "raw_text_preview": r["raw_text"][:400],
        })
        print(f"    repeat {i}: category="
              f"{(r['parsed'] or {}).get('category')}")

    # --------------------------------------------------------------
    # Honest interpretation
    # --------------------------------------------------------------
    if n_exact_top >= 5:
        interpretation = (
            "STRONG MEMORIZATION SIGNAL. Opus 4.7 returns TOP2A-EPAS1 "
            "as its zero-shot top pick in "
            f"{n_exact_top}/{N_REPEATS} repeats without seeing any "
            "cohort data. The PySR 'rediscovery' is better framed "
            "as pipeline-scale confirmation of a prior the model "
            "already carries."
        )
    elif n_prolif_hif_top >= 5:
        interpretation = (
            "STRUCTURAL PRIOR, NOT EXACT. Opus 4.7 returns a "
            "proliferation-vs-HIF-2α form as its top pick in "
            f"{n_prolif_hif_top}/{N_REPEATS} repeats but the exact "
            "TOP2A-EPAS1 pair is the top pick in only "
            f"{n_exact_top}/{N_REPEATS}. The subtype axis family is "
            "in the model's prior; the specific 2-gene form emerged "
            "from unconstrained PySR on the actual cohort."
        )
    elif n_exact_top <= 1 and n_prolif_hif_anywhere <= 2:
        interpretation = (
            "DISCOVERY SIGNAL. TOP2A-EPAS1 is the zero-shot top pick "
            f"in only {n_exact_top}/{N_REPEATS} repeats and the "
            "proliferation-HIF structural family appears only "
            f"{n_prolif_hif_anywhere}/{N_REPEATS} times across top + "
            "runner-up picks. PySR found something the model did not "
            "retrieve from its prior."
        )
    else:
        interpretation = (
            f"MIXED: TOP2A-EPAS1 exact in {n_exact_top}/{N_REPEATS} "
            f"top picks; proliferation-HIF anywhere in "
            f"{n_prolif_hif_anywhere}/{N_REPEATS}. The structural "
            "family is partially in the model's prior, the exact pair "
            "is not fully retrieved zero-shot."
        )
    print(f"\n>>> Interpretation: {interpretation}")

    verdict = {
        "hypothesis_id": "phl13_memorization_audit",
        "run_date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": MODEL,
        "n_repeats_zero_shot": N_REPEATS,
        "n_exact_top2a_epas1_as_top_pick": n_exact_top,
        "n_proliferation_hif_as_top_pick": n_prolif_hif_top,
        "n_proliferation_hif_anywhere": n_prolif_hif_anywhere,
        "literature_check_categories": [r.get("category") for r in lit_runs],
        "interpretation": interpretation,
        "total_tokens": total_cost_tokens,
        "zero_shot_runs": zero_shot_runs,
        "literature_check_runs": lit_runs,
    }

    (OUT_DIR / "verdict.json").write_text(json.dumps(verdict, indent=2))
    print(f"\n>>> Artefacts: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
