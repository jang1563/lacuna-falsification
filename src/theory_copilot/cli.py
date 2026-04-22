from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .contracts import smoke_validate_dataset_cards
from .falsification import run_falsification_suite
from .opus_client import OpusClient
from .qc import write_json
from .reuse_plan import build_reuse_first_stage1_manifest
from .reuse_inventory import inventory_existing_public_data
from .staging import (
    review_progress,
    summarize_registry,
    summarize_stage1_execution_plan,
    write_cayuga_layout_script,
    write_cayuga_stage1_download_script,
    write_cayuga_stage1_reuse_script,
)
from .workflow_data import build_workflow_exports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Theory Copilot staging and QC utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    layout = subparsers.add_parser("render-cayuga-layout", help="Write a Cayuga layout script")
    layout.add_argument("--policy", required=True)
    layout.add_argument("--registry", required=True)
    layout.add_argument("--remote-root", required=True)
    layout.add_argument("--output", required=True)

    registry = subparsers.add_parser("summarize-registry", help="Summarize a registry CSV")
    registry.add_argument("--registry", required=True)

    progress = subparsers.add_parser("report-progress", help="Report overall staging/download progress")
    progress.add_argument("--policy", required=True)
    progress.add_argument("--stage1-registry", required=True)
    progress.add_argument("--workflow-registry", required=True)
    progress.add_argument("--local-public-root", required=True)
    progress.add_argument("--stage1-plan")
    progress.add_argument("--reuse-inventory")

    stage1_plan = subparsers.add_parser(
        "summarize-stage1-plan",
        help="Summarize the resolved vs unresolved Cayuga stage1 execution plan",
    )
    stage1_plan.add_argument("--policy", required=True)
    stage1_plan.add_argument("--registry", required=True)
    stage1_plan.add_argument("--plan", required=True)

    stage1_script = subparsers.add_parser(
        "render-cayuga-stage1-downloads",
        help="Write a Gate 0-aware Cayuga stage1 download/QC shell script",
    )
    stage1_script.add_argument("--policy", required=True)
    stage1_script.add_argument("--registry", required=True)
    stage1_script.add_argument("--plan", required=True)
    stage1_script.add_argument("--remote-root", required=True)
    stage1_script.add_argument("--output", required=True)

    reuse_script = subparsers.add_parser(
        "render-cayuga-stage1-reuse",
        help="Write a Gate 0-aware Cayuga stage1 reuse/copy shell script",
    )
    reuse_script.add_argument("--policy", required=True)
    reuse_script.add_argument("--registry", required=True)
    reuse_script.add_argument("--reuse-manifest", required=True)
    reuse_script.add_argument("--remote-root", required=True)
    reuse_script.add_argument("--output", required=True)

    inventory = subparsers.add_parser(
        "inventory-existing-data",
        help="Inventory already-downloaded public data candidates in external project roots",
    )
    inventory.add_argument("--config", required=True)
    inventory.add_argument("--stage1-registry", required=True)
    inventory.add_argument("--workflow-spec", required=True)
    inventory.add_argument("--output", required=True)
    inventory.add_argument("--summary-output")
    inventory.add_argument("--max-depth", type=int, default=5)

    reuse_manifest = subparsers.add_parser(
        "plan-reuse-sources",
        help="Build a reuse-first source manifest for stage1 datasets",
    )
    reuse_manifest.add_argument("--inventory", required=True)
    reuse_manifest.add_argument("--stage1-registry", required=True)
    reuse_manifest.add_argument("--stage1-plan", required=True)
    reuse_manifest.add_argument("--output", required=True)
    reuse_manifest.add_argument("--summary-output")

    exports = subparsers.add_parser("build-workflow-exports", help="Build real workflow CSVs")
    exports.add_argument("--spec", required=True)
    exports.add_argument("--project-root", default=".")

    smoke = subparsers.add_parser("smoke-datasets", help="Validate dataset cards against CSVs")
    smoke.add_argument("--config", required=True)
    smoke.add_argument("--output")

    compare = subparsers.add_parser(
        "compare",
        help="Run law proposal stage and print PySR sweep handoff command",
    )
    compare.add_argument("--config", required=True, help="Path to datasets.json")
    compare.add_argument("--proposals", required=True, help="Path to law_proposals.json")
    compare.add_argument("--flagship-dataset", required=True, help="Dataset ID for flagship run")
    compare.add_argument("--output-root", required=True, help="Root directory for artifacts")

    replay = subparsers.add_parser(
        "replay",
        help="Replay falsification suite on a transfer dataset using the flagship survivor equation",
    )
    replay.add_argument("--flagship-artifacts", required=True, help="Directory containing falsification_report.json")
    replay.add_argument("--transfer-dataset", required=True, help="Transfer dataset ID")
    replay.add_argument("--output-root", required=True, help="Root directory for output artifacts")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "render-cayuga-layout":
        output_path = write_cayuga_layout_script(
            args.output,
            policy_path=args.policy,
            registry_path=args.registry,
            remote_root=args.remote_root,
        )
        print(output_path)
        return 0

    if args.command == "summarize-registry":
        print(json.dumps(summarize_registry(args.registry), indent=2, sort_keys=True))
        return 0

    if args.command == "report-progress":
        summary = review_progress(
            policy_path=args.policy,
            stage1_registry_path=args.stage1_registry,
            workflow_registry_path=args.workflow_registry,
            local_public_root=args.local_public_root,
            stage1_plan_path=args.stage1_plan,
            reuse_inventory_path=args.reuse_inventory,
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    if args.command == "summarize-stage1-plan":
        summary = summarize_stage1_execution_plan(
            policy_path=args.policy,
            registry_path=args.registry,
            plan_path=args.plan,
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0 if summary["status"] == "pass" else 1

    if args.command == "render-cayuga-stage1-downloads":
        output_path = write_cayuga_stage1_download_script(
            args.output,
            policy_path=args.policy,
            registry_path=args.registry,
            plan_path=args.plan,
            remote_root=args.remote_root,
        )
        print(output_path)
        return 0

    if args.command == "render-cayuga-stage1-reuse":
        output_path = write_cayuga_stage1_reuse_script(
            args.output,
            policy_path=args.policy,
            registry_path=args.registry,
            reuse_manifest_path=args.reuse_manifest,
            remote_root=args.remote_root,
        )
        print(output_path)
        return 0

    if args.command == "inventory-existing-data":
        summary = inventory_existing_public_data(
            config_path=args.config,
            stage1_registry_path=args.stage1_registry,
            workflow_spec_path=args.workflow_spec,
            output_path=args.output,
            summary_path=args.summary_output,
            max_depth=args.max_depth,
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    if args.command == "plan-reuse-sources":
        summary = build_reuse_first_stage1_manifest(
            inventory_path=args.inventory,
            stage1_registry_path=args.stage1_registry,
            stage1_plan_path=args.stage1_plan,
            output_path=args.output,
            summary_path=args.summary_output,
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    if args.command == "build-workflow-exports":
        summary = build_workflow_exports(args.spec, project_root=args.project_root)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0 if summary["status"] == "pass" else 1

    if args.command == "smoke-datasets":
        summary = smoke_validate_dataset_cards(args.config)
        if args.output:
            write_json(args.output, summary)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0 if summary["status"] == "pass" else 1

    if args.command == "compare":
        config_data = json.loads(Path(args.config).read_text())
        flagship_card = next(
            (d for d in config_data if d.get("dataset_id") == args.flagship_dataset),
            config_data[0] if config_data else {},
        )
        proposals = json.loads(Path(args.proposals).read_text())
        features = [p.get("name", p.get("symbolic_template", "")) for p in proposals]

        client = OpusClient()
        client.propose_laws(dataset_card=flagship_card, features=features)

        output_root = args.output_root.rstrip("/")
        print(
            f"Proposal complete. Run PySR sweep manually: "
            f"python3 src/pysr_sweep.py "
            f"--dataset {args.flagship_dataset} "
            f"--output-root {output_root}"
        )
        print(
            f"After sweep completes, run: theory-copilot replay "
            f"--flagship-artifacts {output_root}/flagship_run/ "
            f"--transfer-dataset <dataset-id> "
            f"--output-root {output_root}"
        )
        return 0

    if args.command == "replay":
        flagship_dir = Path(args.flagship_artifacts)
        report = json.loads((flagship_dir / "falsification_report.json").read_text())

        survivors = [r for r in report if r.get("passes")]
        if not survivors:
            print("No surviving equations in flagship run.")
            return 1
        top = max(survivors, key=lambda r: r.get("auroc", r.get("law_auc", 0.0)))
        equation = top["equation"]

        transfer_id = args.transfer_dataset
        candidate_paths = [
            Path("data") / f"{transfer_id}.csv",
            Path("data") / f"{transfer_id}_kirc.csv",
            Path("data") / "examples" / f"{transfer_id}.csv",
        ]
        transfer_csv = next((p for p in candidate_paths if p.exists()), None)
        if transfer_csv is None:
            tried = [str(p) for p in candidate_paths]
            print(f"Transfer dataset CSV not found for '{transfer_id}'. Tried: {tried}")
            return 1

        df = pd.read_csv(transfer_csv)
        label_col = "label"
        gene_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != label_col]
        X = df[gene_cols].values.astype(float)
        y = df[label_col].values.astype(int)

        def _equation_fn(X_arr: np.ndarray) -> np.ndarray:
            ns = {f"x{i}": X_arr[:, i] for i in range(X_arr.shape[1])}
            ns.update({k: getattr(np, k) for k in ["log", "log1p", "exp", "abs", "sqrt", "sin", "cos"]})
            return eval(equation, {"__builtins__": {}}, ns)  # noqa: S307

        transfer_result = run_falsification_suite(_equation_fn, X, y)

        output_dir = Path(args.output_root) / "transfer_run"
        output_dir.mkdir(parents=True, exist_ok=True)
        transfer_report = {**top, **transfer_result, "transfer_dataset": transfer_id}
        write_json(output_dir / "transfer_report.json", transfer_report)

        client = OpusClient()
        dataset_context = {"transfer_dataset": transfer_id, "equation": equation}
        interpretation = client.interpret_survivor(equation, dataset_context)
        write_json(output_dir / "interpretation.json", interpretation)

        status = "PASS" if transfer_result["passes"] else "FAIL"
        print(json.dumps({
            "equation": equation,
            "transfer_dataset": transfer_id,
            "passes": transfer_result["passes"],
            "law_auc": transfer_result["law_auc"],
            "status": status,
        }, indent=2, sort_keys=True))
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
