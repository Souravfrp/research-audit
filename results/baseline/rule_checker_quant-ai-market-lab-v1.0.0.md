# Rule-based checker report: quant-ai-market-lab-v1.0.0

Each row is a candidate issue for a human to judge. A finding is not a verdict.

Total findings: 10.

| Rule | Title | Severity | Count |
|---|---|---|---|
| RC01 | Negative shift | review | 2 |
| RC03 | Fitted transformer: check it is fitted on training data only | review | 7 |
| RC08 | No automated tests found | info | 1 |

## Findings

| Rule | File | Line | Code | Reason |
|---|---|---|---|---|
| RC03 | `src/regime_clustering.py` | 45 | `scaler = StandardScaler()` | StandardScaler learns parameters from data. Check which dates it is fitted on. |
| RC03 | `src/regime_clustering.py` | 46 | `scaled_features = scaler.fit_transform(features)` | Check that this transformer is fitted on training dates only. |
| RC03 | `src/regime_hmm.py` | 510 | `scaler = StandardScaler()` | StandardScaler learns parameters from data. Check which dates it is fitted on. |
| RC03 | `src/regime_hmm.py` | 512 | `train_scaled = scaler.fit_transform(` | Check that this transformer is fitted on training dates only. |
| RC03 | `src/regime_hmm.py` | 682 | `scaler = StandardScaler()` | StandardScaler learns parameters from data. Check which dates it is fitted on. |
| RC03 | `src/regime_hmm.py` | 683 | `train_scaled = scaler.fit_transform(train_features)` | Check that this transformer is fitted on training dates only. |
| RC01 | `src/ridge_alpha_validation.py` | 16 | `target_end = pd.Series(spy.index, index=spy.index).shift(-5)` | A negative shift moves later values onto earlier rows. This is correct when building a forecasting target, and a look-ahead error if it feeds a feature. |
| RC03 | `src/ridge_risk_forecasting.py` | 26 | `model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))` | StandardScaler learns parameters from data. Check which dates it is fitted on. |
| RC01 | `src/risk_full_history_plot.py` | 26 | `target_end = spy.index.to_series().shift(-5)` | A negative shift moves later values onto earlier rows. This is correct when building a forecasting target, and a look-ahead error if it feeds a feature. |
| RC08 | `.` | 0 | `` | No tests/ folder or test_*.py files. Some projects check results inside the scripts instead, which this rule does not inspect. |
