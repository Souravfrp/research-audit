# Fixed-cutoff three-state HMM evaluation

## Purpose and data

The HMM and scaler are fitted using historical observations
through April 30, 2026. Evaluation covers 84 observations
from May 1 through August 31, 2026.

The features are SPY daily log return, 20-day rolling SPY
volatility, and daily cross-asset return dispersion.
The final 19 historical returns provide rolling-window
context for the first later-period observations.
The historical scaler transforms the later features;
neither the scaler nor the HMM is fitted on later data.

## Evaluation method

Forward filtering uses the fixed HMM to calculate state
probabilities from observations available through each date.
The later conditional log-likelihood is the combined-sequence
log-likelihood minus the historical-sequence log-likelihood.
The forward calculation is checked against hmmlearn.

Run: `python -m src.regime_hmm_evaluation`

## Results

| Measure | Result |
| --- | ---: |
| Historical model seed | 10 |
| Later observations | 84 |
| Filtered state counts (0, 1, 2) | 23, 51, 10 |
| Mean filtered probabilities (0, 1, 2) | 0.2721, 0.5947, 0.1332 |
| Historical fitting log-likelihood per observation | -2.6082 |
| Later conditional log-likelihood per observation | -3.5132 |

## Limitations

Filtered probabilities use each date's observed returns.
They are not predictions made before those returns were known.
State labels are statistical descriptions, not verified
economic regimes. Historical fitting and later conditional
likelihoods are not directly comparable forecasting scores.
Their difference alone does not establish forecast accuracy,
trading profitability, or model failure.

Some later-period data had already been inspected during
exploratory analysis. This is a limited fixed-cutoff
evaluation, not a pristine untouched holdout.
