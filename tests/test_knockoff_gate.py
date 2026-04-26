"""Tests for G1 knockoff v2 gate.

Pre-registered in preregistrations/20260425T170647Z_g1_knockoff_v2.yaml.
These tests use small synthetic data; the real 25-replicate sweep on
kirc_metastasis_expanded is in src/track_a_knockoff_sweep.py.
"""
from __future__ import annotations

import numpy as np
import pytest

# Gracefully skip if knockpy not installed (pre-install state)
knockpy = pytest.importorskip("knockpy", reason="knockpy not installed; skip G1 tests")

from lacuna.knockoff_gate import check_compound_law, run_knockoff_gate


@pytest.fixture
def synthetic_with_signal():
    """n=200, p=6 genes; first 2 genes are signal-correlated with y."""
    rng = np.random.default_rng(seed=42)
    n, p = 200, 6
    y = rng.binomial(1, 0.25, n).astype(int)
    # Signal genes: correlated with y
    X_sig = rng.normal(loc=y[:, None] * 1.5, scale=1.0, size=(n, 2))
    # Null genes: independent of y
    X_null = rng.normal(0, 1.0, size=(n, p - 2))
    X = np.hstack([X_sig, X_null])
    # z-score standardize
    X = (X - X.mean(0)) / (X.std(0) + 1e-9)
    gene_names = [f"signal_{i}" for i in range(2)] + [f"null_{i}" for i in range(p - 2)]
    return X, y, gene_names


def test_returns_expected_keys(synthetic_with_signal):
    X, y, gene_names = synthetic_with_signal
    result = run_knockoff_gate(X, y, gene_names=gene_names, n_replicates=3, seed=0)
    expected = {"selected_genes", "selection_rates", "fdr_target", "n_replicates",
                "seed", "sigma_condition_number", "replicate_selections",
                "successful_replicates", "failed_replicates", "replicate_errors",
                "mean_W_statistic", "top_genes_by_W"}
    assert expected.issubset(result.keys())
    assert result["failed_replicates"] == 0
    assert result["successful_replicates"] == 3


def test_selection_rates_sum_to_valid_range(synthetic_with_signal):
    X, y, gene_names = synthetic_with_signal
    result = run_knockoff_gate(X, y, gene_names=gene_names, n_replicates=5, seed=0)
    for gene, rate in result["selection_rates"].items():
        assert 0.0 <= rate <= 1.0, f"Rate {rate} out of [0,1] for {gene}"


def test_replicate_count(synthetic_with_signal):
    X, y, gene_names = synthetic_with_signal
    n_rep = 4
    result = run_knockoff_gate(X, y, gene_names=gene_names, n_replicates=n_rep, seed=0)
    assert len(result["replicate_selections"]) == n_rep


def test_check_compound_law_all_selected():
    """Conjunction rule: all genes selected → law is selected."""
    mock_result = {
        "selection_rates": {"TOP2A": 0.80, "EPAS1": 0.60, "MKI67": 0.40}
    }
    check = check_compound_law(["TOP2A", "EPAS1"], mock_result, conjunction_threshold=0.50)
    assert check["law_genes_selected"] is True
    assert check["min_rate"] == pytest.approx(0.60)
    assert check["bottleneck_gene"] == "EPAS1"


def test_check_compound_law_partial_selection():
    """Conjunction rule: one gene below threshold → law NOT selected."""
    mock_result = {
        "selection_rates": {"TOP2A": 0.80, "EPAS1": 0.40, "MKI67": 0.40}
    }
    check = check_compound_law(["TOP2A", "EPAS1"], mock_result, conjunction_threshold=0.50)
    assert check["law_genes_selected"] is False
    assert check["bottleneck_gene"] == "EPAS1"


def test_check_compound_law_missing_gene():
    """Gene not in selection_rates → rate defaults to 0.0 → not selected."""
    mock_result = {"selection_rates": {"TOP2A": 0.80}}
    check = check_compound_law(["TOP2A", "UNKNOWN_GENE"], mock_result)
    assert check["law_genes_selected"] is False
    assert check["per_gene_rates"]["UNKNOWN_GENE"] == 0.0
