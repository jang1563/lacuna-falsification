#!/usr/bin/env python3
"""H1 — Falsification-Guided SR Loop with LaSR-style concept library.

Lane H: Opus 4.7 capability overhang demonstration.

Design:
  - LaSR-style concept library: pathway groups (HIF, Warburg, Proliferation,
    Housekeeping, Renal_tubule, Metastasis_EMT) structure skeleton proposals.
  - Opus 4.7 receives explicit gate failure reasons per iteration, then proposes
    the next skeleton. Failure information is the primary steering signal.
  - 50-gene expanded panel handled via pathway group abstraction (not raw indices).
  - PySR regression + sigmoid wrapper for binary classification framing.
  - Doom Loop Detector: 3 consecutive iterations with ≥70% gene-token overlap
    → forced direction change to least-used pathway.
  - Max 10 iterations; records convergence trajectory.

Outputs: results/overhang/sr_loop_run.json
"""
from __future__ import annotations

import argparse
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

from theory_copilot.falsification import run_falsification_suite, passes_falsification
from theory_copilot.cost_ledger import log_usage

try:
    import anthropic
    _HAS_ANTHROPIC = True
except ImportError:
    _HAS_ANTHROPIC = False

try:
    import pysr
    _PYSR_AVAILABLE = hasattr(pysr, "PySRRegressor")
except (ImportError, Exception):
    pysr = None  # type: ignore[assignment]
    _PYSR_AVAILABLE = False


# ---------------------------------------------------------------------------
# Pathway concept library (LaSR-style structured skeleton space)
# ---------------------------------------------------------------------------

PATHWAY_GROUPS: dict[str, list[str]] = {
    "HIF": ["EPAS1", "CA9", "CA12", "VEGFA", "ANGPTL4", "BHLHE40", "DDIT4", "NDUFA4L2"],
    "Warburg": ["LDHA", "LDHB", "HK2", "ALDOA", "ENO1", "ENO2", "PKM", "SLC2A1", "PFKP", "PGK1", "PDK1"],
    "Proliferation": ["TOP2A", "MKI67", "PCNA", "CCNB1", "CDK1", "MCM2"],
    "Housekeeping": ["ACTB", "GAPDH", "RPL13A"],
    "Renal_tubule": ["AGXT", "ALB", "LRP2", "CUBN", "PTGER3", "SLC12A1", "SLC12A3", "SLC22A8", "PAX2", "PAX8", "CALB1", "KRT7"],
    "Metastasis_EMT": ["MMP9", "S100A4", "SPP1", "CXCR4", "COL4A2"],
}

# Pre-seeded skeletons representing biological hypotheses — one per pathway pair
SKELETON_LIBRARY: list[dict[str, Any]] = [
    {
        "pathway": "Proliferation_vs_HIF",
        "skeleton": "TOP2A - EPAS1",
        "rationale": "Proliferative-dedifferentiated ccRCC runs ahead of HIF-2α; ccA/ccB axis.",
    },
    {
        "pathway": "Proliferation_vs_HIF",
        "skeleton": "MKI67 - EPAS1",
        "rationale": "Ki-67 proliferation index minus HIF-2α captures the same dedifferentiation axis.",
    },
    {
        "pathway": "Warburg_vs_Tubule",
        "skeleton": "log1p(LDHA) - log1p(AGXT)",
        "rationale": "Warburg glycolysis upregulation vs loss of normal kidney oxidative marker.",
    },
    {
        "pathway": "HIF_axis",
        "skeleton": "log1p(CA9) + log1p(VEGFA) - log1p(AGXT)",
        "rationale": "Classic ccRCC HIF-target compound; expected to fail on delta_baseline (CA9 saturates).",
    },
    {
        "pathway": "Metastasis_EMT",
        "skeleton": "log1p(MMP9) + log1p(S100A4) - log1p(EPAS1)",
        "rationale": "EMT markers vs HIF-2α; aggressive-vs-differentiated hypothesis.",
    },
    {
        "pathway": "Housekeeping_null",
        "skeleton": "log1p(ACTB) - log1p(GAPDH)",
        "rationale": "Deliberate negative control: housekeeping contrast should fail all gates.",
    },
]


