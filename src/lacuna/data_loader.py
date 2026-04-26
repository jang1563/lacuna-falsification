"""DatasetCard abstraction — plug-in-dataset layer.

A `DatasetCard` is the minimum contract the Lacuna pipeline needs
to evaluate law candidates on any disease CSV:

  sample_id, label (disease/control or 0/1), covariates..., gene columns...

The card records the CSV path, how to parse labels, which columns are
covariates, and which are genes. Two load methods are exposed:

  DatasetCard.from_json(path)
      Parse a card JSON file.
  DatasetCard.infer_from_csv(csv_path, label_column, disease_id, ...)
      Auto-infer a card from a CSV (used by `lacuna plug-in-dataset`).

`card.load(csv_path_override=None)` returns `(X_raw, X_zscored, y, gene_cols,
X_cov_or_None)` — a single tuple that `cli._cmd_compare` and downstream
scripts can unpack without caring about which disease the data came from.

This module deliberately re-uses `_parse_labels` and `_zscore` from `cli`
to stay a single source of truth. The card itself is a dataclass.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

import numpy as np
import pandas as pd


_DEFAULT_DISEASE_TOKENS = frozenset(
    {"disease", "tumor", "case", "cancer", "m1", "1", "true", "yes"}
)


@dataclass
class DatasetCard:
    """A CSV-to-(X, y) contract for a disease classification task.

    Required fields: `dataset_id`, `csv_path`, `label_column`, `gene_columns`.
    Optional: `covariate_columns`, `disease_tokens` (override the default),
    `standardize` (bool, default True), `notes`.
    """

    dataset_id: str
    csv_path: str
    label_column: str
    gene_columns: list[str]
    covariate_columns: list[str] = field(default_factory=list)
    disease_tokens: list[str] | None = None
    standardize: bool = True
    notes: str = ""

    # --- Parsing -----------------------------------------------------------

    @classmethod
    def from_json(cls, path: str | Path) -> "DatasetCard":
        data = json.loads(Path(path).read_text())
        return cls(**data)

    def to_json(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(asdict(self), indent=2))
        return p

    # --- Loading -----------------------------------------------------------

    def load(
        self, csv_path_override: str | Path | None = None
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str], np.ndarray | None]:
        csv_path = Path(csv_path_override or self.csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"DatasetCard CSV not found: {csv_path}")
        df = pd.read_csv(csv_path)

        missing_genes = [g for g in self.gene_columns if g not in df.columns]
        if missing_genes:
            raise ValueError(
                f"DatasetCard '{self.dataset_id}' declares genes not in CSV: {missing_genes[:5]}"
                + (f" (+{len(missing_genes)-5} more)" if len(missing_genes) > 5 else "")
            )
        if self.label_column not in df.columns:
            raise ValueError(
                f"DatasetCard '{self.dataset_id}' label column '{self.label_column}' not in CSV"
            )

        y = _parse_labels(df[self.label_column], self.disease_tokens)
        X_raw = df[self.gene_columns].fillna(0).values.astype(float)
        X = _zscore(X_raw) if self.standardize else X_raw
        X_cov = None
        if self.covariate_columns:
            present_cov = [c for c in self.covariate_columns if c in df.columns]
            if present_cov:
                X_cov = df[present_cov].fillna(0).values.astype(float)
        return X_raw, X, y, list(self.gene_columns), X_cov

    # --- Inference from raw CSV -------------------------------------------

    @classmethod
    def infer_from_csv(
        cls,
        csv_path: str | Path,
        label_column: str,
        disease_id: str,
        covariate_columns: list[str] | None = None,
        exclude_columns: list[str] | None = None,
    ) -> "DatasetCard":
        """Auto-infer a DatasetCard from a CSV.

        Rule: every numeric column that is not `label_column`, not a
        covariate, and not in `exclude_columns` (defaults: `sample_id`,
        `patient_id`) is treated as a gene feature.
        """
        csv_path = Path(csv_path)
        df = pd.read_csv(csv_path, nrows=5)
        if label_column not in df.columns:
            raise ValueError(f"label_column '{label_column}' not in {csv_path}")

        cov = list(covariate_columns or [])
        exclude = set(exclude_columns or []) | {"sample_id", "patient_id", label_column} | set(cov)
        numeric_cols = [
            c for c in df.select_dtypes(include=[np.number]).columns if c not in exclude
        ]
        if not numeric_cols:
            raise ValueError(
                f"No numeric gene columns inferred from {csv_path}; "
                "check label_column / covariate_columns / exclude_columns."
            )
        return cls(
            dataset_id=disease_id,
            csv_path=str(csv_path),
            label_column=label_column,
            gene_columns=numeric_cols,
            covariate_columns=cov,
            standardize=True,
            notes=f"Auto-inferred from {csv_path.name} on the plug-in-dataset path.",
        )


# --- Shared helpers (single source of truth) ------------------------------


def _parse_labels(series: pd.Series, disease_tokens: list[str] | None = None) -> np.ndarray:
    """Parse a label series to 0/1 ints.

    Mirrors `cli._parse_labels` so DatasetCard can be used standalone. If
    `disease_tokens` is provided it overrides the default token set
    (useful for e.g. "stage" tasks where 'III' / 'IV' are disease and
    'I' / 'II' are control).
    """
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(int).values
    tokens = frozenset(t.lower() for t in disease_tokens) if disease_tokens else _DEFAULT_DISEASE_TOKENS
    s = series.astype(str).str.strip().str.lower()
    return s.map(lambda v: 1 if v in tokens else 0).values.astype(int)


def _zscore(X: np.ndarray) -> np.ndarray:
    mean = X.mean(axis=0, keepdims=True)
    std = X.std(axis=0, keepdims=True)
    std = np.where(std < 1e-8, 1.0, std)
    return (X - mean) / std
