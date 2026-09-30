# References and Data Sources

This document records external data sources, software libraries, papers,
documentation, and methodological references used in Quant AI Market Lab.

References are added as they are actually used in the project.

## Market Data

### Yahoo Finance / yfinance

Historical market data used in the project are retrieved programmatically
through the open-source `yfinance` Python package.

- yfinance documentation:
  https://ranaroussi.github.io/yfinance/

- yfinance source repository:
  https://github.com/ranaroussi/yfinance

The project uses `yfinance.download()` to retrieve historical market data
for the selected cross-asset universe.

`yfinance` is not affiliated with or endorsed by Yahoo. Usage of downloaded
market data is subject to the applicable provider terms. The data in this
repository are used for research, educational, and portfolio-demonstration
purposes.

## Software

The implemented analysis uses NumPy, pandas, scikit-learn, CVXPY,
OSQP, hmmlearn, matplotlib, and yfinance, among other Python dependencies.
The forecasting comparison currently uses Ridge and Random Forest.
Packages present in an environment snapshot are not necessarily part of
reported experiments. XGBoost, SHAP, and Streamlit are not results of the
current research version; they remain possible later extensions.

Methodological references appear below and in the relevant project notes.


## Principal Component Analysis

### Methodological Reference

The PCA formulation, including variance-maximizing orthogonal directions,
eigendecomposition, and explained variance, is supported by:

- Jolliffe, I. T., and Cadima, J. (2016).
  "Principal component analysis: a review and recent developments."
  *Philosophical Transactions of the Royal Society A*,
  374(2065), 20150202.
  DOI: 10.1098/rsta.2015.0202

### Numerical Implementation

The PCA implementation uses symmetric eigendecomposition through
`numpy.linalg.eigh`. This routine is appropriate for real symmetric matrices
such as covariance and correlation matrices.

- NumPy documentation: `numpy.linalg.eigh`
  https://numpy.org/doc/stable/reference/generated/numpy.linalg.eigh.html


## Market-Regime Baseline: Standardization and KMeans

### Feature Standardization

The regime-feature matrix is standardized before Euclidean-distance-based
KMeans clustering so that differences in numerical scale do not cause one
feature to dominate the distance calculation.

The implementation uses `sklearn.preprocessing.StandardScaler`.

- scikit-learn documentation: `StandardScaler`
  https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html

### KMeans Clustering

KMeans is used as a geometric baseline for partitioning the standardized
market-condition feature space. The project does not assume that the
resulting clusters are automatically genuine or persistent market regimes.

The implementation uses `sklearn.cluster.KMeans` with `k-means++`
initialization, multiple initializations, and a fixed random state for
reproducibility.

- scikit-learn documentation: `KMeans`
  https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html

The initialization strategy is based on:

- Arthur, D., and Vassilvitskii, S. (2007).
  "k-means++: The Advantages of Careful Seeding."
  Proceedings of the Eighteenth Annual ACM-SIAM Symposium on Discrete
  Algorithms (SODA), pp. 1027-1035.

### Cluster Diagnostics

Candidate cluster counts are compared using the silhouette score.
Initialization stability of the selected baseline partition is checked
using the Adjusted Rand Index (ARI).

- scikit-learn documentation: `silhouette_score`
  https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_score.html

- scikit-learn documentation: `adjusted_rand_score`
  https://scikit-learn.org/stable/modules/generated/sklearn.metrics.adjusted_rand_score.html

## Hidden Markov Models

### HMM Methodology

The temporal regime experiment uses a Gaussian Hidden Markov Model (HMM)
to represent an observed market-feature sequence through an underlying
sequence of latent states with transition probabilities and
state-dependent Gaussian emissions.

A standard methodological reference for the HMM framework, likelihood
evaluation, state decoding, and parameter estimation is:

- Rabiner, L. R. (1989).
  "A Tutorial on Hidden Markov Models and Selected Applications in
  Speech Recognition."
  *Proceedings of the IEEE*, 77(2), 257-286.
  DOI: 10.1109/5.18626

### Gaussian HMM Implementation

The implementation uses `hmmlearn.hmm.GaussianHMM`.

The project uses the library for:

- Gaussian-emission HMM fitting,
- full and diagonal covariance specifications,
- sequence log-likelihood evaluation,
- Viterbi state decoding,
- posterior state probabilities,
- and convergence diagnostics.

- hmmlearn documentation:
  https://hmmlearn.readthedocs.io/

- GaussianHMM API documentation:
  https://hmmlearn.readthedocs.io/en/stable/api.html

### Model Comparison

Candidate HMM specifications are compared using multiple random
initializations, sequence likelihood, AIC, BIC, chronological validation,
rolling-origin validation, and state-occupancy diagnostics.

The use of multiple initializations and AIC/BIC for Gaussian HMM model
comparison is also illustrated in the official hmmlearn documentation:

- hmmlearn example: Using AIC and BIC for Model Selection
  https://hmmlearn.readthedocs.io/en/stable/auto_examples/plot_gaussian_model_selection.html

The project's manual Gaussian-HMM parameter count was additionally checked
against the parameter-count implementation in the installed `hmmlearn`
version 0.3.3 before documenting the AIC and BIC calculations.


## Portfolio Optimization and Historical Backtesting

### Minimum-Variance Portfolio Optimization

The project minimizes estimated portfolio variance subject to
long-only and fully invested constraints.

The covariance-based portfolio formulation is related to:

- Markowitz, H. (1952).
  "Portfolio Selection."
  The Journal of Finance, 7(1), 77-91.
  DOI: https://doi.org/10.2307/2975974

The project uses its own eight-ETF universe, historical
estimation windows, trading conventions, and validation
procedures. It does not implement a complete expected-return
mean-variance efficient-frontier study.

### Convex Optimization Software

The minimum-variance quadratic program is formulated
using CVXPY and solved using OSQP.

- CVXPY documentation:
  https://www.cvxpy.org/

- OSQP documentation:
  https://osqp.org/docs/

### Covariance Estimation and Return Transformations

The historical portfolio experiment estimates sample
covariance matrices from daily simple returns.

- pandas DataFrame.cov documentation:
  https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.cov.html

- pandas DataFrame.pct_change documentation:
  https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.pct_change.html

- NumPy expm1 documentation:
  https://numpy.org/doc/stable/reference/generated/numpy.expm1.html

The historical backtest converts previously computed
daily log returns into simple returns using NumPy expm1.

### Historical Backtesting and Transaction Costs

The project uses monthly portfolio decisions followed by
next-session closing-price execution.

Transaction costs are modeled as a proportional expense
on absolute traded notional.

The chronological execution convention, self-financing
transaction-cost equation, and numerical validation
procedures are documented in:

- docs/portfolio_mathematics_and_validation.md

The corresponding implementations are:

- src/portfolio_optimization.py
- src/portfolio_backtest.py
- src/portfolio_benchmarks.py

### Subperiod Robustness

The historical evaluation is divided into four subperiods
to examine the variation of portfolio performance across
different market conditions.

The experimental design, numerical results, reconciliation
checks, and limitations are documented in:

- docs/portfolio_robustness_findings.md
- docs/portfolio_mathematics_and_validation.md

The corresponding implementation is:

- src/portfolio_robustness.py

## Attribution Principle

External ideas, datasets, software, documentation, and adapted
implementations are acknowledged where appropriate. Mathematical
derivations, modeling choices, experiments, validation, interpretation,
and project-specific implementation are documented separately as part of
the project's own quantitative research workflow.
