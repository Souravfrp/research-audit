# My references and evidence

I use established mechanisms, not a new general correctness-verification algorithm.

- [Python 3.12 AST](https://docs.python.org/3.12/library/ast.html): tree nodes, parsing and compilation. I compile for syntax validation without executing scanned projects. Consulted October 10, 2026.
- [Python 3.12 symbol tables](https://docs.python.org/3.12/library/symtable.html): scopes and free-variable references used by my limited parameter check. A static reference does not prove runtime influence. Consulted October 10, 2026.
- [NumPy 2.3 isclose](https://numpy.org/doc/2.3/reference/generated/numpy.isclose.html): relative and absolute tolerance conventions behind the near-unit weight gap. Setting only `atol` retains the default relative tolerance. Consulted October 10, 2026.
- [Snapshot provenance](../snapshot_provenance.json): frozen source from `Souravfrp/research-audit` commit `5f353c9d72ea69aaa1c39e76c77be5ed0044220d`.
- [Claim inventory](../claims/claim_inventory.md), [C07 note](../claims/claim_07_transaction_costs.md), [current report](../results/published_baseline/rule_checker_quant-ai-market-lab-v1.0.0.json), [tests](../tests/) and [evaluation](baseline_evaluation.md): my supporting evidence and its limits.

These sources explain implementation choices; they do not establish financial performance or checker detection accuracy.
