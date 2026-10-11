# Syner × HiTO Transformation Room — Diseño del primer release

Fecha: 2026-10-11
Estado: aprobado en brainstorming, pendiente de revisión escrita
Fuente de requisitos: `docs/TASK_PACK_MAESTRO_Syner_x_HiTO.md` (brief maestro) y los PDFs del Executive Leadership Lab / Project ORION en `docs/`.

## 1. Objetivo y alcance

Construir y desplegar en Railway una aplicación web privada que funcione como memoria operativa y ejecutiva del engagement de consultoría de Grupo Syner con HiTO. El primer release cubre:

- **Fase 0 (foundation):** repositorio, FastAPI, React, PostgreSQL, Railway, autenticación, organizaciones, engagements, RBAC, layout.
- **Fase 1 (client room MVP):** dashboard, findings, initiatives, actions, decisions, meetings, roadmap, documents.
- **Módulo Leadership Lab "core":** sesiones, participantes, pods, CTA tracker y Leadership Action Contract. Sin observación conductual ni Leadership Pulse.

Fuera de alcance del primer release: diagnostic, risks, opportunities, deliverables, KPIs, AI opportunities, búsqueda global, Syner Cortex, agentes, observación conductual del Lab, Pulse, integración con almacenamiento documental externo. No se crean tablas ni rutas para estos módulos.

Criterio de éxito: el producto se puede usar en una reunión real con HiTO para login, ver el dashboard, consultar el roadmap, registrar hallazgos, crear iniciativas, registrar acuerdos y decisiones, consultar siguientes acciones y dar seguimiento a los CTAs del Lab.

## 2. Decisiones tomadas

| Tema | Decisión |
|---|---|
| Primer release | Fase 0 + Fase 1 + Lab core |
| Base de datos | Misma instancia Postgres del proyecto Railway "Atlas Consulting", base de datos propia `hitoxsyner` |
| Idioma de UI | Español, con términos clave de la metodología en inglés (Finding, Decision Log, On Track, Quick Win) |
| Leadership Lab | Módulo propio. Participantes son registros administrados por Syner, sin login |
| Visibilidad del Lab | HITO_EXECUTIVE ve solo calendario, asistencia y agregados; textos de CTAs y nombres solo SYNER_ADMIN |
| Arquitectura backend | Enfoque "brief literal": models, schemas, crud, routers, services por módulo, escritos a mano, sin generadores |
| Health y progreso | Fijados manualmente por Syner en el engagement; los contadores del dashboard sí se derivan de tablas |
| Auth | JWT en cookie httpOnly y también aceptado como Bearer; 12 h; sin refresh; sin registro público |
| Datos del frontend | Hook propio `useResource`, sin librería de cache |
| Migraciones | `alembic upgrade head` en el arranque del contenedor antes de uvicorn |
| Despliegue | Un solo servicio Docker multi-stage, patrón de Atlas-Booking |

## 3. Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy 2, Pydantic v2, Alembic, PostgreSQL, passlib[bcrypt], python-jose (JWT HS256), pytest, httpx.
- Frontend: React 18, TypeScript, Vite, React Router, Zustand, Axios, Tailwind CSS, Recharts.
- Infra: Railway, Dockerfile multi-stage (node 22 build → python 3.12-slim runtime), `railway.json` con healthcheck `/api/health`, variables de entorno para todos los secretos.

## 4. Modelo de datos

### 4.1 Tenancy

Jerarquía: Organization → Engagement → entidades. Syner y HiTO son ambas Organization. Un User pertenece a una Organization y tiene un rol global.

- SYNER_ADMIN: usuario de la organización Syner. Accede a cualquier engagement.
- HITO_EXECUTIVE y HITO_COLLABORATOR: usuarios de la organización cliente. Acceden solo a engagements cuyo `organization_id` es el de su organización.

Nada en el código menciona HiTO como constante; HiTO existe solo como datos de seed.

### 4.2 Columnas comunes

Toda entidad de engagement lleva: `id` UUID (pk), `organization_id` (fk, índice), `engagement_id` (fk, índice), `created_at`, `updated_at`, `created_by` (fk user, nullable). Sin soft-delete. Estados y tipos se modelan como enums de Postgres con los valores en inglés del brief.

