import assert from "node:assert/strict";
import { test } from "node:test";
import { resolveModelSelection } from "../src/app/modelSelection.ts";

const a = { profile_key: "a", enabled: true };
const b = { profile_key: "b", enabled: true };
test("multiple models require explicit selection regardless of server order", () => {
  assert.equal(resolveModelSelection([a, b], ""), "");
  assert.equal(resolveModelSelection([b, a], "a"), "a");
});
test("removed or disabled selected model never redirects writes", () => {
  assert.equal(resolveModelSelection([b], "a"), "");
  assert.equal(resolveModelSelection([{ ...a, enabled: false }, b], "a"), "");
});
test("only a fresh session can automatically select the sole enabled model", () => {
  assert.equal(resolveModelSelection([a, { ...b, enabled: false }], ""), "a");
  assert.equal(resolveModelSelection([], ""), "");
  assert.equal(resolveModelSelection([{ ...a, enabled: false }], ""), "");
});
