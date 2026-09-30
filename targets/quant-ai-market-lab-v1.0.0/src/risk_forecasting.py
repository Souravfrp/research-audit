
"""Five-trading-day SPY realized-risk forecasting."""

import numpy as np
import pandas as pd

FORECAST_HORIZON = 5


def construct_risk_target(spy_returns):
    """
    RMS of SPY log returns over the next five trading days.

    The target at date t uses returns t+1 through t+5.
    """
    future_squares = np.column_stack([
        spy_returns.shift(-step).to_numpy() ** 2
        for step in range(1, FORECAST_HORIZON + 1)
    ])

    target = pd.Series(
        np.sqrt(future_squares.mean(axis=1)),
        index=spy_returns.index,
        name="future_5d_daily_return_rms",
    )

    return target


def split_forecasting_dates(
    spy_returns, feature_dates, target, cutoff
):
    """Split dates without letting training targets enter validation."""

    target_end = pd.Series(
        spy_returns.index,
        index=spy_returns.index,
    ).shift(-FORECAST_HORIZON)

    eligible = feature_dates[
        target_end.loc[feature_dates].le(cutoff)
        & target.loc[feature_dates].notna()
    ]

    validation_start = eligible[int(0.80 * len(eligible))]

    train_dates = eligible[
        target_end.loc[eligible].lt(validation_start)
    ]

    validation_dates = eligible[
        eligible >= validation_start
    ]

    evaluation_dates = feature_dates[
        (feature_dates > cutoff)
        & target.loc[feature_dates].notna()
    ]

    if not target_end.loc[train_dates].lt(validation_start).all():
        raise RuntimeError("Training targets enter validation.")

    if not target_end.loc[validation_dates].le(cutoff).all():
        raise RuntimeError("Validation targets cross the cutoff.")

    return train_dates, validation_dates, evaluation_dates


def constant_risk_baseline(target, train_dates, forecast_dates):
    """Predict the training-period average target on every forecast date."""

    historical_average = target.loc[train_dates].mean()

    if not np.isfinite(historical_average):
        raise ValueError("Invalid historical average.")

    return pd.Series(
        historical_average,
        index=forecast_dates,
        name="constant_baseline",
    )


def rolling_rms_baseline(spy_returns, forecast_dates):
    """Predict future daily-return RMS using the latest 20 observed returns."""

    past_rms = np.sqrt(
        spy_returns.pow(2).rolling(
            window=20,
            min_periods=20,
        ).mean()
    )

    predictions = past_rms.loc[forecast_dates].copy()

    if predictions.isna().any():
        raise ValueError("Missing rolling baseline predictions.")

    predictions.name = "rolling_20d_rms_baseline"

    return predictions


def forecast_error_metrics(prediction, actual):
    """Calculate forecast errors on identically dated observations."""

    if not prediction.index.equals(actual.index):
        raise ValueError("Prediction and target dates do not match.")

    errors = prediction.to_numpy() - actual.to_numpy()

    if not np.isfinite(errors).all():
        raise ValueError("Forecast errors contain non-finite values.")

    return {
        "mae": float(np.abs(errors).mean()),
        "rmse": float(np.sqrt(np.mean(errors ** 2))),
        "mean_error": float(errors.mean()),
    }


if __name__ == "__main__":
    from src.temporal_split import (
        CUTOFF_DATE,
        load_log_returns,
        validate_returns,
    )
    from src.regime_features import construct_regime_features

    returns = load_log_returns()
    validate_returns(returns)

    spy = returns["SPY"]
    features = construct_regime_features(returns)
    target = construct_risk_target(spy)

    train, validation, evaluation = split_forecasting_dates(
        spy, features.index, target, CUTOFF_DATE
    )

    actual = target.loc[validation]

    forecasts = {
        "Constant": constant_risk_baseline(
            target, train, validation
        ),
        "Rolling 20-day": rolling_rms_baseline(
            spy, validation
        ),
    }

    print("Five-day SPY risk forecasting: internal validation")
    print("Training examples:", len(train))
    print("Validation examples:", len(validation))
    print("Validation starts:", validation[0])
    print()
    print("Method             MAE       RMSE      Mean error")

    for name, prediction in forecasts.items():
        scores = forecast_error_metrics(prediction, actual)
        print(
            f"{name:<18}"
            f"{scores['mae']:.6f}  "
            f"{scores['rmse']:.6f}  "
            f"{scores['mean_error']:+.6f}"
        )
