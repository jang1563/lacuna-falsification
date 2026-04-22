from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Load pysr_sweep via importlib.util with a pysr mock pre-installed so the
# try/except at module level resolves PYSR_AVAILABLE = True.
# ---------------------------------------------------------------------------

_SRC_PATH = Path(__file__).resolve().parents[1] / "src" / "pysr_sweep.py"

_pysr_mock = MagicMock()
sys.modules.setdefault("pysr", _pysr_mock)

spec = importlib.util.spec_from_file_location("pysr_sweep", str(_SRC_PATH))
pysr_sweep = importlib.util.module_from_spec(spec)
sys.modules["pysr_sweep"] = pysr_sweep
spec.loader.exec_module(pysr_sweep)  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_csv(tmp_path: Path) -> Path:
    rng = np.random.default_rng(42)
    n = 50
    df = pd.DataFrame(
        {
            "CA9": rng.random(n),
            "VEGFA": rng.random(n),
            "LDHA": rng.random(n),
            "AGXT": rng.random(n),
            "label": ["tumor"] * 25 + ["normal"] * 25,
        }
    )
    p = tmp_path / "test_data.csv"
    df.to_csv(p, index=False)
    return p


def _make_model_mock(n_rows: int = 50, n_eq: int = 5) -> MagicMock:
    equations_df = pd.DataFrame(
        {
            "equation": [f"x{i}" for i in range(n_eq)],
            "score": np.linspace(0.1, 1.0, n_eq),
            "complexity": list(range(1, n_eq + 1)),
        }
    )
    model = MagicMock()
    model.equations_ = equations_df
    # predict returns values spread enough that roc_auc_score doesn't fail
    rng = np.random.default_rng(0)
    model.predict.return_value = rng.random(n_rows)
    return model


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

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
            required = {"equation", "auroc", "complexity", "seed", "law_family"}
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
        assert isinstance(result, list)
        equations = [r["equation"] for r in result]
        # deduplication: no duplicate equation strings
        assert len(equations) == len(set(equations))

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
