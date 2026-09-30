"""Evaluate adaptive and fixed-window forecasts on common dates."""

import pandas as pd

from src.temporal_split import load_log_returns
from src.risk_forecasting import forecast_error_metrics
from src.adaptive_window_selection import (
    build_adaptive_selection_schedule,
    build_adaptive_forecasts,
)


METHODS = (
    "rolling_252",
    "rolling_504",
    "rolling_756",
    "rolling_1008",
    "expanding",
    "adaptive",
)


def build_evaluation():
    """Return date-aligned forecasts and the selection schedule."""
    returns = load_log_returns()

    comparison = pd.read_csv(
        "results/walk_forward_forecasts.csv",
        index_col="forecast_date",
        parse_dates=["forecast_date"],
    )

    schedule = build_adaptive_selection_schedule(
        returns.index,
        comparison,
        history=252,
    )

    adaptive = build_adaptive_forecasts(
        comparison, schedule
    )

    common = comparison.loc[adaptive.index].copy()
    common["adaptive"] = adaptive

    if not common.index.equals(adaptive.index):
        raise RuntimeError("Forecast dates are misaligned.")

    if common.isna().any().any():
        raise RuntimeError("Evaluation contains missing values.")

    return common, schedule


def main():
    common, schedule = build_evaluation()

    print("Walk-forward evaluation")
    print("Forecast dates:", len(common))
    print("First date:", common.index[0].date())
    print("Last date:", common.index[-1].date())
    print("Monthly adaptive selections:", len(schedule))
    print()
    print(
        f"{'Method':<16} {'MAE':>10} "
        f"{'RMSE':>10} {'Mean error':>12}"
    )

    for method in METHODS:
        scores = forecast_error_metrics(
            common[method],
            common["actual"],
        )

        print(
            f"{method:<16} "
            f"{scores['mae']:>10.6f} "
            f"{scores['rmse']:>10.6f} "
            f"{scores['mean_error']:>+12.6f}"
        )


if __name__ == "__main__":
    main()
