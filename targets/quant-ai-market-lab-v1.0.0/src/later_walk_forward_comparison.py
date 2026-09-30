"""Generate fixed-specification walk-forward forecasts through August 2026."""

import pandas as pd

from src.temporal_split import CUTOFF_DATE, load_log_returns
from src.regime_features import construct_regime_features
from src.risk_forecasting import FORECAST_HORIZON, construct_risk_target
from src.walk_forward_comparison import (
    FIRST_FORECAST_DATE,
    WINDOWS,
)
from src.walk_forward_ridge import (
    expanding_window_forecasts,
    rolling_window_forecasts,
)


def build_extended_comparison():
    """Return historical and later candidate forecasts on aligned dates."""
    returns = load_log_returns()
    features = construct_regime_features(returns)
    target = construct_risk_target(returns["SPY"])

    target_end = pd.Series(
        returns.index, index=returns.index
    ).shift(-FORECAST_HORIZON)

    dates = features.index[
        (features.index >= FIRST_FORECAST_DATE)
        & target_end.loc[features.index].notna()
        & target.loc[features.index].notna()
    ]

    comparison = pd.DataFrame(
        {"actual": target.loc[dates]},
        index=dates,
    )

    for window in WINDOWS:
        comparison[f"rolling_{window}"] = rolling_window_forecasts(
            returns, features, target, dates,
            window=window, alpha=1.0,
        )

    comparison["expanding"] = expanding_window_forecasts(
        returns, features, target, dates, alpha=1.0
    )

    if comparison.isna().any().any():
        raise RuntimeError("Extended comparison contains missing values.")

    if not comparison.index.equals(dates):
        raise RuntimeError("Extended forecast dates are misaligned.")

    historical = comparison.loc[comparison.index <= CUTOFF_DATE]
    later = comparison.loc[comparison.index > CUTOFF_DATE]

    if historical.empty or later.empty:
        raise RuntimeError("A comparison period is empty.")

    return historical, later
