"""
Hidden Markov Model analysis for market-regime features.

The first HMM experiment uses the same historical feature matrix as the
KMeans baseline so that the comparison is methodologically fair.
"""

import matplotlib.pyplot as plt
import numpy as np
from hmmlearn.hmm import GaussianHMM

from src.regime_clustering import (
    fit_baseline_kmeans,
    standardize_features,
    temporal_diagnostics,
)
from src.regime_features import construct_regime_features
from src.temporal_split import (
    load_log_returns,
    temporal_split,
    validate_returns,
)


N_STATES = 2
RANDOM_STATE = 42


def prepare_hmm_data():
    """
    Construct and standardize the historical regime-feature matrix.

    The scaler is fitted only on observations available through the
    historical cutoff.
    """
    returns = load_log_returns()
    validate_returns(returns)

    historical, _ = temporal_split(returns)

    features = construct_regime_features(historical)
    scaled_features, scaler = standardize_features(features)

    return features, scaled_features, scaler


def fit_initial_hmm(scaled_features):
    """
    Fit an initial two-state Gaussian HMM.

    This is a diagnostic historical fit, not yet the final selected model.
    """
    model = GaussianHMM(
        n_components=N_STATES,
        covariance_type="full",
        n_iter=500,
        tol=1e-4,
        random_state=RANDOM_STATE,
    )

    model.fit(scaled_features)
    states = model.predict(scaled_features)

    return model, states


def initialization_stability(scaled_features):
    """
    Fit the same two-state HMM from several random initializations.

    Adjusted Rand Index is used to compare decoded state sequences.
    It is invariant to arbitrary swapping of state labels.
    """
    seeds = [0, 1, 2, 3, 4, 10, 42, 100, 2026]

    solutions = {}
    diagnostics = []

    for seed in seeds:
        model = GaussianHMM(
            n_components=N_STATES,
            covariance_type="full",
            n_iter=500,
            tol=1e-4,
            random_state=seed,
        )

        model.fit(scaled_features)
        states = model.predict(scaled_features)

        solutions[seed] = states

        diagnostics.append(
            {
                "seed": seed,
                "converged": model.monitor_.converged,
                "iterations": model.monitor_.iter,
                "log_likelihood": model.score(scaled_features),
                "state_sizes": np.bincount(
                    states,
                    minlength=N_STATES,
                ).tolist(),
            }
        )

    from sklearn.metrics import adjusted_rand_score

    reference_states = solutions[RANDOM_STATE]

    for result in diagnostics:
        result["ari_vs_seed_42"] = adjusted_rand_score(
            reference_states,
            solutions[result["seed"]],
        )

    return diagnostics


def covariance_geometry(model, scaler):
    """
    Convert HMM state covariance matrices back to original financial units
    and compute their eigenvalues.

    The eigenvalues describe variance along the principal axes of each
    Gaussian state's covariance ellipsoid.
    """
    scale_matrix = np.diag(scaler.scale_)

    diagnostics = []

    for state in range(model.n_components):
        standardized_covariance = model.covars_[state]

        original_covariance = (
            scale_matrix
            @ standardized_covariance
            @ scale_matrix
        )

        eigenvalues, eigenvectors = np.linalg.eigh(
            original_covariance
        )

        diagnostics.append(
            {
                "state": state,
                "covariance": original_covariance,
                "eigenvalues": eigenvalues,
                "eigenvectors": eigenvectors,
            }
        )

    return diagnostics


def expected_state_durations(model):
    """
    Compute the expected duration of each state under the fitted
    first-order Markov transition model.
    """
    persistence = np.diag(model.transmat_)

    return 1.0 / (1.0 - persistence)


