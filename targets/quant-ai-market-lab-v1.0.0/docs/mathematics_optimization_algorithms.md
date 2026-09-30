# Mathematics, Optimization, and Algorithms

This document records the mathematical formulations, optimization viewpoints,
algorithmic reasoning, and computational decisions used throughout the
Quant AI Market Lab project.

The goal is to connect theoretical ideas with reproducible quantitative
implementation.

---

## 1. Market Data Representation

Let there be $n$ assets observed over $T_P$ trading dates, where $T_P$
denotes the number of price observations.
The adjusted-price data are represented as a matrix

$$
P =
\begin{pmatrix}
P_{1,1} & P_{2,1} & \cdots & P_{n,1} \\
P_{1,2} & P_{2,2} & \cdots & P_{n,2} \\
\vdots & \vdots & \ddots & \vdots \\
P_{1,T_P} & P_{2,T_P} & \cdots & P_{n,T_P}
\end{pmatrix}
\in \mathbb{R}^{T_P \times n}.
$$

For the current project,

$$
T_P = 2932,
\qquad
n = 8.
$$

The eight assets represent multiple market exposures rather than a single
asset class. This allows later analysis of cross-asset dependence,
covariance structure, principal components, market regimes, and portfolio
optimization.

### Data validation

Before statistical modeling, the data pipeline verifies:

1. the downloaded dataset is non-empty,
2. all requested assets are present,
3. the number of observations and assets is recorded,
4. missing observations are checked explicitly.

The current dataset satisfies

$$
N_{\mathrm{missing},i} = 0
\qquad
\text{for every asset } i.
$$

### Algorithmic viewpoint

If $n$ assets are requested, checking whether every requested asset is
present requires a scan over the asset universe.

At the asset level, this validation is approximately

$$
O(n).
$$

Operations performed over the entire price matrix generally scale with the
number of stored observations,

$$
O(Tn).
$$

### Optimization viewpoint

No optimization problem is solved during the data-ingestion stage.

The purpose of this stage is to construct and validate the numerical input
that will later generate quantities such as the estimated covariance matrix

$$
\hat{\Sigma},
$$

which will subsequently appear in convex portfolio-optimization problems.


---

## 2. Return Transformation

Financial price levels are transformed into returns before statistical
modeling.

For asset $i$, the one-period simple return is

$$
R_{i,t}
=
\frac{P_{i,t}}{P_{i,t-1}} - 1.
$$

The corresponding logarithmic return is

$$
r_{i,t}
=
\log\left(\frac{P_{i,t}}{P_{i,t-1}}\right)
=
\log P_{i,t} - \log P_{i,t-1}.
$$

Simple and logarithmic returns satisfy the exact identity

$$
r_{i,t} = \log(1 + R_{i,t}).
$$

This identity is used in the implementation as a numerical consistency
check.

### Temporal additivity of log returns

Log returns are additive across consecutive time periods. For example,

$$
\sum_{t=1}^{k} r_{i,t}
=
\log\left(\frac{P_{i,k}}{P_{i,0}}\right).
$$

This property is useful in quantitative time-series analysis.

### Return matrix

For each trading date, the cross-asset log-return vector is

$$
r_t =
\begin{pmatrix}
r_{1,t} \\
r_{2,t} \\
\vdots \\
r_{n,t}
\end{pmatrix}
\in \mathbb{R}^{n}.
$$

The validated price dataset contains $T_P=2932$ price observations for
$n=8$ assets. Because a one-period return requires both a current and previous price, define the number of return observations as

$$
T_R = T_P - 1 = 2931.
$$


Therefore,

$$
R_{\mathrm{simple}},
R_{\log}
\in
\mathbb{R}^{T_R \times n}
=
\mathbb{R}^{2931 \times 8}.
$$

### Numerical validation

The implementation verifies that:

1. the return matrices are non-empty,
2. no missing values remain,
3. all values are finite,
4. simple and logarithmic returns satisfy their mathematical relationship
   within a numerical tolerance.

The consistency condition is

$$
\max_{i,t}
\left|
\log(1 + R_{i,t}) - r_{i,t}
\right|
\leq 10^{-12}.
$$

The observed calculation satisfies this condition.

### Algorithmic viewpoint

Computing returns requires processing each observation for every asset.


For $T_P$ price observations and $n$ assets, the computational work is approximately

$$
O(T_P n).
$$

### Statistical viewpoint

The return observations will be used to estimate quantities such as the
sample mean vector

$$
\hat{\mu}
=
\frac{1}{T}
\sum_{t=1}^{T} r_t
$$

and sample covariance matrix

$$
\hat{\Sigma}
=
\frac{1}{T-1}
\sum_{t=1}^{T}
(r_t-\hat{\mu})(r_t-\hat{\mu})^\top.
$$

These quantities connect the preprocessing stage to exploratory analysis,
PCA, risk measurement, and portfolio construction.

### Optimization viewpoint

No optimization problem is solved during return computation.

However, the estimated covariance matrix derived from these returns will
later enter portfolio-risk objectives such as

$$
w^\top \hat{\Sigma} w,
$$

where $w$ denotes the vector of portfolio weights.

## 3. Historical Volatility Estimation

### Problem

For each asset, estimate the historical variability of daily log returns
and express that risk measure on an annualized scale.

Let $r_{i,t}$ denote the daily log return of asset $i$ on return
observation $t$, with $T_R = 2931$ return observations in the current
dataset.

### Mathematical formulation

The sample mean return of asset $i$ is

$$
\bar{r}_i
=
\frac{1}{T_R}
\sum_{t=1}^{T_R} r_{i,t}.
$$

The sample daily volatility is the sample standard deviation

$$
s_i
=
\sqrt{
\frac{1}{T_R-1}
\sum_{t=1}^{T_R}
(r_{i,t}-\bar{r}_i)^2
}.
$$

Using the conventional approximation of 252 trading days per year,
daily volatility is annualized as

$$
\hat{\sigma}_{i,\mathrm{annual}}
=
\sqrt{252}\,s_i.
$$

The square-root-of-time scaling follows from variance additivity under
appropriate assumptions. It is an annualization convention and does not
assert that real financial returns are perfectly independent or
identically distributed.

### Algorithmic viewpoint

For $n$ assets and $T_R$ return observations, computing the sample
standard deviation for every asset requires processing the return matrix
and has time complexity $O(T_R n)$.

### Optimization viewpoint

No optimization problem is solved in this stage. The volatility estimates
are descriptive risk statistics. Later portfolio optimization will use the
full covariance structure rather than individual asset volatilities alone.

### Empirical result

For the current sample, the estimated annualized historical volatilities
range from approximately 14.8% for TLT to 40.5% for USO. These values
describe historical return dispersion over the sample period and should
not be interpreted as forecasts of future risk.

## 4. Cross-Asset Correlation Analysis

### Problem

Individual asset volatility describes the variability of each return
series separately, but portfolio risk also depends on how different
assets move together.

For the current universe of $n=8$ assets, pairwise dependence is
measured using the Pearson correlation coefficient.

### Mathematical formulation

For assets $i$ and $j$, the sample correlation is

$$
\rho_{ij}
=
\frac{\operatorname{Cov}(r_i,r_j)}
{s_i s_j},
$$

where $s_i$ and $s_j$ are the sample standard deviations of the
corresponding daily log-return series.

The complete correlation matrix is

$$
C = [\rho_{ij}]_{i,j=1}^{n}.
$$

For the current asset universe,

$$
C \in \mathbb{R}^{8 \times 8}.
$$

A valid correlation matrix satisfies

$$
\rho_{ii}=1
$$

for every asset and

$$
\rho_{ij}=\rho_{ji},
$$

so that

$$
C=C^\top.
$$

Each correlation coefficient lies in the interval

$$
-1 \leq \rho_{ij} \leq 1.
$$

### Numerical validation

The computed matrix has shape $8\times8$.

The maximum observed symmetry error was

$$
\max_{i,j} |\rho_{ij}-\rho_{ji}| = 0,
$$

and the maximum diagonal error was also zero.

The observed correlation values ranged from approximately $-0.203$
to $1.000$, including the unit diagonal.

### Algorithmic viewpoint

Computing all pairwise correlations requires estimating relationships
between approximately $n^2$ pairs of assets across $T_R$ return
observations.

The resulting time complexity is approximately

$$
O(T_R n^2).
$$

The correlation matrix itself requires

$$
O(n^2)
$$

storage.

### Financial interpretation

The strongest observed correlation between two distinct assets is
approximately $0.932$ between SPY and QQQ, indicating strong historical
linear co-movement in their daily returns.

TLT exhibits mildly negative correlations with several equity exposures,
while GLD has relatively low correlations with many of the equity ETFs.

These relationships illustrate the statistical basis of diversification:
portfolio risk depends not only on individual asset volatility but also
on cross-asset dependence.

Correlation does not imply causation, and historical correlations are not
guaranteed to remain stable across future market regimes.

### Optimization viewpoint

The correlation analysis is descriptive and does not itself solve an
optimization problem.

