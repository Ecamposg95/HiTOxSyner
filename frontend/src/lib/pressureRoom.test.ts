import { test } from "node:test";
import assert from "node:assert/strict";
import {
  ACTS, ACTORS, HOLD_MINUTES, caseClock, firedEvents, formatClock, formatCountdown, initialState, isFinished,
  minutesToDeadline, nextRelease, pendingEvent, pressureLevel, reduce, releaseMap, typingActor,
} from "./pressureRoom.ts";

test("el guion es consistente: eventos ordenados, actores conocidos, 4 liberaciones por acto", () => {
  for (const act of ACTS) {
    const ats = act.events.map((e) => e.at);
    assert.deepEqual(ats, [...ats].sort((a, b) => a - b), `acto ${act.id} desordenado`);
    assert.equal(new Set(act.events.map((e) => e.id)).size, act.events.length, `ids repetidos en ${act.id}`);
    for (const e of act.events) if (e.actor) assert.ok(ACTORS[e.actor], `actor ${e.actor} no existe`);
    const releases = act.events.filter((e) => e.kind === "release");
    assert.equal(releases.length, 4);
    assert.equal(releases[0].gated, undefined, "la primera liberación abre el acto sin compuerta");
    assert.ok(releases.slice(1).every((r) => r.gated && r.reason), "1B..4D pasan por el Director");
    assert.equal(act.events.at(-1)?.kind, "end");
  }
});

test("initialState dispara la liberación inicial y deja el reloj en 0", () => {
  const s = initialState("I");
  assert.equal(s.clock, 0);
  assert.equal(s.running, false);
  assert.ok(s.fired.includes("1A"));
  assert.equal(s.pods.length, 4);
  assert.equal(s.pods[0].pressure, 55);
  assert.equal(caseClock(s), "08:35");
});

test("tick dispara eventos en orden y se detiene en la compuerta del Director", () => {
  let s = reduce(initialState("I"), { type: "play" });
  s = reduce(s, { type: "tick", dt: 20 });
  assert.equal(s.clock, 12, "el reloj se detiene en 1B");
  assert.equal(s.running, false);
  assert.equal(pendingEvent(s)?.code, "1B");
  assert.ok(!s.fired.includes("1B"));
  assert.ok(s.fired.includes("o2"));
  // mientras hay propuesta pendiente el reloj no avanza
  assert.equal(reduce(s, { type: "tick", dt: 5 }).clock, 12);
  assert.equal(reduce(s, { type: "play" }).running, false);
});

test("approve libera y reanuda; los efectos se aplican a las mesas", () => {
  let s = reduce(initialState("I"), { type: "tick", dt: 20 });
  const before = s.pods[0].evidence;
  s = reduce(s, { type: "approve" });
  assert.ok(s.fired.includes("1B"));
  assert.equal(s.running, true);
  assert.equal(s.pending, null);
  assert.ok(s.pods.every((p) => p.evidence === 45 && p.evidence > before));
  assert.equal(nextRelease(s)?.event.code, "1C");
  assert.equal(nextRelease(s)?.inMinutes, 10);
});

test("hold desplaza lo no liberado HOLD_MINUTES y vuelve a proponer", () => {
  let s = reduce(initialState("I"), { type: "tick", dt: 20 });
  s = reduce(s, { type: "hold" });
  assert.equal(s.pending, null);
  assert.equal(s.offset, HOLD_MINUTES);
  assert.equal(nextRelease(s)?.inMinutes, HOLD_MINUTES);
  s = reduce(s, { type: "tick", dt: HOLD_MINUTES });
  assert.equal(pendingEvent(s)?.code, "1B");
  assert.equal(s.clock, 12 + HOLD_MINUTES);
});

test("las alertas y decisiones de los pods salen del guion", () => {
  const s = reduce(initialState("I"), { type: "tick", dt: 11 });
  assert.deepEqual(s.pods[0].alerts, ["Certeza sin evidencia"]);
  assert.equal(s.pods[1].decidedAt, 10);
  assert.equal(s.pods[3].certainty, 85);
  assert.equal(s.pods[2].decidedAt, null);
});

test("un acto completo termina con todos los pods decididos y sin presión fuera de rango", () => {
  for (const act of ACTS) {
    let s = initialState(act.id);
    for (let i = 0; i < 200 && !isFinished(s); i++) {
      s = reduce(s, { type: "tick", dt: 1 });
      if (s.pending) s = reduce(s, { type: "approve" });
    }
    assert.ok(isFinished(s), `acto ${act.id} no terminó`);
    assert.equal(s.running, false);
    assert.equal(firedEvents(s).length, act.events.length);
    assert.ok(s.pods.every((p) => p.decidedAt !== null), `acto ${act.id}: pod sin decidir`);
    assert.ok(s.pods.every((p) => p.pressure >= 0 && p.pressure <= 100));
    assert.ok(releaseMap(s).every((r) => r.status === "fired"));
  }
});

test("act y reset reinician el estado", () => {
  let s = reduce(initialState("I"), { type: "tick", dt: 30 });
  s = reduce(s, { type: "act", actId: "III" });
  assert.equal(s.actId, "III");
  assert.equal(s.clock, 0);
  assert.equal(caseClock(s), "09:00");
  s = reduce(reduce(s, { type: "tick", dt: 5 }), { type: "reset" });
  assert.equal(s.clock, 0);
  assert.equal(s.actId, "III");
});

test("reloj y cuenta regresiva", () => {
  assert.equal(formatClock(8 * 60 + 35), "08:35");
  assert.equal(formatClock(24 * 60 + 5), "00:05");
  const s = initialState("I");
  assert.equal(minutesToDeadline(s), 85);
  assert.equal(formatCountdown(85), "1:25");
  assert.equal(formatCountdown(-3), "−0:03");
  assert.equal(formatCountdown(0), "0:00");
});

test("typingActor solo mientras corre y el siguiente mensaje está cerca", () => {
  const s = reduce(initialState("I"), { type: "play" });
  assert.equal(typingActor(s)?.id, "sofia"); // m2 en el minuto 2
  assert.equal(typingActor(reduce(s, { type: "pause" })), null);
  assert.equal(typingActor(reduce(s, { type: "tick", dt: 20 })), null); // pendiente 1B
});

test("pressureLevel y mapa de liberación", () => {
  assert.equal(pressureLevel(20), "low");
  assert.equal(pressureLevel(45), "mid");
  assert.equal(pressureLevel(70), "high");
  const map = releaseMap(reduce(initialState("I"), { type: "tick", dt: 20 }));
  assert.deepEqual(map.map((r) => r.status), ["fired", "pending", "next", "later"]);
});
