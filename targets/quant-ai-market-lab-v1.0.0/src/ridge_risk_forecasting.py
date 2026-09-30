"""Initial Ridge model for five-day SPY RMS-risk forecasting."""

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def fit_predict_ridge(features, target, train_dates, forecast_dates,
                      alpha=1.0):
    """Fit on training dates only and predict on forecast dates."""

    if alpha < 0 or not np.isfinite(alpha):
        raise ValueError("Ridge alpha must be finite and nonnegative.")

    X_train = features.loc[train_dates]
    y_train = target.loc[train_dates]
    X_forecast = features.loc[forecast_dates]

    if X_train.isna().any().any() or y_train.isna().any():
        raise ValueError("Training inputs contain missing values.")
    if X_forecast.isna().any().any():
        raise ValueError("Forecast inputs contain missing values.")

    model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
    model.fit(X_train, y_train)

    predictions = pd.Series(
        model.predict(X_forecast),
        index=forecast_dates,
        name="ridge_forecast",
    )

    return model, predictions


if __name__ == "__main__":
    from src.temporal_split import CUTOFF_DATE, load_log_returns
    from src.regime_features import construct_regime_features
    from src.risk_forecasting import (
        construct_risk_target,
        split_forecasting_dates,
        forecast_error_metrics,
    )

    returns = load_log_returns()
    spy = returns["SPY"]
    features = construct_regime_features(returns)
    target = construct_risk_target(spy)

    train, validation, _ = split_forecasting_dates(
        spy, features.index, target, CUTOFF_DATE
    )

    model, predictions = fit_predict_ridge(
        features, target, train, validation, alpha=1.0
    )
    scores = forecast_error_metrics(
        predictions, target.loc[validation]
    )

    print("Five-day SPY risk forecasting: provisional Ridge")
    print("Training examples:", len(train))
    print("Validation examples:", len(validation))
    print("Validation starts:", validation[0].date())
    print("Alpha:", model.named_steps["ridge"].alpha)
    print("MAE:", f"{scores['mae']:.6f}")
    print("RMSE:", f"{scores['rmse']:.6f}")
    print("Mean error:", f"{scores['mean_error']:+.6f}")
    print("Negative forecasts:", int((predictions < 0).sum()))