However, correlations are closely related to the covariance matrix.
If $D$ is the diagonal matrix of asset standard deviations, then

$$
\Sigma = D C D.
$$

Portfolio variance can subsequently be written as

$$
\sigma_p^2
=
w^\top \Sigma w,
$$

where $w$ is the portfolio-weight vector.

Thus, cross-asset dependence provides a direct mathematical bridge from
exploratory analysis to portfolio optimization.
---

## 5. Covariance Matrix and Positive Semidefiniteness

### Problem

Correlation measures standardized dependence, but portfolio risk depends on both
cross-asset dependence and the individual scales of asset returns. Therefore,
the covariance matrix is required for later portfolio optimization.

### Mathematical Formulation

Let $X \in \mathbb{R}^{T_R \times n}$ denote the log-return matrix, where
$T_R$ is the number of return observations and $n$ is the number of assets.

After centering each asset return series, let $X_c$ denote the centered
return matrix. The sample covariance matrix is

$$
\hat{\Sigma}
=
\frac{1}{T_R-1}X_c^\top X_c.
$$

The covariance matrix is symmetric:

$$
\hat{\Sigma}=\hat{\Sigma}^\top.
$$

For every vector $x \in \mathbb{R}^n$,

$$
x^\top \hat{\Sigma}x
=
\frac{1}{T_R-1}\|X_cx\|_2^2
\geq 0.
$$

Therefore, $\hat{\Sigma}$ is positive semidefinite.

For the current dataset, the minimum eigenvalue was numerically

$$
\lambda_{\min}(\hat{\Sigma})
\approx 5.019\times10^{-6}>0,
$$

so the estimated covariance matrix is positive definite for this sample.

If $D$ is the diagonal matrix of sample standard deviations and $C$ is the
sample correlation matrix, then

$$
\hat{\Sigma}=DCD.
$$

The numerical reconstruction error in this identity was approximately

$$
5.421\times10^{-19},
$$

which is consistent with floating-point numerical precision.

### Optimization Viewpoint

For a portfolio-weight vector $w$, portfolio variance is

$$
w^\top\hat{\Sigma}w.
$$

Because $\hat{\Sigma}$ is positive semidefinite, this is a convex quadratic
function of $w$. This covariance structure will therefore become the risk
term in the later portfolio-optimization stage.

### Algorithmic Complexity

For $T_R$ return observations and $n$ assets, constructing the covariance
matrix requires approximately $O(T_R n^2)$ arithmetic operations and
$O(n^2)$ storage.
---

## 6. Principal Component Analysis of Standardized Returns

### Problem

The eight asset-return series are correlated, so their movements contain
redundant information. Principal Component Analysis (PCA) constructs
orthogonal directions that summarize the dominant linear variation in the
cross-asset return system.

Because the assets have substantially different volatility scales, PCA is
performed on standardized log returns rather than directly on the raw
covariance matrix. This prevents a high-volatility asset from dominating a
principal component solely because of its scale.

### Standardization

For asset $i$ at time $t$, define

$$
z_{t,i}
=
\frac{r_{t,i}-\bar{r}_i}{s_i},
$$

where $\bar{r}_i$ is the sample mean and $s_i$ is the sample standard
deviation of asset $i$.

The resulting standardized-return matrix $Z$ has approximately zero column
means and unit sample standard deviations.

Therefore,

$$
\operatorname{Cov}(Z)
=
\operatorname{Corr}(R),
$$

up to floating-point numerical precision.

In the implementation, the maximum absolute difference between these two
matrices was

$$
3.775\times10^{-15}.
$$

Thus, the PCA performed here can equivalently be interpreted as PCA on the
sample correlation matrix.

### Optimization Formulation

Let $C$ denote the covariance matrix of the standardized returns, which is
equivalently the sample correlation matrix of the original returns.

The first principal component direction solves

$$
\max_{v\in\mathbb{R}^n}
\quad
v^\top C v
$$

subject to

$$
v^\top v=1.
$$

This asks for the unit-length direction having maximum sample variance.

The Lagrangian is

$$
\mathcal{L}(v,\lambda)
=
v^\top C v
-
\lambda(v^\top v-1).
$$

Differentiating with respect to $v$ gives the first-order condition

$$
2Cv-2\lambda v=0,
$$

and therefore

$$
Cv=\lambda v.
$$

Hence, the principal-component directions are eigenvectors of $C$, and the
corresponding eigenvalues measure the variance captured along those
directions.

The first principal component corresponds to the largest eigenvalue.
Subsequent components solve the same variance-maximization problem subject
also to orthogonality with the previously selected component directions.

### Explained Variance

If

$$
\lambda_1\geq\lambda_2\geq\cdots\geq\lambda_n,
$$

then the explained-variance ratio of component $k$ is

$$
\mathrm{EVR}_k
=
\frac{\lambda_k}
{\sum_{j=1}^{n}\lambda_j}.
$$

For the current eight-asset dataset:

- PC1 explains approximately $50.53\%$ of standardized variance.
- PC1--PC2 cumulatively explain approximately $66.93\%$.
- PC1--PC3 cumulatively explain approximately $79.01\%$.

Thus, three orthogonal directions summarize approximately $79\%$ of the
sample's standardized cross-asset variation.

### Component-Weight Interpretation

The first component has relatively large same-sign coefficients for SPY,
QQQ, IWM, EEM, and VNQ. It therefore represents a broad equity/risk
co-movement direction in this sample.

The second component has its largest absolute coefficients in TLT and GLD,
while the equity coefficients are comparatively small. It captures a
different cross-asset direction dominated by bond and gold behavior.

The third component is dominated by USO and, to a lesser extent, GLD,
indicating a commodity-related direction in the sample.

These interpretations are statistical rather than causal. PCA identifies
directions of linear variation; it does not establish economic causation.

The overall sign of an eigenvector is arbitrary: if $v$ is an eigenvector,
then $-v$ represents the same principal-component direction. Therefore,
interpretation focuses on relative signs and coefficient magnitudes rather
than the absolute orientation of an eigenvector.

### Numerical Validation

The implementation validates that:

- the eigenvectors are orthonormal;
- the sum of the eigenvalues equals the trace of the PCA matrix;
- the explained-variance ratios sum to one.

Observed numerical errors were approximately

$$
\max |V^\top V-I|
=
6.661\times10^{-16},
$$

and

$$
\left|
\sum_i\lambda_i-\operatorname{tr}(C)
\right|
=
8.882\times10^{-16}.
$$

These values are consistent with floating-point numerical precision.

### Algorithm

The PCA implementation:

1. standardizes each asset's log-return series;
2. constructs the covariance matrix of the standardized returns;
3. computes the symmetric eigendecomposition using `numpy.linalg.eigh`;
4. sorts eigenvalues and eigenvectors in descending eigenvalue order;
5. computes explained-variance ratios;
6. validates orthogonality and trace preservation;
7. extracts the first three component directions for interpretation and
   visualization.

### Computational Complexity

Constructing the standardized covariance matrix requires approximately

$$
O(T_R n^2)
$$

operations.

The eigendecomposition of the resulting symmetric $n\times n$ matrix
requires approximately

$$
O(n^3)
$$

operations, with $O(n^2)$ matrix storage.

For this project, $n=8$, so the eigendecomposition is computationally small.
The same formulation, however, makes the scaling behavior explicit for larger
asset universes.



### Scalability and Computational Perspective

For the current universe of only $n=8$ assets, the direct covariance and
eigendecomposition approach is entirely appropriate. Introducing a more
complicated algorithm here would add unnecessary implementation complexity
without a meaningful computational benefit.

The complexity analysis becomes important when considering a substantially
larger asset universe. Covariance construction scales approximately as

$$
O(T_R n^2),
$$

while a full dense eigendecomposition scales approximately as

$$
O(n^3).
$$

Thus, increasing the number of assets can make both computation and
$O(n^2)$ matrix storage significantly more expensive.

If only the leading $k$ principal components are required, with
$k \ll n$, computing the complete eigendecomposition may perform more work
than necessary. For sufficiently large problems, iterative or truncated
methods can target only the dominant components rather than computing every
eigenpair.

This illustrates an algorithmic principle used throughout the project:
the mathematically correct formulation is considered together with its
computational cost, and more scalable alternatives are considered when the
problem size makes them necessary. Optimization of computation should be
motivated by an actual bottleneck rather than added solely for complexity.


### Predictive-Modeling Caveat

The current PCA is descriptive and uses the full historical sample. If PCA is
later used as part of a predictive model or backtest, the standardization
parameters and PCA directions must be estimated using only information
available at that historical time. Fitting them on future observations would
introduce look-ahead bias.

## 7. Market-Regime Feature Construction and Geometric Interpretation

### Research Question

Before choosing a clustering algorithm, I first need to define what I mean by
the "market condition" observed on a particular trading day.

The question is:

> Do the statistical characteristics of the eight ETF market exposures exhibit
> distinguishable states over time?

