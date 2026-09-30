# Portfolio optimization, backtesting, and validation

This document describes the existing historical portfolio experiment. It complements `mathematics_optimization_algorithms.md`, which covers the earlier statistical modeling and SPY forecasting stages. The portfolio study is **retrospective** and distinct from the May–August 2026 SPY forecast evaluation. It is not a live or untouched out-of-sample test.

## 1. Research question and inputs

How do alternative historical covariance estimation windows affect the allocations, realized performance, trading turnover, and cost sensitivity of long-only minimum-variance portfolios across eight ETFs?

The universe is EEM, GLD, IWM, QQQ, SPY, TLT, USO, and VNQ. The pipeline originally computes both daily log returns and daily simple returns from adjusted prices in `src/compute_returns.py`. The standalone optimizer reads `data/processed/simple_returns.csv`. The historical backtest instead loads `data/processed/log_returns.csv` and converts it to simple returns via `expm1`; the two representations should be checked for numerical agreement when reproducing results. Local raw and processed data are excluded from Git.

For asset i on date t, simple return is R_{i,t} = P_{i,t}/P_{i,t-1} - 1. For portfolio weights w held over the next return interval, portfolio simple return before trading costs is R_{p,t} = sum_i w_{i,t-1} R_{i,t}. A weighted sum of *asset log returns* is not generally the exact simple or log return of a rebalanced portfolio.

The backtest restricts its historical data to observations dated on or before **2026-04-30** (`HISTORICAL_CUTOFF` in `src/portfolio_backtest.py`). It is separate from the later May–August 2026 SPY risk-forecasting evaluation.

## 2. Covariance estimation and optimization

For an eligible decision date t and an estimation window of m completed observations, let X_t be the m-by-n matrix of historical daily **simple** returns and let X_{c,t} denote its column-centered version. The sample covariance estimator is

\[\widehat\Sigma_t = \frac{1}{m-1}X_{c,t}^{\mathsf T}X_{c,t}.\]

The estimator is symmetric and positive semidefinite in exact arithmetic, since v^T \widehat\Sigma_t v = ||X_{c,t}v||_2^2/(m-1) >= 0. The implementation checks symmetry and minimum eigenvalue numerically, allowing small floating-point tolerance. It evaluates rolling windows of **252, 504, 756, and 1008** completed observations, and an **expanding** window using all observations through each decision date. These window methods are alternative historical specifications, not an independently selected winning strategy.

At decision date t, the optimizer solves

\[\min_{w\in\mathbb R^8}\; w^{\mathsf T}\widehat\Sigma_t w\quad\text{subject to }\mathbf 1^{\mathsf T}w=1,\;w_i\geq 0.\]

The covariance objective is convex because the estimated covariance is positive semidefinite; the long-only and fully invested constraints are convex. `src/portfolio_backtest.py` solves the quadratic program with CVXPY/OSQP and verifies solver status, weight sum, finite weights, and the nonnegativity tolerance. Numerical residuals near zero are clipped and weights renormalized. `src/portfolio_optimization.py` provides a separate single-window demonstration: it uses the first 252 simple-return observations (2015-01-05 to 2016-01-04), not a complete backtest.

That demonstration reported estimated annualized volatility **7.7720%** and optimized estimated daily variance **2.397006435922423e-05** versus **5.847769400570346e-05** for equal weights on the same input covariance. A second 252-observation window (2025-08-29 to 2026-08-31) reported optimized variance **1.6576714209933225e-05** versus equal-weight variance **4.7355460753861046e-05**. These are **in-sample estimated-variance checks**, not guarantees about later realized risk.

## 3. Chronological execution and portfolio accounting

`get_monthly_decision_dates` chooses eligible month-end trading sessions after the initial 1008-observation history. For the verified historical run there are **87 monthly decision dates**, from **2019-01-31** to **2026-03-31**. At each decision date t, `run_backtest` estimates covariance from the return history **through t** and generates target weights only after t's close. The order for the next session is: existing holdings earn that session's return, then the pending rebalance executes at the **next session's close**. Newly purchased holdings do not receive the earlier part of the execution session's return. Between monthly trades the portfolio is buy-and-hold and weights drift with prices.

The first execution is 2019-02-01. The 1820 *computed daily portfolio returns* span 2019-02-04 through 2026-04-30. The first recorded equity level is post-initial-execution and includes the initial purchase expense, if any. Daily return standard deviation therefore excludes the one-off deduction at initial purchase; total return on the initial 100000 units includes it. The backtest assumes executable next-session adjusted closing prices and does not model intraday liquidity, slippage beyond the assumed proportional cost, taxes, financing, or market impact.

Let V_before denote holdings plus cash immediately before rebalance, h_i old asset values, w_i target weights, and c = cost_bps/10000. `execute_rebalance` solves for post-cost wealth V_after through the self-financing equation

\[V_{\rm after}+c\sum_i|V_{\rm after}w_i-h_i|=V_{\rm before}.\]

The implementation uses bisection and checks the accounting identity. Target holdings become V_after w_i; cash is set to zero. The experiment compares **0, 5, and 10 basis points per unit of absolute traded notional**, rather than treating the basis-point figure as an annual management fee. Turnover is the sum of absolute changes in weights compared with the pre-trade portfolio; reported *rebalancing turnover* omits the initial purchase in the overall backtest summary.

## 4. Historical evaluation and benchmarks

