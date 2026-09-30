# Walk-forward training-window selection

## Research question

Does retaining all available historical training data, using a fixed
rolling window, or selecting a window from past forecast errors produce
different five-day SPY RMS-risk forecasting results?

The training-window length is treated as an experimental choice rather
than assumed to be optimal.

## Experimental design

- Forecast dates: 2019-02-08 through 2026-04-23.
- Forecast target: RMS of SPY daily log returns over the next five
  trading days.
- Features: daily SPY log return, trailing 20-day SPY volatility,
  and same-day cross-asset return dispersion.
- Ridge alpha: 1.
- Models refitted on the first eligible forecast date of each month.
- Candidate training histories: the most recent 252, 504, 756, or
  1008 eligible examples, or all eligible examples (expanding).
- A training example is eligible only after its complete five-day
  target is observable at the refit date.

## Adaptive selection

At each monthly selection date, the algorithm calculates the MAE of
each candidate method using its most recent 252 completed forecasts.
It selects the candidate with the lowest historical MAE, breaking
exact ties by a fixed candidate order.

The first adaptive selection is 2020-03-02. Earlier candidate
forecasts supply its initial performance history.

The selected candidate supplies forecasts for the following monthly
block. Outcomes from that block are not used to select its method.

## Common-date evaluation

All six methods were evaluated on the same 1545 forecast dates,
2020-03-02 through 2026-04-23.

| Method | MAE | RMSE | Mean forecast error |
| --- | ---: | ---: | ---: |
| Rolling 252 | 0.004086 | 0.007246 | +0.000315 |
| Rolling 504 | 0.003781 | 0.006737 | +0.000098 |
| Rolling 756 | 0.003799 | 0.006668 | +0.000239 |
| Rolling 1008 | 0.003813 | 0.006693 | +0.000155 |
| Expanding | 0.003676 | 0.006511 | -0.000325 |
| Adaptive | 0.003715 | 0.006625 | -0.000198 |

The expanding-window method had lower aggregate MAE and RMSE than
the adaptive method during this evaluation. The experiment does not
establish that either method will perform better in future periods.

## Limitations

The five-day targets overlap, so neighboring forecast errors are
dependent. No statistical uncertainty interval has yet been
calculated for the differences between methods.

The candidate windows, monthly refitting, alpha, and 252-forecast
selection history are experimental design choices; this experiment
does not establish that they are optimal.

Historical evaluation results, including the later part of this
period, have been inspected during project development. These dates
must not be described as an untouched independent test.

The experiment forecasts future RMS risk, not return direction or
trading profitability.

## Reproduction

Generate the candidate forecasts using
`src/walk_forward_comparison.py`, then run:

`python -m src.walk_forward_evaluation`

The evaluation reads `results/walk_forward_forecasts.csv`.

## May–August 2026 fixed-cutoff evaluation

The original historical evaluation ended with forecasts dated
2026-04-23: their complete five-trading-day targets were observable
by the 2026-04-30 cutoff. The extended forecast timeline additionally
contains forecasts dated 2026-04-24 through 2026-04-30. These five
forecasts were not included in the original historical scores, but
their outcomes become available during May and can subsequently enter
the adaptive selector's completed-error history.

The later evaluation covers 79 forecast dates, 2026-05-01 through
2026-08-24. The final five-day target becomes observable on
2026-08-31, the last date in the available return dataset.

The candidate methods and selection rule were retained from the
historical experiment: rolling windows of 252, 504, 756, and 1008
eligible training examples; an expanding window; Ridge alpha of 1;
monthly refitting; and adaptive selection using the most recent
252 completed forecast errors. Forecasts are interpreted as being
made after the close of each forecast date. Monthly refits can use
training outcomes observable by that date, rather than freezing all
model coefficients at the April cutoff.

The adaptive selections were:

| Selection date | Selected method |
| --- | --- |
| 2026-05-01 | Rolling 504 |
| 2026-06-01 | Rolling 504 |
| 2026-07-01 | Expanding |
| 2026-08-03 | Rolling 756 |

All six methods were evaluated on the same 79 later forecast dates.

| Method | MAE | RMSE | Mean forecast error |
| --- | ---: | ---: | ---: |
| Rolling 252 | 0.002604 | 0.003220 | +0.000026 |
| Rolling 504 | 0.002969 | 0.003484 | +0.000962 |
| Rolling 756 | 0.002875 | 0.003414 | +0.000771 |
| Rolling 1008 | 0.002980 | 0.003494 | +0.001072 |
| Expanding | 0.003082 | 0.003732 | +0.001371 |
| Adaptive | 0.002954 | 0.003529 | +0.001050 |