# ---------------------------------------------------------------------------
# Doom Loop Detector
# ---------------------------------------------------------------------------

class DoomLoopDetector:
    """Detects when Opus keeps proposing structurally similar skeletons.

    Similarity is measured as Jaccard overlap of the gene-token sets from
    the last `window` skeletons. If ≥ threshold, we've hit a doom loop.
    """

    _GENE_TOKEN_RE = re.compile(r"[A-Z][A-Z0-9]{1,9}")

    def __init__(self, window: int = 3, threshold: float = 0.7) -> None:
        self.window = window
        self.threshold = threshold
        self._history: list[frozenset[str]] = []

    def _tokens(self, skeleton: str) -> frozenset[str]:
        return frozenset(self._GENE_TOKEN_RE.findall(skeleton))

    def add(self, skeleton: str) -> None:
        self._history.append(self._tokens(skeleton))

    def is_doom_loop(self) -> bool:
        if len(self._history) < self.window:
            return False
        recent = self._history[-self.window:]
        union = frozenset().union(*recent)
        if not union:
            return False
        intersection = recent[0].intersection(*recent[1:])
        return len(intersection) / len(union) >= self.threshold

    def force_redirect(self, pathway_usage: Counter) -> str:
        """Return the pathway group least used so far."""
        least_used = min(PATHWAY_GROUPS, key=lambda p: pathway_usage.get(p, 0))
        genes = PATHWAY_GROUPS[least_used]
        # Pick the two least-correlated genes from the pathway as a contrast skeleton
        if len(genes) >= 2:
            return f"log1p({genes[0]}) - log1p({genes[-1]})"
        return f"log1p({genes[0]})"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

_DISEASE_TOKENS = {"disease", "tumor", "case", "cancer", "1", "true"}


def _parse_labels(series: pd.Series) -> np.ndarray:
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(int).values
    s = series.astype(str).str.strip().str.lower()
    return s.map(lambda v: 1 if v in _DISEASE_TOKENS else 0).values.astype(int)


def _zscore(X: np.ndarray) -> np.ndarray:
    mean = X.mean(axis=0, keepdims=True)
    std = np.where(X.std(axis=0, keepdims=True) < 1e-8, 1.0, X.std(axis=0, keepdims=True))
    return (X - mean) / std


def load_dataset(csv_path: str, standardize: bool = True) -> tuple[np.ndarray, np.ndarray, list[str]]:
    df = pd.read_csv(csv_path)
    y = _parse_labels(df["label"])
    non_feature = {"sample_id", "label", "m_stage", "age", "batch_index", "patient_id",
                   "grade", "tissue_type", "tumor_stage"}
    gene_cols = [c for c in df.columns if c not in non_feature]
    X = df[gene_cols].values.astype(float)
    if standardize:
        X = _zscore(X)
    return X, y, gene_cols


# ---------------------------------------------------------------------------
# Equation evaluator (gene-name → column-index binding)
# ---------------------------------------------------------------------------

_NUMPY_SAFE = {
    "log": np.log, "log1p": np.log1p, "exp": np.exp,
    "abs": np.abs, "sqrt": np.sqrt, "sin": np.sin, "cos": np.cos,
    "sigmoid": lambda x: 1.0 / (1.0 + np.exp(-np.clip(x, -50, 50))),
    "np": np,
}


def make_equation_fn(skeleton: str, gene_cols: list[str]):
    """Return a callable (X: ndarray) → scores for the given skeleton string."""
    name_to_idx = {g: i for i, g in enumerate(gene_cols)}

    def fn(X: np.ndarray) -> np.ndarray:
        X = np.asarray(X)
        local_ns = dict(_NUMPY_SAFE)
        for name, idx in name_to_idx.items():
            col = X[:, idx] if X.ndim == 2 else np.full(1, X[idx])
            local_ns[name] = col
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with np.errstate(all="ignore"):
                result = eval(skeleton, {"__builtins__": {}}, local_ns)  # noqa: S307
        arr = np.asarray(result, dtype=float)
        if arr.ndim == 0:
            arr = np.full(X.shape[0] if X.ndim == 2 else 1, float(arr))
        return arr

    return fn


