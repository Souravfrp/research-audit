# First local LangChain ↔ Ollama connection (JavaScript)

**Stage:** Learning exercise only. It is **not** a working ResearchAudit RAG pipeline or a completed audit. This does not access any frozen project files, the OpenAI API, or the existing rule checker. The user runs it on their own Mac; GitHub cannot verify the user's Ollama service.

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

**Not yet completed:** Actual local execution of this example, a RAG retriever, OpenAI API comparison, agents and independent mathematical verification. Those are later steps.

Official references: [ChatOllama integration](https://docs.langchain.com/oss/javascript/integrations/chat/ollama) · [Ollama](https://docs.ollama.com/).
