# Rediseño premium de la UI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-skin del frontend al estilo "Midnight Private Bank" (oscuro por defecto, claro marfil con toggle) y rediseño de Overview, Roadmap, Initiative detail y Leadership Lab, sin tocar backend.

**Architecture:** Los colores pasan a ser CSS custom properties por tema (`data-theme` en `<html>`) y Tailwind los consume como `rgb(var(--x) / <alpha-value>)`, así las clases existentes (`bg-canvas`, `text-ink`…) cambian de tema solas. La lógica nueva que no es JSX (contraste, progreso por fase, layout de la timeline, tema guardado) vive en funciones puras en `src/lib/` con tests `node --test` (Node 24 ejecuta TS por type stripping; cero dependencias nuevas). Las páginas consumen esos helpers y los componentes compartidos rediseñados.

**Tech Stack:** React 18, TypeScript strict, Vite 5, Tailwind 3, Zustand 4, Recharts 2, Google Fonts (Fraunces + Inter).

**Spec:** `docs/superpowers/specs/2026-10-21-premium-ui-design.md`

## Global Constraints

- Solo `frontend/` (más este plan). Sin cambios en `app/`, `alembic/`, `tests/` ni contratos de API; `pytest -q -W error` sigue en 140 passed.
- Sin dependencias npm nuevas. Fuentes: Fraunces 500/600, Inter 400/500/600/700 vía Google Fonts.
- Nada de datos inventados: sin tendencias, deltas ni históricos.
- Contraste WCAG AA: 4.5:1 texto normal, 3:1 texto grande/UI, en ambos temas.
- Responsive desde 390 px sin scroll horizontal de página; bajo 1024 px (`lg`) el sidebar es drawer.
- Visibilidad por rol idéntica: `can(...)`, Lab fuera del sidebar para colaboradores, tarjeta Lab solo si `dashboard.lab`.
- `npm run build` limpio (tsc strict) al final de cada tarea.
- UI en español con términos clave en inglés (Findings, Initiatives, Roadmap, Actions, Decisions, Meetings, Documents, Leadership Lab, Overview).
- Tests frontend: `cd frontend && npm test` (= `node --test src/**/*.test.ts`). Los `*.test.ts` se excluyen de `tsc` (no hay `@types/node`); los módulos que testean no importan nada en runtime salvo otros módulos de `src/lib` con extensión `.ts` explícita (`import type` sí se permite).

## Review Focus

1. **Engagement vacío** (0 initiatives, 0 milestones, 0 CTAs): cockpit, timeline y donas muestran "—"/estado vacío, nunca `NaN`, `Infinity` ni `0/0`. → tests en Task 4 (`avgProgress([])`, `phaseProgress([])`) y Task 5 (`buildTimeline([])`) y Task 7 (`ctaSlices` con total 0).
2. **Todas las fechas iguales o solo hitos sin fecha:** la timeline no divide por cero y los sin fecha van a "Sin fecha". → test en Task 5.
3. **Fechas `YYYY-MM-DD` en México (UTC−6):** se interpretan como fecha local, no UTC (sin corrimiento de un día en la posición ni en "Vencida"). → tests en Task 4 (`isOverdue`) y Task 5 (`positionPct`).
4. **`localStorage` bloqueado o con valor basura:** el tema cae a oscuro sin romper la app. → test en Task 1 (`parseTheme`).
5. **Nombres largos** (engagement, initiative, hito) a 390 px: truncan con `truncate`/`min-w-0`, sin scroll horizontal de página. → paso de verificación manual en Task 8.

---

## File Structure