# ---------------------------------------------------------------------------
# Skeleton → PySR search (gate-aware)
# ---------------------------------------------------------------------------

def run_pysr_on_skeleton(
    skeleton: str,
    X: np.ndarray,
    y: np.ndarray,
    gene_cols: list[str],
    n_iterations: int = 100,
    max_candidates: int = 8,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Run PySR with the skeleton as an initial_guess; return scored candidates."""
    if not _PYSR_AVAILABLE:
        return _mock_pysr_candidates(skeleton, X, y, gene_cols)

    # Filter skeleton genes to those actually present
    present_genes = set(gene_cols)
    skeleton_genes = re.findall(r"[A-Z][A-Z0-9]{1,9}", skeleton)
    missing = [g for g in skeleton_genes if g not in present_genes]
    effective_skeleton = skeleton if not missing else None

    model = pysr.PySRRegressor(
        niterations=n_iterations,
        populations=8,
        population_size=30,
        maxsize=12,
        binary_operators=["+", "-", "*", "/"],
        unary_operators=["log1p", "exp", "sqrt"],
        variable_names=gene_cols,
        verbosity=0,
        progress=False,
        random_state=seed,
    )

    fit_kwargs: dict[str, Any] = {}
    if effective_skeleton:
        try:
            model.fit(X, y.astype(float), guesses=[effective_skeleton],
                      fraction_replaced_guesses=0.3)
        except TypeError:
            model.fit(X, y.astype(float))
    else:
        model.fit(X, y.astype(float))

    try:
        eqs = model.get_hof()
    except Exception:
        eqs = model.equations_ if hasattr(model, "equations_") else pd.DataFrame()

    candidates = []
    for _, row in eqs.iterrows():
        eq = str(row.get("equation", ""))
        if not eq:
            continue
        try:
            fn = make_equation_fn(eq, gene_cols)
            from sklearn.metrics import roc_auc_score
            scores = fn(X)
            auc = float(roc_auc_score(y, scores))
        except Exception:
            auc = 0.5
        candidates.append({
            "equation": eq,
            "auroc": auc,
            "complexity": int(row.get("complexity", 0)),
            "origin_skeleton": skeleton,
        })
        if len(candidates) >= max_candidates:
            break
    return candidates


def _mock_pysr_candidates(
    skeleton: str,
    X: np.ndarray,
    y: np.ndarray,
    gene_cols: list[str],
    max_candidates: int = 4,
) -> list[dict[str, Any]]:
    """Fallback when PySR is unavailable: evaluate skeleton variants directly."""
    from sklearn.metrics import roc_auc_score

    candidates = []
    variants = [skeleton]
    # simple sign-flip variant
    variants.append(f"-1.0 * ({skeleton})")
    for v in variants[:max_candidates]:
        try:
            fn = make_equation_fn(v, gene_cols)
            scores = fn(X)
            auc = float(roc_auc_score(y, scores))
        except Exception:
            auc = 0.5
        candidates.append({
            "equation": v,
            "auroc": auc,
            "complexity": len(v.split()),
            "origin_skeleton": skeleton,
        })
    return candidates


# ---------------------------------------------------------------------------
# Falsification gate (wraps run_falsification_suite)
# ---------------------------------------------------------------------------

def gate_candidate(
    equation: str,
    X: np.ndarray,
    y: np.ndarray,
    gene_cols: list[str],
) -> dict[str, Any]:
    try:
        fn = make_equation_fn(equation, gene_cols)
        result = run_falsification_suite(fn, X, y, include_decoy=True)
    except Exception as exc:
        return {
            "equation": equation,
            "passes": False,
            "fail_reason": f"evaluation_error: {exc}",
            "law_auc": 0.5,
            "delta_baseline": 0.0,
            "perm_p": 1.0,
            "ci_lower": 0.0,
        }
    fail_parts = []
    if result.get("perm_p", 1.0) >= 0.05:
        fail_parts.append("perm_p")
    if result.get("ci_lower", 0.0) <= 0.6:
        fail_parts.append("ci_lower")
    if result.get("delta_baseline", 0.0) <= 0.05:
        fail_parts.append("delta_baseline")
    if result.get("delta_confound") is not None and result["delta_confound"] <= 0.03:
        fail_parts.append("delta_confound")
    if result.get("decoy_p") is not None and result["decoy_p"] >= 0.05:
        fail_parts.append("decoy_p")

    passes = len(fail_parts) == 0
    return {
        "equation": equation,
        "passes": passes,
        "fail_reason": ",".join(fail_parts) if fail_parts else "",
        "law_auc": result.get("law_auc", 0.5),
        "baseline_auc": result.get("baseline_auc", 0.5),
        "delta_baseline": result.get("delta_baseline", 0.0),
        "perm_p": result.get("perm_p", 1.0),
        "ci_lower": result.get("ci_lower", 0.0),
        "ci_width": result.get("ci_width", 1.0),
        "delta_confound": result.get("delta_confound"),
        "decoy_p": result.get("decoy_p"),
    }


# ---------------------------------------------------------------------------
# Opus 4.7 skeleton proposer (falsification-guided)
# ---------------------------------------------------------------------------

_SYSTEM_SKELETON_PROPOSER = """\
You are Opus 4.7 acting as the Proposer in a Falsification-Guided Symbolic Regression loop.

You receive:
1. A pathway concept library (grouped gene symbols with biological role labels).
2. The PREVIOUS iteration's skeleton and its gate failure reasons.
3. A Doom Loop flag indicating whether recent proposals are too similar.

Your task: propose 1-2 NEW symbolic equation skeletons for the next PySR search iteration.
Rules:
- Use only gene symbols from the concept library.
- Each skeleton must use 2-4 genes max.
- Skeletons must be in gene-name form suitable for PySR initial_guess (e.g. "TOP2A - EPAS1").
- Operators allowed: +, -, *, /, log1p(), exp(), sqrt(), sigmoid().
- Each skeleton must change the mathematical structure based on the failure reason:
  - If fail_reason contains "delta_baseline": the compound must beat a single gene — try a ratio or cross-pathway contrast.
  - If fail_reason contains "perm_p": try a fundamentally different gene pair.
  - If fail_reason contains "ci_lower": try a simpler 2-gene form for stability.
  - If fail_reason contains "decoy_p": avoid complex expressions that overfit.
- If doom_loop=true: you MUST use a completely different pathway group than recent iterations.
- Include one skeleton that crosses pathway boundaries (e.g., Proliferation × Warburg).

Output ONLY valid JSON:
{
  "skeletons": [
    {
      "skeleton": "symbolic expression",
      "pathway": "pathway group name",
      "rationale": "one-sentence biological justification targeting the specific gate failure"
    }
  ]
}
"""


def opus_propose_skeleton(
    client: Any,
    pathway_library: dict[str, list[str]],
    prev_skeleton: str,
    prev_fail_reason: str,
    prev_metrics: dict[str, Any],
    doom_loop: bool,
    iteration: int,
) -> list[dict[str, Any]]:
    """Call Opus 4.7 to propose next skeletons given failure context."""
    if not _HAS_ANTHROPIC:
        return _fallback_skeleton_proposal(prev_fail_reason, doom_loop, iteration)

    library_str = "\n".join(
        f"  {name}: {', '.join(genes)}"
        for name, genes in pathway_library.items()
    )
    metrics_str = json.dumps(
        {k: round(v, 4) if isinstance(v, float) else v
         for k, v in prev_metrics.items() if v is not None},
        indent=2,
    )
    user_msg = (
        f"Iteration: {iteration}\n\n"
        f"Pathway concept library:\n{library_str}\n\n"
        f"Previous skeleton: {prev_skeleton}\n"
        f"Gate failure reasons: {prev_fail_reason or 'PASSED'}\n"
        f"Metrics: {metrics_str}\n"
        f"Doom loop detected: {doom_loop}\n\n"
        "Propose the next 1-2 skeletons. Output only the JSON."
    )

    ac = anthropic.Anthropic()
    try:
        with ac.messages.stream(
            model="claude-opus-4-7",
            max_tokens=2000,
            thinking={"type": "adaptive", "display": "summarized"},
            system=_SYSTEM_SKELETON_PROPOSER,
            messages=[{"role": "user", "content": user_msg}],
        ) as stream:
            final = stream.get_final_message()

        log_usage("claude-opus-4-7", "proposer_h1", getattr(final, "usage", None))

        text = ""
        for block in final.content:
            if block.type == "text":
                text += block.text

        # Parse JSON
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            parsed = json.loads(text[start:end])
            return parsed.get("skeletons", [])
    except Exception as exc:
        print(f"  [opus_propose] error: {exc}", file=sys.stderr)

    return _fallback_skeleton_proposal(prev_fail_reason, doom_loop, iteration)


def _fallback_skeleton_proposal(
    prev_fail_reason: str,
    doom_loop: bool,
    iteration: int,
) -> list[dict[str, Any]]:
    """Rule-based fallback when Opus is unavailable."""
    idx = iteration % len(SKELETON_LIBRARY)
    entry = SKELETON_LIBRARY[idx]
    return [{"skeleton": entry["skeleton"], "pathway": entry["pathway"],
             "rationale": entry["rationale"]}]


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run_falsification_sr_loop(
    csv_path: str,
    max_iterations: int = 10,
    pysr_iterations: int = 100,
    standardize: bool = True,
    use_opus: bool = True,
    seed: int = 42,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Run the full falsification-guided SR loop.

    Returns a dict with the full iteration trace and any survivors found.
    """
    print(f"[H1] Loading dataset: {csv_path}")
    X, y, gene_cols = load_dataset(csv_path, standardize=standardize)
    print(f"[H1] Samples={len(y)}, Genes={len(gene_cols)}, Positives={y.sum()}")

    # Filter pathway library to genes present in dataset
    present = set(gene_cols)
    active_pathways: dict[str, list[str]] = {
        name: [g for g in genes if g in present]
        for name, genes in PATHWAY_GROUPS.items()
        if any(g in present for g in genes)
    }

    doom = DoomLoopDetector(window=3, threshold=0.7)
    pathway_usage: Counter = Counter()

    # Start from the seeded library
    current_skeleton = SKELETON_LIBRARY[0]["skeleton"]
    current_pathway = SKELETON_LIBRARY[0]["pathway"]
    prev_fail_reason = ""
    prev_metrics: dict[str, Any] = {}

    iterations = []
    all_survivors: list[dict[str, Any]] = []
    opus_client = None

    if use_opus and _HAS_ANTHROPIC:
        print("[H1] Opus 4.7 steering enabled")
    else:
        print("[H1] Rule-based fallback mode (no Opus)")

    for it in range(1, max_iterations + 1):
        print(f"\n[H1] Iteration {it}/{max_iterations} — skeleton: {current_skeleton}")
        start_t = time.time()

        doom.add(current_skeleton)
        is_doom = doom.is_doom_loop()
        if is_doom:
            print(f"  [doom] Loop detected! Redirecting...")
            current_skeleton = doom.force_redirect(pathway_usage)
            print(f"  [doom] Forced redirect → {current_skeleton}")

        pathway_usage[current_pathway] += 1

        # PySR search
        candidates = run_pysr_on_skeleton(
            current_skeleton, X, y, gene_cols,
            n_iterations=pysr_iterations, seed=seed + it,
        )

        # Gate all candidates
        gated: list[dict[str, Any]] = []
        for cand in candidates:
            result = gate_candidate(cand["equation"], X, y, gene_cols)
            result["origin_skeleton"] = cand.get("origin_skeleton", current_skeleton)
            result["iteration"] = it
            gated.append(result)

        survivors = [g for g in gated if g["passes"]]
        all_survivors.extend(survivors)

        # Best metrics for steering Opus
        best = max(gated, key=lambda g: g.get("law_auc", 0.5), default={})
        fail_reasons_this_iter = [g["fail_reason"] for g in gated if not g["passes"]]
        dominant_fail = Counter(",".join(fail_reasons_this_iter).split(",")).most_common(1)
        aggregated_fail = dominant_fail[0][0] if dominant_fail else ""

        elapsed = time.time() - start_t
        iter_record = {
            "iteration": it,
            "skeleton": current_skeleton,
            "pathway": current_pathway,
            "candidates": len(gated),
            "survivors": len(survivors),
            "best_law_auc": best.get("law_auc", 0.5),
            "best_delta_baseline": best.get("delta_baseline", 0.0),
            "dominant_fail_reason": aggregated_fail,
            "doom_loop_triggered": is_doom,
            "elapsed_sec": round(elapsed, 1),
            "gated_candidates": gated,
        }
        iterations.append(iter_record)

        print(f"  Candidates={len(gated)}, Survivors={len(survivors)}, "
              f"Best AUC={best.get('law_auc',0.5):.3f}, "
              f"ΔBase={best.get('delta_baseline',0):.3f}, "
              f"FailReason={aggregated_fail or 'none'}")

        if survivors:
            print(f"  *** SURVIVOR FOUND: {survivors[0]['equation']} ***")
            # Convergence: if we have survivors, continue but log
            if len(all_survivors) >= 3:
                print("[H1] Convergence: 3+ survivors found, stopping early.")
                break

        # Opus proposes next skeleton
        if it < max_iterations:
            if use_opus and _HAS_ANTHROPIC:
                proposals = opus_propose_skeleton(
                    client=None,
                    pathway_library=active_pathways,
                    prev_skeleton=current_skeleton,
                    prev_fail_reason=aggregated_fail,
                    prev_metrics=best,
                    doom_loop=is_doom,
                    iteration=it,
                )
            else:
                proposals = _fallback_skeleton_proposal(aggregated_fail, is_doom, it)

            if proposals:
                current_skeleton = proposals[0]["skeleton"]
                current_pathway = proposals[0].get("pathway", "unknown")
                print(f"  Next skeleton (from {'Opus' if use_opus else 'fallback'}): {current_skeleton}")
                print(f"  Rationale: {proposals[0].get('rationale','')}")
            else:
                # Advance in the library
                idx = it % len(SKELETON_LIBRARY)
                current_skeleton = SKELETON_LIBRARY[idx]["skeleton"]
                current_pathway = SKELETON_LIBRARY[idx]["pathway"]

        prev_fail_reason = aggregated_fail
        prev_metrics = best

    result = {
        "dataset": csv_path,
        "total_iterations": len(iterations),
        "total_candidates": sum(r["candidates"] for r in iterations),
        "total_survivors": len(all_survivors),
        "iterations": iterations,
        "survivors": all_survivors,
        "pathway_usage": dict(pathway_usage),
    }

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json.dumps(result, indent=2, default=str))
        print(f"\n[H1] Results written to {output_path}")

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="H1 — Falsification-Guided SR Loop (Lane H)",
    )
    parser.add_argument("--csv", default="data/kirc_metastasis_expanded.csv",
                        help="Input CSV with label + gene columns")
    parser.add_argument("--max-iterations", type=int, default=10)
    parser.add_argument("--pysr-iterations", type=int, default=100)
    parser.add_argument("--no-opus", action="store_true",
                        help="Disable Opus steering (rule-based fallback)")
    parser.add_argument("--no-standardize", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="results/overhang/sr_loop_run.json")
    args = parser.parse_args()

    csv_path = args.csv
    if not Path(csv_path).exists():
        csv_path = str(Path(__file__).parents[1] / args.csv)

    result = run_falsification_sr_loop(
        csv_path=csv_path,
        max_iterations=args.max_iterations,
        pysr_iterations=args.pysr_iterations,
        standardize=not args.no_standardize,
        use_opus=not args.no_opus,
        seed=args.seed,
        output_path=args.output,
    )

    print(f"\n[H1] Summary: {result['total_iterations']} iterations, "
          f"{result['total_candidates']} candidates, "
          f"{result['total_survivors']} survivors")
    if result["survivors"]:
        print("Survivors:")
        for s in result["survivors"][:5]:
            print(f"  {s['equation']} | AUC={s['law_auc']:.3f} | iter={s['iteration']}")


if __name__ == "__main__":
    main()