I do not begin by assuming that a particular clustering method will discover
genuine economic regimes. The first step is instead to construct a small set of
interpretable variables that describe different aspects of market behavior.

For each trading day $t$, I represent the market condition by the feature
vector

$$
x_t =
\begin{pmatrix}
r_{\mathrm{SPY},t} \\
\sigma_{\mathrm{SPY},t}^{(20)} \\
d_t
\end{pmatrix}.
$$

The three coordinates describe:

1. the daily SPY log return, representing broad-equity market movement;

2. the trailing 20-day volatility of SPY, representing the recent magnitude of
   market fluctuations;

3. the cross-asset dispersion of the eight ETF returns on that day, representing
   how differently the assets are moving from one another.


### Geometric Interpretation

The feature construction gives a geometric way to think about the problem.

Each trading day is represented by one point in a three-dimensional feature
space. The three coordinate axes correspond to return, recent volatility, and
cross-asset dispersion.

Therefore, instead of initially asking an algorithm to assign a regime label, I
can first inspect the geometry of the resulting point cloud.

If market conditions naturally form well-separated groups, the point cloud
should contain corresponding geometric structure. If the observations instead
form one continuous cloud with tails or outliers, a clustering algorithm may
still divide the observations, but those divisions should not automatically be
interpreted as genuine persistent market regimes.

This distinction is important because clustering algorithms can produce a
partition even when the underlying data do not contain naturally separated
groups.

### Construction of the Three Features

#### 1. Daily Broad-Market Return

The first coordinate is the SPY daily log return,

$$
r_{\mathrm{SPY},t}
=
\log\left(
\frac{P_{\mathrm{SPY},t}}
{P_{\mathrm{SPY},t-1}}
\right).
$$

SPY is used here as a simple and interpretable proxy for broad U.S. equity
market movement. A positive value represents an upward daily movement and a
negative value represents a downward daily movement.

This is not the only possible choice. Alternatives include an equal-weighted
return across the eight ETFs or a PCA-based common-market factor. I use SPY for
the initial baseline because its interpretation is direct and it does not
require estimating an additional model.

If a PCA score is later used as a predictive feature, the PCA transformation
must be fitted using historical data only. Using the previously computed
full-sample PCA directions would introduce future information into the
historical experiment.


#### 2. Trailing 20-Day Volatility

The second coordinate measures the recent variability of SPY returns.

For a window of $w=20$ trading days,

$$
\sigma_{\mathrm{SPY},t}^{(20)}
=
\sqrt{
\frac{1}{w-1}
\sum_{j=0}^{w-1}
\left(
r_{\mathrm{SPY},t-j}
-
\bar r_t^{(20)}
\right)^2
},
$$

where

$$
\bar r_t^{(20)}
=
\frac{1}{w}
\sum_{j=0}^{w-1}
r_{\mathrm{SPY},t-j}.
$$

The window is backward-looking: the feature at time $t$ uses observations
from $t-19$ through $t$, and therefore does not use future returns.

The first 19 observations cannot have a complete 20-day window. They are
therefore unavailable by construction rather than being treated as data
errors.

The 20-day window is a simple baseline corresponding approximately to one
trading month. It is not assumed to be an optimal volatility estimator.
Possible alternatives include other rolling-window lengths, exponentially
weighted volatility, or conditional-volatility models such as GARCH. Such
alternatives should be compared only when there is a clear modeling reason
rather than chosen because they produce visually cleaner regimes.


#### 3. Daily Cross-Asset Dispersion

The third coordinate measures how differently the eight ETF returns behave on
the same trading day.

For $n=8$ assets, first define the cross-sectional mean return

$$
\bar r_t
=
\frac{1}{n}
\sum_{i=1}^{n} r_{i,t}.
$$

The daily cross-asset dispersion is then

$$
d_t
=
\sqrt{
\frac{1}{n-1}
\sum_{i=1}^{n}
\left(
r_{i,t}-\bar r_t
\right)^2
}.
$$

Geometrically, consider the eight-dimensional return vector

$$
r_t =
(r_{1,t},\ldots,r_{n,t})^\top.
$$

The vector

$$
\bar r_t \mathbf{1}
$$

represents the point on the common-movement line where all assets have the
same return.

More precisely, define the one-dimensional common-movement subspace

$$
L=\{c\mathbf{1}:c\in\mathbb{R}\}.
$$

The vector

$$
\bar r_t\mathbf{1}
$$

is the orthogonal projection of $r_t$ onto $L$.

From the definition of $d_t$,

$$
\left\|
r_t-\bar r_t\mathbf{1}
\right\|_2^2
=
(n-1)d_t^2.
$$

Therefore,

$$
d_t
=
\frac{1}{\sqrt{n-1}}
\left\|
r_t-\bar r_t\mathbf{1}
\right\|_2.
$$

For the current universe of $n=8$ ETFs,

$$
\left\|
r_t-\bar r_t\mathbf{1}
\right\|_2
=
\sqrt{7}\,d_t.
$$

Thus, daily cross-asset dispersion has an exact geometric interpretation as a
scaled Euclidean distance from the common-movement subspace.

This is different from correlation. Dispersion is a cross-sectional quantity
computed for one trading day, whereas correlation measures statistical
co-movement between return series over multiple observations.


### Causality and Timing of the Features

All three baseline features are constructed using information available no
later than trading day $t$. No observation from $t+1$ or later is required.

The interpretation nevertheless depends on when the model is intended to be
used. Because the day-$t$ return and dispersion are known only after the
relevant day-$t$ prices are observed, these features describe the market
condition at or after that observation time. They can subsequently be used as
inputs for a next-period forecasting experiment, provided the temporal
ordering is preserved.

## 8. Feature Standardization Before KMeans

### Why Standardization Is Necessary

KMeans is based on Euclidean distances between observations and cluster
centroids. Therefore, the numerical scale of each coordinate directly affects
the geometry seen by the algorithm.

For two feature vectors $x$ and $y$,

$$
\|x-y\|_2^2
=
\sum_{j=1}^{d}(x_j-y_j)^2.
$$

A feature with a substantially larger numerical scale can contribute more to
this distance simply because of its units. This would implicitly give that
coordinate greater influence on the clustering.

To place the three regime features on comparable scales, each feature is
standardized using

$$
z_{t,j}
=
\frac{x_{t,j}-\mu_j}{s_j},
$$

where $\mu_j$ is the historical mean of feature $j$, and $s_j$ is its
historical standard deviation.

After standardization, each coordinate is centered near zero and has unit
variance on the data used to fit the transformation.


### Geometric Interpretation

Standardization changes the coordinate system in which distances are measured.

Subtracting the mean translates the point cloud so that its center is near the
origin. Dividing each coordinate by its standard deviation rescales the axes so
that one unit along each standardized axis represents approximately one
standard deviation of movement in that feature.

This is a diagonal affine transformation of the original feature space. It does
not make the features statistically independent and it does not remove their
correlations.

For example, the historical 20-day SPY volatility and cross-asset dispersion
have a positive sample correlation of approximately $0.529$. Standardizing
the two variables changes their units but does not remove this relationship.


### Historical-Only Fitting

The scaling parameters must respect the temporal structure of the experiment.

The mean and standard deviation used by the scaler are estimated from the
historical feature sample only. When later observations are evaluated, they
must be transformed using these frozen historical parameters rather than
refitting the scaler on the later period.

In symbolic form, if

$$
\mu_j^{\mathrm{hist}}
\quad\text{and}\quad
s_j^{\mathrm{hist}}
$$

are estimated from the historical period, then a later observation is
transformed as

$$
z_{t,j}^{\mathrm{later}}
=
\frac{
x_{t,j}^{\mathrm{later}}-\mu_j^{\mathrm{hist}}
}{
s_j^{\mathrm{hist}}
}.
$$

Using information from the later evaluation period to determine the scaling
parameters would leak future information into the model-development process.


### Numerical Validation

For the historical regime-feature matrix, the standardized feature means were
numerically close to zero,

$$
(-1.22\times10^{-17},
 -1.11\times10^{-16},
 -2.84\times10^{-16}),
$$

and the population standard deviations were

$$
(1,1,1).
$$

The very small deviations of the means from exactly zero are expected
floating-point effects rather than modeling errors.

The implementation also explicitly rejects non-finite feature values before
fitting the scaler and checks that the transformed values remain finite.

## 9. KMeans as a Geometric Baseline

### Objective

After standardization, each trading day is represented by a point

$$
z_t \in \mathbb{R}^3.
$$

For a chosen number of clusters $K$, KMeans seeks cluster assignments
$C_1,\ldots,C_K$ and centroids $\mu_1,\ldots,\mu_K$ that minimize the
within-cluster sum of squared Euclidean distances:

$$
\min_{C_1,\ldots,C_K,\mu_1,\ldots,\mu_K}
\sum_{k=1}^{K}
\sum_{z_t\in C_k}
\|z_t-\mu_k\|_2^2.
$$

In scikit-learn this objective value is reported as `inertia_`.