def fit_three_state_hmm(scaled_features):
    """
    Fit a three-state full-covariance Gaussian HMM using multiple
    random initializations.

    Only converged fits with non-decreasing EM likelihood are eligible.
    The valid fit with the largest historical log-likelihood is retained.

    State labels remain arbitrary.
    """
    seeds = [0, 1, 2, 3, 4, 10, 42, 100, 2026]

    best_model = None
    best_states = None
    best_seed = None
    best_log_likelihood = -np.inf

    for seed in seeds:
        model = GaussianHMM(
            n_components=3,
            covariance_type="full",
            n_iter=500,
            tol=1e-4,
            random_state=seed,
        )

        model.fit(scaled_features)

        history = np.asarray(
            model.monitor_.history,
            dtype=float,
        )

        if len(history) >= 2:
            min_delta = float(
                np.min(np.diff(history))
            )
        else:
            min_delta = np.nan

        monotone_em = not (
            np.isfinite(min_delta)
            and min_delta < -1e-6
        )

        if (
            not model.monitor_.converged
            or not monotone_em
        ):
            continue

        log_likelihood = model.score(
            scaled_features
        )

        if log_likelihood > best_log_likelihood:
            best_log_likelihood = log_likelihood
            best_model = model
            best_states = model.predict(
                scaled_features
            )
            best_seed = seed

    if best_model is None:
        raise RuntimeError(
            "No valid three-state HMM fit was found."
        )

    best_model.selected_seed_ = best_seed

    return best_model, best_states


def three_state_initialization_stability(scaled_features):
    """
    Compare the three-state HMM partition across random initializations.

    Adjusted Rand Index is invariant to arbitrary permutations of
    HMM state labels.
    """
    from sklearn.metrics import adjusted_rand_score

    seeds = [0, 1, 2, 3, 4, 10, 42, 100, 2026]

    solutions = {}
    diagnostics = []

    for seed in seeds:
        model = GaussianHMM(
            n_components=3,
            covariance_type="full",
            n_iter=500,
            tol=1e-4,
            random_state=seed,
        )

        model.fit(scaled_features)

        history = np.asarray(
            model.monitor_.history,
            dtype=float,
        )

        if len(history) >= 2:
            min_delta = float(
                np.min(np.diff(history))
            )
        else:
            min_delta = np.nan

        monotone_em = not (
            np.isfinite(min_delta)
            and min_delta < -1e-6
        )

        valid = (
            model.monitor_.converged
            and monotone_em
        )

        if valid:
            states = model.predict(
                scaled_features
            )

            solutions[seed] = states

            log_likelihood = model.score(
                scaled_features
            )

            state_sizes = np.bincount(
                states,
                minlength=3,
            ).tolist()
        else:
            log_likelihood = np.nan
            state_sizes = None

        diagnostics.append(
            {
                "seed": seed,
                "valid": valid,
                "converged": model.monitor_.converged,
                "iterations": model.monitor_.iter,
                "min_delta": min_delta,
                "log_likelihood": log_likelihood,
                "state_sizes": state_sizes,
            }
        )

    if 1 not in solutions:
        raise RuntimeError(
            "Seed 1 did not produce a valid "
            "three-state reference fit."
        )

    reference_states = solutions[1]

    for result in diagnostics:
        seed = result["seed"]

        if seed in solutions:
            result["ari_vs_seed_1"] = (
                adjusted_rand_score(
                    reference_states,
                    solutions[seed],
                )
            )
        else:
            result["ari_vs_seed_1"] = np.nan

    return diagnostics


def plot_hmm_state_timeline(states, index):
    """
    Plot the decoded two-state HMM baseline through historical time.
    """
    from pathlib import Path

    results_dir = Path(__file__).resolve().parents[1] / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 3))

    for state in range(N_STATES):
        mask = states == state

        plt.scatter(
            index[mask],
            states[mask],
            s=10,
            alpha=0.7,
            label=f"State {state}",
        )

    plt.yticks(
        range(N_STATES),
        [f"State {k}" for k in range(N_STATES)],
    )
    plt.xlabel("Date")
    plt.ylabel("Decoded HMM state")
    plt.title("Decoded Two-State Gaussian HMM Baseline Through Historical Time")
    plt.legend()
    plt.grid(axis="x", alpha=0.25)
    plt.tight_layout()

    output_path = results_dir / "hmm_state_timeline.png"
    plt.savefig(output_path, dpi=160)
    plt.close()

    print("Saved:", output_path)




