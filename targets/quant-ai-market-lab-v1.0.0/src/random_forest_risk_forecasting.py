"""Random Forest model for five-day SPY RMS-risk forecasting."""


import pandas as pd
from sklearn.ensemble import RandomForestRegressor


def fit_predict_random_forest(
    features,
    target,
    train_dates,
    forecast_dates,
    n_estimators=100,
    max_depth=5,
    min_samples_leaf=10,
    random_state=42,
):
    """Fit on training dates only and predict on forecast dates."""

    if n_estimators < 1:
        raise ValueError("n_estimators must be positive.")
    if max_depth is not None and max_depth < 1:
        raise ValueError("max_depth must be positive or None.")
    if min_samples_leaf < 1:
        raise ValueError("min_samples_leaf must be positive.")

    X_train = features.loc[train_dates]
    y_train = target.loc[train_dates]
    X_forecast = features.loc[forecast_dates]

    if X_train.isna().any().any() or y_train.isna().any():
        raise ValueError("Training inputs contain missing values.")
    if X_forecast.isna().any().any():
        raise ValueError("Forecast inputs contain missing values.")

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        random_state=random_state,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    predictions = pd.Series(
        model.predict(X_forecast),
        index=forecast_dates,
        name="random_forest_forecast",
    )

    return model, predictions
