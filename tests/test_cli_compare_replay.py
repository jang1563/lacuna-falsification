"""Tests for the compare and replay CLI commands."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from theory_copilot.cli import main


# ---- shared helpers ----

def _mock_opus_client():
    client = MagicMock()
    client.propose_laws.return_value = {
        "families": [{"name": "ratio", "equation": "x0/x1"}],
        "raw_thinking": "",
        "raw_response": '{"families": []}',
    }
    client.interpret_survivor.return_value = {
        "mechanism": "test mechanism",
        "prediction": "test prediction",
        "hypothesis": "test hypothesis",
    }
    return client


def _make_datasets_config(tmp_path):
    config = [
        {
            "dataset_id": "kirc",
            "name": "Test KIRC dataset",
            "local_path": "data/test.csv",
            "disease_label": "disease",
            "control_label": "control",
            "modality": "synthetic",
            "species": "human",
            "sample_count": 50,
            "allowed_covariates": [],
        }
    ]
    p = tmp_path / "datasets.json"
    p.write_text(json.dumps(config))
    return p


def _make_proposals_config(tmp_path):
    proposals = [
        {"name": "ratio_law", "symbolic_template": "x0/x1"},
        {"name": "difference_law", "symbolic_template": "x0-x1"},
    ]
    p = tmp_path / "law_proposals.json"
    p.write_text(json.dumps(proposals))
    return p


def _make_flagship_report(tmp_path):
    flagship_dir = tmp_path / "flagship_run"
    flagship_dir.mkdir(parents=True, exist_ok=True)
    report = [
        {
            "equation": "x0 - x1",
            "auroc": 0.91,
            "complexity": 3,
            "passes": True,
            "perm_p": 0.001,
            "perm_p_fdr": 0.003,
            "ci_width": 0.05,
            "delta_baseline": 0.12,
            "delta_confound": None,
            "fail_reason": "",
        },
        {
            "equation": "x0 + x1",
            "auroc": 0.55,
            "complexity": 3,
            "passes": False,
            "perm_p": 0.30,
            "perm_p_fdr": 0.50,
            "ci_width": 0.20,
            "delta_baseline": 0.02,
            "delta_confound": None,
            "fail_reason": "perm_p",
        },
    ]
    (flagship_dir / "falsification_report.json").write_text(json.dumps(report))
    return flagship_dir


def _make_transfer_csv(tmp_path, transfer_id="gse40435"):
    rng = np.random.default_rng(42)
    n = 80
    half = n // 2
    y = np.array([1] * half + [0] * half)
    gene_0 = np.concatenate([rng.normal(1.5, 1, half), rng.normal(-1.5, 1, half)])
    gene_1 = np.concatenate([rng.normal(-1.5, 1, half), rng.normal(1.5, 1, half)])
    df = pd.DataFrame({"gene_0": gene_0, "gene_1": gene_1, "label": y})
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    csv_path = data_dir / f"{transfer_id}.csv"
    df.to_csv(csv_path, index=False)
    return csv_path


# ---- compare tests ----

def test_compare_prints_pysr_handoff(tmp_path, monkeypatch, capsys):
    config_path = _make_datasets_config(tmp_path)
    proposals_path = _make_proposals_config(tmp_path)
    output_root = str(tmp_path / "artifacts")

    mock_client = _mock_opus_client()
    with patch("theory_copilot.cli.OpusClient", return_value=mock_client):
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "theory-copilot",
                "compare",
                "--config", str(config_path),
                "--proposals", str(proposals_path),
                "--flagship-dataset", "kirc",
                "--output-root", output_root,
            ],
        )
        result = main()

    captured = capsys.readouterr()
    assert result == 0
    assert "python3 src/pysr_sweep.py" in captured.out
    assert "theory-copilot replay" in captured.out


def test_compare_calls_propose_laws(tmp_path, monkeypatch):
    config_path = _make_datasets_config(tmp_path)
    proposals_path = _make_proposals_config(tmp_path)

    mock_client = _mock_opus_client()
    with patch("theory_copilot.cli.OpusClient", return_value=mock_client):
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "theory-copilot",
                "compare",
                "--config", str(config_path),
                "--proposals", str(proposals_path),
                "--flagship-dataset", "kirc",
                "--output-root", str(tmp_path / "out"),
            ],
        )
        result = main()

    assert result == 0
    mock_client.propose_laws.assert_called_once()
    call_kwargs = mock_client.propose_laws.call_args
    assert call_kwargs is not None


# ---- replay tests ----

def test_replay_creates_transfer_report(tmp_path, monkeypatch, capsys):
    flagship_dir = _make_flagship_report(tmp_path)
    _make_transfer_csv(tmp_path, "gse40435")
    output_root = str(tmp_path / "output")

    mock_client = _mock_opus_client()
    monkeypatch.chdir(tmp_path)
    with patch("theory_copilot.cli.OpusClient", return_value=mock_client):
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "theory-copilot",
                "replay",
                "--flagship-artifacts", str(flagship_dir),
                "--transfer-dataset", "gse40435",
                "--output-root", output_root,
            ],
        )
        result = main()

    assert result == 0

    report_path = Path(output_root) / "transfer_run" / "transfer_report.json"
    assert report_path.exists(), f"transfer_report.json not found at {report_path}"
    report = json.loads(report_path.read_text())
    assert "passes" in report
    assert isinstance(report["passes"], bool)


def test_replay_saves_interpretation(tmp_path, monkeypatch):
    flagship_dir = _make_flagship_report(tmp_path)
    _make_transfer_csv(tmp_path, "gse40435")
    output_root = str(tmp_path / "output")

    mock_client = _mock_opus_client()
    monkeypatch.chdir(tmp_path)
    with patch("theory_copilot.cli.OpusClient", return_value=mock_client):
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "theory-copilot",
                "replay",
                "--flagship-artifacts", str(flagship_dir),
                "--transfer-dataset", "gse40435",
                "--output-root", output_root,
            ],
        )
        result = main()

    assert result == 0
    interp_path = Path(output_root) / "transfer_run" / "interpretation.json"
    assert interp_path.exists()
    mock_client.interpret_survivor.assert_called_once()


def test_replay_no_survivors_returns_one(tmp_path, monkeypatch):
    flagship_dir = tmp_path / "flagship_run"
    flagship_dir.mkdir()
    report = [
        {
            "equation": "x0 + x1",
            "auroc": 0.55,
            "passes": False,
            "perm_p": 0.30,
            "fail_reason": "perm_p",
        }
    ]
    (flagship_dir / "falsification_report.json").write_text(json.dumps(report))
    _make_transfer_csv(tmp_path, "gse40435")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "theory-copilot",
            "replay",
            "--flagship-artifacts", str(flagship_dir),
            "--transfer-dataset", "gse40435",
            "--output-root", str(tmp_path / "output"),
        ],
    )
    result = main()
    assert result == 1


def test_replay_missing_csv_returns_one(tmp_path, monkeypatch):
    flagship_dir = _make_flagship_report(tmp_path)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "theory-copilot",
            "replay",
            "--flagship-artifacts", str(flagship_dir),
            "--transfer-dataset", "nonexistent_dataset",
            "--output-root", str(tmp_path / "output"),
        ],
    )
    result = main()
    assert result == 1
