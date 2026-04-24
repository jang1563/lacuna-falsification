#!/usr/bin/env python3
"""PhL-19 — Interpreter mechanism hypothesis depth.

Question: for a gate-accepted survivor, how deep / disciplined is each
model's biological interpretation?

Design:
- 3 survivors (TOP2A-EPAS1, MKI67-EPAS1, 5-gene MKI67-vs-compound).
- 3 models × 3 survivors = 9 interpretations.
- Blind rubric + programmatic checks:
  - Biological specificity: named pathways, named genes beyond the law
  - Caveat depth: "what this is NOT" statements, honest limits
  - Testable prediction: specific experiment that could extend/refute
  - Prior-art citation: PMID / DOI / year references

Outputs:
  results/live_evidence/phl19_interpreter_depth/interpretations.jsonl
  results/live_evidence/phl19_interpreter_depth/ratings.jsonl
  results/live_evidence/phl19_interpreter_depth/verdict.json
  results/live_evidence/phl19_interpreter_depth/SUMMARY.md
  results/live_evidence/phl19_interpreter_depth/quality_heatmap.png
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
OUT = REPO / "results" / "live_evidence" / "phl19_interpreter_depth"
OUT.mkdir(parents=True, exist_ok=True)

INTERP_PATH = OUT / "interpretations.jsonl"
RATINGS_PATH = OUT / "ratings.jsonl"
VERDICT_PATH = OUT / "verdict.json"
SUMMARY_PATH = OUT / "SUMMARY.md"
PLOT_PATH = OUT / "quality_heatmap.png"

MODELS = ["claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5"]

SURVIVORS = [
    {"id": "top2a_epas1", "equation": "TOP2A - EPAS1",
     "cohort": "TCGA-KIRC metastasis (n=505, 16% M1)",
     "metrics": "AUROC 0.726, Δ_baseline +0.069, perm_p=0, decoy_p=0.001, CI_lower=0.665"},
    {"id": "mki67_epas1", "equation": "MKI67 - EPAS1",
     "cohort": "TCGA-KIRC metastasis (n=505, 16% M1)",
     "metrics": "AUROC 0.708, Δ_baseline +0.051, perm_p=0, decoy_p=0.003"},
    {"id": "5gene", "equation": "MKI67 - (EPAS1 + LRP2 + PTGER3 + RPL13A)/4",
     "cohort": "TCGA-KIRC metastasis (n=505, 16% M1)",
     "metrics": "AUROC 0.726, Δ_baseline +0.069, decoy_p=0 (stress-test compound)"},
]

INTERPRETER_SYSTEM = """\
You are a biology interpreter for a gate-accepted compact law that has
just passed a pre-registered 5-test falsification gate. Your job is to
write a disciplined mechanism hypothesis.

Output JSON with these keys:
{
  "mechanism_hypothesis": "2-3 sentence biological mechanism — cite
    specific pathways and gene roles",
  "what_this_is_not": "honest 1-2 sentence caveat — what the finding does
    NOT claim (not diagnostic, not novel biology, etc.)",
  "testable_prediction": "one specific downstream experiment that would
    extend or refute — be concrete (KO, cohort, assay)",
  "prior_art_citations": ["PMID xxxx or DOI / paper reference", ...]
}

