# Five-day SPY risk forecasting: baseline experiment

## Research question

Can information available at the end of trading day t
help estimate SPY's daily return magnitude over the
following five trading days?

The target is the root mean square (RMS) of SPY log
returns on days t+1 through t+5. It is not the
conventional sample standard deviation.

## Chronological validation

- Internal training: 2,253 eligible examples.
- Internal validation: 565 examples, starting 2024-01-23.
- Fixed historical cutoff: 2026-04-30.
- A separate, subsequent walk-forward Ridge experiment evaluates
  79 forecast dates from 2026-05-01 through 2026-08-24.

Training examples whose five-day target windows enter
validation are excluded. The 79-date results belong to the
monthly-refitted Ridge methods, not to a later evaluation
of the two baselines reported in this note. See
`docs/walk_forward_window_selection.md`.

## Baselines

- Constant: average target from internal training only.
- Rolling: RMS of the latest 20 observed SPY returns.

Both methods forecast the same five-day target on
identical validation dates.

## Internal validation results

| Method | MAE | RMSE | Mean error |
| --- | ---: | ---: | ---: |
| Constant | 0.003597 | 0.005924 | +0.000617 |
| Rolling 20-day RMS | 0.003613 | 0.006217 | +0.000511 |

The constant forecast had slightly lower MAE and RMSE
in this validation period. This does not establish
that it performs better in every market period.

## Limitations

Consecutive five-day targets overlap, so forecast
errors are not independent. This experiment evaluates
simple forecasting baselines, not trading profitability.

Run: `python -m src.risk_forecasting`
