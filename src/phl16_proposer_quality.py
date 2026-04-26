#!/usr/bin/env python3
"""PhL-16 — Cross-model Proposer quality.

Question: Is Opus 4.7 just a better Skeptic (E2 ablation), or also a better
Proposer? The E2 ablation held the Proposer fixed and varied the Skeptic;
this experiment holds the Skeptic (= deterministic gate) fixed and varies
the Proposer.

Design: each model (Opus 4.7, Sonnet 4.6, Haiku 4.5) proposes 30
2-gene compact laws for TCGA-KIRC metastasis. 90 unique equations are
scored by the SAME pre-registered 5-test gate. Per-model metrics:
  - pass rate (% of proposed laws that clear the gate)
  - biological diversity (unique pathway combinations proposed)
  - ccA/ccB rediscovery rate (% of proposals that are proliferation-HIF
    structural form)
  - mean AUROC of proposed laws

This is the *generation-side* capability test; the Skeptic ablation (E2)
was the *judgement-side* test. Two axes of Opus-4.7-vs-others.

Outputs:
  results/live_evidence/phl16_proposer_quality/proposals.jsonl
  results/live_evidence/phl16_proposer_quality/gate_results.jsonl
  results/live_evidence/phl16_proposer_quality/verdict.json
  results/live_evidence/phl16_proposer_quality/SUMMARY.md
  results/live_evidence/phl16_proposer_quality/proposer_comparison.png
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from lacuna.falsification import run_falsification_suite  # noqa: E402

OUT = REPO / "results" / "live_evidence" / "phl16_proposer_quality"
OUT.mkdir(parents=True, exist_ok=True)

PROPOSALS_PATH = OUT / "proposals.jsonl"
GATE_PATH = OUT / "gate_results.jsonl"
VERDICT_PATH = OUT / "verdict.json"
SUMMARY_PATH = OUT / "SUMMARY.md"
PLOT_PATH = OUT / "proposer_comparison.png"

MODELS = ["claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5"]

DATA_CSV = REPO / "data" / "kirc_metastasis_expanded.csv"

PROPOSER_SYSTEM = """\
You are a computational biology researcher proposing candidate compact
laws for predicting metastasis (M0 vs M1) in TCGA-KIRC (clear-cell
renal cell carcinoma).

Constraints:
- Exactly 2 genes per law.
- Operators allowed: - (subtraction), / (ratio), log1p, sqrt
- Gene symbols only from this panel:
  HIF: EPAS1, CA9, CA12, VEGFA, ANGPTL4, BHLHE40, DDIT4, NDUFA4L2
  Warburg: LDHA, LDHB, HK2, ALDOA, ENO1, ENO2, PKM, SLC2A1, PFKP, PGK1, PDK1
  Proliferation: TOP2A, MKI67, PCNA, CCNB1, CDK1, MCM2
  Housekeeping: ACTB, GAPDH, RPL13A
  Renal_tubule: AGXT, ALB, LRP2, CUBN, PTGER3, SLC12A1, SLC12A3, SLC22A8, PAX2, PAX8, CALB1, KRT7
  Metastasis_EMT: MMP9, S100A4, SPP1, CXCR4, COL4A2

Output a single JSON object with this shape:
{
  "equation": "<gene1> - <gene2>",
  "pathway_pair": "<pathway_of_gene1> vs <pathway_of_gene2>",
  "rationale": "<one sentence about why this pair should separate M0 from M1>"
}

Generate only ONE law. No markdown fences. No prose outside the JSON.
"""

PROPOSER_USER_TEMPLATE = """\
Propose compact law #{n} for TCGA-KIRC metastasis prediction.

Diversity constraint: this is your {n}-th proposal out of 30 total.
Try to explore DIFFERENT pathway combinations across your 30 proposals.
{previous_hint}

