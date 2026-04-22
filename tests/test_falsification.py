from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import theory_copilot.falsification as falsification_module
from theory_copilot.falsification import (
    baseline_comparison,
    bootstrap_stability,
    confound_only,
    label_shuffle_null,
    passes_falsification,
    run_falsification_suite,
)


class FalsificationTests(unittest.TestCase):
    @staticmethod
    def _make_synthetic_data() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        rng = np.random.default_rng(1234)
        sample_count = 300
        y = np.array([0] * (sample_count // 2) + [1] * (sample_count // 2))
        latent_signal = (2 * y) - 1

        x1 = 1.2 * latent_signal + rng.normal(scale=1.5, size=sample_count)
        x2 = 1.2 * latent_signal + rng.normal(scale=1.5, size=sample_count)
        X = np.column_stack([x1, x2])

        covariate_1 = 0.35 * latent_signal + rng.normal(scale=1.4, size=sample_count)
        covariate_2 = rng.normal(scale=1.0, size=sample_count)
        X_covariates = np.column_stack([covariate_1, covariate_2])
        return X, X_covariates, y

    @staticmethod
    def _equation_fn(X: np.ndarray) -> np.ndarray:
        return X[:, 0] + X[:, 1]

    def test_label_shuffle_null_returns_small_p_for_strong_signal(self) -> None:
        X, _, y = self._make_synthetic_data()
        np.random.seed(0)

        p_value, original_auc = label_shuffle_null(X, y, self._equation_fn, n_permutations=200)

        self.assertLess(p_value, 0.05)
        self.assertGreater(original_auc, 0.90)

    def test_bootstrap_stability_returns_narrow_interval_for_stable_signal(self) -> None:
        X, _, y = self._make_synthetic_data()
        np.random.seed(1)

        ci_width, mean_auc = bootstrap_stability(X, y, self._equation_fn, n_resamples=200)

        self.assertLess(ci_width, 0.1)
        self.assertGreater(mean_auc, 0.90)

    def test_baseline_comparison_beats_best_single_feature(self) -> None:
        X, _, y = self._make_synthetic_data()

        delta, law_auc, baseline_auc = baseline_comparison(X, y, self._equation_fn)

        self.assertGreater(delta, 0.05)
        self.assertGreater(law_auc, baseline_auc)
        self.assertGreater(baseline_auc, 0.80)

    def test_confound_only_beats_covariate_model(self) -> None:
        X, X_covariates, y = self._make_synthetic_data()

        delta, law_auc, confound_auc = confound_only(X, X_covariates, y, self._equation_fn)

        self.assertGreater(delta, 0.03)
        self.assertGreater(law_auc, confound_auc)
        self.assertGreater(confound_auc, 0.55)

    def test_passes_falsification_applies_thresholds(self) -> None:
        self.assertTrue(passes_falsification(0.01, 0.05, 0.91, 0.80))
        self.assertTrue(passes_falsification(0.01, 0.05, 0.91, 0.80, confound_auc=0.84))
        self.assertFalse(passes_falsification(0.05, 0.05, 0.91, 0.80))
        self.assertFalse(passes_falsification(0.01, 0.10, 0.91, 0.80))
        self.assertFalse(passes_falsification(0.01, 0.05, 0.85, 0.80))
        self.assertFalse(passes_falsification(0.01, 0.05, 0.91, 0.80, confound_auc=0.89))

    def test_run_falsification_suite_without_covariates_sets_confound_fields_to_none(self) -> None:
        X, _, y = self._make_synthetic_data()
        with (
            patch.object(falsification_module, "label_shuffle_null", return_value=(0.01, 0.94)) as mock_perm,
            patch.object(falsification_module, "bootstrap_stability", return_value=(0.04, 0.93)) as mock_boot,
            patch.object(falsification_module, "baseline_comparison", return_value=(0.08, 0.94, 0.86)) as mock_baseline,
            patch.object(falsification_module, "confound_only") as mock_confound,
        ):
            summary = run_falsification_suite(self._equation_fn, X, y)

        self.assertTrue(summary["passes"])
        self.assertEqual(summary["perm_p"], 0.01)
        self.assertEqual(summary["original_auc"], 0.94)
        self.assertEqual(summary["ci_width"], 0.04)
        self.assertEqual(summary["mean_auc"], 0.93)
        self.assertEqual(summary["delta_baseline"], 0.08)
        self.assertEqual(summary["law_auc"], 0.94)
        self.assertEqual(summary["baseline_auc"], 0.86)
        self.assertIsNone(summary["delta_confound"])
        self.assertIsNone(summary["confound_auc"])
        mock_perm.assert_called_once_with(X, y, self._equation_fn)
        mock_boot.assert_called_once_with(X, y, self._equation_fn)
        mock_baseline.assert_called_once_with(X, y, self._equation_fn)
        mock_confound.assert_not_called()

    def test_run_falsification_suite_with_covariates_returns_full_summary(self) -> None:
        X, X_covariates, y = self._make_synthetic_data()
        with (
            patch.object(falsification_module, "label_shuffle_null", return_value=(0.01, 0.94)) as mock_perm,
            patch.object(falsification_module, "bootstrap_stability", return_value=(0.04, 0.93)) as mock_boot,
            patch.object(falsification_module, "baseline_comparison", return_value=(0.08, 0.94, 0.86)) as mock_baseline,
            patch.object(falsification_module, "confound_only", return_value=(0.12, 0.94, 0.82)) as mock_confound,
        ):
            summary = run_falsification_suite(self._equation_fn, X, y, X_covariates=X_covariates)

        self.assertTrue(summary["passes"])
        self.assertEqual(summary["perm_p"], 0.01)
        self.assertEqual(summary["original_auc"], 0.94)
        self.assertEqual(summary["ci_width"], 0.04)
        self.assertEqual(summary["mean_auc"], 0.93)
        self.assertEqual(summary["delta_baseline"], 0.08)
        self.assertEqual(summary["delta_confound"], 0.12)
        self.assertEqual(summary["law_auc"], 0.94)
        self.assertEqual(summary["baseline_auc"], 0.86)
        self.assertEqual(summary["confound_auc"], 0.82)
        mock_perm.assert_called_once_with(X, y, self._equation_fn)
        mock_boot.assert_called_once_with(X, y, self._equation_fn)
        mock_baseline.assert_called_once_with(X, y, self._equation_fn)
        mock_confound.assert_called_once_with(X, X_covariates, y, self._equation_fn)