def plot_three_state_hmm_timeline(states, index):
    """
    Plot the decoded three-state HMM through historical time.
    """
    from pathlib import Path
    import numpy as np

    results_dir = Path(__file__).resolve().parents[1] / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    states = np.asarray(states)

    plt.figure(figsize=(12, 3.5))

    for state in range(3):
        mask = states == state

        plt.scatter(
            index[mask],
            states[mask],
            s=10,
            alpha=0.7,
            label=f"State {state}",
        )

    plt.yticks(
        range(3),
        [f"State {k}" for k in range(3)],
    )
    plt.xlabel("Date")
    plt.ylabel("Decoded HMM state")
    plt.title("Three-State HMM: Full-Sequence Historical Decoding")
    plt.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0))
    plt.grid(axis="x", alpha=0.25)
    plt.tight_layout()

    output_path = results_dir / "hmm_three_state_timeline.png"
    plt.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close()

    print("Saved:", output_path)

def count_hmm_parameters(
    n_states,
    n_features,
    covariance_type,
):
    """
    Count free parameters in a Gaussian HMM.

    Components:
    - initial-state probabilities: K - 1
    - transition probabilities: K(K - 1)
    - state means: Kd
    - covariance parameters:
        diagonal -> Kd
        full -> K d(d + 1) / 2
    """
    start_parameters = n_states - 1
    transition_parameters = n_states * (n_states - 1)
    mean_parameters = n_states * n_features

    if covariance_type == "diag":
        covariance_parameters = n_states * n_features
    elif covariance_type == "full":
        covariance_parameters = (
            n_states
            * n_features
            * (n_features + 1)
            // 2
        )
    else:
        raise ValueError(
            f"Unsupported covariance type: {covariance_type}"
        )

    return (
        start_parameters
        + transition_parameters
        + mean_parameters
        + covariance_parameters
    )


def rolling_origin_hmm_validation(features):
    """
    Evaluate HMM specifications over several expanding chronological folds.

    Each fold fits its scaler and HMM using only observations available
    before that fold's validation period.
    """
    from sklearn.preprocessing import StandardScaler

    candidate_states = [2, 3, 4, 5, 6]
    covariance_types = ["diag", "full"]
    seeds = [0, 1, 2, 42, 2026]

    # Expanding training windows followed by non-overlapping
    # chronological validation blocks.
    fold_boundaries = [
        (0.60, 0.70),
        (0.70, 0.80),
        (0.80, 0.90),
        (0.90, 1.00),
    ]

    results = []

    for n_states in candidate_states:
        for covariance_type in covariance_types:
            fold_scores = []
            minimum_state_sizes = []
            minimum_posterior_shares = []

            for train_fraction, validation_end_fraction in fold_boundaries:
                train_end = int(
                    train_fraction * len(features)
                )
                validation_end = int(
                    validation_end_fraction * len(features)
                )

                train_features = features.iloc[:train_end]
                validation_features = features.iloc[
                    train_end:validation_end
                ]

                scaler = StandardScaler()

                train_scaled = scaler.fit_transform(
                    train_features
                )
                validation_scaled = scaler.transform(
                    validation_features
                )

                full_scaled = np.vstack(
                    [train_scaled, validation_scaled]
                )

                best_model = None
                best_train_log_likelihood = -np.inf

                for seed in seeds:
                    model = GaussianHMM(
                        n_components=n_states,
                        covariance_type=covariance_type,
                        n_iter=500,
                        tol=1e-4,
                        random_state=seed,
                    )

                    model.fit(train_scaled)

                    history = np.asarray(
                        model.monitor_.history,
                        dtype=float,
                    )

                    if len(history) >= 2:
                        min_delta = float(
                            np.min(np.diff(history))
                        )
                    else:
                        min_delta = np.nan

                    monotone_em = not (
                        np.isfinite(min_delta)
                        and min_delta < -1e-6
                    )

                    if (
                        not model.monitor_.converged
                        or not monotone_em
                    ):
                        print(
                            "ROLLING INVALID RUN:",
                            f"K={n_states},",
                            f"covariance={covariance_type},",
                            f"seed={seed},",
                            f"train_fraction={train_fraction:.2f},",
                            f"validation_end={validation_end_fraction:.2f},",
                            f"converged={model.monitor_.converged},",
                            f"min_delta={min_delta:.6f}",
                        )
                        continue

                    train_log_likelihood = model.score(
                        train_scaled
                    )

                    if (
                        train_log_likelihood
                        > best_train_log_likelihood
                    ):
                        best_train_log_likelihood = (
                            train_log_likelihood
                        )
                        best_model = model

                if best_model is None:
                    fold_scores.append(np.nan)
                    minimum_state_sizes.append(np.nan)
                    minimum_posterior_shares.append(np.nan)
                    continue

                joint_log_likelihood = best_model.score(
                    full_scaled
                )

                validation_log_likelihood = (
                    joint_log_likelihood
                    - best_train_log_likelihood
                )

                fold_score = (
                    validation_log_likelihood
                    / len(validation_features)
                )

                full_states = best_model.predict(
                    full_scaled
                )

                validation_states = full_states[
                    len(train_scaled):
                ]

                state_sizes = np.bincount(
                    validation_states,
                    minlength=n_states,
                )

                full_posteriors = best_model.predict_proba(
                    full_scaled
                )

                validation_posteriors = full_posteriors[
                    len(train_scaled):
                ]

                posterior_shares = np.mean(
                    validation_posteriors,
                    axis=0,
                )

                fold_scores.append(fold_score)

                minimum_state_sizes.append(
                    int(state_sizes.min())
                )

                minimum_posterior_shares.append(
                    float(posterior_shares.min())
                )

            finite_scores = np.asarray(
                fold_scores,
                dtype=float,
            )

            results.append(
                {
                    "n_states": n_states,
                    "covariance_type": covariance_type,
                    "fold_scores": fold_scores,
                    "mean_score": np.nanmean(
                        finite_scores
                    ),
                    "std_score": np.nanstd(
                        finite_scores
                    ),
                    "minimum_state_sizes": (
                        minimum_state_sizes
                    ),
                    "minimum_posterior_shares": (
                        minimum_posterior_shares
                    ),
                }
            )

    return results