Use specific gene symbols, pathway names, and PMIDs where you can.
No markdown fences — just raw JSON.
"""


def _extract_json(text: str) -> dict | None:
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def _one_interp(client: Any, model: str, survivor: dict) -> dict[str, Any]:
    user_msg = (
        f"The following compact law PASSED the pre-registered "
        f"5-test falsification gate:\n\n"
        f"Equation: {survivor['equation']}\n"
        f"Cohort: {survivor['cohort']}\n"
        f"Metrics: {survivor['metrics']}\n\n"
        "Write the mechanism hypothesis JSON now."
    )
    try:
        with client.messages.stream(
            model=model,
            max_tokens=3000,
            thinking={"type": "adaptive", "display": "summarized"},
            system=INTERPRETER_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        ) as stream:
            final = stream.get_final_message()
        text = ""
        for block in final.content:
            if getattr(block, "type", "") == "text":
                text += getattr(block, "text", "")
        parsed = _extract_json(text)
        return {
            "model": model,
            "survivor_id": survivor["id"],
            "equation": survivor["equation"],
            "response_text": text,
            "parsed": parsed if parsed else {"err": "parse_fail", "raw": text[:300]},
        }
    except Exception as e:
        return {"model": model, "survivor_id": survivor["id"], "err": str(e)[:200]}


def run_interp() -> None:
    import anthropic
    client = anthropic.Anthropic()
    rows: list[dict] = []
    for model in MODELS:
        print(f"[PhL-19] interpreter pass with {model}...")
        for s in SURVIVORS:
            r = _one_interp(client, model, s)
            rows.append(r)
    with INTERP_PATH.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"[PhL-19] {len(rows)} interpretations saved: {INTERP_PATH}")


# ---------------------------------------------------------------------------
# Programmatic checks
# ---------------------------------------------------------------------------

PMID_RE = re.compile(r"PMID\s*:?\s*\d+|DOI\s*:?\s*10\.\d+/\S+|arXiv\s*:?\s*\d+\.\d+|\([12]\d{3}\)")
PATHWAY_TERMS = {"HIF", "VHL", "Warburg", "glycolysis", "proliferation", "cell cycle",
                 "hypoxia", "oxidative phosphorylation", "EMT", "TCA",
                 "renal tubule", "tubule", "mTOR", "PI3K", "AMPK", "MYC",
                 "apoptosis", "angiogenesis", "immune", "infiltrat"}


def struct_check_interp(parsed: dict, response_text: str) -> dict[str, Any]:
    """Programmatic checks independent of the rater."""
    if not isinstance(parsed, dict):
        return {"mech_present": False, "caveat_present": False,
                "prediction_present": False, "citation_count": 0,
                "pathway_mentions": 0, "mech_len_chars": 0,
                "prediction_len_chars": 0}
    mech = parsed.get("mechanism_hypothesis", "") if isinstance(parsed.get("mechanism_hypothesis"), str) else ""
    caveat = parsed.get("what_this_is_not", "") if isinstance(parsed.get("what_this_is_not"), str) else ""
    prediction = parsed.get("testable_prediction", "") if isinstance(parsed.get("testable_prediction"), str) else ""
    citations = parsed.get("prior_art_citations", [])
    if not isinstance(citations, list):
        citations = [str(citations)] if citations else []
    all_text = mech + " " + caveat + " " + prediction + " " + response_text
    pmid_matches = len(PMID_RE.findall(all_text))
    pw = sum(1 for term in PATHWAY_TERMS if term.lower() in all_text.lower())
    return {
        "mech_present": bool(mech),
        "caveat_present": bool(caveat),
        "prediction_present": bool(prediction),
        "citation_count": len(citations) + pmid_matches,
        "pathway_mentions": pw,
        "mech_len_chars": len(mech),
        "prediction_len_chars": len(prediction),
    }


# ---------------------------------------------------------------------------
# Rubric rating
# ---------------------------------------------------------------------------

RATER_SYSTEM = """\
You are a blind rubric rater for biological-interpretation quality. You
see three mechanism JSONs labelled Candidate_A/B/C (order randomized).
Do NOT guess model identity.

Rate each 0-10 on:
1. BIOLOGICAL_SPECIFICITY: named pathways and specific gene roles
2. CAVEAT_DEPTH: honest discipline — "what this is NOT", scope limits
3. TESTABILITY: is the testable prediction a CONCRETE experiment?
4. PRIOR_ART: does it cite relevant literature (PMIDs, DOIs, years)?
5. OVERALL_TRUSTWORTHINESS: would a ccRCC domain expert trust this?

