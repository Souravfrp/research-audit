# ResearchAudit — local LLM and RAG: no-code corporate pilot

**Status (24 October 2026):** Setup instructions only. **No model has been installed, executed, or evaluated by the repository.** The existing rule-based baseline and the frozen Quant AI Market Lab v1.0.0 target remain unchanged.

## Goal

Learn the practical workflow for building a business-grade, evidence-based LLM assistant without initially writing Python. The immediate milestone is **one local LLM responding in a graphical application**. The next milestone will add **document retrieval (RAG)**. Neither a local desktop pilot nor a convincing answer is production approval or evidence of mathematical correctness.

The initial pilot is kept separate from the four-agent ResearchAudit proposal. A future enterprise application needs organization-approved hosting, identity/access controls, retention/security policies, evaluation, monitoring, and automated integration.

## 1. Choose the simplest tool

**AnythingLLM Desktop:** https://anythingllm.com/download

It supports a built-in local language model, a chat interface, document ingestion and retrieval, workspaces, and optional agents. It is a convenient way to learn **LLM → RAG → evaluation** within one app, rather than starting with Python, LangChain, a separate vector database or several local servers.

Official sources:
- macOS installation: https://docs.anythingllm.com/installation-desktop/macos
- Built-in local model: https://docs.anythingllm.com/setup/llm-configuration/local/built-in
- Document attachment versus RAG: https://docs.anythingllm.com/chatting-with-documents/introduction
- Query mode versus chat mode: https://docs.anythingllm.com/features/chat-modes
- Desktop versus Docker deployment: https://docs.anythingllm.com/installation-docker/overview

## 2. Manual setup — no Terminal or Python

1. On the Mac, choose **Apple menu → About This Mac**. Note **Chip/Processor** and **Memory** (RAM). AnythingLLM recommends 16 GB RAM; a smaller model can be explored on more constrained machines, with limitations. M-series Macs generally perform better for local inference than Intel Macs.
2. At the official download page, choose **Apple Silicon** if the chip is M1/M2/M3/etc., or **Apple Intel** for an Intel machine. Download the macOS `.dmg`, open it, and drag the AnythingLLM app to Applications.
3. Open AnythingLLM. Choose its **built-in/local** LLM provider on first-run setup; select a **small instruct/chat model** compatible with available memory. Prefer a smaller 3B–4B class model if available on a lower-memory Mac; the actual model names and sizes shown depend on the app version and available models. Record the *exact model name and version* rather than inventing it.
4. Create a workspace named **ResearchAudit – Local AI Pilot**. Ask one straightforward business-style question: **"What checks should a financial risk model pass before internal approval?"** This is a language-model-only check; no internal source document has been supplied.
5. Keep the first response and record the model name, date, hardware details, question, answer summary and obvious omissions. Do not mark a single plausible response as independently verified.

**First milestone acceptance:** The installed local model answers within the desktop application without Python, API keys or a remote model endpoint. The project repository cannot verify this until the user actually runs it and records evidence.

## 3. Add RAG only after the local LLM works

Use your own **public, frozen** ResearchAudit documents as the first safe data source:
- `claims/claim_07_transaction_costs.md`
- `claims/claim_inventory.md`
- `docs/baseline_evaluation.md`

In AnythingLLM, open the ResearchAudit workspace, add these documents to the workspace, and choose the option to **embed** or make them searchable across workspace chats (rather than only attaching full text to one chat). The exact location of controls can differ by app version; consult the official document guide above. Start with the default local embedding model and vector database rather than configuring extra services.

Use **Query Mode**, if available, for a question that should be answered from uploaded documents rather than general language-model knowledge. Example: **"Which two input-validation gaps were found in Claim 7? Cite the supplied source."**

**Second milestone acceptance:** Both issues from the published audit note are recovered and accurately attributed; if the document is absent or unsupported, the assistant should say so. Manually verify citations and exact statements against source. Retrieval is not a proof that the answer is correct.

## Terms — what and why

| Term | Meaning | Why we need it |
| --- | --- | --- |
| LLM | Large language model: a pretrained model that predicts/generates text in response to instructions | Answer questions and analyze retrieved material |
| Model weights | Saved numerical parameters from training | Make local inference possible without training a model |
| Inference | Running an existing model to produce a response | We are **using**, not training, a model |
| Prompt | Question/instructions given to the model | Define the task, scope and response format |
| Workspace | Logical separation of project documents and chats | Keep pilot material organized and reduce accidental mixing |
| RAG | Retrieval-augmented generation: find relevant source passages, then give them to a model | Answers can be grounded in specific project evidence |
| Chunk | Short section of a larger file | Enables retrieval without supplying the entire repository every time |
| Embedding | Numeric vector representing text for search | Find semantically related source passages |
| Vector database | Storage/search system for document embeddings | Retrieve candidate evidence efficiently |
| Source citation | File/path or passage supporting a claim | Allows human verification instead of accepting fluent prose |
| Evaluation | Testing on known-answer cases and recording failures | Determine whether the system works reliably |
| POC | Proof of concept: small demonstration of feasibility | A learning milestone, **not** a production deployment |

## What makes this corporate-oriented?

**Pilot:** Use sample/public documents, write down the business question, record model version and evaluation cases, and collect failure examples.

**Internal product:** Integrate permitted internal repositories/document stores through approved interfaces; require reliable citations, access control, human review of decisions, and reproducible tests.

**Enterprise deployment:** AnythingLLM Desktop is single-user and should not be mistaken for an access-controlled shared corporate service. The product's server/Docker edition supports multi-user and workspace management, but must still be evaluated by the organization's security/privacy and compliance teams. Do not upload a future employer's proprietary documents to a personal computer or third-party model without explicit permission.

## Why no Python, Ollama, or agents yet?

A graphical pilot distinguishes **model capability** from **retrieval** and makes the workflow observable. Once both milestones work, a corporate development version can use an approved API/server, scripted evaluations, version-controlled prompts, document-ingestion rules, identity/role controls, tests and monitoring. The planned four-agent ResearchAudit implementation belongs to that later stage.

Nothing about this guide changes the claims, test records or frozen target in the October 10 baseline.
