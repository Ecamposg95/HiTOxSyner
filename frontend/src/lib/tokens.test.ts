import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { contrastRatio } from "./contrast.ts";

const css = readFileSync(new URL("../index.css", import.meta.url), "utf8");

function block(selector: string): string {
  const start = css.indexOf(selector);
  assert.ok(start >= 0, `bloque ${selector} no encontrado`);
  const open = css.indexOf("{", start);
  return css.slice(open + 1, css.indexOf("}", open));
}

function vars(selector: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const m of block(selector).matchAll(/--([\w-]+):\s*(\d+)\s+(\d+)\s+(\d+)\s*;/g)) {
    const hex = [m[2], m[3], m[4]].map((n) => Number(n).toString(16).padStart(2, "0")).join("");
    out[m[1]] = `#${hex}`;
  }
  return out;
}

test("contrastRatio de referencia", () => {
  assert.equal(contrastRatio("#000000", "#FFFFFF").toFixed(1), "21.0");
});

const themes: Record<string, Record<string, string>> = {
  dark: vars(':root, [data-theme="dark"]'),
  light: vars('[data-theme="light"]'),
};

for (const [theme, t] of Object.entries(themes)) {
  const ratio = (fg: string, bg: string) => {
    assert.ok(t[fg] && t[bg], `${theme}: falta --${fg} o --${bg}`);
    return contrastRatio(t[fg], t[bg]);
  };
  test(`${theme}: texto normal >= 4.5 sobre canvas, surface y surface-2`, () => {
    for (const fg of ["ink", "muted", "accent", "warn", "danger"])
      for (const bg of ["canvas", "surface", "surface-2"])
        assert.ok(ratio(fg, bg) >= 4.5, `${theme} ${fg}/${bg} = ${ratio(fg, bg).toFixed(2)}`);
  });
  test(`${theme}: accent-ink/accent y nav`, () => {
    assert.ok(ratio("accent-ink", "accent") >= 4.5);
    assert.ok(ratio("nav-ink", "nav") >= 4.5);
    assert.ok(ratio("nav-accent", "nav") >= 4.5);
  });
  test(`${theme}: badges`, () => {
    for (const tone of ["ok", "warn", "danger", "neutral"]) {
      assert.ok(t[`badge-${tone}-bg`] && t[`badge-${tone}-fg`], `${theme}: falta badge ${tone}`);
      // claro: fondo opaco; oscuro: fondo translucido, se valida el fg sobre surface
      const bg = theme === "light" ? `badge-${tone}-bg` : "surface";
      const r = ratio(`badge-${tone}-fg`, bg);
      assert.ok(r >= 4.5, `${theme} badge ${tone} = ${r.toFixed(2)}`);
    }
  });
}
