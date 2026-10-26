import { readFile } from "node:fs/promises";
import { coversRange } from "./citation-utils.mjs";

const inputPath = process.argv[2];
if (!inputPath) {
  console.error("Usage: node citation-check.mjs <saved-output-file>");
  process.exit(2);
}
const output = await readFile(inputPath, "utf8");

const [header, answer = ""] =
  output.split("Qwen3 answer (verify every citation manually):");

const available = new Set(
  [...header.matchAll(/\[(E\d+)\]\s+\S+:\d+-\d+/g)]
    .map(match => match[1])
);

const cited = [...new Set(
  [...answer.matchAll(/\[(E\d+)\]/g)]
    .map(match => match[1])
)];

console.log("Available evidence:", [...available].join(", "));
console.log("Evidence cited by Qwen3:", cited.join(", "));
console.log("Unknown citations:",
  cited.filter(id => !available.has(id)).join(", ") || "none");
if (cited.some(id => !available.has(id))) process.exitCode = 1;

const passages = new Map(
  [...header.matchAll(/\[(E\d+)\]\s+(\S+):(\d+)-(\d+)/g)]
    .map(match => [
      match[1],
      {
        path: match[2],
        start: Number(match[3]),
        end: Number(match[4])
      }
    ])
);

console.log("\nSources actually cited by Qwen3:");
for (const id of cited) {
  const passage = passages.get(id);
  if (passage) {
    console.log(`${id}: ${passage.path}:${passage.start}-${passage.end}`);
  }
}

function coversLine(id, line) {
  return coversRange(passages.get(id), "tests/test_claim_07_transaction_costs.py", line, line);
}

console.log("\nDoes the evidence include the assertion at line 82?");
for (const id of ["E3", "E5"]) {
  console.log(`${id}: ${coversLine(id, 82) ? "YES" : "NO"}`);
}

const matrixSection = answer.split("**Gap 2:")[1] ?? "";

const matrixCitation = matrixSection.match(
  /\*\*Source\*\*:\s+\[(E\d+)\]\s+(\S+):(\d+)[–-](\d+)/
);

console.log("\nMatrix-weight citation verification:");

if (!matrixCitation) {
  console.log("Citation not found in the answer.");
  process.exitCode = 1;
} else {
  const [, id, path, start, end] = matrixCitation;
  const passage = passages.get(id);

  const validSource = coversRange(passage, path, Number(start), Number(end));

  const coversTest = path === "tests/test_claim_07_transaction_costs.py" &&
    Number(start) <= 84 &&
    Number(end) >= 89;

  console.log(`Qwen3 cited: ${id}, lines ${start}-${end}`);
  console.log(`Range belongs to retrieved evidence: ${validSource ? "YES" : "NO"}`);
  console.log(`Contains complete matrix test: ${coversTest ? "YES" : "NO"}`);
  if (!validSource || !coversTest) process.exitCode = 1;
}
