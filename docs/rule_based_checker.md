# My improved rule-based checker

I use this as a baseline before any agent-based audit. Findings are candidate locations for review, not verdicts. This local revision improves the earlier syntax rules without claiming complete program understanding.

## My rules and their scope

| Rule | What I screen | Limits |
|---|---|---|
| RC01 | Literal negative periods in `shift`, `diff`, `pct_change`; `rolling(center=True)` | Targets or retrospective summaries may legitimately use them; variable settings, receiver types and downstream dataflow are not resolved. |
| RC02 | Recognized shuffled splits and shuffled folds | A non-shuffled KFold can still train on later rows; absence of this finding is not chronological validation. |
| RC03 | Recognized transformer constructors and `fit_transform` | Correct training-only use is still flagged for review. No date/dataflow analysis. |
| RC04 | Missing or explicit `None` seeds in recognized constructors; NumPy global calls without a recognized fixed preceding module seed | Separate generators do not seed the global RNG. Variables, execution order across functions/files, alias reassignment and shadowing remain unresolved. |
| RC05 | Sensitive parameter names with no static reference | Includes positional-only, keyword-only and variadic parameters. Python symbol tables distinguish genuine closure references from shadowed nested names. A reference does not prove the setting affects the result. |
| RC06 | Selected hard-coded absolute-path patterns | Not every platform path or dynamically built path is covered. |
| RC07 | Bare exceptions or pass-only handlers | Does not detect every form of suppressed failure. |
| RC08 | No Python files matching `test_*.py` or `*_test.py` | An empty `tests/` folder is insufficient. Matching files do not establish valid tests, execution or coverage. |
| RC00 | Source syntax could not be parsed | The file was not checked by the other source rules. |

I reject missing targets and file paths supplied where a project directory is required. Reports state how many Python files were scanned, the rule set and the checks not performed. A project with zero Python files cannot be treated as audited.

## How I handle randomness

A separately seeded `np.random.default_rng(1)` does not suppress a warning for `np.random.rand(...)`. Explicit `random_state=None` and `default_rng(None)` are candidates. Ordinary non-shuffled KFold and StratifiedKFold do not receive a randomness warning; this says nothing about time-series suitability.

I recognize simple module imports and aliases, and literal integer NumPy global seed calls that precede module-level draws. A seed after a draw does not cover that draw. Comments do not seed anything. A subsequent unknown or None seed invalidates the simple known-seed state. Function-body draws remain review candidates even when the module has a seed, because execution order can differ from source order.

I do not track cross-file seeds, dynamic aliases, rebinding, imported wrapper functions, variable-valued seeds, seed arrays, or all control-flow paths. Variable-valued model seeds are accepted as explicit syntax, but their value and actual effect remain unverified. False positives and false negatives remain possible.

## Parameters and scopes

I combine the AST with Python's symbol table. An inner function parameter named `cost_bps` does not count as using an outer `cost_bps`. A genuine free-variable reference in a closure does count as a static reference. I do not prove the closure executes, the parameter changes an output, or a parameter was not overwritten before use. These require semantic or runtime checks.

## Computational claims

I parse source, traverse the AST, inspect symbol-table scopes and sort findings. I do not claim the entire implementation is strictly linear. Some seed checks scan module statements, and closure checks inspect nested scopes. With A AST nodes and depth D, additional inspections can exceed O(A); conservative worst-case quadratic behaviour is possible. Sorting F findings costs O(F log F). This is a small-project baseline, not a runtime benchmark.

## What I verified

- Six original checker test methods still pass, including their twenty designed examples.
- Twenty new regression tests cover the observed gaps and related counterexamples.
- Ten transaction-cost test methods pass on the isolated function from the frozen source.
- The improved scan still produces ten candidates on the same Quant AI Market Lab snapshot.

These examples were selected to exercise the rules. Passing them is not an independent estimate of real-world precision or recall. I have not yet tested a second complete frozen project or implemented the planned agent system.

My earlier review confirmed no look-ahead error among the ten flagged locations inspected. It did not establish absence of leakage across the whole project. The saved original triage is qualified accordingly in the local review record.

## Revision v2: coverage and report preservation

I added RC09 for no eligible Python source files and RC10 for unreadable source. I skip explicit dependency/cache folders and symlinks; the report lists these exclusions. Source encoding declarations are supported. Parse or decoding failures produce partial coverage rather than stopping review of other files. Every readable source has a SHA-256 fingerprint.

I refuse report overwrite unless `--force` is explicit. JSON and Markdown expose scan status, checked-file counts and checks not performed. The two reports are not written as a single atomic transaction; a filesystem write failure could leave only one report. I have not added notebook parsing or cross-file dataflow.

Seven new coverage/report test methods bring the current suite to 43 methods. The earlier 36-test result above describes revision v1. The new tests exercise empty scans, encoding, bad bytes, parse failures, dependency exclusions, symlinks and CLI overwrite protection.

## Revision v3: new candidate patterns and remaining blind spots

I added literal negative `diff` and `pct_change` periods and explicit centered rolling windows to RC01. A centered window may use future observations when used as a feature, but I do not establish receiver semantics, window size or downstream use. I continue to require human review.

The report explicitly lists variable-valued periods/shuffle/center settings, aliased split/model imports, RandomState tracking, and lambda execution/scope handling as not checked. I do not claim general alias resolution merely because simple NumPy aliases are recognized. A seed in the `__main__` guard can produce a conservative warning, even in a script that seeds correctly when executed.

The current suite has 52 methods. Two cost-function characterization tests reproduce the known gaps; they are not correctness passes for those inputs. Seven new future-pattern methods include the recognized patterns, clean controls, documented misses and the main-guard false positive. These examples do not establish real-world recall. Earlier count statements describe the prior revisions.
