"""Reconstruct and decompose April 2020 Ridge forecasts."""

import numpy as np
import pandas as pd

from src.temporal_split import load_log_returns
from src.regime_features import construct_regime_features
from src.risk_forecasting import construct_risk_target
from src.ridge_risk_forecasting import fit_predict_ridge
from src.walk_forward_dates import available_training_dates


def build_april_diagnostic():
    """Return forecasts and an original-coordinate decomposition."""
    returns = load_log_returns()
    features = construct_regime_features(returns)
    target = construct_risk_target(returns["SPY"])

    refit_date = pd.Timestamp("2020-04-01")
    april_dates = features.loc["2020-04"].index

    available = available_training_dates(
        returns.index, features.index, target, refit_date
    )

    fitted = {}

    for name, dates in (
        ("rolling_756", available[-756:]),
        ("expanding", available),
    ):
        model, predictions = fit_predict_ridge(
            features, target, dates, april_dates, alpha=1.0
        )

        scaler = model.named_steps["standardscaler"]
        ridge = model.named_steps["ridge"]

        slopes = pd.Series(
            ridge.coef_ / scaler.scale_,
            index=features.columns,
        )
        intercept = ridge.intercept_ - slopes @ scaler.mean_

        fitted[name] = (intercept, slopes, predictions)

    a_r, b_r, pred_r = fitted["rolling_756"]
    a_e, b_e, pred_e = fitted["expanding"]

    contributions = features.loc[april_dates].mul(
        b_r - b_e, axis=1
    )
    contributions["intercept"] = a_r - a_e

    reconstructed = contributions.sum(axis=1)
    direct = pred_r - pred_e

    if not np.allclose(
        reconstructed.to_numpy(),
        direct.to_numpy(),
        rtol=0,
        atol=1e-12,
    ):
        raise RuntimeError("Forecast decomposition failed.")

    forecasts = pd.DataFrame({
        "actual": target.loc[april_dates],
        "rolling_756": pred_r,
        "expanding": pred_e,
    })

    return forecasts, contributions

def plot_april_diagnostic(forecasts, contributions):
    """Plot April forecasts and mean prediction-difference contributions."""
    from pathlib import Path
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(12, 9),
        gridspec_kw={"height_ratios": [2, 1]},
    )

    for column, label in (
        ("actual", "Realized future five-day RMS"),
        ("rolling_756", "Rolling 756"),
        ("expanding", "Expanding"),
    ):
        ax1.plot(forecasts.index, forecasts[column], label=label)

    ax1.set(
        title="April 2020: realized SPY risk and walk-forward forecasts",
        ylabel="Daily log-return RMS",
    )
    ax1.legend()
    ax1.grid(alpha=0.25)

    means = contributions.mean()
    ax2.bar(means.index, means.to_numpy())
    ax2.axhline(0, linewidth=0.8)
    ax2.set(
        title="Mean contribution to rolling-minus-expanding forecast",
        ylabel="Five-day RMS difference",
    )
    ax2.tick_params(axis="x", labelrotation=15)
    ax2.grid(axis="y", alpha=0.25)

    fig.tight_layout()

    output = Path("results/april_2020_ridge_diagnostic.png")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160)
    plt.close(fig)

    return output