| Archivo | Responsabilidad |
|---|---|
| `frontend/src/index.css` | Tokens por tema, clases base (`.card`, `.panel`, `.btn*`, `.input`, `.label`, `.eyebrow`, `.kpi-value`, `.badge-*`) |
| `frontend/tailwind.config.js` | Colores → variables; `fontFamily.display` |
| `frontend/index.html` | Fuentes, script anti-parpadeo de tema |
| `frontend/src/lib/theme.ts` (+test) | `parseTheme`, constantes del tema |
| `frontend/src/lib/contrast.ts` (+`tokens.test.ts`) | Ratio WCAG; el test lee `index.css` y valida pares AA |
| `frontend/src/stores/theme.ts` | Store Zustand del tema |
| `frontend/src/lib/format.ts` (+test) | `initials` |
| `frontend/src/lib/cockpit.ts` (+test) | Cálculos del Overview |
| `frontend/src/lib/timeline.ts` (+test) | Geometría de la timeline del Roadmap |
| `frontend/src/lib/charts.ts` (+test) | `chartColors()` y `ctaSlices()` para Recharts |
| `frontend/src/components/*` | Shell y componentes compartidos rediseñados |
| `frontend/src/components/roadmap/RoadmapTimeline.tsx` | Vista Timeline |
| `frontend/src/components/lab/LabCharts.tsx` | Dona + barras apiladas del Lab |

---

### Task 1: Tokens, tema y tipografía

**Files:**
- Modify: `frontend/package.json`, `frontend/tsconfig.json`, `frontend/tailwind.config.js`, `frontend/index.html`, `frontend/src/index.css`
- Create: `frontend/src/lib/theme.ts`, `frontend/src/lib/theme.test.ts`, `frontend/src/lib/contrast.ts`, `frontend/src/lib/tokens.test.ts`, `frontend/src/stores/theme.ts`

**Interfaces:**
- Produces: `type Theme = "dark" | "light"`; `THEME_KEY = "hito-theme"`; `parseTheme(raw: string | null | undefined): Theme`; `contrastRatio(a: string, b: string): number` (hex `#RRGGBB`); `useThemeStore` con `{ theme: Theme; toggle(): void }`. Clases Tailwind: `canvas`, `surface`, `surface-2`, `line`, `ink`, `muted`, `accent`, `accent-fill`, `accent-ink`, `warn`, `danger`, `nav`, `nav-ink`, `nav-accent`; `font-display`. Clases CSS: `.card`, `.panel`, `.btn`, `.btn-primary`, `.btn-ghost`, `.input`, `.label`, `.eyebrow`, `.kpi-value`, `.badge`, `.badge-ok|warn|danger|neutral`.

- [ ] **Step 1: Infra de tests.** En `package.json` agregar `"test": "node --test 'src/**/*.test.ts'"`. En `tsconfig.json` agregar `"exclude": ["src/**/*.test.ts"]`.

- [ ] **Step 2: Tests que fallan**

`src/lib/theme.test.ts`:
```ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { parseTheme } from "./theme.ts";
test("parseTheme acepta light y dark", () => { assert.equal(parseTheme("light"), "light"); assert.equal(parseTheme("dark"), "dark"); });
test("parseTheme cae a dark con basura o null", () => { for (const v of [null, undefined, "", "LIGHT", "blue"]) assert.equal(parseTheme(v), "dark"); });
```

`src/lib/tokens.test.ts`: lee `src/index.css` con `readFileSync(new URL("../index.css", import.meta.url))`, extrae de los bloques `[data-theme="dark"]` y `[data-theme="light"]` las variables con valor `R G B` y valida:
```ts
test("contrastRatio de referencia", () => { assert.equal(contrastRatio("#000000", "#FFFFFF").toFixed(1), "21.0"); });
// por tema, texto normal ≥ 4.5 sobre canvas y surface:
for (const fg of ["ink", "muted", "accent", "warn", "danger"]) for (const bg of ["canvas", "surface", "surface-2"]) assert.ok(ratio(fg, bg) >= 4.5, `${theme} ${fg}/${bg}`);
assert.ok(ratio("accent-ink", "accent") >= 4.5);
assert.ok(ratio("nav-ink", "nav") >= 4.5); assert.ok(ratio("nav-accent", "nav") >= 4.5);
// badges: --badge-X-fg sobre --badge-X-bg ≥ 4.5 en tema claro (en oscuro el bg es translúcido: validar fg sobre surface)
```

- [ ] **Step 3: Verificar que fallan.** `cd frontend && npm test` → FAIL (`Cannot find module ./theme.ts`).

