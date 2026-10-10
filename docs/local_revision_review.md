# My baseline development record and remaining issues

I prepared the local revisions on October 10, 2026 before publishing the baseline. I developed and tested these revisions locally before integrating this baseline. The frozen audited source remains unchanged.

## Checker changes

I separated NumPy generator seeding from global seeding, rejected explicit None seeds as seed evidence, removed randomness warnings for ordinary deterministic folds, included positional-only and variadic parameters, used symbol-table scope information for nested names, rejected nonexistent targets, and stopped treating empty test directories as evidence of tests.

I added twenty regression tests. The complete thirty-six-test suite passes. I repeated the twenty designed examples and rescanned the same frozen Quant AI Market Lab source; ten candidates remain. I do not interpret this as complete defect detection.

## Claim 7 remains a narrow finding

The ten original tests support the cost calculation in their tested cases. They do not reproduce full portfolio results. The static call-chain tests establish that matching calls with a cost keyword exist, not that every execution path uses the correct rate.

The review exposed two unresolved input-validation gaps in the frozen audited function:

1. `np.isclose(weights.sum(), 1.0, atol=1e-10)` retains NumPy's default relative tolerance. `[0.5, 0.500009]` is accepted, so allocated holdings can exceed reported portfolio value.
2. Two-dimensional weight arrays are accepted and can broadcast against one-dimensional holdings, changing the traded-value calculation.

I preserve this frozen source unchanged. Improving a screening checker does not repair the audited portfolio implementation. The isolated tests should not be described as rejecting every malformed input. The uniqueness proof for the cost equation assumes nonnegative weights summing exactly to one and a rate below one; numerical acceptance of near-unit or mis-shaped weights needs a separate implementation review.

## Packaging and provenance

I exclude bytecode caches. I include the frozen Python source and README needed to run the isolated checks; no raw market data are included. The snapshot comes from `Souravfrp/research-audit` commit `5f353c9d72ea69aaa1c39e76c77be5ed0044220d` under `targets/quant-ai-market-lab-v1.0.0/`. `snapshot_provenance.json` records exact blob IDs and SHA-256 hashes.

The old report is retained under `results/baseline/`; the integrated report is under `results/published_baseline/`. The test log and environment record are in `results/`. I publish this work as a baseline release, not a claim that all seven inventory items were independently verified.

## Local revision v2

I added explicit scan coverage, readable-source hashes, decoding and parsing failure reporting, dependency/cache exclusions, symlink exclusions, source encoding support, and default refusal to overwrite existing reports. Seven additional test methods bring the suite to 43. This remains a screening tool, not an external audit or real-world detection benchmark. The frozen source and its known transaction-cost validation issues remain unchanged.

## Revision v3: claim scope and regression evidence

I moved Claim 7's two-gap qualification into its status line and stated the exact nonnegative, one-dimensional, unit-sum weight assumptions for uniqueness. Two characterization tests record the existing over-allocation and matrix-broadcasting behaviours. The frozen audited source is unchanged.

I added centered rolling and literal negative diff/pct_change checks to RC01. Variable settings, aliased split/model imports, RandomState and lambda handling remain explicit blind spots. The main-guard seed warning is documented as conservative. All 52 test methods pass, with the two known-bug tests clearly separated from valid-accounting tests. I do not use this to claim all seven inventory items verified.

## Integration into ResearchAudit

I retain the original project motivation and multi-agent plan, update C07 in the existing inventory, and publish only the completed baseline work. Second-project evaluation, independent detection accuracy, full numerical reproduction and multi-agent implementation remain pending.