The objective gives KMeans a direct geometric interpretation: observations
assigned to the same cluster should lie relatively close to a common centroid.


### Assignment Step and Voronoi Geometry

For fixed centroids, each observation is assigned to its nearest centroid:

$$
c(t)
=
\arg\min_{k\in\{1,\ldots,K\}}
\|z_t-\mu_k\|_2^2.
$$

Geometrically, the centroids divide feature space into Voronoi cells. Each
Voronoi cell contains the points that are closer to one centroid than to any
other centroid.

For two centroids, the boundary between their cells is a hyperplane consisting
of points that are equally distant from the two centroids.

Therefore, KMeans produces a piecewise-linear geometric partition of the
standardized feature space.


### Why the Centroid Is the Mean

Suppose the observations assigned to one cluster are

$$
z_1,\ldots,z_m.
$$

For fixed cluster membership, KMeans chooses the centroid $\mu$ by minimizing

$$
f(\mu)
=
\sum_{i=1}^{m}\|z_i-\mu\|_2^2.
$$

Differentiating with respect to $\mu$,

$$
\nabla_\mu f(\mu)
=
2m\mu
-
2\sum_{i=1}^{m}z_i.
$$

Setting the gradient equal to zero gives

$$
\mu
=
\frac{1}{m}
\sum_{i=1}^{m}z_i.
$$

The Hessian is

$$
\nabla_\mu^2 f(\mu)=2mI,
$$

which is positive definite for a nonempty cluster. Therefore, the arithmetic
mean is the unique minimizer of the squared-distance objective for that fixed
cluster.

This explains mathematically why the KMeans centroid-update step uses the
within-cluster mean.


### Alternating Algorithm

KMeans alternates between two operations:

1. Assignment: assign every observation to its nearest current centroid.

2. Update: replace each centroid by the arithmetic mean of the observations
   currently assigned to that cluster.

Each step does not increase the KMeans objective. Because there are finitely
many possible cluster assignments, the procedure eventually reaches a stable
partition under the usual finite-data setting.

This does not imply that KMeans finds the globally optimal partition. The final
solution can depend on the initial centroids because the optimization problem
is non-convex.


### Initialization

The implementation uses `k-means++` initialization rather than selecting all
initial centroids uniformly at random.

The purpose of `k-means++` is to spread the initial centroids through the data
more carefully, reducing the chance of starting with several centroids in the
same dense region.

The implementation also uses

`n_init = 20`

so that multiple initializations are tried and the solution with the smallest
KMeans objective is retained.

A fixed `random_state` is used for reproducibility. Reproducibility does not
remove initialization sensitivity, so the final partition is also compared
across several different random seeds.


### Computational Complexity

Let

- $N$ be the number of observations,
- $K$ the number of clusters,
- $d$ the feature dimension,
- $I$ the number of KMeans iterations.

A standard assignment step computes distances from approximately every
observation to every centroid, requiring roughly

$$
O(NKd)
$$

operations per iteration.

Over $I$ iterations, one run therefore has approximate complexity

$$
O(NKdI).
$$

If several initializations are performed, this cost is multiplied by the
number of initializations.

In the current experiment,

$$
N=2828,\qquad d=3,
$$

and only small candidate values of $K$ are considered. The computational
cost is therefore small. The complexity becomes more relevant for much larger
datasets, higher-dimensional feature spaces, or large numbers of repeated
initializations.


### What KMeans Does Not Model

KMeans uses the geometry of the feature vectors but does not use the
chronological ordering of the observations.

For example, it treats two feature vectors with identical coordinates in the
same way whether they occurred on consecutive trading days or several years
apart.

Therefore, KMeans can identify geometrically similar market conditions, but it
does not directly model:

- state persistence through time;
- transition probabilities between states;
- probabilistic uncertainty about state membership;
- different covariance shapes for different states.

For this reason, the KMeans result is treated as a baseline partition rather
than immediate evidence of genuine persistent market regimes.

## 10. KMeans Model Diagnostics and Empirical Findings

### Why Inertia Alone Cannot Select the Number of Clusters

The KMeans objective, or inertia, is

$$
J_K
=
\sum_{k=1}^{K}
\sum_{z_t\in C_k}
\|z_t-\mu_k\|_2^2.
$$

As the number of clusters increases, inertia cannot increase, because a model
with more centroids has at least as much flexibility as a model with fewer
centroids.

Therefore, choosing the value of $K$ with the smallest inertia would
automatically favor larger values of $K$. Inertia must instead be interpreted
together with other diagnostics and the structure of the resulting clusters.


### Silhouette Score

For an observation $i$, let

$$
a(i)
$$

be its average distance to observations in its own cluster, and let

$$
b(i)
$$

be the smallest average distance from $i$ to observations in another
cluster.

The silhouette value is

$$
s(i)
=
\frac{b(i)-a(i)}
{\max\{a(i),b(i)\}}.
$$

Its value lies between $-1$ and $1$.

Values closer to $1$ indicate that an observation is relatively well
separated from neighboring clusters. Values near zero indicate overlap near a
cluster boundary, while negative values can indicate that an observation may
be closer, on average, to another cluster.

The overall silhouette score is the average of $s(i)$ across observations.

A high silhouette score is evidence of geometric separation under the chosen
distance and feature representation. It is not proof that the clusters are
economically meaningful market regimes.


### Candidate Values of K

I evaluated

$$
K=2,\ldots,8
$$

on the standardized historical feature matrix.

The observed diagnostics were:

| K | Inertia | Silhouette | Cluster sizes |
|---:|---:|---:|---|
| 2 | 6293.477 | 0.5624 | 309, 2519 |
| 3 | 4943.018 | 0.4116 | 2208, 33, 587 |
| 4 | 3888.653 | 0.3968 | 509, 1846, 441, 32 |
| 5 | 3433.518 | 0.3938 | 1831, 435, 21, 530, 11 |
| 6 | 3064.706 | 0.3166 | 465, 1548, 159, 625, 10, 21 |
| 7 | 2757.822 | 0.3027 | 171, 1398, 289, 557, 21, 382, 10 |
| 8 | 2526.448 | 0.2921 | 510, 154, 1227, 20, 248, 10, 542, 117 |

Among these candidate values, $K=2$ produced the largest silhouette score.

For larger values of $K$, several very small clusters appeared. Together
with the previously inspected feature-space geometry, this suggests that some
additional centroids may be isolating relatively unusual tail observations
rather than revealing a large number of clearly separated, persistent market
states.

For this reason, $K=2$ is retained as a baseline partition for further
diagnostics. This is not a claim that the market has exactly two true regimes.


### Interpretation of the Two Centroids

After transforming the standardized centroids back into the original feature
units, the two cluster centers were approximately:

| Feature | Cluster 0 | Cluster 1 |
|---|---:|---:|
| SPY daily log return | -0.009342 | 0.001725 |
| SPY 20-day daily volatility | 0.018999 | 0.008184 |
| Cross-asset dispersion | 0.022333 | 0.008783 |

Cluster 0 therefore contains, on average, observations with more negative SPY
returns, higher recent volatility, and higher cross-asset dispersion.

Cluster 1 contains observations with, on average, mildly positive SPY returns,
lower volatility, and lower dispersion.

These descriptions are empirical characteristics of the clusters. The
numerical labels 0 and 1 have no intrinsic economic meaning, and I do not
hard-code semantic regime names into the algorithm.


### Initialization Stability and Adjusted Rand Index

Because KMeans is sensitive to initialization, I repeated the $K=2$
experiment across several random seeds.

To compare two partitions while ignoring arbitrary permutations of the cluster
labels, I use the Adjusted Rand Index (ARI).

ARI compares whether pairs of observations are grouped together or separately
in two different partitions and adjusts the comparison for agreement expected
by chance.

A value of

$$
\mathrm{ARI}=1
$$

means that the two partitions are identical up to a permutation of cluster
labels.

Across the tested seeds, almost all solutions had ARI equal to $1$ relative
to the reference solution. One seed produced

$$
\mathrm{ARI}\approx0.993261,
$$

with only a very small difference in the partition.

Therefore, the observed $K=2$ partition is highly stable with respect to the
tested KMeans initializations.

This stability addresses one computational concern, but it does not establish
that the clusters correspond to true economic regimes.


### Temporal Diagnostics

Although KMeans does not use time ordering during fitting, I examine the
resulting labels afterward to determine whether the geometric clusters also
show temporal persistence.

For consecutive observations, define the empirical transition count

$$
N_{ij}
=
\#\{t:c_t=i,\;c_{t+1}=j\}.
$$

The corresponding empirical transition probability is

$$
\widehat P_{ij}
=
\frac{N_{ij}}
{\sum_j N_{ij}}.
$$

For the $K=2$ baseline, the transition matrix was approximately

$$
\widehat P
=
\begin{pmatrix}
0.436893 & 0.563107 \\
0.069102 & 0.930898
\end{pmatrix}.
$$

The complete historical feature sequence contained 348 cluster switches, giving
a switch rate of approximately

$$
12.31\%.
$$