- [ ] **Step 4: Implementar.**
  - `theme.ts`: `parseTheme` devuelve `"light"` solo con `"light"` exacto.
  - `contrast.ts`: luminancia relativa WCAG 2.x, `(L1+0.05)/(L2+0.05)`.
  - `index.css`: `:root, [data-theme="dark"] { … }` y `[data-theme="light"] { … }` con los valores de la tabla del spec escritos como tripletas `R G B` (ej. `--canvas: 10 16 32;`). `--line` oscuro = `26 34 54` (≈`#1A2236`). `--accent-fill`: oscuro = accent, claro `14 159 85`. Badges como variables completas (`--badge-ok-bg`, `--badge-ok-fg`, …): oscuro bg = `rgb(color / .12)`, fg = color; claro los pasteles del spec (neutral = surface-2 / muted). `body { @apply bg-canvas text-ink font-sans; }`; `color-scheme: dark|light` por tema. `.card`/`.panel`: `rounded-[10px] border border-line bg-surface` (oscuro con `background-image: linear-gradient(180deg, #0D1426, #111A30)` solo en `[data-theme="dark"] .card`). `.btn`: surface-2 + borde line, hover con borde ink/20. `.btn-primary`: `bg-accent text-accent-ink border-accent`. `.btn-ghost`: sin fondo ni borde. `.input` (aplica también a `select`/`textarea`, que ya usan `.input`): `bg-surface-2 border-line`, foco `ring-2 ring-accent outline-none`. `.label` y `.eyebrow`: `text-[10.5px] font-medium uppercase tracking-[0.2em] text-muted` (`.label` añade `mb-1 block`). `.kpi-value`: `font-display text-[30px] font-medium leading-none tabular-nums`. `.badge`: `inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium`.
  - `tailwind.config.js`: cada color `rgb(var(--<name>) / <alpha-value>)`; `fontFamily.display = ["Fraunces", "Georgia", "serif"]`.
  - `index.html`: link de Google Fonts con `Fraunces:opsz,wght@9..144,500;9..144,600` + Inter; quitar `bg-white text-ink` del body; en `<head>` antes de los CSS: script inline que lee `localStorage["hito-theme"]` en try/catch y pone `document.documentElement.dataset.theme` (`"light"` o `"dark"`).
  - `stores/theme.ts`: estado inicial = `parseTheme(document.documentElement.dataset.theme)`; `toggle()` cambia, escribe `dataset.theme` y `localStorage` (try/catch).

- [ ] **Step 5: Verificar.** `npm test` → PASS (ajustar valores solo si el test de contraste falla y documentar el cambio en el commit). `npm run build` → OK.

- [ ] **Step 6: Commit** `feat(ui): tokens por tema, tipografía y store de tema`

---

### Task 2: Shell — Sidebar, Header y Login

**Files:**
- Modify: `frontend/src/lib/labels.ts`, `frontend/src/components/Sidebar.tsx`, `frontend/src/components/Header.tsx`, `frontend/src/components/AppShell.tsx`, `frontend/src/pages/LoginPage.tsx`
- Create: `frontend/src/lib/format.ts`, `frontend/src/lib/format.test.ts`

**Interfaces:**
- Consumes: `useThemeStore` (Task 1).
- Produces: `NAV_GROUPS: { label: string | null; items: { to: string; label: string; end?: boolean }[] }[]` (reemplaza `NAV_ITEMS`); `initials(name: string): string`.

