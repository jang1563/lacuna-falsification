"""G1 knockoff v2 gate — Model-X Knockoffs for FDR-controlled feature selection.

Runs ALONGSIDE the v1 5-test gate (reporting-only, gate logic unchanged).
Pre-registered in preregistrations/20260425T170647Z_g1_knockoff_v2.yaml
before any data interaction.

Design:
- LedoitWolf shrinkage covariance (handles n < p gene panels)
- MVR knockoff construction (minimum variance reconstructability)
- lcd feature statistic (log-contrast, best for binary y)
- FDR target q = 0.10
- 25 seeded replicates for derandomization (Ren & Candès 2020)
- Conjunction rule for compound features: ALL genes must be selected
  in >= 50% of replicates

References:
  Barber & Candès 2015, arXiv:1404.5609
  Bates et al. 2020, arXiv:2006.14342
  Ren & Candès 2020, arXiv:2012.11286
"""
from __future__ import annotations

import warnings

import numpy as np
from sklearn.covariance import LedoitWolf


def _estimate_sigma(X: np.ndarray) -> np.ndarray:
    """Shrinkage covariance estimate robust to near-singular gene panels."""
    lw = LedoitWolf(assume_centered=False)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        lw.fit(X)
    return lw.covariance_


def run_knockoff_gate(
    X: np.ndarray,
    y: np.ndarray,
    gene_names: list[str] | None = None,
    fdr_target: float = 0.10,
    n_replicates: int = 25,
    seed: int = 0,
    verbose: bool = False,
) -> dict:
    """Run Model-X Knockoff filter with derandomization.

    Parameters
    ----------
    X : (n, p) array — gene expression, z-score standardized
    y : (n,) array — binary outcome (0/1)
    gene_names : list of p strings — column names for X
    fdr_target : FDR q-level (pre-registered q=0.10)
    n_replicates : number of knockoff realizations (pre-registered 25)
    seed : base RNG seed; replicate r uses seed+r
    verbose : print replicate progress

    Returns
    -------
    dict with keys:
      - selected_genes: list of gene names selected in >= 50% of replicates
      - selection_rates: dict {gene: rate} for all genes
      - fdr_target, n_replicates, seed
      - sigma_condition_number: diagnostic for Sigma quality
      - replicate_selections: list of sets (one per replicate)
      - mean_W_statistic: dict {gene: mean W across replicates}
      - top_genes_by_W: list of {gene, mean_W} sorted descending
    """
    try:
        import knockpy
    except ImportError as e:
        raise ImportError(
            "knockpy is required for the G1 gate. "
            "Install with: pip install 'knockpy[fast]'"
        ) from e

    X = np.asarray(X, dtype=float)
    y = np.asarray(y).astype(int).reshape(-1)
    n, p = X.shape

    if gene_names is None:
        gene_names = [f"gene_{i}" for i in range(p)]
    assert len(gene_names) == p, f"gene_names length {len(gene_names)} != p={p}"

    Sigma = _estimate_sigma(X)
    cond = float(np.linalg.cond(Sigma))
    if verbose:
        print(f"  Sigma condition number: {cond:.1f}")

    replicate_selections: list[set[str]] = []
    replicate_errors: list[dict] = []
    selection_counts = np.zeros(p, dtype=int)
    # Per-replicate W statistics — needed to verify the knockoff filter
    # ranks signal genes correctly even when none cross the q-threshold
    # (Barber & Candès 2015; relevant when selection rate is 0).
    W_per_replicate: list[np.ndarray] = []

    for rep in range(n_replicates):
        rep_seed = seed + rep
        try:
            kf = knockpy.KnockoffFilter(
                ksampler="gaussian",
                fstat="lcd",
            )
            # knockpy 1.3.x uses the legacy global NumPy RNG internally
            # for Gaussian knockoff sampling and feature permutation.
            np_state = np.random.get_state()
            np.random.seed(rep_seed)
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    rejections = kf.forward(
                        X=X,
                        y=y,
                        Sigma=Sigma,
                        fdr=fdr_target,
                        knockoff_kwargs={"method": "mvr", "verbose": False},
                    )
            finally:
                np.random.set_state(np_state)
            selected_idx = set(np.where(np.asarray(rejections).astype(bool))[0])
            # Capture W statistics for this replicate (knockpy exposes
            # `kf.W` after forward(); fall back gracefully if missing).
            W_arr = np.asarray(getattr(kf, "W", np.full(p, np.nan)), dtype=float)
            if W_arr.shape != (p,):
                W_arr = np.full(p, np.nan)
            W_per_replicate.append(W_arr)
        except Exception as exc:
            if verbose:
                print(f"  Replicate {rep} failed: {exc}")
            replicate_errors.append({"replicate": rep, "error": repr(exc)})
            replicate_selections.append(set())
            W_per_replicate.append(np.full(p, np.nan))
            continue

        selected_names = {gene_names[i] for i in selected_idx}
        replicate_selections.append(selected_names)
        for i in selected_idx:
            selection_counts[i] += 1

        if verbose and (rep + 1) % 5 == 0:
            print(f"  Replicate {rep + 1}/{n_replicates} done")

    selection_rates = {
        gene_names[i]: float(selection_counts[i]) / n_replicates
        for i in range(p)
    }

    # Aggregate W statistics across replicates (mean over non-NaN replicates).
    W_matrix = np.vstack(W_per_replicate) if W_per_replicate else np.zeros((0, p))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        W_mean = np.nanmean(W_matrix, axis=0) if W_matrix.size else np.full(p, np.nan)
    mean_W = {gene_names[i]: float(W_mean[i]) for i in range(p)}
    # Rank by mean W (descending). NaN treated as -inf for ranking.
    ranked_genes = sorted(mean_W.items(), key=lambda kv: -kv[1] if not np.isnan(kv[1]) else float("inf"))

    threshold = 0.50
    selected_genes = sorted(
        g for g, rate in selection_rates.items() if rate >= threshold
    )

    return {
        "selected_genes": selected_genes,
        "selection_rates": selection_rates,
        "fdr_target": fdr_target,
        "n_replicates": n_replicates,
        "seed": seed,
        "sigma_condition_number": cond,
        "replicate_selections": [list(s) for s in replicate_selections],
        "successful_replicates": n_replicates - len(replicate_errors),
        "failed_replicates": len(replicate_errors),
        "replicate_errors": replicate_errors,
        "mean_W_statistic": mean_W,
        "top_genes_by_W": [
            {"gene": g, "mean_W": w} for g, w in ranked_genes
            if not np.isnan(w)
        ][:15],
    }


