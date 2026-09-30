"""
Chronological minimum-variance portfolio backtesting.

Research experiment:
- Eight ETFs.
- Five historical covariance estimation methods.
- Long-only, fully invested portfolio.
- Monthly portfolio decisions.
- Next-session closing-price execution.
- Buy-and-hold between monthly rebalancing events.
- No transaction costs in the initial baseline.

Historical evaluation ends on April 30, 2026.
"""

from pathlib import Path

import cvxpy as cp
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

LOG_RETURNS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "log_returns.csv"
)

HISTORICAL_CUTOFF = pd.Timestamp("2026-04-30")

INITIAL_CAPITAL = 100000.0

TRADING_DAYS_PER_YEAR = 252

COVARIANCE_METHODS = {
    "Rolling 252": 252,
    "Rolling 504": 504,
    "Rolling 756": 756,
    "Rolling 1008": 1008,
    "Expanding": None,
}


def load_simple_returns():
    """
    Load the existing daily log returns and convert
    them into daily simple returns.
    """

    log_returns = pd.read_csv(
        LOG_RETURNS_PATH,
        index_col=0,
        parse_dates=True,
    ).sort_index()

    returns = np.expm1(log_returns)

    historical = returns.loc[
        returns.index <= HISTORICAL_CUTOFF
    ].copy()

    if not historical.index.is_unique:
        raise RuntimeError(
            "Duplicate return dates detected."
        )

    if not historical.index.is_monotonic_increasing:
        raise RuntimeError(
            "Return dates are not chronological."
        )

    if not np.isfinite(
        historical.to_numpy()
    ).all():
        raise RuntimeError(
            "Non-finite return observations detected."
        )

    if not (historical > -1).all().all():
        raise RuntimeError(
            "Invalid simple returns detected."
        )

    if historical.shape[1] != 8:
        raise RuntimeError(
            "Expected eight ETF return series."
        )

    return historical


def get_monthly_decision_dates(historical):
    """
    Identify the final observed trading date
    of each eligible historical month.
    """

    eligible = historical.iloc[1008:]

    monthly_dates = (
        eligible.groupby(
            eligible.index.to_period("M")
        )
        .apply(
            lambda group: group.index[-1]
        )
    )

    if len(monthly_dates) != 88:
        raise RuntimeError(
            "Unexpected number of monthly decision dates."
        )

    # The final April 2026 decision cannot be
    # executed within the historical evaluation period.

    decision_dates = pd.DatetimeIndex(
        monthly_dates.iloc[:-1].to_numpy()
    )

    return decision_dates


def optimize_portfolio(history, window_length):
    """
    Solve the long-only minimum-variance problem
    using covariance estimated from historical
    simple returns.
    """

    if window_length is None:
        estimation_data = history
    else:
        estimation_data = history.tail(window_length)

    sigma = estimation_data.cov().to_numpy()

    if not np.isfinite(sigma).all():
        raise RuntimeError(
            "Non-finite covariance matrix."
        )

    if not np.allclose(
        sigma,
        sigma.T,
        atol=1e-12,
    ):
        raise RuntimeError(
            "Covariance matrix is not symmetric."
        )

    if np.linalg.eigvalsh(sigma).min() < -1e-12:
        raise RuntimeError(
            "Covariance matrix is not positive semidefinite."
        )

    n_assets = history.shape[1]

    weights_variable = cp.Variable(n_assets)

    problem = cp.Problem(
        cp.Minimize(
            cp.quad_form(
                weights_variable,
                sigma,
            )
        ),
        [
            cp.sum(weights_variable) == 1,
            weights_variable >= 0,
        ],
    )

    problem.solve(
        solver="OSQP",
        eps_abs=1e-9,
        eps_rel=1e-9,
        max_iter=100000,
    )

    if problem.status != cp.OPTIMAL:
        raise RuntimeError(
            f"Optimization failed: {problem.status}"
        )

    weights = np.asarray(
        weights_variable.value
    ).ravel()

    if not np.isfinite(weights).all():
        raise RuntimeError(
            "Non-finite portfolio weights."
        )

    if (
        abs(weights.sum() - 1) > 1e-7
        or weights.min() < -1e-7
    ):
        raise RuntimeError(
            "Portfolio constraints violated."
        )

    # Remove numerical negative-zero residuals.

    weights = np.maximum(weights, 0.0)

    weights = weights / weights.sum()

    return weights