- [ ] **Step 1: Test que falla** (`format.test.ts`):
```ts
assert.equal(initials("Syner Admin"), "SA");
assert.equal(initials("Dirección HiTO (demo)"), "DH");
assert.equal(initials("  ana  "), "A");
assert.equal(initials(""), "?");
```
- [ ] **Step 2:** `npm test` → FAIL.
- [ ] **Step 3: Implementar.**
  - `initials`: primeras letras de las dos primeras palabras alfabéticas, mayúsculas; `"?"` si no hay.
  - `NAV_GROUPS`: `null` → Overview (`/`, end); "Estrategia" → Findings, Initiatives, Roadmap; "Ejecución" → Actions, Decisions, Meetings, Documents; "Liderazgo" → Leadership Lab (`/lab`). Sidebar filtra `/lab` con `can(user, "viewLabSummary")` y oculta grupos vacíos.
  - Sidebar: `bg-nav text-nav-ink w-60`; logotipo "HiTO" `font-display text-2xl` + eyebrow "TRANSFORMATION ROOM" (color `nav-ink/60`); títulos de grupo como eyebrow; activo = `text-nav-accent` + `border-l-2 border-nav-accent`, inactivo `text-nav-ink/70 border-transparent`; pie "Syner × HiTO".
  - Header (`bg-surface border-b border-line`): botón menú (`lg:hidden`); selector de engagement (`select.input`, `max-w-[50vw] sm:max-w-xs truncate`); búsqueda deshabilitada `hidden md:block` con `title="Próximamente"`; quitar el botón de notificaciones; toggle con texto ☾/☀ y `aria-label={theme === "dark" ? "Cambiar a tema claro" : "Cambiar a tema oscuro"}`; botón avatar circular con `initials(user.full_name)`, `aria-haspopup="menu"`, `aria-expanded`; menú desplegable (`.card` absoluto) con nombre, `ROLE_LABELS[role] · organization_name` y botón "Salir" (logout + `/login`). Cierra con Escape y click fuera.
  - AppShell: overlay del drawer `bg-[rgba(5,8,16,.6)] backdrop-blur-sm`; `main` con `min-w-0`.
  - LoginPage: `lg:grid lg:grid-cols-2 min-h-screen`; izquierda `bg-nav text-nav-ink` con "HiTO" `font-display text-6xl`, "Transformation Room" y "Syner × HiTO"; derecha `bg-surface` con el formulario (labels Email/Password, botón `btn-primary` "Entrar"); bajo `lg` una columna con la marca arriba (bloque marino compacto). Toggle de tema también en la esquina del login.
- [ ] **Step 4:** `npm test` y `npm run build` → OK. Verificación manual en `npm run dev`: los 3 roles (collab sin Leadership Lab), toggle persiste tras recarga, drawer a 390 px.
- [ ] **Step 5: Commit** `feat(ui): sidebar marino agrupado, header con tema y avatar, login en dos columnas`

---

### Task 3: Componentes compartidos

**Files:**
- Modify: `frontend/src/components/{PageHeader,StatusBadge,ProgressBar,FormDrawer,EmptyState,DataTable,Block}.tsx`, `frontend/src/pages/LabPage.tsx:28` (tab activa)
- Create: `frontend/src/components/KpiCard.tsx`, `frontend/src/components/ProgressRing.tsx`
- Delete: `frontend/src/components/Tile.tsx` (usos → `KpiCard`)

**Interfaces:**
- Produces:
  - `PageHeader({ eyebrow?: string; title: string; subtitle?: string; action?: ReactNode })`
  - `KpiCard({ label: string; value: ReactNode; note?: ReactNode; tone?: "default" | "ok" | "warn" | "danger"; visual?: ReactNode })` — `visual` se pinta a la izquierda de la cifra (para el anillo).
  - `ProgressRing({ value: number; size?: number /* 56 */; label?: string })` — SVG, pista `stroke-line`, arco `stroke-accent-fill`, `role="img" aria-label={label ?? \`${value}%\`}`, valor clampeado 0–100.
  - `StatusBadge({ value: string })` con `TONE: Record<string, "ok" | "warn" | "danger" | "neutral">` (exportado) → clase `badge badge-${tone}`. Mapear los mismos valores que hoy: verdes → ok, ámbar → warn, rojos → danger, grises → neutral; desconocidos → neutral.
  - `ProgressBar({ value: number })` relleno `bg-accent-fill`.
- [ ] **Step 1: Implementar** según el spec §2: PageHeader con `.eyebrow` + h1 `font-display text-[28px] md:text-[32px] font-medium`; Block → `.panel p-5`, título `font-display text-[15px] font-medium text-ink` (sin uppercase); FormDrawer: overlay `bg-[rgba(5,8,16,.6)] backdrop-blur-sm`, panel `bg-surface border-l border-line`, título `font-display text-lg`, Escape cierra; EmptyState: icono SVG lineal (círculo vacío, `stroke-muted`), título `font-display`; DataTable: `<thead>` con `.eyebrow` sin fondo, filas `border-line`, hover/focus `bg-surface-2`, `tabular-nums` en la tabla; LabPage tab activa `border-accent text-ink`.
- [ ] **Step 2: Sin colores fijos.** `grep -rnE "bg-white|gray-[0-9]|emerald-|amber-|red-[0-9]|bg-black/|border-ink|bg-ink|text-white" frontend/src` → sin resultados (reemplazar los de `LabSummaryView` por `bg-accent-fill`, `bg-warn`, `bg-muted`, `bg-line`).
- [ ] **Step 3:** `npm run build` → OK; ver Findings y un drawer en ambos temas.
- [ ] **Step 4: Commit** `feat(ui): componentes compartidos con tokens (KpiCard, ProgressRing, badges, drawer)`

