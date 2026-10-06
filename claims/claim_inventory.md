# Claim inventory: Quant AI Market Lab v1.0.0

Scope: claims from `docs/portfolio_mathematics_and_validation.md`, checked against `src/portfolio_backtest.py`. I read the code but did not run it. The raw and processed data are not in this repository, so I could not reproduce any numbers. Labels below are provisional.

| ID | Claim | Where | Type | My label | Evidence |
|---|---|---|---|---|---|
| C01 | The backtest uses only data dated on or before 2026-04-30. | Doc line 13; code lines 29 and 59 | Code | Supported | `HISTORICAL_CUTOFF` is set to 2026-04-30 and the loader keeps rows with `index <= HISTORICAL_CUTOFF`. |
| C02 | Each month's covariance uses returns through the decision date only, with no look-ahead. | Doc line 33; `run_backtest`, decision step | Method | Supported | The code passes `historical.loc[:date]` to `optimize_portfolio`, which includes the decision date and nothing later. The window is cut from the end of that history. |
| C03 | The rebalance executes at the next session's close, after existing holdings earn that session's return. | Doc line 33; `run_backtest` | Method | Supported | Each day, returns are applied first. The execution date is the next row in the data, and the code stops if it is not later than the decision date. |
| C04 | The covariance objective is convex because the covariance matrix is positive semidefinite. | Doc line 27; `optimize_portfolio` | Maths | Supported, with a caveat | The code checks symmetry and that the smallest eigenvalue is at least -1e-12, then solves a long-only quadratic program with OSQP. The check allows a tiny numerical tolerance, so the matrix is positive semidefinite only up to that tolerance. |
| C05 | There are 87 monthly decision dates. | Doc line 33; `get_monthly_decision_dates` | Count | Supported | The code finds 88 month-ends after the first 1008 observations and drops the last one (April 2026) because it cannot be executed within the evaluation period, leaving 87. The doc does not mention that an 88th date was found and dropped. |
| C06 | Log returns are converted to simple returns with `expm1`. | Doc line 9; code line 56 | Maths | Supported | `np.expm1` is applied to the values read from the log-return file. It computes exp(x) - 1, which is the simple return for a log return x. |
| C07 | Transaction cost is charged per unit of absolute traded value, not as an annual fee. | Doc line 41; `execute_rebalance` | Code | Not yet checked | I have not read `execute_rebalance` (lines 214-366) yet. |
