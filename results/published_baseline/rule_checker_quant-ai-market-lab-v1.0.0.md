# Rule-based checker report: quant-ai-market-lab-v1.0.0

Each row is a candidate issue for a human to judge. A finding is not a verdict.

Scan status: complete_for_eligible_files
Python files checked: 34 / 34.
Complete means only that eligible files were readable and parsed; it is not a correctness verdict.
Not checked: Dataflow and cross-file seed execution; Mathematical correctness; Result reproduction; Statistical validity; Test execution or coverage; Variable-valued periods, shuffle and center settings; Aliased model/split imports such as train_test_split as tts; RandomState seed tracking and lambda execution/scope handling; Conditional seeds including if __name__ == '__main__' are not certified.

Total findings: 10.

| Rule | Title | Severity | Count |
|---|---|---|---|
| RC01 | Future-aligned shift/difference or centered rolling window | review | 2 |
| RC03 | Fitted transformer: check it is fitted on training data only | review | 7 |
| RC08 | No matching Python test files found | info | 1 |

## Findings

| Rule | File | Line | Code | Reason |
|---|---|---|---|---|
| RC03 | `src/regime_clustering.py` | 45 | `scaler = StandardScaler()` | StandardScaler learns parameters from data. Check which dates it is fitted on. |
| RC03 | `src/regime_clustering.py` | 46 | `scaled_features = scaler.fit_transform(features)` | Check that this transformer is fitted on training dates only. |
| RC03 | `src/regime_hmm.py` | 510 | `scaler = StandardScaler()` | StandardScaler learns parameters from data. Check which dates it is fitted on. |
| RC03 | `src/regime_hmm.py` | 512 | `train_scaled = scaler.fit_transform(` | Check that this transformer is fitted on training dates only. |
| RC03 | `src/regime_hmm.py` | 682 | `scaler = StandardScaler()` | StandardScaler learns parameters from data. Check which dates it is fitted on. |
| RC03 | `src/regime_hmm.py` | 683 | `train_scaled = scaler.fit_transform(train_features)` | Check that this transformer is fitted on training dates only. |
| RC01 | `src/ridge_alpha_validation.py` | 16 | `target_end = pd.Series(spy.index, index=spy.index).shift(-5)` | shift with a negative literal period uses later observations. Targets may legitimately do this; review whether the result feeds a feature. |
| RC03 | `src/ridge_risk_forecasting.py` | 26 | `model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))` | StandardScaler learns parameters from data. Check which dates it is fitted on. |
| RC01 | `src/risk_full_history_plot.py` | 26 | `target_end = spy.index.to_series().shift(-5)` | shift with a negative literal period uses later observations. Targets may legitimately do this; review whether the result feeds a feature. |
| RC08 | `.` | 0 | `` | No eligible Python test filenames. File presence alone would not prove valid tests or coverage. |