---

### Task 4: Overview cockpit

**Files:**
- Create: `frontend/src/lib/cockpit.ts`, `frontend/src/lib/cockpit.test.ts`
- Modify: `frontend/src/pages/DashboardPage.tsx`

**Interfaces:**
- Consumes: `KpiCard`, `ProgressRing`, `StatusBadge`, `Block`, `ProgressBar` (Task 3).
- Produces (`cockpit.ts`, solo `import type` de `../types`):
  - `avgProgress(items: { progress_pct: number }[]): number | null` — promedio redondeado; `null` si vacío.
  - `phaseProgress(milestones: { status: string }[]): number | null` — % Done redondeado; `null` si vacío.
  - `initiativeTone(status: InitiativeStatus): "accent" | "muted" | "warn"` — Execution/Monitoring/Completed → accent; Discovery/Design/Validation → muted; On Hold → warn.
  - `isOverdue(date: string | null, today: Date): boolean` — compara la fecha `YYYY-MM-DD` contra la fecha local de `today` (sin horas); `null` → false.
  - `todayLocal(): Date` (medianoche local) para las páginas.

- [ ] **Step 1: Tests que fallan:**
```ts
assert.equal(avgProgress([]), null);
assert.equal(avgProgress([{ progress_pct: 10 }, { progress_pct: 25 }]), 18);
assert.equal(phaseProgress([]), null);
assert.equal(phaseProgress([{ status: "Done" }, { status: "Planned" }, { status: "Done" }]), 67);
assert.equal(initiativeTone("Monitoring"), "accent"); assert.equal(initiativeTone("Validation"), "muted"); assert.equal(initiativeTone("On Hold"), "warn");
const today = new Date(2026, 9, 22, 23, 30); // 22 oct, 23:30 local
assert.equal(isOverdue("2026-10-21", today), true);
assert.equal(isOverdue("2026-10-22", today), false);
assert.equal(isOverdue(null, today), false);
```
- [ ] **Step 2:** `npm test` → FAIL. **Step 3:** implementar. **Step 4:** `npm test` → PASS.
- [ ] **Step 5: Reescribir `DashboardPage`** en el orden del spec §3:
  1. `PageHeader eyebrow="Syner × HiTO · Engagement" title={engagement.name} subtitle={engagement.subtitle}`.
  2. Grid `grid-cols-1 sm:grid-cols-2 xl:grid-cols-4` de `KpiCard`: "Avance del programa" (`visual=<ProgressRing value={progress_pct}/>`, valor `N%`, nota `<StatusBadge value={health}/>`); "Initiatives activas" (nota `avance promedio ${avg ?? "—"}% · ${open_actions} acciones abiertas`, si `avg` es null escribir "avance promedio —"); "Decisiones pendientes" (tono warn si > 0, nota "requieren a Dirección"); "Findings críticos" (tono danger si > 0).
  3. Resumen ejecutivo: mismo flujo de edición actual; texto `font-display text-[15px] leading-7`.
  4. `lg:grid-cols-2`: *Roadmap por fase* (una fila por `roadmap[]`: nombre, `ProgressBar`, `${pct}%` o "—"; acción "Roadmap →") | *Decisiones requeridas* (título, owner; a la derecha la fecha `decided_on` si existe, con badge "Vencida" (`badge-danger`) si `isOverdue(decided_on, today)`; sin fecha → `StatusBadge` del status; acción "Decision Log →"). *Nota: `Decision` no tiene fecha límite; se usa `decided_on`, el único campo de fecha.*
  5. `lg:grid-cols-3`: *Initiatives* (punto `h-2 w-2 rounded-full bg-{tone}`, nombre con link `truncate`, `%`) | *Próximos hitos* | *Leadership Lab* si `data.lab` (próxima sesión, `ProgressBar` de `evidenced_pct`, `active_contracts` contratos activos) o *Próximas acciones* si es null.
  6. `lg:grid-cols-2`: *Key findings* y *Actividad reciente*.
