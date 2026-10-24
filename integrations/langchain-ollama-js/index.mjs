// A minimal local LangChain → Ollama → Qwen3 example.
// No API keys, external services or ResearchAudit documents are used.
import { ChatOllama } from "@langchain/ollama";

const model = new ChatOllama({
  model: "qwen3:4b-instruct",
  baseUrl: "http://127.0.0.1:11434",
  temperature: 0,
});

const messages = [
  [
    "system",
    "You are a cautious quantitative risk model reviewer. " +
      "Use plain language. Do not claim to have accessed code or documents " +
      "that have not been provided. State uncertainty when appropriate.",
  ],
  [
    "human",
    "A portfolio model claims that it correctly subtracts transaction costs " +
      "when rebalancing. Name three concrete tests you would perform before " +
      "approving this claim, and explain why each matters. " +
      "Do not say you have checked the actual code.",
  ],
];

console.log("Model: qwen3:4b-instruct (local Ollama)");
console.log("Mode: LLM only — no RAG or source-file access\n");

try {
  const reply = await model.invoke(messages);
  console.log("Model response:\n");
  console.log(typeof reply.content === "string" ? reply.content : JSON.stringify(reply.content, null, 2));
} catch (error) {
  console.error("Could not ask the local model.");
  console.error("Check that Ollama is running and qwen3:4b-instruct is downloaded.");
  console.error("Details:", error?.message ?? String(error));
  process.exitCode = 1;
}
