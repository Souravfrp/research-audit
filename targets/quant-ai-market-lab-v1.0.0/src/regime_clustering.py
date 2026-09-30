"""
Baseline KMeans analysis for market-condition features.

This module treats KMeans as a geometric baseline rather than assuming
that its clusters are genuine persistent market regimes.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from src.regime_features import construct_regime_features
from src.temporal_split import (
    load_log_returns,
    temporal_split,
    validate_returns,
)

MIN_CLUSTERS = 2
MAX_CLUSTERS = 8
BASELINE_CLUSTERS = 2
N_INIT = 20
RANDOM_STATE = 42


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results"

def standardize_features(features):
    """
    Standardize each feature using statistics fitted on historical data.
    """
    feature_values = features.to_numpy()

    if not np.isfinite(feature_values).all():
        raise ValueError(
            "Input features contain non-finite values."
        )

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    if not np.isfinite(scaled_features).all():
        raise ValueError(
            "Standardized features contain non-finite values."
        )

    return scaled_features, scaler

def evaluate_candidate_clusters(scaled_features):
    """
    Evaluate candidate KMeans partitions using inertia and silhouette score.
    """
    diagnostics = []

    for k in range(MIN_CLUSTERS, MAX_CLUSTERS + 1):
        model = KMeans(
            n_clusters=k,
            init="k-means++",
            n_init=N_INIT,
            random_state=RANDOM_STATE,
        )

        labels = model.fit_predict(scaled_features)

        diagnostics.append(
            {
                "k": k,
                "inertia": model.inertia_,
                "silhouette": silhouette_score(
                    scaled_features,
                    labels,
                ),
                "cluster_sizes": np.bincount(
                    labels,
                    minlength=k,
                ).tolist(),
            }
        )

    return diagnostics


def fit_baseline_kmeans(scaled_features):
    """
    Fit the selected K=2 baseline partition.
    """
    model = KMeans(
        n_clusters=BASELINE_CLUSTERS,
        init="k-means++",
        n_init=N_INIT,
        random_state=RANDOM_STATE,
    )

    labels = model.fit_predict(scaled_features)

    return model, labels

def plot_cluster_geometry(features, labels, centroids):
    """
    Visualize the KMeans partition in the original feature coordinates.

    Points are colored by cluster assignment and cluster centroids are
    marked separately. These plots are diagnostic views of the KMeans
    partition, not evidence that the clusters are true market regimes.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    centroid_frame = pd.DataFrame(
        centroids,
        columns=features.columns,
    )

    pairs = [
        (
            "spy_return",
            "spy_volatility_20d",
            "SPY Return vs 20-Day Volatility",
            "kmeans_return_vs_volatility.png",
        ),
        (
            "spy_return",
            "cross_asset_dispersion",
            "SPY Return vs Cross-Asset Dispersion",
            "kmeans_return_vs_dispersion.png",
        ),
        (
            "spy_volatility_20d",
            "cross_asset_dispersion",
            "20-Day Volatility vs Cross-Asset Dispersion",
            "kmeans_volatility_vs_dispersion.png",
        ),
    ]

    for x_column, y_column, title, filename in pairs:
        plt.figure(figsize=(8, 6))

        for cluster in range(BASELINE_CLUSTERS):
            cluster_mask = labels == cluster

            plt.scatter(
                features.loc[cluster_mask, x_column],
                features.loc[cluster_mask, y_column],
                alpha=0.45,
                s=16,
                label=f"Cluster {cluster}",
            )

        plt.scatter(
            centroid_frame[x_column],
            centroid_frame[y_column],
            marker="X",
            s=180,
            edgecolors="black",
            linewidths=1.2,
            label="KMeans centroids",
        )

        plt.xlabel(x_column.replace("_", " ").title())
        plt.ylabel(y_column.replace("_", " ").title())
        plt.title(f"KMeans Baseline: {title}")
        plt.legend()
        plt.grid(alpha=0.25)
        plt.tight_layout()

        output_path = RESULTS_DIR / filename
        plt.savefig(output_path, dpi=160)
        plt.close()

        print("Saved:", output_path)

