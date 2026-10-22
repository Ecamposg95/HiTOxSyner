# Rediseño premium de la UI — Diseño

**Estado:** aprobado por el usuario el 2026-10-21 (dirección B "Midnight Private Bank", tema claro marfil con sidebar marino, alcance (c)).
**Base:** `docs/material-hito-syner` @ 9d98b4c (planes 1–3 desplegados).
**Mockups:** `.superpowers/brainstorm/*/content/{direction,theme-light,cockpit}.html` (git-ignored, referencia).

## Objetivo

Que la Transformation Room se vea como un producto ejecutivo de una fintech (HiTO, administrador de activos): sobrio, editorial, nivel consejo de administración. Solo cambia el frontend; la API, los permisos y los datos quedan igual.

## Restricciones globales

- Solo `frontend/`. Sin cambios en `app/`, `alembic/`, `tests/` ni contratos de API. Los 140 tests backend siguen pasando sin tocarse.
- React 18 + TS strict + Vite 5 + Tailwind 3 + Recharts 2 (ya instalado). Sin dependencias nuevas, salvo las fuentes de Google Fonts.
- Fuentes: **Fraunces** (500/600; titulares, cifras KPI, logotipo) e **Inter** (400/500/600/700; todo lo demás).
- Nada de datos inventados: sin tendencias, deltas ni históricos que la API no entrega.
- Contraste WCAG AA (4.5:1 texto normal, 3:1 texto grande y UI) en ambos temas.
- Responsive desde 390 px sin scroll horizontal de página; bajo 1024 px el sidebar sigue siendo drawer.
- Visibilidad por rol idéntica a hoy (`can(...)`, sidebar sin Lab para colaboradores, tarjeta Lab solo si `dashboard.lab`).
- `npm run build` limpio (tsc strict).

## 1. Sistema visual

### Tokens (CSS custom properties en `src/index.css`)

Tailwind mapea sus colores a variables (`rgb(var(--x) / <alpha-value>)`), así las clases existentes (`bg-canvas`, `text-ink`, `text-muted`, `border-line`, `text-danger`...) cambian de tema sin reescribir cada página.

| Token | Oscuro (default) | Claro |
|---|---|---|
| `canvas` (fondo app) | `#0A1020` | `#F7F6F2` marfil |
| `surface` (tarjetas) | `#0D1426` (gradiente sutil a `#111A30`) | `#FFFFFF` |
| `surface-2` (hover, inputs) | `#131C33` | `#F1EFE8` |
| `line` (bordes) | `rgba(255,255,255,.07)` ≈ `#1A2236` | `#E6E3DA` |
| `ink` (texto) | `#EDEFF5` | `#0A1020` |
| `muted` | `#8E97AD` | `#5F6678` |
| `accent` (señal positiva, activo) | `#5CFF9D` neón | `#0E9F55` esmeralda |
| `accent-ink` (texto sobre accent) | `#06261A` | `#FFFFFF` |
| `warn` | `#FFC24B` | `#9A5B00` |
| `danger` | `#FF7A7A` | `#C2312F` |
| `nav` (sidebar, siempre marino) | `#070C18` | `#0A1020` |
| `nav-ink` / `nav-accent` | `#EDEFF5` / `#5CFF9D` | `#EDEFF5` / `#5CFF9D` |

Badges: fondo = color de estado al 12% (oscuro) o tono pastel (claro: ok `#DDFBE9`/`#0B7A41`, warn `#FFF1D6`/`#9A5B00`, danger `#FDE2E1`/`#A32020`, neutral `surface-2`/`muted`).

### Tema

- `data-theme="dark|light"` en `<html>`; default oscuro. Store `stores/theme.ts` (Zustand) con `theme` y `toggle()`, persistido en `localStorage` (`hito-theme`) con try/catch; un script inline en `index.html` aplica el tema antes del primer pintado (sin parpadeo).
- Toggle ☾/☀ en el Header, con `aria-label` "Cambiar a tema claro/oscuro".
- Recharts lee colores de un helper `chartColors()` que resuelve las variables CSS actuales; las gráficas se re-renderizan al cambiar el tema.

### Tipografía

- `font-display` = Fraunces: h1 de página (28–32 px, peso 500), títulos de panel (15–16 px), cifras KPI (28–34 px, `tabular-nums`), logotipo "HiTO".
- Inter para cuerpo (13–14 px), tablas, formularios. Eyebrows: 10–11 px, mayúsculas, `tracking-[0.2em]`, `muted`.

## 2. Componentes compartidos