Rolling 252 had the lowest observed MAE and RMSE in this later
period. Adaptive had lower MAE and RMSE than expanding, reversing
their aggregate relationship in the earlier historical evaluation.
These observations do not justify revising the candidate methods or
adaptive selection rule based on the later-period outcomes.

This is a fixed-cutoff, pseudo-out-of-sample walk-forward evaluation,
not a pristine untouched holdout: some May–August information had
previously been inspected during project development. The 79
forecast errors are also dependent because successive five-day
targets overlap. No uncertainty interval has been established for
the differences between methods.

### Reproduction of the later evaluation

Run `python -m src.later_walk_forward_evaluation`.

The module rebuilds the extended forecasts, checks the original
historical forecasts on their 1811 saved dates, verifies the later
adaptive selections, and compares the later predictions against
`results/later_walk_forward_forecasts.csv` before printing the scores.
It does not overwrite the original historical forecast CSV.

## April 2020 diagnostic

The adaptive selector chose rolling 756 at its 2020-04-01
selection date using the most recent 252 completed historical
forecast errors. Its choice did not use April forecast outcomes.

Across the 21 April 2020 forecast dates, rolling 756 had an
MAE of 0.020607, compared with 0.017249 for expanding.
Both methods overpredicted the realized five-day RMS target
on all 21 dates; rolling 756 produced a larger absolute
error on every date.

To examine the prediction difference, both Ridge models were
reconstructed using their eligible training examples at the
2020-04-01 refit. Their fitted coefficients were converted
from standardized feature coordinates to the same original
feature coordinates. For each April forecast date, the
rolling-minus-expanding prediction difference was decomposed as

    (a_rolling - a_expanding)
    + sum_j (b_rolling,j - b_expanding,j) * x_t,j

where a denotes the intercept, b denotes original-coordinate
feature slopes, and x_t denotes the observed feature vector.

The mean contributions across April were:

| Component | Mean contribution |
| --- | ---: |
| Intercept | -0.000382 |
| SPY return | +0.000094 |
| SPY 20-day volatility | -0.000245 |
| Cross-asset dispersion | +0.003890 |
| Total forecast difference | +0.003358 |

The reconstructed and direct prediction differences agreed
within numerical tolerance. Cross-asset dispersion supplied
the largest positive term in this algebraic decomposition,
partly offset by the intercept and volatility terms.

This analysis explains how the fitted models produced different
forecasts. It does not establish that cross-asset dispersion
caused the subsequent market outcomes or forecast errors.

The reproducible diagnostic is in
`src/april_2020_ridge_diagnostic.py`; its figure is saved as
`results/april_2020_ridge_diagnostic.png`.


## Coefficient stability of the rolling 504 model

I also examined how the fitted coefficients of the rolling
504-observation Ridge model changed across its 87 monthly refits,
from 2019-02-08 to 2026-04-01. I used the same historical
training-date schedule and Ridge parameter as in the walk-forward
experiment.

All 87 refits gave a negative coefficient for the current SPY log
return and positive coefficients for trailing SPY volatility and
cross-asset dispersion. The signs were consistent, although the
coefficient magnitudes varied.

| Feature | Minimum standardized coefficient | Median | Maximum |
| --- | ---: | ---: | ---: |
| SPY log return | -0.001806 | -0.001057 | -0.000397 |
| SPY 20-day volatility | 0.000497 | 0.002785 | 0.005331 |
| Cross-asset dispersion | 0.000051 | 0.000755 | 0.004068 |

Because the feature scaler was fitted again at each monthly refit,
I also converted the coefficients to the original feature units.
For each refit, I used

\[
b_j = \frac{\beta_j}{s_j},
\qquad
a = \beta_0 - \sum_j b_j\mu_j,
\]

where \(\beta_j\) is the coefficient for a standardized feature,
and \(\mu_j\) and \(s_j\) are that refit's training mean and scale.
The resulting expression, \(a+\sum_j b_jx_j\), reproduced the fitted
model's prediction on each refit date. The maximum absolute
reconstruction difference across the 87 dates was
\(6.939\times10^{-18}\).

This analysis shows that the directions of the fitted relationships
were consistent across these historical refits, while their
magnitudes were not constant. It covers the rolling 504-observation
specification only. The coefficients describe the model's
predictions conditional on its other inputs; they do not establish
causal relationships or guarantee the same signs in future refits.

To reproduce this analysis, run:

`python -m src.ridge_coefficient_stability`
