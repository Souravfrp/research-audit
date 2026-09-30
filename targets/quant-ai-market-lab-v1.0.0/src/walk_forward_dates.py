"""Select leakage-safe training dates for walk-forward forecasts."""

import pandas as pd

from src.risk_forecasting import FORECAST_HORIZON


def available_training_dates(
    return_dates, feature_dates, target, forecast_date
):
    """Select examples with labels observable by forecast_date."""

    return_dates = pd.DatetimeIndex(return_dates)
    feature_dates = pd.DatetimeIndex(feature_dates)
    forecast_date = pd.Timestamp(forecast_date)

    if forecast_date not in return_dates:
        raise ValueError("Forecast date is not a trading date.")

    target_end = pd.Series(
        return_dates, index=return_dates
    ).shift(-FORECAST_HORIZON)

    eligible = feature_dates[
        (feature_dates < forecast_date)
        & target_end.loc[feature_dates].le(forecast_date)
        & target.loc[feature_dates].notna()
    ]

    if not target_end.loc[eligible].le(forecast_date).all():
        raise RuntimeError("Training contains an unavailable target.")

    return eligible

def monthly_refit_dates(forecast_dates):
    """Select the first eligible forecast date of each month."""
    dates = pd.DatetimeIndex(forecast_dates)

    if dates.empty:
        raise ValueError("No forecast dates supplied.")

    if dates.has_duplicates or not dates.is_monotonic_increasing:
        raise ValueError(
            "Forecast dates must be unique and chronological."
        )

    months = dates.to_period("M")
    return dates[~months.duplicated()]

def build_refit_training_schedule(
    return_dates, feature_dates, target, forecast_dates
):
    """Map each monthly refit date to its eligible training dates."""
    refits = monthly_refit_dates(forecast_dates)
    schedule = {}

    for refit_date in refits:
        training_dates = available_training_dates(
            return_dates, feature_dates, target, refit_date
        )

        if len(training_dates) == 0:
            raise ValueError(
                f"No training examples available at {refit_date}."
            )

        schedule[refit_date] = training_dates

    return schedule
