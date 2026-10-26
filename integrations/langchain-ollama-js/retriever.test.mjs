import test from "node:test";
import assert from "node:assert/strict";
import { SOURCE_PATHS, loadEvidence, retrieve } from "./retriever.mjs";

test("the local allowlisted source files can be read", async () => {
  const docs = await loadEvidence();
  assert.equal(docs.length, SOURCE_PATHS.length);
  assert.ok(docs.every((d) => d.lines.length > 0 && d.sha256.length === 64));
});

test("keyword retrieval surfaces the recorded Claim 7 validation gaps", async () => {
  const question =
    "Which two input-validation gaps exist in the audited transaction-cost " +
    "rebalance implementation? Explain their consequences and cite sources.";
  const results = retrieve(question, await loadEvidence());
  assert.ok(results.length > 0);
  const matching = results.filter((r) =>
    r.path === "claims/claim_07_transaction_costs.md"
  );
  assert.ok(matching.some((r) =>
    r.text.includes("slightly above-unit") &&
    r.text.includes("two-dimensional weights")
  ), "Known validation gaps should appear in retrieved passages");
  assert.ok(results.every((r) => r.startLine >= 1 && r.endLine >= r.startLine));
});

test("empty query retrieves no passages", async () => {
  assert.deepEqual(retrieve("?", await loadEvidence()), []);
});

test("retrieves original portfolio validation code", async () => {
  const question =
    "Which two input-validation gaps exist in the audited transaction-cost " +
    "rebalance implementation? Explain their consequences and cite sources.";

  const results = retrieve(question, await loadEvidence());

  const found = results.some((r) =>
    r.path.endsWith("/portfolio_backtest.py") &&
    r.startLine <= 263 &&
    r.endLine >= 275
  );

  assert.ok(found, "Original validation code was not retrieved");
});