def execute_rebalance(
    asset_values,
    cash,
    target_weights,
    cost_bps=0.0,
):
    """
    Calculate a self-financing portfolio rebalance.

    Transaction costs are proportional to the
    absolute monetary value of asset purchases
    and sales.

    The cost is deducted from portfolio wealth.
    """

    asset_values = np.asarray(
        asset_values,
        dtype=float,
    )

    target_weights = np.asarray(
        target_weights,
        dtype=float,
    )

    if not np.isfinite(asset_values).all():
        raise ValueError(
            "Non-finite asset values."
        )

    if (
        not np.isfinite(cash)
        or cash < 0
        or np.any(asset_values < 0)
    ):
        raise ValueError(
            "Invalid portfolio holdings."
        )

    if (
        not np.isfinite(cost_bps)
        or cost_bps < 0
        or cost_bps >= 10000
    ):
        raise ValueError(
            "Invalid transaction-cost rate."
        )

    if (
        len(asset_values) != len(target_weights)
        or not np.isfinite(target_weights).all()
        or np.any(target_weights < 0)
        or not np.isclose(
            target_weights.sum(),
            1.0,
            atol=1e-10,
        )
    ):
        raise ValueError(
            "Invalid target portfolio weights."
        )

    total_value = asset_values.sum() + cash

    if total_value <= 0:
        raise ValueError(
            "Portfolio value must be positive."
        )

    cost_rate = cost_bps / 10000.0

    if cost_rate == 0:
        post_cost_value = total_value

    else:
        # Solve the self-financing equation:
        #
        # V_after + cost_rate *
        # sum(abs(V_after * w - old_holdings))
        # = V_before
        #
        # The new allocation is fully invested
        # after transaction costs.

        lower = 0.0
        upper = total_value

        for _ in range(100):

            midpoint = (lower + upper) / 2.0

            proposed_holdings = (
                midpoint * target_weights
            )

            traded_value = np.abs(
                proposed_holdings - asset_values
            ).sum()

            required_value = (
                midpoint
                + cost_rate * traded_value
            )

            if required_value > total_value:
                upper = midpoint
            else:
                lower = midpoint

        post_cost_value = (
            lower + upper
        ) / 2.0

    new_asset_values = (
        post_cost_value * target_weights
    )

    traded_value = np.abs(
        new_asset_values - asset_values
    ).sum()

    transaction_cost = (
        cost_rate * traded_value
    )

    old_weights = (
        asset_values / total_value
    )

    turnover = np.abs(
        target_weights - old_weights
    ).sum()

    if not np.isclose(
        post_cost_value + transaction_cost,
        total_value,
        rtol=1e-10,
        atol=1e-7,
    ):
        raise RuntimeError(
            "Portfolio accounting identity failed."
        )

    return {
        "Asset values": new_asset_values,
        "Portfolio value": post_cost_value,
        "Transaction cost": transaction_cost,
        "Traded value": traded_value,
        "Turnover": turnover,
    }


def run_backtest(
    historical,
    decision_dates,
    window_length,
    cost_bps=0.0,
):
    """
    Simulate monthly portfolio rebalancing.

    A signal is generated after the decision-date
    close and executed at the following session's
    closing price.

    Existing holdings earn their daily returns
    before the next allocation is executed.

    Proportional transaction costs are applied at execution
    when cost_bps is nonzero.
    """

    dates = historical.index

    n_assets = historical.shape[1]

    asset_values = np.zeros(
        n_assets,
        dtype=float,
    )

    cash = INITIAL_CAPITAL

    pending_weights = None

    execution_date = None

    records = []

    trades = []

    for position, date in enumerate(dates):

        if date < decision_dates[0]:
            continue

        daily_returns = historical.loc[
            date
        ].to_numpy(dtype=float)

        # Existing holdings earn the current
        # trading day's returns.

        asset_values *= 1.0 + daily_returns

        # Execute the pending allocation
        # at the current session's close.

        if execution_date == date:

            if pending_weights is None:
                raise RuntimeError(
                    "Missing pending portfolio weights."
                )

            execution = execute_rebalance(
                asset_values=asset_values,
                cash=cash,
                target_weights=pending_weights,
                cost_bps=cost_bps,
            )

            asset_values = execution["Asset values"]
            cash = 0.0

            trades.append({
                "Execution date": date,
                "Turnover": execution["Turnover"],
                "Portfolio value": execution["Portfolio value"],
                "Transaction cost": execution["Transaction cost"],
                "Traded value": execution["Traded value"],
            })

            pending_weights = None

            execution_date = None

        # Generate a new portfolio signal
        # using historical information through today.

        if date in decision_dates:

            history = historical.loc[:date]

            pending_weights = optimize_portfolio(
                history,
                window_length,
            )

            next_position = position + 1

            if next_position >= len(dates):
                raise RuntimeError(
                    "No subsequent execution date."
                )

            execution_date = dates[next_position]

            if execution_date <= date:
                raise RuntimeError(
                    "Invalid execution chronology."
                )

        total_value = (
            asset_values.sum() + cash
        )

        records.append({
            "Date": date,
            "Portfolio value": total_value,
        })

    equity = pd.DataFrame(
        records
    ).set_index("Date")

    trades = pd.DataFrame(trades)

    if len(trades) != len(decision_dates):
        raise RuntimeError(
            "Unexpected number of portfolio executions."
        )

    if pending_weights is not None:
        raise RuntimeError(
            "An unexecuted portfolio signal remains."
        )

    first_execution = trades[
        "Execution date"
    ].iloc[0]

    equity = equity.loc[
        equity.index >= first_execution
    ]

    daily_portfolio_returns = (
        equity["Portfolio value"]
        .pct_change()
        .dropna()
    )

    if not np.isfinite(
        daily_portfolio_returns
    ).all():
        raise RuntimeError(
            "Non-finite portfolio returns."
        )

    return (
        equity,
        daily_portfolio_returns,
        trades,
    )


