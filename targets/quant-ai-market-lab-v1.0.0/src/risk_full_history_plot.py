"""Plot historical five-day SPY risk and the forecasting split."""

from pathlib import Path

import matplotlib.pyplot as plt

from src.temporal_split import CUTOFF_DATE, load_log_returns
from src.regime_features import construct_regime_features
from src.risk_forecasting import (
    construct_risk_target,
    split_forecasting_dates,
)


def main():
    returns = load_log_returns()
    spy = returns["SPY"]
    features = construct_regime_features(returns)
    target = construct_risk_target(spy)

    train, validation, _ = split_forecasting_dates(
        spy, features.index, target, CUTOFF_DATE
    )

    # A historical target must end no later than the cutoff.
    target_end = spy.index.to_series().shift(-5)
    historical = target.loc[
        target_end.le(CUTOFF_DATE) & target.notna()
    ]

    if historical.empty or len(validation) == 0:
        raise ValueError("Historical target or validation dates missing.")

    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(
        historical.index,
        historical,
        linewidth=1,
        label="Realized future five-day RMS",
    )
    ax.axvline(
        validation.min(),
        color="black",
        linestyle="--",
        linewidth=1.2,
        label="Validation starts: 2024-01-23",
    )

    ax.set(
        title=(
            "SPY five-day risk: full historical overview\n"
            "Historical targets ending by 2026-04-30"
        ),
        xlabel="Forecast date",
        ylabel="Daily log-return RMS",
    )
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()

    output = Path("results/risk_full_history_overview.png")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160)
    plt.close(fig)

    print("First plotted date:", historical.index.min().date())
    print("Last plotted date:", historical.index.max().date())
    print("Plotted observations:", len(historical))
    print("Training examples:", len(train))
    print("Validation examples:", len(validation))
    print("Saved figure:", output)


if __name__ == "__main__":
    main()
