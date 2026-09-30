"""
Fixed-cutoff evaluation of the historical three-state HMM.

The historical cutoff is April 30, 2026.
Later observations are used for evaluation, not model fitting.
"""

import numpy as np
import pandas as pd

from src.regime_hmm import prepare_hmm_data
from src.regime_features import (
    VOLATILITY_WINDOW,
    construct_regime_features,
)
from src.temporal_split import (
    load_log_returns,
    temporal_split,
    validate_returns,
)


def prepare_later_hmm_features():
    """Apply the historical scaler to later-period features."""

    historical_features, historical_scaled, scaler = (
        prepare_hmm_data()
    )

    returns = load_log_returns()
    validate_returns(returns)

    historical_returns, later_returns = temporal_split(
        returns
    )

    context = historical_returns.tail(
        VOLATILITY_WINDOW - 1
    )

    later_features = construct_regime_features(
        pd.concat([context, later_returns])
    ).loc[later_returns.index]

    if not later_features.index.equals(later_returns.index):
        raise RuntimeError("Later feature dates do not match.")

    if list(later_features.columns) != list(
        historical_features.columns
    ):
        raise RuntimeError("Feature columns do not match.")

    # Transform only: never refit the historical scaler.
    later_scaled = scaler.transform(later_features)

    if not np.isfinite(later_scaled).all():
        raise RuntimeError("Later features contain non-finite values.")

    return historical_scaled, later_features, later_scaled


def filter_later_hmm_states(model, historical_scaled, later_scaled):
    """Filter later states using a fixed historical HMM."""
    from scipy.special import logsumexp
    from scipy.stats import multivariate_normal

    historical_scaled = np.asarray(historical_scaled)
    later_scaled = np.asarray(later_scaled)

    if historical_scaled.ndim != 2 or later_scaled.ndim != 2:
        raise ValueError("Expected two-dimensional feature matrices.")

    if not len(historical_scaled) or not len(later_scaled):
        raise ValueError("Both periods must contain observations.")

    if historical_scaled.shape[1] != later_scaled.shape[1]:
        raise ValueError("Feature dimensions do not match.")

    combined = np.vstack([historical_scaled, later_scaled])
    historical_count = len(historical_scaled)
    n_states = model.n_components

    emissions = np.column_stack([
        multivariate_normal.logpdf(
            combined,
            mean=model.means_[state],
            cov=model.covars_[state],
        )
        for state in range(n_states)
    ])

    with np.errstate(divide="ignore"):
        log_start = np.log(model.startprob_)
        log_transition = np.log(model.transmat_)

    # First historical observation.
    log_alpha = log_start + emissions[0]
    log_alpha -= logsumexp(log_alpha)

    later_probabilities = []
    later_log_likelihood = 0.0

    # Process observations in chronological order.
    for t in range(1, len(combined)):
        log_alpha = (
            logsumexp(
                log_alpha[:, None] + log_transition,
                axis=0,
            )
            + emissions[t]
        )

        normalizer = logsumexp(log_alpha)
        log_alpha -= normalizer

        if t >= historical_count:
            later_log_likelihood += normalizer
            later_probabilities.append(np.exp(log_alpha.copy()))

    later_probabilities = np.asarray(later_probabilities)

    # Independently check the conditional sequence likelihood.
    reference = (
        model.score(combined)
        - model.score(historical_scaled)
    )

    if later_probabilities.shape != (len(later_scaled), n_states):
        raise RuntimeError("Unexpected filtered probability shape.")

    if not np.allclose(later_probabilities.sum(axis=1), 1.0):
        raise RuntimeError("State probabilities do not sum to one.")

    if not np.isclose(later_log_likelihood, reference, atol=1e-3):
        raise RuntimeError("Forward likelihood check failed.")

    return later_probabilities, later_log_likelihood

if __name__ == "__main__":
    from src.regime_hmm import fit_three_state_hmm

    historical_scaled, later_features, later_scaled = (
        prepare_later_hmm_features()
    )

    # Fit using historical observations only.
    model, _ = fit_three_state_hmm(historical_scaled)

    # Keep the fitted model fixed for later-period evaluation.
    probabilities, later_log_likelihood = (
        filter_later_hmm_states(
            model,
            historical_scaled,
            later_scaled,
        )
    )

    filtered_states = probabilities.argmax(axis=1)
    state_counts = np.bincount(
        filtered_states,
        minlength=model.n_components,
    )

    print("\nFixed-cutoff three-state HMM evaluation")
    print("---------------------------------------")
    print("Historical model seed:", model.selected_seed_)
    print("Later observations:", len(later_features))
    print("First later date:", later_features.index.min())
    print("Last later date:", later_features.index.max())
    print("Filtered state counts:", state_counts)
    print(
        "Mean filtered state probabilities:",
        np.round(probabilities.mean(axis=0), 4),
    )
    print(
        "Later conditional log-likelihood per observation:",
        round(later_log_likelihood / len(later_scaled), 4),
    )
    print(
        "Historical fitting log-likelihood per observation:",
        round(
            model.score(historical_scaled)
            / len(historical_scaled),
            4,
        ),
    )
    print(
        "Note: Filtered probabilities use returns observed"
        " through each date; they are not advance forecasts."
    )
