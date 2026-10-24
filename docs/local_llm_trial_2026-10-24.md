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

## Follow-up: first local keyword-RAG run (user-shared partial output, 24 October 2026)

**Run was initiated on the Mac; retrieval was successful, but the final model answer is not yet in the supplied transcript.** The user ran from `integrations/langchain-ollama-js/`:

```bash
git pull --ff-only
npm run check
npm run rag:check
npm run rag
```

Reported results:

- Git fast-forwarded `main` from `484b457` to `ac15587` and loaded the RAG demonstration files.
- `npm run check` passed the Node syntax checks.
- `npm run rag:check`: **3 passed, 0 failed**, including the targeted fixture test that the Claim 7 validation-gap text can be retrieved. This is not a production retrieval-quality or recall study.
- `npm run rag` printed `LOCAL KEYWORD-RAG DEMONSTRATION` and listed ten source passages `[E1]`–`[E10]` with file paths, line numbers and SHA-256 prefixes.
- The supplied output stopped immediately after `Qwen3 answer (verify every citation manually):`. The program prints this header **before** executing `await model.invoke(messages)`. Therefore the transcript **does not yet show a completed Qwen3 response**, return to the shell, model-quality validation or end-to-end completed RAG answer. A later report may append verified information when available.

Selected retrieved evidence included:

- `[E3]` `claims/claim_07_transaction_costs.md:33-43`, encompassing the previously documented **near-unit total weights accepted by the default `np.isclose` tolerance** and **two-dimensional weights being accepted/broadcast**.
- `[E5]` `tests/test_claim_07_transaction_costs.py:81-96`, covering the latter part of the over-allocation test and the 2-D broadcast test.
- `[E9]` `targets/quant-ai-market-lab-v1.0.0/src/portfolio_backtest.py:369-384`, **not** the most relevant target-weight validation statement at `portfolio_backtest.py:263-275`. This is a *documented keyword-retrieval limitation*: it located the summary and tests but selected a less relevant source-code snippet. Improving retrieval to cover specific original code ranges and measuring evidence coverage will be separate work, not a success implied by the passing tests.

**No claims of full mathematical source validation, semantic-vector RAG, embedding retrieval, corporate deployment, or independent model judgment follow from this partial run.**
