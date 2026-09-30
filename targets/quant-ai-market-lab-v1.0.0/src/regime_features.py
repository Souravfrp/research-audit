"""
Construct and visualize baseline features for market-regime analysis.

Baseline features:
1. SPY daily log return
2. 20-day rolling SPY volatility
3. Daily cross-asset return dispersion

The features are constructed from historical information without using
observations after the fixed temporal cutoff.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.temporal_split import (
    load_log_returns,
    temporal_split,
    validate_returns,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results"

VOLATILITY_WINDOW = 20


def construct_regime_features(returns):
    """
    Construct the baseline regime-feature matrix.
    """
    spy_return = returns["SPY"]

    spy_volatility_20d = spy_return.rolling(
        window=VOLATILITY_WINDOW,
        min_periods=VOLATILITY_WINDOW,
    ).std()

    cross_asset_dispersion = returns.std(axis=1)

    features = pd.DataFrame(
        {
            "spy_return": spy_return,
            "spy_volatility_20d": spy_volatility_20d,
            "cross_asset_dispersion": cross_asset_dispersion,
        }
    )

    return features.dropna()


def plot_feature_geometry(features):
    """
    Plot pairwise geometric views of the baseline feature space.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    pairs = [
        (
            "spy_return",
            "spy_volatility_20d",
            "SPY Return vs 20-Day Volatility",
            "regime_return_vs_volatility.png",
        ),
        (
            "spy_return",
            "cross_asset_dispersion",
            "SPY Return vs Cross-Asset Dispersion",
            "regime_return_vs_dispersion.png",
        ),
        (
            "spy_volatility_20d",
            "cross_asset_dispersion",
            "20-Day Volatility vs Cross-Asset Dispersion",
            "regime_volatility_vs_dispersion.png",
        ),
    ]

    for x_column, y_column, title, filename in pairs:
        plt.figure(figsize=(8, 6))

        plt.scatter(
            features[x_column],
            features[y_column],
            alpha=0.45,
            s=16,
        )

        plt.xlabel(x_column.replace("_", " ").title())
        plt.ylabel(y_column.replace("_", " ").title())
        plt.title(title)
        plt.grid(alpha=0.25)
        plt.tight_layout()

        output_path = RESULTS_DIR / filename
        plt.savefig(output_path, dpi=160)
        plt.close()

        print("Saved:", output_path)


if __name__ == "__main__":
    returns = load_log_returns()
    validate_returns(returns)

    historical, _ = temporal_split(returns)

    features = construct_regime_features(historical)

    print("Baseline regime-feature matrix")
    print("Shape:", features.shape)
    print("First date:", features.index.min())
    print("Last date: ", features.index.max())
    print("\nMissing values:")
    print(features.isna().sum())

    plot_feature_geometry(features)