### 4.3 Entidades

**Organization**: `name`, `slug` (único), `kind` (CONSULTANCY, CLIENT).

**Engagement**: `organization_id` (el cliente), `name`, `subtitle`, `status` (Active, Paused, Closed), `health` (On Track, Attention, At Risk), `progress_pct` (0–100), `executive_summary` (texto), `start_date`, `target_end_date`.

**User**: `organization_id`, `email` (único), `full_name`, `password_hash`, `role` (SYNER_ADMIN, HITO_EXECUTIVE, HITO_COLLABORATOR), `is_active`, `last_login_at`.

**Finding**: `title`, `description`, `context`, `type` (Opportunity, Risk, Gap, Finding, Quick Win, Strategic Insight), `area`, `source`, `impact` (Low, Medium, High, Critical), `severity` (Low, Medium, High, Critical), `evidence`, `recommendation`, `syner_owner_id` (fk user), `found_on` (date), `status` (New, Under Analysis, Validated, Converted to Initiative, Accepted, Closed), `initiative_id` (fk nullable; se llena al convertir).

**Initiative**: `name`, `description`, `objective`, `expected_outcome`, `hito_owner` (texto), `syner_owner_id` (fk user nullable), `area`, `priority` (Low, Medium, High, Critical), `status` (Discovery, Design, Validation, Execution, Monitoring, Completed, On Hold), `start_date`, `target_date`, `progress_pct`, `expected_impact`, `kpis` (texto), `risks` (texto), `dependencies` (texto).

**Milestone**: `name`, `description`, `phase` (Discover, Diagnose, Design, Prioritize, Execute, Measure), `due_date`, `status` (Planned, In Progress, Done, Slipped), `owner` (texto), `initiative_id` (fk nullable), `deliverable` (texto).

**Action**: `title`, `description`, `owner_user_id` (fk nullable), `owner_name` (texto, para responsables sin cuenta), `organization_side` (SYNER, CLIENT), `initiative_id` (fk nullable), `meeting_id` (fk nullable), `due_date`, `priority` (Low, Medium, High, Critical), `status` (Open, In Progress, Blocked, Completed, Cancelled), `evidence` (texto).

**Decision**: `title`, `context`, `alternatives` (texto), `syner_recommendation`, `final_decision`, `owner_name`, `participants` (texto), `decided_on` (date nullable), `impact`, `status` (Proposed, Under Review, Approved, Rejected, Deferred), `initiative_id` (fk nullable), `meeting_id` (fk nullable).

**Meeting**: `title`, `held_on` (datetime), `participants` (texto), `objective`, `summary`, `discussion` (texto), `next_steps` (texto). Decisiones y acciones derivadas son filas de Decision y Action con `meeting_id`.

**Document**: `name`, `description`, `category` (Discovery, Assessment, Strategy, Process, Technology, Data, AI, Reports, Meetings, Deliverables, Evidence), `version`, `url`, `doc_date`, `uploader_id` (fk user), `tags` (array de texto), `internal_only` (bool; si es true solo SYNER_ADMIN lo ve).

**DocumentLink**: `document_id`, `entity_type` (finding, initiative, meeting, decision, action), `entity_id`. Única por tripleta.

**Comment**: `entity_type`, `entity_id`, `author_id`, `body`.

**Activity**: `user_id`, `action` (created, updated, status_changed, converted, commented), `entity_type`, `entity_id`, `summary` (texto legible, en inglés con nombres de entidades), `changes` (JSON lista de `{field, before, after}`), `created_at`.

### 4.4 Entidades del Leadership Lab

**LabSession**: `number` (1–4), `name` (The Brain Under Pressure; Trust, Conflict & Difficult Conversations; From Silos to Flow; AI, Judgment & Collective Accountability), `theme` (DECIDIR, CONFRONTAR, ALINEAR, TRANSFORMAR), `held_on` (date nullable), `status` (Planned, Done, Cancelled), `attendance_count` (int nullable), `syner_notes` (texto; solo Syner).