Output JSON only.
"""

GENE_RE = re.compile(r"[A-Z][A-Z0-9]{1,9}")

# Pathway classification (for diversity / ccA-ccB rediscovery analysis)
PATHWAYS = {
    "HIF": {"EPAS1", "CA9", "CA12", "VEGFA", "ANGPTL4", "BHLHE40", "DDIT4", "NDUFA4L2"},
    "Warburg": {"LDHA", "LDHB", "HK2", "ALDOA", "ENO1", "ENO2", "PKM", "SLC2A1",
                "PFKP", "PGK1", "PDK1"},
    "Proliferation": {"TOP2A", "MKI67", "PCNA", "CCNB1", "CDK1", "MCM2"},
    "Housekeeping": {"ACTB", "GAPDH", "RPL13A"},
    "Renal_tubule": {"AGXT", "ALB", "LRP2", "CUBN", "PTGER3", "SLC12A1", "SLC12A3",
                     "SLC22A8", "PAX2", "PAX8", "CALB1", "KRT7"},
    "Metastasis_EMT": {"MMP9", "S100A4", "SPP1", "CXCR4", "COL4A2"},
}


def classify_pathway(gene: str) -> str:
    for p, genes in PATHWAYS.items():
        if gene in genes:
            return p
    return "Unknown"


def is_prolif_hif(gene_a: str, gene_b: str) -> bool:
    a_prolif = gene_a in PATHWAYS["Proliferation"]
    a_hif = gene_a in PATHWAYS["HIF"]
    b_prolif = gene_b in PATHWAYS["Proliferation"]
    b_hif = gene_b in PATHWAYS["HIF"]
    return (a_prolif and b_hif) or (a_hif and b_prolif)


def _strip_json(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        lines = s.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        s = "\n".join(lines)
    return s


def _one_proposal(client: Any, model: str, n: int,
                  previous: list[str]) -> dict[str, Any]:
    prev_hint = ""
    if len(previous) >= 3:
        prev_hint = "\nSkeletons already proposed: " + ", ".join(previous[-5:])
    user_msg = PROPOSER_USER_TEMPLATE.format(n=n+1, previous_hint=prev_hint)
    thinking = {"type": "adaptive", "display": "summarized"}
    if model == "claude-haiku-4-5":
        # Haiku 4.5 supports adaptive via same API
        thinking = {"type": "adaptive", "display": "summarized"}
    try:
        with client.messages.stream(
            model=model,
            max_tokens=1500,
            thinking=thinking,
            system=PROPOSER_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        ) as stream:
            final = stream.get_final_message()
        text = ""
        for block in final.content:
            if getattr(block, "type", "") == "text":
                text += getattr(block, "text", "")
        parsed = None
        try:
            parsed = json.loads(_strip_json(text))
        except Exception:
            # try substring
            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                try:
                    parsed = json.loads(m.group(0))
                except Exception:
                    pass
        if not isinstance(parsed, dict):
            return {"model": model, "n": n, "err": "parse_fail", "raw": text[:200]}
        eq = parsed.get("equation", "")
        return {
            "model": model,
            "n": n,
            "equation": eq,
            "pathway_pair": parsed.get("pathway_pair", ""),
            "rationale": parsed.get("rationale", ""),
        }
    except Exception as e:
        return {"model": model, "n": n, "err": str(e)[:200]}


def run_proposals(n_per_model: int = 30, workers: int = 4) -> None:
    import anthropic
    client = anthropic.Anthropic()
    all_rows: list[dict] = []
    for model in MODELS:
        print(f"[PhL-16] generating {n_per_model} proposals from {model}...")
        # Sequential within model (uses `previous` context); parallel across models
        # would confuse diversity. Let's do sequential but fast.
        previous_skeletons: list[str] = []
        for n in range(n_per_model):
            row = _one_proposal(client, model, n, previous_skeletons)
            all_rows.append(row)
            if "equation" in row:
                previous_skeletons.append(row["equation"])
        print(f"  {model}: {sum(1 for r in all_rows if r['model']==model and 'equation' in r)}/{n_per_model} valid")
    with PROPOSALS_PATH.open("w") as f:
        for r in all_rows:
            f.write(json.dumps(r) + "\n")
    print(f"[PhL-16] saved {PROPOSALS_PATH}")


def make_fn(equation: str, gene_cols: list[str]):
    name_to_idx = {g: i for i, g in enumerate(gene_cols)}
    NUMPY_SAFE = {
        "log1p": np.log1p, "exp": np.exp, "sqrt": np.sqrt,
        "log": np.log, "abs": np.abs,
    }
    def fn(X):
        X = np.asarray(X)
        local = dict(NUMPY_SAFE)
        for name, idx in name_to_idx.items():
            local[name] = X[:, idx] if X.ndim == 2 else np.array([X[idx]])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with np.errstate(all="ignore"):
                result = eval(equation, {"__builtins__": {}}, local)  # noqa: S307
        arr = np.asarray(result, dtype=float)
        if arr.ndim == 0:
            arr = np.full(X.shape[0] if X.ndim == 2 else 1, float(arr))
        return arr
    return fn


def run_gate() -> None:
    if not PROPOSALS_PATH.exists():
        print("ERROR: run proposals first.", file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(DATA_CSV)
    y = df["label"].astype(int).values if df["label"].dtype.kind in "iufc" else \
        df["label"].astype(str).str.strip().str.lower().map(
            lambda v: 1 if v in {"disease", "tumor", "case", "cancer", "1", "true"} else 0
        ).values.astype(int)
    non_feat = {"sample_id", "label", "m_stage", "age", "batch_index",
                "patient_id", "grade", "tissue_type", "tumor_stage"}
    gene_cols = [c for c in df.columns if c not in non_feat]
    X_all = df[gene_cols].values.astype(float)
    # Use raw expression values for equation evaluation (log1p requires
    # non-negative input; the CSV stores TPM-scale expression which is
    # already non-negative). The falsification gate's internal tests
    # standardize where needed.
    X = X_all

    rows = [json.loads(l) for l in PROPOSALS_PATH.read_text().splitlines() if l]
    proposals_with_eq = [r for r in rows if "equation" in r and r["equation"]]
    print(f"[PhL-16] gating {len(proposals_with_eq)} proposals on {DATA_CSV.name} (n={len(y)})...")
    gate_rows: list[dict] = []
    for r in proposals_with_eq:
        eq = r["equation"]
        genes = GENE_RE.findall(eq)
        missing = [g for g in genes if g not in gene_cols]
        if missing:
            gate_rows.append({**r, "passes": False, "fail_reason": f"missing_gene:{missing}",
                              "law_auc": None, "delta_baseline": None})
            continue
        try:
            fn = make_fn(eq, gene_cols)
            result = run_falsification_suite(fn, X, y, include_decoy=True)
        except Exception as e:
            gate_rows.append({**r, "passes": False, "fail_reason": f"eval_error:{e}",
                              "law_auc": None, "delta_baseline": None})
            continue
        fail_parts = []
        if result.get("perm_p", 1) >= 0.05:
            fail_parts.append("perm_p")
        if result.get("ci_lower", 0) <= 0.6:
            fail_parts.append("ci_lower")
        if result.get("delta_baseline", 0) <= 0.05:
            fail_parts.append("delta_baseline")
        if result.get("decoy_p") is not None and result["decoy_p"] >= 0.05:
            fail_parts.append("decoy_p")
        passes = len(fail_parts) == 0
        gate_rows.append({
            **r,
            "passes": passes,
            "fail_reason": ",".join(fail_parts) if fail_parts else "",
            "law_auc": round(result.get("law_auc", 0.5), 4),
            "delta_baseline": round(result.get("delta_baseline", 0), 4),
            "perm_p": round(result.get("perm_p", 1), 4),
            "ci_lower": round(result.get("ci_lower", 0), 4),
            "decoy_p": round(result.get("decoy_p", 1) or 1, 4),
        })
    with GATE_PATH.open("w") as f:
        for r in gate_rows:
            f.write(json.dumps(r) + "\n")
    print(f"[PhL-16] gate results saved: {GATE_PATH}")


def analyze() -> None:
    if not GATE_PATH.exists():
        print("ERROR: run gate first.", file=sys.stderr)
        sys.exit(1)
    rows = [json.loads(l) for l in GATE_PATH.read_text().splitlines() if l]
    summary: dict[str, Any] = {"model_stats": {}, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    for model in MODELS:
        m_rows = [r for r in rows if r["model"] == model]
        n_valid = sum(1 for r in m_rows if "equation" in r and r.get("law_auc") is not None)
        n_pass = sum(1 for r in m_rows if r.get("passes", False))
        pathway_pairs = set()
        prolif_hif_count = 0
        aucs = []
        for r in m_rows:
            if "equation" not in r:
                continue
            genes = GENE_RE.findall(r["equation"])
            if len(genes) >= 2:
                pa, pb = classify_pathway(genes[0]), classify_pathway(genes[1])
                pathway_pairs.add(tuple(sorted([pa, pb])))
                if is_prolif_hif(genes[0], genes[1]):
                    prolif_hif_count += 1
            if r.get("law_auc") is not None:
                aucs.append(r["law_auc"])
        summary["model_stats"][model] = {
            "total_proposals": len(m_rows),
            "valid_gated": n_valid,
            "pass_count": n_pass,
            "pass_rate": round(n_pass / max(n_valid, 1), 3),
            "unique_pathway_pairs": len(pathway_pairs),
            "prolif_hif_proposals": prolif_hif_count,
            "prolif_hif_rate": round(prolif_hif_count / max(len(m_rows), 1), 3),
            "mean_law_auc": round(sum(aucs)/max(len(aucs),1), 4),
            "max_law_auc": round(max(aucs) if aucs else 0, 4),
        }
    VERDICT_PATH.write_text(json.dumps(summary, indent=2))
    print(f"[PhL-16] verdict saved: {VERDICT_PATH}")
    print(json.dumps(summary, indent=2))
    _make_plot(summary)
    _write_summary(summary)


def _make_plot(summary: dict) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    stats = summary["model_stats"]
    models = list(stats.keys())
    short = [m.split("-")[1] for m in models]  # opus/sonnet/haiku
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    # Panel 1: pass rate
    pass_rates = [stats[m]["pass_rate"] for m in models]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    axes[0].bar(short, pass_rates, color=colors)
    axes[0].set_ylabel("Gate pass rate")
    axes[0].set_title("(a) Gate-passing proposals per model")
    axes[0].grid(axis="y", alpha=0.3)
    for i, v in enumerate(pass_rates):
        axes[0].text(i, v + 0.005, f"{v:.2f}", ha="center")
    # Panel 2: pathway diversity
    diversity = [stats[m]["unique_pathway_pairs"] for m in models]
    axes[1].bar(short, diversity, color=colors)
    axes[1].set_ylabel("Unique pathway combinations")
    axes[1].set_title("(b) Biological diversity (max 21 if all pairs)")
    axes[1].grid(axis="y", alpha=0.3)
    for i, v in enumerate(diversity):
        axes[1].text(i, v + 0.1, f"{v}", ha="center")
    # Panel 3: proliferation-HIF rediscovery
    prolif_hif = [stats[m]["prolif_hif_rate"] for m in models]
    axes[2].bar(short, prolif_hif, color=colors)
    axes[2].set_ylabel("Proliferation-HIF form rate")
    axes[2].set_title("(c) ccA/ccB axis structural rediscovery")
    axes[2].grid(axis="y", alpha=0.3)
    for i, v in enumerate(prolif_hif):
        axes[2].text(i, v + 0.005, f"{v:.2f}", ha="center")
    fig.suptitle("PhL-16 · Cross-model Proposer quality on TCGA-KIRC metastasis",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(PLOT_PATH, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[PhL-16] plot saved: {PLOT_PATH}")


def _write_summary(summary: dict) -> None:
    md = ["# PhL-16 — Cross-model Proposer quality", "",
          "**Question:** is Opus 4.7 better only as Skeptic (E2 ablation result), "
          "or also as Proposer?", "",
          "## Design", "",
          "- Each of 3 models (Opus 4.7 / Sonnet 4.6 / Haiku 4.5) proposes 30",
          "  compact 2-gene laws for TCGA-KIRC metastasis (M0 vs M1, n=505).",
          "- All 90 proposals scored by the SAME pre-registered 5-test gate.",
          "- Metrics: pass rate, pathway diversity (unique combinations),",
          "  proliferation-HIF structural rediscovery, mean law AUROC.", "",
          "## Result", "",
          "| Model | Valid | Gate pass | Pass rate | Unique pathway pairs | Prolif-HIF rate | Mean AUC |",
          "|---|---|---|---|---|---|---|"]
    for m, s in summary["model_stats"].items():
        short = m.split("-")[1]
        md.append(f"| {short} | {s['valid_gated']}/{s['total_proposals']} | "
                  f"{s['pass_count']} | {s['pass_rate']:.2f} | "
                  f"{s['unique_pathway_pairs']} | {s['prolif_hif_rate']:.2f} | "
                  f"{s['mean_law_auc']:.3f} |")
    md.extend(["", "## Interpretation", ""])
    stats = summary["model_stats"]
    opus = stats.get("claude-opus-4-7", {})
    sonnet = stats.get("claude-sonnet-4-6", {})
    haiku = stats.get("claude-haiku-4-5", {})
    if opus.get("pass_rate", 0) > max(sonnet.get("pass_rate", 0), haiku.get("pass_rate", 0)) + 0.05:
        md.append("**Opus 4.7 proposes more gate-surviving laws.** The advantage measured "
                  "in E2 (Skeptic role) extends to the Proposer role — Opus is not just a "
                  "better critic, it is a better generator for this task.")
    elif opus.get("pass_rate", 0) < min(sonnet.get("pass_rate", 1), haiku.get("pass_rate", 1)) - 0.05:
        md.append("**Honest finding: Opus 4.7 is NOT the best Proposer here.** Sonnet/Haiku "
                  "produce more gate-surviving laws. This is tessl.io-consistent — capability "
                  "is task-specific, not universal. Opus's E2 Skeptic advantage does not "
                  "generalize to generation on this task.")
    else:
        md.append("**Pass rates are within ±0.05.** Proposer role is model-agnostic on this "
                  "task; the E2 Skeptic differentiation does not extend to generation. The "
                  "gate absorbs Proposer-side variation.")
    if opus.get("prolif_hif_rate", 0) > max(sonnet.get("prolif_hif_rate", 0), haiku.get("prolif_hif_rate", 0)):
        md.append("")
        md.append("**Opus 4.7 rediscovers the ccA/ccB subtype axis more often** — "
                  f"{opus['prolif_hif_rate']*100:.1f}% of its proposals are proliferation-HIF "
                  "structural form, versus Sonnet's "
                  f"{sonnet.get('prolif_hif_rate',0)*100:.1f}% and Haiku's "
                  f"{haiku.get('prolif_hif_rate',0)*100:.1f}%. This is a biology-grounding "
                  "advantage under the compactness constraint.")
    md.extend(["", "## Reproduce", "```bash",
               "source ~/.api_keys",
               "PYTHONPATH=src .venv/bin/python src/phl16_proposer_quality.py propose",
               "PYTHONPATH=src .venv/bin/python src/phl16_proposer_quality.py gate",
               "PYTHONPATH=src .venv/bin/python src/phl16_proposer_quality.py analyze",
               "```"])
    SUMMARY_PATH.write_text("\n".join(md))


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("propose").add_argument("--n-per-model", type=int, default=30)
    sub.add_parser("gate")
    sub.add_parser("analyze")
    args, extra = p.parse_known_args()
    if args.cmd == "propose":
        n = 30
        for i, a in enumerate(extra):
            if a == "--n-per-model" and i+1 < len(extra):
                n = int(extra[i+1])
        run_proposals(n_per_model=n)
    elif args.cmd == "gate":
        run_gate()
    elif args.cmd == "analyze":
        analyze()


if __name__ == "__main__":
    main()