The run-length diagnostics were:

| Cluster | Number of runs | Mean run length | Median | Maximum |
|---|---:|---:|---:|---:|
| 0 | 174 | 1.776 | 1 | 44 |
| 1 | 175 | 14.394 | 3 | 295 |

Cluster 1 is relatively persistent, with an estimated self-transition
probability of approximately $0.931$.

Cluster 0 is substantially less persistent. Its median run length is only one
trading day, even though a few longer episodes occur.


### What the Baseline Result Supports

The KMeans experiment supports the conclusion that the selected feature space
contains a reproducible geometric separation between a large lower-volatility,
lower-dispersion group and a smaller group associated with more negative
returns, higher volatility, and higher dispersion.

However, the temporal diagnostics show that the smaller group is frequently
short-lived.

Therefore, I interpret KMeans as identifying different geometric market
conditions rather than claiming that it has established two persistent latent
economic regimes.


### Limitations and Reasonable Alternatives

KMeans has several limitations for this problem.

It uses squared Euclidean distance, so extreme observations can exert a strong
influence on centroids. The feature-space plots contain tails and unusual
stress observations, so this sensitivity is relevant.

KMeans also favors centroid-based geometric partitions and does not explicitly
represent clusters with different covariance structures.

Most importantly, it ignores temporal dependence while fitting the clusters.

Reasonable alternatives include:

- a Gaussian Mixture Model, which can represent probabilistic membership and
  different ellipsoidal covariance structures;

- a Hidden Markov Model, which can explicitly represent latent states and
  transition probabilities through time;

- alternative feature representations or scaling methods when justified by the
  statistical properties of the data.

These alternatives should not be adopted simply because they are more
sophisticated. They should be compared against the KMeans baseline using
consistent historical information and clearly defined diagnostics.



### 3-D Geometry and the KMeans Decision Boundary

The regime feature vector has three coordinates,

$$
x_t =
\begin{pmatrix}
r_{\mathrm{SPY},t} \\
\sigma_{\mathrm{SPY},t}^{(20)} \\
d_t
\end{pmatrix}.
$$

Therefore, each trading date can be viewed geometrically as one point in a
three-dimensional feature space.

The three coordinates have different numerical scales. KMeans is therefore
not fitted directly to the original financial coordinates. Each feature is
standardized using historical-sample statistics,

$$
z_{t,j}
=
\frac{x_{t,j}-\mu_j}{s_j},
$$

where $\mu_j$ and $s_j$ are respectively the fitted mean and scale of feature
$j$.

Standardization changes the coordinate system but not the identity of an
observation. The original-coordinate and standardized-coordinate panels in
the 3-D comparison figure therefore show the same trading dates and the same
final cluster assignments.

This distinction matters because KMeans minimizes squared Euclidean distances
in the standardized feature space. Consequently, the standardized panel
shows the geometry that is directly relevant to the clustering objective.

For the $K=2$ baseline, let the standardized centroids be $c_0$ and $c_1$.
A point $z$ lies on the KMeans decision boundary when it is equally distant
from the two centroids,

$$
\|z-c_0\|_2^2
=
\|z-c_1\|_2^2.
$$

Expanding both sides gives

$$
z^\top z
-2c_0^\top z
+\|c_0\|_2^2
=
z^\top z
-2c_1^\top z
+\|c_1\|_2^2.
$$

The common $z^\top z$ terms cancel, leaving

$$
2(c_1-c_0)^\top z
=
\|c_1\|_2^2-\|c_0\|_2^2.
$$

This is the equation of a plane in three dimensions. Geometrically, it is
the perpendicular-bisector plane separating the two KMeans Voronoi regions.

The 3-D comparison figure displays this plane only in standardized
coordinates because that is the space in which the KMeans distance
calculation is performed.

For readability, the plotted axes use the 1st-99th percentile range of each
feature. This is only a visualization choice. KMeans is fitted using all
2,828 historical feature observations, including observations outside the
displayed axis limits. In the current figure, 138 observations fall outside
at least one displayed axis limit; they are not removed from model fitting.

The centroid coordinates are also written directly on the figure. This makes
it possible to compare both their financial interpretation in the original
coordinates and their geometric position in standardized coordinates.

### Motivation for the Next Experiment

The KMeans result creates a specific next research question:

> If temporal state transitions are modeled explicitly, do the inferred market
> states become more coherent and persistent without sacrificing interpretability?

This provides a methodological reason to investigate a Hidden Markov Model
rather than adding it only as a more advanced algorithm.

The later May-August period remains outside this model-development comparison.
Feature choices, scaling rules, and model decisions should be developed using
the historical period before the later temporal evaluation is used.

## 11. Hidden Markov Model for Temporal Market States

### 11.1 Motivation and Model

KMeans partitions observations by geometry in feature space, but it does not use chronological order during fitting. The Hidden Markov Model (HMM) extends the same three-feature regime representation by introducing a latent state sequence with explicit transition probabilities.

The observed feature vector is

\[
X_t =
\begin{pmatrix}
r_{\mathrm{SPY},t} \\
\sigma_{\mathrm{SPY},t}^{(20)} \\
d_t
\end{pmatrix},
\]

where \(r_{\mathrm{SPY},t}\) is the SPY daily log return, \(\sigma_{\mathrm{SPY},t}^{(20)}\) is backward-looking 20-trading-day SPY volatility, and \(d_t\) is cross-asset return dispersion.

Let

\[
S_t \in \{1,\ldots,K\}
\]

denote the latent market state. The first-order Markov assumption is

\[
P(S_t \mid S_{t-1},S_{t-2},\ldots)
=
P(S_t\mid S_{t-1}).
\]

The transition matrix is

\[
A=(a_{ij}),
\qquad
a_{ij}=P(S_t=j\mid S_{t-1}=i).
\]

One model step corresponds to one consecutive trading observation, not one fixed calendar-day interval.

### 11.2 Gaussian Emissions

Conditioned on state \(k\), the feature vector is modeled as

\[
X_t\mid S_t=k
\sim
\mathcal{N}(\mu_k,\Sigma_k).
\]

The project compares diagonal and full covariance specifications. A diagonal covariance model treats the three features as conditionally uncorrelated within a state, while a full covariance model allows state-specific dependence between return, recent volatility, and cross-asset dispersion.

For a full covariance state, constant-density contours satisfy

\[
(x-\mu_k)^\top \Sigma_k^{-1}(x-\mu_k)=c,
\]

so the emission geometry is ellipsoidal rather than purely centroid-based as in KMeans.

### 11.3 Scaling and Information Availability

The HMM is fitted to standardized features because the three coordinates have different numerical scales.

For chronological validation, the scaler is fitted only on that fold's training period,

\[
z_{tj}
=
\frac{x_{tj}-\mu_j^{\mathrm{train}}}
{\sigma_j^{\mathrm{train}}},
\]

and the same training statistics are then used to transform the later validation block. This prevents future validation information from entering the scaling step.

The HMM development experiments use historical observations only through 2026-04-30. The later May-August 2026 period remains outside model specification and tuning.

### 11.4 EM Fitting and Multiple Initializations

The Gaussian HMM parameters are estimated iteratively using
expectation-maximization (EM).

The fitted parameters include:

- the initial-state probabilities,
- the transition matrix,
- state-specific mean vectors,
- and state-specific covariance matrices.

HMM likelihood optimization can converge to different local solutions.
Therefore, one random initialization is not treated as sufficient evidence
of a stable fit.

For each candidate specification, several random seeds are fitted.

A run is treated as valid only when:

1. the fitting routine reports convergence, and
2. the recorded EM log-likelihood history does not contain a material
   decrease beyond the numerical tolerance used in the diagnostic.

Among valid runs for a fixed specification, the fit with the largest
historical log-likelihood is retained.

This multi-start procedure is particularly important for the three-state
full-covariance model because the initialization experiment identified
more than one local optimum.

### 11.5 Sequence Likelihood and Model Complexity

For model parameters \(\theta\), the likelihood of the observed feature
sequence is

\[
P(X_{1:T}\mid\theta),
\]

and the corresponding log-likelihood is

\[
\ell(\theta)
=
\log P(X_{1:T}\mid\theta).
\]

A larger log-likelihood means that the fitted model assigns greater
probability density to the observed sequence.

However, likelihood alone is not sufficient for comparing models of
different complexity because adding states and covariance parameters can
improve in-sample fit.

For \(K\) hidden states and \(d\) observed features, the number of free
parameters used in this project is

\[
p
=
(K-1)
+
K(K-1)
+
Kd
+
p_{\mathrm{cov}}.
\]

The four terms represent:

1. initial-state probabilities,
2. transition probabilities,
3. state-specific means,
4. covariance parameters.

For diagonal covariance,

\[
p_{\mathrm{cov}}
=
Kd,
\]

while for full covariance,

\[
p_{\mathrm{cov}}
=
K\frac{d(d+1)}{2}.
\]

The Akaike Information Criterion is

\[
\mathrm{AIC}
=
-2\ell + 2p,
\]