def chronological_hmm_validation(features):
    """
    Compare HMM specifications using a chronological 80/20 split.

    The scaler and HMM are fitted only on the training period.
    Validation likelihood is evaluated conditionally on the preceding
    training sequence.
    """
    from sklearn.preprocessing import StandardScaler

    split_index = int(0.80 * len(features))

    train_features = features.iloc[:split_index]
    validation_features = features.iloc[split_index:]

    scaler = StandardScaler()
    train_scaled = scaler.fit_transform(train_features)
    validation_scaled = scaler.transform(validation_features)

    full_scaled = np.vstack(
        [train_scaled, validation_scaled]
    )

    candidate_states = [2, 3, 4, 5, 6]
    covariance_types = ["diag", "full"]
    seeds = [0, 1, 2, 42, 2026]

    results = []

    for n_states in candidate_states:
        for covariance_type in covariance_types:
            best_model = None
            best_seed = None
            best_train_log_likelihood = -np.inf
            valid_runs = 0

            for seed in seeds:
                model = GaussianHMM(
                    n_components=n_states,
                    covariance_type=covariance_type,
                    n_iter=500,
                    tol=1e-4,
                    random_state=seed,
                )

                model.fit(train_scaled)

                history = np.asarray(
                    model.monitor_.history,
                    dtype=float,
                )

                if len(history) >= 2:
                    min_delta = float(
                        np.min(np.diff(history))
                    )
                else:
                    min_delta = np.nan

                monotone_em = not (
                    np.isfinite(min_delta)
                    and min_delta < -1e-6
                )

                if (
                    not model.monitor_.converged
                    or not monotone_em
                ):
                    continue

                valid_runs += 1

                train_log_likelihood = model.score(
                    train_scaled
                )

                if (
                    train_log_likelihood
                    > best_train_log_likelihood
                ):
                    best_train_log_likelihood = (
                        train_log_likelihood
                    )
                    best_model = model
                    best_seed = seed

            if best_model is None:
                results.append(
                    {
                        "n_states": n_states,
                        "covariance_type": covariance_type,
                        "valid_runs": 0,
                    }
                )
                continue

            joint_log_likelihood = best_model.score(
                full_scaled
            )

            validation_log_likelihood = (
                joint_log_likelihood
                - best_train_log_likelihood
            )

            validation_log_likelihood_per_observation = (
                validation_log_likelihood
                / len(validation_features)
            )

            full_states = best_model.predict(
                full_scaled
            )

            validation_states = full_states[
                len(train_scaled):
            ]

            validation_state_sizes = np.bincount(
                validation_states,
                minlength=n_states,
            ).tolist()

            results.append(
                {
                    "n_states": n_states,
                    "covariance_type": covariance_type,
                    "valid_runs": valid_runs,
                    "best_seed": best_seed,
                    "train_log_likelihood": (
                        best_train_log_likelihood
                    ),
                    "validation_log_likelihood": (
                        validation_log_likelihood
                    ),
                    "validation_log_likelihood_per_observation": (
                        validation_log_likelihood_per_observation
                    ),
                    "validation_state_sizes": (
                        validation_state_sizes
                    ),
                }
            )

    return (
        train_features,
        validation_features,
        results,
    )