Return JSON:
{
  "Candidate_A": {"biological_specificity": 0-10, "caveat_depth": 0-10,
                  "testability": 0-10, "prior_art": 0-10,
                  "overall_trustworthiness": 0-10, "notes": "one sentence"},
  "Candidate_B": {...}, "Candidate_C": {...}
}
No markdown fences — just JSON.
"""


def _rate_triplet(client: Any, triplet: dict, mapping: dict) -> dict:
    user_msg = (
        "Rate these three mechanism-hypothesis outputs:\n\n"
        + "\n\n---\n\n".join(
            f"### {k}\n\n```json\n{json.dumps(v, indent=2)}\n```"
            for k, v in triplet.items())
        + "\n\nReturn the JSON rubric."
    )
    try:
        with client.messages.stream(
            model="claude-opus-4-7",
            max_tokens=1500,
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
            return {"err": "no_json", "mapping": mapping}
        try:
            return {"ratings": json.loads(m.group(0)), "mapping": mapping}
        except Exception as e:
            return {"err": f"parse: {e}", "mapping": mapping, "raw": text[:300]}
    except Exception as e:
        return {"err": str(e)[:200], "mapping": mapping}


def run_rate() -> None:
    import anthropic
    if not INTERP_PATH.exists():
        print("ERROR: run interp first.", file=sys.stderr)
        sys.exit(1)
    client = anthropic.Anthropic()
    rows = [json.loads(l) for l in INTERP_PATH.read_text().splitlines() if l]
    rng = random.Random(73)
    rating_rows: list[dict] = []
    survivor_ids = sorted({r["survivor_id"] for r in rows})
    for sid in survivor_ids:
        subset = {r["model"]: r["parsed"] for r in rows
                  if r["survivor_id"] == sid and isinstance(r.get("parsed"), dict)
                  and "err" not in r["parsed"]}
        if len(subset) < 3:
            continue
        models_shuffled = list(subset.keys())
        rng.shuffle(models_shuffled)
        triplet_keys = ["Candidate_A", "Candidate_B", "Candidate_C"]
        triplet = {tk: subset[m] for tk, m in zip(triplet_keys, models_shuffled)}
        mapping = {tk: m for tk, m in zip(triplet_keys, models_shuffled)}
        print(f"[PhL-19] rating triplet for {sid}")
        result = _rate_triplet(client, triplet, mapping)
        result["survivor_id"] = sid
        rating_rows.append(result)
    with RATINGS_PATH.open("w") as f:
        for r in rating_rows:
            f.write(json.dumps(r) + "\n")
    print(f"[PhL-19] ratings saved: {RATINGS_PATH}")


def analyze() -> None:
    if not INTERP_PATH.exists():
        print("ERROR: run interp first.", file=sys.stderr)
        sys.exit(1)
    interps = [json.loads(l) for l in INTERP_PATH.read_text().splitlines() if l]
    struct_by_model: dict[str, list[dict]] = {m: [] for m in MODELS}
    # Also track raw-level format compliance
    format_compliance: dict[str, dict[str, int]] = {m: {"valid_json": 0, "truncated": 0, "empty": 0, "total": 0} for m in MODELS}
    for r in interps:
        fc = format_compliance[r["model"]]
        fc["total"] += 1
        raw_text = r.get("response_text", "")
        if not raw_text:
            fc["empty"] += 1
        elif isinstance(r.get("parsed"), dict) and "err" not in r["parsed"] and "mechanism_hypothesis" in r["parsed"]:
            fc["valid_json"] += 1
        else:
            # maybe truncated JSON — try recovery
            if raw_text.startswith("{") and not raw_text.rstrip().endswith("}"):
                fc["truncated"] += 1
        if isinstance(r.get("parsed"), dict) and "err" not in r.get("parsed", {"err": 1}):
            s = struct_check_interp(r["parsed"], raw_text)
        else:
            # Structural check on raw text for partial data
            s = struct_check_interp({}, raw_text)
        s["survivor_id"] = r["survivor_id"]
        struct_by_model[r["model"]].append(s)
    summary: dict[str, Any] = {"structural": {}, "rubric": {}, "format_compliance": format_compliance, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    for m, items in struct_by_model.items():
        if not items:
            continue
        summary["structural"][m] = {
            "n": len(items),
            "caveat_present_pct": round(100 * sum(1 for i in items if i["caveat_present"]) / len(items), 1),
            "prediction_present_pct": round(100 * sum(1 for i in items if i["prediction_present"]) / len(items), 1),
            "mean_citations": round(sum(i["citation_count"] for i in items) / len(items), 1),
            "mean_pathway_mentions": round(sum(i["pathway_mentions"] for i in items) / len(items), 1),
            "mean_mech_len": round(sum(i["mech_len_chars"] for i in items) / len(items), 0),
            "mean_prediction_len": round(sum(i["prediction_len_chars"] for i in items) / len(items), 0),
        }
    # Rubric
    if RATINGS_PATH.exists():
        ratings = [json.loads(l) for l in RATINGS_PATH.read_text().splitlines() if l]
        rubric_scores: dict[str, dict[str, list[int]]] = {m: {} for m in MODELS}
        for r in ratings:
            if "ratings" not in r or "mapping" not in r:
                continue
            for cand_label, model in r["mapping"].items():
                cand = r["ratings"].get(cand_label, {})
                for axis, val in cand.items():
                    if axis == "notes" or not isinstance(val, (int, float)):
                        continue
                    rubric_scores[model].setdefault(axis, []).append(val)
        for m, axes in rubric_scores.items():
            summary["rubric"][m] = {
                axis: round(sum(v)/len(v), 2) for axis, v in axes.items()
            }
    VERDICT_PATH.write_text(json.dumps(summary, indent=2))
    print(f"[PhL-19] verdict saved: {VERDICT_PATH}")
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
    rubric = summary.get("rubric", {})
    axes_names = ["biological_specificity", "caveat_depth", "testability",
                  "prior_art", "overall_trustworthiness"]
    if not rubric:
        return
    models = list(rubric.keys())
    short = [m.split("-")[1] for m in models]
    matrix = np.array([[rubric[m].get(a, 0) for a in axes_names] for m in models])
    fig, ax = plt.subplots(1, 1, figsize=(9, 4.5))
    im = ax.imshow(matrix, aspect="auto", cmap="YlGnBu", vmin=0, vmax=10)
    ax.set_xticks(range(len(axes_names)))
    ax.set_xticklabels([a.replace("_", "\n") for a in axes_names], fontsize=9)
    ax.set_yticks(range(len(short)))
    ax.set_yticklabels(short)
    for i in range(len(short)):
        for j in range(len(axes_names)):
            ax.text(j, i, f"{matrix[i,j]:.1f}", ha="center", va="center",
                    color="white" if matrix[i,j] > 5 else "black")
    plt.colorbar(im, ax=ax, label="Rubric score (0-10)")
    ax.set_title("PhL-19 · Interpreter mechanism depth (blind rubric)",
                 fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(PLOT_PATH, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[PhL-19] plot saved: {PLOT_PATH}")


def _write_summary(summary: dict) -> None:
    md = ["# PhL-19 — Interpreter mechanism hypothesis depth", "",
          "**Question:** for a gate-accepted survivor, how deep / disciplined",
          "is each model's biological interpretation?", "",
          "## Design", "",
          "- 3 survivors (TOP2A-EPAS1, MKI67-EPAS1, 5-gene compound).",
          "- 3 models × 3 survivors = 9 mechanism hypotheses.",
          "- Blind Opus rubric (model labels hidden) + programmatic checks.", "",
          "## Rubric (blind-rated)", ""]
    if summary["rubric"]:
        md.append("| Model | Specificity | Caveat | Testability | Prior art | Trust |")
        md.append("|---|---|---|---|---|---|")
        for m in MODELS:
            r = summary["rubric"].get(m, {})
            short = m.split("-")[1]
            md.append(f"| {short} | {r.get('biological_specificity', 0):.1f} | "
                      f"{r.get('caveat_depth', 0):.1f} | "
                      f"{r.get('testability', 0):.1f} | "
                      f"{r.get('prior_art', 0):.1f} | "
                      f"{r.get('overall_trustworthiness', 0):.1f} |")
    md.extend(["", "## Structural metrics (rater-independent)", "",
               "| Model | Caveat % | Prediction % | Mean citations | Mean pathway mentions |",
               "|---|---|---|---|---|"])
    for m in MODELS:
        s = summary["structural"].get(m, {})
        short = m.split("-")[1]
        md.append(f"| {short} | {s.get('caveat_present_pct', 0):.0f}% | "
                  f"{s.get('prediction_present_pct', 0):.0f}% | "
                  f"{s.get('mean_citations', 0):.1f} | "
                  f"{s.get('mean_pathway_mentions', 0):.1f} |")
    md.extend(["", "## Reproduce", "```bash",
               "source ~/.api_keys",
               "PYTHONPATH=src .venv/bin/python src/phl19_interpreter_depth.py interp",
               "PYTHONPATH=src .venv/bin/python src/phl19_interpreter_depth.py rate",
               "PYTHONPATH=src .venv/bin/python src/phl19_interpreter_depth.py analyze",
               "```"])
    SUMMARY_PATH.write_text("\n".join(md))


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("interp")
    sub.add_parser("rate")
    sub.add_parser("analyze")
    args = p.parse_args()
    if args.cmd == "interp":
        run_interp()
    elif args.cmd == "rate":
        run_rate()
    elif args.cmd == "analyze":
        analyze()


if __name__ == "__main__":
    main()