All five minimum-variance methods were run at each of the three cost assumptions: **15 scenarios**. The comparison benchmarks are equally weighted buy-and-hold, equally weighted monthly rebalancing, and SPY buy-and-hold. They share the same initial nominal capital (**100000**), evaluation dates, next-session-close execution convention, and proportional-cost scenarios. The benchmarks were run for **9 scenarios**. The nominal unit is not a claim about an INR account.

For the verified 0-bps run, the five optimized portfolios ended at 200065.77 (rolling 252), 204323.60 (rolling 504), 208357.79 (rolling 756), 205073.73 (rolling 1008), and 195766.86 (expanding). The three 0-bps benchmarks ended at 228956.45 (equal-weight buy-and-hold), 236838.19 (equal-weight monthly), and 296706.25 (SPY buy-and-hold). These are realized outcomes for one historical sample and do not justify choosing a covariance window solely by its terminal wealth. The optimizer minimizes *estimated variance*, not expected-return shortfall or negative returns.

At 10 bps, terminal values for rolling 252, 504, 756, 1008, and expanding were respectively 197820.12, 203046.59, 207333.35, 204199.60, and 195081.57. Transaction costs reduced final capital in the verified scenarios. Reported statistics include final capital, total return, realized annualized volatility (`std(daily_returns, ddof=1)*sqrt(252)`), maximum drawdown from the running equity peak, turnover, and accumulated transaction expense. Initial transaction cost must be included separately when reconciling the full-period result with compounded *post-inception* daily portfolio returns.

## 5. Subperiod robustness and checks

`src/portfolio_robustness.py` reuses the existing eight strategy simulations at **10 bps**, splitting the daily evaluation into four non-overlapping periods: 2019–2020 (483 days), 2021–2022 (503), 2023–2024 (502), and 2025–April 2026 (332). This produces **32 strategy-period observations**. The implementation checks that subperiod growth compounded from post-initial-cost equity reproduces each full-period final value, and that period transaction expenses reconcile with the total expense. All eight strategy reconciliations and the 32-result check passed in the recorded local run. `docs/portfolio_robustness_findings.md` discusses results and the unequal length of the final period.

The verified 15-scenario backtest printed `PASS: All 15 transaction-cost scenarios completed` and `PASS: Original zero-cost baseline preserved`; the benchmark run printed `PASS: All nine benchmark scenarios completed` and `PASS: Original benchmark results preserved`. These checks reproduce expected historical numbers and inspect accounting consistency. They are **not** independent tests of every modeling assumption, exchange execution feasibility, future performance, or every possible source of look-ahead bias. Hard-coded expected results may need carefully documented updates if the upstream data vendor revises historical adjusted prices.

## 6. Reproduction and file map

Run from the repository root in the existing `quant-ai` environment after reconstructing the local data according to the project data-ingestion instructions:

```bash
python -m src.portfolio_optimization
python -m src.portfolio_backtest
python src/portfolio_benchmarks.py
python src/portfolio_robustness.py
```

The two direct-file commands above follow the **current** import convention in the benchmark and robustness scripts (`from portfolio_backtest import ...`). Running those two as `python -m src.portfolio_benchmarks` or `python -m src.portfolio_robustness` currently may fail without import-path changes. Do not interpret this import-path error as a statistical-model failure.

Related implementations: `src/compute_returns.py`, `src/portfolio_optimization.py`, `src/portfolio_backtest.py`, `src/portfolio_benchmarks.py`, `src/portfolio_robustness.py`, and the portfolio visualization modules. Related write-ups: `docs/mathematics_optimization_algorithms.md`, `docs/portfolio_robustness_findings.md`, and the separate forecasting documents. The calculation and reconciliation outputs recorded above were observed during the September 2026 local review; this document does not claim a new execution or an untouched forward test.

## 7. Method and software attribution

- The minimum-variance quadratic objective is an application of portfolio variance and covariance-based allocation; see Markowitz, H. (1952), *Portfolio Selection*, *The Journal of Finance* 7(1), 77–91, DOI: https://doi.org/10.2307/2975974. The project's specific eight-ETF restrictions, windows, trading convention and historical comparisons are its own experimental design; the model is not a full expected-return mean–variance efficient-frontier study.
- Convex modeling and quadratic-program solution: CVXPY documentation, https://www.cvxpy.org/ ; OSQP documentation, https://osqp.org/docs/ .
- Data transformations and sample covariance: pandas `DataFrame.pct_change` and `DataFrame.cov`, https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.pct_change.html and https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.cov.html ; NumPy `expm1`, https://numpy.org/doc/stable/reference/generated/numpy.expm1.html .
- Adjusted-price data source and provider limitations: `docs/references.md` (Yahoo Finance / yfinance).

These references identify established methods and software; they do not imply external validation of the project's numerical results. No citation is offered for a claim about an external source that was not actually used in the project.

## 8. Limitations and follow-up audit items

Results depend on the selected asset universe, dates, vendor-adjusted data, price-execution convention, estimation windows, costs and rebalancing schedule. Because the historical results have already been inspected during development, comparisons between the five windows are retrospective. The May–August 2026 forecasting period must not be repurposed as an untouched portfolio holdout. More rigorous checks could include independent unit tests of execution timing and cost accounting, a comparison of saved versus reconstructed simple returns, portfolio performance under alternative trading assumptions, and a frozen-method test on genuinely later observations.