- [ ] **Step 6:** `npm run build` → OK. Manual: admin y exec ven tarjeta Lab; collab ve Próximas acciones.
- [ ] **Step 7: Commit** `feat(ui): Overview tipo cockpit`

---

### Task 5: Roadmap Timeline

**Files:**
- Create: `frontend/src/lib/timeline.ts`, `frontend/src/lib/timeline.test.ts`, `frontend/src/components/roadmap/RoadmapTimeline.tsx`
- Modify: `frontend/src/pages/RoadmapPage.tsx`

**Interfaces:**
- Produces (`timeline.ts`):
  - `parseLocalDate(iso: string): Date` — `YYYY-MM-DD` → medianoche local.
  - `interface TimelineModel { start: Date; end: Date; months: { key: string; label: string; leftPct: number }[]; dated: Milestone[]; undated: Milestone[] }`
  - `buildTimeline(milestones: Milestone[]): TimelineModel | null` — `null` si no hay hitos con fecha. `start` = día 1 del mes de la fecha mínima; `end` = día 1 del mes siguiente al de la fecha máxima, más 1 mes de margen (spec: "+1 mes"). `months` cubre `[start, end)`, `label` con `Intl.DateTimeFormat("es-MX", { month: "short", year: "2-digit" })`.
  - `positionPct(model: TimelineModel, date: Date): number` — `(date - start) / (end - start) * 100`, clampeado a [0, 100].
  - `RoadmapTimeline({ milestones: Milestone[]; onSelect: (m: Milestone) => void })`.

- [ ] **Step 1: Tests que fallan:**
```ts
assert.equal(buildTimeline([]), null);
assert.equal(buildTimeline([ms({ due_date: null })]), null);
const one = buildTimeline([ms({ due_date: "2026-11-15" })])!;   // misma fecha: rango no vacío
assert.equal(one.start.getMonth(), 10); assert.equal(one.months.length, 2);
assert.ok(positionPct(one, parseLocalDate("2026-11-15")) > 0 && positionPct(one, parseLocalDate("2026-11-15")) < 100);
const m = buildTimeline([ms({ due_date: "2026-10-01" }), ms({ due_date: "2026-12-20" }), ms({ due_date: null })])!;
assert.equal(m.undated.length, 1); assert.equal(m.dated.length, 2);
assert.equal(m.months.length, 4);                                   // oct, nov, dic + margen ene
assert.equal(positionPct(m, parseLocalDate("2026-10-01")), 0);     // sin corrimiento UTC
assert.equal(parseLocalDate("2026-10-01").getDate(), 1);
assert.equal(positionPct(m, new Date(2030, 0, 1)), 100);
```
(`ms(partial)` = helper local del test que completa un `Milestone`.)
- [ ] **Step 2:** `npm test` → FAIL. **Step 3:** implementar `timeline.ts`. **Step 4:** `npm test` → PASS.
- [ ] **Step 5: `RoadmapTimeline`.** Panel `.panel overflow-x-auto` con contenido `min-w-[720px]`; columna izquierda fija de 120 px con el nombre de cada fase (`ROADMAP_PHASES`, todas las filas aunque estén vacías); cabecera de meses posicionada con `leftPct`; cada hito = botón rombo (`h-3 w-3 rotate-45`) en `left: positionPct%` con color por estado (Done → `bg-accent-fill`, In Progress → `bg-accent-fill/50` con borde accent, Planned → `bg-muted`, Slipped → `bg-danger`), `title` y `aria-label` = `"${name} · ${formatDate(due_date)} · ${status}"`; línea vertical "Hoy" `bg-accent` si hoy cae en el rango; leyenda de estados debajo; sección "Sin fecha" con la lista de `undated`. `null` → `EmptyState` "Sin hitos con fecha".
- [ ] **Step 6: `RoadmapPage`.** `const view = params.get("view") === "list" ? "list" : "timeline"`; segmented control "Timeline | Lista" (`aria-pressed`) que hace `setParams({ view })`. Lista = la grilla actual sin cambios funcionales. En Timeline, `onSelect` abre `openEdit(m)` si `writable`; si no, abre `FormDrawer` en modo lectura (`hideSubmit`, campos como `Prose`: fase, fecha, estado, owner, initiative, deliverable, descripción).
- [ ] **Step 7:** `npm run build` → OK. Manual: 390 px → la timeline hace scroll dentro del panel y la página no.
- [ ] **Step 8: Commit** `feat(ui): timeline del Roadmap con toggle Timeline/Lista`

