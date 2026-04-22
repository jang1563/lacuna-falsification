"""Tests for the falsification_sweep batch runner."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture
def tmp_workspace(tmp_path):
    rng = np.random.default_rng(42)
    n = 100
    half = n // 2

    y = np.array([1] * half + [0] * half)

    # gene_0: high in disease, gene_1: high in control → "x0 - x1" separates strongly
    gene_0 = np.concatenate([rng.normal(1.5, 1, half), rng.normal(-1.5, 1, half)])
    gene_1 = np.concatenate([rng.normal(-1.5, 1, half), rng.normal(1.5, 1, half)])
    gene_2 = rng.normal(0, 1, n)
    gene_3 = rng.normal(0, 1, n)

    age = rng.integers(30, 70, n).astype(float)
    batch_index = rng.integers(0, 2, n).astype(float)

    df = pd.DataFrame(
        {
            "gene_0": gene_0,
            "gene_1": gene_1,
            "gene_2": gene_2,
            "gene_3": gene_3,
            "age": age,
            "batch_index": batch_index,
            "label": y,
        }
    )
    data_path = tmp_path / "test_data.csv"
    df.to_csv(data_path, index=False)

    # xi notation: x0=gene_0, x1=gene_1, x2=gene_2, x3=gene_3
    candidates = [
        {"equation": "x0 - x1", "auroc": 0.95, "complexity": 3},
        {"equation": "x0 + 0 * x1", "auroc": 0.55, "complexity": 4},
        {"equation": "x2 * 0.1", "auroc": 0.50, "complexity": 2},
    ]
    cand_path = tmp_path / "candidates.json"
    cand_path.write_text(json.dumps(candidates))

    out_path = tmp_path / "report.json"
    return data_path, cand_path, out_path


def test_falsification_sweep_produces_output(tmp_workspace):
    data_path, cand_path, out_path = tmp_workspace

    result = subprocess.run(
        [
            sys.executable,
            "src/falsification_sweep.py",
            "--candidates", str(cand_path),
            "--data", str(data_path),
            "--covariate-cols", "age,batch_index",
            "--n-permutations", "50",
            "--n-resamples", "50",
            "--output", str(out_path),
        ],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )

    assert result.returncode == 0, f"Script failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    assert out_path.exists(), "Output JSON was not created"

    report = json.loads(out_path.read_text())
    assert len(report) == 3, f"Expected 3 entries, got {len(report)}"

    required_keys = {"passes", "perm_p", "perm_p_fdr", "ci_width", "delta_baseline", "delta_confound", "fail_reason"}
    for entry in report:
        assert "passes" in entry, f"Missing 'passes' key in {entry}"
        for key in required_keys:
            assert key in entry, f"Missing '{key}' key in {entry}"
        assert isinstance(entry["passes"], bool)
        assert isinstance(entry["perm_p"], float)
        assert isinstance(entry["perm_p_fdr"], float)
        assert isinstance(entry["fail_reason"], str)


def test_falsification_sweep_no_covariates(tmp_workspace):
    data_path, cand_path, out_path = tmp_workspace

    result = subprocess.run(
        [
            sys.executable,
            "src/falsification_sweep.py",
            "--candidates", str(cand_path),
            "--data", str(data_path),
            "--n-permutations", "50",
            "--n-resamples", "50",
            "--output", str(out_path),
        ],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )

    assert result.returncode == 0, f"Script failed:\nSTDERR: {result.stderr}"
    report = json.loads(out_path.read_text())
    assert len(report) == 3
    for entry in report:
        assert "passes" in entry
        assert entry["delta_confound"] is None


def test_falsification_sweep_summary_line(tmp_workspace):
    data_path, cand_path, out_path = tmp_workspace

    result = subprocess.run(
        [
            sys.executable,
            "src/falsification_sweep.py",
            "--candidates", str(cand_path),
            "--data", str(data_path),
            "--n-permutations", "50",
            "--n-resamples", "50",
            "--output", str(out_path),
        ],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )

    assert result.returncode == 0
    assert "candidates" in result.stdout
    assert "survived falsification" in result.stdout
