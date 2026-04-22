from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score


def _auc_sign_invariant(y, scores) -> float:
    a = float(roc_auc_score(y, scores))
    return max(a, 1.0 - a)


def label_shuffle_null(X, y, equation_fn, n_permutations=1000) -> tuple[float, float]:
    """Two-sided permutation test on AUROC.

    The law direction is arbitrary (PySR may return a sign-flipped winner),
    so a one-sided test would miss genuinely predictive but inverted laws.
    """
    X = np.asarray(X)
    if X.ndim == 1:
        X = X[:, np.newaxis]
    y = np.asarray(y)
    scores = np.asarray(equation_fn(X)).reshape(-1)
    original_auc = float(roc_auc_score(y, scores))
    observed_dist = abs(original_auc - 0.5)

    null_dists = np.empty(int(n_permutations), dtype=float)
    for index in range(int(n_permutations)):
        null_auc = roc_auc_score(np.random.permutation(y), scores)
        null_dists[index] = abs(null_auc - 0.5)

    p_value = float(np.mean(null_dists >= observed_dist))
    return p_value, original_auc


def bootstrap_stability(X, y, equation_fn, n_resamples=1000) -> tuple[float, float, float]:
    """Returns (ci_width, ci_lower, mean_auc).

    ci_lower is the primary cohort-size-invariant stability metric
    (lower bound of 95% percentile CI on AUROC).
    """
    X = np.asarray(X)
    if X.ndim == 1:
        X = X[:, np.newaxis]
    y = np.asarray(y)

    aucs: list[float] = []
    sample_count = y.shape[0]
    while len(aucs) < int(n_resamples):
        sample_index = np.random.choice(sample_count, size=sample_count, replace=True)
        y_sample = y[sample_index]
        if np.unique(y_sample).size < 2:
            continue
        scores = np.asarray(equation_fn(X[sample_index])).reshape(-1)
        aucs.append(float(roc_auc_score(y_sample, scores)))

    auc_array = np.asarray(aucs, dtype=float)
    lower, upper = np.percentile(auc_array, [2.5, 97.5])
    return float(upper - lower), float(lower), float(auc_array.mean())


def baseline_comparison(X, y, equation_fn) -> tuple[float, float, float]:
    """Best sign-invariant single-feature baseline.

    A feature that is negatively correlated with y still provides a valid
    single-feature classifier with AUROC = 1 - raw_auc. Ignoring the sign
    inflates the perceived advantage of the law over baselines.
    """
    X = np.asarray(X)
    if X.ndim == 1:
        X = X[:, np.newaxis]
    y = np.asarray(y)

    law_scores = np.asarray(equation_fn(X)).reshape(-1)
    law_auc = float(roc_auc_score(y, law_scores))
    baseline_auc = float(
        max(_auc_sign_invariant(y, X[:, i]) for i in range(X.shape[1]))
    )
    return law_auc - baseline_auc, law_auc, baseline_auc


def confound_only(X_biological, X_covariates, y, equation_fn) -> tuple[float, float, float]:
    """Incremental AUC of the law beyond covariates.

    Returns (incremental_delta, law_auc, confound_auc) where
    incremental_delta = AUROC(LR(cov + law_score)) - AUROC(LR(cov)).
    Both models fit on the same data so in-sample optimism cancels in the delta.
    """
    X_biological = np.asarray(X_biological)
    if X_biological.ndim == 1:
        X_biological = X_biological[:, np.newaxis]
    X_covariates = np.asarray(X_covariates)
    if X_covariates.ndim == 1:
        X_covariates = X_covariates[:, np.newaxis]
    y = np.asarray(y)

    law_scores = np.asarray(equation_fn(X_biological)).reshape(-1, 1)
    law_auc = float(roc_auc_score(y, law_scores.ravel()))

    lr_cov = LogisticRegression(max_iter=1000).fit(X_covariates, y)
    confound_auc = float(roc_auc_score(y, lr_cov.predict_proba(X_covariates)[:, 1]))

    X_combined = np.hstack([X_covariates, law_scores])
    lr_combined = LogisticRegression(max_iter=1000).fit(X_combined, y)
    combined_auc = float(roc_auc_score(y, lr_combined.predict_proba(X_combined)[:, 1]))

    return combined_auc - confound_auc, law_auc, confound_auc


def decoy_feature_test(
    X, y, equation_fn, n_decoys: int = 100, seed: int = 0
) -> tuple[float, float, float]:
    """Compare law AUROC to a null distribution of random-feature AUROCs.

    Borrows the decoy-injection idea from the Nomos Phase-3 null model.
    Returns (decoy_p, decoy_q95, law_auc). A small decoy_p means the law
    outperforms essentially all random linear features of matched scale.
    """
    rng = np.random.default_rng(seed)
    X = np.asarray(X)
    if X.ndim == 1:
        X = X[:, np.newaxis]
    y = np.asarray(y)

    law_scores = np.asarray(equation_fn(X)).reshape(-1)
    law_auc = float(roc_auc_score(y, law_scores))

    decoy_aucs = np.empty(int(n_decoys), dtype=float)
    law_std = float(np.std(law_scores)) or 1.0
    for i in range(int(n_decoys)):
        noise = rng.normal(loc=0.0, scale=law_std, size=y.shape[0])
        decoy_aucs[i] = _auc_sign_invariant(y, noise)

    p_value = float(np.mean(decoy_aucs >= law_auc))
    q95 = float(np.quantile(decoy_aucs, 0.95))
    return p_value, q95, law_auc


def passes_falsification(
    perm_p,
    ci_lower,
    law_auc,
    baseline_auc,
    confound_delta=None,
    decoy_p=None,
) -> bool:
    passes = (
        perm_p < 0.05
        and ci_lower > 0.6
        and (law_auc - baseline_auc) > 0.05
    )
    if confound_delta is not None:
        passes = passes and confound_delta > 0.03
    if decoy_p is not None:
        passes = passes and decoy_p < 0.05
    return bool(passes)


def run_falsification_suite(equation_fn, X, y, X_covariates=None, include_decoy=True) -> dict:
    perm_p, original_auc = label_shuffle_null(X, y, equation_fn)
    ci_width, ci_lower, mean_auc = bootstrap_stability(X, y, equation_fn)
    delta_baseline, law_auc, baseline_auc = baseline_comparison(X, y, equation_fn)

    confound_delta = None
    confound_auc = None
    if X_covariates is not None:
        confound_delta, law_auc, confound_auc = confound_only(X, X_covariates, y, equation_fn)

    decoy_p = None
    decoy_q95 = None
    if include_decoy:
        decoy_p, decoy_q95, law_auc = decoy_feature_test(X, y, equation_fn)

    return {
        "passes": passes_falsification(
            perm_p, ci_lower, law_auc, baseline_auc, confound_delta, decoy_p
        ),
        "perm_p": perm_p,
        "original_auc": original_auc,
        "ci_width": ci_width,
        "ci_lower": ci_lower,
        "mean_auc": mean_auc,
        "delta_baseline": delta_baseline,
        "law_auc": law_auc,
        "baseline_auc": baseline_auc,
        "delta_confound": confound_delta,
        "confound_auc": confound_auc,
        "decoy_p": decoy_p,
        "decoy_q95": decoy_q95,
    }
