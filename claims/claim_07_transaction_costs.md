# Claim 7: Transaction-cost implementation

**Claim (from the frozen README, lines 18 and 359).** The portfolio backtests apply proportional transaction costs of 0, 5 and 10 basis points to the traded notional of each rebalance, deduct them from portfolio wealth, and report turnover and transaction expense.

**Status: supported for the tested cases by code inspection and isolated-function tests, with two input-validation gaps found in the audited function. The full backtest and its numerical results are not reproduced.**

## What I inspected

- `execute_rebalance` in `portfolio_backtest.py` (line 214) charges `cost_rate` times the absolute value of all purchases and sales. It finds the post-cost portfolio value `V'` from the self-financing equation
  `V' + c * sum(|V' * w - h|) = V`,
  where `V` is the value before trading, `w` the target weights, `h` the old holdings and `c` the cost rate. It solves this by bisection (100 steps, line 302) and then checks the accounting identity (line 355).
- For non-negative one-dimensional weights summing exactly to 1 and `0 <= c < 1`, the equation has exactly one solution. The left side increases in `V'`, with one-sided slopes at least `1 - c > 0`. Zero is below the root and `V` is at or above it, so the bisection bracket is valid. The numerical input check does not strictly enforce all these weight assumptions; the two documented validation gaps qualify this implementation claim.
- The backtest (`run_backtest`, line 367), the benchmark loop (`portfolio_benchmarks.py`, line 172) and the robustness analysis (`COST_BPS = 10`, line 21) all pass the cost rate to this function.
- The scenario counts follow from the code: 5 covariance methods x 3 cost rates = 15 optimized scenarios, and 3 benchmarks x 3 cost rates = 9 benchmark scenarios.

## What I tested

I loaded only `execute_rebalance` from the frozen file and tested it in [`tests/test_claim_07_transaction_costs.py`](../tests/test_claim_07_transaction_costs.py). The ten original tests pass. Two additional characterization tests also pass by demonstrating the current validation gaps; those tests do not certify the observed behaviour as correct.

| Test | Hand-worked answer |
|---|---|
| First purchase from cash | `V' = V / (1 + c)` |
| Full switch from one asset to another | `V' = V (1 - c) / (1 + c)` |
| No trade | Cost is 0 and value is unchanged |
| Zero cost rate | Value is unchanged |
| 1,000 random portfolios at 0, 5, 10 and 50 bp | `V' + cost = V`, `cost = c * traded value`, and the new holdings equal `V' * w` |
| Increasing the rate | Cost rises and final value falls |
| Invalid inputs | Negative or non-finite rates, rates of 10,000 bp or more, the tested bad-weight cases and negative holdings raise errors |
| Call chain | The cost rate reaches the function in the backtest, benchmarks and robustness code |

## What this does not show

- I tested the function in isolation. I did not run the full backtest, because the source data are not in the audit snapshot and the optimizer needs CVXPY. The numerical results (for example the portfolio values in the README) are not reproduced.
- The cost model is proportional only. It has no bid-ask spread, market impact, taxes, financing or short selling, so it should not be read as a full trading-cost model.
- The first purchase from cash also pays the cost, so a buy-and-hold benchmark starts below its nominal capital at 5 and 10 bp.
- "Turnover" in the code is the sum of absolute weight changes. A complete switch from one asset to another gives 2, not 1.

## Qualification from my local review on October 10

The ten original tests pass on the frozen isolated function. Two additional tests now preserve evidence of the unresolved input cases: slightly above-unit total weights are accepted through the default relative tolerance in `np.isclose`, and two-dimensional weights are accepted and can broadcast. I do not claim universal invalid-input rejection. The frozen source remains unchanged. The [local review](../docs/local_revision_review.md) explains these findings and the limits of the static call-chain checks.

The added tests are `test_current_near_unit_weights_are_accepted_and_overallocate` and `test_current_matrix_weights_are_accepted_and_change_cost`. They are characterization tests of known problems. If the audited implementation is corrected in a new snapshot, I should replace their current-behaviour assertions with rejection or corrected-accounting assertions; I should not preserve the defect just to keep these tests passing.
