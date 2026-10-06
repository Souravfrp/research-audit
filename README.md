# ResearchAudit

**Multi-Agent Validation for Quantitative and Risk Analytics**

## Status

 ResearchAudit is my project for checking the maths, algorithms, code, and claims of the Quant AI Market Lab, to see whether they are correct and justified. I have frozen the Quant AI Market Lab at v1.0.0 and published a clean snapshot of it in this repository, so every finding refers to a fixed version.

I am building the audit in two stages. First, I will build a rule-based checker as a baseline and measure how well the checker performs against known issues, without claiming a formal labelled set exists as a concept yet. Then I plan to build a multi-agent system with four AI agents: a math checker, a code and implementation checker, a methodology and/or domain-soundness checker, and a skeptic. The skeptic challenges the verdicts of the other three and asks them to support their answers with evidence, so that no verdict is accepted without scrutiny. A coordinator, written as plain Python, will send questions to the agents, repeat them to test whether the answers are consistent, and produce a final report.

I am planning to run everything locally with Ollama, without a third-party AI API, so the whole system can be run and inspected on my own machine. A local model may reason less well than a cloud model on complex judgments, so the report will mark claims that remain disputed or unresolved instead of hiding them.

## Why I Want to Build This

My academic background is in mathematics, computer science and system sciences. As I move from academic research towards quantitative research, data science and risk analytics roles, I want to study whether multi-agent systems can evaluate technical work in a rigorous and reproducible way.

ResearchAudit will be developed as an independent project using frozen versions of two projects that I am already working on:

* **Quant AI Market Lab**, focused on quantitative market analysis
* **PaymentGuard**, focused on transaction-risk analysis and constrained decision-making

The purpose is not to combine these projects or repeat their analyses. Instead, ResearchAudit will treat completed components from them as audit targets and test whether different reviewing approaches can detect mathematical, statistical, data-validation and reproducibility problems.

Only components that have actually been completed in the source projects will be included. Planned or unfinished work will remain outside the audit until it has been implemented and documented.
