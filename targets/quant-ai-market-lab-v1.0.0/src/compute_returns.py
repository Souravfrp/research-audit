"""
Return computation module for Quant AI Market Lab.

This module transforms adjusted asset prices into simple returns
and logarithmic returns for downstream statistical and quantitative analysis.
"""

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "adjusted_close.csv"

PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def load_prices():
    """
    Load adjusted closing prices from the raw-data directory.
    """

    prices = pd.read_csv(
        RAW_DATA_PATH,
        index_col=0,
        parse_dates=True,
    )

    return prices


def compute_returns(prices):
    """
    Compute simple returns and log returns.

    Parameters
    ----------
    prices : pandas.DataFrame
        Adjusted closing prices.

    Returns
    -------
    simple_returns : pandas.DataFrame
        One-period percentage returns.

    log_returns : pandas.DataFrame
        One-period continuously compounded returns.
    """

    simple_returns = prices.pct_change(fill_method=None)

    log_returns = np.log(prices / prices.shift(1))

    simple_returns = simple_returns.dropna()
    log_returns = log_returns.dropna()

    if simple_returns.empty or log_returns.empty:
        raise RuntimeError("Return computation produced an empty dataset.")

    if simple_returns.isna().any().any():
        raise RuntimeError("Simple-return matrix contains missing values.")

    if log_returns.isna().any().any():
        raise RuntimeError("Log-return matrix contains missing values.")

    if not np.isfinite(simple_returns.to_numpy()).all():
        raise RuntimeError("Simple-return matrix contains non-finite values.")

    if not np.isfinite(log_returns.to_numpy()).all():
        raise RuntimeError("Log-return matrix contains non-finite values.")

    consistency_error = np.max(
        np.abs(np.log1p(simple_returns) - log_returns)
    )

    if consistency_error > 1e-12:
        raise RuntimeError(
            f"Simple/log return consistency check failed: {consistency_error}"
        )

    print(f"Return consistency error: {consistency_error:.3e}")

    return simple_returns, log_returns


def save_returns(simple_returns, log_returns):
    """
    Save processed return matrices to disk.
    """

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    simple_path = PROCESSED_DATA_DIR / "simple_returns.csv"
    log_path = PROCESSED_DATA_DIR / "log_returns.csv"

    simple_returns.to_csv(simple_path)
    log_returns.to_csv(log_path)

    print(f"Saved simple returns to: {simple_path}")
    print(f"Saved log returns to: {log_path}")

    print(f"Simple-return shape: {simple_returns.shape}")
    print(f"Log-return shape: {log_returns.shape}")


if __name__ == "__main__":
    prices = load_prices()

    simple_returns, log_returns = compute_returns(prices)

    save_returns(simple_returns, log_returns)
