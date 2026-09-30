"""Generate the portfolio backtesting research overview."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

from portfolio_robustness import PERIODS, run_robustness_analysis


OUTPUT = Path("results/portfolio_research_overview.png")

STRATEGIES = [
    "Rolling 252",
    "Rolling 504",
    "Rolling 756",
    "Rolling 1008",
    "Expanding",
    "Equal-weight buy-and-hold",
    "Equal-weight monthly",
    "SPY buy-and-hold",
]

PERIOD_LABELS = [
    "2019–20",
    "2021–22",
    "2023–24",
    "2025–Apr 2026*",
]


def add_panel(fig, x, y, width, height, title, description):
    panel = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.008,rounding_size=0.012",
        transform=fig.transFigure,
        facecolor="#F5F7FA",
        edgecolor="#CBD5E1",
        linewidth=1,
    )
    fig.patches.append(panel)

    fig.text(
        x + 0.015,
        y + height - 0.025,
        title,
        fontsize=13,
        fontweight="bold",
        va="top",
    )

    fig.text(
        x + 0.015,
        y + height - 0.060,
        description,
        fontsize=10,
        va="top",
        linespacing=1.5,
    )


def main():
    comparison = run_robustness_analysis()

    matrix = comparison.pivot(
        index="Strategy",
        columns="Period",
        values="Return (%)",
    ).loc[STRATEGIES, list(PERIODS)]

    values = matrix.to_numpy(dtype=float)

    assert values.shape == (8, 4)
    assert np.isfinite(values).all()

    fig = plt.figure(figsize=(18, 12), facecolor="white")

    fig.text(
        0.055,
        0.965,
        "PORTFOLIO BACKTESTING | RESEARCH OVERVIEW",
        fontsize=22,
        fontweight="bold",
        va="top",
    )

    fig.text(
        0.055,
        0.929,
        "February 2019–April 2026 | "
        "10 bps transaction costs | "
        "100,000 nominal starting units",
        fontsize=11,
    )

    # A: Historical timeline and research motivation.
    add_panel(
        fig, 0.055, 0.765, 0.89, 0.125,
        "A   WHY THESE HISTORICAL PERIODS?",
        "One continuous evaluation: first execution 1 Feb 2019; "
        "final evaluation 30 Apr 2026; 1,820 daily returns.\n"
        "Four fixed calendar periods: 2019–20 (483), "
        "2021–22 (503), 2023–24 (502), "
        "2025–Apr 2026 (332).\n"
        "Purpose: examine whether full-history findings "
        "remain consistent across different periods.",
    )

    # B: Strategies and comparison metrics.
    add_panel(
        fig, 0.055, 0.630, 0.89, 0.115,
        "B   WHAT DID WE COMPARE?",
        "Five minimum-variance strategies: rolling covariance "
        "windows of 252, 504, 756 and 1008 observations, "
        "plus expanding.\n"
        "Three benchmarks: equal-weight buy-and-hold, "
        "monthly equal-weight and SPY buy-and-hold.\n"
        "Metrics: cumulative return, realized volatility, "
        "maximum drawdown, turnover and transaction expenses.",
    )

    # C: The complete eight-strategy, four-period heatmap.
    fig.text(
        0.055,
        0.603,
        "C   WHAT CHANGED? | CUMULATIVE RETURNS BY PERIOD",
        fontsize=13,
        fontweight="bold",
    )

    fig.text(
        0.055,
        0.580,
        "Blue indicates positive returns; "
        "orange indicates negative returns. "
        "Each cell shows the cumulative return.",
        fontsize=9.8,
    )

    ax = fig.add_axes([0.25, 0.205, 0.64, 0.35])

    image = ax.imshow(
        values,
        cmap="RdBu",
        vmin=-60,
        vmax=60,
        aspect="auto",
    )

    colorbar_axis = fig.add_axes(
        [0.91, 0.225, 0.014, 0.31]
    )

    colorbar = fig.colorbar(
        image,
        cax=colorbar_axis,
        ticks=[-60, -30, 0, 30, 60],
    )

    colorbar.set_label(
        "Cumulative return (%)",
        fontsize=10,
        labelpad=10,
    )

    ax.set_xticks(range(4), PERIOD_LABELS)
    ax.set_yticks(range(8), STRATEGIES)
    ax.xaxis.tick_top()
    ax.tick_params(length=0, pad=9)

    for row in range(8):
        for column in range(4):
            value = values[row, column]

            ax.text(
                column,
                row,
                f"{value:+.1f}%",
                ha="center",
                va="center",
                fontsize=10,
                fontweight="bold",
                color="white" if abs(value) >= 35 else "black",
            )

    ax.set_xticks(np.arange(-0.5, 4, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, 8, 1), minor=True)

    ax.grid(which="minor", color="white", linewidth=2.5)
    ax.tick_params(which="minor", bottom=False, left=False)

    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.text(
        0.055,
        0.187,
        "*The final period ends April 2026 and is shorter. "
        "Returns are cumulative, not annualized.",
        fontsize=9.4,
    )

    # D: Research conclusions and limitations.
    add_panel(
        fig, 0.055, 0.038, 0.89, 0.124,
        "D   FINDINGS AND LIMITATIONS",
        "All five minimum-variance portfolios recorded negative "
        "returns in 2021–22; their relative returns changed "
        "across periods.\n"
        "Their realized volatility was lower than benchmark "
        "volatility in the evaluated subperiods, but losses "
        "still occurred.\n"
        "Retain all five methods for comparison. "
        "This retrospective study is not an untouched "
        "holdout or a prediction of future returns.",
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(
        OUTPUT,
        dpi=200,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(fig)

    assert OUTPUT.is_file()
    assert OUTPUT.stat().st_size > 0

    print(f"\nPASS: Figure generated: {OUTPUT}")
    print(f"File size: {OUTPUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
