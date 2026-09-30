"""
Portfolio benchmarks for Quant AI Market Lab.

Benchmark strategies:
1. Equal-weight buy-and-hold.
2. Equal-weight monthly rebalancing.
3. SPY buy-and-hold.

All benchmarks use the same eight-ETF universe
as the minimum-variance portfolio experiment.
"""

import numpy as np
import pandas as pd


def equal_weight_portfolio(assets):
    """
    Return an equally weighted allocation
    across the supplied assets.
    """

    n_assets = len(assets)

    if n_assets == 0:
        raise ValueError(
            "The asset universe cannot be empty."
        )

    weights = np.full(
        n_assets,
        1.0 / n_assets,
    )

    return weights


def single_asset_portfolio(
    assets,
    selected_asset,
):
    """
    Allocate the entire portfolio
    to one specified asset.
    """

    if selected_asset not in assets:
        raise ValueError(
            f"{selected_asset} is not in the asset universe."
        )

    weights = np.zeros(
        len(assets),
        dtype=float,
    )

    selected_index = assets.index(
        selected_asset
    )

    weights[selected_index] = 1.0

    return weights


def validate_weights(weights):
    """
    Validate a long-only, fully invested
    portfolio allocation.
    """

    weights = np.asarray(
        weights,
        dtype=float,
    )

    if not np.isfinite(weights).all():
        raise RuntimeError(
            "Non-finite portfolio weights."
        )

    if not np.isclose(
        weights.sum(),
        1.0,
        atol=1e-12,
    ):
        raise RuntimeError(
            "Portfolio weights do not sum to one."
        )

    if np.any(weights < 0):
        raise RuntimeError(
            "Negative portfolio weights detected."
        )

    return True


def run_benchmark(
    historical,
    decision_dates,
    target_weights,
    rebalance_monthly=False,
    cost_bps=0.0,
    initial_capital=100000.0,
):
    """
    Simulate a benchmark using next-session close execution.

    Existing positions earn their daily returns before
    trades are executed at the session's close.

    Buy-and-hold strategies trade only at inception.
    Monthly strategies rebalance after each decision date.
    """

    from portfolio_backtest import execute_rebalance

    validate_weights(target_weights)

    assets = historical.columns.tolist()
    weights = np.asarray(target_weights, dtype=float)

    if len(weights) != len(assets):
        raise ValueError("Asset and weight dimensions differ.")

    dates = historical.index

    first_decision = decision_dates[0]

    first_position = dates.get_loc(first_decision)

    if first_position + 1 >= len(dates):
        raise RuntimeError("No initial execution date.")

    first_execution = dates[first_position + 1]

    execution_dates = {first_execution}

    if rebalance_monthly:
        for decision_date in decision_dates[1:]:
            position = dates.get_loc(decision_date)

            if position + 1 >= len(dates):
                raise RuntimeError(
                    "No subsequent execution date."
                )

            execution_dates.add(dates[position + 1])

    asset_values = np.zeros(len(assets), dtype=float)
    cash = float(initial_capital)

    records = []
    trades = []

    for date in dates:

        if date < first_decision:
            continue

        daily_returns = historical.loc[
            date
        ].to_numpy(dtype=float)

        # Existing holdings earn the current day's return.
        asset_values *= 1.0 + daily_returns

        # Trades occur after the current day's return.
        if date in execution_dates:

            execution = execute_rebalance(
                asset_values=asset_values,
                cash=cash,
                target_weights=weights,
                cost_bps=cost_bps,
            )

            asset_values = execution["Asset values"]
            cash = 0.0

            trades.append({
                "Execution date": date,
                "Turnover": execution["Turnover"],
                "Transaction cost": execution["Transaction cost"],
                "Traded value": execution["Traded value"],
            })

        total_value = asset_values.sum() + cash

        records.append({
            "Date": date,
            "Portfolio value": total_value,
        })

    equity = pd.DataFrame(records).set_index("Date")

    equity = equity.loc[
        equity.index >= first_execution
    ]

    daily_portfolio_returns = (
        equity["Portfolio value"]
        .pct_change()
        .dropna()
    )

    trades = pd.DataFrame(trades)

    expected_executions = (
        len(decision_dates)
        if rebalance_monthly
        else 1
    )

    if len(trades) != expected_executions:
        raise RuntimeError(
            "Unexpected number of benchmark executions."
        )

    if len(daily_portfolio_returns) != 1820:
        raise RuntimeError(
            "Unexpected benchmark evaluation length."
        )

    if not np.isfinite(
        equity["Portfolio value"]
    ).all():
        raise RuntimeError(
            "Non-finite benchmark portfolio value."
        )

    return equity, daily_portfolio_returns, trades


def main():
    """Compare three benchmarks under three transaction-cost scenarios."""

    from portfolio_backtest import (
        load_simple_returns,
        get_monthly_decision_dates,
        summarize_backtest,
    )

    historical = load_simple_returns()
    decision_dates = get_monthly_decision_dates(historical)
    assets = historical.columns.tolist()

    benchmarks = {
        "Equal-weight buy-and-hold": (
            equal_weight_portfolio(assets), False
        ),
        "Equal-weight monthly": (
            equal_weight_portfolio(assets), True
        ),
        "SPY buy-and-hold": (
            single_asset_portfolio(assets, "SPY"), False
        ),
    }

    results = []

    for cost_bps in [0, 5, 10]:

        print(f"\nTRANSACTION COST: {cost_bps} bps")

        for name, (weights, monthly) in benchmarks.items():

            equity, daily_returns, trades = run_benchmark(
                historical=historical,
                decision_dates=decision_dates,
                target_weights=weights,
                rebalance_monthly=monthly,
                cost_bps=cost_bps,
            )

            summary = summarize_backtest(
                name, equity, daily_returns, trades
            )

            assert len(daily_returns) == 1820
            assert len(trades) == (87 if monthly else 1)

            results.append({
                "Cost (bps)": cost_bps,
                **summary,
                "Transaction expense":
                    trades["Transaction cost"].sum(),
            })

    comparison = pd.DataFrame(results)

    expected_zero_cost = {
        "Equal-weight buy-and-hold": 228956.45,
        "Equal-weight monthly": 236838.19,
        "SPY buy-and-hold": 296706.25,
    }

    for name, expected in expected_zero_cost.items():

        actual = comparison.loc[
            (comparison["Cost (bps)"] == 0)
            & (comparison["Method"] == name),
            "Final capital",
        ].iloc[0]

        assert abs(actual - expected) < 0.01

    print("\nBENCHMARK COMPARISON")

    print(
        comparison[
            [
                "Cost (bps)",
                "Method",
                "Final capital",
                "Total return",
                "Annualized volatility",
                "Maximum drawdown",
                "Transaction expense",
            ]
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    print("\nPASS: All nine benchmark scenarios completed.")
    print("PASS: Original benchmark results preserved.")


if __name__ == "__main__":
    main()
