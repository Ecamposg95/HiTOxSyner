import { test } from "node:test";
import assert from "node:assert/strict";
import { buildTimeline, parseLocalDate, positionPct } from "./timeline.ts";
import type { Milestone } from "../types";

function ms(p: Partial<Milestone>): Milestone {
  return {
    id: "1", engagement_id: "e", name: "M", description: "", phase: "Discover", due_date: null,
    status: "Planned", owner: "", initiative_id: null, deliverable: "", created_at: "", updated_at: "", ...p,
  };
}

test("buildTimeline devuelve null sin hitos con fecha", () => {
  assert.equal(buildTimeline([]), null);
  assert.equal(buildTimeline([ms({ due_date: null })]), null);
});
test("una sola fecha produce un rango no vacío", () => {
  const one = buildTimeline([ms({ due_date: "2026-11-15" })])!;
  assert.equal(one.start.getMonth(), 10);
  assert.equal(one.months.length, 2);
  const p = positionPct(one, parseLocalDate("2026-11-15"));
  assert.ok(p > 0 && p < 100);
});
test("varios hitos: separa sin fecha y añade margen de un mes", () => {
  const m = buildTimeline([ms({ due_date: "2026-10-01" }), ms({ due_date: "2026-12-20" }), ms({ due_date: null })])!;
  assert.equal(m.undated.length, 1);
  assert.equal(m.dated.length, 2);
  assert.equal(m.months.length, 4);
  assert.equal(m.months[0].leftPct, 0);
  assert.equal(positionPct(m, parseLocalDate("2026-10-01")), 0);
  assert.equal(parseLocalDate("2026-10-01").getDate(), 1);
  assert.equal(positionPct(m, new Date(2030, 0, 1)), 100);
  assert.equal(positionPct(m, new Date(2020, 0, 1)), 0);
});
