#!/usr/bin/env python3
"""P2a / PhL-14 — LLM-SR 10-iteration convergence analysis.

Runs the falsification-guided SR loop for 10 full iterations (no early stop)
on both Opus 4.7 and Sonnet 4.6. Uses DrSR-style outcome categorization:
last-50%-of-history context + positive/marginal/negative categorization to
prevent mode collapse.

Outputs:
  results/overhang/llm_sr_10iter/opus_iterations.json
  results/overhang/llm_sr_10iter/sonnet_iterations.json
  results/overhang/llm_sr_10iter/convergence_summary.json
  results/overhang/llm_sr_10iter/convergence_plot.png

Usage:
  PYTHONPATH=src .venv/bin/python src/phl14_llm_sr_10iter.py
"""
from __future__ import annotations

import json
import re
import sys
import time
import warnings
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from falsification_sr_loop import (
    PATHWAY_GROUPS,
    SKELETON_LIBRARY,
    DoomLoopDetector,
    _parse_labels,
    _zscore,
    make_equation_fn,
    gate_candidate,
    _fallback_skeleton_proposal,
    run_pysr_on_skeleton,
)
from lacuna.cost_ledger import log_usage


# ---------------------------------------------------------------------------
# Fast mock PySR: produce PySR-like variants without Julia
# ---------------------------------------------------------------------------

def fast_mock_candidates(
    skeleton: str,
    X: np.ndarray,
    y: np.ndarray,
    gene_cols: list[str],
    max_candidates: int = 6,
) -> list[dict[str, Any]]:
    """Produce ~6 PySR-style variants of a skeleton without running Julia.

    Variants:
      1. Raw skeleton
      2. Sign-flipped skeleton
      3. Scaled with small constant (PySR-style: c0 + c1*expr)
      4. log1p-wrapped version
      5. Single-gene drop (if multi-gene)
      6. Sigmoid-wrapped
    """
    from sklearn.metrics import roc_auc_score

    variants: list[str] = [skeleton]

    # Sign flip
    variants.append(f"-1.0 * ({skeleton})")

    # Scaled PySR-style constant form
    variants.append(f"0.15 + 0.08 * ({skeleton})")

    # log1p wrap (simulates PySR's log1p unary)
    variants.append(f"log1p(exp(0.1 * ({skeleton})))")

    # Gene-dropout: replace first gene with 0.0 if multi-gene
    tokens = re.findall(r"[A-Z][A-Z0-9]{1,9}", skeleton)
    if len(tokens) >= 2:
        # drop the first gene by zeroing it
        variants.append(skeleton.replace(tokens[0], "0.0", 1))

    # Sigmoid wrap
    variants.append(f"sigmoid({skeleton})")

    candidates = []
    for v in variants[:max_candidates]:
        try:
            fn = make_equation_fn(v, gene_cols)
            scores = fn(X)
            auc = float(roc_auc_score(y, scores))
            auc = max(auc, 1 - auc)  # sign-invariant
        except Exception:
            auc = 0.5
        candidates.append({
            "equation": v,
            "auroc": auc,
            "complexity": len(v.split()),
            "origin_skeleton": skeleton,
        })
    return candidates

try:
    import anthropic
    _HAS_ANTHROPIC = True
except ImportError:
    _HAS_ANTHROPIC = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    _HAS_MPL = True
except ImportError:
    _HAS_MPL = False


# ---------------------------------------------------------------------------
# DrSR-style outcome categorisation
# ---------------------------------------------------------------------------

def _classify_outcome(iter_record: dict[str, Any]) -> str:
    """Categorise an iteration outcome for DrSR-style history context."""
    if iter_record["survivors"] > 0:
        return "positive"
    best_auc = iter_record.get("best_law_auc", 0.5)
    best_delta = iter_record.get("best_delta_baseline", 0.0)
    best_ci = max(
        (g.get("ci_lower", 0.0) for g in iter_record.get("gated_candidates", [])),
        default=0.0,
    )
    if best_auc >= 0.68 or best_delta >= 0.03 or best_ci >= 0.58:
        return "marginal"
    return "negative"


