# ResearchAudit — Ollama, LangChain, OpenAI and RAG: beginner-to-corporate roadmap

**Status — 24 October 2026:** This is a **setup and learning plan, not a completed integration**. The 10 October rule-based checker, its 52 locally verified test methods, and the frozen Quant AI Market Lab v1.0.0 source are unchanged. No Ollama model, OpenAI API integration, LangChain pipeline, or RAG system has been demonstrated in this repository.

## Goal and choice of tools

Build an auditable **business application** in stages, while keeping installation and early experiments understandable for someone new to LLMs. The desired stack is:

| Component | Definition | Why it is part of ResearchAudit |
| --- | --- | --- |
| **Ollama** | A local model runner and Mac chat app | Use an existing language model on the Mac and learn inference, model versions, and resource limits without starting with Python or API billing |
| **OpenAI API** | A hosted model service requiring a separate API account/key for conventional API integration | Learn hosted model integration and later compare model quality, latency and cost to Ollama |
| **LangChain** | An application framework available in Python and JavaScript/TypeScript | Build repeatable workflows that talk to different models, process documents, retrieve evidence, and record outputs |
| **RAG** | Retrieval-augmented generation: find relevant source passages before giving them to an LLM | Ground audits in frozen documentation, code, test output and claim inventories |
| **ResearchAudit checker** | The existing deterministic AST/rule-based program | Preserve a non-LLM baseline for comparison and independently check source claims |

**These are complementary components, not four separate LLMs.** Ollama is a way to run a local model. OpenAI is an optional remote provider. LangChain connects providers and retrieval. RAG is a technique, not another model.

We choose **Ollama first**. AnythingLLM remains an **optional** user interface for a visual document-chat demonstration later, but it is not the main required technology stack and should not replace learning LangChain.

## Stage 0 — Check the Mac (no installation yet)

Choose **Apple menu → About This Mac**. Record the macOS version, **Chip/Processor**, and **Memory**. This controls compatibility and which *local* models will fit. Do not select a model size before checking the hardware. Ollama's macOS download currently requires **macOS 14 Sonoma or later**; on an older macOS version, first consider operating-system compatibility rather than blindly installing.

The model is run locally only when a **local** model is selected; Ollama also offers explicitly hosted cloud models. Do not confuse a cloud model with the privacy or offline properties of local inference.

