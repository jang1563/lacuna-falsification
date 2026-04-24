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
    decoy_feature_test,
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

    def test_label_shuffle_null_two_sided_small_p_for_strong_signal(self) -> None:
        X, _, y = self._make_synthetic_data()
        np.random.seed(0)
        p_value, original_auc = label_shuffle_null(X, y, self._equation_fn, n_permutations=200)
        self.assertLess(p_value, 0.05)
        self.assertGreater(original_auc, 0.90)

    def test_label_shuffle_null_two_sided_catches_inverted_signal(self) -> None:
        """A sign-flipped equation should still register small two-sided p
        AND report a sign-invariant AUROC > 0.5 (post-2026-04-23 fix:
        label_shuffle_null returns sign-invariant `max(auc, 1-auc)` so the
        gate cannot reject mathematically equivalent sign-flipped laws).
        """
        X, _, y = self._make_synthetic_data()
        inverted = lambda arr: -(arr[:, 0] + arr[:, 1])
        p_value, auc_sign_inv = label_shuffle_null(
            X, y, inverted, n_permutations=200, seed=0
        )
        self.assertLess(p_value, 0.05)
        self.assertGreater(auc_sign_inv, 0.9)  # sign-invariant view of strong inverted signal

    def test_bootstrap_stability_returns_width_lower_mean(self) -> None:
        X, _, y = self._make_synthetic_data()
        np.random.seed(1)
        ci_width, ci_lower, mean_auc = bootstrap_stability(X, y, self._equation_fn, n_resamples=200)
        self.assertLess(ci_width, 0.1)
        self.assertGreater(ci_lower, 0.85)
        self.assertGreater(mean_auc, 0.90)

    def test_baseline_comparison_sign_invariant(self) -> None:
        X, _, y = self._make_synthetic_data()
        # Invert one feature. Sign-invariant baseline should still recognize it.
        X_flipped = X.copy()
        X_flipped[:, 0] = -X_flipped[:, 0]
        delta, law_auc, baseline_auc = baseline_comparison(
            X_flipped, y, lambda a: a[:, 0] + a[:, 1]
        )
        # baseline_auc reflects the stronger single feature (>= 0.80) not the raw AUC.
        self.assertGreater(baseline_auc, 0.80)
        self.assertGreater(law_auc, 0.5)

    def test_confound_only_incremental_delta(self) -> None:
        X, X_covariates, y = self._make_synthetic_data()
        delta, law_auc, confound_auc = confound_only(X, X_covariates, y, self._equation_fn)
        # Incremental delta: combined (cov + law) − covariates only.
        self.assertGreater(delta, 0.03)
        self.assertGreater(law_auc, confound_auc)
        self.assertGreater(confound_auc, 0.55)

    def test_decoy_feature_test_rejects_random_noise(self) -> None:
        X, _, y = self._make_synthetic_data()
        np.random.seed(2)
        decoy_p, q95, law_auc = decoy_feature_test(X, y, self._equation_fn, n_decoys=50, seed=2)
        self.assertLess(decoy_p, 0.05)
        self.assertGreater(law_auc, q95)

    def test_passes_falsification_applies_thresholds(self) -> None:
        # (perm_p, ci_lower, law_auc, baseline_auc, confound_delta=None, decoy_p=None)
        self.assertTrue(passes_falsification(0.01, 0.85, 0.91, 0.80))
        self.assertTrue(passes_falsification(0.01, 0.85, 0.91, 0.80, confound_delta=0.05))
        self.assertTrue(
            passes_falsification(0.01, 0.85, 0.91, 0.80, confound_delta=0.05, decoy_p=0.001)
        )
        self.assertFalse(passes_falsification(0.05, 0.85, 0.91, 0.80))  # perm_p boundary
        self.assertFalse(passes_falsification(0.01, 0.55, 0.91, 0.80))  # ci_lower too low
        self.assertFalse(passes_falsification(0.01, 0.85, 0.85, 0.80))  # delta_baseline too small
        self.assertFalse(passes_falsification(0.01, 0.85, 0.91, 0.80, confound_delta=0.02))
        self.assertFalse(
            passes_falsification(0.01, 0.85, 0.91, 0.80, confound_delta=0.05, decoy_p=0.10)
        )

    def test_run_falsification_suite_without_covariates(self) -> None:
        X, _, y = self._make_synthetic_data()
        with (
            patch.object(falsification_module, "label_shuffle_null", return_value=(0.01, 0.94)),
            patch.object(falsification_module, "bootstrap_stability", return_value=(0.04, 0.88, 0.93)),
            patch.object(falsification_module, "baseline_comparison", return_value=(0.08, 0.94, 0.86)),
            patch.object(falsification_module, "confound_only") as mock_confound,
            patch.object(falsification_module, "decoy_feature_test", return_value=(0.01, 0.65, 0.94)),
        ):
            summary = run_falsification_suite(self._equation_fn, X, y)

        self.assertTrue(summary["passes"])
        self.assertEqual(summary["perm_p"], 0.01)
        self.assertEqual(summary["ci_lower"], 0.88)
        self.assertEqual(summary["delta_baseline"], 0.08)
        self.assertEqual(summary["law_auc"], 0.94)
        self.assertIsNone(summary["delta_confound"])
        self.assertEqual(summary["decoy_p"], 0.01)
        mock_confound.assert_not_called()

    def test_run_falsification_suite_with_covariates_full_output(self) -> None:
        X, X_covariates, y = self._make_synthetic_data()
        with (
            patch.object(falsification_module, "label_shuffle_null", return_value=(0.01, 0.94)),
            patch.object(falsification_module, "bootstrap_stability", return_value=(0.04, 0.88, 0.93)),
            patch.object(falsification_module, "baseline_comparison", return_value=(0.08, 0.94, 0.86)),
            patch.object(falsification_module, "confound_only", return_value=(0.12, 0.94, 0.82)),
            patch.object(falsification_module, "decoy_feature_test", return_value=(0.01, 0.65, 0.94)),
        ):
            summary = run_falsification_suite(self._equation_fn, X, y, X_covariates=X_covariates)

        self.assertTrue(summary["passes"])
        self.assertEqual(summary["delta_confound"], 0.12)
        self.assertEqual(summary["confound_auc"], 0.82)
        self.assertEqual(summary["decoy_p"], 0.01)

    def test_run_falsification_suite_skip_decoy(self) -> None:
        X, _, y = self._make_synthetic_data()
        summary = run_falsification_suite(
            self._equation_fn, X, y, include_decoy=False
        )
        self.assertIsNone(summary["decoy_p"])
