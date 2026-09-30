"""
Covariance and Principal Component Analysis for Quant AI Market Lab.

This module analyzes the covariance structure of cross-asset
daily log returns and develops the PCA factor representation.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_RETURNS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "log_returns.csv"
)


RESULTS_DIR = PROJECT_ROOT / "results"


def load_log_returns():
    """
    Load the validated daily log-return matrix.
    """

    log_returns = pd.read_csv(
        LOG_RETURNS_PATH,
        index_col=0,
        parse_dates=True,
    )

    return log_returns
def compute_covariance_matrix(log_returns):
    """
    Compute and validate the sample covariance matrix
    of daily log returns.
    """

    covariance_matrix = log_returns.cov()

    symmetry_error = np.max(
        np.abs(
            covariance_matrix.to_numpy()
            - covariance_matrix.to_numpy().T
        )
    )

    minimum_eigenvalue = np.linalg.eigvalsh(
        covariance_matrix.to_numpy()
    ).min()

    if symmetry_error > 1e-12:
        raise RuntimeError(
            f"Covariance matrix is not symmetric: {symmetry_error}"
        )

    if minimum_eigenvalue < -1e-12:
        raise RuntimeError(
            "Covariance matrix failed the positive-semidefinite check: "
            f"{minimum_eigenvalue}"
        )

    print("Covariance matrix shape:", covariance_matrix.shape)
    print(f"Maximum symmetry error: {symmetry_error:.3e}")
    print(f"Minimum eigenvalue: {minimum_eigenvalue:.3e}")

    return covariance_matrix

def standardize_returns(log_returns):
    """
    Center and scale each asset's log returns
    to zero mean and unit sample standard deviation.
    """

    means = log_returns.mean()
    standard_deviations = log_returns.std()

    standardized_returns = (
        log_returns - means
    ) / standard_deviations

    maximum_mean_error = np.max(
        np.abs(standardized_returns.mean().to_numpy())
    )

    maximum_std_error = np.max(
        np.abs(
            standardized_returns.std().to_numpy() - 1.0
        )
    )

    if maximum_mean_error > 1e-12:
        raise RuntimeError(
            "Standardized returns failed zero-mean validation: "
            f"{maximum_mean_error}"
        )

    if maximum_std_error > 1e-12:
        raise RuntimeError(
            "Standardized returns failed unit-variance validation: "
            f"{maximum_std_error}"
        )

    print(
        "Maximum standardized-mean error: "
        f"{maximum_mean_error:.3e}"
    )
    print(
        "Maximum standardized-std error: "
        f"{maximum_std_error:.3e}"
    )

    return standardized_returns


def compute_pca(standardized_returns):
    """
    Compute PCA from the covariance matrix of standardized returns.
    """

    pca_matrix = standardized_returns.cov().to_numpy()

    eigenvalues, eigenvectors = np.linalg.eigh(pca_matrix)

    order = np.argsort(eigenvalues)[::-1]

    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]

    explained_variance_ratio = (
        eigenvalues / eigenvalues.sum()
    )

    orthogonality_error = np.max(
        np.abs(
            eigenvectors.T @ eigenvectors
            - np.eye(eigenvectors.shape[1])
        )
    )

    eigenvalue_sum_error = np.abs(
        eigenvalues.sum() - np.trace(pca_matrix)
    )

    print("\nPCA validation:")
    print(
        f"Maximum eigenvector orthogonality error: "
        f"{orthogonality_error:.3e}"
    )
    print(
        f"Eigenvalue-sum/trace error: "
        f"{eigenvalue_sum_error:.3e}"
    )
    print(
        "Explained variance ratio sum: "
        f"{explained_variance_ratio.sum():.12f}"
    )

    return (
        eigenvalues,
        eigenvectors,
        explained_variance_ratio,
    )

def plot_explained_variance(explained_variance_ratio):
    """
    Plot individual and cumulative PCA explained variance.
    """

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    component_numbers = np.arange(
        1,
        len(explained_variance_ratio) + 1,
    )

    cumulative_variance = np.cumsum(
        explained_variance_ratio
    )

    fig, ax = plt.subplots(figsize=(9, 6))

    ax.bar(
        component_numbers,
        explained_variance_ratio * 100,
        label="Individual explained variance",
    )

    ax.plot(
        component_numbers,
        cumulative_variance * 100,
        marker="o",
        label="Cumulative explained variance",
    )

    ax.set_xlabel("Principal Component")
    ax.set_ylabel("Explained Variance (%)")
    ax.set_title("PCA Explained Variance")
    ax.set_xticks(component_numbers)
    ax.set_ylim(0, 105)
    ax.legend()

    figure_path = RESULTS_DIR / "pca_explained_variance.png"

    plt.tight_layout()
    plt.savefig(
        figure_path,
        dpi=200,
        bbox_inches="tight",
    )

    print(f"Saved PCA figure to: {figure_path}")

    plt.close()

def plot_pca_loadings(loadings):
    """
    Plot the first three principal-component loadings.
    """

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 6))

    image = ax.imshow(
        loadings.to_numpy(),
        vmin=-1,
        vmax=1,
    )

    ax.set_xticks(range(loadings.shape[1]))
    ax.set_yticks(range(loadings.shape[0]))

    ax.set_xticklabels(loadings.columns)
    ax.set_yticklabels(loadings.index)

    for i in range(loadings.shape[0]):
        for j in range(loadings.shape[1]):
            ax.text(
                j,
                i,
                f"{loadings.iloc[i, j]:.2f}",
                ha="center",
                va="center",
            )

    ax.set_title("PCA Component Weights: First Three Components")

    fig.colorbar(
        image,
        ax=ax,
        label="Component Weight",
    )

    figure_path = RESULTS_DIR / "pca_loadings.png"

    plt.tight_layout()
    plt.savefig(
        figure_path,
        dpi=200,
        bbox_inches="tight",
    )

    print(f"Saved PCA loadings figure to: {figure_path}")

    plt.close()



if __name__ == "__main__":
    log_returns = load_log_returns()
    covariance_matrix = compute_covariance_matrix(log_returns)
    standardized_returns = standardize_returns(log_returns)

    standardized_covariance = standardized_returns.cov()
    correlation_matrix = log_returns.corr()

    correlation_equivalence_error = np.max(
        np.abs(
            standardized_covariance.to_numpy()
            - correlation_matrix.to_numpy()
        )
    )

    print(
        "Maximum standardized-covariance/correlation error: "
        f"{correlation_equivalence_error:.3e}"
    )



    
    eigenvalues, eigenvectors, explained_variance_ratio = (
    compute_pca(standardized_returns)
    )
 
    loadings = pd.DataFrame(
    eigenvectors[:, :3],
    index=log_returns.columns,
    columns=["PC1", "PC2", "PC3"],
    )

    print("\nPCA Component Weights (First Three Components):")
    print(loadings.round(4))
    
    plot_explained_variance(explained_variance_ratio)


    print("\nPCA Eigenvalues:")
    print(eigenvalues)

    print("\nExplained Variance Ratios:")
    print(explained_variance_ratio)
    daily_std = log_returns.std()
    correlation_matrix = log_returns.corr()

    diagonal_error = np.max(
        np.abs(
            np.diag(covariance_matrix.to_numpy())
            - daily_std.to_numpy() ** 2
        )
    )

    D = np.diag(daily_std.to_numpy())

    reconstructed_covariance = (
        D
        @ correlation_matrix.to_numpy()
        @ D
    )

    reconstruction_error = np.max(
        np.abs(
            covariance_matrix.to_numpy()
            - reconstructed_covariance
        )
    )
    plot_pca_loadings(loadings)
    print(f"Maximum variance-diagonal error: {diagonal_error:.3e}")
    print(
        "Maximum covariance reconstruction error: "
        f"{reconstruction_error:.3e}"
    )

    print("Log-return matrix shape:", log_returns.shape)
    print("Assets:", list(log_returns.columns))

    print("\nDaily Return Covariance Matrix:")
    print(covariance_matrix)
