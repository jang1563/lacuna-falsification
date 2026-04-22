"""Theory Copilot CLI.

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
_NUMPY_FUNCS = ["log", "log1p", "exp", "abs", "sqrt", "sin", "cos"]


def _write_json(path: Path, payload: dict | list) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str))
    return path


def _parse_labels(series: pd.Series) -> np.ndarray:
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(int).values
    s = series.astype(str).str.strip().str.lower()
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
            config_data[0] if config_data else {},
        )
        local_path = flagship_card.get("local_path", f"data/{args.flagship_dataset}.csv")
        dataset_id_for_handoff = args.flagship_dataset
        gene_list_for_handoff = "CA9,VEGFA,LDHA,AGXT,ALB,NDUFA4L2,SLC2A1,ENO2"
        cov_list_for_handoff = "age,batch_index"

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
        f"Then: theory-copilot replay "
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

    top = max(survivors, key=lambda r: r.get("auroc", r.get("law_auc", 0.0)))
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="theory-copilot",
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

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
