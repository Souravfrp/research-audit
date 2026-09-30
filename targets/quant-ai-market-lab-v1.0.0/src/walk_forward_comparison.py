"""Compare walk-forward Ridge training windows on common dates."""

import pandas as pd

from src.temporal_split import CUTOFF_DATE, load_log_returns
from src.regime_features import construct_regime_features
from src.risk_forecasting import (
    FORECAST_HORIZON,
    construct_risk_target,
)
from src.walk_forward_ridge import (
    expanding_window_forecasts,
    rolling_window_forecasts,
)


WINDOWS = (252, 504, 756, 1008)
FIRST_FORECAST_DATE = "2019-02-08"


def build_walk_forward_comparison():
    """Return aligned actual risk and candidate-window forecasts."""
    returns = load_log_returns()
    features = construct_regime_features(returns)
    target = construct_risk_target(returns["SPY"])

    target_end = pd.Series(
        returns.index, index=returns.index
    ).shift(-FORECAST_HORIZON)

    dates = features.index[
        (features.index >= FIRST_FORECAST_DATE)
        & target_end.loc[features.index].le(CUTOFF_DATE)
        & target.loc[features.index].notna()
    ]

    comparison = pd.DataFrame(
        {"actual": target.loc[dates]},
        index=dates,
    )

    for window in WINDOWS:
        comparison[f"rolling_{window}"] = (
            rolling_window_forecasts(
                returns, features, target, dates,
                window=window, alpha=1.0,
            )
        )

    comparison["expanding"] = expanding_window_forecasts(
        returns, features, target, dates, alpha=1.0
    )

    if comparison.isna().any().any():
        raise RuntimeError("Comparison contains missing values.")

    if not comparison.index.equals(dates):
        raise RuntimeError("Forecast dates are misaligned.")

    return comparison

if __name__ == "__main__":
    import numpy as np
    from pathlib import Path

    output = Path("results/walk_forward_forecasts.csv")
    comparison = build_walk_forward_comparison()

    if output.exists():
        saved = pd.read_csv(
            output,
            index_col="forecast_date",
            parse_dates=["forecast_date"],
        )

        if (
            not saved.index.equals(comparison.index)
            or not saved.columns.equals(comparison.columns)
            or not np.allclose(
                saved.to_numpy(),
                comparison.to_numpy(),
                rtol=0,
                atol=1e-12,
            )
        ):
            raise RuntimeError(
                "Existing CSV differs from reproduced forecasts."
            )

        print("PASS: Existing forecast CSV reproduced.")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        comparison.to_csv(
            output,
            index_label="forecast_date",
            float_format="%.17g",
        )
        print("Created:", output)

    print("Forecast dates:", len(comparison))
    print("First date:", comparison.index[0].date())
    print("Last date:", comparison.index[-1].date())
