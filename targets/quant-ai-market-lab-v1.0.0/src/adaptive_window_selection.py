"""Past-only evaluation data for adaptive window selection."""

import pandas as pd

from src.risk_forecasting import FORECAST_HORIZON


def observable_forecast_dates(
    return_dates, comparison_dates, selection_date
):
    """Return forecast dates with outcomes known by selection_date."""

    return_dates = pd.DatetimeIndex(return_dates)
    comparison_dates = pd.DatetimeIndex(comparison_dates)
    selection_date = pd.Timestamp(selection_date)

    if selection_date not in return_dates:
        raise ValueError("Selection date is not a trading date.")

    if not comparison_dates.isin(return_dates).all():
        raise ValueError("Forecast dates are missing from trading dates.")

    target_end = pd.Series(
        return_dates,
        index=return_dates,
    ).shift(-FORECAST_HORIZON)

    eligible = comparison_dates[
        (comparison_dates < selection_date)
        & target_end.loc[comparison_dates].le(selection_date)
    ]

    if not target_end.loc[eligible].le(selection_date).all():
        raise RuntimeError("Selection includes an unobserved outcome.")

    return eligible

CANDIDATE_METHODS = (
    "rolling_252",
    "rolling_504",
    "rolling_756",
    "rolling_1008",
    "expanding",
)


def select_window_from_past_errors(
    return_dates, comparison, selection_date, history=252
):
    """Select a method using only completed historical forecast errors."""

    if isinstance(history, bool) or not isinstance(history, int):
        raise ValueError("History must be a positive integer.")
    if history < 1:
        raise ValueError("History must be a positive integer.")

    required = ("actual",) + CANDIDATE_METHODS
    if not set(required).issubset(comparison.columns):
        raise ValueError("Comparison is missing required columns.")

    eligible = observable_forecast_dates(
        return_dates,
        comparison.index,
        selection_date,
    )

    if len(eligible) < history:
        raise ValueError(
            f"Need {history} completed forecasts; "
            f"only {len(eligible)} are available."
        )

    selected_dates = eligible[-history:]
    past = comparison.loc[selected_dates, required]

    if past.isna().any().any():
        raise ValueError("Historical comparison contains missing values.")

    losses = {
        method: (past[method] - past["actual"]).abs().mean()
        for method in CANDIDATE_METHODS
    }

    # Candidate order breaks an exact tie reproducibly.
    selected_method = min(CANDIDATE_METHODS, key=losses.get)

    return selected_method, losses, selected_dates

def build_adaptive_selection_schedule(
    return_dates, comparison, history=252
):
    """Record past-only method selections at monthly refit dates."""
    from src.walk_forward_dates import monthly_refit_dates

    refit_dates = monthly_refit_dates(comparison.index)
    records = []

    for refit_date in refit_dates:
        eligible = observable_forecast_dates(
            return_dates, comparison.index, refit_date
        )

        if len(eligible) < history:
            continue

        method, losses, selected_dates = (
            select_window_from_past_errors(
                return_dates,
                comparison,
                refit_date,
                history=history,
            )
        )

        records.append({
            "refit_date": refit_date,
            "selected_method": method,
            "history_count": len(selected_dates),
            "history_start": selected_dates[0],
            "history_end": selected_dates[-1],
            **{f"mae_{name}": losses[name]
               for name in CANDIDATE_METHODS},
        })

    if not records:
        raise ValueError("No refit date has sufficient completed history.")

    return pd.DataFrame(records).set_index("refit_date")

def build_adaptive_forecasts(comparison, schedule):
    """Use each month's past-selected method for that month's forecasts."""
    if schedule.empty:
        raise ValueError("Selection schedule is empty.")

    dates = comparison.index[
        comparison.index >= schedule.index[0]
    ]

    predictions = pd.Series(
        index=dates,
        dtype=float,
        name="adaptive",
    )

    refits = list(schedule.index)

    for i, refit_date in enumerate(refits):
        end = (
            refits[i + 1]
            if i + 1 < len(refits)
            else dates[-1] + pd.Timedelta(days=1)
        )

        block_dates = dates[
            (dates >= refit_date) & (dates < end)
        ]

        method = schedule.loc[refit_date, "selected_method"]

        if method not in CANDIDATE_METHODS:
            raise ValueError("Unknown selected method.")

        predictions.loc[block_dates] = comparison.loc[
            block_dates, method
        ]

    if predictions.isna().any():
        raise RuntimeError("Adaptive forecasts are incomplete.")

    return predictions