---

### Task 6: Initiative detail ("ficha")

**Files:**
- Modify: `frontend/src/pages/InitiativeDetailPage.tsx`

**Interfaces:**
- Consumes: `PageHeader`, `KpiCard`, `ProgressRing`, `StatusBadge`, `Block`, `Prose`.

- [ ] **Step 1: Reestructurar la cabecera:** link "← Initiatives", `PageHeader eyebrow={i.area || "Initiative"} title={i.name}` con `action` = botón Editar (solo `writable`), badges de `status` y `priority` bajo el título.
- [ ] **Step 2: Banda de 4 `KpiCard`** (`grid-cols-2 lg:grid-cols-4`): "Avance" (`visual` = `ProgressRing`, valor `N%`), "Owner HiTO" (`hito_owner || "—"`, valor en `text-lg` para que no desborde: `value` como `<span className="font-display text-lg">`), "Inicio" (`formatDate(start_date)`), "Objetivo" (`formatDate(target_date)`).
- [ ] **Step 3: Cuerpo `lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]`:** izquierda bloques Objetivo, Descripción, Resultado esperado (`Prose`); derecha los bloques actuales (Milestones, Actions, Decisions, Findings, Documents con link/unlink, Comments) sin cambio funcional.
- [ ] **Step 4:** `npm run build` → OK; manual con admin (editar, vincular documento) y collab (solo lectura + comentar).
- [ ] **Step 5: Commit** `feat(ui): ficha de Initiative`

---

### Task 7: Leadership Lab con gráficas

**Files:**
- Create: `frontend/src/lib/charts.ts`, `frontend/src/lib/charts.test.ts`, `frontend/src/components/lab/LabCharts.tsx`
- Modify: `frontend/src/components/lab/LabSummaryView.tsx`, `frontend/src/pages/LabPage.tsx`, `frontend/src/lib/labels.ts` (`LabTab`, `LAB_TABS`)

**Interfaces:**
- Consumes: `useThemeStore` (Task 1), `KpiCard` (Task 3).
- Produces:
  - `ctaSlices(t: CtaStatusTotals): { key: "evidenced" | "in_progress" | "committed" | "dropped"; label: string; value: number }[]` — en ese orden, omite valores 0; `[]` si `total === 0`.
  - `chartColors(): { evidenced: string; in_progress: string; committed: string; dropped: string; grid: string; text: string }` — lee `getComputedStyle(document.documentElement)` de `--accent-fill`, `--warn`, `--muted`, `--line`, `--line`, `--muted` y devuelve `rgb(r g b)`; `committed` usa `--muted`, `dropped` `--line`.
  - `LabSummaryContent({ data: LabSummary })` — KPIs + dona + barras + sesiones (sin `PageHeader`).
  - `CtaDonut({ totals: CtaStatusTotals; evidencedPct: number })`, `CtaStackedBars({ rows: { label: string; totals: CtaStatusTotals }[] })`.
  - `LabTab` gana `"summary"`; `LAB_TABS` empieza con `{ key: "summary", label: "Resumen" }` y es la tab por defecto de Syner.

