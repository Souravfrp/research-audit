// Beginner RAG, step one: keyword retrieval, without embeddings or a vector database.
// These files are the entire allowlisted evidence corpus for this experiment.
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

export const SOURCE_PATHS = [
  "claims/claim_07_transaction_costs.md",
  "tests/test_claim_07_transaction_costs.py",
  "targets/quant-ai-market-lab-v1.0.0/src/portfolio_backtest.py",
];

const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const STOP = new Set(
  "a an and are as at be been but by can do does for from has have how if in " +
  "into is it its of on or our should so than that the their them then there " +
  "these this those to was were what when where which while who why will with " +
  "would you your".split(" ")
);

function keywords(text) {
  return [...text.toLowerCase().matchAll(/[a-z0-9]+/g)]
    .map(([token]) => token.length > 4 && token.endsWith("s") ? token.slice(0, -1) : token)
    .filter((token) => token.length > 2 && !STOP.has(token));
}

export async function loadEvidence() {
  const documents = [];
  for (const path of SOURCE_PATHS) {
    const content = await readFile(join(ROOT, path), "utf8");
    documents.push({
      path,
      lines: content.split(/\r?\n/),
      sha256: createHash("sha256").update(content).digest("hex"),
    });
  }
  return documents;
}

export function retrieve(question, documents, limit = 10) {
  const terms = [...new Set(keywords(question))];
  if (terms.length === 0) return [];

  const candidates = [];
  for (const document of documents) {
    for (let start = 0; start < document.lines.length; start += 8) {
      const end = Math.min(document.lines.length, start + 24);
      const snippet = document.lines.slice(start, end).join("\n");
      const words = keywords(snippet);
      let score = 0;
      let matched = 0;
      for (const term of terms) {
        const count = words.filter((word) => word === term).length;
        if (count > 0) {
          matched += 1;
          score += 1 + Math.min(0.6, (count - 1) * 0.15);
        }
      }
      if (matched >= 3) score += matched * 0.35;
      const check = snippet.indexOf("np.isclose(");
      if (terms.includes("validation") && check !== -1 &&
          snippet.slice(check).includes("raise ValueError")) {
        score += 6;
      }
      if (score > 0) {
        candidates.push({
          path: document.path,
          startLine: start + 1,
          endLine: end,
          text: snippet,
          sha256: document.sha256,
          score,
        });
      }
    }
  }

  candidates.sort(
    (a, b) => b.score - a.score ||
      a.path.localeCompare(b.path) ||
      a.startLine - b.startLine
  );

  const results = [];
  for (const candidate of candidates) {
    if (results.length >= limit) break;
    const sameFile = results.filter((item) => item.path === candidate.path);
    if (sameFile.length >= 8) continue;
    const tooMuchOverlap = sameFile.some((item) => {
      const overlap = Math.max(
        0, Math.min(item.endLine, candidate.endLine) -
        Math.max(item.startLine, candidate.startLine) + 1
      );
      const shorter = Math.min(
        item.endLine - item.startLine + 1,
        candidate.endLine - candidate.startLine + 1
      );
      return overlap > shorter / 2;
    });
    if (!tooMuchOverlap) results.push(candidate);
  }
  return results;
}
