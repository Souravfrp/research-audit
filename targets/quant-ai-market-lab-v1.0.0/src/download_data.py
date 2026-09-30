"""
Market data ingestion module for Quant AI Market Lab.

This module downloads historical market data for a diversified
cross-asset universe used in the quantitative analysis pipeline.
"""

from pathlib import Path

import numpy as np
import yfinance as yf


# Cross-asset universe used throughout the project
TICKERS = {
    "SPY": "US Large-Cap Equity",
    "QQQ": "US Growth/Technology Equity",
    "IWM": "US Small-Cap Equity",
    "TLT": "Long-Term US Treasury Bonds",
    "GLD": "Gold",
    "USO": "Crude Oil",
    "EEM": "Emerging-Market Equity",
    "VNQ": "US Real Estate",
}


# Project directories
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


START_DATE = "2015-01-01"
END_DATE = "2026-09-01"

def validate_adjusted_prices(adjusted_prices):
    """
    Validate adjusted-price data before saving it.

    The downstream return calculation requires a clean,
    chronologically ordered matrix of finite positive prices.
    """
    if adjusted_prices.empty:
        raise RuntimeError("Adjusted-price dataset is empty.")

    if adjusted_prices.index.duplicated().any():
        raise RuntimeError("Adjusted-price dataset contains duplicate dates.")

    if not adjusted_prices.index.is_monotonic_increasing:
        raise RuntimeError(
            "Adjusted-price dates are not in chronological order."
        )

    if adjusted_prices.isna().any().any():
        raise RuntimeError(
            "Adjusted-price dataset contains missing values."
        )

    values = adjusted_prices.to_numpy()

    if not np.isfinite(values).all():
        raise RuntimeError(
            "Adjusted-price dataset contains non-finite values."
        )

    if (values <= 0).any():
        raise RuntimeError(
            "Adjusted-price dataset contains non-positive prices."
        )

    print("Adjusted-price validation passed.")



def download_adjusted_prices():
    """
    Download adjusted closing prices for the project asset universe.

    Returns
    -------
    pandas.DataFrame
        Rows correspond to trading dates and columns correspond to assets.
    """

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    data = yf.download(
        tickers=list(TICKERS.keys()),
        start=START_DATE,
        end=END_DATE,
        auto_adjust=False,
        progress=False,
    )

    if data.empty:
        raise RuntimeError("No market data was downloaded.")

    adjusted_prices = data["Adj Close"].copy()

    missing_assets = [
        ticker
        for ticker in TICKERS
        if ticker not in adjusted_prices.columns
    ]

    if missing_assets:
        raise RuntimeError(
            f"Missing adjusted-price data for: {missing_assets}"
        )
    validate_adjusted_prices(adjusted_prices)
    output_path = RAW_DATA_DIR / "adjusted_close.csv"
    adjusted_prices.to_csv(output_path)

    print(f"Saved adjusted prices to: {output_path}")
    print(f"Observations: {adjusted_prices.shape[0]}")
    print(f"Assets: {adjusted_prices.shape[1]}")

    return adjusted_prices


if __name__ == "__main__":
    download_adjusted_prices()
