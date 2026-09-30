# Random Forest for five-day SPY risk forecasting

## Research question

I wanted to test whether allowing nonlinear relationships between the
current market features and future SPY risk improves the forecasting
results obtained with Ridge regression.

I kept the forecasting problem unchanged. The target is the RMS of SPY
daily log returns over the next five trading days, and the inputs are:

- current SPY log return,
- trailing 20-day SPY volatility,
- same-day cross-asset return dispersion.

This keeps the comparison focused on the forecasting model rather than
changes in the data or target definition.

## Why I tested Random Forest

Ridge regression models the prediction as a linear combination of the
features. Random Forest provides a different modelling approach because
individual regression trees can divide the feature space into regions
and represent nonlinear relationships and interactions.

A Random Forest averages the predictions of many regression trees. I
used it here as an additional forecasting experiment rather than
assuming that a more flexible model would necessarily perform better.

## Chronological selection of model settings

I did not choose the Random Forest settings using the outer historical
validation period.

Instead, I reused the chronological training-only validation structure
from the Ridge alpha study. The original training period was divided
into three chronological folds.

For each fold, a training example was used only when its complete
five-day target was observable before the fold's validation dates.

The fold sizes were:

| Fold | Fitting examples | Validation examples |
| --- | ---: | ---: |
| 1 | 1121 | 338 |
| 2 | 1459 | 338 |
| 3 | 1797 | 451 |

For this initial experiment, I fixed the forest size at 100 trees and
compared four modest combinations of maximum tree depth and minimum
leaf size.

| Trees | Maximum depth | Minimum leaf size | Mean fold MAE | Mean fold RMSE |
| ---: | ---: | ---: | ---: | ---: |
| 100 | 3 | 10 | 0.004160 | 0.006944 |
| 100 | 5 | 10 | 0.004093 | 0.006835 |
| 100 | 5 | 20 | 0.004139 | 0.006925 |
| 100 | 8 | 20 | 0.004185 | 0.006962 |

With the number of trees fixed at 100, the candidate with maximum
depth 5 and minimum leaf size 10 had the lowest mean fold MAE and RMSE
among the four configurations I tested.

I therefore used this configuration for the historical comparison. I do
not treat it as a uniquely optimal Random Forest specification; it was
the strongest candidate within this small training-only comparison.

The model uses a fixed random seed of 42 so that the experiment is
reproducible.

## Historical validation comparison

After selecting the Random Forest settings from the training-only
folds, I fitted the model on the complete training period and evaluated
it on the same 565 historical validation dates used for the existing
baselines and Ridge model.

The validation period runs from 2024-01-23 through 2026-04-23.

| Method | MAE | RMSE |
| --- | ---: | ---: |
| Constant baseline | 0.003597 | 0.005924 |
| Rolling 20-day RMS | 0.003613 | 0.006217 |
| Ridge, alpha = 1 | 0.003201 | 0.005386 |
| Random Forest | 0.003443 | 0.005982 |

Random Forest had lower MAE than both simple baselines. Its RMSE was
lower than the rolling 20-day RMS baseline but slightly higher than the
constant baseline.

Ridge had lower MAE and RMSE than Random Forest during this historical
validation period.

This result does not show that Ridge will generally outperform Random
Forest. It only describes the observed results for this target, feature
set, model settings, and historical period.

## Interpretation

The Random Forest experiment allows nonlinear relationships between the
three market features and future five-day SPY risk, but the additional
model flexibility did not improve on Ridge in this historical
comparison.

This is useful because it gives me a direct comparison between a linear
regularized model and a nonlinear tree-based model while keeping the
forecasting target, features, and evaluation dates fixed.

The experiment therefore provides evidence about whether additional
model complexity was useful in this particular setting rather than
assuming that a more complicated model should perform better.


## Permutation importance

I also examined how much the fitted Random Forest relied on each
feature during the same 565-date historical validation period.

For each feature, I permuted its validation values 50 times while
keeping the fitted model fixed and measured the change in MAE.

| Feature | Mean increase in MAE | Standard deviation |
| --- | ---: | ---: |
| SPY 20-day volatility | 0.000624 | 0.000078 |
| SPY return | 0.000143 | 0.000043 |
| Cross-asset dispersion | -0.000005 | 0.000012 |

Recent SPY volatility had the largest permutation importance in this
experiment. SPY return had a smaller positive contribution.

The cross-asset-dispersion result is close to zero relative to its
permutation variability. I therefore interpret it as showing little
measurable standalone permutation importance in this validation sample,
not as evidence that dispersion is economically harmful or irrelevant.

Permutation importance measures the fitted model's reliance on a
feature conditional on the other available inputs. It does not measure
causation, and correlated features can share predictive information.

The reproducible analysis is implemented in:

`src/random_forest_permutation_importance.py`

Its numerical output is saved in:

`results/random_forest_permutation_importance.csv`

and the corresponding figure is:

`results/random_forest_permutation_importance.png`


## Limitations

The Random Forest settings were selected from only four candidate
configurations. This experiment does not establish that the chosen
settings are globally optimal.

The five-day target windows overlap, so neighboring forecast errors are
not independent.

The historical validation period has already been inspected during
project development and should not be described as a pristine untouched
test.

The experiment predicts future RMS risk. It does not predict return
direction or establish trading profitability.

Random Forest feature relationships should not be interpreted as causal
effects.

## Reproduction

The Random Forest fitting function is implemented in:

`src/random_forest_risk_forecasting.py`

The chronological training-only setting comparison is implemented in:

`src/random_forest_validation.py`

Run:

`python -m src.random_forest_validation`

The historical model comparison is produced by:

`python -m src.risk_forecast_comparison`

The comparison figure is saved as:

`results/risk_forecast_validation_comparison.png`