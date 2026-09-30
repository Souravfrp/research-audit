"""Plot May-August 2026 actual and forecasted SPY five-day risk."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


INPUT_PATH = Path("results/later_walk_forward_forecasts.csv")
ACTUAL_FIGURE = Path("results/later_actual_vs_forecast.png")
ERROR_FIGURE = Path("results/later_forecast_errors.png")


def load_later_forecasts():
    """Load the saved May-August 2026 forecast table."""
    table = pd.read_csv(
        INPUT_PATH,
        index_col="forecast_date",
        parse_dates=["forecast_date"],
    )

    required = {"actual", "expanding", "adaptive"}
    if not required.issubset(table.columns):
        raise ValueError(
            f"Missing required columns. Need {sorted(required)}."
        )

    if table.empty:
        raise ValueError("Later forecast table is empty.")

    if table.isna().any().any():
        raise ValueError("Later forecast table contains missing values.")

    return table


def plot_actual_vs_forecast(table):
    """Plot actual risk against expanding and adaptive forecasts."""
    fig, ax = plt.subplots(figsize=(13, 5.5))

    ax.plot(
        table.index,
        table["actual"],
        linewidth=2.4,
        color="black",
        label="Actual five-day SPY risk",
        zorder=4,
    )

    ax.plot(
        table.index,
        table["expanding"],
        linewidth=1.9,
        linestyle="--",
        marker="o",
        markersize=3.5,
        markevery=slice(0, None, 2),
        alpha=0.95,
        label="Expanding-window forecast",
        zorder=3,
    )

    ax.plot(
        table.index,
        table["adaptive"],
        linewidth=1.9,
        linestyle="-",
        marker="s",
        markersize=3.5,
        markevery=slice(1, None, 2),
        alpha=0.85,
        label="Adaptive-window forecast",
        zorder=2,
    )

    for refit_date in [
        pd.Timestamp("2026-06-01"),
        pd.Timestamp("2026-07-01"),
        pd.Timestamp("2026-08-03"),
    ]:
        ax.axvline(
            refit_date,
            linestyle=":",
            linewidth=1.0,
            color="gray",
            alpha=0.65,
        )

    ax.set_title(
        "Five-day SPY risk: actual versus forecast, May-August 2026\n"
        "Dashed blue and solid orange use different markers so overlap is visible"
    )
    ax.set_xlabel("Forecast date")
    ax.set_ylabel("Daily log-return RMS")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()

    ACTUAL_FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ACTUAL_FIGURE, dpi=160)
    plt.close(fig)

    return ACTUAL_FIGURE


def plot_error_over_time(table):
    """Plot forecast errors over time for expanding and adaptive forecasts."""
    errors = pd.DataFrame(
        {
            "expanding_error": table["expanding"] - table["actual"],
            "adaptive_error": table["adaptive"] - table["actual"],
        },
        index=table.index,
    )

    fig, ax = plt.subplots(figsize=(13, 5.5))

    ax.plot(
        errors.index,
        errors["expanding_error"],
        linewidth=1.9,
        linestyle="--",
        marker="o",
        markersize=3.5,
        markevery=slice(0, None, 2),
        alpha=0.95,
        label="Expanding-window error",
        zorder=3,
    )

    ax.plot(
        errors.index,
        errors["adaptive_error"],
        linewidth=1.9,
        linestyle="-",
        marker="s",
        markersize=3.5,
        markevery=slice(1, None, 2),
        alpha=0.85,
        label="Adaptive-window error",
        zorder=2,
    )

    ax.axhline(
        0.0,
        color="black",
        linestyle="--",
        linewidth=1.2,
        alpha=0.9,
    )

    for refit_date in [
        pd.Timestamp("2026-06-01"),
        pd.Timestamp("2026-07-01"),
        pd.Timestamp("2026-08-03"),
    ]:
        ax.axvline(
            refit_date,
            linestyle=":",
            linewidth=1.0,
            color="gray",
            alpha=0.65,
        )

    ax.set_title(
        "Five-day SPY risk forecast errors, May-August 2026\n"
        "Error = forecast - actual"
    )
    ax.set_xlabel("Forecast date")
    ax.set_ylabel("Forecast - actual (daily log-return RMS)")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()

    ERROR_FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ERROR_FIGURE, dpi=160)
    plt.close(fig)

    return ERROR_FIGURE



def plot_absolute_error(table):
    """Compare the magnitude of expanding and adaptive forecast errors."""
    expanding_error = (table["expanding"] - table["actual"]).abs()
    adaptive_error = (table["adaptive"] - table["actual"]).abs()

    fig, ax = plt.subplots(figsize=(13, 5.5))

    ax.plot(
        table.index,
        expanding_error,
        label="Expanding-window absolute error",
        linestyle="--",
        marker="o",
        markersize=3.5,
        markevery=slice(0, None, 2),
        linewidth=1.9,
    )
    ax.plot(
        table.index,
        adaptive_error,
        label="Adaptive-window absolute error",
        linestyle="-",
        marker="s",
        markersize=3.5,
        markevery=slice(1, None, 2),
        linewidth=1.9,
    )

    ax.set(
        title="Five-day SPY risk: absolute forecast error, May-August 2026",
        xlabel="Forecast date",
        ylabel="Absolute error (daily log-return RMS)",
    )
    ax.set_ylim(bottom=0)
    ax.grid(alpha=0.25)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()

    output = Path("results/later_absolute_forecast_errors.png")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160)
    plt.close(fig)

    return output


def main():
    table = load_later_forecasts()

    actual_figure = plot_actual_vs_forecast(table)
    error_figure = plot_error_over_time(table)
    absolute_error_figure = plot_absolute_error(table)

    same = (table["expanding"] - table["adaptive"]).abs() < 1e-12
    same_by_month = same.groupby(table.index.to_period("M")).sum()
    count_by_month = same.groupby(table.index.to_period("M")).size()

    print("Plotted forecast dates:", len(table))
    print("First forecast date:", table.index.min().date())
    print("Last forecast date:", table.index.max().date())
    print("Saved figure:", actual_figure)
    print("Saved error figure:", error_figure)
    print("Saved absolute-error figure:", absolute_error_figure)
    print()
    print("Expanding and adaptive forecast equality by month:")
    for month in count_by_month.index:
        print(
            f"{month}: {same_by_month.loc[month]} of "
            f"{count_by_month.loc[month]} dates identical"
        )


if __name__ == "__main__":
    main()
