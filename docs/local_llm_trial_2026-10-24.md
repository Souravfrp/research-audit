# ResearchAudit local LLM trial — 24 October 2026

**Evidence:** The project owner shared Terminal output from their Mac on 24 October 2026. This is a **user-reported local execution record**, not a CI run or an independent execution on GitHub. The existing frozen audit source, historical rule-checker evaluations and the isolated cost-function tests are separate from this experiment.

## Environment reported

- MacBook Air (2025), Apple M4, 16 GB RAM.
- Ollama 0.40.10 (installed locally using Ollama's official installer).
- Local model downloaded: `qwen3:4b-instruct`, about 2.5 GB.
- Node.js v24.22.1; npm 11.19.1.
- Source: `integrations/langchain-ollama-js/index.mjs`, run from a clean Git clone.

## Commands and outcome

The user ran:

```bash
cd ~/Documents/research-audit/integrations/langchain-ollama-js
npm install
npm run check
npm start
```

Observed in the supplied output:

- `npm install` added 15 packages and reported 0 known vulnerabilities in that installation audit.
- `npm run check` invoked `node --check index.mjs` and exited successfully.
- `npm start` invoked `node index.mjs`.
- Console printed `Model: qwen3:4b-instruct (local Ollama)` and `Mode: LLM only — no RAG or source-file access`.
- The LangChain `ChatOllama` call returned a coherent model answer with three proposed transaction-cost checks, and Terminal returned to the shell prompt.

## What the model proposed

1. A small, hand-worked example (e.g. rebalancing two holdings).
2. Simultaneous multiple purchases/sales, to see whether trade costs are aggregated.
3. Sensitivity to different transaction-cost rates.

The model did **not** claim to have inspected actual files, consistent with the prompt. These are reasonable **testing suggestions** but not evidence that the frozen target meets its claims. The answer did **not** independently rediscover the known near-unit weight sum or two-dimensional broadcasting validation issues described in `claims/claim_07_transaction_costs.md`. That is a helpful motivation for retrieval-grounded testing, not a measurement of detection sensitivity.

## Interpretation and limitations

**Demonstrated from user-shared output:** A JavaScript program using LangChain successfully reached the local Ollama-served Qwen3 model and received a response.

**Not demonstrated at this milestone:** Source code retrieval, RAG, model-validated citations, a run of the existing rule checker, end-to-end backtest reproduction, an OpenAI API comparison, multi-agent behavior, quality/accuracy benchmarking, or corporate production readiness.

**Next exercise:** A separate keyword-based RAG example in `integrations/langchain-ollama-js/rag.mjs` retrieves selected passages from the frozen repository files with line references and then passes them to the same model. This is explicitly a **beginner retrieval demonstration**, not vector/embedding search and not independently verified until the owner runs it.
