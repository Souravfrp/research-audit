# First local LangChain ↔ Ollama connection (JavaScript)

**Stage:** A user-reported **successful local LLM-only run** is recorded in [the October 24 trial note](../../docs/local_llm_trial_2026-10-24.md). The new `rag.mjs` is a separate **unrun beginner RAG demonstration**, not a fully validated audit. `index.mjs` remains LLM-only; the RAG exercise retrieves selected allowlisted frozen source files, but never changes them. Neither script uses the OpenAI API or runs the rule checker. GitHub cannot independently execute the Ollama service on the user's Mac.

## What is already available on the learner's Mac

- Ollama **0.40.10** with the local model `qwen3:4b-instruct` successfully downloaded and queried
- Node.js **v24.22.1** and npm **11.19.1**
- Apple M4 MacBook Air with 16 GB RAM

## How to run it (no JavaScript to type)

First, open Terminal. If `~/Documents/research-audit` does **not** exist, use:

```bash
cd ~/Documents
git clone https://github.com/Souravfrp/research-audit.git
```

If you **already** have that folder, update your existing checkout instead (assuming you have no outstanding changes preventing a fast-forward):

```bash
cd ~/Documents/research-audit
git pull --ff-only
```

Then run the example:

```bash
cd ~/Documents/research-audit/integrations/langchain-ollama-js
npm install
npm run check
npm start
```

The first `npm install` downloads two libraries from the **npm registry**. `npm run check` verifies JavaScript syntax only. `npm start` calls your own locally running Ollama service. It does **not** send the prompt to an OpenAI API or other cloud provider.

`npm install` generates a local `package-lock.json`; preserve it for a later reproducible release. Install inside this specific folder, **not** in your home folder or the Python project root.

## What each piece means

| Term | Plain-language meaning | Why we need it |
|---|---|---|
| Node.js | Runs JavaScript outside the browser | Executes our script |
| npm | Downloads JavaScript dependencies | Installs LangChain's Ollama integration |
| LangChain.js | Framework/adapters for language-model applications | Connects our program to the model runtime |
| `ChatOllama` | The LangChain adapter for Ollama | Sends text to Ollama and receives a reply |
| `127.0.0.1:11434` | Ollama server on this same Mac | Makes the first model call locally |
| System message | Instructions about the reviewer's role | Limits unsupported claims |
| Human message | The actual question we ask | Defines the example task |
| `invoke` | Executes one model request | Generates an answer |
| `temperature: 0` | Requests lower randomness | Can improve repeatability, not correctness |
| LLM-only | Model has no additional evidence | Gives us a baseline before RAG |

The included question asks for **three tests of a portfolio transaction-cost claim**. The model should offer *proposed* tests without pretending it examined code. Those proposals are not verified findings.

## Troubleshooting

If `npm start` cannot reach Ollama, open the Ollama app and check:

```bash
ollama list
```

The downloaded model should include `qwen3:4b-instruct`. You do not need to install Claude Code, OpenCode, or another integration from the launcher.

If `npm run check` passes but `npm start` fails, it might be the Ollama service connection, missing local model, or a library/runtime issue. The syntax check alone cannot verify inference.

## Definition of done

1. Two LangChain JavaScript packages are installed.
2. The file passes a syntax check.
3. The program receives a response from **local Qwen3 via Ollama**, without claiming to have accessed source files.
4. Record the model, date and result; inspect for unsupported statements.

**Completed based on user-shared Terminal output (24 October 2026):** `npm install`, `npm run check`, and `npm start` returned a LangChain → local Ollama → Qwen3 answer. **Still unverified:** Execution of the new RAG demonstration, quality of retrieval/citations, OpenAI comparison, agents and independent mathematical verification.


## Next lesson: first retrieval-augmented answer (RAG)

This is the **smallest real retrieval experiment**, separate from the previous LLM-only script. RAG means **retrieval-augmented generation**: look up evidence first, then give the selected passages to the LLM to answer. You do **not** need a vector database or embedding model just to learn RAG. We start with transparent **keyword retrieval** (matching words), then upgrade to embeddings once it works.

The demonstration reads three **local, allowlisted** ResearchAudit files without modifying them:

- `claims/claim_07_transaction_costs.md`
- `tests/test_claim_07_transaction_costs.py`
- `targets/quant-ai-market-lab-v1.0.0/src/portfolio_backtest.py`

It divides their text into small overlapping **chunks** (16 lines each, starting every 8 lines), scores each chunk against the question, selects up to 10 relatively relevant chunks, prints **source path + exact line range + source file SHA-256**, and passes those excerpts to the same Qwen3 model via LangChain. This is genuine (keyword-based) retrieval + generation, but **not semantic/vector RAG yet**, and it does not guarantee relevant documents are found.

From the already installed example folder on your Mac, run:

```bash
git pull --ff-only
npm run check
npm run rag:check
npm run rag
```

**Important:** `git pull --ff-only` must be run from inside the research-audit Git checkout, which includes this example folder. Git identifies the repository from a nested folder. `npm run rag:check` tests the retriever **without calling an LLM**. `npm run rag` then invokes Qwen3 **locally**.

**Terminology:**

| Term | In this example |
| --- | --- |
| Corpus | The three allowed source files |
| Chunk | An excerpt of consecutive source lines |
| Retriever | Keyword matching that chooses chunks relevant to the question |
| Citation | Source path and line range printed alongside each retrieved excerpt |
| Grounding | Asking Qwen3 to answer using supplied retrieved chunks, not just prior model knowledge |
| SHA-256 | A file fingerprint; it helps identify exactly which source content supplied evidence |
| Embedding | A vector representation for semantic search; **not used yet** |
| Vector database | A database for similarity search; **not used yet** |

**Exercise:** Compare the model's new evidence-backed answer to the earlier three generic test suggestions. Can it identify **both** documented known input-validation issues? Did it cite a genuinely retrieved path/line for each? Did it falsely claim tests passed or the full backtest was reproduced? **Read the cited code and tests yourself**: a printed citation or LLM statement is not a mathematical proof.

The retrieval test checks whether the selected snippets include the documented near-unit target-weight issue and the two-dimensional broadcasting issue. It is a deliberately narrow, fixture-like smoke test; it is **not a precision/recall benchmark** and doesn't demonstrate broad retrieval reliability. We will later compare local no-RAG vs RAG and evaluate retrieval misses with held-out questions.

Official references: [ChatOllama integration](https://docs.langchain.com/oss/javascript/integrations/chat/ollama) · [Ollama](https://docs.ollama.com/).
