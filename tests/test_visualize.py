import matplotlib
matplotlib.use("Agg")

import numpy as np
import pytest

from theory_copilot.visualize import plot_falsification_panel, plot_separation


def test_plot_separation_creates_file(tmp_path):
    rng = np.random.default_rng(42)
    disease_scores = rng.standard_normal(50) + 1.0
    control_scores = rng.standard_normal(50)
    scores = np.concatenate([disease_scores, control_scores])
    labels = np.array([1] * 50 + [0] * 50)
    out = tmp_path / "separation.png"

    result = plot_separation(scores, labels, "log(A) + B*C", str(out))

    assert result == out
    assert out.exists()
    assert out.stat().st_size > 0


def test_plot_separation_long_title(tmp_path):
    rng = np.random.default_rng(0)
    scores = rng.standard_normal(40)
    labels = np.array([1] * 20 + [0] * 20)
    long_eq = "x" * 80
    out = tmp_path / "long_title.png"

    result = plot_separation(scores, labels, long_eq, out)

    assert out.exists()
    assert out.stat().st_size > 0


def test_plot_falsification_panel_creates_file(tmp_path):
    candidates = [
        {"name": "eq_A", "law_auc": 0.85, "passes": True, "fail_reason": ""},
        {"name": "eq_B", "law_auc": 0.78, "passes": True, "fail_reason": ""},
        {"name": "eq_C", "law_auc": 0.55, "passes": False, "fail_reason": "unstable bootstrap"},
        {"name": "eq_D", "law_auc": 0.48, "passes": False, "fail_reason": "low AUROC"},
    ]
    out = tmp_path / "panel.png"

    result = plot_falsification_panel(candidates, out)

    assert result == out
    assert out.exists()
    assert out.stat().st_size > 0
