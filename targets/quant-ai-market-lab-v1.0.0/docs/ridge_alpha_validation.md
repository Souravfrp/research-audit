# Ridge regularization: training-only validation

## Purpose

Investigate how Ridge regularization strength affects
five-day SPY RMS-risk forecasting errors.

The existing Ridge model uses alpha=1 provisionally.
This experiment compares alpha values without using
the previously examined outer validation period or
the later May-August 2026 evaluation period.

## Experimental design

Candidate alphas: 0, 1, 10, 100, 1000.

Three expanding-window chronological folds were constructed
within the 2,253 internal training forecast dates.

| Fold | Fit examples | Validation examples |
| --- | ---: | ---: |
| 1 | 1121 | 338 |
| 2 | 1459 | 338 |
| 3 | 1797 | 451 |

Five training examples were excluded at each fold boundary
because their five-day targets extended into that fold's
validation period.

The feature scaler and Ridge coefficients were fitted
separately on each fold's fitting observations.

## Mean validation errors across folds

| Alpha | Mean fold MAE | Mean fold RMSE |
| ---: | ---: | ---: |
| 0 | 0.003814 | 0.006043 |
| 1 | 0.003814 | 0.006044 |
| 10 | 0.003814 | 0.006047 |
| 100 | 0.003819 | 0.006085 |
| 1000 | 0.003992 | 0.006506 |

Alpha values 0, 1, and 10 had nearly identical errors
at the displayed precision. No one of these values had
the lowest MAE in every fold.

We retained alpha=1 for the current reproducible Ridge
baseline. This is not evidence that alpha=1 is uniquely
optimal or that Ridge will outperform simpler forecasts
in every future market period.

## Limitations

The five-day targets overlap, so neighboring validation
errors are dependent. The three folds cover different
historical periods but do not provide a formal uncertainty
interval for differences between alpha values.

The outer historical validation period was already examined
during development. May-August 2026 baseline results were
also previously inspected. Neither period was used in this
training-only alpha comparison.

Run: `python -m src.ridge_alpha_validation`