- **Sidebar:** marino en ambos temas. Logotipo "HiTO" en Fraunces + "TRANSFORMATION ROOM" en eyebrow. Grupos: *Overview*; **Estrategia** (Findings, Initiatives, Roadmap); **Ejecución** (Actions, Decisions, Meetings, Documents); **Liderazgo** (Leadership Lab). Item activo: texto neón + barra izquierda de 2 px. Pie: "Syner × HiTO".
- **Header:** selector de engagement como botón con borde, búsqueda deshabilitada (tooltip "Próximamente") conservada, toggle de tema, avatar con iniciales y menú (nombre, rol, logout).
- **PageHeader:** eyebrow (sección) + h1 Fraunces + descripción opcional + acciones a la derecha.
- **Clases base (`index.css`):** `.card`/`.panel` (surface, borde line, radio 10 px), `.btn` (surface-2), `.btn-primary` (accent con accent-ink), `.btn-ghost`, `.input`/`.select`/`.textarea` (surface-2, foco con anillo accent 2 px), `.label` (eyebrow), `.eyebrow`, `.kpi-value`.
- **DataTable:** cabecera en eyebrow sin fondo, filas con separador `line`, hover `surface-2`, cifras `tabular-nums`; mantiene filas accesibles por teclado.
- **StatusBadge:** pastilla redondeada según la tabla de tonos.
- **Tile → KpiCard:** eyebrow + cifra Fraunces + nota; tono opcional (ok/warn/danger) colorea solo la cifra.
- **ProgressBar:** pista `line`, relleno `accent`; variante anillo (`ProgressRing`, SVG) para el KPI de avance.
- **FormDrawer:** panel `surface` con overlay `rgba(5,8,16,.6)` + blur, título Fraunces.
- **EmptyState:** icono lineal sutil, título Fraunces, texto muted.
- **LoginPage:** pantalla completa en dos columnas (≥1024 px): izquierda marino con logotipo grande, tagline "Transformation Room" y línea "Syner × HiTO"; derecha formulario en surface. En móvil, una columna con la marca arriba.

## 3. Overview (cockpit)

Orden, de arriba abajo (todo con datos existentes de `GET /engagements/{id}/dashboard`):

1. **Encabezado:** eyebrow "Syner × HiTO · Engagement", h1 con `engagement.name`, subtítulo.
2. **Hero de 4 KPIs:** (a) Avance del programa — `ProgressRing` con `tiles.progress_pct` + badge de `tiles.health`; (b) Initiatives activas — `tiles.active_initiatives`, nota "avance promedio N%" calculada de `active_initiatives`; (c) Decisiones pendientes — `tiles.decisions_required` (tono warn si > 0), nota "requieren a Dirección"; (d) Findings críticos — `tiles.critical_findings` (tono danger si > 0). `tiles.open_actions` va como quinto KPI compacto en la fila o dentro del panel de acciones (ver 4).
3. **Resumen ejecutivo:** texto en Fraunces 15 px; edición inline como hoy (solo quien puede).
4. **Fila 2 columnas:** *Roadmap por fase* (una barra por fase de `roadmap`, % = hitos Done / total de la fase, "—" si sin hitos; enlace a /roadmap) | *Decisiones requeridas* (de `decisions_required`, con badge de fecha; "Vencida" en danger si due < hoy; enlace a /decisions).
5. **Fila 3 columnas:** *Initiatives* (de `active_initiatives`: punto de color por estado, nombre, % avance) | *Próximos hitos* (`next_milestones`) | *Leadership Lab* (si `lab`: próxima sesión, barra de evidencia, contratos activos) — si `lab` es null, la columna la ocupan *Próximas acciones* (`next_actions`).
6. **Fila final:** *Key findings* y *Actividad reciente* como hoy, restilizados.

Color por estado de initiative: Execution/Monitoring/Completed → accent; Discovery/Design/Validation → muted; On Hold → warn.

## 4. Vistas clave

- **Roadmap:** además de la lista actual (que se conserva como vista "Lista" con su CRUD), vista **Timeline** por defecto: filas por fase, eje horizontal de meses entre el primer y último `due_date` (+1 mes de margen), cada hito como marcador (rombo) coloreado por estado en su fecha, línea vertical "Hoy" en accent. Hitos sin fecha se listan aparte bajo "Sin fecha". Click en un hito abre el drawer de edición (si `write`) o muestra su detalle. En < 768 px la timeline hace scroll horizontal dentro de su panel (no la página). Toggle Timeline/Lista conservado en `?view=`.
- **Initiative detail ("ficha"):** encabezado con eyebrow (área), h1 Fraunces, badges de estado y prioridad; banda de 4 KPIs (avance con anillo, owner HiTO, inicio, objetivo); cuerpo en dos columnas (≥1024 px): izquierda Objetivo / Descripción / Resultado esperado con `Prose`; derecha hitos y acciones vinculados y comentarios, como hoy.
- **Leadership Lab:** `LabSummaryView` (exec) y la pestaña de resumen de Syner reciben: dona Recharts de `cta_totals` por estado con `evidenced_pct` al centro; barras apiladas por sesión (`by_session`) y por pod (`by_pod`); tarjetas KPI (sesiones hechas, contratos activos). Las tablas CRUD de Syner se restilizan sin cambio funcional. Las gráficas siguen respetando la minimización de datos (solo agregados).

## 5. Resto de páginas

Findings, Initiatives (lista), Actions, Decisions, Meetings (+detalle), Documents: re-skin vía componentes compartidos y PageHeader nuevo; sin cambios funcionales.

## 6. Verificación

- `npm run build` limpio; `pytest -q -W error` sigue en 140 passed (sin cambios backend).
- Revisión manual con los 3 roles en ambos temas: login, Overview, Roadmap (timeline y lista), Initiative detail, Lab (Syner y exec), una página CRUD con drawer.
- 390 px y 1440 px en ambos temas; sin scroll horizontal de página.
- Contraste AA verificado para ink/muted/accent/warn/danger sobre canvas y surface en ambos temas (tabla en el PR).
- Tema persistente tras recarga, sin parpadeo inicial.

## Fuera de alcance

Históricos/tendencias (requiere backend), logo oficial de HiTO en imagen (se usa logotipo tipográfico hasta tener el archivo), i18n, nuevas funcionalidades.