**Pod**: `number`, `name`.

**Participant**: `full_name`, `area`, `title`, `pod_id` (fk nullable), `is_active`.

**Cta**: `participant_id`, `session_id`, `trigger`, `behavior`, `stakeholder`, `evidence_expected`, `due_date`, `accountability_partner`, `impact`, `status` (Committed, In Progress, Evidenced, Dropped), `evidence_notes`.

**ActionContract**: `participant_id` (único por engagement), `start_date`, `review_30_date`, `review_60_date`, `success_signal` (texto), `status` (Draft, Active, Reviewed 30, Reviewed 60, Closed).

**ActionContractCta**: `contract_id`, `cta_id`. Máximo 3 por contrato, validado en service.

## 5. Backend

### 5.1 Estructura

```
app/
  main.py            # crea la app, monta routers bajo /api, sirve frontend/dist
  database.py        # engine, SessionLocal, Base, get_db
  dependencies.py    # get_current_user, get_engagement, require_roles
  seed.py            # python -m app.seed
  core/config.py     # Settings desde env (pydantic-settings)
  core/security.py   # hash/verify password, create/decode JWT
  models/            # un archivo por entidad de la sección 4
  schemas/           # Create / Update / Read por entidad
  crud/              # acceso a datos, siempre recibe engagement_id
  routers/           # un router por módulo, prefijo /api
  services/          # reglas: conversiones, activity, dashboard, lab summary
  utils/
alembic/
tests/
frontend/
Dockerfile
railway.json
requirements.txt
.env.example
README.md
```

Responsabilidades: crud solo consulta y persiste; services aplican reglas y escriben Activity; routers validan rol, resuelven engagement y delegan. Cada función de crud que lista o busca recibe `engagement_id` como parámetro obligatorio.

### 5.2 Autenticación

- `POST /api/auth/login` con email y password. Verifica bcrypt, emite JWT HS256 con `sub` (user id), `org`, `role`, `exp` (12 h). Responde con el token en el cuerpo y además lo fija en cookie `access_token` httpOnly, Secure en producción, SameSite=Lax.
- `POST /api/auth/logout` borra la cookie.
- `GET /api/auth/me` devuelve usuario, organización y rol.
- `get_current_user` lee `Authorization: Bearer` primero y la cookie después. Usuario inactivo o token inválido → 401.
- Secreto JWT y URL de base de datos solo por variables de entorno. No hay registro público; `POST /api/engagements/{id}/users` lo usa SYNER_ADMIN.

### 5.3 Scope y RBAC

- `get_engagement(engagement_id)` carga el engagement, verifica acceso (Syner: siempre; cliente: `engagement.organization_id == user.organization_id`), de lo contrario 404 (no se revela existencia). Todos los routers de entidad dependen de esta función.
- `require_roles(*roles)` devuelve 403 si el rol no está incluido.
- Matriz:

| Acción | SYNER_ADMIN | HITO_EXECUTIVE | HITO_COLLABORATOR |
|---|---|---|---|
| Leer cualquier módulo del engagement | sí | sí | sí (documents sin `internal_only`) |
| Crear/editar findings, initiatives, milestones, meetings, documents, decisions | sí | no | no |
| Editar executive summary, health, progress | sí | no | no |
| Cambiar status de Decision a Approved/Rejected/Deferred | sí | sí | no |
| Crear actions | sí | no | no |
| Actualizar status y evidence de una Action | sí | no | solo si `owner_user_id` es el propio |
| Comentar | sí | sí | sí |
| Administrar usuarios | sí | no | no |
| Lab: sessions, participants, pods, ctas, contracts | sí | no | no |
| Lab: summary agregado | sí | sí | no |

### 5.4 API

Prefijo `/api`. Paginación con `limit` (default 50, máximo 200) y `offset`. Las respuestas de listado devuelven `{items, total}`.

