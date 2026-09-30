"""Chronological, training-only Ridge alpha comparison."""

import numpy as np
import pandas as pd

from src.ridge_risk_forecasting import fit_predict_ridge
from src.risk_forecasting import forecast_error_metrics

ALPHAS = (0.0, 1.0, 10.0, 100.0, 1000.0)
BOUNDARIES = (0.50, 0.65, 0.80, 1.00)


def compare_alphas(spy, features, target, train_dates):
    """Evaluate alpha without using the outer validation period."""

    target_end = pd.Series(spy.index, index=spy.index).shift(-5)
    results = {alpha: [] for alpha in ALPHAS}

    for fold in range(3):
        start = int(BOUNDARIES[fold] * len(train_dates))
        stop = int(BOUNDARIES[fold + 1] * len(train_dates))

        check_dates = train_dates[start:stop]
        earlier = train_dates[:start]
        fit_dates = earlier[
            target_end.loc[earlier].lt(check_dates[0])
        ]

        assert target_end.loc[fit_dates].lt(check_dates[0]).all()

        print(
            f"Fold {fold + 1}: {len(fit_dates)} fit, "
            f"{len(check_dates)} validation examples"
        )

        for alpha in ALPHAS:
            _, prediction = fit_predict_ridge(
                features, target, fit_dates, check_dates,
                alpha=alpha,
            )
            scores = forecast_error_metrics(
                prediction, target.loc[check_dates]
            )
            results[alpha].append(scores)

    print("\nAlpha      Mean fold MAE    Mean fold RMSE")

    for alpha in ALPHAS:
        mean_mae = np.mean(
            [score["mae"] for score in results[alpha]]
        )
        mean_rmse = np.mean(
            [score["rmse"] for score in results[alpha]]
        )
        print(
            f"{alpha:<10g} "
            f"{mean_mae:.6f}         {mean_rmse:.6f}"
        )

    return results


if __name__ == "__main__":
    from src.temporal_split import CUTOFF_DATE, load_log_returns
    from src.regime_features import construct_regime_features
    from src.risk_forecasting import (
        construct_risk_target,
        split_forecasting_dates,
    )

    returns = load_log_returns()
    spy = returns["SPY"]
    features = construct_regime_features(returns)
    target = construct_risk_target(spy)

    train, _, _ = split_forecasting_dates(
        spy, features.index, target, CUTOFF_DATE
    )

    compare_alphas(spy, features, target, train)
