# My baseline evaluation

I publish the rule-based audit baseline and isolated transaction-cost checks on October 10, 2026. My multi-agent system remains planned.

| Check | Outcome | What it means |
|---|---|---|
| Frozen Python source | 34 files checked; no read or parse failures. | Coverage, not correctness. |
| Candidate findings | RC01: 2; RC03: 7; RC08: 1. | Ten items requiring review. |
| Designed examples | 20 of 20 behave as designed, exercised inside one test method. | Functional checks, not independent accuracy measurement. |
| Integrated tests | 52 methods pass: 40 checker, 10 original cost, 2 known-gap characterization tests. | The two gap tests reproduce problems rather than approve them. |
| Audited source | Preserved unchanged. | Input-validation gaps remain unresolved. |
| Full financial outputs | Not reproduced. | No independent validation of reported portfolio performance. |

The two RC01 candidates construct target-end dates and were judged safeguards in my earlier triage. RC03 includes correct training-only transformations and descriptive full-history scaling requiring context. RC08 observes no separate matching tests in the target. I confirmed no look-ahead error among the inspected flagged locations; I do not establish absence of leakage across the project.

## Claim 7

The cost equation has a unique solution for one-dimensional nonnegative weights summing exactly to one and a rate below one. The implementation does not strictly enforce the weight assumptions. My status line records the two validation gaps: accepted above-unit totals and matrix weights that broadcast. The characterization tests retain evidence of both. A future corrected snapshot should test rejection or corrected accounting instead. Static call-chain checks establish matching cost-keyword calls exist, not that all runtime paths use intended rates.

C01-C06 retain provisional source-inspection labels. I do not write "all seven claims verified." The [inventory](../claims/claim_inventory.md) and [C07 note](../claims/claim_07_transaction_costs.md) preserve the distinction.

## Remaining stages

I have not evaluated a second complete frozen project, measured independent real-world detection accuracy, built the Ollama agents and coordinator, or performed agent-consistency and baseline-comparison experiments. Full financial numerical reproduction requires separate preserved market data and dependencies. These stages are pending, not requirements already satisfied by passing the designed examples.

The checker still misses variable-valued future periods/shuffle settings, aliased split imports and RandomState/lambda execution paths. It can flag correctly seeded main-guard code conservatively. A complete eligible-file scan does not prove chronology, mathematical correctness or statistical validity.

## Evidence

The original baseline report is retained under `results/baseline/`; the current integrated report is under `results/published_baseline/`. The [verification record](../results/baseline_verification.json), [test log](../results/integrated_test_log.txt), [checker notes](rule_based_checker.md) and [snapshot provenance](../snapshot_provenance.json) explain the checks and inputs. The root README gives reproduction commands.
