"""Permutation importance for the selected Random Forest risk model."""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.inspection import permutation_importance

from src.temporal_split import CUTOFF_DATE, load_log_returns
from src.regime_features import construct_regime_features
from src.risk_forecasting import (
    construct_risk_target,
    split_forecasting_dates,
)
from src.random_forest_risk_forecasting import fit_predict_random_forest


RESULTS_DIR = Path("results")


def main():
    returns = load_log_returns()
    spy = returns["SPY"]
    features = construct_regime_features(returns)
    target = construct_risk_target(spy)

    train_dates, validation_dates, _ = split_forecasting_dates(
        spy,
        features.index,
        target,
        CUTOFF_DATE,
    )

    model, _ = fit_predict_random_forest(
        features,
        target,
        train_dates,
        validation_dates,
        n_estimators=100,
        max_depth=5,
        min_samples_leaf=10,
        random_state=42,
    )

    X_validation = features.loc[validation_dates]
    y_validation = target.loc[validation_dates]

    importance = permutation_importance(
        model,
        X_validation,
        y_validation,
        scoring="neg_mean_absolute_error",
        n_repeats=50,
        random_state=42,
        n_jobs=-1,
    )

    summary = pd.DataFrame({
        "feature": features.columns,
        "mae_increase_mean": importance.importances_mean,
        "mae_increase_std": importance.importances_std,
    }).sort_values(
        "mae_increase_mean",
        ascending=False,
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    csv_output = (
        RESULTS_DIR / "random_forest_permutation_importance.csv"
    )
    summary.to_csv(csv_output, index=False)

    plot_data = summary.sort_values("mae_increase_mean")

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(
        plot_data["feature"],
        plot_data["mae_increase_mean"],
        xerr=plot_data["mae_increase_std"],
    )

    ax.set(
        title=(
            "Random Forest permutation importance\n"
            "Historical validation, 50 permutations per feature"
        ),
        xlabel="Increase in MAE after feature permutation",
        ylabel="Feature",
    )
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()

    figure_output = (
        RESULTS_DIR / "random_forest_permutation_importance.png"
    )
    fig.savefig(figure_output, dpi=180, bbox_inches="tight")
    plt.close(fig)

    print("Validation observations:", len(validation_dates))
    print("\nPermutation importance:")
    print(summary.to_string(index=False))
    print("\nSaved:", csv_output)
    print("Saved:", figure_output)
    print(
        "\nNote: permutation importance measures model reliance "
        "in this historical validation sample, not causation."
    )


if __name__ == "__main__":
    main()
