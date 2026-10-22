import { test } from "node:test";
import assert from "node:assert/strict";
import { parseTheme } from "./theme.ts";
test("parseTheme acepta light y dark", () => { assert.equal(parseTheme("light"), "light"); assert.equal(parseTheme("dark"), "dark"); });
test("parseTheme cae a dark con basura o null", () => { for (const v of [null, undefined, "", "LIGHT", "blue"]) assert.equal(parseTheme(v), "dark"); });
