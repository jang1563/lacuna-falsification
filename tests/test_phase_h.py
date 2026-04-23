"""Phase H smoke tests — H1 (SR Loop) and H2 (1M Synthesis)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))


# ---------------------------------------------------------------------------
# H1 — falsification_sr_loop
# ---------------------------------------------------------------------------

class TestDoomLoopDetector:
    def test_no_doom_below_window(self):
        from falsification_sr_loop import DoomLoopDetector
        d = DoomLoopDetector(window=3, threshold=0.7)
        d.add("TOP2A - EPAS1")
        d.add("TOP2A + EPAS1")
        assert not d.is_doom_loop()

    def test_doom_detected_on_identical_skeletons(self):
        from falsification_sr_loop import DoomLoopDetector
        d = DoomLoopDetector(window=3, threshold=0.7)
        for _ in range(3):
            d.add("TOP2A - EPAS1")
        assert d.is_doom_loop()

    def test_redirect_picks_least_used(self):
        from falsification_sr_loop import DoomLoopDetector, PATHWAY_GROUPS
        from collections import Counter
        d = DoomLoopDetector()
        usage: Counter = Counter({"HIF": 5, "Warburg": 3})
        redirect = d.force_redirect(usage)
        assert isinstance(redirect, str) and len(redirect) > 0


class TestEquationFn:
    def test_top2a_minus_epas1(self):
        from falsification_sr_loop import make_equation_fn
        genes = ["TOP2A", "EPAS1", "CA9"]
        fn = make_equation_fn("TOP2A - EPAS1", genes)
        X = np.array([[1.0, 0.5, 0.3], [0.2, 0.8, 0.9]])
        scores = fn(X)
        assert scores.shape == (2,)
        assert abs(scores[0] - 0.5) < 1e-6  # 1.0 - 0.5
        assert abs(scores[1] - (-0.6)) < 1e-6  # 0.2 - 0.8

    def test_sigmoid_in_skeleton(self):
        from falsification_sr_loop import make_equation_fn
        genes = ["CA9"]
        fn = make_equation_fn("sigmoid(CA9)", genes)
        X = np.zeros((5, 1))
        scores = fn(X)
        # sigmoid(0) = 0.5
        assert np.allclose(scores, 0.5, atol=1e-5)

    def test_constant_broadcast(self):
        from falsification_sr_loop import make_equation_fn
        genes = ["CA9"]
        fn = make_equation_fn("1.0", genes)
        X = np.zeros((10, 1))
        scores = fn(X)
        assert scores.shape == (10,)


class TestLoadDataset:
    def test_loads_expanded(self):
        from falsification_sr_loop import load_dataset
        repo = Path(__file__).parents[1]
        csv = repo / "data" / "kirc_metastasis_expanded.csv"
        if not csv.exists():
            pytest.skip("expanded dataset not available")
        X, y, genes = load_dataset(str(csv))
        assert X.shape[0] == y.shape[0]
        assert len(genes) >= 40
        assert set(np.unique(y)) == {0, 1}


class TestSrLoop:
    def test_loop_runs_without_pysr(self):
        """Full loop with mock gate — validates flow without PySR or API."""
        import falsification_sr_loop as m
        orig_pysr = m._PYSR_AVAILABLE
        orig_gate = m.gate_candidate

        m._PYSR_AVAILABLE = False

        def _fast_gate(eq, X, y, gene_cols):
            # First skeleton passes; rest fail
            if "TOP2A" in eq and "EPAS1" in eq:
                return {"equation": eq, "passes": True, "fail_reason": "",
                        "law_auc": 0.726, "baseline_auc": 0.657,
                        "delta_baseline": 0.069, "perm_p": 0.001,
                        "ci_lower": 0.665, "ci_width": 0.06,
                        "delta_confound": None, "decoy_p": 0.001}
            return {"equation": eq, "passes": False, "fail_reason": "delta_baseline",
                    "law_auc": 0.69, "baseline_auc": 0.66, "delta_baseline": 0.03,
                    "perm_p": 0.01, "ci_lower": 0.63, "ci_width": 0.09,
                    "delta_confound": None, "decoy_p": 0.01}

        m.gate_candidate = _fast_gate

        try:
            repo = Path(__file__).parents[1]
            csv = repo / "data" / "kirc_metastasis_expanded.csv"
            if not csv.exists():
                pytest.skip("expanded dataset not available")

            result = m.run_falsification_sr_loop(
                csv_path=str(csv),
                max_iterations=2,
                pysr_iterations=5,
                use_opus=False,
                output_path=None,
            )
            assert result["total_iterations"] == 2
            assert result["total_candidates"] >= 2
            # At least iteration structure is there
            assert len(result["iterations"]) == 2
        finally:
            m._PYSR_AVAILABLE = orig_pysr
            m.gate_candidate = orig_gate


# ---------------------------------------------------------------------------
# H2 — opus_1m_synthesis
# ---------------------------------------------------------------------------

class TestSynthesisDataLoad:
    def test_load_rejections(self):
        from opus_1m_synthesis import load_all_rejections_and_survivors
        repo = Path(__file__).parents[1]
        rejections, survivors = load_all_rejections_and_survivors(repo)
        assert isinstance(rejections, list)
        assert isinstance(survivors, list)
        assert len(rejections) > 0, "Expected rejection records"

    def test_build_prompt(self):
        from opus_1m_synthesis import (
            load_all_rejections_and_survivors, build_1m_prompt, PAPER_ABSTRACTS
        )
        repo = Path(__file__).parents[1]
        rejections, survivors = load_all_rejections_and_survivors(repo)
        prompt = build_1m_prompt(rejections[:5], survivors[:3], PAPER_ABSTRACTS[:2])
        assert len(prompt) > 100
        assert "REJECTED" in prompt or "rejection" in prompt.lower()
        assert "SURVIVOR" in prompt or "survivor" in prompt.lower()

    def test_dry_run(self, tmp_path):
        from opus_1m_synthesis import load_all_rejections_and_survivors, build_1m_prompt, PAPER_ABSTRACTS, call_opus_1m
        repo = Path(__file__).parents[1]
        rejections, survivors = load_all_rejections_and_survivors(repo)
        prompt = build_1m_prompt(rejections, survivors, PAPER_ABSTRACTS)
        result = call_opus_1m(prompt, dry_run=True)
        assert result.get("_dry_run") is True
