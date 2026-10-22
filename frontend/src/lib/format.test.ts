import { test } from "node:test";
import assert from "node:assert/strict";
import { initials } from "./format.ts";
test("initials toma las dos primeras palabras", () => {
  assert.equal(initials("Syner Admin"), "SA");
  assert.equal(initials("Dirección HiTO (demo)"), "DH");
});
test("initials tolera espacios y vacío", () => {
  assert.equal(initials("  ana  "), "A");
  assert.equal(initials(""), "?");
});
