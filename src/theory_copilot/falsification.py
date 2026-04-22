from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score


def label_shuffle_null(X, y, equation_fn, n_permutations=1000) -> tuple[float, float]:
    X = np.asarray(X)
    if X.ndim == 1:
        X = X[:, np.newaxis]
    y = np.asarray(y)
    scores = np.asarray(equation_fn(X)).reshape(-1)
    original_auc = float(roc_auc_score(y, scores))

    null_aucs = np.empty(int(n_permutations), dtype=float)
    for index in range(int(n_permutations)):
        null_aucs[index] = roc_auc_score(np.random.permutation(y), scores)

    return float(np.mean(null_aucs >= original_auc)), original_auc


def bootstrap_stability(X, y, equation_fn, n_resamples=1000) -> tuple[float, float]:
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
    return float(upper - lower), float(auc_array.mean())


def baseline_comparison(X, y, equation_fn) -> tuple[float, float, float]:
    X = np.asarray(X)
    if X.ndim == 1:
        X = X[:, np.newaxis]
    y = np.asarray(y)

    law_scores = np.asarray(equation_fn(X)).reshape(-1)
    law_auc = float(roc_auc_score(y, law_scores))
    baseline_auc = float(max(roc_auc_score(y, X[:, index]) for index in range(X.shape[1])))
    return law_auc - baseline_auc, law_auc, baseline_auc


def confound_only(X_biological, X_covariates, y, equation_fn) -> tuple[float, float, float]:
    X_biological = np.asarray(X_biological)
    if X_biological.ndim == 1:
        X_biological = X_biological[:, np.newaxis]
    X_covariates = np.asarray(X_covariates)
    if X_covariates.ndim == 1:
        X_covariates = X_covariates[:, np.newaxis]
    y = np.asarray(y)

    law_scores = np.asarray(equation_fn(X_biological)).reshape(-1)
    law_auc = float(roc_auc_score(y, law_scores))
    model = LogisticRegression(max_iter=1000)
    model.fit(X_covariates, y)
    confound_auc = float(roc_auc_score(y, model.predict_proba(X_covariates)[:, 1]))
    return law_auc - confound_auc, law_auc, confound_auc


def passes_falsification(perm_p, boot_ci_width, law_auc, baseline_auc, confound_auc=None) -> bool:
    passes = perm_p < 0.05 and boot_ci_width < 0.1 and (law_auc - baseline_auc) > 0.05
    if confound_auc is not None:
        passes = passes and (law_auc - confound_auc) > 0.03
    return passes


def run_falsification_suite(equation_fn, X, y, X_covariates=None) -> dict:
    perm_p, original_auc = label_shuffle_null(X, y, equation_fn)
    ci_width, mean_auc = bootstrap_stability(X, y, equation_fn)
    delta_baseline, law_auc, baseline_auc = baseline_comparison(X, y, equation_fn)

    delta_confound = None
    confound_auc = None
    if X_covariates is not None:
        delta_confound, law_auc, confound_auc = confound_only(X, X_covariates, y, equation_fn)

    return {
        "passes": passes_falsification(perm_p, ci_width, law_auc, baseline_auc, confound_auc),
        "perm_p": perm_p,
        "original_auc": original_auc,
        "ci_width": ci_width,
        "mean_auc": mean_auc,
        "delta_baseline": delta_baseline,
        "law_auc": law_auc,
        "baseline_auc": baseline_auc,
        "delta_confound": delta_confound,
        "confound_auc": confound_auc,
    }