and the Bayesian Information Criterion is

\[
\mathrm{BIC}
=
-2\ell + p\log N,
\]

where \(N\) is the number of feature observations.

Lower values indicate a better fit-complexity trade-off under the
corresponding criterion.

The manual parameter-count function in this project was checked against
the implementation in `hmmlearn` 0.3.3. The formulas agree for the
initial-state, transition, mean, diagonal-covariance, and full-covariance
parameter counts.

Because the observations form a dependent financial time series, AIC and
BIC are treated here as comparative model diagnostics rather than proof
that one candidate state count is the uniquely correct description of
market behavior.

### 11.6 Viterbi Decoding and Posterior State Probabilities

After fitting an HMM, there are two useful ways to describe its latent
states.

The first is a hard state sequence. The Viterbi algorithm finds the
most likely joint hidden-state path

\[
\hat S_{1:T}
=
\arg\max_{S_{1:T}}
P(S_{1:T}\mid X_{1:T},\theta).
\]

This assigns one state to every observation.

The numerical state labels themselves have no intrinsic economic meaning.
For example, State 0 is not automatically a low-risk or high-risk state.
Interpretation must instead come from the fitted state means, covariance
structure, transition probabilities, and observed state occupancy.

A hard Viterbi assignment does not describe uncertainty. Therefore, the
project also examines posterior state probabilities,

\[
\gamma_t(k)
=
P(S_t=k\mid X_{1:T},\theta).
\]

For a validation period containing \(T_{\mathrm{val}}\) observations, the
average posterior share of state \(k\) is

\[
\bar{\gamma}_k
=
\frac{1}{T_{\mathrm{val}}}
\sum_{t\in\mathrm{validation}}
\gamma_t(k).
\]

This diagnostic helps distinguish between two situations:

1. a state is absent from the Viterbi path but still receives meaningful
   posterior probability, or
2. a state receives essentially no probability during that period.

In the current experiments, posterior probabilities are used as structural
diagnostics rather than real-time trading signals. Because the diagnostic
uses the observed sequence when computing smoothed state probabilities, it
should not be interpreted as information that would necessarily have been
available at the corresponding historical time.

### 11.7 Expected State Duration

Let

\[
a_{kk}
=
P(S_t=k\mid S_{t-1}=k)
\]

be the probability that the HMM remains in state \(k\) for the next
trading observation.

Under the first-order time-homogeneous Markov assumption, the duration
\(D_k\) of a continuous visit to state \(k\) follows a geometric
distribution.

Its expected duration is

\[
E[D_k]
=
\frac{1}{1-a_{kk}}.
\]

Therefore, a self-transition probability close to one corresponds to a
more persistent latent state.

The duration is measured in trading observations rather than calendar
days. For example, a Friday-to-Monday transition and a Monday-to-Tuesday
transition are each counted as one model transition.

Expected duration is useful for comparing temporal persistence across
states, but it should be interpreted as a model-implied average rather
than a guarantee that every observed state episode lasts that long.

### 11.8 Chronological Validation

HMM model comparison is not based only on in-sample likelihood.

An internal chronological train-validation split is constructed entirely
inside the historical development period.

Approximately the first 80% of the historical regime-feature observations
are used for training, while the remaining 20% are used for validation.

The split is chronological rather than randomly shuffled. This preserves
the ordering of the financial time series and avoids allowing later
observations to enter the training period.

For each candidate HMM specification:

1. the scaler is fitted using only the training observations,
2. the training observations are standardized using that scaler,
3. the validation observations are transformed using the same training
   scaler,
4. the HMM is fitted only to the standardized training sequence,
5. the later validation sequence is then evaluated.

For fitted parameters \(\theta\), the conditional validation
log-likelihood is calculated as

\[
\log P(
X_{\mathrm{val}}
\mid
X_{\mathrm{train}},
\theta
)
=
\log P(
X_{\mathrm{train}},
X_{\mathrm{val}}
\mid
\theta
)
-
\log P(
X_{\mathrm{train}}
\mid
\theta
).
\]

Dividing this quantity by the number of validation observations gives
validation log-likelihood per observation.

This normalization makes scores from validation blocks of different sizes
more directly comparable.

A larger validation log-likelihood per observation indicates that the
fitted model assigns greater conditional probability density to the later
observations.

For decoded validation states, the training and validation observations
are joined in chronological order before decoding, and only the validation
tail is retained for validation-state diagnostics.

This preserves the state-history information at the train-validation
boundary instead of decoding the validation block as if it began with an
unrelated new hidden-state sequence.

Chronological validation is used here as a model-development diagnostic.
It is separate from the later May-August 2026 fixed-cutoff evaluation
period.

### 11.9 Rolling-Origin Validation

A single chronological train-validation split may depend strongly on the
particular date chosen for the boundary.

To test whether conclusions remain similar across several later periods,
the project also uses expanding-window rolling-origin validation.

The four training and validation boundaries are approximately

\[
60\% \rightarrow 70\%,
\qquad
70\% \rightarrow 80\%,
\qquad
80\% \rightarrow 90\%,
\qquad
90\% \rightarrow 100\%.
\]

For example, in the first fold, approximately the first 60% of the
historical observations form the training sequence and the following
10% form the validation sequence.

The next fold expands the training sequence to approximately 70%, and
the following 10% becomes the new validation period.

This process continues until the final historical observations are used
for validation.

For every fold:

1. the scaler is fitted only on that fold's training observations,
2. the HMM is fitted only on the standardized training sequence,
3. the validation observations are transformed with the training scaler,
4. conditional validation log-likelihood per observation is calculated,
5. the combined train-validation sequence is decoded chronologically,
6. only the validation tail is used for validation-state diagnostics.

The model specifications compared are

\[
K \in \{2,3,4,5,6\},
\]

with both diagonal and full covariance matrices.

Several random initializations are attempted for each specification.
Only valid fits are considered when selecting the fitted model for a fold.

For each specification, the project records the mean and standard deviation
of validation log-likelihood per observation across the folds.

The standard deviation is useful because two models can have similar
average validation performance while differing substantially in stability
across time periods.

State occupancy is also examined.

For each validation block, the minimum number of observations assigned to
any state by the Viterbi path is recorded.

In addition, the minimum average posterior state probability is examined.

These diagnostics are important because a model can obtain improved
likelihood by introducing additional latent components that are used only
rarely or effectively disappear during some later periods.

Therefore, rolling-origin validation is used not only to compare
likelihood, but also to examine whether the inferred state structure
remains meaningfully represented through time.

This is especially relevant when comparing three-state models with more
complex four-, five-, and six-state specifications.

### 11.10 Two-State Temporal Baseline

The first temporal comparison uses a two-state, full-covariance Gaussian
HMM fitted to the same 2,828 historical regime-feature observations used
for the KMeans comparison.

The fitted historical log-likelihood is approximately

\[
\ell = -8563.705.
\]

The decoded state sizes are

\[
1853
\quad\text{and}\quad
975,
\]

corresponding to approximately

\[
65.52\%
\quad\text{and}\quad
34.48\%
\]

of the historical observations.

The estimated transition matrix is approximately

\[
A
=
\begin{pmatrix}
0.9836 & 0.0164 \\
0.0311 & 0.9689
\end{pmatrix}.
\]

The large diagonal entries indicate substantial temporal persistence.

Using

\[
E[D_k]
=
\frac{1}{1-a_{kk}},
\]

the corresponding expected state durations are approximately

\[
61.1
\quad\text{and}\quad
32.1
\]

trading observations.

In original financial units, the approximate state means are

\[
\begin{array}{c|ccc}
 & r_{\mathrm{SPY}}
 & \sigma_{\mathrm{SPY}}^{(20)}
 & d_t \\
\hline
\text{State 0}
& 0.000778
& 0.006418
& 0.008267 \\
\text{State 1}
& 0.000031
& 0.014939
& 0.014034
\end{array}
\]

The second state therefore has substantially higher recent SPY volatility
and higher cross-asset dispersion in this historical fit.

These states are interpreted descriptively as lower-volatility and
higher-volatility statistical conditions rather than as automatically
identified economic regimes.

The two-state initialization experiment was highly stable across the tested
random seeds. Fits reached the same likelihood and equivalent decoded
partitions up to arbitrary state-label permutation.

The two-state HMM also produces much more persistent temporal assignments
than the KMeans baseline.

The KMeans baseline changes cluster assignment 348 times over the historical
sequence, corresponding to approximately 12.31% of consecutive transitions.

The two-state HMM changes decoded state only 54 times, corresponding to
approximately 1.91% of consecutive transitions.

This difference should not be interpreted as proof that the HMM is
automatically superior. Persistence is explicitly encouraged by the HMM
transition structure, while KMeans contains no temporal transition model.

Instead, the comparison demonstrates the methodological distinction between
a purely geometric partition and a latent-state model that explicitly
represents temporal persistence.

### 11.11 Three-State Full-Covariance HMM

