# Portfolio Subperiod Robustness Analysis

## Research question

How consistently do five historical covariance estimation methods perform
across different market periods, and how do their results compare with
equal-weight and SPY benchmarks?

This is a retrospective analysis of an existing backtest. It is not an
untouched out-of-sample evaluation.

## Experimental setup

The study uses eight ETFs: EEM, GLD, IWM, QQQ, SPY, TLT, USO, and VNQ.

The five long-only, fully invested minimum-variance portfolios use rolling
covariance estimation windows of 252, 504, 756, and 1008 trading observations,
or an expanding estimation window.

The benchmarks are equal-weight buy-and-hold, monthly rebalanced equal-weight,
and SPY buy-and-hold.

Initial capital is 100,000 nominal accounting units. The analysis uses a
10-basis-point transaction-cost assumption. The first portfolio execution
occurs on February 1, 2019; daily evaluation returns run from February 4,
2019, through April 30, 2026.

The four fixed, non-overlapping calendar periods contain:

| Period | Daily evaluation returns |
|---|---:|
| 2019–2020 | 483 |
| 2021–2022 | 503 |
| 2023–2024 | 502 |
| 2025–April 2026 | 332 |
| **Total** | **1,820** |

Each subperiod's cumulative return compounds the daily returns from the
existing chronological simulation. The initial purchase expense is accounted
for separately when reconciling subperiod growth with the full-period return.

## Historical findings

All five minimum-variance portfolios experienced negative cumulative returns
during 2021–2022. Rolling 252 returned approximately -10.69% over that period,
while the other four covariance methods returned between approximately
-13.67% and -14.97%.

Rolling 252 also incurred more turnover than the longer-window methods during
2021–2022: approximately 2.75, compared with 0.62–1.20 for the other methods.

The relative returns of the covariance methods changed across periods.
For example, Rolling 252 returned approximately 31.82% in 2023–2024 and
24.60% in the shorter 2025–April 2026 period. Rolling 1008 returned
approximately 25.14% and 39.99% over those respective periods.

Across the four evaluated periods, the minimum-variance portfolios had lower
realized annualized volatility than the three benchmarks. This describes the
observed historical results; it is not a guarantee of future volatility.

## Validation

The saved analysis in `src/portfolio_robustness.py` reproduces 32 results:
eight strategies across four periods. For every strategy, compounded
subperiod growth reconciles with the original final portfolio value, and
subperiod transaction expenses reconcile with the original backtest.

## Limitations

- This is a retrospective comparison, not an untouched out-of-sample test.
- The results depend on the selected ETFs, estimation methods, historical
  sample, rebalance schedule, and simplified transaction-cost assumptions.
- The final subperiod ends on April 30, 2026, and is shorter than the others;
  its cumulative return should not be compared with two-year returns as though
  their durations were equal.
- The initial purchase expense is excluded from compounded daily subperiod
  returns but included when measuring the full-period return on initial capital.
- Transaction costs are modeled, but taxes, financing, market impact, and
  currency conversion are not.
- The assets are US-listed ETFs; the accounting units should not be interpreted
  as Indian rupees without an explicit currency-conversion model.
- The covariance window must not be selected solely because it generated
  the highest terminal wealth in this historical experiment.

## Next research question

How sensitive are these findings to transaction costs, portfolio turnover,
and the choice of evaluation period? Any subsequent method selection should
use a clearly specified validation procedure rather than treating this
retrospective comparison as an untouched test.