def summarize_backtest(
    method,
    equity,
    daily_returns,
    trades,
):
    """
    Calculate historical portfolio performance
    and trading statistics.
    """

    final_capital = equity[
        "Portfolio value"
    ].iloc[-1]

    total_return = (
        final_capital / INITIAL_CAPITAL - 1
    )

    realized_volatility = (
        daily_returns.std(ddof=1)
        * np.sqrt(TRADING_DAYS_PER_YEAR)
    )

    running_peak = equity[
        "Portfolio value"
    ].cummax()

    drawdown = (
        equity["Portfolio value"]
        / running_peak
        - 1
    )

    maximum_drawdown = drawdown.min()

    rebalancing_turnover = (
        trades["Turnover"].iloc[1:].sum()
    )

    return {
        "Method": method,
        "Final capital": final_capital,
        "Total return": total_return,
        "Annualized volatility": realized_volatility,
        "Maximum drawdown": maximum_drawdown,
        "Rebalancing turnover": rebalancing_turnover,
        "Executions": len(trades),
    }



def main():
    """
    Compare five covariance estimation methods under
    zero, five and ten basis points of transaction costs.
    """

    historical = load_simple_returns()

    decision_dates = get_monthly_decision_dates(
        historical
    )

    cost_scenarios = [0, 5, 10]

    results = []

    print(
        "Historical cutoff:",
        HISTORICAL_CUTOFF.date(),
    )

    print(
        "First decision date:",
        decision_dates[0].date(),
    )

    print(
        "Last evaluated decision date:",
        decision_dates[-1].date(),
    )

    print(
        "Monthly decisions:",
        len(decision_dates),
    )

    for cost_bps in cost_scenarios:

        print(
            f"\nTRANSACTION COST: {cost_bps} bps"
        )

        for method, window_length in COVARIANCE_METHODS.items():

            equity, daily_returns, trades = run_backtest(
                historical,
                decision_dates,
                window_length,
                cost_bps=cost_bps,
            )

            summary = summarize_backtest(
                method,
                equity,
                daily_returns,
                trades,
            )

            if len(trades) != 87:
                raise RuntimeError(
                    "Unexpected number of executions."
                )

            if len(daily_returns) != 1820:
                raise RuntimeError(
                    "Unexpected evaluation period."
                )

            transaction_expense = (
                trades["Transaction cost"].sum()
            )

            if transaction_expense < 0:
                raise RuntimeError(
                    "Negative transaction expense."
                )

            results.append({
                "Cost (bps)": cost_bps,
                "Method": method,
                **summary,
                "Transaction expense": transaction_expense,
            })

            print(
                f"{method}: "
                f"final capital = "
                f"{summary['Final capital']:,.2f}, "
                f"transaction expense = "
                f"{transaction_expense:,.2f}"
            )

    comparison = pd.DataFrame(results)

    baseline = comparison.loc[
        comparison["Cost (bps)"] == 0
    ].set_index("Method")["Final capital"]

    expected_baseline = {
        "Rolling 252": 200065.774455,
        "Rolling 504": 204323.603226,
        "Rolling 756": 208357.787908,
        "Rolling 1008": 205073.725451,
        "Expanding": 195766.864260,
    }

    for method, expected in expected_baseline.items():

        actual = baseline.loc[method]

        if abs(actual - expected) > 0.01:
            raise RuntimeError(
                f"Zero-cost baseline changed: {method}"
            )

    comparison["Capital reduction"] = (
        comparison["Method"].map(baseline)
        - comparison["Final capital"]
    )

    if (
        comparison["Capital reduction"] < -0.01
    ).any():
        raise RuntimeError(
            "Transaction costs unexpectedly increased "
            "final portfolio wealth."
        )

    print("\nTRANSACTION-COST COMPARISON")

    columns = [
        "Cost (bps)",
        "Method",
        "Final capital",
        "Total return",
        "Annualized volatility",
        "Maximum drawdown",
        "Rebalancing turnover",
        "Transaction expense",
        "Capital reduction",
    ]

    print(
        comparison[columns].to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    print(
        "\nPASS: All 15 transaction-cost "
        "scenarios completed."
    )

    print(
        "PASS: Original zero-cost baseline preserved."
    )


if __name__ == "__main__":
    main()