For more detailed interpretation, the project also fits a three-state
full-covariance Gaussian HMM using multiple random initializations.

The selected valid fit has historical log-likelihood approximately

\[
\ell = -7376.127.
\]

The decoded historical state sizes are

\[
1377,\qquad1095,\qquad356,
\]

corresponding approximately to

\[
48.69\%,\qquad38.72\%,\qquad12.59\%
\]

of the 2,828 historical feature observations.

The estimated transition matrix is approximately

\[
A
=
\begin{pmatrix}
0.9781 & 0.0150 & 0.0070 \\
0.0251 & 0.9595 & 0.0155 \\
0.0077 & 0.0666 & 0.9257
\end{pmatrix}.
\]

All three diagonal transition probabilities are large, although the
third state is less persistent than the first two.

The corresponding expected durations are approximately

\[
45.6,\qquad24.7,\qquad13.5
\]

trading observations.

In original financial units, the approximate state means are

\[
\begin{array}{c|ccc}
 & r_{\mathrm{SPY}}
 & \sigma_{\mathrm{SPY}}^{(20)}
 & d_t \\
\hline
\text{State 0}
& 0.000777
& 0.005593
& 0.007944 \\
\text{State 1}
& 0.000582
& 0.010558
& 0.010614 \\
\text{State 2}
& -0.000666
& 0.020252
& 0.018119
\end{array}
\]

The states therefore show a clear ordering in the two risk-related
coordinates:

\[
\text{State 0}
<
\text{State 1}
<
\text{State 2}
\]

for both recent SPY volatility and cross-asset dispersion.

For descriptive interpretation, the states are therefore referred to as:

- lower-volatility / lower-dispersion,
- intermediate-volatility / intermediate-dispersion,
- higher-volatility / higher-dispersion and stress-like.

The final description remains statistical rather than causal. In
particular, the third state is not automatically labeled a financial
crisis state.

The full covariance matrices also have increasingly large eigenvalues as
the state index moves from the lower-volatility state toward the
higher-volatility state.

Approximate covariance eigenvalues are

\[
\text{State 0: }
(1.69\times10^{-6},
1.25\times10^{-5},
3.16\times10^{-5}),
\]

\[
\text{State 1: }
(4.35\times10^{-6},
2.21\times10^{-5},
1.10\times10^{-4}),
\]

and

\[
\text{State 2: }
(7.65\times10^{-5},
1.95\times10^{-4},
5.36\times10^{-4}).
\]

Geometrically, this means that the higher-volatility state has a broader
Gaussian covariance ellipsoid in all principal covariance directions.

This geometric interpretation complements the state means: the
higher-volatility state is characterized not only by larger average
volatility and dispersion, but also by greater within-state variation.

### 11.12 Initialization Sensitivity and Model-Selection Decision

The three-state full-covariance HMM is not completely independent of
initialization.

Several tested random seeds converged to the same higher-likelihood
solution with approximately

\[
\ell = -7376.127,
\]

and equivalent decoded partitions up to arbitrary state-label permutation.

Other seeds converged to a different local solution with approximately

\[
\ell = -7441.404.
\]

The Adjusted Rand Index between these two partitions is approximately

\[
0.591.
\]

Therefore, the three-state model should not be described as
initialization-independent.

The implementation instead fits multiple initializations, rejects invalid
runs, and retains the valid fit with the largest historical log-likelihood.

For the retained three-state full-covariance model, the selected
initialization used random seed 10.

The candidate-state comparison considered

\[
K \in \{2,3,4,5,6\}
\]

with both diagonal and full covariance structures.

Increasing model complexity generally continued to improve historical
likelihood and chronological validation likelihood.

Therefore, the experiment does not support the claim that three states
are statistically optimal.

However, higher-state models increasingly produced small or
period-specific latent components.

The three-state full-covariance model has historical state proportions of
approximately

\[
48.69\%,\qquad38.72\%,\qquad12.59\%.
\]

All three states therefore retain substantial representation over the
full historical period.

For larger values of \(K\), some states become much smaller.

The rolling-origin validation diagnostics show that some higher-state
models contain states with zero Viterbi occupancy in particular future
validation blocks.

Posterior-probability diagnostics also show that some of these states
receive extremely small posterior probability during those periods.

Even the three-state model contains a relatively rare state in some
validation folds, so its interpretation should remain cautious.

The three-state full-covariance HMM is retained as the primary
interpretable specification because it provides:

1. a clear ordering in volatility and cross-asset dispersion,
2. substantial full-history occupancy for all three states,
3. explicit temporal persistence,
4. state-specific covariance geometry,
5. and lower complexity than the four-, five-, and six-state alternatives.

This is a modeling trade-off rather than proof of the true number of
market regimes.

The experiment therefore separates two questions:

\[
\text{Which model gives the highest likelihood?}
\]

and

\[
\text{Which model gives a useful and defensible state representation?}
\]

In the current results, these questions do not have the same answer.

The higher-state models are retained as sensitivity analyses rather than
discarded. Their improved likelihood shows that richer latent
representations can fit the observed sequence more closely, while their
sparse-state behavior cautions against interpreting every additional
component as a persistent economic regime.

### 11.13 Limitations and Conclusion

The HMM analysis provides a more explicitly temporal description of the
regime-feature sequence than KMeans, but it still relies on several
simplifying assumptions.

First, the Gaussian emission model may not fully represent heavy tails,
skewness, or other non-Gaussian behavior commonly observed in financial
data.

Second, the current HMM is first-order and time-homogeneous. The transition
matrix is therefore assumed to remain constant through the fitted historical
period.

Third, one model step corresponds to one consecutive trading observation.
The model does not explicitly adjust transition probabilities for the
different calendar gaps created by weekends and market holidays.

Fourth, the inferred states are latent statistical components. They should
not automatically be assigned causal macroeconomic labels such as
"recession", "crisis", or "recovery" without independent evidence.

Fifth, posterior smoothing probabilities use information from the observed
sequence on both sides of a time point. They are therefore useful for
structural diagnosis, but they are not equivalent to probabilities that
would necessarily have been available in real time.

Sixth, increasing the number of states improves likelihood in the current
experiments. The retained three-state model is therefore a deliberate
interpretability and parsimony choice rather than a statistically unique
solution.

The main conclusion of this stage is therefore comparative.

KMeans provides a simple geometric baseline based on distances from
centroids.

The Gaussian HMM extends this framework by adding:

- latent temporal states,
- state-transition probabilities,
- persistence,
- state-specific covariance geometry,
- probabilistic state uncertainty,
- and chronological validation.

The resulting three-state full-covariance model gives an interpretable
progression from lower to intermediate to higher volatility and
cross-asset dispersion.

At the same time, the initialization and higher-state sensitivity
experiments show that latent-state conclusions depend on model
specification and optimization.

The HMM stage is therefore treated as a validated statistical modeling
component of the project rather than as proof that financial markets
possess a fixed or uniquely identifiable set of regimes.

## 12. Five-Day SPY Risk Forecasting

### 12.1 Forecast Target and Information Timing

The forecasting question is:

> Given market information observed by the close of trading day
> \(t\), what will be the RMS magnitude of SPY's daily log returns
> over the next five trading days?

Let \(r_t\) denote SPY's daily log return at trading date \(t\).
The forecasting target is

\[
y_t =
\sqrt{\frac{1}{5}\sum_{j=1}^{5}r_{t+j}^{\,2}}.
\]

The target measures the magnitude of future daily return movements,
not their direction. It is a root mean square around zero, not a
sample standard deviation around the five-day sample mean.

Our forecast is made after the close on date \(t\). At that time,
the current SPY return, trailing 20-day SPY volatility, and
same-day cross-asset return dispersion are available as inputs.
The five future returns in \(y_t\) are not yet known.

If trading date \(t+5\) is the fifth subsequent trading date,
the target \(y_t\) becomes observable only after the close on
that date. Accordingly, a training example indexed by \(s\)
may enter a model refit on date \(t\) only if its fifth future
trading date is no later than \(t\).

For the original historical evaluation cutoff of 2026-04-30,
the last forecast date with a fully observable target was
2026-04-23. The extended May-August evaluation contains
79 forecast dates from 2026-05-01 through 2026-08-24;
the last target becomes observable on 2026-08-31.

Consecutive targets overlap: \(y_t\) and \(y_{t+1}\) share four
daily returns. Their associated forecast errors therefore
cannot generally be treated as independent observations.

### 12.2 Ridge Regression as a Convex Quadratic Problem

#### Model and parameter dimension

At the close of trading date \(t\), define the three-feature vector

\[
x_t =
\begin{pmatrix}
r_{\mathrm{SPY},t}\\
\sigma_{\mathrm{SPY},t}^{(20)}\\
d_t
\end{pmatrix}
\in \mathbb{R}^3.
\]

The forecasting model uses these observed features directly. The
descriptive PCA directions and inferred HMM states are not inputs
to the current Ridge forecasting experiment.

For a given fit, the training-only `StandardScaler` transforms
\(x_t\) into \(z_t\). Ridge then predicts

