"""E2 cross-model ablation on the Skeptic turn.

Compares Opus 4.7 / Sonnet 4.6 / Haiku 4.5 on judging the same 6 candidates
against the 5-test falsification gate's real metric bundle. Pre-registered
predictions live in results/ablation/SUMMARY.md (committed before this
runs); this script fills in the observed numbers after the sweep.

Design: 3 models * 6 candidates * 10 repeats = 180 API calls.
Candidates span the pass/borderline/fail spectrum:
  1. TOP2A - EPAS1            (strong survivor, metastasis_expanded)
  2. MKI67 - EPAS1            (strong survivor, metastasis_expanded)
  3. log1p(CA9)+log1p(VEGFA)-log1p(AGXT)  (borderline reject, tumor_normal)
  4. 5-gene compound (MKI67 vs EPAS1/LRP2/PTGER3/RPL13A)  (stress test)
  5. log1p(ACTB)-log1p(GAPDH)  (housekeeping null reject)
  6. log1p(MKI67)-log1p(RPL13A)  (proliferation/housekeeping null reject)

Outputs:
  results/ablation/candidate_metrics.json   (precompute phase)
  results/ablation/skeptic_model_sweep.jsonl  (sweep phase, one row per call)
  results/ablation/SUMMARY.md               (analyze phase; headline table)
  results/ablation/plots/model_specificity_histogram.png

Usage:
  python src/track_a_model_ablation.py precompute
  python src/track_a_model_ablation.py sweep --workers 6 --repeats 10
  python src/track_a_model_ablation.py analyze
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lacuna.falsification import run_falsification_suite  # noqa: E402
from lacuna.cost_ledger import estimate_cost, log_usage  # noqa: E402

OUT = REPO / "results" / "ablation"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "plots").mkdir(exist_ok=True)

METRICS_PATH = OUT / "candidate_metrics.json"
JSONL_PATH = OUT / "skeptic_model_sweep.jsonl"
SUMMARY_PATH = OUT / "SUMMARY.md"
HIST_PATH = OUT / "plots" / "model_specificity_histogram.png"

MODELS = ["claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5"]

# Thinking configs: Opus 4.7 uses adaptive/summarized; Sonnet/Haiku use
# fixed-budget thinking to keep the comparison interpretable (same task,
# different model) rather than comparing against no-thinking baselines.
THINKING_CONFIG = {
    "claude-opus-4-7": {"type": "enabled", "budget_tokens": 8000},
    "claude-sonnet-4-6": {"type": "enabled", "budget_tokens": 8000},
    "claude-haiku-4-5": {"type": "enabled", "budget_tokens": 8000},
}

# -----------------------------------------------------------------------
# Candidate equations
# -----------------------------------------------------------------------
# Each candidate is (name, equation_string, gene_list, fn, csv, label_col,
# disease_tokens, expected_verdict). fn receives X (n, len(gene_list))
# already sliced to the requested genes in that order.


def _fn_top2a_minus_epas1(X):  # TOP2A, EPAS1
    return X[:, 0] - X[:, 1]


def _fn_mki67_minus_epas1(X):  # MKI67, EPAS1
    return X[:, 0] - X[:, 1]


def _fn_hif_textbook(X):  # CA9, VEGFA, AGXT
    return np.log1p(X[:, 0]) + np.log1p(X[:, 1]) - np.log1p(X[:, 2])


def _fn_five_gene_compound(X):  # MKI67, EPAS1, PTGER3, LRP2, RPL13A
    inner = np.exp(((X[:, 1] - X[:, 2]) + X[:, 3]) - X[:, 4])
    return np.log1p(np.log1p(np.exp(X[:, 0] - inner))) * 0.6274355


def _fn_housekeeping_null(X):  # ACTB, GAPDH
    return np.log1p(X[:, 0]) - np.log1p(X[:, 1])


def _fn_proliferation_null(X):  # MKI67, RPL13A
    return np.log1p(X[:, 0]) - np.log1p(X[:, 1])


CANDIDATES: list[dict] = [
    dict(
        name="top2a_minus_epas1",
        equation="0.0986*(TOP2A - EPAS1) + 0.1606",
        genes=["TOP2A", "EPAS1"],
        fn=_fn_top2a_minus_epas1,
        csv="data/kirc_metastasis_expanded.csv",
        label_col="label",
        disease_tokens=["disease", "m1", "1"],
        dataset="TCGA-KIRC metastasis M1 vs M0 (n=505, 45 genes)",
        expected_gate="pass",
        category="strong_survivor",
    ),
    dict(
        name="mki67_minus_epas1",
        equation="0.1686 * log1p(exp(MKI67 - EPAS1))",
        genes=["MKI67", "EPAS1"],
        fn=_fn_mki67_minus_epas1,
        csv="data/kirc_metastasis_expanded.csv",
        label_col="label",
        disease_tokens=["disease", "m1", "1"],
        dataset="TCGA-KIRC metastasis M1 vs M0 (n=505, 45 genes)",
        expected_gate="pass",
        category="strong_survivor",
    ),
    dict(
        name="hif_textbook_tn",
        equation="log1p(CA9) + log1p(VEGFA) - log1p(AGXT)",
        genes=["CA9", "VEGFA", "AGXT"],
        fn=_fn_hif_textbook,
        csv="data/kirc_tumor_normal.csv",
        label_col="label",
        disease_tokens=["disease", "tumor"],
        dataset="TCGA-KIRC tumor vs normal (n=609, 11 genes)",
        expected_gate="fail",
        category="borderline_reject",
    ),
    dict(
        name="five_gene_compound",
        equation="log1p(log1p(exp(MKI67 - exp(((EPAS1 - PTGER3) + LRP2) - RPL13A)))) * 0.627",
        genes=["MKI67", "EPAS1", "PTGER3", "LRP2", "RPL13A"],
        fn=_fn_five_gene_compound,
        csv="data/kirc_metastasis_expanded.csv",
        label_col="label",
        disease_tokens=["disease", "m1", "1"],
        dataset="TCGA-KIRC metastasis M1 vs M0 (n=505, 45 genes)",
        expected_gate="pass",
        category="stress_test",
    ),
    dict(
        name="actb_minus_gapdh",
        equation="log1p(ACTB) - log1p(GAPDH)",
        genes=["ACTB", "GAPDH"],
        fn=_fn_housekeeping_null,
        csv="data/kirc_metastasis_expanded.csv",
        label_col="label",
        disease_tokens=["disease", "m1", "1"],
        dataset="TCGA-KIRC metastasis M1 vs M0 (n=505, 45 genes)",
        expected_gate="fail",
        category="clean_reject",
    ),
    dict(
        name="mki67_minus_rpl13a",
        equation="log1p(MKI67) - log1p(RPL13A)",
        genes=["MKI67", "RPL13A"],
        fn=_fn_proliferation_null,
        csv="data/kirc_metastasis_expanded.csv",
        label_col="label",
        disease_tokens=["disease", "m1", "1"],
        dataset="TCGA-KIRC metastasis M1 vs M0 (n=505, 45 genes)",
        expected_gate="fail",
        category="clean_reject",
    ),
]


def _parse_labels(series: pd.Series, disease_tokens: list[str]) -> np.ndarray:
    toks = {t.strip().lower() for t in disease_tokens}
    return series.astype(str).str.strip().str.lower().isin(toks).astype(int).values


# -----------------------------------------------------------------------
# Precompute: real metric bundles
# -----------------------------------------------------------------------


def precompute_metrics() -> dict:
    bundles: dict[str, dict] = {}
    for cand in CANDIDATES:
        csv_path = REPO / cand["csv"]
        df = pd.read_csv(csv_path)
        missing = [g for g in cand["genes"] if g not in df.columns]
        if missing:
            raise RuntimeError(f"{cand['name']}: missing genes {missing}")
        X = df[cand["genes"]].fillna(0).values.astype(float)
        y = _parse_labels(df[cand["label_col"]], cand["disease_tokens"])
        cov_cols = [c for c in ("age", "batch_index") if c in df.columns]
        X_cov = df[cov_cols].fillna(0).values.astype(float) if cov_cols else None
        np.random.seed(7)
        metrics = run_falsification_suite(
            cand["fn"], X, y, X_covariates=X_cov, include_decoy=True
        )
        bundles[cand["name"]] = {
            "candidate_name": cand["name"],
            "equation": cand["equation"],
            "genes_used": cand["genes"],
            "dataset": cand["dataset"],
            "expected_gate": cand["expected_gate"],
            "category": cand["category"],
            "n_samples": int(len(y)),
            "n_disease": int(y.sum()),
            "passes": bool(metrics["passes"]),
            "perm_p": float(metrics["perm_p"]),
            "original_auc": float(metrics["original_auc"]),
            "law_auc": float(metrics["law_auc"]),
            "baseline_auc": float(metrics["baseline_auc"]),
            "delta_baseline": float(metrics["delta_baseline"]),
            "ci_width": float(metrics["ci_width"]),
            "ci_lower": float(metrics["ci_lower"]),
            "delta_confound": (
                float(metrics["delta_confound"])
                if metrics["delta_confound"] is not None
                else None
            ),
            "confound_auc": (
                float(metrics["confound_auc"])
                if metrics["confound_auc"] is not None
                else None
            ),
            "decoy_p": float(metrics["decoy_p"]),
            "decoy_q95": float(metrics["decoy_q95"]),
        }
        print(
            f"[precompute] {cand['name']}: law_auc={metrics['law_auc']:.3f} "
            f"delta_base={metrics['delta_baseline']:+.3f} passes={metrics['passes']}",
            flush=True,
        )
    METRICS_PATH.write_text(json.dumps(bundles, indent=2))
    print(f"\nWrote {METRICS_PATH}")
    return bundles


# -----------------------------------------------------------------------
# Specificity regex: does the reason text cite >=2 distinct metric values?
# -----------------------------------------------------------------------

_METRIC_NAMES = [
    r"perm_p(?:_fdr)?",
    r"ci_lower",
    r"ci_width",
    r"delta_baseline",
    r"delta_confound",
    r"decoy_p",
    r"decoy_q95",
    r"law_auc",
    r"baseline_auc",
    r"confound_auc",
    r"original_auc",
]
_VALUE_RE = r"[-+]?\d*\.?\d+"
_METRIC_RE = re.compile(
    r"(?P<name>%s)\s*(?:[=≈:]|is|of|was|reached|reaches|hits?|at|=|around)\s*"
    r"(?P<val>%s)" % ("|".join(_METRIC_NAMES), _VALUE_RE),
    re.IGNORECASE,
)


def count_metric_citations(reason: str) -> tuple[int, list[str]]:
    """Return (n_distinct_metric_names_cited, list_of_names)."""
    if not reason:
        return 0, []
    hits = {m.group("name").lower() for m in _METRIC_RE.finditer(reason)}
    normalized = {name.replace("perm_p_fdr", "perm_p") for name in hits}
    return len(normalized), sorted(normalized)


# -----------------------------------------------------------------------
# Sweep
# -----------------------------------------------------------------------

_SKEPTIC_PROMPT_PATH = REPO / "prompts" / "skeptic_review.md"
_ANTHROPIC_CLIENT = None
_CLIENT_LOCK = threading.Lock()
_WRITE_LOCK = threading.Lock()
_LEDGER_LOCK = threading.Lock()

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```\s*$", re.MULTILINE)


def _strip_json_fences(text: str) -> str:
    cleaned = _FENCE_RE.sub("", text).strip()
    if not cleaned.startswith(("{", "[")):
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]
    return cleaned


def _get_anthropic_client():
    global _ANTHROPIC_CLIENT
    with _CLIENT_LOCK:
        if _ANTHROPIC_CLIENT is None:
            import anthropic

            _ANTHROPIC_CLIENT = anthropic.Anthropic()
    return _ANTHROPIC_CLIENT


def _one_call(model: str, candidate_bundle: dict, repeat: int) -> dict:
    import anthropic

    client = _get_anthropic_client()
    system = _SKEPTIC_PROMPT_PATH.read_text()
    metrics_for_prompt = {
        k: v
        for k, v in candidate_bundle.items()
        if k
        in (
            "perm_p",
            "ci_width",
            "ci_lower",
            "law_auc",
            "baseline_auc",
            "delta_baseline",
            "delta_confound",
            "confound_auc",
            "decoy_p",
            "decoy_q95",
            "original_auc",
            "n_samples",
            "n_disease",
            "passes",
        )
    }
    equation = candidate_bundle["equation"]
    user_msg = (
        f"Candidate equation: {equation}\n"
        f"Dataset: {candidate_bundle['dataset']}\n"
        f"Falsification metrics: {json.dumps(metrics_for_prompt, default=str)}\n\n"
        "Output only the JSON described in the system prompt."
    )

    t0 = time.time()
    thinking_text = ""
    response_text = ""
    err_msg = None
    usage = None
    try:
        with client.messages.stream(
            model=model,
            max_tokens=16000,
            thinking=THINKING_CONFIG[model],
            system=system,
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
    except anthropic.BadRequestError as e:
        # Retry without thinking (older model configurations may not support it)
        err_msg = f"bad_request_with_thinking: {e}"
        try:
            with client.messages.stream(
                model=model,
                max_tokens=8000,
                system=system,
                messages=[{"role": "user", "content": user_msg}],
            ) as stream:
                final = stream.get_final_message()
            usage = getattr(final, "usage", None)
            for block in final.content:
                if getattr(block, "type", "") == "text":
                    response_text += getattr(block, "text", "")
        except Exception as e2:
            err_msg = f"{err_msg}; retry_failed: {e2}"

    latency = time.time() - t0

    # Parse JSON response
    parsed = None
    try:
        parsed = json.loads(_strip_json_fences(response_text))
    except Exception:
        parsed = None

    if isinstance(parsed, dict):
        verdict = parsed.get("verdict", "UNPARSED")
        reason = parsed.get("reason", "")
        additional_test = parsed.get("additional_test", "")
    else:
        verdict = "UNPARSED"
        reason = response_text
        additional_test = ""

    # Specificity regex
    spec_count, spec_names = count_metric_citations(reason)

    # Token + cost accounting
    input_tokens = int(getattr(usage, "input_tokens", 0) or 0) if usage else 0
    output_tokens = int(getattr(usage, "output_tokens", 0) or 0) if usage else 0
    thinking_tokens = int(
        (getattr(usage, "thinking_tokens", None) or 0)
        if usage
        else 0
    )
    cost_usd = estimate_cost(model, input_tokens, output_tokens, thinking_tokens)

    # Record usage via existing ledger (thread-safe append)
    with _LEDGER_LOCK:
        log_usage(model, "skeptic_ablation", usage)

    row = {
        "model": model,
        "candidate_name": candidate_bundle["candidate_name"],
        "candidate_category": candidate_bundle["category"],
        "gate_verdict": "PASS" if candidate_bundle["passes"] else "FAIL",
        "repeat": repeat,
        "verdict": verdict,
        "reason": reason,
        "additional_test": additional_test,
        "reason_length_chars": len(reason),
        "metric_citation_count": spec_count,
        "metric_citations": spec_names,
        "cites_two_or_more_metrics": spec_count >= 2,
        "latency_sec": round(latency, 2),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "thinking_tokens": thinking_tokens,
        "cost_usd": round(cost_usd, 5),
        "error": err_msg,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    with _WRITE_LOCK:
        with JSONL_PATH.open("a") as f:
            f.write(json.dumps(row) + "\n")
    return row


def run_sweep(workers: int = 6, repeats: int = 10, only_model: str | None = None) -> None:
    if not METRICS_PATH.exists():
        raise SystemExit("candidate_metrics.json missing — run `precompute` first.")
    bundles = json.loads(METRICS_PATH.read_text())
    models = [only_model] if only_model else MODELS

    # Build work list
    work = []
    for m in models:
        for cand in CANDIDATES:
            bundle = bundles[cand["name"]]
            for r in range(repeats):
                work.append((m, bundle, r))

    total = len(work)
    print(f"[sweep] dispatching {total} calls across {len(models)} models "
          f"with {workers} workers...", flush=True)

    # Truncate JSONL if starting a fresh sweep (single-model fills append).
    if only_model is None and JSONL_PATH.exists():
        backup = JSONL_PATH.with_suffix(".jsonl.bak")
        JSONL_PATH.replace(backup)
        print(f"[sweep] moved prior {JSONL_PATH.name} -> {backup.name}", flush=True)

    done = 0
    t_start = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(_one_call, m, b, r) for (m, b, r) in work]
        for fut in as_completed(futures):
            try:
                row = fut.result()
                done += 1
                elapsed = time.time() - t_start
                print(
                    f"[sweep] {done}/{total} {row['model']} {row['candidate_name']} "
                    f"r{row['repeat']} verdict={row['verdict']} "
                    f"cite={row['metric_citation_count']} "
                    f"cost=${row['cost_usd']:.3f} elapsed={elapsed:.0f}s",
                    flush=True,
                )
            except Exception as e:
                done += 1
                print(f"[sweep] {done}/{total} ERROR: {e}", flush=True)
    print(f"[sweep] done in {time.time()-t_start:.0f}s")


# -----------------------------------------------------------------------
# Analyze
# -----------------------------------------------------------------------


def _df_to_md(df: pd.DataFrame, index_name: str | None = None) -> str:
    """Render a DataFrame as a pipe-markdown table without the tabulate dep."""
    df = df.copy()
    if index_name is None:
        index_name = df.index.name or ""
    # Reset index so the first column shows index values
    headers = [index_name] + [str(c) for c in df.columns]
    rows = []
    for idx, row in df.iterrows():
        idx_str = str(idx) if not isinstance(idx, tuple) else " / ".join(str(p) for p in idx)
        row_cells = [idx_str] + [
            (f"{v:.2f}" if isinstance(v, (float, np.floating)) else str(v))
            for v in row.values
        ]
        rows.append(row_cells)
    sep = ["---"] * len(headers)
    out = []
    out.append("| " + " | ".join(headers) + " |")
    out.append("| " + " | ".join(sep) + " |")
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def analyze() -> None:
    if not JSONL_PATH.exists():
        raise SystemExit(f"{JSONL_PATH} not found — run sweep first.")
    rows = [json.loads(l) for l in JSONL_PATH.read_text().splitlines() if l.strip()]
    df = pd.DataFrame(rows)
    print(f"[analyze] loaded {len(df)} rows")

    # Per-model aggregates
    agg = df.groupby("model").agg(
        n=("verdict", "size"),
        n_parsed=("verdict", lambda s: int((s != "UNPARSED").sum())),
        pct_cite_2plus=("cites_two_or_more_metrics", lambda s: 100 * s.mean()),
        avg_citation_count=("metric_citation_count", "mean"),
        avg_reason_chars=("reason_length_chars", "mean"),
        avg_latency_s=("latency_sec", "mean"),
        total_cost_usd=("cost_usd", "sum"),
    ).round(2)

    # Dissent rate on gate-PASS candidates: FAIL/NEEDS_MORE_TESTS verdict
    # counts as dissent against the gate's PASS decision.
    def _dissent_rate(sub: pd.DataFrame) -> float:
        pass_rows = sub[sub["gate_verdict"] == "PASS"]
        if len(pass_rows) == 0:
            return float("nan")
        dissent = pass_rows["verdict"].isin(["FAIL", "NEEDS_MORE_TESTS"])
        return float(100 * dissent.mean())

    agg["dissent_on_gate_PASS_pct"] = df.groupby("model").apply(_dissent_rate).round(2)

    # Verdict distribution
    verdict_pivot = (
        df.groupby(["model", "verdict"]).size().unstack(fill_value=0)
    )

    # Per-candidate × model specificity
    per_cand = (
        df.groupby(["candidate_name", "candidate_category", "model"])
        .agg(
            pct_cite_2plus=("cites_two_or_more_metrics", lambda s: 100 * s.mean()),
            verdicts=("verdict", lambda s: dict(s.value_counts())),
        )
        .reset_index()
    )

    # Plot: histogram of metric_citation_count per model
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 5))
        max_cite = int(df["metric_citation_count"].max() or 0)
        bins = np.arange(-0.5, max_cite + 1.5, 1)
        colors = {"claude-opus-4-7": "#d62728", "claude-sonnet-4-6": "#1f77b4",
                  "claude-haiku-4-5": "#2ca02c"}
        for m in MODELS:
            vals = df.loc[df["model"] == m, "metric_citation_count"]
            if len(vals) == 0:
                continue
            ax.hist(
                vals, bins=bins, alpha=0.55,
                label=f"{m} (mean={vals.mean():.2f})",
                color=colors.get(m, None),
            )
        ax.set_xlabel("# distinct metric names cited in Skeptic reason")
        ax.set_ylabel("# Skeptic calls")
        ax.set_title("Skeptic specificity by model (E2 cross-model ablation)")
        ax.legend()
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(HIST_PATH, dpi=140)
        print(f"[analyze] wrote {HIST_PATH}")
    except Exception as e:
        print(f"[analyze] plot skipped: {e}")

    # Update SUMMARY.md with observed results. Preserves the pre-registered
    # predictions block at the top (we look for a marker and replace everything
    # after it).
    marker = "<!-- OBSERVED_RESULTS_BELOW -->"
    existing = SUMMARY_PATH.read_text() if SUMMARY_PATH.exists() else ""
    if marker in existing:
        prefix = existing.split(marker)[0] + marker + "\n"
    else:
        prefix = existing.rstrip() + "\n\n" + marker + "\n"

    # Build observed section
    lines: list[str] = []
    lines.append("")
    lines.append("## Observed results")
    lines.append("")
    lines.append(
        f"Sweep completed: **{len(df)} Skeptic calls** across {df['model'].nunique()} "
        f"models, {df['candidate_name'].nunique()} candidates, "
        f"≈{int(len(df) / (df['model'].nunique() * df['candidate_name'].nunique()))} repeats."
    )
    lines.append("")
    lines.append("### Headline table")
    lines.append("")
    lines.append(agg.pipe(_df_to_md))
    lines.append("")
    lines.append("### Verdict distribution (rows = model, cols = verdict)")
    lines.append("")
    lines.append(verdict_pivot.pipe(_df_to_md))
    lines.append("")
    lines.append("### Per-candidate × model specificity (% citing ≥2 metrics)")
    lines.append("")
    spec_pivot = per_cand.pivot_table(
        index=["candidate_name", "candidate_category"],
        columns="model",
        values="pct_cite_2plus",
        aggfunc="first",
    ).round(1)
    lines.append(spec_pivot.pipe(_df_to_md))
    lines.append("")
    lines.append("### Pre-registered prediction verification")
    lines.append("")

    def _row(label: str, threshold: str, observed: float, pred_pass: bool) -> str:
        check = "✅" if pred_pass else "❌"
        return f"- {check} **{label}** — predicted {threshold}; observed {observed:.1f}%."

    opus_spec = float(agg.loc["claude-opus-4-7", "pct_cite_2plus"]) if "claude-opus-4-7" in agg.index else float("nan")
    sonnet_spec = float(agg.loc["claude-sonnet-4-6", "pct_cite_2plus"]) if "claude-sonnet-4-6" in agg.index else float("nan")
    haiku_spec = float(agg.loc["claude-haiku-4-5", "pct_cite_2plus"]) if "claude-haiku-4-5" in agg.index else float("nan")

    lines.append(_row("Opus ≥2 metric citations ≥70%", "≥70%", opus_spec, opus_spec >= 70))
    lines.append(_row("Sonnet ≥2 metric citations 30-60%", "30–60%", sonnet_spec, 30 <= sonnet_spec <= 60))
    lines.append(_row("Haiku ≥2 metric citations ≤30%", "≤30%", haiku_spec, haiku_spec <= 30))
    lines.append("")
    lines.append("*If any prediction is falsified, the honest finding is reported*")
    lines.append("*verbatim; `docs/why_opus_4_7.md` is updated to cite the observed result.*")
    lines.append("")

    cost_total = float(df["cost_usd"].sum())
    lines.append(f"**Total API spend for this sweep:** ${cost_total:.2f}")
    lines.append("")
    lines.append("Per-call data: `results/ablation/skeptic_model_sweep.jsonl`")
    lines.append("Histogram: `results/ablation/plots/model_specificity_histogram.png`")
    lines.append("")

    SUMMARY_PATH.write_text(prefix + "\n".join(lines))
    print(f"[analyze] wrote {SUMMARY_PATH}")


# -----------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("precompute")
    sp = sub.add_parser("sweep")
    sp.add_argument("--workers", type=int, default=6)
    sp.add_argument("--repeats", type=int, default=10)
    sp.add_argument("--only-model", type=str, default=None)
    sub.add_parser("analyze")
    args = parser.parse_args()

    if args.cmd == "precompute":
        precompute_metrics()
    elif args.cmd == "sweep":
        run_sweep(workers=args.workers, repeats=args.repeats, only_model=args.only_model)
    elif args.cmd == "analyze":
        analyze()


if __name__ == "__main__":
    main()
