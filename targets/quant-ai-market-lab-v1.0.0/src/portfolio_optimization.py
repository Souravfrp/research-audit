"""
Minimum-variance portfolio optimization for Quant AI Market Lab.

This module constructs a long-only, fully invested portfolio
using the sample covariance matrix of historical simple returns.
"""

from pathlib import Path

import cvxpy as cp
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SIMPLE_RETURNS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "simple_returns.csv"
)

WINDOW_SIZE = 252


def load_simple_returns():
    """
    Load the validated daily simple-return matrix.
    """
    returns = pd.read_csv(
        SIMPLE_RETURNS_PATH,
        index_col=0,
        parse_dates=True,
    )

    if returns.empty:
        raise ValueError("The return dataset is empty.")

    if not returns.index.is_monotonic_increasing:
        raise ValueError("Return dates are not chronological.")

    if returns.index.has_duplicates:
        raise ValueError("Duplicate return dates detected.")

    if not np.isfinite(returns.to_numpy()).all():
        raise ValueError("Invalid return observations detected.")

    return returns


def estimate_covariance(returns):
    """
    Estimate covariance from a historical return window.
    """
    if len(returns) != WINDOW_SIZE:
        raise ValueError(
            f"Expected {WINDOW_SIZE} return observations."
        )

    covariance = returns.cov()

    matrix = covariance.to_numpy()

    if not np.allclose(
        matrix,
        matrix.T,
        atol=1e-12,
        rtol=0,
    ):
        raise ValueError("Covariance matrix is not symmetric.")

    minimum_eigenvalue = np.linalg.eigvalsh(
        matrix
    ).min()

    if minimum_eigenvalue < -1e-12:
        raise ValueError(
            "Covariance matrix is not positive semidefinite."
        )

    return covariance


def optimize_minimum_variance(covariance):
    """
    Solve the long-only minimum-variance portfolio problem.

    Minimize:
        w.T @ covariance @ w

    Subject to:
        sum(w) = 1
        w >= 0
    """
    matrix = covariance.to_numpy()

    number_of_assets = matrix.shape[0]

    weights = cp.Variable(number_of_assets)

    portfolio_variance = cp.quad_form(
        weights,
        cp.psd_wrap(matrix),
    )

    problem = cp.Problem(
        cp.Minimize(portfolio_variance),
        [
            cp.sum(weights) == 1,
            weights >= 0,
        ],
    )

    problem.solve(
        solver=cp.OSQP,
        eps_abs=1e-9,
        eps_rel=1e-9,
        max_iter=100000,
    )

    if problem.status != cp.OPTIMAL:
        raise RuntimeError(
            f"Optimization failed: {problem.status}"
        )

    optimal_weights = np.asarray(
        weights.value
    ).reshape(-1)

    if not np.isfinite(optimal_weights).all():
        raise RuntimeError("Invalid portfolio weights.")

    if abs(optimal_weights.sum() - 1) > 1e-7:
        raise RuntimeError(
            "Portfolio weights do not sum to one."
        )

    if optimal_weights.min() < -1e-7:
        raise RuntimeError(
            "Portfolio contains a negative weight."
        )

    return pd.Series(
        optimal_weights,
        index=covariance.index,
        name="Portfolio weight",
    )


def main():
    returns = load_simple_returns()

    historical_window = returns.iloc[
        :WINDOW_SIZE
    ]

    covariance = estimate_covariance(
        historical_window
    )

    weights = optimize_minimum_variance(
        covariance
    )

    estimated_variance = (
        weights.to_numpy()
        @ covariance.to_numpy()
        @ weights.to_numpy()
    )

    estimated_volatility = np.sqrt(
        estimated_variance
    ) * np.sqrt(252)

    print("\nMinimum-variance portfolio")
    print("--------------------------")

    print(
        "Estimation window:",
        historical_window.index.min().date(),
        "to",
        historical_window.index.max().date(),
    )

    print("\nPortfolio weights:")
    print(weights.to_string())

    print(
        "\nSum of weights:",
        weights.sum(),
    )

    print(
        "Minimum weight:",
        weights.min(),
    )

    print(
        "Estimated annualized volatility:",
        f"{estimated_volatility:.4%}",
    )


if __name__ == "__main__":
    main()