def check_compound_law(
    law_genes: list[str],
    knockoff_result: dict,
    conjunction_threshold: float = 0.50,
) -> dict:
    """Check if all genes in a compound law are knockoff-selected.

    Uses the pre-registered conjunction rule: ALL constituent genes must
    be selected in >= conjunction_threshold fraction of replicates.

    Parameters
    ----------
    law_genes : genes referenced in the compound law (e.g. ["TOP2A", "EPAS1"])
    knockoff_result : output of run_knockoff_gate
    conjunction_threshold : pre-registered 0.50

    Returns
    -------
    dict with keys:
      - law_genes_selected: bool (conjunction rule passed)
      - per_gene_rates: {gene: selection_rate}
      - min_rate: the bottleneck gene's rate
      - bottleneck_gene: which gene has the lowest rate
    """
    rates = knockoff_result["selection_rates"]
    per_gene = {g: rates.get(g, 0.0) for g in law_genes}
    min_rate = min(per_gene.values()) if per_gene else 0.0
    bottleneck = min(per_gene, key=per_gene.get) if per_gene else None

    return {
        "law_genes_selected": all(r >= conjunction_threshold for r in per_gene.values()),
        "per_gene_rates": per_gene,
        "min_rate": min_rate,
        "bottleneck_gene": bottleneck,
        "conjunction_threshold": conjunction_threshold,
    }
