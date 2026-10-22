import { test } from "node:test";
import assert from "node:assert/strict";
import { ctaSlices } from "./charts.ts";

test("ctaSlices vacío si total es 0", () => {
  assert.deepEqual(ctaSlices({ committed: 0, in_progress: 0, evidenced: 0, dropped: 0, total: 0 }), []);
});
test("ctaSlices omite ceros y respeta el orden", () => {
  const s = ctaSlices({ committed: 2, in_progress: 0, evidenced: 3, dropped: 1, total: 6 });
  assert.deepEqual(s.map((x) => x.key), ["evidenced", "committed", "dropped"]);
  assert.deepEqual(s.map((x) => x.value), [3, 2, 1]);
});