- [ ] **Step 1: Test que falla:**
```ts
assert.deepEqual(ctaSlices({ committed: 0, in_progress: 0, evidenced: 0, dropped: 0, total: 0 }), []);
assert.deepEqual(ctaSlices({ committed: 2, in_progress: 0, evidenced: 3, dropped: 1, total: 6 }).map((s) => s.key), ["evidenced", "committed", "dropped"]);
```
- [ ] **Step 2:** `npm test` → FAIL. **Step 3:** implementar `ctaSlices` (y `chartColors`, sin test: depende del DOM). **Step 4:** `npm test` → PASS.
- [ ] **Step 5: `LabCharts.tsx`.** Cada gráfica lee `const theme = useThemeStore((s) => s.theme)` y calcula `chartColors()` en `useMemo([theme])`, y el contenedor lleva `key={theme}` para forzar el redibujado. `CtaDonut`: `PieChart` con `Pie innerRadius="70%"` sobre `ctaSlices`, centro con `evidenced_pct%` en `font-display` + "con evidencia"; total 0 → anillo vacío `stroke-line` y "Sin CTAs". `CtaStackedBars`: `BarChart layout="vertical"` con 4 `Bar stackId="cta"` (orden evidenced, in_progress, committed, dropped), ejes con `colors.text`, sin grid vertical, `Tooltip` con fondo surface; altura `40 * rows + 40`. Leyenda común con los cuatro estados. Solo datos agregados: no se añaden props con nombres de participantes ni textos de CTA.
- [ ] **Step 6: `LabSummaryView`** = `PageHeader eyebrow="Liderazgo"` + carga + `LabSummaryContent`. `LabSummaryContent`: `KpiCard` "Sesiones realizadas" (`sessions_done/sessions.length`) y "Contratos activos"; panel con `CtaDonut`; dos paneles `CtaStackedBars` (por sesión y por pod); panel Sesiones restilizado (lista actual). Retirar `CtaStatusBar`/`CtaLegend` si quedan sin uso (`grep -rn "CtaStatusBar\|CtaLegend" frontend/src`).
- [ ] **Step 7: `LabPage` (Syner).** Tab `summary` por defecto: carga `labApi.summary(engagementId)` con `useResource` y pinta `LabSummaryContent`. Las demás tabs sin cambio funcional; restilizar sus tablas solo vía componentes compartidos.
- [ ] **Step 8:** `npm run build` → OK. Manual: exec ve solo el resumen (y `/lab/participants` sigue dando 403); toggle de tema recolorea las gráficas sin recargar.
- [ ] **Step 9: Commit** `feat(ui): Leadership Lab con dona y barras apiladas`

---

### Task 8: Resto de páginas y verificación final

**Files:**
- Modify: `frontend/src/pages/{FindingsPage,InitiativesPage,ActionsPage,DecisionsPage,MeetingsPage,MeetingDetailPage,DocumentsPage}.tsx`, `frontend/src/components/{Comments,ActionForm,DecisionForm,InitiativeForm}.tsx`, `frontend/src/components/lab/{SessionsTab,ParticipantsTab,CtaTrackerTab,ContractsTab}.tsx` (solo clases)

- [ ] **Step 1: Re-skin.** Cada `PageHeader` recibe `eyebrow` según su grupo del sidebar ("Estrategia", "Ejecución", "Liderazgo"). Revisar clases sueltas que asumían fondo blanco (`hover:bg-canvas` en superficies → `hover:bg-surface-2`). Sin cambios funcionales.
- [ ] **Step 2: Barrido de colores fijos:** el `grep` del Task 3 Step 2 sin resultados.
- [ ] **Step 3: Verificación automática.**
  - `cd frontend && npm test` → todos PASS.
  - `npm run build` → sin errores.
  - `cd .. && pytest -q -W error` → `140 passed`.
  - `git diff --stat docs/material-hito-syner... -- app alembic tests` → vacío.
- [ ] **Step 4: Verificación manual** (`npm run dev`, 3 roles × 2 temas): login, Overview, Roadmap (timeline y lista), Initiative detail, Lab (Syner y exec), una página CRUD con drawer. A 390 px y 1440 px: `document.documentElement.scrollWidth <= window.innerWidth` en la consola de cada página; nombres largos (editar temporalmente una initiative con un nombre de 150 caracteres) truncan sin desbordar. Recargar con tema claro → sin parpadeo oscuro.
- [ ] **Step 5: Tabla de contraste para el PR.** Generar con `contrastRatio` los ratios de ink/muted/accent/warn/danger sobre canvas y surface por tema (script de una vez en el scratchpad, no versionado) y pegarla en la descripción del PR.
- [ ] **Step 6: Commit** `feat(ui): re-skin de páginas restantes`