def plot_cluster_timeline(labels, index):
    """
    Plot KMeans cluster assignments through historical time.

    This is a post-clustering temporal diagnostic. KMeans itself does not
    use chronological ordering when assigning observations to clusters.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    regimes = pd.Series(
        labels,
        index=index,
        name="cluster",
    )

    plt.figure(figsize=(12, 3))

    for cluster in range(BASELINE_CLUSTERS):
        cluster_mask = regimes == cluster

        plt.scatter(
            regimes.index[cluster_mask],
            regimes.loc[cluster_mask],
            s=10,
            alpha=0.7,
            label=f"Cluster {cluster}",
        )

    plt.yticks(
        range(BASELINE_CLUSTERS),
        [f"Cluster {k}" for k in range(BASELINE_CLUSTERS)],
    )
    plt.xlabel("Date")
    plt.ylabel("KMeans cluster")
    plt.title("KMeans Baseline Cluster Assignments Through Time")
    plt.legend()
    plt.grid(axis="x", alpha=0.25)
    plt.tight_layout()

    output_path = RESULTS_DIR / "kmeans_cluster_timeline.png"
    plt.savefig(output_path, dpi=160)
    plt.close()

    print("Saved:", output_path)



def plot_3d_cluster_comparison(
    features,
    scaled_features,
    labels,
    original_centroids,
    standardized_centroids,
):
    """
    Compare the same KMeans partition in original and standardized 3D space.

    KMeans is fitted using the complete historical feature matrix.
    Percentile-based axis limits are used only to improve visualization;
    observations outside the displayed window remain part of model fitting.
    """
    from matplotlib.patches import Patch

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    original_values = features.to_numpy()

    # Display the central feature-space geometry without changing the model.
    lower_percentile = 1
    upper_percentile = 99

    original_lower = np.percentile(
        original_values,
        lower_percentile,
        axis=0,
    )
    original_upper = np.percentile(
        original_values,
        upper_percentile,
        axis=0,
    )

    standardized_lower = np.percentile(
        scaled_features,
        lower_percentile,
        axis=0,
    )
    standardized_upper = np.percentile(
        scaled_features,
        upper_percentile,
        axis=0,
    )

    original_visible = np.all(
        (original_values >= original_lower)
        & (original_values <= original_upper),
        axis=1,
    )

    standardized_visible = np.all(
        (scaled_features >= standardized_lower)
        & (scaled_features <= standardized_upper),
        axis=1,
    )

    original_hidden = int((~original_visible).sum())
    standardized_hidden = int((~standardized_visible).sum())

    fig = plt.figure(figsize=(18, 8))

    ax_original = fig.add_subplot(
        1, 2, 1, projection="3d"
    )
    ax_standardized = fig.add_subplot(
        1, 2, 2, projection="3d"
    )

    # Plot all observations. Axis limits control only what is displayed.
    for cluster in range(BASELINE_CLUSTERS):
        cluster_mask = labels == cluster

        ax_original.scatter(
            original_values[cluster_mask, 0],
            original_values[cluster_mask, 1],
            original_values[cluster_mask, 2],
            s=12,
            alpha=0.40,
            label=(
                f"Cluster {cluster} "
                f"(n={int(cluster_mask.sum())})"
            ),
        )

        ax_standardized.scatter(
            scaled_features[cluster_mask, 0],
            scaled_features[cluster_mask, 1],
            scaled_features[cluster_mask, 2],
            s=12,
            alpha=0.40,
            label=(
                f"Cluster {cluster} "
                f"(n={int(cluster_mask.sum())})"
            ),
        )

    ax_original.scatter(
        original_centroids[:, 0],
        original_centroids[:, 1],
        original_centroids[:, 2],
        marker="X",
        s=220,
        edgecolors="black",
        linewidths=1.3,
        label="KMeans centroids",
    )

    ax_standardized.scatter(
        standardized_centroids[:, 0],
        standardized_centroids[:, 1],
        standardized_centroids[:, 2],
        marker="X",
        s=220,
        edgecolors="black",
        linewidths=1.3,
        label="KMeans centroids",
    )

    # K=2 equal-distance decision plane in standardized coordinates:
    #
    # 2(c1-c0)^T z = ||c1||^2 - ||c0||^2.
    c0 = standardized_centroids[0]
    c1 = standardized_centroids[1]

    normal = 2.0 * (c1 - c0)
    rhs = np.dot(c1, c1) - np.dot(c0, c0)

    solve_axis = int(np.argmax(np.abs(normal)))
    free_axes = [j for j in range(3) if j != solve_axis]

    grid_a = np.linspace(
        standardized_lower[free_axes[0]],
        standardized_upper[free_axes[0]],
        30,
    )
    grid_b = np.linspace(
        standardized_lower[free_axes[1]],
        standardized_upper[free_axes[1]],
        30,
    )

    mesh_a, mesh_b = np.meshgrid(grid_a, grid_b)

    coordinates = [None, None, None]
    coordinates[free_axes[0]] = mesh_a
    coordinates[free_axes[1]] = mesh_b

    coordinates[solve_axis] = (
        rhs
        - normal[free_axes[0]] * mesh_a
        - normal[free_axes[1]] * mesh_b
    ) / normal[solve_axis]

    ax_standardized.plot_surface(
        coordinates[0],
        coordinates[1],
        coordinates[2],
        alpha=0.22,
        linewidth=0,
    )

    # Apply display limits only. No observation is removed from KMeans.
    ax_original.set_xlim(
        original_lower[0],
        original_upper[0],
    )
    ax_original.set_ylim(
        original_lower[1],
        original_upper[1],
    )
    ax_original.set_zlim(
        original_lower[2],
        original_upper[2],
    )

    ax_standardized.set_xlim(
        standardized_lower[0],
        standardized_upper[0],
    )
    ax_standardized.set_ylim(
        standardized_lower[1],
        standardized_upper[1],
    )
    ax_standardized.set_zlim(
        standardized_lower[2],
        standardized_upper[2],
    )

    ax_original.set_xlabel("SPY daily log return")
    ax_original.set_ylabel("SPY 20-day volatility")
    ax_original.set_zlabel("Cross-asset dispersion")
    ax_original.set_title(
        "(A) Original Financial Coordinates\n"
        "1st-99th percentile axis limits (visualization only)"
    )

    ax_standardized.set_xlabel(
        "Standardized SPY daily log return"
    )
    ax_standardized.set_ylabel(
        "Standardized SPY 20-day volatility"
    )
    ax_standardized.set_zlabel(
        "Standardized cross-asset dispersion"
    )
    ax_standardized.set_title(
        "(B) Standardized Coordinates\n"
        "1st-99th percentile axis limits (visualization only)"
    )

    # Same viewing angle makes the coordinate transformation comparable.
    ax_original.view_init(elev=25, azim=-55)
    ax_standardized.view_init(elev=25, azim=-55)

    # Place centroid labels near the points with readable backgrounds.
    original_offsets = [
        (0.0015, 0.0015, 0.0020),
        (0.0015, 0.0015, 0.0020),
    ]

    standardized_offsets = [
        (0.15, 0.15, 0.20),
        (0.15, 0.15, 0.20),
    ]

    for cluster in range(BASELINE_CLUSTERS):
        x, y, z = original_centroids[cluster]
        dx, dy, dz = original_offsets[cluster]

        ax_original.text(
            x + dx,
            y + dy,
            z + dz,
            (
                f"Cluster {cluster} centroid\n"
                f"({x:.6f}, {y:.6f}, {z:.6f})"
            ),
            fontsize=8,
            bbox={
                "boxstyle": "round,pad=0.3",
                "facecolor": "white",
                "alpha": 0.85,
            },
        )

        sx, sy, sz = standardized_centroids[cluster]
        dx, dy, dz = standardized_offsets[cluster]

        ax_standardized.text(
            sx + dx,
            sy + dy,
            sz + dz,
            (
                f"Cluster {cluster} centroid\n"
                f"({sx:.3f}, {sy:.3f}, {sz:.3f})"
            ),
            fontsize=8,
            bbox={
                "boxstyle": "round,pad=0.3",
                "facecolor": "white",
                "alpha": 0.85,
            },
        )

    ax_original.legend(loc="upper left")

    handles, legend_labels = (
        ax_standardized.get_legend_handles_labels()
    )
    handles.append(
        Patch(
            alpha=0.22,
            label="KMeans decision plane",
        )
    )
    legend_labels.append("KMeans decision plane")

    ax_standardized.legend(
        handles,
        legend_labels,
        loc="upper left",
    )

    fig.suptitle(
        "KMeans Baseline: Original vs Standardized 3D Geometry",
        fontsize=15,
    )

    fig.text(
        0.5,
        0.012,
        (
            "KMeans uses all 2,828 historical observations. "
            "Axis limits show the 1st-99th percentile range only "
            "for visual clarity; observations outside the displayed "
            f"window are not removed from model fitting. "
            f"{original_hidden} observations fall outside the displayed "
            "axis limits; all observations are retained in model fitting."
        ),
        ha="center",
        fontsize=9,
    )

    plt.tight_layout(rect=[0, 0.07, 1, 0.94])

    output_path = RESULTS_DIR / "kmeans_3d_comparison.png"

    plt.savefig(
        output_path,
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)

    print("Saved:", output_path)
    print(
        "Original-coordinate observations outside display window:",
        original_hidden,
    )
    print(
        "Standardized-coordinate observations outside display window:",
        standardized_hidden,
    )

def temporal_diagnostics(labels, index):
    """
    Measure persistence and transitions of consecutive KMeans labels.

    These statistics diagnose temporal behavior after clustering.
    KMeans itself does not use time ordering.
    """
    regimes = pd.Series(
        labels,
        index=index,
        name="cluster",
    )

    switches = int(
        (
            regimes.iloc[1:].to_numpy()
            != regimes.iloc[:-1].to_numpy()
        ).sum()
    )

    run_id = regimes.ne(regimes.shift()).cumsum()

    runs = pd.DataFrame(
        {
            "cluster": regimes.groupby(run_id).first().to_numpy(),
            "length": regimes.groupby(run_id).size().to_numpy(),
        }
    )

    previous = regimes.iloc[:-1].to_numpy()
    current = regimes.iloc[1:].to_numpy()

    transition_counts = pd.crosstab(
        pd.Series(previous, name="from"),
        pd.Series(current, name="to"),
    )

    transition_probabilities = transition_counts.div(
        transition_counts.sum(axis=1),
        axis=0,
    )

    return (
        switches,
        runs,
        transition_counts,
        transition_probabilities,
    )


def initialization_stability(scaled_features):
    """
    Compare K=2 solutions across several random seeds.
    """
    seeds = [0, 1, 2, 3, 4, 10, 42, 100, 2026]
    solutions = {}
    diagnostics = []

    for seed in seeds:
        model = KMeans(
            n_clusters=BASELINE_CLUSTERS,
            init="k-means++",
            n_init=N_INIT,
            random_state=seed,
        )

        labels = model.fit_predict(scaled_features)
        solutions[seed] = labels

        diagnostics.append(
            {
                "seed": seed,
                "inertia": model.inertia_,
                "cluster_sizes": np.bincount(
                    labels,
                    minlength=BASELINE_CLUSTERS,
                ).tolist(),
            }
        )

    reference = solutions[RANDOM_STATE]

    for result in diagnostics:
        result["ari_vs_reference"] = adjusted_rand_score(
            reference,
            solutions[result["seed"]],
        )

    return diagnostics

if __name__ == "__main__":
    returns = load_log_returns()
    validate_returns(returns)

    historical, _ = temporal_split(returns)
    features = construct_regime_features(historical)

    scaled_features, scaler = standardize_features(features)

    print("Candidate KMeans diagnostics")
    print("----------------------------")

    diagnostics = evaluate_candidate_clusters(
        scaled_features
    )

    for result in diagnostics:
        print(
            f"K={result['k']}: "
            f"inertia={result['inertia']:.3f}, "
            f"silhouette={result['silhouette']:.4f}, "
            f"sizes={result['cluster_sizes']}"
        )

    model, labels = fit_baseline_kmeans(
        scaled_features
    )

    centroids = scaler.inverse_transform(
        model.cluster_centers_
    )

    plot_cluster_geometry(
        features,
        labels,
        centroids,
    )

    plot_cluster_timeline(
        labels,
        features.index,
    )

    plot_3d_cluster_comparison(
        features,
        scaled_features,
        labels,
        centroids,
        model.cluster_centers_,
    )

    print("\nK=2 baseline centroids")
    print("----------------------")

    for cluster, centroid in enumerate(centroids):
        print(f"\nCluster {cluster}")
        for feature_name, value in zip(
            features.columns,
            centroid,
        ):
            print(f"  {feature_name}: {value:.6f}")

    (
        switches,
        runs,
        transition_counts,
        transition_probabilities,
    ) = temporal_diagnostics(
        labels,
        features.index,
    )

    print("\nTemporal diagnostics")
    print("--------------------")
    print("Number of regime switches:", switches)
    print(
        "Switch rate:",
        f"{100 * switches / (len(labels) - 1):.2f}%"
    )

    print("\nRun-length statistics:")
    print(
        runs.groupby("cluster")["length"]
        .agg(["count", "mean", "median", "max"])
    )

    print("\nTransition counts:")
    print(transition_counts)

    print("\nTransition probabilities:")
    print(transition_probabilities)

    stability = initialization_stability(
        scaled_features
    )

    print("\nInitialization stability")
    print("------------------------")

    for result in stability:
        print(
            f"seed={result['seed']:4d}, "
            f"inertia={result['inertia']:.6f}, "
            f"sizes={result['cluster_sizes']}, "
            f"ARI={result['ari_vs_reference']:.6f}"
        )
