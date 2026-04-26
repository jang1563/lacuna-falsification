"""Lacuna CLI.

Two commands:

  compare --config datasets.json --proposals law_proposals.json \
          --flagship-dataset <id> --output-root <dir>
      Invokes the Opus 4.7 Proposer, saves the proposal output, and prints
      the PySR + falsification commands to run next plus the replay command.

  replay --flagship-artifacts <flagship_run_dir> --transfer-dataset <id> \
         --output-root <dir>
      Loads the flagship falsification_report.json, picks the highest-AUROC
      survivor, evaluates it on an independent transfer cohort CSV, runs
      the full 5-test falsification gate with per-cohort z-score standardization,
      and writes transfer_report.json + interpretation.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from .data_loader import DatasetCard
from .falsification import run_falsification_suite
from .opus_client import OpusClient


_DISEASE_TOKENS = {"disease", "tumor", "case", "cancer", "1", "true"}
_CONTROL_TOKENS = {"control", "normal", "healthy", "0", "false"}
_NUMPY_FUNCS = ["log", "log1p", "exp", "abs", "sqrt", "sin", "cos"]


def _write_json(path: Path, payload: dict | list) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str))
    return path


def _parse_labels(series: pd.Series) -> np.ndarray:
    """Parse a label column into 0/1.

    Disease tokens → 1, control tokens → 0. Unknown string labels print
    a warning to stderr (review-handoff finding #16: silently mapping
    unknowns to control can invert or dilute cohorts; especially risky
    for plug-in datasets with stage / metastasis labels). They are
    still mapped to 0 to preserve current behaviour, but the warning
    surfaces them. Custom tokens → use DatasetCard with explicit
    `disease_tokens` (see `data_loader._parse_labels`).
    """
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(int).values
    s = series.astype(str).str.strip().str.lower()
    unknown = sorted(set(s.unique()) - _DISEASE_TOKENS - _CONTROL_TOKENS)
    if unknown:
        print(
            f"_parse_labels WARNING: {len(unknown)} unknown label value(s) "
            f"mapped to 0 (control): {unknown[:5]}"
            f"{'...' if len(unknown) > 5 else ''}. "
            "If these are valid disease labels (e.g. stage IV / M1) use "
            "DatasetCard with explicit `disease_tokens=[...]` instead.",
            file=sys.stderr,
        )
    return s.map(lambda v: 1 if v in _DISEASE_TOKENS else 0).values.astype(int)


def _zscore(X: np.ndarray) -> np.ndarray:
    mean = X.mean(axis=0, keepdims=True)
    std = X.std(axis=0, keepdims=True)
    std = np.where(std < 1e-8, 1.0, std)
    return (X - mean) / std


def _equation_callable(equation_str: str, col_names: list[str]):
    ns_funcs = {k: getattr(np, k) for k in _NUMPY_FUNCS}

    def fn(X: np.ndarray) -> np.ndarray:
        ns = {col_names[i]: X[:, i] for i in range(len(col_names))}
        ns.update({f"x{i}": X[:, i] for i in range(X.shape[1])})
        ns.update(ns_funcs)
        return eval(equation_str, {"__builtins__": {}}, ns)  # noqa: S307

    return fn


def _cmd_compare(args: argparse.Namespace) -> int:
    # Two ways to describe the flagship dataset: the legacy datasets.json
    # list (--config + --flagship-dataset), or a DatasetCard JSON
    # (--dataset-card). The card path takes priority when both are given.
    if not getattr(args, "dataset_card", None) and not (args.config and args.flagship_dataset):
        print(
            "compare requires either --dataset-card OR both --config and --flagship-dataset.",
            file=sys.stderr,
        )
        return 2
    if getattr(args, "dataset_card", None):
        card = DatasetCard.from_json(args.dataset_card)
        flagship_card = {
            "dataset_id": card.dataset_id,
            "name": card.dataset_id,
            "local_path": card.csv_path,
            "disease_label": "disease",
            "control_label": "control",
            "modality": "csv",
            "species": "human",
            "sample_count": None,
            "allowed_covariates": list(card.covariate_columns),
            "notes": card.notes,
        }
        local_path = card.csv_path
        dataset_id_for_handoff = card.dataset_id
        gene_list_for_handoff = ",".join(card.gene_columns)
        cov_list_for_handoff = ",".join(card.covariate_columns) if card.covariate_columns else ""
    else:
        config_data = json.loads(Path(args.config).read_text())
        flagship_card = next(
            (d for d in config_data if d.get("dataset_id") == args.flagship_dataset),
            None,
        )
        if flagship_card is None:
            available_ids = [d.get("dataset_id", "<no-id>") for d in config_data]
            print(
                f"compare: flagship-dataset '{args.flagship_dataset}' not found in "
                f"{args.config}. Available IDs: {available_ids}",
                file=sys.stderr,
            )
            return 2
        local_path = flagship_card.get("local_path", f"data/{args.flagship_dataset}.csv")
        dataset_id_for_handoff = args.flagship_dataset
        # Honest scope note: the legacy --config + --flagship-dataset path
        # cannot infer a per-dataset gene list or covariate list automatically
        # (DatasetCard does, hence the recommended path). Read these from the
        # config entry when present; otherwise fall back to the documented
        # KIRC default but PRINT the fallback so the user notices.
        gene_list_for_handoff = flagship_card.get(
            "gene_columns_csv",
            "CA9,VEGFA,LDHA,AGXT,ALB,NDUFA4L2,SLC2A1,ENO2",
        )
        cov_list_for_handoff = flagship_card.get(
            "covariate_columns_csv",
            ",".join(flagship_card.get("allowed_covariates", []))
            or "age,batch_index",
        )
        if "gene_columns_csv" not in flagship_card:
            print(
                "compare WARNING: --config path uses the KIRC default gene panel "
                "(CA9,VEGFA,LDHA,AGXT,ALB,NDUFA4L2,SLC2A1,ENO2). For non-KIRC "
                "cohorts use --dataset-card instead, OR add `gene_columns_csv` "
                "and `covariate_columns_csv` fields to the config entry.",
                file=sys.stderr,
            )

    proposals = json.loads(Path(args.proposals).read_text())
    features = [p.get("name", p.get("symbolic_template", "")) for p in proposals]

    client = OpusClient()
    proposer_result = client.propose_laws(
        dataset_card=flagship_card,
        features=features,
        context=flagship_card.get("name", ""),
    )

    output_root = args.output_root.rstrip("/")
    compare_dir = Path(output_root) / "compare_run"
    _write_json(compare_dir / "proposer_output.json", proposer_result)

    print(
        f"Proposer emitted {len(proposer_result.get('families', []))} law families -> "
        f"{compare_dir / 'proposer_output.json'}"
    )
    print()
    print("Run the PySR sweep manually:")
    print(
        f"  python3 src/pysr_sweep.py --data {local_path} "
        f"--genes {gene_list_for_handoff} "
        f"--proposals {args.proposals} --standardize "
        f"--output {output_root}/flagship_run/candidates.json"
    )
    covariate_arg = f"--covariate-cols {cov_list_for_handoff} " if cov_list_for_handoff else ""
    print(
        f"  python3 src/falsification_sweep.py "
        f"--candidates {output_root}/flagship_run/candidates.json "
        f"--data {local_path} --standardize {covariate_arg}"
        f"--output {output_root}/flagship_run/falsification_report.json"
    )
    print()
    print(
        f"Then: lacuna replay "
        f"--flagship-artifacts {output_root}/flagship_run/ "
        f"--transfer-dataset <dataset-id> --output-root {output_root}"
    )
    _ = dataset_id_for_handoff  # retained for future extensions
    return 0


def _cmd_plug_in_dataset(args: argparse.Namespace) -> int:
    covariates = [c.strip() for c in (args.covariate_columns or "").split(",") if c.strip()]
    exclude = [c.strip() for c in (args.exclude_columns or "").split(",") if c.strip()]
    card = DatasetCard.infer_from_csv(
        csv_path=args.csv,
        label_column=args.label_column,
        disease_id=args.disease_id,
        covariate_columns=covariates or None,
        exclude_columns=exclude or None,
    )
    out = card.to_json(args.output)
    print(
        json.dumps(
            {
                "dataset_id": card.dataset_id,
                "gene_column_count": len(card.gene_columns),
                "covariate_columns": card.covariate_columns,
                "output": str(out),
            },
            indent=2,
        )
    )
    return 0


def _cmd_replay(args: argparse.Namespace) -> int:
    flagship_dir = Path(args.flagship_artifacts)
    report_path = flagship_dir / "falsification_report.json"
    if not report_path.exists():
        print(f"Flagship report not found: {report_path}", file=sys.stderr)
        return 1

    flagship_report = json.loads(report_path.read_text())
    survivors = [r for r in flagship_report if r.get("passes")]
    if not survivors:
        print("No surviving laws in flagship report - nothing to replay.", file=sys.stderr)
        return 1

    transfer_id = args.transfer_dataset
    candidate_paths = [
        Path("data") / f"{transfer_id}.csv",
        Path("data") / f"{transfer_id}_kirc.csv",
        Path("data") / "examples" / f"{transfer_id}.csv",
    ]
    transfer_csv = next((p for p in candidate_paths if p.exists()), None)
    if transfer_csv is None:
        tried = [str(p) for p in candidate_paths]
        print(f"Transfer dataset CSV not found for '{transfer_id}'. Tried: {tried}", file=sys.stderr)
        return 1

    df = pd.read_csv(transfer_csv)
    label_col = "label"
    exclude = {label_col, "sample_id", "patient_id"}
    covariate_cols = [c for c in ("age", "batch_index") if c in df.columns]
    exclude |= set(covariate_cols)
    gene_cols = [
        c for c in df.select_dtypes(include=[np.number]).columns if c not in exclude
    ]
    X_raw = df[gene_cols].fillna(0).values.astype(float)
    X = _zscore(X_raw)
    y = _parse_labels(df[label_col])
    X_cov = df[covariate_cols].values.astype(float) if covariate_cols else None

    # Prefer the falsification gate's `law_auc` (gate-time, sign-invariant)
    # over the candidate-search `auroc` (PySR search-time). They can differ
    # when sign-invariance + bootstrap re-evaluation move the metric. Fix
    # for review-handoff finding #5 (2026-04-23): the prior order
    # `r.get("auroc", r.get("law_auc", ...))` could promote a search-time
    # winner that the gate later down-ranked.
    top = max(survivors, key=lambda r: r.get("law_auc", r.get("auroc", 0.0)))
    equation = top["equation"]
    fn = _equation_callable(equation, gene_cols)

    transfer_result = run_falsification_suite(fn, X, y, X_covariates=X_cov)
    transfer_report = {
        **top,
        **transfer_result,
        "transfer_dataset": transfer_id,
        "equation": equation,
    }

    output_dir = Path(args.output_root) / "transfer_run"
    _write_json(output_dir / "transfer_report.json", transfer_report)

    client = OpusClient()
    dataset_context = {
        "transfer_dataset": transfer_id,
        "equation": equation,
        "law_auc": transfer_result["law_auc"],
        "passes": transfer_result["passes"],
    }
    interpretation = client.interpret_survivor(equation, dataset_context)
    _write_json(output_dir / "interpretation.json", interpretation)

    status = "PASS" if transfer_result["passes"] else "FAIL"
    print(
        json.dumps(
            {
                "equation": equation,
                "transfer_dataset": transfer_id,
                "passes": transfer_result["passes"],
                "law_auc": transfer_result["law_auc"],
                "ci_lower": transfer_result["ci_lower"],
                "status": status,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _cmd_loop(args: argparse.Namespace) -> int:
    """
    Path C Routine driver — wraps run_path_b locally, OR fires a real Claude
    Code Routine via `/v1/claude_code/routines/{trig_id}/fire` when
    --use-routine is set (requires CLAUDE_ROUTINE_TRIG_ID + CLAUDE_ROUTINE_TOKEN
    env vars). Falls back to the local loop if either env var is missing.
    """
    import os

    from .managed_agent_runner import _NIGHT_TASKS, run_path_c_routine

    invoke_fn = None
    if getattr(args, "use_routine", False):
        if os.environ.get("CLAUDE_ROUTINE_TRIG_ID") and os.environ.get("CLAUDE_ROUTINE_TOKEN"):
            from .routines_client import make_routine_invoke_fn

            invoke_fn = make_routine_invoke_fn(_NIGHT_TASKS)
            print("[loop] Using real Routines /fire invocation.")
        else:
            print(
                "[loop] --use-routine requested but CLAUDE_ROUTINE_TRIG_ID / "
                "CLAUDE_ROUTINE_TOKEN not set; falling back to local Path B loop."
            )

    result = run_path_c_routine(
        night=args.night,
        interval_seconds=args.interval_seconds,
        max_iterations=args.max_iterations,
        watch_dir=args.watch_dir,
        log_path=args.log_path,
        invoke_fn=invoke_fn,
    )
    print(
        json.dumps(
            {
                "iteration_count": result.get("iteration_count", 0),
                "status": result.get("status", "unknown"),
                "log_path": result.get("log_path"),
                "last_session_id": result.get("session_id", ""),
                "routine_session_url": result.get("routine_session_url", ""),
            },
            indent=2,
        )
    )
    return 0 if result.get("status") in {"completed", "skipped_no_change"} else 1


def _cmd_persist_events(args: argparse.Namespace) -> int:
    """Paginate `sessions.events.list` and dump every event to JSONL."""
    from .managed_agent_runner import persist_session_events

    result = persist_session_events(
        session_id=args.session_id,
        out_path=args.output,
    )
    print(json.dumps(result, indent=2))
    return 0


def _cmd_replay_events(args: argparse.Namespace) -> int:
    """Replay user-origin events from a persisted log into a different session."""
    from .managed_agent_runner import replay_session_from_log

    result = replay_session_from_log(
        log_path=args.log,
        target_session_id=args.target_session_id,
    )
    print(json.dumps(result, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lacuna",
        description="Falsification-aware biological law discovery loop.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_compare = sub.add_parser(
        "compare",
        help="Run the Opus 4.7 Proposer and print the PySR + falsification handoff.",
    )
    p_compare.add_argument("--config", required=False, help="Path to datasets.json (legacy path)")
    p_compare.add_argument("--proposals", required=True, help="Path to law_proposals.json")
    p_compare.add_argument(
        "--flagship-dataset", required=False,
        help="Dataset ID for the flagship run (legacy path, requires --config).",
    )
    p_compare.add_argument(
        "--dataset-card", required=False,
        help="Path to a DatasetCard JSON file (preferred over --config + --flagship-dataset).",
    )
    p_compare.add_argument("--output-root", required=True, help="Root for artifacts.")
    p_compare.set_defaults(func=_cmd_compare)

    p_plug = sub.add_parser(
        "plug-in-dataset",
        help="Auto-infer a DatasetCard JSON from an arbitrary CSV.",
    )
    p_plug.add_argument("--csv", required=True, help="Path to the input CSV.")
    p_plug.add_argument("--label-column", required=True, help="Name of the disease/control column.")
    p_plug.add_argument("--disease-id", required=True, help="Short ID for this cohort/task.")
    p_plug.add_argument("--covariate-columns", required=False, default="",
                        help="Comma-separated covariate column names (optional).")
    p_plug.add_argument("--exclude-columns", required=False, default="",
                        help="Comma-separated columns to exclude from gene features (optional).")
    p_plug.add_argument("--output", required=True, help="Output DatasetCard JSON path.")
    p_plug.set_defaults(func=_cmd_plug_in_dataset)

    p_replay = sub.add_parser(
        "replay",
        help="Replay the flagship survivor on an independent transfer cohort.",
    )
    p_replay.add_argument(
        "--flagship-artifacts",
        required=True,
        help="Directory containing falsification_report.json.",
    )
    p_replay.add_argument(
        "--transfer-dataset", required=True, help="Transfer dataset ID."
    )
    p_replay.add_argument("--output-root", required=True, help="Root for artifacts.")
    p_replay.set_defaults(func=_cmd_replay)

    p_loop = sub.add_parser(
        "loop",
        help="Path C Routine: run the Managed Agent on a schedule or file-watch trigger.",
    )
    p_loop.add_argument(
        "--night", type=int, required=True, choices=[2, 3, 4],
        help="Night task to drive (2 = PySR sweep, 3 = falsification, 4 = replay).",
    )
    p_loop.add_argument(
        "--interval-seconds", type=int, default=1800,
        help="Seconds between iterations (default 1800 = 30min). 0 = fire once and exit.",
    )
    p_loop.add_argument(
        "--max-iterations", type=int, default=1,
        help="Hard stop after N iterations (0 = unbounded until SIGINT). Default 1 for safety.",
    )
    p_loop.add_argument(
        "--watch-dir", default=None,
        help="Only invoke when files under this directory change (baseline iteration always runs).",
    )
    p_loop.add_argument(
        "--log-path", default="results/routine/verdicts.jsonl",
        help="Append-mode JSONL log of per-iteration verdicts.",
    )
    p_loop.add_argument(
        "--use-routine", action="store_true",
        help=(
            "Fire a real Claude Code Routine (`POST /v1/claude_code/routines/"
            "{trig_id}/fire`) each iteration. Requires CLAUDE_ROUTINE_TRIG_ID + "
            "CLAUDE_ROUTINE_TOKEN env vars. Falls back to local Path B loop if "
            "either is missing."
        ),
    )
    p_loop.set_defaults(func=_cmd_loop)

    p_persist = sub.add_parser(
        "persist-events",
        help="Dump every event in a Managed Agents session to JSONL (durable log).",
    )
    p_persist.add_argument("--session-id", required=True, help="Managed Agents session id.")
    p_persist.add_argument("--output", required=True, help="Output JSONL file path.")
    p_persist.set_defaults(func=_cmd_persist_events)

    p_replay_ev = sub.add_parser(
        "replay-events",
        help=(
            "Replay user-origin events from a persisted log into a different "
            "session (brain/body-decouple demo)."
        ),
    )
    p_replay_ev.add_argument("--log", required=True, help="JSONL log from `persist-events`.")
    p_replay_ev.add_argument(
        "--target-session-id", required=True,
        help="Destination Managed Agents session id.",
    )
    p_replay_ev.set_defaults(func=_cmd_replay_events)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
