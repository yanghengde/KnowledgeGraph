import assert from "node:assert/strict";
import { test } from "node:test";
import { modelRevisionState } from "../src/features/modeling/modelRevisionState.ts";

const draft = { draftId: "d", snapshotId: "s", revision: 4 };
test("published membership does not imply the current draft is incorporated", () => {
  assert.equal(modelRevisionState(draft, { ...draft, revision: 3 }), "草稿有新修改");
  assert.equal(modelRevisionState(draft, draft), "与草稿一致");
});
test("missing provenance and different sources are never labeled current", () => {
  assert.equal(modelRevisionState(draft), "版本待核实");
  assert.equal(modelRevisionState(draft, { ...draft, snapshotId: "other" }), "来源版本不同");
  assert.equal(modelRevisionState(draft, { ...draft, draftId: "other" }), "来源版本不同");
  assert.equal(modelRevisionState(draft, { ...draft, revision: 5 }), "版本待核实");
});
