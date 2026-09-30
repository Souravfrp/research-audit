# Five-day SPY risk forecasting: provisional Ridge model

## Research question

Does combining current market features improve forecasts
of SPY's future five-trading-day daily-return RMS compared
with our constant and rolling-RMS baselines?

The target and chronological dates are defined in
`docs/risk_forecasting_baselines.md`.

## Why Ridge regression?

Ridge provides an interpretable multivariable benchmark.
Its L2 penalty can reduce coefficient sensitivity when
features are correlated. Its fitting objective is a
convex quadratic optimization problem.

This is an initial trained model, not a claim that a
linear model is the correct description of market risk.

For training targets y_i and standardized feature vectors z_i,
the fitted model minimizes

    sum_i (y_i - beta_0 - z_i^T beta)^2
    + alpha * ||beta||_2^2

over the intercept beta_0 in R and the slope vector beta in R^3.
The intercept is not penalized. This is a convex quadratic
optimization problem in four model parameters. The fitted
objective is penalized training squared error; the later
validation MAE and RMSE are separate evaluation metrics.

## Inputs and fitting

Features: current SPY log return, SPY 20-day rolling
sample volatility, and cross-asset return dispersion.

The feature scaler and Ridge coefficients are fitted
on the 2,253 internal training examples only.

The original model used `alpha=1.0` provisionally.
A subsequent training-only study compared alpha values
0, 1, 10, 100, and 1000 using three chronological folds.
Alpha values 0, 1, and 10 produced nearly identical mean
fold MAE at the reported precision. We retained alpha=1
as a reproducible, weakly regularized setting, not as a
uniquely established optimum. See
`docs/ridge_alpha_validation.md`.

## Historical validation

Validation starts on 2024-01-23 and contains 565
forecast dates.

| Method | MAE | RMSE | Mean error |
| --- | ---: | ---: | ---: |
| Constant baseline | 0.003597 | 0.005924 | +0.000617 |
| Rolling 20-day RMS | 0.003613 | 0.006217 | +0.000511 |
| Provisional Ridge | 0.003201 | 0.005386 | +0.000167 |

Ridge had lower MAE and RMSE than both baselines in
this historical validation period. This observation
does not establish performance in other periods.

The 565 validation forecasts were nonnegative.

## Limitations and next questions

Five-day target windows overlap, so neighboring forecast
errors are dependent. The features may be correlated,
and fitted coefficients should not be interpreted as
causal effects.

Ridge does not enforce nonnegative predictions generally,
even though this validation run produced none.

This original fixed-fit Ridge model has not been
separately evaluated on the May-August 2026 period.
The subsequent walk-forward experiment instead refits
Ridge monthly under fixed rolling and expanding training
histories, with an additional past-error-based adaptive
selector. Its later-period results must not be attributed
to the original fixed-fit model. See
`docs/walk_forward_window_selection.md`.

Some May-August 2026 information was inspected during
project development; the later walk-forward evaluation
is therefore not an untouched holdout. Its outcomes
must not be used to revise the model settings while
presenting the same period as independent confirmation.

Run: `python -m src.ridge_risk_forecasting`