def _build_drsr_context(
    history: list[dict[str, Any]],
    window_frac: float = 0.5,
) -> str:
    """Build DrSR history context from the LAST window_frac of iterations."""
    if not history:
        return "No prior iterations."
    n_window = max(1, int(len(history) * window_frac))
    recent = history[-n_window:]

    lines = []
    for rec in recent:
        cat = _classify_outcome(rec)
        fail = rec.get("dominant_fail_reason", "none") or "none"
        best_auc = rec.get("best_law_auc", 0.5)
        best_delta = rec.get("best_delta_baseline", 0.0)
        survivors = rec.get("survivors", 0)
        lines.append(
            f"  iter {rec['iteration']} [{cat.upper()}] skeleton={rec['skeleton']} "
            f"survivors={survivors} best_auc={best_auc:.3f} Δbase={best_delta:.3f} "
            f"fail={fail}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Opus/Sonnet skeleton proposer (DrSR-enhanced)
# ---------------------------------------------------------------------------

_SYSTEM_DRSR_PROPOSER = """\
You are the Proposer in a Falsification-Guided Symbolic Regression loop.
You propose symbolic equation skeletons for PySR to search.

You receive:
1. A pathway concept library (biological gene groups).
2. A DrSR-style outcome history: the MOST RECENT iterations only
   (positive = survivors found, marginal = near-miss, negative = failed).
3. A doom-loop flag (recent proposals too similar).

Your task: propose exactly 2 NEW symbolic equation skeletons.

Rules:
- Use only gene symbols from the concept library.
- 2-4 genes per skeleton maximum.
- Equation form suitable for PySR initial_guess (e.g. "TOP2A - EPAS1").
- Operators: +, -, *, /, log1p(), exp(), sqrt().
- Learn from outcome history:
  * POSITIVE outcomes: note which structural type succeeded; consider extensions.
  * MARGINAL outcomes: the skeleton was biologically right but needed different
    form — try ratio instead of difference, or log transform.
  * NEGATIVE outcomes: avoid the same pathway pair — switch to a different axis.
- If doom_loop=true: MUST switch to a completely different pathway group.
- At least one skeleton should cross pathway boundaries
  (e.g., Proliferation gene − HIF gene, Warburg gene / Renal-tubule gene).

Gate failure guidance:
  - "delta_baseline": compound must beat a single gene — try cross-pathway ratio
  - "perm_p": try a fundamentally different gene pair
  - "ci_lower": simpler 2-gene form for stability
  - "decoy_p": avoid complex expressions that overfit

Output ONLY valid JSON:
{
  "skeletons": [
    {
      "skeleton": "symbolic expression",
      "pathway": "pathway group name",
      "rationale": "one-sentence targeting the specific outcome history pattern"
    }
  ]
}
"""


def propose_skeleton_drsr(
    model: str,
    pathway_library: dict[str, list[str]],
    history: list[dict[str, Any]],
    doom_loop: bool,
    iteration: int,
) -> list[dict[str, Any]]:
    """Propose next skeletons using DrSR-style context."""
    if not _HAS_ANTHROPIC:
        dominant_fail = history[-1].get("dominant_fail_reason", "") if history else ""
        return _fallback_skeleton_proposal(dominant_fail, doom_loop, iteration)

    library_str = "\n".join(
        f"  {name}: {', '.join(genes)}"
        for name, genes in pathway_library.items()
    )
    drsr_context = _build_drsr_context(history)

    user_msg = (
        f"Iteration: {iteration}\n\n"
        f"Pathway concept library:\n{library_str}\n\n"
        f"DrSR outcome history (last 50% of iterations):\n{drsr_context}\n\n"
        f"Doom loop detected: {doom_loop}\n\n"
        "Propose the next 2 skeletons. Output only the JSON."
    )

    ac = anthropic.Anthropic()
    try:
        with ac.messages.stream(
            model=model,
            max_tokens=1500,
            thinking={"type": "adaptive", "display": "summarized"},
            system=_SYSTEM_DRSR_PROPOSER,
            messages=[{"role": "user", "content": user_msg}],
        ) as stream:
            final = stream.get_final_message()

        log_usage(model, "phl14_proposer", getattr(final, "usage", None))

        text = "".join(
            block.text for block in final.content if block.type == "text"
        )
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            parsed = json.loads(text[start:end])
            skeletons = parsed.get("skeletons", [])
            if skeletons:
                print(f"    [{model.split('-')[1]}] proposed: "
                      + "; ".join(s["skeleton"] for s in skeletons[:2]))
                return skeletons[:2]
    except Exception as exc:
        print(f"  [propose_drsr] error: {exc}", file=sys.stderr)

    dominant_fail = history[-1].get("dominant_fail_reason", "") if history else ""
    return _fallback_skeleton_proposal(dominant_fail, doom_loop, iteration)


# ---------------------------------------------------------------------------
# Held-out evaluation
# ---------------------------------------------------------------------------

def held_out_auc(
    equation: str,
    X_test: np.ndarray,
    y_test: np.ndarray,
    gene_cols: list[str],
) -> float:
    from sklearn.metrics import roc_auc_score
    try:
        fn = make_equation_fn(equation, gene_cols)
        scores = fn(X_test)
        auc = float(roc_auc_score(y_test, scores))
        return max(auc, 1 - auc)
    except Exception:
        return 0.5


# ---------------------------------------------------------------------------
# 10-iteration loop (no early stop)
# ---------------------------------------------------------------------------

def run_10iter_loop(
    csv_path: str,
    model: str,
    max_iterations: int = 10,
    pysr_iterations: int = 100,
    seed: int = 42,
    use_fast_mock: bool = True,
) -> dict[str, Any]:
    """Run the full 10-iteration LLM-SR convergence loop."""
    from sklearn.model_selection import train_test_split

    print(f"\n{'='*60}")
    print(f"[PhL-14] Model: {model}")
    print(f"[PhL-14] Loading: {csv_path}")

    df = pd.read_csv(csv_path)
    y_all = _parse_labels(df["label"])
    non_feat = {"sample_id", "label", "m_stage", "age", "batch_index",
                "patient_id", "grade", "tissue_type", "tumor_stage"}
    gene_cols = [c for c in df.columns if c not in non_feat]
    X_all = df[gene_cols].values.astype(float)

    # Train/test split — gate runs on train; held-out AUROC on test
    X_train, X_test, y_train, y_test = train_test_split(
        X_all, y_all, test_size=0.30, random_state=seed, stratify=y_all,
    )
    X_train = _zscore(X_train)
    X_test = _zscore(X_test)

    print(f"[PhL-14] Train={len(y_train)} ({y_train.sum()} M1), "
          f"Test={len(y_test)} ({y_test.sum()} M1)")

    # Filter pathway library to present genes
    present = set(gene_cols)
    active_pathways: dict[str, list[str]] = {
        name: [g for g in genes if g in present]
        for name, genes in PATHWAY_GROUPS.items()
        if any(g in present for g in genes)
    }

    doom = DoomLoopDetector(window=3, threshold=0.7)
    pathway_usage: Counter = Counter()

    current_skeleton = SKELETON_LIBRARY[0]["skeleton"]
    current_pathway = SKELETON_LIBRARY[0]["pathway"]

    iterations: list[dict[str, Any]] = []
    all_survivors: list[dict[str, Any]] = []
    # Track unique equations to avoid counting duplicates
    seen_equations: set[str] = set()
    unique_survivors_per_iter: list[int] = []
    best_held_out_per_iter: list[float] = []
    cumulative_best_held_out: float = 0.5

    for it in range(1, max_iterations + 1):
        print(f"\n[PhL-14] Iteration {it}/{max_iterations} — {current_skeleton}")
        t0 = time.time()

        doom.add(current_skeleton)
        is_doom = doom.is_doom_loop()
        if is_doom:
            new_sk = doom.force_redirect(pathway_usage)
            print(f"  [doom] Redirect → {new_sk}")
            current_skeleton = new_sk

        pathway_usage[current_pathway] += 1

        # Candidate generation on TRAIN split.
        # fast_mock=True: synthetic PySR-style variants (~0.5s/iter)
        # fast_mock=False: real PySR search (~60s/iter after Julia JIT)
        if use_fast_mock:
            candidates = fast_mock_candidates(
                current_skeleton, X_train, y_train, gene_cols,
            )
        else:
            candidates = run_pysr_on_skeleton(
                current_skeleton, X_train, y_train, gene_cols,
                n_iterations=pysr_iterations, seed=seed + it,
            )

        # Gate on TRAIN, evaluate held-out AUROC on TEST
        gated: list[dict[str, Any]] = []
        new_this_iter = 0
        iter_best_held_out = 0.5
        for cand in candidates:
            result = gate_candidate(cand["equation"], X_train, y_train, gene_cols)
            result["origin_skeleton"] = cand.get("origin_skeleton", current_skeleton)
            result["iteration"] = it
            # Held-out AUROC (regardless of gate verdict)
            ho_auc = held_out_auc(cand["equation"], X_test, y_test, gene_cols)
            result["held_out_auroc"] = ho_auc
            gated.append(result)

            if result["passes"] and cand["equation"] not in seen_equations:
                seen_equations.add(cand["equation"])
                new_this_iter += 1
                all_survivors.append(result)
            if result["passes"]:
                iter_best_held_out = max(iter_best_held_out, ho_auc)

        cumulative_best_held_out = max(cumulative_best_held_out, iter_best_held_out)
        unique_survivors_per_iter.append(new_this_iter)
        best_held_out_per_iter.append(cumulative_best_held_out)

        # Per-iter stats
        best = max(gated, key=lambda g: g.get("law_auc", 0.5), default={})
        fail_ctr = Counter(",".join(
            g["fail_reason"] for g in gated if not g["passes"]
        ).split(","))
        dom_fail = fail_ctr.most_common(1)[0][0] if fail_ctr else ""

        elapsed = time.time() - t0
        outcome_cat = _classify_outcome({
            "survivors": new_this_iter,
            "best_law_auc": best.get("law_auc", 0.5),
            "best_delta_baseline": best.get("delta_baseline", 0.0),
            "gated_candidates": gated,
        })
        iter_record = {
            "iteration": it,
            "skeleton": current_skeleton,
            "pathway": current_pathway,
            "candidates": len(gated),
            "survivors": new_this_iter,
            "cumulative_survivors": len(all_survivors),
            "best_law_auc": best.get("law_auc", 0.5),
            "best_held_out_auroc": iter_best_held_out,
            "cumulative_best_held_out": cumulative_best_held_out,
            "best_delta_baseline": best.get("delta_baseline", 0.0),
            "dominant_fail_reason": dom_fail,
            "doom_loop_triggered": is_doom,
            "outcome_category": outcome_cat,
            "elapsed_sec": round(elapsed, 1),
            "gated_candidates": gated,
        }
        iterations.append(iter_record)

        print(f"  Cands={len(gated)} NewSurvivors={new_this_iter} "
              f"CumulSurv={len(all_survivors)} "
              f"BestTrainAUC={best.get('law_auc',0.5):.3f} "
              f"BestHeldOutAUC={iter_best_held_out:.3f} "
              f"[{outcome_cat.upper()}]")

        # Propose next skeleton (iterations 2..N)
        if it < max_iterations:
            proposals = propose_skeleton_drsr(
                model=model,
                pathway_library=active_pathways,
                history=iterations,
                doom_loop=is_doom,
                iteration=it,
            )
            if proposals:
                # Pick the one with a different skeleton from current
                for prop in proposals:
                    if prop["skeleton"] != current_skeleton:
                        current_skeleton = prop["skeleton"]
                        current_pathway = prop.get("pathway", "unknown")
                        print(f"  Next skeleton: {current_skeleton}")
                        print(f"  Rationale: {prop.get('rationale','')[:80]}")
                        break
                else:
                    current_skeleton = proposals[0]["skeleton"]
                    current_pathway = proposals[0].get("pathway", "unknown")
            else:
                idx = it % len(SKELETON_LIBRARY)
                current_skeleton = SKELETON_LIBRARY[idx]["skeleton"]
                current_pathway = SKELETON_LIBRARY[idx]["pathway"]

    return {
        "model": model,
        "dataset": csv_path,
        "max_iterations": max_iterations,
        "total_candidates": sum(r["candidates"] for r in iterations),
        "total_unique_survivors": len(all_survivors),
        "unique_survivors_per_iter": unique_survivors_per_iter,
        "cumulative_survivors_per_iter": [
            sum(unique_survivors_per_iter[:i+1]) for i in range(len(unique_survivors_per_iter))
        ],
        "best_held_out_per_iter": best_held_out_per_iter,
        "pathway_usage": dict(pathway_usage),
        "iterations": iterations,
        "survivors": all_survivors,
    }


# ---------------------------------------------------------------------------
# Convergence plot
# ---------------------------------------------------------------------------

def make_convergence_plot(
    opus_result: dict[str, Any],
    sonnet_result: dict[str, Any],
    out_path: str,
) -> None:
    if not _HAS_MPL:
        print("[plot] matplotlib not available — skipping plot")
        return

    n_iters = max(len(opus_result["iterations"]), len(sonnet_result["iterations"]))
    x = list(range(1, n_iters + 1))

    def _pad(lst: list, target: int, val: Any = None) -> list:
        if val is None and lst:
            val = lst[-1]
        return lst + [val] * (target - len(lst))

    # Per-iteration best train AUC (NOT cumulative) — shows exploration quality
    opus_per_iter_auc = [it["best_law_auc"] for it in opus_result["iterations"]]
    sonnet_per_iter_auc = [it["best_law_auc"] for it in sonnet_result["iterations"]]
    opus_per_iter_auc = _pad(opus_per_iter_auc, n_iters)
    sonnet_per_iter_auc = _pad(sonnet_per_iter_auc, n_iters)

    # Cumulative survivors (unchanged)
    opus_surv = _pad(opus_result["cumulative_survivors_per_iter"], n_iters)
    sonnet_surv = _pad(sonnet_result["cumulative_survivors_per_iter"], n_iters)

    # Skeleton diversity — unique pathways up to iter i
    def _cumul_pathway_diversity(it_list: list) -> list[int]:
        seen = set()
        out = []
        for it in it_list:
            seen.add(it["pathway"])
            out.append(len(seen))
        return out
    opus_div = _pad(_cumul_pathway_diversity(opus_result["iterations"]), n_iters)
    sonnet_div = _pad(_cumul_pathway_diversity(sonnet_result["iterations"]), n_iters)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle(
        "PhL-14 · LLM-SR 10-Iteration Convergence · Opus 4.7 vs Sonnet 4.6",
        fontsize=13, fontweight="bold",
    )
    ax1, ax2, ax3 = axes

    # Panel 1: cumulative unique survivors
    ax1.step(x, opus_surv, where="post", color="#1f77b4", linewidth=2.5,
             label="Opus 4.7", marker="o", markersize=7)
    ax1.step(x, sonnet_surv, where="post", color="#ff7f0e", linewidth=2.5,
             label="Sonnet 4.6", linestyle="--", marker="s", markersize=7)
    ax1.set_xlabel("Iteration", fontsize=11)
    ax1.set_ylabel("Cumulative Unique Survivors", fontsize=11)
    ax1.set_title("(a) Gate-Passing Laws", fontsize=11)
    ax1.set_xticks(x)
    ax1.legend(fontsize=10)
    ax1.grid(axis="y", alpha=0.3)
    ax1.set_ylim(0, max(max(opus_surv or [0]), max(sonnet_surv or [0])) + 2)
    if opus_surv and opus_surv[0] > 0:
        ax1.annotate(
            f"iter-1 seed:\nTOP2A − EPAS1\n→ {opus_surv[0]} survivors",
            xy=(1, opus_surv[0]),
            xytext=(2.5, opus_surv[0] - 2.0),
            fontsize=8, color="black",
            arrowprops=dict(arrowstyle="->", color="black", lw=1),
        )

    # Panel 2: per-iter best TRAIN AUROC (exploration quality)
    ax2.plot(x, opus_per_iter_auc, color="#1f77b4", linewidth=2.0,
             label="Opus 4.7", marker="o", markersize=7)
    ax2.plot(x, sonnet_per_iter_auc, color="#ff7f0e", linewidth=2.0,
             label="Sonnet 4.6", linestyle="--", marker="s", markersize=7)
    ax2.axhline(y=0.726, color="green", linestyle="-", linewidth=1.2,
                alpha=0.5, label="TOP2A − EPAS1 full-train AUC 0.726")
    ax2.axhline(y=0.657, color="gray", linestyle=":", linewidth=1.2,
                label="Best single gene AUC 0.657")
    ax2.fill_between(x, 0.5, 0.657, alpha=0.08, color="red")
    ax2.set_xlabel("Iteration", fontsize=11)
    ax2.set_ylabel("Best Train AUROC on that iteration", fontsize=11)
    ax2.set_title("(b) Per-Iteration Exploration Quality", fontsize=11)
    ax2.set_xticks(x)
    ax2.legend(fontsize=8, loc="upper right")
    ax2.grid(axis="y", alpha=0.3)
    ax2.set_ylim(0.48, 0.80)

    # Annotate peak non-seed AUROCs for each model
    opus_nonseed = [(i+1, a) for i, a in enumerate(opus_per_iter_auc) if i > 0]
    if opus_nonseed:
        peak_i, peak_a = max(opus_nonseed, key=lambda t: t[1])
        peak_skel = opus_result["iterations"][peak_i - 1]["skeleton"]
        ax2.annotate(
            f"Opus peak non-seed:\n{peak_skel}\nAUC={peak_a:.3f}",
            xy=(peak_i, peak_a),
            xytext=(peak_i - 3, peak_a + 0.05),
            fontsize=7, color="#1f77b4",
            arrowprops=dict(arrowstyle="->", color="#1f77b4", lw=0.8),
        )
    sonnet_nonseed = [(i+1, a) for i, a in enumerate(sonnet_per_iter_auc) if i > 0]
    if sonnet_nonseed:
        peak_i, peak_a = max(sonnet_nonseed, key=lambda t: t[1])
        peak_skel = sonnet_result["iterations"][peak_i - 1]["skeleton"]
        ax2.annotate(
            f"Sonnet peak non-seed:\n{peak_skel}\nAUC={peak_a:.3f}",
            xy=(peak_i, peak_a),
            xytext=(peak_i + 0.5, peak_a - 0.08),
            fontsize=7, color="#ff7f0e",
            arrowprops=dict(arrowstyle="->", color="#ff7f0e", lw=0.8),
        )

    # Panel 3: pathway diversity (staircase)
    ax3.step(x, opus_div, where="post", color="#1f77b4", linewidth=2.5,
             label="Opus 4.7", marker="o", markersize=7)
    ax3.step(x, sonnet_div, where="post", color="#ff7f0e", linewidth=2.5,
             label="Sonnet 4.6", linestyle="--", marker="s", markersize=7)
    ax3.set_xlabel("Iteration", fontsize=11)
    ax3.set_ylabel("Unique Pathway Groups Explored", fontsize=11)
    ax3.set_title("(c) Skeleton-Space Exploration", fontsize=11)
    ax3.set_xticks(x)
    ax3.legend(fontsize=10, loc="lower right")
    ax3.grid(axis="y", alpha=0.3)
    ax3.set_ylim(0, max(max(opus_div or [0]), max(sonnet_div or [0])) + 2)

    plt.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[plot] Saved to {out_path}")


# ---------------------------------------------------------------------------
# Skeleton evolution summary
# ---------------------------------------------------------------------------

def summarise_skeleton_evolution(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "iteration": it["iteration"],
            "skeleton": it["skeleton"],
            "pathway": it["pathway"],
            "outcome": it["outcome_category"],
            "survivors": it["survivors"],
            "best_train_auc": round(it["best_law_auc"], 3),
            "best_held_out_auc": round(it["best_held_out_auroc"], 3),
            "doom_loop": it["doom_loop_triggered"],
        }
        for it in result["iterations"]
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="PhL-14 LLM-SR 10-iter convergence")
    parser.add_argument("--csv", default="data/kirc_metastasis_expanded.csv")
    parser.add_argument("--max-iterations", type=int, default=10)
    parser.add_argument("--pysr-iterations", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--real-pysr",
        action="store_true",
        help="Use real PySR (slow, requires Julia warmup). Default: fast-mock variants.",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=["claude-opus-4-7", "claude-sonnet-4-6"],
        help="Models to run (default: opus and sonnet)",
    )
    parser.add_argument(
        "--out-dir",
        default="results/overhang/llm_sr_10iter",
    )
    args = parser.parse_args()

    csv_path = args.csv
    if not Path(csv_path).exists():
        csv_path = str(Path(__file__).parents[1] / args.csv)
    if not Path(csv_path).exists():
        print(f"[ERROR] CSV not found: {args.csv}", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(__file__).parents[1] / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, dict[str, Any]] = {}

    for model in args.models:
        # "claude-opus-4-7" → "opus"; "claude-sonnet-4-6" → "sonnet"
        short = model.split("-")[1]
        out_json = out_dir / f"{short}_iterations.json"

        # Resume if already done
        if out_json.exists():
            print(f"[PhL-14] Loading cached result: {out_json}")
            results[model] = json.loads(out_json.read_text())
            continue

        result = run_10iter_loop(
            csv_path=csv_path,
            model=model,
            max_iterations=args.max_iterations,
            pysr_iterations=args.pysr_iterations,
            seed=args.seed,
            use_fast_mock=not args.real_pysr,
        )
        out_json.write_text(json.dumps(result, indent=2, default=str))
        print(f"[PhL-14] Saved: {out_json}")
        results[model] = result

    # Convergence summary
    opus_key = next((m for m in results if "opus" in m), None)
    sonnet_key = next((m for m in results if "sonnet" in m), None)

    if opus_key and sonnet_key:
        opus_r = results[opus_key]
        sonnet_r = results[sonnet_key]

        summary = {
            "opus_4_7": {
                "total_unique_survivors": opus_r["total_unique_survivors"],
                "first_survivor_iter": next(
                    (i+1 for i, n in enumerate(opus_r["unique_survivors_per_iter"]) if n > 0),
                    None,
                ),
                "final_held_out_auroc": opus_r["best_held_out_per_iter"][-1] if opus_r["best_held_out_per_iter"] else None,
                "pathway_diversity": len(opus_r["pathway_usage"]),
                "skeleton_evolution": summarise_skeleton_evolution(opus_r),
            },
            "sonnet_4_6": {
                "total_unique_survivors": sonnet_r["total_unique_survivors"],
                "first_survivor_iter": next(
                    (i+1 for i, n in enumerate(sonnet_r["unique_survivors_per_iter"]) if n > 0),
                    None,
                ),
                "final_held_out_auroc": sonnet_r["best_held_out_per_iter"][-1] if sonnet_r["best_held_out_per_iter"] else None,
                "pathway_diversity": len(sonnet_r["pathway_usage"]),
                "skeleton_evolution": summarise_skeleton_evolution(sonnet_r),
            },
        }
        (out_dir / "convergence_summary.json").write_text(json.dumps(summary, indent=2))
        print(f"[PhL-14] Summary saved: {out_dir}/convergence_summary.json")

        # Convergence plot
        make_convergence_plot(
            opus_r, sonnet_r,
            str(out_dir / "convergence_plot.png"),
        )

        # Print digest
        print("\n" + "="*60)
        print("CONVERGENCE DIGEST")
        print("="*60)
        for model_label, r in [("Opus 4.7", opus_r), ("Sonnet 4.6", sonnet_r)]:
            print(f"\n{model_label}:")
            print(f"  Total unique survivors:  {r['total_unique_survivors']}")
            print(f"  Final held-out AUROC:    {r['best_held_out_per_iter'][-1]:.3f}")
            print(f"  Pathway diversity:       {len(r['pathway_usage'])} groups")
            print(f"  Per-iter survivors:      {r['unique_survivors_per_iter']}")
            print(f"  Cumulative:              {r['cumulative_survivors_per_iter']}")

    elif len(results) == 1:
        model_key = list(results.keys())[0]
        r = results[model_key]
        print(f"\n[PhL-14] Single model run: {model_key}")
        print(f"  Unique survivors: {r['total_unique_survivors']}")
        print(f"  Per-iter:         {r['unique_survivors_per_iter']}")

    print(f"\n[PhL-14] Done. Outputs in: {out_dir}")


if __name__ == "__main__":
    main()
