import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";

test("correct matrix citation produces exit code zero", () => {
  const result = spawnSync(
    process.execPath,
    ["citation-check.mjs", "test-fixtures/correct-matrix.txt"],
    { encoding: "utf8" }
  );

  assert.equal(result.status, 0);
});

test("incorrect matrix citation produces exit code one", () => {
  const result = spawnSync(
    process.execPath,
    ["citation-check.mjs", "test-fixtures/incorrect-matrix.txt"],
    { encoding: "utf8" }
  );

  assert.equal(result.status, 1);
  assert.ok(result.stdout.includes("Contains complete matrix test: NO"));
});

test("missing matrix source citation produces exit code one", () => {
  const result = spawnSync(
    process.execPath,
    ["citation-check.mjs", "test-fixtures/missing-source.txt"],
    { encoding: "utf8" }
  );

  assert.equal(result.status, 1);
  assert.ok(result.stdout.includes("Citation not found in the answer."));
});

test("missing filename produces exit code two", () => {
  const result = spawnSync(
    process.execPath,
    ["citation-check.mjs"],
    { encoding: "utf8" }
  );

  assert.equal(result.status, 2);
  assert.ok(result.stderr.includes("Usage:"));
});

test("unknown evidence label produces exit code one", () => {
  const result = spawnSync(
    process.execPath,
    ["citation-check.mjs", "test-fixtures/unknown-label.txt"],
    { encoding: "utf8" }
  );

  assert.ok(result.stdout.includes("Unknown citations: E99"));
  assert.equal(result.status, 1);
});