def compare_hmm_specifications(scaled_features):
    """
    Compare candidate Gaussian HMM specifications.

    Model fitting uses only the historical feature matrix.
    Several random initializations are tried for each specification.
    """
    candidate_states = [2, 3, 4, 5, 6]
    covariance_types = ["diag", "full"]
    seeds = [0, 1, 2, 42, 2026]

    n_samples, n_features = scaled_features.shape

    results = []

    for n_states in candidate_states:
        for covariance_type in covariance_types:
            best_result = None
            valid_runs = 0

            for seed in seeds:
                candidate = GaussianHMM(
                    n_components=n_states,
                    covariance_type=covariance_type,
                    n_iter=500,
                    tol=1e-4,
                    random_state=seed,
                )

                candidate.fit(scaled_features)

                history = np.asarray(
                    candidate.monitor_.history,
                    dtype=float,
                )

                if len(history) >= 2:
                    likelihood_deltas = np.diff(history)
                    min_likelihood_delta = float(
                        np.min(likelihood_deltas)
                    )
                else:
                    min_likelihood_delta = np.nan

                monotone_em = not (
                    np.isfinite(min_likelihood_delta)
                    and min_likelihood_delta < -1e-6
                )

                if not monotone_em:
                    print(
                        "LIKELIHOOD DECREASE:",
                        f"K={n_states},",
                        f"covariance={covariance_type},",
                        f"seed={seed},",
                        f"min_delta={min_likelihood_delta:.6f}",
                    )

                if (
                    not candidate.monitor_.converged
                    or not monotone_em
                ):
                    continue

                valid_runs += 1

                log_likelihood = candidate.score(
                    scaled_features
                )

                candidate_states_decoded = candidate.predict(
                    scaled_features
                )

                state_sizes = np.bincount(
                    candidate_states_decoded,
                    minlength=n_states,
                ).tolist()

                if (
                    best_result is None
                    or log_likelihood
                    > best_result["log_likelihood"]
                ):
                    best_result = {
                        "seed": seed,
                        "log_likelihood": log_likelihood,
                        "state_sizes": state_sizes,
                    }

            if best_result is None:
                results.append(
                    {
                        "n_states": n_states,
                        "covariance_type": covariance_type,
                        "valid_runs": 0,
                    }
                )
                continue

            parameter_count = count_hmm_parameters(
                n_states,
                n_features,
                covariance_type,
            )

            log_likelihood = best_result["log_likelihood"]

            aic = (
                2 * parameter_count
                - 2 * log_likelihood
            )

            bic = (
                parameter_count * np.log(n_samples)
                - 2 * log_likelihood
            )

            results.append(
                {
                    "n_states": n_states,
                    "covariance_type": covariance_type,
                    "valid_runs": valid_runs,
                    "best_seed": best_result["seed"],
                    "log_likelihood": log_likelihood,
                    "parameters": parameter_count,
                    "aic": aic,
                    "bic": bic,
                    "state_sizes": best_result["state_sizes"],
                }
            )

    return results