- `GET /health` → `{status: "ok", database: "ok"}`; 503 si la base no responde.
- `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`.
- `GET /engagements` (los accesibles al usuario), `GET /engagements/{id}`, `PATCH /engagements/{id}` (Syner: summary, health, progress, fechas).
- `GET /engagements/{id}/users`, `POST .../users`, `PATCH .../users/{user_id}` (Syner).
- `GET /engagements/{id}/dashboard` → tiles (health, progress, active_initiatives, open_actions, decisions_required, critical_findings; este último sustituye al tile "Critical Risks" del brief porque el módulo Risks es de Fase 2 y cuenta findings con impact Critical no cerrados), executive_summary, roadmap (fases con milestones), active_initiatives, decisions_required, key_findings (impact High o Critical, no cerrados), recent_activity (últimas 15), next_milestones (próximos 5), lab (solo si hay sesiones: próxima sesión y agregados).
- `GET|POST /engagements/{id}/findings`, `GET|PATCH /findings/{fid}`, `POST /findings/{fid}/convert` → crea Initiative con nombre, descripción y área del finding, llena `finding.initiative_id`, pone status Converted to Initiative, registra Activity. Idempotente: si ya tiene `initiative_id` responde 409.
- `GET|POST /engagements/{id}/initiatives`, `GET|PATCH /initiatives/{iid}`, `GET /initiatives/{iid}/detail` → iniciativa más milestones, actions, decisions, findings origen, documents, activity.
- `GET|POST /engagements/{id}/milestones`, `PATCH /milestones/{mid}`.
- `GET|POST /engagements/{id}/actions` (filtros: status, initiative_id, owner_user_id, `mine=true`), `PATCH /actions/{aid}`.
- `GET|POST /engagements/{id}/decisions` (filtro status), `PATCH /decisions/{did}`.
- `GET|POST /engagements/{id}/meetings`, `GET /meetings/{mid}/detail` (reunión más decisions y actions con `meeting_id`), `PATCH /meetings/{mid}`, `POST /meetings/{mid}/actions` y `POST /meetings/{mid}/decisions` → crean la entidad con `meeting_id` fijado y registran Activity.
- `GET|POST /engagements/{id}/documents`, `PATCH /documents/{docid}`, `POST /documents/{docid}/links`, `DELETE /documents/{docid}/links/{link_id}`.
- `GET /engagements/{id}/activity` (filtros entity_type, entity_id).
- `GET|POST /engagements/{id}/comments?entity_type=&entity_id=`.
- Lab: `GET|POST /engagements/{id}/lab/sessions`, `PATCH /lab/sessions/{sid}`; `GET|POST .../lab/pods`, `PATCH /lab/pods/{pid}`; `GET|POST .../lab/participants`, `PATCH /lab/participants/{pid}`; `GET|POST .../lab/ctas` (filtros session_id, pod_id, status), `PATCH /lab/ctas/{cid}`; `GET|POST .../lab/contracts`, `PATCH /lab/contracts/{cid}`; `GET .../lab/summary`.

`/lab/summary` devuelve: sesiones (número, nombre, fecha, status, attendance_count), totales de CTAs por status, porcentaje de CTAs con status Evidenced, desglose por sesión y por pod (solo número y nombre del pod), contratos activos. Nunca incluye `participant`, `trigger`, `behavior` ni texto libre.

### 5.5 Activity trail

Los services escriben Activity en: creación de cualquier entidad, cambio de `status`, conversión de finding, creación de action o decision desde reunión, comentario. El `summary` se construye como `"{user.full_name} {verbo} {EntityType} \"{title}\"{detalle}"`, por ejemplo `Syner updated Initiative "Automatización de conciliación" from Discovery to Design`. `changes` guarda solo campos que cambiaron.

### 5.6 Errores, validación y rate limit

- Pydantic v2 valida entradas; longitudes máximas en títulos (200) y textos (10 000).
- Errores con envelope `{"detail": "..."}` para 401, 403, 404, 409, 422, 500. Los 500 se registran con logging y no exponen trazas.
- Middleware de rate limit en memoria por IP, activable con `RATE_LIMIT_ENABLED=true`; desactivado por defecto.
- CORS solo si `CORS_ORIGINS` está definido (desarrollo local con Vite).

### 5.7 Migraciones y seed

