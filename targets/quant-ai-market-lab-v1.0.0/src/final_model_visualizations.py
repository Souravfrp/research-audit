"""Final visualizations for Ridge and Random Forest risk forecasting."""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.tree import plot_tree

from src.temporal_split import CUTOFF_DATE, load_log_returns
from src.regime_features import construct_regime_features
from src.risk_forecasting import (
    FORECAST_HORIZON,
    construct_risk_target,
    split_forecasting_dates,
)
from src.ridge_risk_forecasting import fit_predict_ridge
from src.random_forest_risk_forecasting import fit_predict_random_forest
from src.walk_forward_dates import build_refit_training_schedule
from src.walk_forward_comparison import FIRST_FORECAST_DATE


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results"


def load_common_inputs():
    """Load the common return, feature, and target objects."""
    returns = load_log_returns()
    spy = returns["SPY"]
    features = construct_regime_features(returns)
    target = construct_risk_target(spy)
    return returns, spy, features, target


def historical_training_dates(spy, features, target):
    """Return the original internal training and validation dates."""
    train_dates, validation_dates, _ = split_forecasting_dates(
        spy, features.index, target, CUTOFF_DATE
    )
    return train_dates, validation_dates


def rolling_504_coefficient_history(returns, features, target):
    """Collect standardized Ridge coefficients across rolling-504 refits."""
    target_end = pd.Series(
        returns.index,
        index=returns.index,
    ).shift(-FORECAST_HORIZON)

    forecast_dates = features.index[
        (features.index >= FIRST_FORECAST_DATE)
        & target_end.loc[features.index].le(CUTOFF_DATE)
        & target.loc[features.index].notna()
    ]

    schedule = build_refit_training_schedule(
        returns.index,
        features.index,
        target,
        forecast_dates,
    )

    records = []

    for refit_date in schedule:
        available = schedule[refit_date]
        training_dates = available[-504:]

        model, _ = fit_predict_ridge(
            features,
            target,
            training_dates,
            pd.DatetimeIndex([refit_date]),
            alpha=1.0,
        )

        ridge = model.named_steps["ridge"]

        row = {"refit_date": refit_date}
        for feature_name, coefficient in zip(features.columns, ridge.coef_):
            row[feature_name] = coefficient

        records.append(row)

    coefficient_history = pd.DataFrame(records).set_index("refit_date")

    if coefficient_history.isna().any().any():
        raise RuntimeError("Coefficient history contains missing values.")

    return coefficient_history


def plot_ridge_coefficient_stability(coefficient_history):
    """Plot standardized Ridge coefficients through time."""
    plt.figure(figsize=(12, 6))

    for column in coefficient_history.columns:
        plt.plot(
            coefficient_history.index,
            coefficient_history[column],
            label=column,
        )

    plt.axhline(0.0, linewidth=1.0)
    plt.title(
        "Rolling 504 Ridge model: coefficient stability\n"
        "Monthly refits from 2019-02-08 to 2026-04-01"
    )
    plt.xlabel("Refit date")
    plt.ylabel("Standardized coefficient")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()

    output = RESULTS_DIR / "ridge_504_coefficient_stability.png"
    plt.savefig(output, dpi=180, bbox_inches="tight")
    plt.close()

    print("Saved:", output)
    return output


def build_surface_frame(base_point, x_name, y_name, x_values, y_values):
    """Create a feature grid for a two-variable response surface."""
    mesh_x, mesh_y = np.meshgrid(x_values, y_values)

    rows = []
    for y_value in y_values:
        for x_value in x_values:
            row = base_point.copy()
            row[x_name] = x_value
            row[y_name] = y_value
            rows.append(row)

    surface_frame = pd.DataFrame(rows)
    surface_frame = surface_frame[base_point.index]

    return mesh_x, mesh_y, surface_frame


def plot_prediction_surface(
    model,
    training_features,
    training_target,
    model_name,
    output_name,
):
    """
    Plot a 3D prediction surface using volatility and dispersion,
    holding SPY return fixed at its median training value.
    """
    x_name = "spy_volatility_20d"
    y_name = "cross_asset_dispersion"
    fixed_name = "spy_return"

    base_point = training_features.median().copy()
    fixed_value = float(base_point[fixed_name])

    x_values = np.linspace(
        training_features[x_name].quantile(0.05),
        training_features[x_name].quantile(0.95),
        45,
    )
    y_values = np.linspace(
        training_features[y_name].quantile(0.05),
        training_features[y_name].quantile(0.95),
        45,
    )

    mesh_x, mesh_y, surface_frame = build_surface_frame(
        base_point,
        x_name,
        y_name,
        x_values,
        y_values,
    )

    surface_z = model.predict(surface_frame).reshape(
        len(y_values),
        len(x_values),
    )

    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(111, projection="3d")

    ax.plot_surface(
        mesh_x,
        mesh_y,
        surface_z,
        alpha=0.80,
        linewidth=0,
        antialiased=True,
    )

    # This is a two-feature model slice. I do not overlay the raw
    # training targets because their SPY-return values vary, whereas
    # this surface holds SPY return fixed at its training median.

    ax.set_xlabel("SPY 20-day volatility")
    ax.set_ylabel("Cross-asset dispersion")
    ax.set_zlabel("Predicted five-day RMS")
    ax.set_title(
        f"{model_name}: prediction surface\n"
        f"SPY return fixed at median training value = {fixed_value:.6f}"
    )

    fig.tight_layout()

    output = RESULTS_DIR / output_name
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)

    print("Saved:", output)
    return output


def plot_representative_tree(random_forest_model, feature_names):
    """Plot one representative tree from the fitted Random Forest."""
    estimator = random_forest_model.estimators_[0]

    plt.figure(figsize=(20, 10))
    plot_tree(
        estimator,
        feature_names=list(feature_names),
        filled=False,
        rounded=True,
        max_depth=3,
        fontsize=8,
    )
    plt.title(
        "Representative Random Forest tree\n"
        "First estimator, shown only to depth 3"
    )
    plt.tight_layout()

    output = RESULTS_DIR / "random_forest_representative_tree.png"
    plt.savefig(output, dpi=180, bbox_inches="tight")
    plt.close()

    print("Saved:", output)
    return output


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    returns, spy, features, target = load_common_inputs()
    train_dates, validation_dates = historical_training_dates(
        spy, features, target
    )

    train_features = features.loc[train_dates]
    train_target = target.loc[train_dates]

    ridge_model, _ = fit_predict_ridge(
        features,
        target,
        train_dates,
        validation_dates,
        alpha=1.0,
    )

    random_forest_model, _ = fit_predict_random_forest(
        features,
        target,
        train_dates,
        validation_dates,
        n_estimators=100,
        max_depth=5,
        min_samples_leaf=10,
        random_state=42,
    )

    coefficient_history = rolling_504_coefficient_history(
        returns,
        features,
        target,
    )

    outputs = []
    outputs.append(plot_ridge_coefficient_stability(coefficient_history))
    outputs.append(
        plot_prediction_surface(
            ridge_model,
            train_features,
            train_target,
            model_name="Ridge model",
            output_name="ridge_prediction_surface.png",
        )
    )
    outputs.append(
        plot_prediction_surface(
            random_forest_model,
            train_features,
            train_target,
            model_name="Random Forest",
            output_name="random_forest_prediction_surface.png",
        )
    )
    outputs.append(
        plot_representative_tree(
            random_forest_model,
            train_features.columns,
        )
    )

    print("\nCreated figures:")
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
