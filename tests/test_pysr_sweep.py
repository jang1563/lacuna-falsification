from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

# Load pysr_sweep via importlib.util with a pysr mock pre-installed.

_SRC_PATH = Path(__file__).resolve().parents[1] / "src" / "pysr_sweep.py"

_pysr_mock = MagicMock()
_pysr_mock.PySRRegressor = MagicMock()
sys.modules.setdefault("pysr", _pysr_mock)

spec = importlib.util.spec_from_file_location("pysr_sweep", str(_SRC_PATH))
pysr_sweep = importlib.util.module_from_spec(spec)
sys.modules["pysr_sweep"] = pysr_sweep
spec.loader.exec_module(pysr_sweep)  # type: ignore[union-attr]


def _make_csv(tmp_path: Path) -> Path:
    rng = np.random.default_rng(42)
    n = 60
    df = pd.DataFrame(
        {
            "CA9": rng.random(n),
            "VEGFA": rng.random(n),
            "LDHA": rng.random(n),
            "AGXT": rng.random(n),
            "label": ["tumor"] * 30 + ["normal"] * 30,
        }
    )
    p = tmp_path / "test_data.csv"
    df.to_csv(p, index=False)
    return p


def _make_model_mock(n_eq: int = 5) -> MagicMock:
    equations_df = pd.DataFrame(
        {
            "equation": [f"x{i}" for i in range(n_eq)],
            "score": np.linspace(0.1, 1.0, n_eq),
            "complexity": list(range(1, n_eq + 1)),
        }
    )
    model = MagicMock()
    model.equations_ = equations_df
    rng = np.random.default_rng(0)
    # Return predict output sized to the input matrix (train and test both).
    model.predict.side_effect = lambda X, index=None: rng.random(X.shape[0])
    return model


class TestPysrSweep:
    def test_output_json_exists_and_is_list(self, tmp_path: Path) -> None:
        csv_path = _make_csv(tmp_path)
        output_path = tmp_path / "candidates.json"

        mock_pysr = MagicMock()
        mock_pysr.PySRRegressor.return_value = _make_model_mock()

        with patch("pysr_sweep.pysr", mock_pysr), patch("pysr_sweep.PYSR_AVAILABLE", True):
            pysr_sweep.main(
                [
                    "--data", str(csv_path),
                    "--genes", "CA9,VEGFA,LDHA,AGXT",
                    "--seeds", "1",
                    "--n-populations", "2",
                    "--population-size", "10",
                    "--iterations", "5",
                    "--test-size", "0.3",
                    "--output", str(output_path),
                ]
            )

        assert output_path.exists()
        result = json.loads(output_path.read_text())
        assert isinstance(result, list)

    def test_output_items_have_required_keys(self, tmp_path: Path) -> None:
        csv_path = _make_csv(tmp_path)
        output_path = tmp_path / "candidates.json"

        mock_pysr = MagicMock()
        mock_pysr.PySRRegressor.return_value = _make_model_mock()

        with patch("pysr_sweep.pysr", mock_pysr), patch("pysr_sweep.PYSR_AVAILABLE", True):
            pysr_sweep.main(
                [
                    "--data", str(csv_path),
                    "--genes", "CA9,VEGFA",
                    "--seeds", "1",
                    "--output", str(output_path),
                ]
            )

        result = json.loads(output_path.read_text())
        if result:
            required = {
                "equation", "auroc", "train_auroc", "test_auroc",
                "complexity", "seed", "law_family", "novelty",
            }
            assert required <= result[0].keys()

    def test_multiple_seeds_deduplicated(self, tmp_path: Path) -> None:
        csv_path = _make_csv(tmp_path)
        output_path = tmp_path / "multi_seed.json"

        mock_pysr = MagicMock()
        mock_pysr.PySRRegressor.return_value = _make_model_mock()

        with patch("pysr_sweep.pysr", mock_pysr), patch("pysr_sweep.PYSR_AVAILABLE", True):
            pysr_sweep.main(
                [
                    "--data", str(csv_path),
                    "--genes", "CA9,VEGFA,LDHA,AGXT",
                    "--seeds", "1", "2", "3",
                    "--output", str(output_path),
                ]
            )

        result = json.loads(output_path.read_text())
        equations = [r["equation"] for r in result]
        assert len(equations) == len(set(equations))

    def test_variable_names_passed_to_pysr(self, tmp_path: Path) -> None:
        csv_path = _make_csv(tmp_path)
        output_path = tmp_path / "vars.json"

        mock_pysr = MagicMock()
        mock_pysr.PySRRegressor.return_value = _make_model_mock()

        with patch("pysr_sweep.pysr", mock_pysr), patch("pysr_sweep.PYSR_AVAILABLE", True):
            pysr_sweep.main(
                [
                    "--data", str(csv_path),
                    "--genes", "CA9,VEGFA",
                    "--seeds", "1",
                    "--output", str(output_path),
                ]
            )

        _, kwargs = mock_pysr.PySRRegressor.call_args
        assert kwargs.get("variable_names") == ["CA9", "VEGFA"]

    def test_import_error_writes_empty_list_and_exits_0(self, tmp_path: Path) -> None:
        csv_path = _make_csv(tmp_path)
        output_path = tmp_path / "empty.json"

        with patch("pysr_sweep.PYSR_AVAILABLE", False):
            with pytest.raises(SystemExit) as exc_info:
                pysr_sweep.main(
                    [
                        "--data", str(csv_path),
                        "--genes", "CA9",
                        "--seeds", "1",
                        "--output", str(output_path),
                    ]
                )

        assert exc_info.value.code == 0
        assert output_path.exists()
        result = json.loads(output_path.read_text())
        assert result == []

    def test_novelty_score_matches_guess_returns_zero(self) -> None:
        proposals = [
            {"initial_guess": "log1p(CA9) + log1p(VEGFA)"},
            {"initial_guess": "log1p(LDHA)"},
        ]
        # Same string (whitespace normalised) should score 0.
        assert pysr_sweep._novelty_score("log1p(CA9) + log1p(VEGFA)", proposals) == 0.0
        # Different expression should score > 0.
        assert pysr_sweep._novelty_score("log1p(AGXT) * log1p(ALB)", proposals) > 0.0
