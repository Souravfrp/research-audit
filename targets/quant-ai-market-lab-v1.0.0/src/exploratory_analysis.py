"""
Exploratory data analysis and visualization for Quant AI Market Lab.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "adjusted_close.csv"

RESULTS_DIR = PROJECT_ROOT / "results"

LOG_RETURNS_PATH = PROJECT_ROOT / "data" / "processed" / "log_returns.csv"


def load_prices():
    """
    Load adjusted closing prices.
    """

    prices = pd.read_csv(
        RAW_DATA_PATH,
        index_col=0,
        parse_dates=True,
    )

    return prices
def load_log_returns():
    """
    Load previously validated daily log returns.
    """

    log_returns = pd.read_csv(
        LOG_RETURNS_PATH,
        index_col=0,
        parse_dates=True,
    )

    return log_returns
def compute_annualized_volatility(log_returns):
    """
    Compute annualized volatility from daily log returns.
    """

    daily_volatility = log_returns.std()

    annualized_volatility = daily_volatility * (252 ** 0.5)

    return annualized_volatility

def compute_correlation_matrix(log_returns):
    """
    Compute the cross-asset Pearson correlation matrix
    from daily log returns.
    """

    correlation_matrix = log_returns.corr()

    return correlation_matrix

def plot_correlation_matrix(correlation_matrix):
    """
    Plot and save the cross-asset return correlation matrix.
    """

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(9, 7))

    image = ax.imshow(
        correlation_matrix,
        vmin=-1,
        vmax=1,
    )

    assets = correlation_matrix.columns

    ax.set_xticks(range(len(assets)))
    ax.set_yticks(range(len(assets)))

    ax.set_xticklabels(assets)
    ax.set_yticklabels(assets)

    for i in range(len(assets)):
        for j in range(len(assets)):
            ax.text(
                j,
                i,
                f"{correlation_matrix.iloc[i, j]:.2f}",
                ha="center",
                va="center",
            )

    ax.set_title("Cross-Asset Daily Return Correlation")

    fig.colorbar(
        image,
        ax=ax,
        label="Pearson Correlation",
    )

    figure_path = RESULTS_DIR / "correlation_matrix.png"

    plt.tight_layout()
    plt.savefig(
        figure_path,
        dpi=200,
        bbox_inches="tight",
    )

    print(f"Saved figure to: {figure_path}")

    plt.close()

def plot_annualized_volatility(annualized_volatility):
    """
    Plot annualized volatility for each asset and save the figure.
    """

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    volatility_percent = 100 * annualized_volatility.sort_values(
        ascending=False
    )

    ax = volatility_percent.plot(
        kind="bar",
        figsize=(10, 6),
    )

    ax.set_title("Annualized Historical Volatility by Asset")
    ax.set_xlabel("Asset")
    ax.set_ylabel("Annualized Volatility (%)")
    ax.grid(True, axis="y", alpha=0.3)


    for container in ax.containers:
        ax.bar_label(
            container,
            fmt="%.1f%%",
            padding=3,
        )
    figure_path = RESULTS_DIR / "annualized_volatility.png"

    plt.tight_layout()
    plt.savefig(
        figure_path,
        dpi=200,
        bbox_inches="tight",
    )

    print(f"Saved figure to: {figure_path}")

    plt.close()


def normalize_prices(prices):
    """
    Normalize each asset so that its first observation equals 100.
    """

    normalized = 100 * prices / prices.iloc[0]

    return normalized


def plot_normalized_performance(normalized):
    """
    Plot normalized cross-asset performance and save the figure.
    """

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    ax = normalized.plot(
        figsize=(12, 7),
        linewidth=1.5,
    )

    ax.set_title("Normalized Cross-Asset Performance")
    ax.set_xlabel("Date")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlim(normalized.index.min(), normalized.index.max())
    ax.set_ylabel("Normalized Value (Start = 100)")
    ax.grid(True, alpha=0.3)

    figure_path = RESULTS_DIR / "normalized_asset_performance.png"

    plt.tight_layout()
    plt.savefig(
        figure_path,
        dpi=200,
        bbox_inches="tight",
    )

    print(f"Saved figure to: {figure_path}")

    plt.close()


if __name__ == "__main__":
    prices = load_prices()
    log_returns = load_log_returns()

    normalized = normalize_prices(prices)
    annualized_volatility = compute_annualized_volatility(log_returns)
    correlation_matrix = compute_correlation_matrix(log_returns)

    plot_normalized_performance(normalized)
    plot_annualized_volatility(annualized_volatility)
    plot_correlation_matrix(correlation_matrix)

    print("\nCross-Asset Correlation Matrix:")
    print(correlation_matrix.round(3))
