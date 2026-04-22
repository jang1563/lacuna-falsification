"""Generate synthetic KIRC-like CSVs matching config/law_proposals.json gene names.

Not real patient data. Produces two cohorts (flagship + transfer) with
biologically-plausible effect sizes so the falsification gate behaves
realistically during the demo:

- HIF-axis and Warburg genes are upregulated in tumor (CA9, VEGFA, LDHA, SLC2A1, NDUFA4L2)
- Normal-kidney markers are downregulated in tumor (AGXT, ALB)
- Housekeeping genes show near-zero effect (ACTB, GAPDH, RPL13A)
- MKI67 shows small noisy effect to mimic a proliferation red herring

Cohorts share biology but differ in mean expression scale + noise profile,
mimicking RNA-seq (flagship) vs microarray (transfer) platforms.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

GENES = [
    "CA9", "VEGFA", "LDHA", "SLC2A1", "NDUFA4L2",  # tumor-up
    "AGXT", "ALB",                                   # normal-up
    "ACTB", "GAPDH", "RPL13A",                      # housekeeping
    "MKI67",                                         # noisy red herring
]

EFFECT = {
    # Effects calibrated so no single gene dominates — compound laws have
    # room to exceed the best single-feature baseline by >0.05 AUROC and
    # the 5-test falsification gate has something to separate.
    "CA9":      1.0,
    "VEGFA":    0.9,
    "LDHA":     0.85,
    "SLC2A1":   0.7,
    "NDUFA4L2": 0.8,
    "AGXT":    -0.9,
    "ALB":     -0.8,
    "ACTB":     0.0,
    "GAPDH":    0.0,
    "RPL13A":   0.0,
    "MKI67":    0.15,
}


def _simulate_cohort(
    n_disease: int,
    n_control: int,
    base_scale: float,
    noise_scale: float,
    seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n_total = n_disease + n_control
    y = np.array([1] * n_disease + [0] * n_control)

    rows: dict[str, np.ndarray] = {}
    for gene in GENES:
        base = rng.normal(loc=base_scale, scale=0.25, size=n_total)
        effect_contrib = EFFECT[gene] * y
        noise = rng.normal(loc=0.0, scale=noise_scale, size=n_total)
        raw = np.exp(base + effect_contrib + noise)
        rows[gene] = np.round(raw, 3)

    df = pd.DataFrame(rows)
    df.insert(0, "sample_id", [f"S{i:03d}" for i in range(n_total)])
    df.insert(1, "label", np.where(y == 1, "disease", "control"))
    df.insert(2, "age", rng.integers(35, 78, size=n_total))
    df.insert(3, "batch_index", rng.integers(0, 4, size=n_total))

    # Shuffle so disease/control are interleaved.
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    return df


def main() -> None:
    out_dir = Path(__file__).parent

    flagship = _simulate_cohort(
        n_disease=220, n_control=220, base_scale=4.0, noise_scale=1.3, seed=11,
    )
    flagship.to_csv(out_dir / "flagship_kirc_demo.csv", index=False)

    transfer = _simulate_cohort(
        n_disease=50, n_control=51, base_scale=3.5, noise_scale=1.5, seed=23,
    )
    transfer.to_csv(out_dir / "transfer_kirc_demo.csv", index=False)

    print(f"Wrote {len(flagship)} flagship and {len(transfer)} transfer rows.")
    print("Columns:", list(flagship.columns))


if __name__ == "__main__":
    main()
