"""Historical subperiod robustness analysis for portfolio strategies."""

import numpy as np
import pandas as pd

from portfolio_backtest import (
    INITIAL_CAPITAL,
    COVARIANCE_METHODS,
    load_simple_returns,
    get_monthly_decision_dates,
    run_backtest,
)

from portfolio_benchmarks import (
    equal_weight_portfolio,
    single_asset_portfolio,
    run_benchmark,
)


COST_BPS = 10

PERIODS = {
    "2019-2020": ("2019-02-01", "2020-12-31"),
    "2021-2022": ("2021-01-01", "2022-12-31"),
    "2023-2024": ("2023-01-01", "2024-12-31"),
    "2025-2026": ("2025-01-01", "2026-04-30"),
}

EXPECTED_FINAL_VALUES = {
    "Rolling 252": 197820.124590,
    "Rolling 504": 203046.588185,
    "Rolling 756": 207333.353281,
    "Rolling 1008": 204199.599064,
    "Expanding": 195081.574501,
    "Equal-weight buy-and-hold": 228727.720066,
    "Equal-weight monthly": 235897.555803,
    "SPY buy-and-hold": 296409.838440,
}


def calculate_subperiod_metrics(daily_returns, trades, start, end):
    """Calculate performance using the existing chronological backtest."""

    selected = daily_returns.loc[start:end]

    if selected.empty:
        raise ValueError(f"No evaluation returns from {start} to {end}")

    growth = float((1.0 + selected).prod())
    period_return = growth - 1.0

    volatility = float(
        selected.std(ddof=1) * np.sqrt(252)
    )

    # Include opening wealth when measuring subperiod drawdown.
    relative_wealth = np.concatenate(
        (
            [1.0],
            (1.0 + selected).cumprod().to_numpy(),
        )
    )

    running_peak = np.maximum.accumulate(relative_wealth)

    max_drawdown = float(
        np.min(relative_wealth / running_peak - 1.0)
    )

    period_trades = trades.loc[
        (trades["Execution date"] >= pd.Timestamp(start))
        & (trades["Execution date"] <= pd.Timestamp(end))
    ]

    return {
        "Days": len(selected),
        "Return (%)": 100.0 * period_return,
        "Volatility (%)": 100.0 * volatility,
        "Max drawdown (%)": 100.0 * max_drawdown,
        "Turnover": float(period_trades["Turnover"].sum()),
        "Transaction expense": float(
            period_trades["Transaction cost"].sum()
        ),
        "Growth factor": growth,
    }


def build_simulations(historical, decision_dates):
    """Reuse the five optimized strategies and three benchmarks."""

    simulations = {}

    for method, window_length in COVARIANCE_METHODS.items():
        simulations[method] = run_backtest(
            historical=historical,
            decision_dates=decision_dates,
            window_length=window_length,
            cost_bps=COST_BPS,
        )

    assets = historical.columns.tolist()

    benchmarks = {
        "Equal-weight buy-and-hold": (
            equal_weight_portfolio(assets),
            False,
        ),
        "Equal-weight monthly": (
            equal_weight_portfolio(assets),
            True,
        ),
        "SPY buy-and-hold": (
            single_asset_portfolio(assets, "SPY"),
            False,
        ),
    }

    for name, (weights, monthly) in benchmarks.items():
        simulations[name] = run_benchmark(
            historical=historical,
            decision_dates=decision_dates,
            target_weights=weights,
            rebalance_monthly=monthly,
            cost_bps=COST_BPS,
        )

    return simulations


def run_robustness_analysis():
    """Return validated subperiod results for all eight strategies."""

    historical = load_simple_returns()
    decision_dates = get_monthly_decision_dates(historical)

    simulations = build_simulations(
        historical,
        decision_dates,
    )

    rows = []

    for name, (equity, daily_returns, trades) in simulations.items():

        initial_post_cost_value = float(
            equity["Portfolio value"].iloc[0]
        )

        final_value = float(
            equity["Portfolio value"].iloc[-1]
        )

        initial_cost = float(
            trades["Transaction cost"].iloc[0]
        )

        assert len(daily_returns) == 1820

        assert np.isclose(
            initial_post_cost_value + initial_cost,
            INITIAL_CAPITAL,
            atol=1e-7,
        ), f"{name}: initial investment did not reconcile"

        assert np.isclose(
            final_value,
            EXPECTED_FINAL_VALUES[name],
            atol=0.01,
        ), f"{name}: final value changed"

        growth_factors = []
        period_expenses = []
        period_day_counts = []

        for period, (start, end) in PERIODS.items():

            metrics = calculate_subperiod_metrics(
                daily_returns,
                trades,
                start,
                end,
            )

            growth_factors.append(metrics["Growth factor"])
            period_expenses.append(metrics["Transaction expense"])
            period_day_counts.append(metrics["Days"])

            rows.append({
                "Strategy": name,
                "Period": period,
                "Days": metrics["Days"],
                "Return (%)": metrics["Return (%)"],
                "Volatility (%)": metrics["Volatility (%)"],
                "Max drawdown (%)": metrics["Max drawdown (%)"],
                "Turnover": metrics["Turnover"],
                "Transaction expense": metrics["Transaction expense"],
            })

        reconstructed_final_value = (
            initial_post_cost_value * np.prod(growth_factors)
        )

        assert sum(period_day_counts) == 1820

        assert np.isclose(
            reconstructed_final_value,
            final_value,
            atol=1e-7,
        ), f"{name}: subperiod wealth did not reconcile"

        assert np.isclose(
            sum(period_expenses),
            trades["Transaction cost"].sum(),
            atol=1e-7,
        ), f"{name}: transaction expenses did not reconcile"

        print(
            f"PASS: {name} | "
            f"final value {final_value:,.2f} | "
            "wealth and expenses reconciled"
        )

    comparison = pd.DataFrame(rows)

    assert len(comparison) == 32
    assert comparison["Strategy"].nunique() == 8
    assert comparison["Period"].nunique() == 4

    assert (
        comparison.groupby("Strategy")["Days"].sum() == 1820
    ).all()

    return comparison


def main():
    comparison = run_robustness_analysis()

    print("\nSUBPERIOD ROBUSTNESS COMPARISON — 10 BPS\n")

    print(
        comparison.to_string(
            index=False,
            float_format=lambda value: f"{value:.4f}",
        )
    )

    print(
        "\nPASS: All eight strategies and "
        "32 strategy-period results validated."
    )


if __name__ == "__main__":
    main()
