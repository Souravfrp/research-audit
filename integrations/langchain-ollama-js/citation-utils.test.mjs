import test from "node:test";
import assert from "node:assert/strict";
import { coversRange } from "./citation-utils.mjs";

const passage = {
  path: "tests/example.py",
  start: 73,
  end: 96
};

test("accepts complete evidence coverage", () => {
  assert.equal(coversRange(passage, "tests/example.py", 84, 89), true);
});

test("rejects incomplete evidence coverage", () => {
  assert.equal(coversRange(passage, "tests/example.py", 90, 99), false);
});

test("rejects evidence from another file", () => {
  assert.equal(coversRange(passage, "tests/other.py", 84, 89), false);
});

test("rejects reversed line ranges", () => {
  assert.equal(
    coversRange(passage, "tests/example.py", 90, 84),
    false
  );
});
