"""Select Random Forest settings using chronological training-only folds."""

import numpy as np
import pandas as pd

from src.random_forest_risk_forecasting import fit_predict_random_forest
from src.risk_forecasting import (
    FORECAST_HORIZON,
    construct_risk_target,
    forecast_error_metrics,
    split_forecasting_dates,
)
from src.temporal_split import CUTOFF_DATE, load_log_returns
from src.regime_features import construct_regime_features


# Fix the forest size at 100 trees and compare a small set of
# depth and minimum-leaf-size combinations.

CANDIDATES = (
    (100, 3, 10),
    (100, 5, 10),
    (100, 5, 20),
    (100, 8, 20),
)

# Reuse the boundaries from the existing Ridge alpha-validation study.
BOUNDARIES = (0.50, 0.65, 0.80, 1.00)


def compare_random_forest_settings(
    spy, features, target, train_dates
):
    """Compare candidates without using the outer validation period."""

    target_end = pd.Series(
        spy.index, index=spy.index
    ).shift(-FORECAST_HORIZON)

    results = {candidate: [] for candidate in CANDIDATES}
    
    for fold in range(len(BOUNDARIES) - 1):
        start = int(BOUNDARIES[fold] * len(train_dates))
        stop = int(BOUNDARIES[fold + 1] * len(train_dates))

        check_dates = train_dates[start:stop]
        earlier = train_dates[:start]

        # Exclude labels that are not fully observable before this fold.
        fit_dates = earlier[
            target_end.loc[earlier].lt(check_dates[0])
        ]

        if not target_end.loc[fit_dates].lt(check_dates[0]).all():
            raise RuntimeError("Training targets enter validation.")

        print(
            f"Fold {fold + 1}: {len(fit_dates)} fit, "
            f"{len(check_dates)} validation examples"
        )

        for candidate in CANDIDATES:
            n_estimators, max_depth, min_samples_leaf = candidate

            _, predictions = fit_predict_random_forest(
                features,
                target,
                fit_dates,
                check_dates,
                n_estimators=n_estimators,
                max_depth=max_depth,
                min_samples_leaf=min_samples_leaf,
                random_state=42,
            )

            scores = forecast_error_metrics(
                predictions,
                target.loc[check_dates],
            )
            results[candidate].append(scores)

    print("\nCandidate settings and mean chronological-fold errors")
    print("Trees  Depth  Min leaf  Mean MAE  Mean RMSE")

    for candidate in CANDIDATES:
        mean_mae = np.mean(
            [score["mae"] for score in results[candidate]]
        )
        mean_rmse = np.mean(
            [score["rmse"] for score in results[candidate]]
        )

        trees, depth, min_leaf = candidate
        print(
            f"{trees:>5}  {depth:>5}  {min_leaf:>8}  "
            f"{mean_mae:.6f}  {mean_rmse:.6f}"
        )

    return results


if __name__ == "__main__":
    returns = load_log_returns()
    spy = returns["SPY"]
    features = construct_regime_features(returns)
    target = construct_risk_target(spy)

    train_dates, _, _ = split_forecasting_dates(
        spy, features.index, target, CUTOFF_DATE
    )

    compare_random_forest_settings(
        spy, features, target, train_dates
    )