- Alembic con `env.py` leyendo `DATABASE_URL`. Una migración inicial para todo el primer release, autogenerada y revisada a mano.
- `python -m app.seed`: idempotente por `slug` y `email`. Crea organización Syner (CONSULTANCY), organización HiTO (CLIENT), engagement "Syner × HiTO Transformation Program", un usuario por rol con passwords desde `SEED_SYNER_PASSWORD`, `SEED_EXEC_PASSWORD`, `SEED_COLLAB_PASSWORD`, y datos demo con prefijo `[Demo]`: 5 findings, 4 initiatives, 8 actions, 3 decisions, 3 meetings, 5 documents, 6 milestones, 4 sesiones de Lab, 4 pods, 20 participantes ficticios y 8 CTAs. Ningún dato describe la operación real de HiTO.

## 6. Frontend

### 6.1 Estructura

```
frontend/src/
  api/          # client.ts (axios, baseURL /api, withCredentials, header X-Engagement-Id), un archivo por recurso
  stores/       # auth.ts (user, login, logout), engagement.ts (engagement activo, lista)
  hooks/        # useResource.ts (loading, error, data, refetch)
  components/   # AppShell, Sidebar, Header, DataTable, StatusBadge, FormDrawer, EmptyState, PageHeader, Tile
  pages/        # login, dashboard, findings, initiatives, roadmap, actions, decisions, meetings, documents, lab
  lib/          # labels.ts (enum → etiqueta), dates.ts, roles.ts
  App.tsx, main.tsx, router.tsx
```

### 6.2 Navegación

Rutas: `/login`, `/`, `/findings`, `/initiatives`, `/initiatives/:id`, `/roadmap`, `/actions`, `/actions/mine`, `/decisions`, `/meetings`, `/meetings/:id`, `/documents`, `/lab`. Rutas protegidas redirigen a `/login` sin sesión. Sidebar: Overview, Findings, Initiatives, Roadmap, Actions, Decisions, Meetings, Documents, Leadership Lab. Header: selector de engagement, búsqueda deshabilitada con tooltip "Próximamente", placeholder de notificaciones, menú de usuario con logout. En anchos menores a 1024 px el sidebar se convierte en drawer.

### 6.3 Patrón de página

Cada módulo: PageHeader con título y botón de crear (si el rol puede), filtros simples, DataTable con StatusBadge, FormDrawer lateral para crear y editar. Vistas de detalle para Initiative (mission control: header, objective, expected outcome, milestones, actions, decisions, findings, documents, activity) y Meeting (discussion, decisions, action items, next steps, botones "Registrar decisión" y "Registrar acción"). En Findings, botón "Convertir a Initiative" visible si no está convertido.

### 6.4 Dashboard

Orden: encabezado "SYNER × HiTO / Transformation Program"; seis tiles (Engagement Health, Progress, Active Initiatives, Open Actions, Decisions Required, Critical Findings); Executive Summary editable inline por Syner; Transformation Roadmap como barra de seis fases con milestones y estado; Active Initiatives con barra de progreso; Decisions Required destacado; Key Findings; Recent Activity; Next Milestones; tarjeta Leadership Lab con próxima sesión y porcentaje de CTAs con evidencia. Un solo request a `/dashboard`. Legible en móvil apilando tiles en dos columnas.

### 6.5 Idioma y estilo

Textos de UI en español; términos de la metodología en inglés desde `lib/labels.ts`. Estilo: fondo blanco, grises suaves, tipografía Inter, acento verde sobrio solo para señales de estado positivo, líneas de 1 px, cards sin sombras fuertes, números grandes en tiles. Sin gradientes, glassmorphism ni iconografía decorativa. Login: "SYNER × HiTO", "Transformation Room", email, password, botón "Sign in", texto "Private advisory workspace".

### 6.6 Roles en UI

`lib/roles.ts` expone `can(user, action)` usado solo para ocultar botones. El backend es la autoridad; un 403 se muestra como mensaje neutro "No tienes permisos para esta acción".

## 7. Módulo Leadership Lab (UI)

Página `/lab`:

