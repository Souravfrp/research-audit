"""Compare five-day SPY risk forecasts on the same historical validation dates.

The comparison uses the existing constant and rolling-RMS baselines,
Ridge regression, and a Random Forest configuration selected using
chronological training-only folds. All methods are evaluated on the
same validation dates so that their forecast errors are directly
comparable.
"""

import pandas as pd

from src.temporal_split import CUTOFF_DATE, load_log_returns
from src.regime_features import construct_regime_features
from src.risk_forecasting import (
    construct_risk_target,
    split_forecasting_dates,
    constant_risk_baseline,
    rolling_rms_baseline,
)
from src.ridge_risk_forecasting import fit_predict_ridge
from src.random_forest_risk_forecasting import fit_predict_random_forest


def build_validation_comparison():
    """Return date-aligned actual risk and baseline forecasts.

    I use the same feature set, five-day SPY RMS-risk target, training
    dates, and validation dates for every forecasting method. This keeps
    the comparison focused on differences between the models rather than
    differences in data preparation or evaluation dates.
    """



    returns = load_log_returns()
    spy = returns["SPY"]
    features = construct_regime_features(returns)
    target = construct_risk_target(spy)
    
    # I keep the chronological split used in the earlier forecasting work.
    # Training examples are restricted so that their complete five-day
    # targets are observable before the validation period begins.

    train, validation, _ = split_forecasting_dates(
        spy, features.index, target, CUTOFF_DATE
    )

    _, ridge = fit_predict_ridge(
        features, target, train, validation, alpha=1.0
    )

    # These Random Forest settings were selected from a small candidate
    # set using three chronological folds within the training period only.
    # The outer historical validation dates were not used to choose them.
    # I then fit the selected configuration on the full training period
    # and evaluate it on the same validation dates used for Ridge.
    _, random_forest = fit_predict_random_forest(
        features,
        target,
        train,
        validation,
        n_estimators=100,
        max_depth=5,
        min_samples_leaf=10,
        random_state=42,
    )

    comparison = pd.DataFrame({
        "actual": target.loc[validation],
        "constant": constant_risk_baseline(
            target, train, validation
        ),
        "rolling_20d": rolling_rms_baseline(
            spy, validation
        ),
        "ridge": ridge,
        "random_forest": random_forest,
    })

    if comparison.isna().any().any():
        raise ValueError("Comparison contains missing values.")

    return comparison

def plot_validation_forecast_comparison(comparison):
    """Plot historical validation forecasts against realized risk."""
    import matplotlib.pyplot as plt
    from pathlib import Path

    fig, ax = plt.subplots(figsize=(12, 6))

    for column, label in [
        ("actual", "Actual five-day RMS"),
        ("constant", "Training-average baseline"),
        ("rolling_20d", "Rolling 20-day RMS"),
        ("ridge", "Ridge, alpha=1"),
        ("random_forest", "Random Forest"),
    ]:
        ax.plot(comparison.index, comparison[column], label=label)

    ax.set(
        title=(
            "SPY five-day risk: historical validation\n"
            "Forecast dates: 2024-01-23 to 2026-04-23"
        ),
        xlabel="Forecast date",
        ylabel="Daily-return RMS",
    )
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()

    output = Path("results/risk_forecast_validation_comparison.png")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160)
    plt.close(fig)
    return output

if __name__ == "__main__":
    comparison = build_validation_comparison()
    output = plot_validation_forecast_comparison(comparison)

    print("\nFive-day risk forecast comparison")
    print("--------------------------------")
    print("Validation dates:", len(comparison))
    print("First date:", comparison.index.min())
    print("Last date:", comparison.index.max())
    print("Columns:", list(comparison.columns))

    for column in ["constant", "rolling_20d", "ridge", "random_forest"]:
        errors = comparison[column] - comparison["actual"]
        mae = errors.abs().mean()
        rmse = (errors.pow(2).mean()) ** 0.5
        print(f"{column}: MAE={mae:.6f}, RMSE={rmse:.6f}")

    print("Saved figure:", output)
