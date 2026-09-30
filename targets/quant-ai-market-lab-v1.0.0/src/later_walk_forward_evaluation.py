"""Reproduce the fixed-cutoff May–August 2026 forecast evaluation."""

import numpy as np
import pandas as pd

from src.temporal_split import CUTOFF_DATE, load_log_returns
from src.risk_forecasting import (
    FORECAST_HORIZON,
    forecast_error_metrics,
)
from src.later_walk_forward_comparison import build_extended_comparison
from src.adaptive_window_selection import (
    CANDIDATE_METHODS,
    build_adaptive_selection_schedule,
    build_adaptive_forecasts,
    observable_forecast_dates,
)
from src.walk_forward_evaluation import METHODS


def build_later_evaluation():
    """Rebuild the later forecasts using the unchanged historical rules."""
    returns = load_log_returns()
    historical, later = build_extended_comparison()
    extended = pd.concat([historical, later])

    saved_historical = pd.read_csv(
        "results/walk_forward_forecasts.csv",
        index_col="forecast_date",
        parse_dates=["forecast_date"],
    )

    if not saved_historical.index.isin(historical.index).all():
        raise RuntimeError("Saved historical forecast dates are missing.")

    if not saved_historical.columns.equals(historical.columns):
        raise RuntimeError("Historical forecast columns changed.")

    if not np.allclose(
        historical.loc[saved_historical.index].to_numpy(),
        saved_historical.to_numpy(),
        rtol=0,
        atol=1e-12,
    ):
        raise RuntimeError("Saved historical forecasts were not reproduced.")

    schedule = build_adaptive_selection_schedule(
        returns.index, extended, history=252
    )
    adaptive = build_adaptive_forecasts(extended, schedule)

    evaluation = later.copy()
    evaluation["adaptive"] = adaptive.loc[later.index]

    target_end = pd.Series(
        returns.index, index=returns.index
    ).shift(-FORECAST_HORIZON)

    if not target_end.loc[evaluation.index].le(returns.index[-1]).all():
        raise RuntimeError("Evaluation includes an incomplete target.")

    if len(evaluation) != 79:
        raise RuntimeError("Unexpected later evaluation date count.")

    if (
        evaluation.index[0] != pd.Timestamp("2026-05-01")
        or evaluation.index[-1] != pd.Timestamp("2026-08-24")
    ):
        raise RuntimeError("Later evaluation dates changed.")

    if evaluation.isna().any().any():
        raise RuntimeError("Later evaluation contains missing values.")

    later_schedule = schedule.loc[schedule.index > CUTOFF_DATE]

    if len(later_schedule) != 4:
        raise RuntimeError("Expected four later monthly selections.")

    for refit_date, row in later_schedule.iterrows():
        completed = observable_forecast_dates(
            returns.index, extended.index, refit_date
        )
        history = completed[-252:]

        if (
            len(history) != 252
            or history[0] != row["history_start"]
            or history[-1] != row["history_end"]
        ):
            raise RuntimeError("Adaptive selection history changed.")

        method = row["selected_method"]

        if method not in CANDIDATE_METHODS:
            raise RuntimeError("Unknown adaptive method.")

        if method != min(
            CANDIDATE_METHODS,
            key=lambda name: row[f"mae_{name}"],
        ):
            raise RuntimeError("Adaptive selection does not match past MAE.")

        month_dates = evaluation.index[
            evaluation.index.to_period("M") == refit_date.to_period("M")
        ]

        if not np.allclose(
            evaluation.loc[month_dates, "adaptive"].to_numpy(),
            evaluation.loc[month_dates, method].to_numpy(),
            rtol=0,
            atol=1e-12,
        ):
            raise RuntimeError("Adaptive forecasts do not match selection.")

    return evaluation, later_schedule


def main():
    evaluation, schedule = build_later_evaluation()

    saved = pd.read_csv(
        "results/later_walk_forward_forecasts.csv",
        index_col="forecast_date",
        parse_dates=["forecast_date"],
    )

    if (
        not evaluation.index.equals(saved.index)
        or not evaluation.columns.equals(saved.columns)
        or not np.allclose(
            evaluation.to_numpy(),
            saved.to_numpy(),
            rtol=0,
            atol=1e-12,
        )
    ):
        raise RuntimeError("Saved later forecast CSV was not reproduced.")

    print("PASS: Saved later forecasts reproduced.")
    print("Forecast dates:", len(evaluation))
    print("Period:", evaluation.index[0].date(), "to",
          evaluation.index[-1].date())

    print("\nLater monthly selections:")
    for date, row in schedule.iterrows():
        print(date.date(), row["selected_method"])

    print("\nMay–August 2026 evaluation")
    print(f"{'Method':<16} {'MAE':>10} {'RMSE':>10} {'Mean error':>12}")

    for method in METHODS:
        scores = forecast_error_metrics(
            evaluation[method], evaluation["actual"]
        )
        print(
            f"{method:<16}"
            f" {scores['mae']:>10.6f}"
            f" {scores['rmse']:>10.6f}"
            f" {scores['mean_error']:>+12.6f}"
        )


if __name__ == "__main__":
    main()