def plot_three_state_hmm_geometry(features, states, state_means):
    """Plot the primary three-state HMM in 3D and three 2D views."""

    from pathlib import Path
    import matplotlib.pyplot as plt
    import numpy as np

    values = features.to_numpy()
    states = np.asarray(states)
    state_means = np.asarray(state_means)

    if values.shape[1] != 3:
        raise ValueError("Expected exactly three features.")
    if len(states) != len(values):
        raise ValueError("State labels must match observations.")
    if state_means.shape != (3, 3):
        raise ValueError("Expected three means in three dimensions.")

    names = list(features.columns)
    colors = ["tab:blue", "tab:orange", "tab:green"]

    fig = plt.figure(figsize=(15, 11))
    ax3d = fig.add_subplot(2, 2, 1, projection="3d")
    ax12 = fig.add_subplot(2, 2, 2)
    ax13 = fig.add_subplot(2, 2, 3)
    ax23 = fig.add_subplot(2, 2, 4)

    for state in range(3):
        mask = states == state
        points = values[mask]
        mean = state_means[state]
        color = colors[state]
        label = f"State {state} (n={mask.sum()})"

        ax3d.scatter(
            points[:, 0], points[:, 1], points[:, 2],
            s=7, alpha=0.30, color=color, label=label,
        )
        ax3d.scatter(
            mean[0], mean[1], mean[2],
            marker="X", s=130, color=color,
            edgecolor="black", linewidth=0.8,
        )

        for ax, i, j in [
            (ax12, 0, 1),
            (ax13, 0, 2),
            (ax23, 1, 2),
        ]:
            ax.scatter(
                points[:, i], points[:, j],
                s=7, alpha=0.30, color=color,
            )
            ax.scatter(
                mean[i], mean[j],
                marker="X", s=110, color=color,
                edgecolor="black", linewidth=0.8,
            )

    ax3d.set(
        xlabel=names[0], ylabel=names[1], zlabel=names[2],
        title="Full 3D feature space",
    )

    for ax, i, j, title in [
        (ax12, 0, 1, "Return vs Volatility"),
        (ax13, 0, 2, "Return vs Dispersion"),
        (ax23, 1, 2, "Volatility vs Dispersion"),
    ]:
        ax.set(
            xlabel=names[i],
            ylabel=names[j],
            title=title,
        )
        ax.grid(alpha=0.2)

    fig.suptitle(
        "Three-State Gaussian HMM: Feature-Space Geometry",
        fontsize=15,
    )
    fig.legend(
        *ax3d.get_legend_handles_labels(),
        loc="upper center",
        bbox_to_anchor=(0.5, 0.95),
        ncol=3,
    )
    fig.text(
        0.5, 0.015,
        "Colors: full-sequence decoded HMM states. "
        "X markers: fitted Gaussian state means. "
        "States are statistical descriptions, not live predictions.",
        ha="center", fontsize=9,
    )
    fig.tight_layout(rect=[0, 0.04, 1, 0.92])

    output = (
        Path(__file__).resolve().parents[1]
        / "results"
        / "hmm_three_state_geometry.png"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", output)


if __name__ == "__main__":
    features, scaled_features, scaler = prepare_hmm_data()

    print("HMM input data")
    print("--------------")
    print("Shape:", features.shape)
    print("First date:", features.index.min())
    print("Last date: ", features.index.max())

    print("\nStandardized feature means:")
    print(np.mean(scaled_features, axis=0))

    print("\nStandardized feature standard deviations:")
    print(np.std(scaled_features, axis=0))

    model, states = fit_initial_hmm(scaled_features)

    print("\nInitial 2-state Gaussian HMM")
    print("----------------------------")
    print("Converged:", model.monitor_.converged)
    print("EM iterations:", model.monitor_.iter)
    print(
        "Historical log-likelihood:",
        f"{model.score(scaled_features):.3f}",
    )

    print("\nInitial-state probabilities:")
    print(model.startprob_)

    print("\nTransition matrix:")
    print(model.transmat_)

    print("\nState sizes:")
    print(
        np.bincount(
            states,
            minlength=N_STATES,
        )
    )

    original_state_means = scaler.inverse_transform(
        model.means_
    )

    print("\nState means in original financial units:")
    for state, mean in enumerate(original_state_means):
        print(f"State {state}")
        for feature_name, value in zip(features.columns, mean):
            print(f"  {feature_name}: {value:.6f}")

    stability = initialization_stability(scaled_features)

    print("\nInitialization stability")
    print("------------------------")

    for result in stability:
        print(
            f"seed={result['seed']:4d}, "
            f"converged={result['converged']}, "
            f"iterations={result['iterations']:3d}, "
            f"logL={result['log_likelihood']:.3f}, "
            f"sizes={result['state_sizes']}, "
            f"ARI={result['ari_vs_seed_42']:.6f}"
        )

    durations = expected_state_durations(model)

    print("\nExpected state durations")
    print("------------------------")

    for state, duration in enumerate(durations):
        print(
            f"State {state}: "
            f"{duration:.2f} trading observations"
        )

    geometry = covariance_geometry(model, scaler)

    print("\nState covariance geometry")
    print("-------------------------")

    for result in geometry:
        print(f"\nState {result['state']}")
        print("Covariance matrix in original financial units:")
        print(result["covariance"])

        print("Eigenvalues:")
        print(result["eigenvalues"])

    primary_model, primary_states = fit_three_state_hmm(
        scaled_features
    )

    print("\nPrimary 3-state full-covariance Gaussian HMM")
    print("--------------------------------------------")

    print("Converged:", primary_model.monitor_.converged)
    print("Selected seed:", primary_model.selected_seed_)
    print("EM iterations:", primary_model.monitor_.iter)

    print(
        "Historical log-likelihood:",
        f"{primary_model.score(scaled_features):.3f}",
    )

    print("\nInitial-state probabilities:")
    print(primary_model.startprob_)

    print("\nTransition matrix:")
    print(primary_model.transmat_)

    primary_sizes = np.bincount(
        primary_states,
        minlength=3,
    )

    print("\nState sizes:")
    print(primary_sizes)

    print("State proportions:")
    print(primary_sizes / len(primary_states))

    primary_means = scaler.inverse_transform(
        primary_model.means_
    )

    print("\nState means in original financial units:")

    for state, mean in enumerate(primary_means):
        print(f"State {state}")

        for feature_name, value in zip(
            features.columns,
            mean,
        ):
            print(
                f"  {feature_name}: "
                f"{value:.6f}"
            )

    plot_three_state_hmm_geometry(
        features,
        primary_states,
        primary_means,
    )

    plot_three_state_hmm_timeline(
        primary_states,
        features.index,
    )

    primary_durations = expected_state_durations(
        primary_model
    )

    print("\nExpected 3-state durations")
    print("--------------------------")

    for state, duration in enumerate(
        primary_durations
    ):
        print(
            f"State {state}: "
            f"{duration:.2f} trading observations"
        )

    primary_geometry = covariance_geometry(
        primary_model,
        scaler,
    )

    print("\n3-state covariance geometry")
    print("---------------------------")

    for result in primary_geometry:
        print(f"\nState {result['state']}")

        print(
            "Covariance matrix in original "
            "financial units:"
        )
        print(result["covariance"])

        print("Eigenvalues:")
        print(result["eigenvalues"])

    primary_stability = (
        three_state_initialization_stability(
            scaled_features
        )
    )

    print("\n3-state initialization stability")
    print("--------------------------------")

    for result in primary_stability:
        log_likelihood = result["log_likelihood"]
        ari = result["ari_vs_seed_1"]

        log_text = (
            f"{log_likelihood:.3f}"
            if np.isfinite(log_likelihood)
            else "nan"
        )

        ari_text = (
            f"{ari:.6f}"
            if np.isfinite(ari)
            else "nan"
        )

        print(
            f"seed={result['seed']:4d}, "
            f"valid={result['valid']}, "
            f"converged={result['converged']}, "
            f"iterations={result['iterations']:3d}, "
            f"logL={log_text}, "
            f"sizes={result['state_sizes']}, "
            f"ARI_vs_seed_1={ari_text}"
        )

    plot_hmm_state_timeline(
        states,
        features.index,
    )

    hmm_switches, hmm_runs, _, _ = temporal_diagnostics(
        states,
        features.index,
    )

    kmeans_model, kmeans_labels = fit_baseline_kmeans(
        scaled_features
    )

    kmeans_switches, kmeans_runs, _, _ = temporal_diagnostics(
        kmeans_labels,
        features.index,
    )

    from sklearn.metrics import adjusted_rand_score

    hmm_kmeans_ari = adjusted_rand_score(
        states,
        kmeans_labels,
    )

    print("\nKMeans vs HMM temporal comparison")
    print("---------------------------------")

    print(
        "KMeans switches:",
        kmeans_switches,
        f"({100 * kmeans_switches / (len(kmeans_labels) - 1):.2f}%)",
    )

    print(
        "HMM switches:",
        hmm_switches,
        f"({100 * hmm_switches / (len(states) - 1):.2f}%)",
    )

    print("\nKMeans run-length statistics:")
    print(
        kmeans_runs.groupby("cluster")["length"]
        .agg(["count", "mean", "median", "max"])
    )

    print("\nHMM run-length statistics:")
    print(
        hmm_runs.groupby("cluster")["length"]
        .agg(["count", "mean", "median", "max"])
    )

    print(
        "\nARI between KMeans and HMM partitions:",
        f"{hmm_kmeans_ari:.6f}",
    )

    specification_results = compare_hmm_specifications(
        scaled_features
    )

    print("\nHMM specification comparison")
    print("----------------------------")

    for result in specification_results:
        if result["valid_runs"] == 0:
            print(
                f"K={result['n_states']}, "
                f"covariance={result['covariance_type']}: "
                "no converged runs"
            )
            continue

        print(
            f"K={result['n_states']}, "
            f"covariance={result['covariance_type']}, "
            f"valid={result['valid_runs']}/5, "
            f"best_seed={result['best_seed']}, "
            f"logL={result['log_likelihood']:.3f}, "
            f"p={result['parameters']}, "
            f"AIC={result['aic']:.3f}, "
            f"BIC={result['bic']:.3f}, "
            f"sizes={result['state_sizes']}"
        )

    (
        internal_train,
        internal_validation,
        validation_results,
    ) = chronological_hmm_validation(features)

    print("\nChronological HMM validation")
    print("----------------------------")

    print(
        "Training period:",
        internal_train.index.min(),
        "to",
        internal_train.index.max(),
        f"({len(internal_train)} observations)",
    )

    print(
        "Validation period:",
        internal_validation.index.min(),
        "to",
        internal_validation.index.max(),
        f"({len(internal_validation)} observations)",
    )

    for result in validation_results:
        if result["valid_runs"] == 0:
            print(
                f"K={result['n_states']}, "
                f"covariance={result['covariance_type']}: "
                "no valid runs"
            )
            continue

        print(
            f"K={result['n_states']}, "
            f"covariance={result['covariance_type']}, "
            f"valid={result['valid_runs']}/5, "
            f"best_seed={result['best_seed']}, "
            f"train_logL={result['train_log_likelihood']:.3f}, "
            f"val_logL={result['validation_log_likelihood']:.3f}, "
            f"val_logL_per_obs="
            f"{result['validation_log_likelihood_per_observation']:.6f}, "
            f"val_sizes={result['validation_state_sizes']}"
        )

    rolling_results = rolling_origin_hmm_validation(
        features
    )

    print("\nRolling-origin HMM validation")
    print("-----------------------------")

    for result in rolling_results:
        score_text = ", ".join(
            f"{score:.4f}"
            if np.isfinite(score)
            else "nan"
            for score in result["fold_scores"]
        )

        print(
            f"K={result['n_states']}, "
            f"covariance={result['covariance_type']}, "
            f"fold_scores=[{score_text}], "
            f"mean={result['mean_score']:.4f}, "
            f"std={result['std_score']:.4f}, "
            f"min_state_sizes="
            f"{result['minimum_state_sizes']}, "
            f"min_posterior_shares="
            f"{[round(x, 4) if np.isfinite(x) else np.nan for x in result['minimum_posterior_shares']]}"
        )