Official sources: [Ollama macOS download](https://ollama.com/download/mac), [Ollama local desktop chat app](https://ollama.com/blog/new-app), [Ollama quickstart](https://docs.ollama.com/quickstart).

## Stage 1 — Ollama: first local LLM, no Python or Terminal

1. Open https://ollama.com/download/mac and download the official macOS application compatible with the Mac.
2. Open the download, install and launch the Ollama app through Finder/Applications as directed by its installer.
3. In Ollama's graphical chat interface, choose/download a **small local chat/instruction model** that fits available memory. Model names, sizes and available choices may change. Record the *exact model and version*, RAM and whether it was local or hosted. Do not start with a huge model simply because it is popular.
4. Ask exactly this question: **"What checks should a financial risk model pass before an internal company approves it?"** Save the output and note missing assumptions and citations.
5. Then ask a second question: **"If a model audit lacks source evidence, should I say the claim is correct?"** Check whether the model admits uncertainty.

**Pass condition:** A genuinely local model responds within the Ollama app. Save what the model said; do not claim an audit or retrieval system is working. **No source documents or RAG are involved yet.**

*Definitions:* LLM = pretrained language model; model weights = numerical parameters loaded to run it; inference = producing answers with an existing model, not training one; prompt = your question/instruction; token = a unit of text processed by the model.

## Stage 2 — OpenAI: learn the hosted alternative

Open https://platform.openai.com/ and read https://developers.openai.com/api/docs/quickstart.

Understand the distinction:

- **ChatGPT** is the conversational product. **The ordinary OpenAI API** is a separate developer service with separate billing; a ChatGPT Plus subscription does not automatically pay for it.
- An **API** (application programming interface) lets your software send an authorized request to a model service and receive a response.
- An **API key** is a secret credential for API requests. Never paste it into chat, a GitHub repository, screenshots, public webpages, or client-side code.
- An API call may be billed based on usage. Before making a paid request, check billing controls and price, and use **public or synthetic** ResearchAudit examples only. Company-confidential material requires employer approval and the appropriate account/data controls.

**Pass condition:** The learner understands API access, credentials, provider differences and cost. This stage does not require payment or making a call until the user chooses to try it.

Official source for separate billing: https://help.openai.com/en/articles/9039756-managing-billing-for-chatgpt-and-the-api-platform

## Stage 3 — LangChain: connect local and hosted providers

We will add LangChain **after** a single Ollama model works and the basic OpenAI API concepts are clear.

An actual LangChain application normally requires **some code**, typically Python or JavaScript. This is a professional engineering skill, not something that a visual Ollama chat window does automatically. We can keep the first application extremely small and use **VS Code with a graphical editor**, learning only the few lines needed. The learner will do their own setup; no unrequested code changes or automation should be represented as already running.

- **LangChain ↔ Ollama:** \`ChatOllama\` in the \`langchain-ollama\` integration.
- **LangChain ↔ OpenAI API:** \`ChatOpenAI\` in the \`langchain-openai\` integration.
- Use **the same task and grading rules** for both providers, then record model name, prompt version, response, evidence use, failures, latency and cost where relevant.

Official documentation:
- https://docs.langchain.com/oss/python/integrations/chat/ollama
- https://docs.langchain.com/oss/python/integrations/chat/openai

**Pass condition:** A version-controlled minimal project can ask the same question of the local and (when authorized) hosted provider, then save distinct outputs. We do not need four agents yet.

## Stage 4 — RAG: connect ResearchAudit to its evidence

RAG is not fine-tuning or retraining. Build an index using **public frozen** research documents such as:

- \`claims/claim_07_transaction_costs.md\`
- \`claims/claim_inventory.md\`
- \`docs/baseline_evaluation.md\`
- selected functions from \`targets/quant-ai-market-lab-v1.0.0/src/portfolio_backtest.py\`

*Definitions:*
- **Ingestion:** read allowed source files into the index.
- **Chunking:** split files into meaningful text/code passages; preserve paths, line numbers and source hashes.
- **Embedding:** turn a passage into a numerical vector so similar passages can be searched.
- **Vector database:** store/search those vectors.
- **Retriever:** return candidate passages for a question.
- **Grounding:** require the answer to rely on actual supplied passages.
- **Evaluation:** compare output against independently checked expected answers and verify cited lines.

A first RAG task: **"Which two target-weight validation gaps exist in Claim 7? Show the source lines and say what the tests demonstrate."** A successful run must find the near-unit weight issue and the 2-D broadcasting issue, with verifiable source paths. Compare with an **LLM-only** version of the same question.

**Pass condition:** Relevant evidence is retrieved with verifiable file/line references. Fluency is not proof; do not classify source-code issues as fixed just because an LLM explains them.

## Stage 5 — Business application and later agents

Only after evaluating single-model RAG should we implement the four planned agents (mathematics, code, methodology, skeptic) and a coordinator. For corporate use, add controlled document access, protected secrets, approved data residency/handling, audit trails, repeatable evaluations, monitoring, version pinning and human review. A local Mac pilot is not a multi-user production system.

## What we are **not** doing today

- Not downloading or configuring any model on the user's computer on their behalf.
- Not training a new language model.
- Not claiming RAG, LangChain or OpenAI API integration exists in ResearchAudit.
- Not changing the rule checker, test results, or frozen audit source.
- Not requiring a Terminal command, Python, an API key, or paid API credits for the **first Ollama GUI milestone**.

## Evidence to record after the first run

Keep a dated local note of: macOS version, Mac chip, RAM, Ollama app version, downloaded **local** model tag, the two exact prompts, summarized responses, failure examples and whether any remote/cloud option was used. Only publish a sanitized note after reviewing it for secrets and private data.
