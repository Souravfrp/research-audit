"""
Temporal data splitting for Quant AI Market Lab.

This module separates the validated return dataset into a historical
fitting period and a later evaluation period. The split is designed
to prevent observations after the cutoff date from entering model fitting.
"""

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

LOG_RETURNS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "log_returns.csv"
)

CUTOFF_DATE = pd.Timestamp("2026-04-30")


def load_log_returns():
    """
    Load the validated daily log-return matrix.
    """
    returns = pd.read_csv(
        LOG_RETURNS_PATH,
        index_col=0,
        parse_dates=True,
    )

    return returns


def validate_returns(returns):
    """
    Validate the return matrix before applying the temporal split.
    """
    if returns.empty:
        raise RuntimeError("Return dataset is empty.")

    if returns.index.duplicated().any():
        raise RuntimeError("Return dataset contains duplicate dates.")

    if not returns.index.is_monotonic_increasing:
        raise RuntimeError(
            "Return dates are not in chronological order."
        )

    if returns.isna().any().any():
        raise RuntimeError("Return dataset contains missing values.")

    if not np.isfinite(returns.to_numpy()).all():
        raise RuntimeError(
            "Return dataset contains non-finite values."
        )


def temporal_split(returns, cutoff=CUTOFF_DATE):
    """
    Split returns into historical fitting and later evaluation periods.

    A return dated on or before the cutoff belongs to the historical
    period. A return dated after the cutoff belongs to the later
    evaluation period.
    """
    historical = returns.loc[returns.index <= cutoff].copy()
    later = returns.loc[returns.index > cutoff].copy()

    if historical.empty:
        raise RuntimeError("Historical return period is empty.")

    if later.empty:
        raise RuntimeError("Later evaluation period is empty.")

    if len(historical) + len(later) != len(returns):
        raise RuntimeError(
            "Temporal split did not preserve all return observations."
        )

    if historical.index.max() > cutoff:
        raise RuntimeError(
            "Historical period contains observations after the cutoff."
        )

    if later.index.min() <= cutoff:
        raise RuntimeError(
            "Evaluation period contains observations on or before the cutoff."
        )

    return historical, later


if __name__ == "__main__":
    returns = load_log_returns()
    validate_returns(returns)

    historical, later = temporal_split(returns)

    print("Temporal split validation passed.")

    print("\nHistorical fitting period:")
    print("First return date:", historical.index.min())
    print("Last return date: ", historical.index.max())
    print("Observations:      ", len(historical))

    print("\nLater evaluation period:")
    print("First return date:", later.index.min())
    print("Last return date: ", later.index.max())
    print("Observations:      ", len(later))

    print("\nTotal observations preserved:")
    print(len(historical) + len(later), "/", len(returns))