- SYNER_ADMIN: pestañas Sessions (tabla de 4 sesiones con fecha, status, asistencia, notas), Participants & Pods (tabla de participantes con pod asignable; lista de pods), CTA Tracker (tabla filtrable por sesión, pod y status; drawer con los siete campos del CTA más status y evidencia), Contracts (uno por participante, selección de hasta 3 CTAs, fechas +30 y +60, señal de éxito).
- HITO_EXECUTIVE: solo vista de resumen con tiles (sesiones realizadas, CTAs activos, porcentaje con evidencia, contratos activos) y una barra por sesión con CTAs por status. Sin nombres ni textos.
- HITO_COLLABORATOR: no ve el módulo en el sidebar; el backend responde 403.

El material de Project ORION no se modela: los PDFs se registran como Documents con categoría Deliverables e `internal_only=true`.

## 8. Testing

- pytest con base Postgres de prueba definida por `TEST_DATABASE_URL`; esquema creado desde los modelos al inicio de la sesión y limpiado por tabla entre tests.
- Fixtures: dos organizaciones cliente (A y B) cada una con engagement y usuarios de cada rol, más un SYNER_ADMIN.
- Cobertura mínima obligatoria:
  - login correcto, password incorrecto, usuario inactivo;
  - para cada endpoint de listado del primer release, un test parametrizado que verifica que un usuario de A no ve filas de B y que B no puede leer el engagement de A (404);
  - un test de creación por módulo que verifica 403 para HITO_COLLABORATOR y HITO_EXECUTIVE, más dos positivos: HITO_EXECUTIVE puede aprobar una decision y HITO_COLLABORATOR puede actualizar una action propia;
  - conversión Finding → Initiative y su 409 al repetir;
  - creación de action y decision desde reunión con `meeting_id`;
  - HITO_COLLABORATOR solo puede actualizar actions propias;
  - `/lab/summary` no contiene claves `participant`, `trigger`, `behavior`, `full_name`;
  - `/health` responde 200.
- Frontend: `npm run build` y `tsc --noEmit` deben pasar; sin tests de componentes en el primer release.

## 9. Despliegue

- Dockerfile y `railway.json` siguen el patrón de Atlas-Booking: build del frontend con node 22, runtime python 3.12-slim, `CMD` que ejecuta `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- FastAPI sirve `frontend/dist` en `/` con fallback a `index.html` para rutas del router; `/api/*` tiene prioridad.
- Servicio Railway `HiTOxSyner` dentro del proyecto "Atlas Consulting". Variables: `DATABASE_URL` (base `hitoxsyner` en el Postgres existente), `JWT_SECRET`, `JWT_EXPIRE_HOURS`, `ENV`, `SEED_*_PASSWORD`, `RATE_LIMIT_ENABLED`, `CORS_ORIGINS`.
- La base `hitoxsyner` se crea una vez con `CREATE DATABASE` sobre el Postgres de Atlas Consulting; Atlas-Booking no se toca.
- README: desarrollo local (Postgres local o Railway, `.env`, `alembic upgrade head`, `python -m app.seed`, `uvicorn`, `npm run dev` con proxy a `/api`), tests, build y deploy.

## 10. Definition of Done del primer release

- Desplegado en Railway con la base `hitoxsyner` y `/api/health` en verde.
- Login funcional con los tres roles del seed.
- Aislamiento por organización verificado por tests.
- Dashboard operativo con datos del seed.
- CRUD de findings, initiatives, milestones, actions, decisions, meetings, documents y módulo Lab core.
- Conversión finding → initiative y acuerdos de reunión → actions y decisions.
- Activity trail visible en dashboard y en detalle de iniciativa.
- Responsive básico; dashboard legible en teléfono.
- Seed idempotente, `.env.example`, README, migración reproducible, tests backend en verde, build frontend en verde.

## 11. Preparación para fases siguientes

Sin construir nada extra, el diseño deja: IDs UUID estables, timestamps, `organization_id` y `engagement_id` en todo, relaciones explícitas por fk, `DocumentLink` y `Comment` genéricos, Activity con cambios estructurados, y rutas `/api` documentadas por OpenAPI. Esto es lo que el brief pide para Syner Cortex y búsqueda futura.
