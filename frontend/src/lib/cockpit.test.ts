import { test } from "node:test";
import assert from "node:assert/strict";
import { avgProgress, phaseProgress, initiativeTone, isOverdue } from "./cockpit.ts";

test("avgProgress promedia y redondea", () => {
  assert.equal(avgProgress([]), null);
  assert.equal(avgProgress([{ progress_pct: 10 }, { progress_pct: 25 }]), 18);
});
test("phaseProgress es el % Done", () => {
  assert.equal(phaseProgress([]), null);
  assert.equal(phaseProgress([{ status: "Done" }, { status: "Planned" }, { status: "Done" }]), 67);
});
test("initiativeTone", () => {
  assert.equal(initiativeTone("Monitoring"), "accent");
  assert.equal(initiativeTone("Validation"), "muted");
  assert.equal(initiativeTone("On Hold"), "warn");
});
test("isOverdue compara solo fechas locales", () => {
  const today = new Date(2026, 9, 22, 23, 30);
  assert.equal(isOverdue("2026-10-21", today), true);
  assert.equal(isOverdue("2026-10-22", today), false);
  assert.equal(isOverdue(null, today), false);
});