\[
\widehat y_t=\beta_0+z_t^\top\beta,
\]

where \(\beta_0\in\mathbb{R}\) is the intercept and
\(\beta\in\mathbb{R}^3\) contains the three feature slopes.

Thus, the input space is three-dimensional, while the complete
parameter vector \((\beta_0,\beta)\) belongs to \(\mathbb{R}^4\).

#### Optimization objective

Let \(\mathcal I\) be the set of eligible training dates at a
particular fit, and let \(N=|\mathcal I|\). The implementation
uses scikit-learn Ridge with an unpenalized intercept:

\[
\boxed{
\min_{\beta_0\in\mathbb{R},\,\beta\in\mathbb{R}^3}
\left[
\sum_{t\in\mathcal I}
(y_t-\beta_0-z_t^\top\beta)^2
+\alpha\|\beta\|_2^2
\right].
}
\]

Our retained setting is \(\alpha=1\). The objective is the sum
of squared *training* residuals plus an L2 penalty on the slopes.
The training sum is not divided by \(N\) in this formulation.

The penalty discourages large standardized-feature coefficients;
it does not impose a hard coefficient constraint. MAE and RMSE
are calculated afterward to evaluate forecasts and are not the
objective minimized by this Ridge fit.

#### Convexity and solution

Let \(Z\in\mathbb{R}^{N\times3}\) be the standardized training
design matrix, and let \(y\in\mathbb{R}^N\) be the training
target vector. For fixed \(Z\) and \(y\), the objective is
quadratic in \((\beta_0,\beta)\).

For \(\alpha>0\), its quadratic variation in a parameter
direction \((u_0,u)\) is

\[
2\|\mathbf{1}u_0+Zu\|_2^2
+2\alpha\|u\|_2^2.
\]

For any nonzero parameter direction and \(N>0\), this
quantity is strictly positive. Therefore, the objective
is strictly convex and has a unique global minimizer.

A numerical optimizer or linear-algebra solver finds this
minimizer; changing an iterative initialization cannot
produce a distinct local optimum of the same Ridge objective.

#### Interpretation and limitations

The predicted target is a magnitude and is therefore
nonnegative by definition. Ordinary Ridge regression does
not constrain \(\widehat y_t\geq0\), although no negative
predictions occurred in the original historical validation.

The fitted coefficients describe statistical associations
within the selected features and training period. They do
not establish causal effects or guarantee that subsequent
forecasting errors will be small.

### 12.3 Walk-Forward Refitting and Training Windows

#### Why refit chronologically?

The original Ridge experiment fitted one model and evaluated it on a
subsequent historical validation block. The walk-forward experiment
instead repeats model fitting at the first eligible forecast date
of each month.

This represents a forecasting process in which the information
available for training grows as later trading outcomes become known.
It also allows us to investigate whether retaining all available
history or emphasizing more recent observations changes forecast
accuracy.

#### Eligible training dates

Let \(\tau\) be a monthly refit date, and let \(e(s)\) denote the
trading date on which the five-day target for forecast date \(s\)
becomes fully observable.

The eligible training-date set is

\[
\mathcal I_\tau
=
\{s:\ s<\tau,\ e(s)\leq\tau,\ y_s
\text{ is available}\}.
\]

The strict condition \(s<\tau\) excludes the current forecast
date from its own training sample. The condition
\(e(s)\leq\tau\) prevents training on a target containing
returns that have not yet been observed.

This definition assumes that monthly refitting and forecasting
occur after the close on date \(\tau\).

#### Fixed rolling and expanding training windows

Write the eligible dates in chronological order as

\[
\mathcal I_\tau
=
(s_1,\ldots,s_{N_\tau}).
\]

For a rolling window of \(W\) eligible examples, the training
dates at refit \(\tau\) are

\[
\mathcal I_{\tau,W}
=
(s_{N_\tau-W+1},\ldots,s_{N_\tau}),
\qquad N_\tau\geq W.
\]

The experiment compares

\[
W\in\{252,504,756,1008\}.
\]

The expanding-window method instead uses all eligible dates:

\[
\mathcal I_{\tau,\mathrm{expanding}}
=
\mathcal I_\tau.
\]

Each candidate fits its own training-only feature scaler and
Ridge model with \(\alpha=1\). Within a month, the fitted
scaler and coefficients remain fixed while newly observed
daily features generate fresh predictions. The models are
refitted on the next monthly refit date.

A rolling window of \(W\) denotes \(W\) eligible training
examples, not necessarily the most recent \(W\) consecutive
trading dates: the latest observations may be excluded
because their complete five-day targets are not yet known.

### 12.4 Adaptive Selection Using Completed Forecast Errors

The adaptive method selects among five existing Ridge candidates:
rolling windows of 252, 504, 756, and 1008 eligible training
examples, and the expanding window. It does not fit a sixth
Ridge model.

Let \(\mathcal M\) denote this candidate set. At the first eligible
forecast date \(\tau\) of each month, consider earlier forecast
dates \(s<\tau\) for which the actual five-day target has become
observable by the close on \(\tau\). The selector uses the most
recent 252 such completed forecast dates for which all candidate
predictions are available. Denote this common set by
\(\mathcal C_\tau\), with \(|\mathcal C_\tau|=252\).
Adaptive selection begins only once this full common
history is available.

For candidate \(m\in\mathcal M\), define its past error score by

\[
A_m(\tau)
=
\frac{1}{|\mathcal C_\tau|}
\sum_{s\in\mathcal C_\tau}
|y_s-\widehat y_{s,m}|.
\]

Here, \(\widehat y_{s,m}\) is the prediction candidate \(m\)
actually produced for date \(s\) under the historical
walk-forward procedure. The selector chooses

\[
m_\tau^*
=
\operatorname*{arg\,min}_{m\in\mathcal M}
A_m(\tau).
\]

Ties follow a fixed, deterministic candidate order. The
selected candidate supplies the adaptive predictions
throughout that month; the selection is reconsidered at
the next monthly refit date.

The score uses only targets completed by the selection
date. In particular, a forecast whose five-day horizon
extends beyond \(\tau\) cannot contribute to
\(\mathcal C_\tau\), even if its prediction was already made.

The adaptive method minimizes *past observed MAE across
candidate forecasts* when choosing a model. Each candidate's
Ridge coefficients were separately obtained by minimizing
its penalized training squared-error objective. Neither
optimization guarantees the lowest MAE in a subsequent
evaluation period.

Because adjacent five-day targets overlap, the 252 completed
forecast errors need not be statistically independent.

### 12.5 Forecast Evaluation and Limitations

#### Error measures

For an evaluation set \(\mathcal T\) of \(n\) forecast dates,
define the error of a forecasting method \(m\) by

\[
e_{t,m}=\widehat y_{t,m}-y_t.
\]

We report three aggregate measures:

\[
\operatorname{MAE}_m
=
\frac{1}{n}\sum_{t\in\mathcal T}|e_{t,m}|,
\]

\[
\operatorname{RMSE}_m
=
\sqrt{\frac{1}{n}
\sum_{t\in\mathcal T}e_{t,m}^{\,2}},
\]

\[
\operatorname{MeanError}_m
=
\frac{1}{n}\sum_{t\in\mathcal T}e_{t,m}.
\]

MAE measures average absolute prediction error; RMSE gives
greater weight to large errors. Mean error describes the
direction of average forecast bias under this sign convention:
positive values indicate overprediction on average, while
negative values indicate underprediction on average.

These evaluation measures are distinct from the penalized
training squared-error objective of Ridge regression.

#### Evaluation periods

The historical comparison of all five Ridge candidates and
the adaptive selector uses 1,545 common forecast dates from
2020-03-02 through 2026-04-23.

The later comparison uses 79 forecast dates from 2026-05-01
through 2026-08-24, with complete targets observed by
2026-08-31. The later predictions retain the historical
walk-forward chronology, including eligible observations
whose target completion dates fall between the original
historical cutoff and the start of May.

The later period is a fixed-cutoff pseudo-out-of-sample
evaluation, not an untouched holdout: its outcomes were
examined during earlier stages of this project. We therefore
report its results descriptively rather than treating it
as independent confirmation of a model-selection decision.

The detailed candidate comparisons, monthly selections,
and April 2020 diagnostic are recorded in
`docs/walk_forward_window_selection.md`.

#### Statistical and modeling limitations

Five-day targets at adjacent forecast dates share four
daily returns. Consequently, daily forecast errors can
be dependent, and the number of forecast dates should
not be interpreted as the number of independent outcomes.
The 79-date later period is also short relative to the
range of market conditions a forecasting method may encounter.

The adaptive selector chooses a candidate using past
completed errors. It does not guarantee that the chosen
candidate will have the smallest subsequent error, and
the observed comparison does not establish a universally
preferred training-window length.

These forecasts concern the future magnitude of SPY's
daily returns. They do not predict return direction,
portfolio returns, or the profitability of a trading
strategy. Portfolio construction and backtesting require
separate objectives, assumptions, and evaluation.
