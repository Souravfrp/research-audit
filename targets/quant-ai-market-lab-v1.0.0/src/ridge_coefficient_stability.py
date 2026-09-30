"""Examine coefficient stability in the rolling 504-observation Ridge model."""

import numpy as np
import pandas as pd

from src.temporal_split import CUTOFF_DATE, load_log_returns
from src.regime_features import construct_regime_features
from src.risk_forecasting import (
    FORECAST_HORIZON,
    construct_risk_target,
)
from src.walk_forward_dates import build_refit_training_schedule
from src.ridge_risk_forecasting import fit_predict_ridge


def main():
    returns = load_log_returns()
    features = construct_regime_features(returns)
    target = construct_risk_target(returns["SPY"])

    # Use the same historical forecast dates as the walk-forward experiment.
    target_end = pd.Series(
        returns.index, index=returns.index
    ).shift(-FORECAST_HORIZON)

    forecast_dates = features.index[
        (features.index >= "2019-02-08")
        & target_end.loc[features.index].le(CUTOFF_DATE)
        & target.loc[features.index].notna()
    ]

    schedule = build_refit_training_schedule(
        returns.index,
        features.index,
        target,
        forecast_dates,
    )

    standardized_rows = []
    original_unit_rows = []
    maximum_reconstruction_error = 0.0

    for refit_date, eligible_dates in schedule.items():
        # Reproduce the existing rolling 504-observation training rule.
        training_dates = eligible_dates[-504:]

        model, predictions = fit_predict_ridge(
            features,
            target,
            training_dates,
            pd.DatetimeIndex([refit_date]),
            alpha=1.0,
        )

        scaler = model.named_steps["standardscaler"]
        ridge = model.named_steps["ridge"]

        # Coefficients for standardized inputs.
        standardized_rows.append(
            dict(zip(features.columns, ridge.coef_))
        )

        # Convert coefficients back to the original input units.
        original_coefficients = ridge.coef_ / scaler.scale_
        original_intercept = (
            ridge.intercept_
            - np.dot(original_coefficients, scaler.mean_)
        )

        original_unit_rows.append(
            dict(zip(features.columns, original_coefficients))
        )

        # Check that both forms give the same prediction.
        x = features.loc[refit_date].to_numpy()
        reconstructed_prediction = (
            original_intercept + np.dot(original_coefficients, x)
        )

        error = abs(
            reconstructed_prediction - predictions.iloc[0]
        )

        maximum_reconstruction_error = max(
            maximum_reconstruction_error,
            error,
        )

    standardized = pd.DataFrame(
        standardized_rows, index=list(schedule)
    )
    original_units = pd.DataFrame(
        original_unit_rows, index=list(schedule)
    )

    print("Monthly refits:", len(standardized))
    print("First refit:", standardized.index.min().date())
    print("Last refit:", standardized.index.max().date())

    print("\nStandardized coefficient summary:")
    print(standardized.agg(["min", "median", "max"]).round(8))

    print("\nPositive coefficient counts:")
    print((standardized > 0).sum())

    print("\nNegative coefficient counts:")
    print((standardized < 0).sum())

    print("\nOriginal-unit coefficient summary:")
    print(original_units.agg(["min", "median", "max"]).round(6))

    print(
        "\nMaximum prediction reconstruction error:",
        f"{maximum_reconstruction_error:.3e}",
    )
    print(
        "Reconstruction passed:",
        maximum_reconstruction_error < 1e-12,
    )


if __name__ == "__main__":
    main()