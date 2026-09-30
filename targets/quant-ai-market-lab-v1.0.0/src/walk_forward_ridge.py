"""Walk-forward Ridge forecasts with monthly refitting."""

import pandas as pd

from src.ridge_risk_forecasting import fit_predict_ridge
from src.walk_forward_dates import build_refit_training_schedule


def expanding_window_forecasts(
    returns, features, target, forecast_dates, alpha=1.0
):
    """Fit monthly on all eligible history and forecast daily."""

    forecast_dates = pd.DatetimeIndex(forecast_dates)

    if forecast_dates.empty:
        raise ValueError("No forecast dates supplied.")

    schedule = build_refit_training_schedule(
        returns.index,
        features.index,
        target,
        forecast_dates,
    )

    refits = list(schedule)
    prediction_blocks = []

    for i, refit_date in enumerate(refits):
        end = (
            refits[i + 1]
            if i + 1 < len(refits)
            else forecast_dates[-1] + pd.Timedelta(days=1)
        )

        block_dates = forecast_dates[
            (forecast_dates >= refit_date)
            & (forecast_dates < end)
        ]

        _, predictions = fit_predict_ridge(
            features,
            target,
            schedule[refit_date],
            block_dates,
            alpha=alpha,
        )

        prediction_blocks.append(predictions)

    forecasts = pd.concat(prediction_blocks)

    if not forecasts.index.equals(forecast_dates):
        raise RuntimeError("Forecast dates are missing or misaligned.")

    if forecasts.isna().any():
        raise RuntimeError("Missing walk-forward forecasts.")

    return forecasts

def rolling_window_forecasts(
    returns, features, target, forecast_dates,
    window, alpha=1.0,
):
    """Refit monthly using the most recent eligible training examples."""

    if isinstance(window, bool) or not isinstance(window, int) or window < 1:
        raise ValueError("Window must be a positive integer.")

    forecast_dates = pd.DatetimeIndex(forecast_dates)

    if forecast_dates.empty:
        raise ValueError("No forecast dates supplied.")

    schedule = build_refit_training_schedule(
        returns.index,
        features.index,
        target,
        forecast_dates,
    )

    refits = list(schedule)
    prediction_blocks = []

    for i, refit_date in enumerate(refits):
        available = schedule[refit_date]

        if len(available) < window:
            raise ValueError(
                f"Insufficient training history at {refit_date.date()}."
            )

        training_dates = available[-window:]

        end = (
            refits[i + 1]
            if i + 1 < len(refits)
            else forecast_dates[-1] + pd.Timedelta(days=1)
        )

        block_dates = forecast_dates[
            (forecast_dates >= refit_date)
            & (forecast_dates < end)
        ]

        _, predictions = fit_predict_ridge(
            features,
            target,
            training_dates,
            block_dates,
            alpha=alpha,
        )

        prediction_blocks.append(predictions)

    forecasts = pd.concat(prediction_blocks)

    if not forecasts.index.equals(forecast_dates):
        raise RuntimeError("Forecast dates are missing or misaligned.")

    if forecasts.isna().any():
        raise RuntimeError("Missing rolling-window forecasts.")

    return forecasts
