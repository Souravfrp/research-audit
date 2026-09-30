"""Visualize historical portfolio risk and trading activity."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from portfolio_robustness import PERIODS, run_robustness_analysis


OUTPUT = Path("results/portfolio_risk_comparison.png")

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

METRICS = [
    (
        "Volatility (%)",
        "A   ANNUALIZED REALIZED VOLATILITY",
        "YlOrBr",
        1,
        "%",
    ),
    (
        "Max drawdown (%)",
        "B   MAXIMUM DRAWDOWN",
        "OrRd",
        -1,
        "%",
    ),
    (
        "Turnover",
        "C   CUMULATIVE PORTFOLIO TURNOVER",
        "Blues",
        1,
        "",
    ),
]


def draw_heatmap(ax, comparison, metric, title, cmap, sign, suffix):
    matrix = comparison.pivot(
        index="Strategy",
        columns="Period",
        values=metric,
    ).loc[STRATEGIES, list(PERIODS)]

    values = sign * matrix.to_numpy(dtype=float)

    assert values.shape == (8, 4)
    assert np.isfinite(values).all()

    image = ax.imshow(
        values,
        cmap=cmap,
        vmin=0,
        vmax={
            "Volatility (%)": 30,
            "Max drawdown (%)": 35,
            "Turnover": 5,
        }[metric],
        aspect="auto",
    )

    ax.set_title(
        title,
        loc="left",
        fontsize=13,
        fontweight="bold",
        pad=28,
    )

    ax.set_xticks(
        range(4),
        PERIOD_LABELS,
        fontsize=10,
    )

    ax.set_yticks(
        range(8),
        STRATEGIES,
        fontsize=10,
    )

    ax.xaxis.tick_top()
    ax.tick_params(length=0, pad=8)

    midpoint = float(values.max()) / 2.0

    for row in range(8):
        for column in range(4):
            value = values[row, column]

            ax.text(
                column,
                row,
                f"{sign * value:.2f}{suffix}",
                ha="center",
                va="center",
                fontsize=9.5,
                fontweight="medium",
                color=(
                    "white"
                    if value > midpoint
                    else "#172033"
                ),
            )

    ax.set_xticks(
        np.arange(-0.5, 4, 1),
        minor=True,
    )

    ax.set_yticks(
        np.arange(-0.5, 8, 1),
        minor=True,
    )

    ax.grid(
        which="minor",
        color="white",
        linewidth=2,
    )

    ax.tick_params(
        which="minor",
        bottom=False,
        left=False,
    )

    for spine in ax.spines.values():
        spine.set_visible(False)

    return image


def main():
    comparison = run_robustness_analysis()

    assert len(comparison) == 32

    fig, axes = plt.subplots(
        nrows=3,
        ncols=1,
        figsize=(16, 19),
        facecolor="white",
    )

    fig.subplots_adjust(
        left=0.27,
        right=0.94,
        top=0.88,
        bottom=0.085,
        hspace=0.55,
    )

    fig.suptitle(
        "PORTFOLIO RISK AND TRADING ACTIVITY",
        fontsize=22,
        fontweight="bold",
        x=0.055,
        y=0.975,
        ha="left",
    )

    fig.text(
        0.055,
        0.947,
        "Eight strategies | Four historical periods | "
        "10-basis-point transaction costs",
        fontsize=11,
        color="#475569",
    )

    fig.text(
        0.055,
        0.925,
        "All metrics are calculated from the same chronological "
        "portfolio simulations as the research overview.",
        fontsize=10,
        color="#475569",
    )

    for ax, (
        metric,
        title,
        cmap,
        sign,
        suffix,
    ) in zip(axes, METRICS):

        image = draw_heatmap(
            ax,
            comparison,
            metric,
            title,
            cmap,
            sign,
            suffix,
        )

        colorbar = fig.colorbar(
            image,
            ax=ax,
            fraction=0.025,
            pad=0.025,
        )

        if metric == "Volatility (%)":
            colorbar.set_ticks([0, 10, 20, 30])
            colorbar.set_label(
                "Annualized volatility (%)",
                fontsize=10,
            )

        elif metric == "Max drawdown (%)":
            colorbar.set_ticks([0, 10, 20, 30, 35])
            colorbar.set_label(
                "Drawdown magnitude (%)",
                fontsize=10,
            )

        else:
            colorbar.set_ticks([0, 1, 2, 3, 4, 5])
            colorbar.set_label(
                "Cumulative turnover",
                fontsize=10,
            )

    fig.text(
        0.055,
        0.045,
        "*The final period ends April 2026 and is shorter "
        "than the other periods.",
        fontsize=10,
        color="#475569",
    )

    fig.text(
        0.055,
        0.026,
        "Volatility is annualized. Drawdown is measured "
        "from each subperiod's opening wealth; turnover "
        "is the sum of recorded execution turnover.",
        fontsize=10,
        color="#475569",
    )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig.savefig(
        OUTPUT,
        dpi=200,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(fig)

    assert OUTPUT.is_file()
    assert OUTPUT.stat().st_size > 0

    print(f"\nPASS: Risk figure generated: {OUTPUT}")
    print(f"File size: {OUTPUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
