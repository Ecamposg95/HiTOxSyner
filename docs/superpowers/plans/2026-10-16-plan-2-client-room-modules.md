# Transformation Room — Plan 2: Client Room (milestones, meetings, decisions, comments, documents)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Completar la Fase 1 (client room MVP) sobre la base del plan 1: roadmap con milestones, meetings con acuerdos que se convierten en actions y decisions, decision log con aprobación ejecutiva, documents con vínculos a entidades, comments, y su reflejo en dashboard, initiative detail y meeting detail; desplegado en Railway.

**Architecture:** Mismo servicio único FastAPI + React del plan 1. Por cada módulo nuevo un archivo en `app/models/`, `app/schemas/`, `app/crud/`, `app/services/`, `app/routers/` escrito a mano. Toda consulta recibe `engagement_id`; el acceso se resuelve con `get_engagement` y `scoped(Model, param)` de `app/dependencies.py`; los services escriben el activity trail con `log_activity`/`diff_changes` de `app/services/activity.py`. Una sola migración Alembic nueva para todas las tablas del plan. Frontend: un archivo en `frontend/src/api/` por recurso, páginas con el patrón `PageHeader + filtros + DataTable + FormDrawer` del plan 1.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2, Pydantic v2, Alembic, PostgreSQL, pytest + httpx. React 18, TypeScript, Vite 5, React Router 6, Zustand 4, Axios, Tailwind 3. Railway + Docker multi-stage.

**Spec:** `docs/superpowers/specs/2026-10-11-transformation-room-design.md` (secciones 4.3, 5.3, 5.4, 5.5, 6.2–6.4, 8). Plan anterior: `docs/superpowers/plans/2026-10-12-plan-1-foundation-vertical-slice.md` (ya mergeado; el código del plan 1 es la base de este plan).

Este es el plan 2 de 3. Plan 3 cubre el módulo Leadership Lab, el registro de los PDFs de ORION como Documents internos y el cierre del Definition of Done.

## Global Constraints

- Rama de trabajo: `feat/plan-2-client-room`, creada desde `docs/material-hito-syner` (rama default del remoto; no existe `main`). Al terminar se abre PR contra `docs/material-hito-syner`.
- Entorno: `.venv/bin/python`, `.venv/bin/pytest`, `.venv/bin/alembic` (venv ya creada). Postgres 16 local en espacio de usuario: si `~/.local/pg/bin/pg_isready -h localhost` falla, arrancar con `~/.local/pg/bin/pg_ctl -D ~/.local/pgdata -l ~/.local/pgdata/server.log -o "-p 5432 -k /tmp" start`. Bases `hitoxsyner_dev` (Alembic, seed, uvicorn) y `hitoxsyner_test` (pytest, esquema desde `Base.metadata.create_all`). `.env` ya existe y no se commitea.
- Postgres es la única base soportada (UUID, enums nativos, ARRAY). No hay SQLite ni en tests.
- Todos los endpoints viven bajo `/api`. Listados paginados devuelven `{"items": [...], "total": n}` con `limit` default 50, máximo 200, `offset` default 0, usando `Page`, `Pagination`, `pagination_params` de `app/schemas/common.py`.
- Un PATCH con `null` explícito en un campo que no admite null responde 422 vía `updates(data, nullable=...)` de `app/schemas/common.py` (nunca 500).
- Referencias cruzadas (`initiative_id`, `meeting_id`, `entity_id` de links y comments) que apuntan a una entidad de otro engagement responden 422 con `{"detail": "..."}`; nunca se revela la existencia de la entidad ajena con un 404 distinto.
- Errores siempre con envelope `{"detail": "..."}`; los 500 no exponen trazas.
- Nada en el código menciona HiTO como constante salvo los nombres de rol (`SYNER_ADMIN`, `HITO_EXECUTIVE`, `HITO_COLLABORATOR`) y el seed.
- Valores de enums exactamente como el brief. Nuevos en este plan: milestone phase `Discover`, `Diagnose`, `Design`, `Prioritize`, `Execute`, `Measure` (reutiliza `RoadmapPhase` de `app/models/enums.py`); milestone status `Planned`, `In Progress`, `Done`, `Slipped`; decision status `Proposed`, `Under Review`, `Approved`, `Rejected`, `Deferred`; document category `Discovery`, `Assessment`, `Strategy`, `Process`, `Technology`, `Data`, `AI`, `Reports`, `Meetings`, `Deliverables`, `Evidence`.
- Cada columna enum usa un tipo de Postgres con nombre propio `<tabla>_<columna>` vía `db_enum(EnumCls, "nombre")` de `app/models/base.py` (nunca compartir un tipo entre columnas). Los nombres nuevos: `milestone_phase`, `milestone_status`, `decision_status`, `document_category`. La migración los elimina en `downgrade()`.
- Longitudes: títulos y nombres 200, textos largos 10 000, `url` 2 000, `version` 50, cada tag 50 y máximo 20 tags.
- Activity trail: los services escriben Activity en creación, cambio de `status`, creación de action/decision desde meeting, vínculo de documento y comentario. `summary` sigue el formato `{user.full_name} {verbo} {EntityType} "{title}"{detalle}` en inglés.
- RBAC (spec 5.3): SYNER_ADMIN escribe todo; HITO_EXECUTIVE solo puede cambiar el `status` de una Decision a `Approved`, `Rejected` o `Deferred` y comentar; HITO_COLLABORATOR solo comenta (y sus actions propias, ya implementado). HITO_COLLABORATOR nunca ve documents con `internal_only=true` (ni en listados, ni por id, ni en initiative detail).
- UI en español; nombres de módulos, estados y términos de la metodología en inglés. `can(user, "write")` de `frontend/src/lib/roles.ts` solo oculta botones; el backend es la autoridad.
- Sin soft-delete (excepto `DELETE` de un DocumentLink, que es un vínculo, no una entidad). Commits pequeños por tarea. Mensajes de commit terminan con la línea de atribución indicada por la sesión.

## Review Focus

1. HITO_EXECUTIVE hace PATCH a una decision con `{"status": "Approved", "title": "Otro"}`: 403 y la decision no cambia (ni siquiera el status). (Test en Task 3.)
2. HITO_COLLABORATOR pide `GET /api/documents/{id}` de un documento `internal_only`: 404, y ese documento tampoco aparece en `GET /initiatives/{id}/detail` aunque esté vinculado. (Test en Task 5.)
3. `POST /engagements/{A}/comments` con `entity_id` de una initiative que existe pero pertenece al engagement B: 422, sin crear comentario ni activity. (Test en Task 4.)
4. `POST /engagements/{A}/milestones` con `initiative_id` de B: 422; y PATCH del milestone con ese `initiative_id`: 422. (Test en Task 1.)
5. `DELETE /documents/{doc1}/links/{link}` donde `link` pertenece a `doc2`: 404 y el vínculo sigue existiendo. (Test en Task 5.)

---

### Task 0: Rama de trabajo y verificación del punto de partida

**Files:** ninguno.

- [ ] **Step 1: Crear la rama desde la rama default**

```bash
cd /mnt/d/Devs/HiTOxSyner
git checkout docs/material-hito-syner && git pull --ff-only
git checkout -b feat/plan-2-client-room
```

- [ ] **Step 2: Verificar Postgres, Alembic y la suite del plan 1**

```bash
cd /mnt/d/Devs/HiTOxSyner
~/.local/pg/bin/pg_isready -h localhost || ~/.local/pg/bin/pg_ctl -D ~/.local/pgdata -l ~/.local/pgdata/server.log -o "-p 5432 -k /tmp" start
.venv/bin/alembic current
.venv/bin/pytest -q
```
Expected: `localhost:5432 - accepting connections`, `abb020e368aa (head)`, `65 passed`. Si Alembic no está en head: `.venv/bin/alembic upgrade head`.

---

### Task 1: Milestones (roadmap) + reflejo en dashboard e initiative detail

**Files:**
- Modify: `app/models/enums.py`, `app/models/__init__.py`, `app/main.py`, `app/schemas/dashboard.py`, `app/services/dashboard.py`, `app/schemas/initiative.py`, `app/routers/initiatives.py`
- Create: `app/models/milestone.py`, `app/schemas/milestone.py`, `app/crud/milestones.py`, `app/services/milestones.py`, `app/routers/milestones.py`
- Test: `tests/test_milestones.py`

**Interfaces:**
- Consumes: `EngagementScopedMixin`, `db_enum` (`app/models/base.py`); `RoadmapPhase` (`app/models/enums.py`); `get_engagement`, `require_roles`, `scoped` (`app/dependencies.py`); `updates`, `Page`, `Pagination`, `pagination_params` (`app/schemas/common.py`); `log_activity`, `diff_changes` (`app/services/activity.py`).
- Produces: `MilestoneStatus` enum; modelo `Milestone`; `MilestoneCreate`, `MilestoneUpdate`, `MilestoneRead`; `milestones_crud.list_for_engagement(db, engagement_id, *, phase=None, status=None, initiative_id=None, limit=50, offset=0) -> tuple[list[Milestone], int]`, `milestones_crud.list_all(db, engagement_id) -> list[Milestone]`, `milestones_crud.upcoming(db, engagement_id, limit=5) -> list[Milestone]`, `milestones_crud.list_by_initiative(db, initiative_id) -> list[Milestone]`; `milestones_service.create_milestone(db, *, user, engagement, data)`, `milestones_service.update_milestone(db, *, user, milestone, data)`; `RoadmapPhaseRead.milestones: list[MilestoneRead]`; `DashboardRead.next_milestones: list[MilestoneRead]`; `InitiativeDetail.milestones: list[MilestoneRead]`.

- [ ] **Step 1: Escribir los tests (fallan porque no existe el módulo)**

`tests/test_milestones.py`:

```python
from datetime import date, timedelta

from tests.factories import login

MILESTONE = {"name": "Diagnóstico consolidado", "phase": "Diagnose", "due_date": "2026-11-15", "owner": "Equipo Syner", "deliverable": "Informe de diagnóstico"}


def _admin_and_initiative(client, world):
    admin = login(client, "admin@syner.example")
    initiative = client.post(f"/api/engagements/{world.eng_a.id}/initiatives", headers=admin, json={"name": "Automatización"}).json()
    return admin, initiative


def test_syner_creates_milestone_with_defaults_and_logs_activity(client, world):
    admin = login(client, "admin@syner.example")
    response = client.post(f"/api/engagements/{world.eng_a.id}/milestones", headers=admin, json=MILESTONE)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "Planned"
    assert body["phase"] == "Diagnose"
    assert body["initiative_id"] is None
    assert body["engagement_id"] == str(world.eng_a.id)
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["summary"] == 'Syner Admin created Milestone "Diagnóstico consolidado"'


def test_client_roles_cannot_write_milestones(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/milestones", headers=admin, json=MILESTONE).json()
    for email in ("exec@a.example", "collab@a.example"):
        headers = login(client, email)
        assert client.post(f"/api/engagements/{world.eng_a.id}/milestones", headers=headers, json=MILESTONE).status_code == 403
        assert client.patch(f"/api/milestones/{created['id']}", headers=headers, json={"status": "Done"}).status_code == 403
        assert client.get(f"/api/engagements/{world.eng_a.id}/milestones", headers=headers).json()["total"] == 1


def test_milestones_isolated_by_organization(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/milestones", headers=admin, json=MILESTONE).json()
    client.post(f"/api/engagements/{world.eng_b.id}/milestones", headers=admin, json={**MILESTONE, "name": "De B"})
    listing = client.get(f"/api/engagements/{world.eng_a.id}/milestones", headers=login(client, "exec@a.example")).json()
    assert listing["total"] == 1 and listing["items"][0]["name"] == MILESTONE["name"]
    assert client.get(f"/api/milestones/{created['id']}", headers=login(client, "exec@b.example")).status_code == 404
    assert client.get(f"/api/engagements/{world.eng_a.id}/milestones", headers=login(client, "collab@b.example")).status_code == 404


def test_initiative_must_belong_to_engagement(client, world):
    admin = login(client, "admin@syner.example")
    other = client.post(f"/api/engagements/{world.eng_b.id}/initiatives", headers=admin, json={"name": "De B"}).json()
    base = f"/api/engagements/{world.eng_a.id}/milestones"
    assert client.post(base, headers=admin, json={**MILESTONE, "initiative_id": other["id"]}).status_code == 422
    created = client.post(base, headers=admin, json=MILESTONE).json()
    assert client.patch(f"/api/milestones/{created['id']}", headers=admin, json={"initiative_id": other["id"]}).status_code == 422
    assert client.get(f"/api/milestones/{created['id']}", headers=admin).json()["initiative_id"] is None


def test_status_change_logs_before_and_after_and_null_rules(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/milestones", headers=admin, json=MILESTONE).json()
    response = client.patch(f"/api/milestones/{created['id']}", headers=admin, json={"status": "In Progress"})
    assert response.status_code == 200 and response.json()["status"] == "In Progress"
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["action"] == "status_changed"
    assert activity["summary"] == 'Syner Admin updated Milestone "Diagnóstico consolidado" from Planned to In Progress'
    assert client.patch(f"/api/milestones/{created['id']}", headers=admin, json={"name": None}).status_code == 422
    cleared = client.patch(f"/api/milestones/{created['id']}", headers=admin, json={"due_date": None})
    assert cleared.status_code == 200 and cleared.json()["due_date"] is None


def test_list_filters_by_phase_status_and_initiative(client, world):
    admin, initiative = _admin_and_initiative(client, world)
    base = f"/api/engagements/{world.eng_a.id}/milestones"
    client.post(base, headers=admin, json=MILESTONE)
    client.post(base, headers=admin, json={**MILESTONE, "name": "Piloto", "phase": "Execute", "status": "Done", "initiative_id": initiative["id"]})
    assert client.get(base, headers=admin, params={"phase": "Execute"}).json()["total"] == 1
    assert client.get(base, headers=admin, params={"status": "Planned"}).json()["items"][0]["name"] == MILESTONE["name"]
    assert client.get(base, headers=admin, params={"initiative_id": initiative["id"]}).json()["items"][0]["name"] == "Piloto"


def test_dashboard_roadmap_groups_by_phase_and_next_milestones_skip_done(client, world):
    admin = login(client, "admin@syner.example")
    base = f"/api/engagements/{world.eng_a.id}/milestones"
    today = date.today()
    client.post(base, headers=admin, json={"name": "Lejano", "phase": "Execute", "due_date": (today + timedelta(days=40)).isoformat()})
    client.post(base, headers=admin, json={"name": "Cercano", "phase": "Diagnose", "due_date": (today + timedelta(days=5)).isoformat()})
    client.post(base, headers=admin, json={"name": "Hecho", "phase": "Discover", "due_date": (today - timedelta(days=5)).isoformat(), "status": "Done"})
    client.post(base, headers=admin, json={"name": "Sin fecha", "phase": "Measure"})
    body = client.get(f"/api/engagements/{world.eng_a.id}/dashboard", headers=login(client, "exec@a.example")).json()
    phases = {p["phase"]: [m["name"] for m in p["milestones"]] for p in body["roadmap"]}
    assert list(phases) == ["Discover", "Diagnose", "Design", "Prioritize", "Execute", "Measure"]
    assert phases["Discover"] == ["Hecho"] and phases["Diagnose"] == ["Cercano"] and phases["Measure"] == ["Sin fecha"]
    assert [m["name"] for m in body["next_milestones"]] == ["Cercano", "Lejano"]


def test_initiative_detail_includes_milestones(client, world):
    admin, initiative = _admin_and_initiative(client, world)
    client.post(f"/api/engagements/{world.eng_a.id}/milestones", headers=admin, json={**MILESTONE, "initiative_id": initiative["id"]})
    client.post(f"/api/engagements/{world.eng_a.id}/milestones", headers=admin, json={**MILESTONE, "name": "Suelto"})
    detail = client.get(f"/api/initiatives/{initiative['id']}/detail", headers=login(client, "collab@a.example")).json()
    assert [m["name"] for m in detail["milestones"]] == [MILESTONE["name"]]
```

- [ ] **Step 2: Correr los tests para ver que fallan**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest tests/test_milestones.py -q 2>&1 | tail -3`
Expected: fallos por 404 en `/milestones` o `KeyError: 'milestones'` (la ruta no existe todavía).

- [ ] **Step 3: Enum, modelo y registro**

Añadir al final de `app/models/enums.py`:

```python
class MilestoneStatus(str, enum.Enum):
    PLANNED = "Planned"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    SLIPPED = "Slipped"
```

`app/models/milestone.py`:

```python
import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import EngagementScopedMixin, db_enum
from app.models.enums import MilestoneStatus, RoadmapPhase


class Milestone(EngagementScopedMixin, Base):
    __tablename__ = "milestones"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    phase: Mapped[RoadmapPhase] = mapped_column(db_enum(RoadmapPhase, "milestone_phase"), default=RoadmapPhase.DISCOVER, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[MilestoneStatus] = mapped_column(
        db_enum(MilestoneStatus, "milestone_status"), default=MilestoneStatus.PLANNED, nullable=False
    )
    owner: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    initiative_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("initiatives.id"), index=True, nullable=True)
    deliverable: Mapped[str] = mapped_column(Text, default="", nullable=False)
```

`app/models/__init__.py` completo (se irá ampliando en tareas siguientes; aquí la versión de esta tarea):

```python
from app.models.activity import Activity
from app.models.action import Action
from app.models.engagement import Engagement
from app.models.initiative import Initiative
from app.models.finding import Finding
from app.models.milestone import Milestone
from app.models.organization import Organization
from app.models.user import User

__all__ = ["Action", "Activity", "Engagement", "Finding", "Initiative", "Milestone", "Organization", "User"]
```

- [ ] **Step 4: Schemas**

`app/schemas/milestone.py`:

```python
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MilestoneStatus, RoadmapPhase


class MilestoneCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10000)
    phase: RoadmapPhase = RoadmapPhase.DISCOVER
    due_date: date | None = None
    status: MilestoneStatus = MilestoneStatus.PLANNED
    owner: str = Field(default="", max_length=200)
    initiative_id: uuid.UUID | None = None
    deliverable: str = Field(default="", max_length=10000)


class MilestoneUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    phase: RoadmapPhase | None = None
    due_date: date | None = None
    status: MilestoneStatus | None = None
    owner: str | None = Field(default=None, max_length=200)
    initiative_id: uuid.UUID | None = None
    deliverable: str | None = Field(default=None, max_length=10000)


class MilestoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    engagement_id: uuid.UUID
    name: str
    description: str
    phase: RoadmapPhase
    due_date: date | None
    status: MilestoneStatus
    owner: str
    initiative_id: uuid.UUID | None
    deliverable: str
    created_at: datetime
    updated_at: datetime
```

- [ ] **Step 5: CRUD**

`app/crud/milestones.py`:

```python
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import MilestoneStatus, RoadmapPhase
from app.models.milestone import Milestone


def list_for_engagement(
    db: Session, engagement_id: uuid.UUID, *, phase: RoadmapPhase | None = None,
    status: MilestoneStatus | None = None, initiative_id: uuid.UUID | None = None,
    limit: int = 50, offset: int = 0,
) -> tuple[list[Milestone], int]:
    query = select(Milestone).where(Milestone.engagement_id == engagement_id)
    if phase:
        query = query.where(Milestone.phase == phase)
    if status:
        query = query.where(Milestone.status == status)
    if initiative_id:
        query = query.where(Milestone.initiative_id == initiative_id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Milestone.due_date.nulls_last(), Milestone.created_at).limit(limit).offset(offset)))
    return items, total


def list_all(db: Session, engagement_id: uuid.UUID) -> list[Milestone]:
    query = select(Milestone).where(Milestone.engagement_id == engagement_id).order_by(Milestone.due_date.nulls_last(), Milestone.created_at)
    return list(db.scalars(query))


def upcoming(db: Session, engagement_id: uuid.UUID, limit: int = 5) -> list[Milestone]:
    query = (
        select(Milestone)
        .where(Milestone.engagement_id == engagement_id)
        .where(Milestone.status != MilestoneStatus.DONE)
        .where(Milestone.due_date.is_not(None))
        .order_by(Milestone.due_date, Milestone.created_at)
        .limit(limit)
    )
    return list(db.scalars(query))


def list_by_initiative(db: Session, initiative_id: uuid.UUID) -> list[Milestone]:
    query = select(Milestone).where(Milestone.initiative_id == initiative_id).order_by(Milestone.due_date.nulls_last(), Milestone.created_at)
    return list(db.scalars(query))
```

- [ ] **Step 6: Service**

`app/services/milestones.py`:

```python
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.engagement import Engagement
from app.models.enums import ActivityAction
from app.models.initiative import Initiative
from app.models.milestone import Milestone
from app.models.user import User
from app.schemas.common import updates
from app.schemas.milestone import MilestoneCreate, MilestoneUpdate
from app.services.activity import diff_changes, log_activity


def validate_initiative(db: Session, engagement: Engagement, initiative_id) -> None:
    if initiative_id is None:
        return
    initiative = db.get(Initiative, initiative_id)
    if initiative is None or initiative.engagement_id != engagement.id:
        raise HTTPException(status_code=422, detail="initiative_id no pertenece a este engagement")


def create_milestone(db: Session, *, user: User, engagement: Engagement, data: MilestoneCreate) -> Milestone:
    validate_initiative(db, engagement, data.initiative_id)
    milestone = Milestone(organization_id=engagement.organization_id, engagement_id=engagement.id, created_by=user.id, **data.model_dump())
    db.add(milestone)
    db.flush()
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="milestone",
        entity_id=milestone.id, summary=f'{user.full_name} created Milestone "{milestone.name}"',
    )
    db.commit()
    db.refresh(milestone)
    return milestone


def update_milestone(db: Session, *, user: User, milestone: Milestone, data: MilestoneUpdate) -> Milestone:
    payload = updates(data, nullable={"due_date", "initiative_id"})
    engagement = db.get(Engagement, milestone.engagement_id)
    validate_initiative(db, engagement, payload.get("initiative_id"))
    changes = diff_changes(milestone, payload)
    if not changes:
        return milestone
    for field, value in payload.items():
        setattr(milestone, field, value)
    status_change = next((c for c in changes if c["field"] == "status"), None)
    if status_change:
        action = ActivityAction.STATUS_CHANGED
        summary = f'{user.full_name} updated Milestone "{milestone.name}" from {status_change["before"]} to {status_change["after"]}'
    else:
        action = ActivityAction.UPDATED
        summary = f'{user.full_name} updated Milestone "{milestone.name}"'
    log_activity(
        db, user=user, engagement=engagement, action=action, entity_type="milestone",
        entity_id=milestone.id, summary=summary, changes=changes,
    )
    db.commit()
    db.refresh(milestone)
    return milestone
```

- [ ] **Step 7: Router y registro en `main.py`**

`app/routers/milestones.py`:

```python
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import milestones as milestones_crud
from app.database import get_db
from app.dependencies import get_engagement, require_roles, scoped
from app.models.engagement import Engagement
from app.models.enums import MilestoneStatus, RoadmapPhase, Role
from app.models.milestone import Milestone
from app.models.user import User
from app.schemas.common import Page, Pagination, pagination_params
from app.schemas.milestone import MilestoneCreate, MilestoneRead, MilestoneUpdate
from app.services import milestones as milestones_service

router = APIRouter(tags=["milestones"])
syner_only = Depends(require_roles(Role.SYNER_ADMIN))
scoped_milestone = Depends(scoped(Milestone, "milestone_id"))


@router.get("/engagements/{engagement_id}/milestones", response_model=Page[MilestoneRead])
def list_milestones(
    engagement: Engagement = Depends(get_engagement),
    phase: RoadmapPhase | None = None,
    status: MilestoneStatus | None = None,
    initiative_id: uuid.UUID | None = None,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = milestones_crud.list_for_engagement(
        db, engagement.id, phase=phase, status=status, initiative_id=initiative_id,
        limit=pagination.limit, offset=pagination.offset,
    )
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/milestones", response_model=MilestoneRead, status_code=201)
def create_milestone(
    data: MilestoneCreate,
    user: User = syner_only,
    engagement: Engagement = Depends(get_engagement),
    db: Session = Depends(get_db),
):
    return milestones_service.create_milestone(db, user=user, engagement=engagement, data=data)


@router.get("/milestones/{milestone_id}", response_model=MilestoneRead)
def read_milestone(milestone: Milestone = scoped_milestone):
    return milestone


@router.patch("/milestones/{milestone_id}", response_model=MilestoneRead)
def update_milestone(
    data: MilestoneUpdate,
    user: User = syner_only,
    milestone: Milestone = scoped_milestone,
    db: Session = Depends(get_db),
):
    return milestones_service.update_milestone(db, user=user, milestone=milestone, data=data)
```

En `app/main.py`, cambiar el import de routers y añadir el include:

```python
from app.routers import actions, activity, auth, dashboard, engagements, findings, health, initiatives, milestones
```

y después de `app.include_router(actions.router, prefix="/api")`:

```python
app.include_router(milestones.router, prefix="/api")
```

- [ ] **Step 8: Dashboard e initiative detail**

`app/schemas/dashboard.py` completo:

```python
from pydantic import BaseModel

from app.models.enums import Health
from app.schemas.action import ActionRead
from app.schemas.activity import ActivityRead
from app.schemas.engagement import EngagementRead
from app.schemas.finding import FindingRead
from app.schemas.initiative import InitiativeRead
from app.schemas.milestone import MilestoneRead


class DashboardTiles(BaseModel):
    health: Health
    progress_pct: int
    active_initiatives: int
    open_actions: int
    decisions_required: int
    critical_findings: int


class RoadmapPhaseRead(BaseModel):
    phase: str
    milestones: list[MilestoneRead] = []


class DashboardRead(BaseModel):
    engagement: EngagementRead
    tiles: DashboardTiles
    active_initiatives: list[InitiativeRead]
    key_findings: list[FindingRead]
    next_actions: list[ActionRead]
    recent_activity: list[ActivityRead]
    roadmap: list[RoadmapPhaseRead]
    decisions_required: list[dict]
    next_milestones: list[MilestoneRead]
```

`app/services/dashboard.py` completo:

```python
from sqlalchemy.orm import Session

from app.crud import actions as actions_crud
from app.crud import activities as activities_crud
from app.crud import findings as findings_crud
from app.crud import initiatives as initiatives_crud
from app.crud import milestones as milestones_crud
from app.models.engagement import Engagement
from app.models.enums import RoadmapPhase
from app.schemas.action import ActionRead
from app.schemas.activity import ActivityRead
from app.schemas.dashboard import DashboardRead, DashboardTiles, RoadmapPhaseRead
from app.schemas.engagement import EngagementRead
from app.schemas.finding import FindingRead
from app.schemas.initiative import InitiativeRead
from app.schemas.milestone import MilestoneRead


def build_roadmap(db: Session, engagement: Engagement) -> list[RoadmapPhaseRead]:
    by_phase: dict[RoadmapPhase, list[MilestoneRead]] = {phase: [] for phase in RoadmapPhase}
    for milestone in milestones_crud.list_all(db, engagement.id):
        by_phase[milestone.phase].append(MilestoneRead.model_validate(milestone))
    return [RoadmapPhaseRead(phase=phase.value, milestones=items) for phase, items in by_phase.items()]


def build_dashboard(db: Session, engagement: Engagement) -> DashboardRead:
    tiles = DashboardTiles(
        health=engagement.health,
        progress_pct=engagement.progress_pct,
        active_initiatives=initiatives_crud.count_active(db, engagement.id),
        open_actions=actions_crud.count_open(db, engagement.id),
        decisions_required=0,
        critical_findings=findings_crud.count_critical_open(db, engagement.id),
    )
    return DashboardRead(
        engagement=EngagementRead.model_validate(engagement),
        tiles=tiles,
        active_initiatives=[InitiativeRead.model_validate(i) for i in initiatives_crud.active(db, engagement.id)],
        key_findings=[FindingRead.model_validate(f) for f in findings_crud.key_findings(db, engagement.id)],
        next_actions=[ActionRead.model_validate(a) for a in actions_crud.next_open(db, engagement.id)],
        recent_activity=[ActivityRead.model_validate(a) for a in activities_crud.recent(db, engagement.id, limit=15)],
        roadmap=build_roadmap(db, engagement),
        decisions_required=[],
        next_milestones=[MilestoneRead.model_validate(m) for m in milestones_crud.upcoming(db, engagement.id)],
    )
```

En `app/schemas/initiative.py`, añadir el import `from app.schemas.milestone import MilestoneRead` y dejar `InitiativeDetail` así:

```python
class InitiativeDetail(BaseModel):
    initiative: InitiativeRead
    findings: list[FindingRead]
    milestones: list[MilestoneRead]
    actions: list[ActionRead]
    activity: list[ActivityRead]
```

En `app/routers/initiatives.py`, añadir `from app.crud import milestones as milestones_crud` y `from app.schemas.milestone import MilestoneRead`, y reemplazar `initiative_detail` por:

```python
@router.get("/initiatives/{initiative_id}/detail", response_model=InitiativeDetail)
def initiative_detail(initiative: Initiative = scoped_initiative, db: Session = Depends(get_db)):
    findings = findings_crud.list_by_initiative(db, initiative.id)
    milestones = milestones_crud.list_by_initiative(db, initiative.id)
    actions = actions_crud.list_by_initiative(db, initiative.id)
    own_activity, _ = activities_crud.list_for_engagement(
        db, initiative.engagement_id, entity_type="initiative", entity_id=initiative.id, limit=20
    )
    finding_activity = []
    for finding in findings:
        items, _ = activities_crud.list_for_engagement(
            db, initiative.engagement_id, entity_type="finding", entity_id=finding.id, limit=5
        )
        finding_activity.extend(items)
    activity = sorted(own_activity + finding_activity, key=lambda a: a.created_at, reverse=True)[:20]
    return InitiativeDetail(
        initiative=InitiativeRead.model_validate(initiative),
        findings=[FindingRead.model_validate(f) for f in findings],
        milestones=[MilestoneRead.model_validate(m) for m in milestones],
        actions=[ActionRead.model_validate(a) for a in actions],
        activity=[ActivityRead.model_validate(a) for a in activity],
    )
```

- [ ] **Step 9: Correr toda la suite**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest -q 2>&1 | tail -3`
Expected: `73 passed` (65 anteriores + 8 nuevos). `tests/test_dashboard.py` sigue pasando porque `next_milestones == []` sin milestones y `roadmap` conserva las seis fases.

- [ ] **Step 10: Commit**

```bash
cd /mnt/d/Devs/HiTOxSyner
git add app tests/test_milestones.py
git commit -m "feat: milestones con roadmap por fase en dashboard e initiative detail"
```

---

### Task 2: Meetings y `Action.meeting_id` (acuerdos de reunión → actions)

**Files:**
- Modify: `app/models/action.py`, `app/schemas/action.py`, `app/crud/actions.py`, `app/services/actions.py`, `app/models/__init__.py`, `app/main.py`
- Create: `app/models/meeting.py`, `app/schemas/meeting.py`, `app/crud/meetings.py`, `app/services/meetings.py`, `app/routers/meetings.py`
- Test: `tests/test_meetings.py`

**Interfaces:**
- Consumes: lo mismo que Task 1 más `actions_service.create_action(db, *, user, engagement, data: ActionCreate)`.
- Produces: modelo `Meeting` (campos `title`, `held_on: datetime`, `participants`, `objective`, `summary`, `discussion`, `next_steps`); `MeetingCreate`, `MeetingUpdate`, `MeetingRead`; `meetings_crud.list_for_engagement(db, engagement_id, *, limit, offset)`; `meetings_service.create_meeting`, `update_meeting`; `Action.meeting_id`, `ActionCreate.meeting_id`, `ActionRead.meeting_id`; `actions_crud.list_by_meeting(db, meeting_id) -> list[Action]`; rutas `GET|POST /engagements/{id}/meetings`, `GET|PATCH /meetings/{mid}`, `POST /meetings/{mid}/actions`. `GET /meetings/{mid}/detail` y `POST /meetings/{mid}/decisions` se añaden en Task 3.

- [ ] **Step 1: Escribir los tests**

`tests/test_meetings.py`:

```python
from datetime import datetime, timezone

from tests.factories import login

MEETING = {"title": "Comité de transformación #1", "held_on": "2026-10-20T16:00:00Z", "participants": "Dirección, Syner", "objective": "Validar diagnóstico", "summary": "Se validó el diagnóstico.", "discussion": "Se discutieron prioridades.", "next_steps": "Preparar roadmap."}


def test_syner_creates_and_updates_meeting(client, world):
    admin = login(client, "admin@syner.example")
    response = client.post(f"/api/engagements/{world.eng_a.id}/meetings", headers=admin, json=MEETING)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["title"] == MEETING["title"]
    # Postgres devuelve la hora en la zona de la sesión (puede no ser UTC): comparar instantes, no texto.
    assert datetime.fromisoformat(body["held_on"]) == datetime(2026, 10, 20, 16, 0, tzinfo=timezone.utc)
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["summary"] == 'Syner Admin created Meeting "Comité de transformación #1"'
    updated = client.patch(f"/api/meetings/{body['id']}", headers=admin, json={"next_steps": "Roadmap listo."})
    assert updated.status_code == 200 and updated.json()["next_steps"] == "Roadmap listo."
    assert client.patch(f"/api/meetings/{body['id']}", headers=admin, json={"held_on": None}).status_code == 422


def test_held_on_is_required(client, world):
    admin = login(client, "admin@syner.example")
    assert client.post(f"/api/engagements/{world.eng_a.id}/meetings", headers=admin, json={"title": "Sin fecha"}).status_code == 422


def test_list_orders_by_held_on_desc(client, world):
    admin = login(client, "admin@syner.example")
    base = f"/api/engagements/{world.eng_a.id}/meetings"
    client.post(base, headers=admin, json={**MEETING, "title": "Vieja", "held_on": "2026-09-01T10:00:00Z"})
    client.post(base, headers=admin, json={**MEETING, "title": "Nueva", "held_on": "2026-10-01T10:00:00Z"})
    listing = client.get(base, headers=login(client, "collab@a.example")).json()
    assert [m["title"] for m in listing["items"]] == ["Nueva", "Vieja"]


def test_client_roles_cannot_write_meetings(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/meetings", headers=admin, json=MEETING).json()
    for email in ("exec@a.example", "collab@a.example"):
        headers = login(client, email)
        assert client.post(f"/api/engagements/{world.eng_a.id}/meetings", headers=headers, json=MEETING).status_code == 403
        assert client.patch(f"/api/meetings/{created['id']}", headers=headers, json={"summary": "x"}).status_code == 403
        assert client.post(f"/api/meetings/{created['id']}/actions", headers=headers, json={"title": "x"}).status_code == 403
        assert client.get(f"/api/meetings/{created['id']}", headers=headers).status_code == 200


def test_meetings_isolated_by_organization(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/meetings", headers=admin, json=MEETING).json()
    client.post(f"/api/engagements/{world.eng_b.id}/meetings", headers=admin, json={**MEETING, "title": "De B"})
    assert client.get(f"/api/engagements/{world.eng_a.id}/meetings", headers=login(client, "exec@a.example")).json()["total"] == 1
    assert client.get(f"/api/meetings/{created['id']}", headers=login(client, "exec@b.example")).status_code == 404
    assert client.get(f"/api/engagements/{world.eng_a.id}/meetings", headers=login(client, "collab@b.example")).status_code == 404


def test_action_created_from_meeting_carries_meeting_id_and_activity_mentions_meeting(client, world):
    admin = login(client, "admin@syner.example")
    meeting = client.post(f"/api/engagements/{world.eng_a.id}/meetings", headers=admin, json=MEETING).json()
    response = client.post(f"/api/meetings/{meeting['id']}/actions", headers=admin, json={"title": "Enviar roadmap", "owner_user_id": str(world.collab_a.id), "due_date": "2026-10-27"})
    assert response.status_code == 201, response.text
    action = response.json()
    assert action["meeting_id"] == meeting["id"]
    assert action["owner_name"] == "Collab A"
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["summary"] == 'Syner Admin created Action "Enviar roadmap" from Meeting "Comité de transformación #1"'
    listing = client.get(f"/api/engagements/{world.eng_a.id}/actions", headers=admin, params={"meeting_id": meeting["id"]}).json()
    assert listing["total"] == 1 and listing["items"][0]["id"] == action["id"]


def test_action_meeting_id_must_belong_to_engagement(client, world):
    admin = login(client, "admin@syner.example")
    other = client.post(f"/api/engagements/{world.eng_b.id}/meetings", headers=admin, json=MEETING).json()
    base = f"/api/engagements/{world.eng_a.id}/actions"
    assert client.post(base, headers=admin, json={"title": "x", "meeting_id": other["id"]}).status_code == 422
    created = client.post(base, headers=admin, json={"title": "x"}).json()
    assert client.patch(f"/api/actions/{created['id']}", headers=admin, json={"meeting_id": other["id"]}).status_code == 422
```

- [ ] **Step 2: Correr los tests para ver que fallan**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest tests/test_meetings.py -q 2>&1 | tail -3`
Expected: fallos por 404 en `/meetings`.

- [ ] **Step 3: Modelo Meeting y columna `meeting_id` en Action**

`app/models/meeting.py`:

```python
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import EngagementScopedMixin


class Meeting(EngagementScopedMixin, Base):
    __tablename__ = "meetings"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    held_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    participants: Mapped[str] = mapped_column(Text, default="", nullable=False)
    objective: Mapped[str] = mapped_column(Text, default="", nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    discussion: Mapped[str] = mapped_column(Text, default="", nullable=False)
    next_steps: Mapped[str] = mapped_column(Text, default="", nullable=False)
```

En `app/models/action.py`, después de la línea de `initiative_id`, añadir:

```python
    meeting_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("meetings.id"), index=True, nullable=True)
```

`app/models/__init__.py`:

```python
from app.models.activity import Activity
from app.models.action import Action
from app.models.engagement import Engagement
from app.models.initiative import Initiative
from app.models.finding import Finding
from app.models.meeting import Meeting
from app.models.milestone import Milestone
from app.models.organization import Organization
from app.models.user import User

__all__ = ["Action", "Activity", "Engagement", "Finding", "Initiative", "Meeting", "Milestone", "Organization", "User"]
```

- [ ] **Step 4: Schemas**

En `app/schemas/action.py`, añadir `meeting_id: uuid.UUID | None = None` a `ActionCreate` (después de `initiative_id`), a `ActionUpdate` (igual) y `meeting_id: uuid.UUID | None` a `ActionRead` (después de `initiative_id`).

`app/schemas/meeting.py`:

```python
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MeetingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    held_on: datetime
    participants: str = Field(default="", max_length=10000)
    objective: str = Field(default="", max_length=10000)
    summary: str = Field(default="", max_length=10000)
    discussion: str = Field(default="", max_length=10000)
    next_steps: str = Field(default="", max_length=10000)


class MeetingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    held_on: datetime | None = None
    participants: str | None = Field(default=None, max_length=10000)
    objective: str | None = Field(default=None, max_length=10000)
    summary: str | None = Field(default=None, max_length=10000)
    discussion: str | None = Field(default=None, max_length=10000)
    next_steps: str | None = Field(default=None, max_length=10000)


class MeetingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    engagement_id: uuid.UUID
    title: str
    held_on: datetime
    participants: str
    objective: str
    summary: str
    discussion: str
    next_steps: str
    created_at: datetime
    updated_at: datetime
```

- [ ] **Step 5: CRUD de meetings y filtro `meeting_id` en actions**

`app/crud/meetings.py`:

```python
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.meeting import Meeting


def list_for_engagement(db: Session, engagement_id: uuid.UUID, *, limit: int = 50, offset: int = 0) -> tuple[list[Meeting], int]:
    query = select(Meeting).where(Meeting.engagement_id == engagement_id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Meeting.held_on.desc(), Meeting.created_at.desc()).limit(limit).offset(offset)))
    return items, total
```

En `app/crud/actions.py`, cambiar la firma de `list_for_engagement` para aceptar `meeting_id` y añadir `list_by_meeting`:

```python
def list_for_engagement(
    db: Session, engagement_id: uuid.UUID, *, status: ActionStatus | None = None,
    initiative_id: uuid.UUID | None = None, owner_user_id: uuid.UUID | None = None,
    meeting_id: uuid.UUID | None = None, limit: int = 50, offset: int = 0,
) -> tuple[list[Action], int]:
    query = select(Action).where(Action.engagement_id == engagement_id)
    if status:
        query = query.where(Action.status == status)
    if initiative_id:
        query = query.where(Action.initiative_id == initiative_id)
    if owner_user_id:
        query = query.where(Action.owner_user_id == owner_user_id)
    if meeting_id:
        query = query.where(Action.meeting_id == meeting_id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Action.due_date.nulls_last(), Action.created_at.desc()).limit(limit).offset(offset)))
    return items, total


def list_by_meeting(db: Session, meeting_id: uuid.UUID) -> list[Action]:
    return list(db.scalars(select(Action).where(Action.meeting_id == meeting_id).order_by(Action.due_date.nulls_last(), Action.created_at)))
```

En `app/routers/actions.py`, en `list_actions` añadir el parámetro `meeting_id: uuid.UUID | None = None` (después de `owner_user_id`) y pasarlo: `meeting_id=meeting_id,` en la llamada a `actions_crud.list_for_engagement`.

- [ ] **Step 6: Service de actions valida `meeting_id` y menciona la reunión**

En `app/services/actions.py`: añadir `from app.models.meeting import Meeting`; en `_validate_links`, antes de la validación de `owner_id`, añadir:

```python
    meeting_id = payload.get("meeting_id")
    if meeting_id is not None:
        meeting = db.get(Meeting, meeting_id)
        if meeting is None or meeting.engagement_id != engagement.id:
            raise HTTPException(status_code=422, detail="meeting_id no pertenece a este engagement")
```

En `create_action`, reemplazar la llamada a `log_activity` por:

```python
    summary = f'{user.full_name} created Action "{action.title}"'
    if action.meeting_id is not None:
        meeting = db.get(Meeting, action.meeting_id)
        summary += f' from Meeting "{meeting.title}"'
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="action",
        entity_id=action.id, summary=summary,
    )
```

En `update_action`, cambiar el set nullable a `nullable={"owner_user_id", "initiative_id", "meeting_id", "due_date"}`.

- [ ] **Step 7: Service y router de meetings**

`app/services/meetings.py`:

```python
from sqlalchemy.orm import Session

from app.models.engagement import Engagement
from app.models.enums import ActivityAction
from app.models.meeting import Meeting
from app.models.user import User
from app.schemas.common import updates
from app.schemas.meeting import MeetingCreate, MeetingUpdate
from app.services.activity import diff_changes, log_activity


def create_meeting(db: Session, *, user: User, engagement: Engagement, data: MeetingCreate) -> Meeting:
    meeting = Meeting(organization_id=engagement.organization_id, engagement_id=engagement.id, created_by=user.id, **data.model_dump())
    db.add(meeting)
    db.flush()
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="meeting",
        entity_id=meeting.id, summary=f'{user.full_name} created Meeting "{meeting.title}"',
    )
    db.commit()
    db.refresh(meeting)
    return meeting


def update_meeting(db: Session, *, user: User, meeting: Meeting, data: MeetingUpdate) -> Meeting:
    payload = updates(data)
    changes = diff_changes(meeting, payload)
    if not changes:
        return meeting
    for field, value in payload.items():
        setattr(meeting, field, value)
    engagement = db.get(Engagement, meeting.engagement_id)
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.UPDATED, entity_type="meeting",
        entity_id=meeting.id, summary=f'{user.full_name} updated Meeting "{meeting.title}"', changes=changes,
    )
    db.commit()
    db.refresh(meeting)
    return meeting
```

`app/routers/meetings.py` (versión de esta tarea; Task 3 añade `detail` y `decisions`):

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import meetings as meetings_crud
from app.database import get_db
from app.dependencies import get_engagement, require_roles, scoped
from app.models.engagement import Engagement
from app.models.enums import Role
from app.models.meeting import Meeting
from app.models.user import User
from app.schemas.action import ActionCreate, ActionRead
from app.schemas.common import Page, Pagination, pagination_params
from app.schemas.meeting import MeetingCreate, MeetingRead, MeetingUpdate
from app.services import actions as actions_service
from app.services import meetings as meetings_service

router = APIRouter(tags=["meetings"])
syner_only = Depends(require_roles(Role.SYNER_ADMIN))
scoped_meeting = Depends(scoped(Meeting, "meeting_id"))


@router.get("/engagements/{engagement_id}/meetings", response_model=Page[MeetingRead])
def list_meetings(
    engagement: Engagement = Depends(get_engagement),
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = meetings_crud.list_for_engagement(db, engagement.id, limit=pagination.limit, offset=pagination.offset)
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/meetings", response_model=MeetingRead, status_code=201)
def create_meeting(
    data: MeetingCreate,
    user: User = syner_only,
    engagement: Engagement = Depends(get_engagement),
    db: Session = Depends(get_db),
):
    return meetings_service.create_meeting(db, user=user, engagement=engagement, data=data)


@router.get("/meetings/{meeting_id}", response_model=MeetingRead)
def read_meeting(meeting: Meeting = scoped_meeting):
    return meeting


@router.patch("/meetings/{meeting_id}", response_model=MeetingRead)
def update_meeting(
    data: MeetingUpdate,
    user: User = syner_only,
    meeting: Meeting = scoped_meeting,
    db: Session = Depends(get_db),
):
    return meetings_service.update_meeting(db, user=user, meeting=meeting, data=data)


@router.post("/meetings/{meeting_id}/actions", response_model=ActionRead, status_code=201)
def create_action_from_meeting(
    data: ActionCreate,
    user: User = syner_only,
    meeting: Meeting = scoped_meeting,
    db: Session = Depends(get_db),
):
    engagement = db.get(Engagement, meeting.engagement_id)
    payload = data.model_copy(update={"meeting_id": meeting.id})
    return actions_service.create_action(db, user=user, engagement=engagement, data=payload)
```

En `app/main.py`: import `..., initiatives, meetings, milestones` y `app.include_router(meetings.router, prefix="/api")` después de `milestones`.

- [ ] **Step 8: Correr toda la suite**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest -q 2>&1 | tail -3`
Expected: `80 passed`.

- [ ] **Step 9: Commit**

```bash
cd /mnt/d/Devs/HiTOxSyner
git add app tests/test_meetings.py
git commit -m "feat: meetings y actions derivadas de reunión con meeting_id"
```

---

### Task 3: Decisions (decision log con aprobación ejecutiva), meeting detail y tile "Decisions Required"

**Files:**
- Modify: `app/models/enums.py`, `app/models/__init__.py`, `app/main.py`, `app/schemas/meeting.py`, `app/routers/meetings.py`, `app/schemas/dashboard.py`, `app/services/dashboard.py`, `app/schemas/initiative.py`, `app/routers/initiatives.py`
- Create: `app/models/decision.py`, `app/schemas/decision.py`, `app/crud/decisions.py`, `app/services/decisions.py`, `app/routers/decisions.py`
- Test: `tests/test_decisions.py`

**Interfaces:**
- Consumes: `Meeting`, `scoped_meeting` (Task 2); `validate_initiative` no se reutiliza (cada service valida sus propios vínculos para mantener los mensajes de error).
- Produces: `DecisionStatus` enum y `RESOLUTION_STATUSES = (APPROVED, REJECTED, DEFERRED)`; modelo `Decision`; `DecisionCreate`, `DecisionUpdate`, `DecisionRead`; `decisions_crud.list_for_engagement(db, engagement_id, *, status=None, initiative_id=None, meeting_id=None, limit, offset)`, `count_required(db, engagement_id) -> int`, `required(db, engagement_id, limit=5) -> list[Decision]`, `list_by_initiative(db, initiative_id)`, `list_by_meeting(db, meeting_id)`; `decisions_service.create_decision(db, *, user, engagement, data)`, `update_decision(db, *, user, decision, data)`; `MeetingDetail(meeting, decisions, actions)`; rutas `GET|POST /engagements/{id}/decisions`, `GET|PATCH /decisions/{did}`, `GET /meetings/{mid}/detail`, `POST /meetings/{mid}/decisions`; `DashboardRead.decisions_required: list[DecisionRead]`; `InitiativeDetail.decisions: list[DecisionRead]`.

- [ ] **Step 1: Escribir los tests**

`tests/test_decisions.py`:

```python
from datetime import date

from tests.factories import login

DECISION = {"title": "Adoptar plataforma única de conciliación", "context": "Hoy hay tres herramientas.", "alternatives": "A) Mantener. B) Consolidar.", "syner_recommendation": "Consolidar en 90 días.", "owner_name": "Dirección de Operaciones", "impact": "Alto en costo operativo"}
MEETING = {"title": "Comité #2", "held_on": "2026-10-21T16:00:00Z"}


def test_syner_creates_decision_with_defaults_and_logs_activity(client, world):
    admin = login(client, "admin@syner.example")
    response = client.post(f"/api/engagements/{world.eng_a.id}/decisions", headers=admin, json=DECISION)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "Proposed"
    assert body["decided_on"] is None
    assert body["final_decision"] == ""
    assert body["initiative_id"] is None and body["meeting_id"] is None
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["summary"] == 'Syner Admin created Decision "Adoptar plataforma única de conciliación"'


def test_client_roles_cannot_create_decisions(client, world):
    for email in ("exec@a.example", "collab@a.example"):
        assert client.post(f"/api/engagements/{world.eng_a.id}/decisions", headers=login(client, email), json=DECISION).status_code == 403


def test_executive_approves_and_decided_on_is_set(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/decisions", headers=admin, json=DECISION).json()
    exec_a = login(client, "exec@a.example")
    response = client.patch(f"/api/decisions/{created['id']}", headers=exec_a, json={"status": "Approved"})
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "Approved"
    assert response.json()["decided_on"] == date.today().isoformat()
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=exec_a).json()["items"][0]
    assert activity["action"] == "status_changed"
    assert activity["summary"] == 'Exec A updated Decision "Adoptar plataforma única de conciliación" from Proposed to Approved'
    deferred = client.patch(f"/api/decisions/{created['id']}", headers=exec_a, json={"status": "Deferred"})
    assert deferred.status_code == 200 and deferred.json()["decided_on"] == date.today().isoformat()


def test_executive_can_only_resolve_status_and_nothing_else(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/decisions", headers=admin, json=DECISION).json()
    exec_a = login(client, "exec@a.example")
    assert client.patch(f"/api/decisions/{created['id']}", headers=exec_a, json={"status": "Approved", "title": "Otro"}).status_code == 403
    assert client.patch(f"/api/decisions/{created['id']}", headers=exec_a, json={"status": "Under Review"}).status_code == 403
    assert client.patch(f"/api/decisions/{created['id']}", headers=exec_a, json={"final_decision": "x"}).status_code == 403
    assert client.patch(f"/api/decisions/{created['id']}", headers=exec_a, json={}).status_code == 403
    unchanged = client.get(f"/api/decisions/{created['id']}", headers=exec_a).json()
    assert unchanged["status"] == "Proposed" and unchanged["title"] == DECISION["title"]
    assert client.patch(f"/api/decisions/{created['id']}", headers=login(client, "collab@a.example"), json={"status": "Approved"}).status_code == 403


def test_syner_sets_decided_on_explicitly_and_it_is_not_overwritten(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/decisions", headers=admin, json=DECISION).json()
    response = client.patch(f"/api/decisions/{created['id']}", headers=admin, json={"status": "Rejected", "decided_on": "2026-10-01", "final_decision": "No por ahora."})
    assert response.status_code == 200
    assert response.json()["decided_on"] == "2026-10-01"
    assert response.json()["final_decision"] == "No por ahora."
    assert client.patch(f"/api/decisions/{created['id']}", headers=admin, json={"title": None}).status_code == 422
    cleared = client.patch(f"/api/decisions/{created['id']}", headers=admin, json={"decided_on": None})
    assert cleared.status_code == 200 and cleared.json()["decided_on"] is None


def test_decisions_isolated_by_organization(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/decisions", headers=admin, json=DECISION).json()
    client.post(f"/api/engagements/{world.eng_b.id}/decisions", headers=admin, json={**DECISION, "title": "De B"})
    assert client.get(f"/api/engagements/{world.eng_a.id}/decisions", headers=login(client, "collab@a.example")).json()["total"] == 1
    assert client.get(f"/api/decisions/{created['id']}", headers=login(client, "exec@b.example")).status_code == 404
    assert client.patch(f"/api/decisions/{created['id']}", headers=login(client, "exec@b.example"), json={"status": "Approved"}).status_code == 404
    assert client.get(f"/api/engagements/{world.eng_a.id}/decisions", headers=login(client, "exec@b.example")).status_code == 404


def test_links_must_belong_to_engagement(client, world):
    admin = login(client, "admin@syner.example")
    other_initiative = client.post(f"/api/engagements/{world.eng_b.id}/initiatives", headers=admin, json={"name": "De B"}).json()
    other_meeting = client.post(f"/api/engagements/{world.eng_b.id}/meetings", headers=admin, json=MEETING).json()
    base = f"/api/engagements/{world.eng_a.id}/decisions"
    assert client.post(base, headers=admin, json={**DECISION, "initiative_id": other_initiative["id"]}).status_code == 422
    assert client.post(base, headers=admin, json={**DECISION, "meeting_id": other_meeting["id"]}).status_code == 422
    created = client.post(base, headers=admin, json=DECISION).json()
    assert client.patch(f"/api/decisions/{created['id']}", headers=admin, json={"initiative_id": other_initiative["id"]}).status_code == 422


def test_dashboard_counts_and_lists_decisions_required(client, world):
    admin = login(client, "admin@syner.example")
    base = f"/api/engagements/{world.eng_a.id}/decisions"
    client.post(base, headers=admin, json={**DECISION, "title": "Propuesta"})
    client.post(base, headers=admin, json={**DECISION, "title": "En revisión", "status": "Under Review"})
    client.post(base, headers=admin, json={**DECISION, "title": "Aprobada", "status": "Approved"})
    body = client.get(f"/api/engagements/{world.eng_a.id}/dashboard", headers=login(client, "exec@a.example")).json()
    assert body["tiles"]["decisions_required"] == 2
    assert {d["title"] for d in body["decisions_required"]} == {"Propuesta", "En revisión"}
    assert client.get(base, headers=admin, params={"status": "Approved"}).json()["total"] == 1


def test_meeting_detail_aggregates_decisions_and_actions(client, world):
    admin = login(client, "admin@syner.example")
    meeting = client.post(f"/api/engagements/{world.eng_a.id}/meetings", headers=admin, json=MEETING).json()
    decision = client.post(f"/api/meetings/{meeting['id']}/decisions", headers=admin, json=DECISION)
    assert decision.status_code == 201, decision.text
    assert decision.json()["meeting_id"] == meeting["id"]
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["summary"] == 'Syner Admin created Decision "Adoptar plataforma única de conciliación" from Meeting "Comité #2"'
    client.post(f"/api/meetings/{meeting['id']}/actions", headers=admin, json={"title": "Acción de reunión"})
    client.post(f"/api/engagements/{world.eng_a.id}/decisions", headers=admin, json={**DECISION, "title": "Suelta"})
    detail = client.get(f"/api/meetings/{meeting['id']}/detail", headers=login(client, "collab@a.example"))
    assert detail.status_code == 200
    body = detail.json()
    assert body["meeting"]["id"] == meeting["id"]
    assert [d["title"] for d in body["decisions"]] == [DECISION["title"]]
    assert [a["title"] for a in body["actions"]] == ["Acción de reunión"]
    assert client.get(f"/api/meetings/{meeting['id']}/detail", headers=login(client, "exec@b.example")).status_code == 404
    assert client.post(f"/api/meetings/{meeting['id']}/decisions", headers=login(client, "exec@a.example"), json=DECISION).status_code == 403


def test_initiative_detail_includes_decisions(client, world):
    admin = login(client, "admin@syner.example")
    initiative = client.post(f"/api/engagements/{world.eng_a.id}/initiatives", headers=admin, json={"name": "Automatización"}).json()
    client.post(f"/api/engagements/{world.eng_a.id}/decisions", headers=admin, json={**DECISION, "initiative_id": initiative["id"]})
    client.post(f"/api/engagements/{world.eng_a.id}/decisions", headers=admin, json={**DECISION, "title": "Suelta"})
    detail = client.get(f"/api/initiatives/{initiative['id']}/detail", headers=login(client, "exec@a.example")).json()
    assert [d["title"] for d in detail["decisions"]] == [DECISION["title"]]
```

- [ ] **Step 2: Correr los tests para ver que fallan**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest tests/test_decisions.py -q 2>&1 | tail -3`
Expected: fallos por 404 en `/decisions`.

- [ ] **Step 3: Enum y modelo**

Añadir al final de `app/models/enums.py`:

```python
class DecisionStatus(str, enum.Enum):
    PROPOSED = "Proposed"
    UNDER_REVIEW = "Under Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    DEFERRED = "Deferred"


RESOLUTION_STATUSES = (DecisionStatus.APPROVED, DecisionStatus.REJECTED, DecisionStatus.DEFERRED)
PENDING_DECISION_STATUSES = (DecisionStatus.PROPOSED, DecisionStatus.UNDER_REVIEW)
```

`app/models/decision.py`:

```python
import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import EngagementScopedMixin, db_enum
from app.models.enums import DecisionStatus


class Decision(EngagementScopedMixin, Base):
    __tablename__ = "decisions"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    context: Mapped[str] = mapped_column(Text, default="", nullable=False)
    alternatives: Mapped[str] = mapped_column(Text, default="", nullable=False)
    syner_recommendation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    final_decision: Mapped[str] = mapped_column(Text, default="", nullable=False)
    owner_name: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    participants: Mapped[str] = mapped_column(Text, default="", nullable=False)
    decided_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    impact: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[DecisionStatus] = mapped_column(
        db_enum(DecisionStatus, "decision_status"), default=DecisionStatus.PROPOSED, nullable=False
    )
    initiative_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("initiatives.id"), index=True, nullable=True)
    meeting_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("meetings.id"), index=True, nullable=True)
```

`app/models/__init__.py`: añadir `from app.models.decision import Decision` (en orden alfabético, después de `Action`) y `"Decision"` en `__all__`.

- [ ] **Step 4: Schemas**

`app/schemas/decision.py`:

```python
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DecisionStatus


class DecisionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    context: str = Field(default="", max_length=10000)
    alternatives: str = Field(default="", max_length=10000)
    syner_recommendation: str = Field(default="", max_length=10000)
    final_decision: str = Field(default="", max_length=10000)
    owner_name: str = Field(default="", max_length=200)
    participants: str = Field(default="", max_length=10000)
    decided_on: date | None = None
    impact: str = Field(default="", max_length=10000)
    status: DecisionStatus = DecisionStatus.PROPOSED
    initiative_id: uuid.UUID | None = None
    meeting_id: uuid.UUID | None = None


class DecisionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    context: str | None = Field(default=None, max_length=10000)
    alternatives: str | None = Field(default=None, max_length=10000)
    syner_recommendation: str | None = Field(default=None, max_length=10000)
    final_decision: str | None = Field(default=None, max_length=10000)
    owner_name: str | None = Field(default=None, max_length=200)
    participants: str | None = Field(default=None, max_length=10000)
    decided_on: date | None = None
    impact: str | None = Field(default=None, max_length=10000)
    status: DecisionStatus | None = None
    initiative_id: uuid.UUID | None = None
    meeting_id: uuid.UUID | None = None


class DecisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    engagement_id: uuid.UUID
    title: str
    context: str
    alternatives: str
    syner_recommendation: str
    final_decision: str
    owner_name: str
    participants: str
    decided_on: date | None
    impact: str
    status: DecisionStatus
    initiative_id: uuid.UUID | None
    meeting_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
```

En `app/schemas/meeting.py` añadir al final (con los imports `from app.schemas.action import ActionRead` y `from app.schemas.decision import DecisionRead` arriba):

```python
class MeetingDetail(BaseModel):
    meeting: MeetingRead
    decisions: list[DecisionRead]
    actions: list[ActionRead]
```

- [ ] **Step 5: CRUD**

`app/crud/decisions.py`:

```python
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.decision import Decision
from app.models.enums import PENDING_DECISION_STATUSES, DecisionStatus


def list_for_engagement(
    db: Session, engagement_id: uuid.UUID, *, status: DecisionStatus | None = None,
    initiative_id: uuid.UUID | None = None, meeting_id: uuid.UUID | None = None,
    limit: int = 50, offset: int = 0,
) -> tuple[list[Decision], int]:
    query = select(Decision).where(Decision.engagement_id == engagement_id)
    if status:
        query = query.where(Decision.status == status)
    if initiative_id:
        query = query.where(Decision.initiative_id == initiative_id)
    if meeting_id:
        query = query.where(Decision.meeting_id == meeting_id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Decision.created_at.desc()).limit(limit).offset(offset)))
    return items, total


def _pending(engagement_id: uuid.UUID):
    return select(Decision).where(Decision.engagement_id == engagement_id).where(Decision.status.in_(PENDING_DECISION_STATUSES))


def count_required(db: Session, engagement_id: uuid.UUID) -> int:
    return db.scalar(select(func.count()).select_from(_pending(engagement_id).subquery())) or 0


def required(db: Session, engagement_id: uuid.UUID, limit: int = 5) -> list[Decision]:
    return list(db.scalars(_pending(engagement_id).order_by(Decision.created_at).limit(limit)))


def list_by_initiative(db: Session, initiative_id: uuid.UUID) -> list[Decision]:
    return list(db.scalars(select(Decision).where(Decision.initiative_id == initiative_id).order_by(Decision.created_at)))


def list_by_meeting(db: Session, meeting_id: uuid.UUID) -> list[Decision]:
    return list(db.scalars(select(Decision).where(Decision.meeting_id == meeting_id).order_by(Decision.created_at)))
```

- [ ] **Step 6: Service**

`app/services/decisions.py`:

```python
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.decision import Decision
from app.models.engagement import Engagement
from app.models.enums import RESOLUTION_STATUSES, ActivityAction
from app.models.initiative import Initiative
from app.models.meeting import Meeting
from app.models.user import User
from app.schemas.common import updates
from app.schemas.decision import DecisionCreate, DecisionUpdate
from app.services.activity import diff_changes, log_activity


def _validate_links(db: Session, engagement: Engagement, payload: dict) -> None:
    initiative_id = payload.get("initiative_id")
    if initiative_id is not None:
        initiative = db.get(Initiative, initiative_id)
        if initiative is None or initiative.engagement_id != engagement.id:
            raise HTTPException(status_code=422, detail="initiative_id no pertenece a este engagement")
    meeting_id = payload.get("meeting_id")
    if meeting_id is not None:
        meeting = db.get(Meeting, meeting_id)
        if meeting is None or meeting.engagement_id != engagement.id:
            raise HTTPException(status_code=422, detail="meeting_id no pertenece a este engagement")


def create_decision(db: Session, *, user: User, engagement: Engagement, data: DecisionCreate) -> Decision:
    payload = data.model_dump()
    _validate_links(db, engagement, payload)
    decision = Decision(organization_id=engagement.organization_id, engagement_id=engagement.id, created_by=user.id, **payload)
    db.add(decision)
    db.flush()
    summary = f'{user.full_name} created Decision "{decision.title}"'
    if decision.meeting_id is not None:
        meeting = db.get(Meeting, decision.meeting_id)
        summary += f' from Meeting "{meeting.title}"'
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="decision",
        entity_id=decision.id, summary=summary,
    )
    db.commit()
    db.refresh(decision)
    return decision


def update_decision(db: Session, *, user: User, decision: Decision, data: DecisionUpdate) -> Decision:
    payload = updates(data, nullable={"decided_on", "initiative_id", "meeting_id"})
    engagement = db.get(Engagement, decision.engagement_id)
    _validate_links(db, engagement, payload)
    new_status = payload.get("status")
    if new_status in RESOLUTION_STATUSES and "decided_on" not in payload and decision.decided_on is None:
        payload["decided_on"] = date.today()
    changes = diff_changes(decision, payload)
    if not changes:
        return decision
    for field, value in payload.items():
        setattr(decision, field, value)
    status_change = next((c for c in changes if c["field"] == "status"), None)
    if status_change:
        action = ActivityAction.STATUS_CHANGED
        summary = f'{user.full_name} updated Decision "{decision.title}" from {status_change["before"]} to {status_change["after"]}'
    else:
        action = ActivityAction.UPDATED
        summary = f'{user.full_name} updated Decision "{decision.title}"'
    log_activity(
        db, user=user, engagement=engagement, action=action, entity_type="decision",
        entity_id=decision.id, summary=summary, changes=changes,
    )
    db.commit()
    db.refresh(decision)
    return decision
```

Nota: en el test `test_executive_approves_and_decided_on_is_set`, el segundo PATCH a `Deferred` conserva el `decided_on` ya fijado porque la regla solo lo rellena cuando está vacío.

- [ ] **Step 7: Router de decisions con RBAC ejecutivo**

`app/routers/decisions.py`:

```python
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import decisions as decisions_crud
from app.database import get_db
from app.dependencies import get_current_user, get_engagement, require_roles, scoped
from app.models.decision import Decision
from app.models.engagement import Engagement
from app.models.enums import RESOLUTION_STATUSES, DecisionStatus, Role
from app.models.user import User
from app.schemas.common import Page, Pagination, pagination_params
from app.schemas.decision import DecisionCreate, DecisionRead, DecisionUpdate
from app.services import decisions as decisions_service

router = APIRouter(tags=["decisions"])
syner_only = Depends(require_roles(Role.SYNER_ADMIN))
scoped_decision = Depends(scoped(Decision, "decision_id"))
FORBIDDEN = HTTPException(status_code=403, detail="No tienes permisos para esta acción")


@router.get("/engagements/{engagement_id}/decisions", response_model=Page[DecisionRead])
def list_decisions(
    engagement: Engagement = Depends(get_engagement),
    status: DecisionStatus | None = None,
    initiative_id: uuid.UUID | None = None,
    meeting_id: uuid.UUID | None = None,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = decisions_crud.list_for_engagement(
        db, engagement.id, status=status, initiative_id=initiative_id, meeting_id=meeting_id,
        limit=pagination.limit, offset=pagination.offset,
    )
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/decisions", response_model=DecisionRead, status_code=201)
def create_decision(
    data: DecisionCreate,
    user: User = syner_only,
    engagement: Engagement = Depends(get_engagement),
    db: Session = Depends(get_db),
):
    return decisions_service.create_decision(db, user=user, engagement=engagement, data=data)


@router.get("/decisions/{decision_id}", response_model=DecisionRead)
def read_decision(decision: Decision = scoped_decision):
    return decision


@router.patch("/decisions/{decision_id}", response_model=DecisionRead)
def update_decision(
    data: DecisionUpdate,
    decision: Decision = scoped_decision,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role == Role.HITO_EXECUTIVE:
        sent = data.model_dump(exclude_unset=True)
        if set(sent) != {"status"} or sent["status"] not in RESOLUTION_STATUSES:
            raise FORBIDDEN
    elif user.role != Role.SYNER_ADMIN:
        raise FORBIDDEN
    return decisions_service.update_decision(db, user=user, decision=decision, data=data)
```

En `app/main.py`: import `..., dashboard, decisions, engagements, ...` y `app.include_router(decisions.router, prefix="/api")` después de `meetings`.

- [ ] **Step 8: Meeting detail y decisions desde reunión**

En `app/routers/meetings.py` añadir imports `from app.crud import actions as actions_crud`, `from app.crud import decisions as decisions_crud`, `from app.schemas.decision import DecisionCreate, DecisionRead`, `from app.schemas.meeting import MeetingCreate, MeetingDetail, MeetingRead, MeetingUpdate` (reemplaza el import anterior de meeting), `from app.services import decisions as decisions_service`, y añadir al final:

```python
@router.get("/meetings/{meeting_id}/detail", response_model=MeetingDetail)
def meeting_detail(meeting: Meeting = scoped_meeting, db: Session = Depends(get_db)):
    return MeetingDetail(
        meeting=MeetingRead.model_validate(meeting),
        decisions=[DecisionRead.model_validate(d) for d in decisions_crud.list_by_meeting(db, meeting.id)],
        actions=[ActionRead.model_validate(a) for a in actions_crud.list_by_meeting(db, meeting.id)],
    )


@router.post("/meetings/{meeting_id}/decisions", response_model=DecisionRead, status_code=201)
def create_decision_from_meeting(
    data: DecisionCreate,
    user: User = syner_only,
    meeting: Meeting = scoped_meeting,
    db: Session = Depends(get_db),
):
    engagement = db.get(Engagement, meeting.engagement_id)
    payload = data.model_copy(update={"meeting_id": meeting.id})
    return decisions_service.create_decision(db, user=user, engagement=engagement, data=payload)
```

- [ ] **Step 9: Dashboard e initiative detail**

En `app/schemas/dashboard.py`: añadir `from app.schemas.decision import DecisionRead` y cambiar `decisions_required: list[dict]` por `decisions_required: list[DecisionRead]`.

En `app/services/dashboard.py`: añadir `from app.crud import decisions as decisions_crud` y `from app.schemas.decision import DecisionRead`; en `build_dashboard` cambiar `decisions_required=0,` por `decisions_required=decisions_crud.count_required(db, engagement.id),` en los tiles y `decisions_required=[],` por `decisions_required=[DecisionRead.model_validate(d) for d in decisions_crud.required(db, engagement.id)],` en el `DashboardRead`.

En `app/schemas/initiative.py`: añadir `from app.schemas.decision import DecisionRead` y en `InitiativeDetail` añadir `decisions: list[DecisionRead]` después de `actions`.

En `app/routers/initiatives.py`: añadir `from app.crud import decisions as decisions_crud` y `from app.schemas.decision import DecisionRead`; en `initiative_detail` añadir `decisions = decisions_crud.list_by_initiative(db, initiative.id)` después de `actions = ...` y `decisions=[DecisionRead.model_validate(d) for d in decisions],` en el `InitiativeDetail(...)` después de `actions=`.

- [ ] **Step 10: Correr toda la suite**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest -q 2>&1 | tail -3`
Expected: `90 passed`.

- [ ] **Step 11: Commit**

```bash
cd /mnt/d/Devs/HiTOxSyner
git add app tests/test_decisions.py
git commit -m "feat: decision log con aprobación ejecutiva, meeting detail y tile Decisions Required"
```

---

### Task 4: Comments y resolución genérica de entidades

**Files:**
- Create: `app/services/entities.py`, `app/models/comment.py`, `app/schemas/comment.py`, `app/crud/comments.py`, `app/services/comments.py`, `app/routers/comments.py`
- Modify: `app/models/__init__.py`, `app/main.py`
- Test: `tests/test_comments.py`

**Interfaces:**
- Produces: `ENTITY_MODELS: dict[str, tuple[type, str]]` y `resolve_entity(db, engagement, entity_type, entity_id) -> tuple[object, str]` (devuelve la entidad y su título; 422 si el tipo es desconocido, no existe o es de otro engagement) en `app/services/entities.py`; modelo `Comment`; `CommentCreate(entity_type, entity_id, body)`, `CommentRead`; `comments_crud.list_for_entity(db, engagement_id, entity_type, entity_id, *, limit, offset)`; `comments_service.create_comment(db, *, user, engagement, data)`; rutas `GET|POST /engagements/{id}/comments?entity_type=&entity_id=`.

- [ ] **Step 1: Escribir los tests**

`tests/test_comments.py`:

```python
import uuid

import pytest

from tests.factories import login


def _initiative(client, world, engagement=None):
    admin = login(client, "admin@syner.example")
    eng = engagement or world.eng_a
    return admin, client.post(f"/api/engagements/{eng.id}/initiatives", headers=admin, json={"name": "Automatización"}).json()


@pytest.mark.parametrize("email", ["admin@syner.example", "exec@a.example", "collab@a.example"])
def test_every_role_can_comment_and_activity_targets_the_entity(client, world, email):
    _, initiative = _initiative(client, world)
    headers = login(client, email)
    response = client.post(f"/api/engagements/{world.eng_a.id}/comments", headers=headers, json={"entity_type": "initiative", "entity_id": initiative["id"], "body": "Revisemos alcance."})
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["body"] == "Revisemos alcance."
    assert body["author_name"] in ("Syner Admin", "Exec A", "Collab A")
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=headers, params={"entity_type": "initiative", "entity_id": initiative["id"]}).json()["items"][0]
    assert activity["action"] == "commented"
    assert activity["summary"] == f'{body["author_name"]} commented on Initiative "Automatización"'


def test_comments_list_in_chronological_order_for_the_entity(client, world):
    admin, initiative = _initiative(client, world)
    base = f"/api/engagements/{world.eng_a.id}/comments"
    client.post(base, headers=admin, json={"entity_type": "initiative", "entity_id": initiative["id"], "body": "Primero"})
    client.post(base, headers=admin, json={"entity_type": "initiative", "entity_id": initiative["id"], "body": "Segundo"})
    finding = client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, json={"title": "Otro"}).json()
    client.post(base, headers=admin, json={"entity_type": "finding", "entity_id": finding["id"], "body": "Del finding"})
    listing = client.get(base, headers=login(client, "collab@a.example"), params={"entity_type": "initiative", "entity_id": initiative["id"]}).json()
    assert listing["total"] == 2
    assert [c["body"] for c in listing["items"]] == ["Primero", "Segundo"]
    assert client.get(base, headers=admin).status_code == 422


def test_comment_target_must_exist_in_this_engagement(client, world):
    admin, foreign = _initiative(client, world, engagement=world.eng_b)
    base = f"/api/engagements/{world.eng_a.id}/comments"
    assert client.post(base, headers=admin, json={"entity_type": "initiative", "entity_id": foreign["id"], "body": "x"}).status_code == 422
    assert client.post(base, headers=admin, json={"entity_type": "initiative", "entity_id": str(uuid.uuid4()), "body": "x"}).status_code == 422
    assert client.post(base, headers=admin, json={"entity_type": "unicorn", "entity_id": foreign["id"], "body": "x"}).status_code == 422
    assert client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["total"] == 0


def test_body_is_required_and_comments_are_scoped(client, world):
    admin, initiative = _initiative(client, world)
    base = f"/api/engagements/{world.eng_a.id}/comments"
    assert client.post(base, headers=admin, json={"entity_type": "initiative", "entity_id": initiative["id"], "body": ""}).status_code == 422
    assert client.get(base, headers=login(client, "exec@b.example"), params={"entity_type": "initiative", "entity_id": initiative["id"]}).status_code == 404
    assert client.post(base, headers=login(client, "collab@b.example"), json={"entity_type": "initiative", "entity_id": initiative["id"], "body": "x"}).status_code == 404
```

- [ ] **Step 2: Correr los tests para ver que fallan**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest tests/test_comments.py -q 2>&1 | tail -3`
Expected: fallos por 404 en `/comments`.

- [ ] **Step 3: Resolución genérica de entidades**

`app/services/entities.py`:

```python
import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.action import Action
from app.models.decision import Decision
from app.models.engagement import Engagement
from app.models.finding import Finding
from app.models.initiative import Initiative
from app.models.meeting import Meeting

ENTITY_MODELS: dict[str, tuple[type, str]] = {
    "finding": (Finding, "title"),
    "initiative": (Initiative, "name"),
    "meeting": (Meeting, "title"),
    "decision": (Decision, "title"),
    "action": (Action, "title"),
}


def entity_label(entity_type: str) -> str:
    return entity_type.capitalize()


def resolve_entity(db: Session, engagement: Engagement, entity_type: str, entity_id: uuid.UUID) -> tuple[object, str]:
    """Devuelve (entidad, título). 422 si el tipo no se conoce o la entidad no es de este engagement."""
    if entity_type not in ENTITY_MODELS:
        raise HTTPException(status_code=422, detail=f"entity_type debe ser uno de: {', '.join(ENTITY_MODELS)}")
    model, title_attr = ENTITY_MODELS[entity_type]
    entity = db.get(model, entity_id)
    if entity is None or entity.engagement_id != engagement.id:
        raise HTTPException(status_code=422, detail="entity_id no pertenece a este engagement")
    return entity, getattr(entity, title_attr)
```

- [ ] **Step 4: Modelo, schemas, crud**

`app/models/comment.py`:

```python
import uuid

from sqlalchemy import ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import EngagementScopedMixin


class Comment(EngagementScopedMixin, Base):
    __tablename__ = "comments"
    __table_args__ = (Index("ix_comments_entity", "entity_type", "entity_id"),)

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    author_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    author_name: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
```

`app/models/__init__.py`: añadir `from app.models.comment import Comment` y `"Comment"` en `__all__`.

`app/schemas/comment.py`:

```python
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    entity_type: str = Field(min_length=1, max_length=50)
    entity_id: uuid.UUID
    body: str = Field(min_length=1, max_length=10000)


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    engagement_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    author_id: uuid.UUID | None
    author_name: str
    body: str
    created_at: datetime
```

`app/crud/comments.py`:

```python
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.comment import Comment


def list_for_entity(
    db: Session, engagement_id: uuid.UUID, entity_type: str, entity_id: uuid.UUID, *, limit: int = 50, offset: int = 0,
) -> tuple[list[Comment], int]:
    query = (
        select(Comment)
        .where(Comment.engagement_id == engagement_id)
        .where(Comment.entity_type == entity_type)
        .where(Comment.entity_id == entity_id)
    )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Comment.created_at, Comment.id).limit(limit).offset(offset)))
    return items, total
```

- [ ] **Step 5: Service y router**

`app/services/comments.py`:

```python
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.engagement import Engagement
from app.models.enums import ActivityAction
from app.models.user import User
from app.schemas.comment import CommentCreate
from app.services.activity import log_activity
from app.services.entities import entity_label, resolve_entity


def create_comment(db: Session, *, user: User, engagement: Engagement, data: CommentCreate) -> Comment:
    _, title = resolve_entity(db, engagement, data.entity_type, data.entity_id)
    comment = Comment(
        organization_id=engagement.organization_id, engagement_id=engagement.id, created_by=user.id,
        entity_type=data.entity_type, entity_id=data.entity_id, author_id=user.id, author_name=user.full_name, body=data.body,
    )
    db.add(comment)
    db.flush()
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.COMMENTED, entity_type=data.entity_type,
        entity_id=data.entity_id, summary=f'{user.full_name} commented on {entity_label(data.entity_type)} "{title}"',
    )
    db.commit()
    db.refresh(comment)
    return comment
```

`app/routers/comments.py`:

```python
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.crud import comments as comments_crud
from app.database import get_db
from app.dependencies import get_current_user, get_engagement
from app.models.engagement import Engagement
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentRead
from app.schemas.common import Page, Pagination, pagination_params
from app.services import comments as comments_service

router = APIRouter(tags=["comments"])


@router.get("/engagements/{engagement_id}/comments", response_model=Page[CommentRead])
def list_comments(
    engagement: Engagement = Depends(get_engagement),
    entity_type: str = Query(min_length=1, max_length=50),
    entity_id: uuid.UUID = Query(),
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = comments_crud.list_for_entity(
        db, engagement.id, entity_type, entity_id, limit=pagination.limit, offset=pagination.offset
    )
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/comments", response_model=CommentRead, status_code=201)
def create_comment(
    data: CommentCreate,
    user: User = Depends(get_current_user),
    engagement: Engagement = Depends(get_engagement),
    db: Session = Depends(get_db),
):
    return comments_service.create_comment(db, user=user, engagement=engagement, data=data)
```

En `app/main.py`: import `..., auth, comments, dashboard, ...` y `app.include_router(comments.router, prefix="/api")` después de `decisions`.

- [ ] **Step 6: Correr toda la suite**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest -q 2>&1 | tail -3`
Expected: `96 passed` (el test parametrizado cuenta como 3).

- [ ] **Step 7: Commit**

```bash
cd /mnt/d/Devs/HiTOxSyner
git add app tests/test_comments.py
git commit -m "feat: comments por entidad con activity trail y resolución genérica de entidades"
```

---

### Task 5: Documents, DocumentLink y documentos en initiative detail

**Files:**
- Modify: `app/models/enums.py`, `app/models/__init__.py`, `app/main.py`, `app/schemas/initiative.py`, `app/routers/initiatives.py`
- Create: `app/models/document.py`, `app/schemas/document.py`, `app/crud/documents.py`, `app/services/documents.py`, `app/routers/documents.py`
- Test: `tests/test_documents.py`

**Interfaces:**
- Consumes: `resolve_entity`, `entity_label` (Task 4).
- Produces: `DocumentCategory` enum; modelos `Document` (con relationship `links`) y `DocumentLink`; `DocumentCreate`, `DocumentUpdate`, `DocumentRead` (incluye `links: list[DocumentLinkRead]`), `DocumentLinkCreate(entity_type, entity_id)`, `DocumentLinkRead`; `documents_crud.list_for_engagement(db, engagement_id, *, category=None, include_internal: bool, limit, offset)`, `documents_crud.list_by_entity(db, engagement_id, entity_type, entity_id, *, include_internal: bool) -> list[Document]`; `documents_service.create_document`, `update_document`, `add_link(db, *, user, document, data) -> DocumentLink`, `remove_link(db, *, user, document, link_id) -> None`; `can_see_internal(user) -> bool`; rutas `GET|POST /engagements/{id}/documents`, `GET|PATCH /documents/{docid}`, `POST /documents/{docid}/links`, `DELETE /documents/{docid}/links/{link_id}`; `InitiativeDetail.documents: list[DocumentRead]`.

- [ ] **Step 1: Escribir los tests**

`tests/test_documents.py`:

```python
import uuid

from tests.factories import login

DOCUMENT = {"name": "Diagnóstico operativo v1", "category": "Assessment", "version": "1.0", "url": "https://drive.example.com/d/abc", "doc_date": "2026-10-10", "tags": ["diagnóstico", "operaciones"]}


def _admin_and_initiative(client, world):
    admin = login(client, "admin@syner.example")
    return admin, client.post(f"/api/engagements/{world.eng_a.id}/initiatives", headers=admin, json={"name": "Automatización"}).json()


def test_syner_creates_document_with_uploader_tags_and_activity(client, world):
    admin = login(client, "admin@syner.example")
    response = client.post(f"/api/engagements/{world.eng_a.id}/documents", headers=admin, json=DOCUMENT)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["uploader_id"] == str(world.admin.id)
    assert body["tags"] == ["diagnóstico", "operaciones"]
    assert body["internal_only"] is False
    assert body["links"] == []
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["summary"] == 'Syner Admin created Document "Diagnóstico operativo v1"'
    updated = client.patch(f"/api/documents/{body['id']}", headers=admin, json={"version": "1.1", "tags": []})
    assert updated.status_code == 200 and updated.json()["version"] == "1.1" and updated.json()["tags"] == []
    assert client.patch(f"/api/documents/{body['id']}", headers=admin, json={"name": None}).status_code == 422
    assert client.post(f"/api/engagements/{world.eng_a.id}/documents", headers=admin, json={**DOCUMENT, "tags": ["x"] * 21}).status_code == 422


def test_client_roles_cannot_write_documents(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/documents", headers=admin, json=DOCUMENT).json()
    for email in ("exec@a.example", "collab@a.example"):
        headers = login(client, email)
        assert client.post(f"/api/engagements/{world.eng_a.id}/documents", headers=headers, json=DOCUMENT).status_code == 403
        assert client.patch(f"/api/documents/{created['id']}", headers=headers, json={"version": "2"}).status_code == 403
        assert client.post(f"/api/documents/{created['id']}/links", headers=headers, json={"entity_type": "initiative", "entity_id": str(uuid.uuid4())}).status_code == 403


def test_internal_only_documents_are_hidden_from_collaborators(client, world):
    admin, initiative = _admin_and_initiative(client, world)
    base = f"/api/engagements/{world.eng_a.id}/documents"
    public = client.post(base, headers=admin, json=DOCUMENT).json()
    internal = client.post(base, headers=admin, json={**DOCUMENT, "name": "Notas internas Syner", "internal_only": True}).json()
    for doc in (public, internal):
        assert client.post(f"/api/documents/{doc['id']}/links", headers=admin, json={"entity_type": "initiative", "entity_id": initiative["id"]}).status_code == 201
    collab = login(client, "collab@a.example")
    listing = client.get(base, headers=collab).json()
    assert [d["name"] for d in listing["items"]] == [DOCUMENT["name"]] and listing["total"] == 1
    assert client.get(f"/api/documents/{internal['id']}", headers=collab).status_code == 404
    assert client.get(f"/api/documents/{public['id']}", headers=collab).status_code == 200
    detail = client.get(f"/api/initiatives/{initiative['id']}/detail", headers=collab).json()
    assert [d["name"] for d in detail["documents"]] == [DOCUMENT["name"]]
    exec_a = login(client, "exec@a.example")
    assert client.get(base, headers=exec_a).json()["total"] == 2
    assert client.get(f"/api/documents/{internal['id']}", headers=exec_a).status_code == 200
    assert len(client.get(f"/api/initiatives/{initiative['id']}/detail", headers=exec_a).json()["documents"]) == 2


def test_links_are_unique_validated_and_removable(client, world):
    admin, initiative = _admin_and_initiative(client, world)
    base = f"/api/engagements/{world.eng_a.id}/documents"
    doc = client.post(base, headers=admin, json=DOCUMENT).json()
    other_doc = client.post(base, headers=admin, json={**DOCUMENT, "name": "Otro"}).json()
    link = client.post(f"/api/documents/{doc['id']}/links", headers=admin, json={"entity_type": "initiative", "entity_id": initiative["id"]})
    assert link.status_code == 201, link.text
    assert link.json()["entity_type"] == "initiative"
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["summary"] == 'Syner Admin linked Document "Diagnóstico operativo v1" to Initiative "Automatización"'
    assert client.post(f"/api/documents/{doc['id']}/links", headers=admin, json={"entity_type": "initiative", "entity_id": initiative["id"]}).status_code == 409
    foreign = client.post(f"/api/engagements/{world.eng_b.id}/initiatives", headers=admin, json={"name": "De B"}).json()
    assert client.post(f"/api/documents/{doc['id']}/links", headers=admin, json={"entity_type": "initiative", "entity_id": foreign["id"]}).status_code == 422
    assert client.post(f"/api/documents/{doc['id']}/links", headers=admin, json={"entity_type": "unicorn", "entity_id": initiative["id"]}).status_code == 422
    other_link = client.post(f"/api/documents/{other_doc['id']}/links", headers=admin, json={"entity_type": "initiative", "entity_id": initiative["id"]}).json()
    assert client.delete(f"/api/documents/{doc['id']}/links/{other_link['id']}", headers=admin).status_code == 404
    assert len(client.get(f"/api/documents/{other_doc['id']}", headers=admin).json()["links"]) == 1
    assert client.delete(f"/api/documents/{doc['id']}/links/{link.json()['id']}", headers=admin).status_code == 204
    assert client.get(f"/api/documents/{doc['id']}", headers=admin).json()["links"] == []
    assert [d["name"] for d in client.get(f"/api/initiatives/{initiative['id']}/detail", headers=admin).json()["documents"]] == ["Otro"]


def test_documents_filter_by_category_and_are_isolated(client, world):
    admin = login(client, "admin@syner.example")
    base = f"/api/engagements/{world.eng_a.id}/documents"
    created = client.post(base, headers=admin, json=DOCUMENT).json()
    client.post(base, headers=admin, json={**DOCUMENT, "name": "Minuta", "category": "Meetings"})
    client.post(f"/api/engagements/{world.eng_b.id}/documents", headers=admin, json={**DOCUMENT, "name": "De B"})
    assert client.get(base, headers=admin, params={"category": "Meetings"}).json()["items"][0]["name"] == "Minuta"
    assert client.get(base, headers=login(client, "exec@a.example")).json()["total"] == 2
    assert client.get(f"/api/documents/{created['id']}", headers=login(client, "exec@b.example")).status_code == 404
    assert client.get(base, headers=login(client, "collab@b.example")).status_code == 404
```

- [ ] **Step 2: Correr los tests para ver que fallan**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest tests/test_documents.py -q 2>&1 | tail -3`
Expected: fallos por 404 en `/documents`.

- [ ] **Step 3: Enum y modelos**

Añadir al final de `app/models/enums.py`:

```python
class DocumentCategory(str, enum.Enum):
    DISCOVERY = "Discovery"
    ASSESSMENT = "Assessment"
    STRATEGY = "Strategy"
    PROCESS = "Process"
    TECHNOLOGY = "Technology"
    DATA = "Data"
    AI = "AI"
    REPORTS = "Reports"
    MEETINGS = "Meetings"
    DELIVERABLES = "Deliverables"
    EVIDENCE = "Evidence"
```

`app/models/document.py`:

```python
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import EngagementScopedMixin, db_enum
from app.models.enums import DocumentCategory


class Document(EngagementScopedMixin, Base):
    __tablename__ = "documents"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    category: Mapped[DocumentCategory] = mapped_column(
        db_enum(DocumentCategory, "document_category"), default=DocumentCategory.DISCOVERY, nullable=False
    )
    version: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    url: Mapped[str] = mapped_column(String(2000), default="", nullable=False)
    doc_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    uploader_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(50)), default=list, nullable=False)
    internal_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    links: Mapped[list["DocumentLink"]] = relationship(
        "DocumentLink", back_populates="document", lazy="selectin", cascade="all, delete-orphan", order_by="DocumentLink.created_at"
    )


class DocumentLink(Base):
    __tablename__ = "document_links"
    __table_args__ = (UniqueConstraint("document_id", "entity_type", "entity_id", name="uq_document_links_target"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    document: Mapped[Document] = relationship(Document, back_populates="links")
```

`app/models/__init__.py` completo:

```python
from app.models.activity import Activity
from app.models.action import Action
from app.models.comment import Comment
from app.models.decision import Decision
from app.models.document import Document, DocumentLink
from app.models.engagement import Engagement
from app.models.initiative import Initiative
from app.models.finding import Finding
from app.models.meeting import Meeting
from app.models.milestone import Milestone
from app.models.organization import Organization
from app.models.user import User

__all__ = [
    "Action", "Activity", "Comment", "Decision", "Document", "DocumentLink", "Engagement", "Finding",
    "Initiative", "Meeting", "Milestone", "Organization", "User",
]
```

- [ ] **Step 4: Schemas**

`app/schemas/document.py`:

```python
import uuid
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DocumentCategory

Tag = Annotated[str, Field(min_length=1, max_length=50)]


class DocumentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10000)
    category: DocumentCategory = DocumentCategory.DISCOVERY
    version: str = Field(default="", max_length=50)
    url: str = Field(default="", max_length=2000)
    doc_date: date | None = None
    tags: list[Tag] = Field(default_factory=list, max_length=20)
    internal_only: bool = False


class DocumentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    category: DocumentCategory | None = None
    version: str | None = Field(default=None, max_length=50)
    url: str | None = Field(default=None, max_length=2000)
    doc_date: date | None = None
    tags: list[Tag] | None = Field(default=None, max_length=20)
    internal_only: bool | None = None


class DocumentLinkCreate(BaseModel):
    entity_type: str = Field(min_length=1, max_length=50)
    entity_id: uuid.UUID


class DocumentLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    engagement_id: uuid.UUID
    name: str
    description: str
    category: DocumentCategory
    version: str
    url: str
    doc_date: date | None
    uploader_id: uuid.UUID | None
    tags: list[str]
    internal_only: bool
    links: list[DocumentLinkRead]
    created_at: datetime
    updated_at: datetime
```

- [ ] **Step 5: CRUD**

`app/crud/documents.py`:

```python
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentLink
from app.models.enums import DocumentCategory


def list_for_engagement(
    db: Session, engagement_id: uuid.UUID, *, category: DocumentCategory | None = None,
    include_internal: bool, limit: int = 50, offset: int = 0,
) -> tuple[list[Document], int]:
    query = select(Document).where(Document.engagement_id == engagement_id)
    if category:
        query = query.where(Document.category == category)
    if not include_internal:
        query = query.where(Document.internal_only.is_(False))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Document.doc_date.desc().nulls_last(), Document.created_at.desc()).limit(limit).offset(offset)))
    return items, total


def list_by_entity(
    db: Session, engagement_id: uuid.UUID, entity_type: str, entity_id: uuid.UUID, *, include_internal: bool,
) -> list[Document]:
    query = (
        select(Document)
        .join(DocumentLink, DocumentLink.document_id == Document.id)
        .where(Document.engagement_id == engagement_id)
        .where(DocumentLink.entity_type == entity_type)
        .where(DocumentLink.entity_id == entity_id)
    )
    if not include_internal:
        query = query.where(Document.internal_only.is_(False))
    return list(db.scalars(query.order_by(Document.doc_date.desc().nulls_last(), Document.created_at.desc())))


def find_link(db: Session, document_id: uuid.UUID, entity_type: str, entity_id: uuid.UUID) -> DocumentLink | None:
    query = (
        select(DocumentLink)
        .where(DocumentLink.document_id == document_id)
        .where(DocumentLink.entity_type == entity_type)
        .where(DocumentLink.entity_id == entity_id)
    )
    return db.scalar(query)
```

- [ ] **Step 6: Service**

`app/services/documents.py`:

```python
import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.crud import documents as documents_crud
from app.models.document import Document, DocumentLink
from app.models.engagement import Engagement
from app.models.enums import ActivityAction, Role
from app.models.user import User
from app.schemas.common import updates
from app.schemas.document import DocumentCreate, DocumentLinkCreate, DocumentUpdate
from app.services.activity import diff_changes, log_activity
from app.services.entities import entity_label, resolve_entity


def can_see_internal(user: User) -> bool:
    return user.role != Role.HITO_COLLABORATOR


def create_document(db: Session, *, user: User, engagement: Engagement, data: DocumentCreate) -> Document:
    document = Document(
        organization_id=engagement.organization_id, engagement_id=engagement.id, created_by=user.id,
        uploader_id=user.id, **data.model_dump(),
    )
    db.add(document)
    db.flush()
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="document",
        entity_id=document.id, summary=f'{user.full_name} created Document "{document.name}"',
    )
    db.commit()
    db.refresh(document)
    return document


def update_document(db: Session, *, user: User, document: Document, data: DocumentUpdate) -> Document:
    payload = updates(data, nullable={"doc_date"})
    changes = diff_changes(document, payload)
    if not changes:
        return document
    for field, value in payload.items():
        setattr(document, field, value)
    engagement = db.get(Engagement, document.engagement_id)
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.UPDATED, entity_type="document",
        entity_id=document.id, summary=f'{user.full_name} updated Document "{document.name}"', changes=changes,
    )
    db.commit()
    db.refresh(document)
    return document


def add_link(db: Session, *, user: User, document: Document, data: DocumentLinkCreate) -> DocumentLink:
    engagement = db.get(Engagement, document.engagement_id)
    _, title = resolve_entity(db, engagement, data.entity_type, data.entity_id)
    if documents_crud.find_link(db, document.id, data.entity_type, data.entity_id) is not None:
        raise HTTPException(status_code=409, detail="El documento ya está vinculado a esta entidad")
    link = DocumentLink(document_id=document.id, entity_type=data.entity_type, entity_id=data.entity_id)
    db.add(link)
    db.flush()
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.UPDATED, entity_type="document",
        entity_id=document.id,
        summary=f'{user.full_name} linked Document "{document.name}" to {entity_label(data.entity_type)} "{title}"',
        changes=[{"field": "links", "before": None, "after": f"{data.entity_type}:{data.entity_id}"}],
    )
    db.commit()
    db.refresh(link)
    return link


def remove_link(db: Session, *, user: User, document: Document, link_id: uuid.UUID) -> None:
    link = db.get(DocumentLink, link_id)
    if link is None or link.document_id != document.id:
        raise HTTPException(status_code=404, detail="DocumentLink not found")
    engagement = db.get(Engagement, document.engagement_id)
    db.delete(link)
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.UPDATED, entity_type="document",
        entity_id=document.id, summary=f'{user.full_name} unlinked Document "{document.name}" from {entity_label(link.entity_type)}',
        changes=[{"field": "links", "before": f"{link.entity_type}:{link.entity_id}", "after": None}],
    )
    db.commit()
```

- [ ] **Step 7: Router**

`app/routers/documents.py`:

```python
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.crud import documents as documents_crud
from app.database import get_db
from app.dependencies import get_current_user, get_engagement, require_roles, scoped
from app.models.document import Document
from app.models.engagement import Engagement
from app.models.enums import DocumentCategory, Role
from app.models.user import User
from app.schemas.common import Page, Pagination, pagination_params
from app.schemas.document import DocumentCreate, DocumentLinkCreate, DocumentLinkRead, DocumentRead, DocumentUpdate
from app.services import documents as documents_service

router = APIRouter(tags=["documents"])
syner_only = Depends(require_roles(Role.SYNER_ADMIN))
scoped_document = Depends(scoped(Document, "document_id"))


def visible_document(document: Document = scoped_document, user: User = Depends(get_current_user)) -> Document:
    if document.internal_only and not documents_service.can_see_internal(user):
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/engagements/{engagement_id}/documents", response_model=Page[DocumentRead])
def list_documents(
    engagement: Engagement = Depends(get_engagement),
    user: User = Depends(get_current_user),
    category: DocumentCategory | None = None,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = documents_crud.list_for_engagement(
        db, engagement.id, category=category, include_internal=documents_service.can_see_internal(user),
        limit=pagination.limit, offset=pagination.offset,
    )
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/documents", response_model=DocumentRead, status_code=201)
def create_document(
    data: DocumentCreate,
    user: User = syner_only,
    engagement: Engagement = Depends(get_engagement),
    db: Session = Depends(get_db),
):
    return documents_service.create_document(db, user=user, engagement=engagement, data=data)


@router.get("/documents/{document_id}", response_model=DocumentRead)
def read_document(document: Document = Depends(visible_document)):
    return document


@router.patch("/documents/{document_id}", response_model=DocumentRead)
def update_document(
    data: DocumentUpdate,
    user: User = syner_only,
    document: Document = scoped_document,
    db: Session = Depends(get_db),
):
    return documents_service.update_document(db, user=user, document=document, data=data)


@router.post("/documents/{document_id}/links", response_model=DocumentLinkRead, status_code=201)
def add_link(
    data: DocumentLinkCreate,
    user: User = syner_only,
    document: Document = scoped_document,
    db: Session = Depends(get_db),
):
    return documents_service.add_link(db, user=user, document=document, data=data)


@router.delete("/documents/{document_id}/links/{link_id}", status_code=204, response_class=Response)
def remove_link(
    link_id: uuid.UUID,
    user: User = syner_only,
    document: Document = scoped_document,
    db: Session = Depends(get_db),
):
    documents_service.remove_link(db, user=user, document=document, link_id=link_id)
    return Response(status_code=204)
```

En `app/main.py`: import `..., decisions, documents, engagements, ...` y `app.include_router(documents.router, prefix="/api")` después de `comments`.

- [ ] **Step 8: Documentos en initiative detail**

En `app/schemas/initiative.py`: añadir `from app.schemas.document import DocumentRead` y en `InitiativeDetail` añadir `documents: list[DocumentRead]` después de `decisions`.

En `app/routers/initiatives.py`: añadir `from app.crud import documents as documents_crud`, `from app.schemas.document import DocumentRead`, `from app.services.documents import can_see_internal` y `from app.dependencies import get_current_user, get_engagement, require_roles, scoped` (reemplaza el import de dependencies). Reemplazar `initiative_detail` por la versión final:

```python
@router.get("/initiatives/{initiative_id}/detail", response_model=InitiativeDetail)
def initiative_detail(
    initiative: Initiative = scoped_initiative,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    findings = findings_crud.list_by_initiative(db, initiative.id)
    milestones = milestones_crud.list_by_initiative(db, initiative.id)
    actions = actions_crud.list_by_initiative(db, initiative.id)
    decisions = decisions_crud.list_by_initiative(db, initiative.id)
    documents = documents_crud.list_by_entity(db, initiative.engagement_id, "initiative", initiative.id, include_internal=can_see_internal(user))
    own_activity, _ = activities_crud.list_for_engagement(
        db, initiative.engagement_id, entity_type="initiative", entity_id=initiative.id, limit=20
    )
    finding_activity = []
    for finding in findings:
        items, _ = activities_crud.list_for_engagement(
            db, initiative.engagement_id, entity_type="finding", entity_id=finding.id, limit=5
        )
        finding_activity.extend(items)
    activity = sorted(own_activity + finding_activity, key=lambda a: a.created_at, reverse=True)[:20]
    return InitiativeDetail(
        initiative=InitiativeRead.model_validate(initiative),
        findings=[FindingRead.model_validate(f) for f in findings],
        milestones=[MilestoneRead.model_validate(m) for m in milestones],
        actions=[ActionRead.model_validate(a) for a in actions],
        decisions=[DecisionRead.model_validate(d) for d in decisions],
        documents=[DocumentRead.model_validate(d) for d in documents],
        activity=[ActivityRead.model_validate(a) for a in activity],
    )
```

- [ ] **Step 9: Correr toda la suite**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest -q 2>&1 | tail -3`
Expected: `101 passed`.

- [ ] **Step 10: Commit**

```bash
cd /mnt/d/Devs/HiTOxSyner
git add app tests/test_documents.py
git commit -m "feat: documents con vínculos a entidades, visibilidad internal_only y documentos en initiative detail"
```

---

### Task 6: Migración Alembic del plan 2, seed demo ampliado y README

**Files:**
- Create: `alembic/versions/<rev>_plan_2_client_room_modules.py` (autogenerada y revisada)
- Modify: `app/seed.py`, `tests/test_seed.py`, `README.md`

**Interfaces:**
- Consumes: todos los services de Tasks 1–5.
- Produces: esquema de producción con `milestones`, `meetings`, `decisions`, `comments`, `documents`, `document_links` y `actions.meeting_id`; seed idempotente por módulo.

- [ ] **Step 1: Generar la migración sobre la base de desarrollo**

```bash
cd /mnt/d/Devs/HiTOxSyner
.venv/bin/alembic upgrade head
.venv/bin/alembic revision --autogenerate -m "plan 2 client room modules"
ls alembic/versions
```
Expected: aparece un archivo nuevo `alembic/versions/<rev>_plan_2_client_room_modules.py`. Abrirlo y verificar que `upgrade()` contiene `op.create_table` para `meetings`, `milestones`, `comments`, `documents`, `decisions`, `document_links` (en ese orden de dependencias o equivalente: `meetings` antes que `decisions`; `documents` antes que `document_links`), más `op.add_column('actions', sa.Column('meeting_id', sa.Uuid(), nullable=True))`, `op.create_index(op.f('ix_actions_meeting_id'), ...)` y `op.create_foreign_key(None, 'actions', 'meetings', ['meeting_id'], ['id'])`.

- [ ] **Step 2: Revisar a mano la migración**

Hacer estas tres ediciones en el archivo generado:

1. Nombrar la foreign key de `actions.meeting_id` (Alembic genera `None` y el downgrade fallaría). En `upgrade()`:
   ```python
   op.create_foreign_key('fk_actions_meeting_id_meetings', 'actions', 'meetings', ['meeting_id'], ['id'])
   ```
   y en `downgrade()`:
   ```python
   op.drop_constraint('fk_actions_meeting_id_meetings', 'actions', type_='foreignkey')
   ```
2. Añadir debajo de los identificadores de revisión:
   ```python
   ENUM_TYPES = ('milestone_phase', 'milestone_status', 'decision_status', 'document_category')
   ```
3. Al final de `downgrade()`, después del último `op.drop_table`, añadir:
   ```python
   for enum_name in ENUM_TYPES:
       op.execute(f'DROP TYPE IF EXISTS "{enum_name}"')
   ```

Verificar también que el `downgrade()` elimina `document_links` antes que `documents`, y `decisions` antes que `meetings` (Alembic lo genera en orden inverso al `upgrade()`; si no, reordenar).

- [ ] **Step 3: Probar upgrade, downgrade y upgrade**

```bash
cd /mnt/d/Devs/HiTOxSyner
.venv/bin/alembic upgrade head
.venv/bin/alembic downgrade -1
.venv/bin/alembic upgrade head
PGPASSWORD=hitoxsyner ~/.local/pg/bin/psql -h localhost -U hitoxsyner -d hitoxsyner_dev -tAc "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY 1"
PGPASSWORD=hitoxsyner ~/.local/pg/bin/psql -h localhost -U hitoxsyner -d hitoxsyner_dev -tAc "SELECT typname FROM pg_type WHERE typname IN ('milestone_phase','milestone_status','decision_status','document_category')"
```
Expected: sin errores; la lista de tablas incluye `comments`, `decisions`, `document_links`, `documents`, `meetings`, `milestones`; los cuatro tipos enum existen. Si el `downgrade -1` falla por un tipo enum que sigue en uso, revisar que el `DROP TYPE` esté después de todos los `drop_table`.

- [ ] **Step 4: Actualizar `tests/test_seed.py`**

```python
from sqlalchemy import func, select

from app.models.action import Action
from app.models.comment import Comment
from app.models.decision import Decision
from app.models.document import Document, DocumentLink
from app.models.finding import Finding
from app.models.initiative import Initiative
from app.models.meeting import Meeting
from app.models.milestone import Milestone
from app.models.user import User
from app.seed import seed


def _count(db, model):
    return db.scalar(select(func.count()).select_from(model))


def test_seed_is_idempotent_and_creates_demo_data(db, client):
    seed(db)
    seed(db)
    assert _count(db, User) == 3
    assert _count(db, Finding) == 5
    assert _count(db, Initiative) == 4
    assert _count(db, Action) == 8
    assert _count(db, Milestone) == 6
    assert _count(db, Meeting) == 3
    assert _count(db, Decision) == 3
    assert _count(db, Document) == 5
    assert _count(db, DocumentLink) == 3
    assert _count(db, Comment) == 2
    titles = list(db.scalars(select(Finding.title))) + list(db.scalars(select(Milestone.name))) + list(db.scalars(select(Document.name)))
    assert all(t.startswith("[Demo]") for t in titles)
    assert db.scalar(select(func.count()).select_from(Document).where(Document.internal_only.is_(True))) == 1
    response = client.post("/api/auth/login", json={"email": "admin@syner.demo", "password": "syner-demo"})
    assert response.status_code == 200
```

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest tests/test_seed.py -q 2>&1 | tail -3`
Expected: FAIL en `_count(db, Milestone) == 6` (devuelve 0).

- [ ] **Step 5: Reescribir `app/seed.py` con guardas por módulo**

```python
"""Seed demo: python -m app.seed. Idempotente por slug/email y por módulo. Todo el contenido es ficticio y lleva prefijo [Demo]."""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.database import SessionLocal
from app.models.comment import Comment
from app.models.decision import Decision
from app.models.document import Document
from app.models.engagement import Engagement
from app.models.enums import Health, Level, OrganizationKind, Role
from app.models.finding import Finding
from app.models.initiative import Initiative
from app.models.meeting import Meeting
from app.models.milestone import Milestone
from app.models.organization import Organization
from app.models.user import User
from app.schemas.action import ActionCreate
from app.schemas.comment import CommentCreate
from app.schemas.decision import DecisionCreate
from app.schemas.document import DocumentCreate, DocumentLinkCreate
from app.schemas.finding import FindingCreate
from app.schemas.initiative import InitiativeCreate
from app.schemas.meeting import MeetingCreate
from app.schemas.milestone import MilestoneCreate
from app.services import actions as actions_service
from app.services import comments as comments_service
from app.services import decisions as decisions_service
from app.services import documents as documents_service
from app.services import findings as findings_service
from app.services import initiatives as initiatives_service
from app.services import meetings as meetings_service
from app.services import milestones as milestones_service


def _org(db: Session, name: str, slug: str, kind: OrganizationKind) -> Organization:
    org = db.scalar(select(Organization).where(Organization.slug == slug))
    if org is None:
        org = Organization(name=name, slug=slug, kind=kind)
        db.add(org)
        db.flush()
    return org


def _user(db: Session, org: Organization, email: str, name: str, role: Role, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(organization_id=org.id, email=email, full_name=name, password_hash=hash_password(password), role=role)
        db.add(user)
        db.flush()
    return user


def _has_rows(db: Session, model, engagement: Engagement) -> bool:
    return db.scalar(select(model).where(model.engagement_id == engagement.id).limit(1)) is not None


def _initiatives(db: Session, engagement: Engagement) -> list[Initiative]:
    return list(db.scalars(select(Initiative).where(Initiative.engagement_id == engagement.id).order_by(Initiative.created_at)))


def _seed_delivery(db: Session, admin: User, collab: User, engagement: Engagement) -> None:
    """Findings, initiatives y actions del plan 1."""
    if _has_rows(db, Finding, engagement):
        return
    findings_data = [
        ("[Demo] Conciliación diaria dependiente de hojas de cálculo", "Quick Win", "Operaciones", Level.HIGH),
        ("[Demo] Reportes a clientes institucionales generados manualmente", "Opportunity", "Operaciones", Level.HIGH),
        ("[Demo] Sin inventario único de procesos críticos", "Gap", "Procesos", Level.MEDIUM),
        ("[Demo] Aprobaciones concentradas en pocas personas", "Risk", "Gobierno", Level.CRITICAL),
        ("[Demo] Datos de cartera replicados en varios sistemas", "Strategic Insight", "Datos", Level.HIGH),
    ]
    for title, ftype, area, impact in findings_data:
        findings_service.create_finding(
            db, user=admin, engagement=engagement,
            data=FindingCreate(title=title, type=ftype, area=area, impact=impact, description="Contenido ficticio de demostración.", recommendation="Recomendación ficticia de demostración."),
        )
    initiatives_data = [
        ("[Demo] Automatización de conciliación diaria", "Execution", 40),
        ("[Demo] Reporting institucional automatizado", "Design", 15),
        ("[Demo] Mapa de procesos críticos", "Discovery", 5),
        ("[Demo] Modelo de gobierno de aprobaciones", "Validation", 25),
    ]
    initiatives = []
    for name, status, progress in initiatives_data:
        initiatives.append(initiatives_service.create_initiative(
            db, user=admin, engagement=engagement,
            data=InitiativeCreate(name=name, status=status, progress_pct=progress, objective="Objetivo ficticio de demostración.", hito_owner="Owner HiTO (demo)", target_date=date.today() + timedelta(days=60)),
        ))
    actions_data = [
        ("[Demo] Levantar inventario de hojas de cálculo", 0, collab.id, 7),
        ("[Demo] Definir reglas de conciliación", 0, None, 14),
        ("[Demo] Validar formato de reporte con cliente piloto", 1, collab.id, 10),
        ("[Demo] Entrevistar responsables de proceso", 2, None, 5),
        ("[Demo] Documentar matriz de aprobaciones actual", 3, collab.id, 12),
        ("[Demo] Proponer umbrales de delegación", 3, None, 20),
        ("[Demo] Revisar fuentes de datos de cartera", 2, None, 18),
        ("[Demo] Preparar sesión de validación con dirección", 1, None, 9),
    ]
    for title, idx, owner_id, days in actions_data:
        actions_service.create_action(
            db, user=admin, engagement=engagement,
            data=ActionCreate(title=title, initiative_id=initiatives[idx].id, owner_user_id=owner_id, owner_name="" if owner_id else "Equipo Syner", organization_side="CLIENT" if owner_id else "SYNER", due_date=date.today() + timedelta(days=days), priority=Level.HIGH if days < 10 else Level.MEDIUM),
        )
    db.commit()


def _seed_client_room(db: Session, admin: User, collab: User, engagement: Engagement) -> None:
    """Milestones, meetings, decisions, documents y comments del plan 2."""
    today = date.today()
    now = datetime.now(timezone.utc)
    initiatives = _initiatives(db, engagement)

    if not _has_rows(db, Milestone, engagement):
        milestones_data = [
            ("[Demo] Entrevistas de discovery completadas", "Discover", -10, "Done", None),
            ("[Demo] Diagnóstico operativo consolidado", "Diagnose", 7, "In Progress", 2),
            ("[Demo] Diseño del modelo de conciliación", "Design", 21, "Planned", 0),
            ("[Demo] Portafolio priorizado con dirección", "Prioritize", 30, "Planned", None),
            ("[Demo] Piloto de conciliación automatizada", "Execute", 60, "Planned", 0),
            ("[Demo] Primer tablero de KPIs de transformación", "Measure", 90, "Planned", None),
        ]
        for name, phase, days, status, idx in milestones_data:
            milestones_service.create_milestone(
                db, user=admin, engagement=engagement,
                data=MilestoneCreate(name=name, phase=phase, due_date=today + timedelta(days=days), status=status, owner="Equipo Syner", initiative_id=initiatives[idx].id if idx is not None else None, deliverable="Entregable ficticio de demostración."),
            )

    meetings = list(db.scalars(select(Meeting).where(Meeting.engagement_id == engagement.id).order_by(Meeting.held_on)))
    if not meetings:
        meetings_data = [
            ("[Demo] Kick-off del engagement", -12, "Alinear objetivos y gobierno del programa."),
            ("[Demo] Comité de transformación #1", -5, "Revisar hallazgos preliminares y acordar prioridades."),
            ("[Demo] Sesión de validación de diagnóstico", 2, "Validar el diagnóstico operativo con dirección."),
        ]
        for title, days, objective in meetings_data:
            meetings.append(meetings_service.create_meeting(
                db, user=admin, engagement=engagement,
                data=MeetingCreate(title=title, held_on=now + timedelta(days=days), participants="Dirección HiTO (demo), Equipo Syner", objective=objective, summary="Resumen ficticio de demostración.", discussion="Discusión ficticia de demostración.", next_steps="Siguientes pasos ficticios de demostración."),
            ))

    if not _has_rows(db, Decision, engagement):
        decisions_data = [
            ("[Demo] Consolidar la conciliación en una sola plataforma", "Proposed", 0, 1, None),
            ("[Demo] Nombrar owner único del reporting institucional", "Under Review", 1, None, None),
            ("[Demo] Aprobar el alcance de la fase de discovery", "Approved", None, 0, today - timedelta(days=10)),
        ]
        for title, status, idx, meeting_idx, decided_on in decisions_data:
            decisions_service.create_decision(
                db, user=admin, engagement=engagement,
                data=DecisionCreate(title=title, status=status, context="Contexto ficticio de demostración.", alternatives="A) Mantener. B) Cambiar.", syner_recommendation="Recomendación ficticia de demostración.", owner_name="Dirección HiTO (demo)", decided_on=decided_on, initiative_id=initiatives[idx].id if idx is not None else None, meeting_id=meetings[meeting_idx].id if meeting_idx is not None else None),
            )

    if not _has_rows(db, Document, engagement):
        documents_data = [
            ("[Demo] Plan de trabajo del engagement", "Strategy", "1.0", False, None),
            ("[Demo] Diagnóstico operativo preliminar", "Assessment", "0.9", False, ("initiative", initiatives[2].id)),
            ("[Demo] Minuta Comité de transformación #1", "Meetings", "1.0", False, ("meeting", meetings[1].id)),
            ("[Demo] Inventario de hojas de cálculo", "Evidence", "1.0", False, ("initiative", initiatives[0].id)),
            ("[Demo] Notas internas del equipo Syner", "Reports", "0.1", True, None),
        ]
        for name, category, version, internal, link in documents_data:
            document = documents_service.create_document(
                db, user=admin, engagement=engagement,
                data=DocumentCreate(name=name, category=category, version=version, url="", doc_date=today - timedelta(days=3), tags=["demo"], internal_only=internal, description="Documento ficticio de demostración."),
            )
            if link is not None:
                documents_service.add_link(db, user=admin, document=document, data=DocumentLinkCreate(entity_type=link[0], entity_id=link[1]))

    if not _has_rows(db, Comment, engagement):
        comments_service.create_comment(db, user=collab, engagement=engagement, data=CommentCreate(entity_type="initiative", entity_id=initiatives[0].id, body="[Demo] Iniciamos el inventario esta semana."))
        comments_service.create_comment(db, user=admin, engagement=engagement, data=CommentCreate(entity_type="initiative", entity_id=initiatives[0].id, body="[Demo] Perfecto, lo revisamos en el próximo comité."))
    db.commit()


def seed(db: Session) -> None:
    settings = get_settings()
    if settings.is_production and (
        settings.seed_syner_password == "syner-demo"
        or settings.seed_exec_password == "exec-demo"
        or settings.seed_collab_password == "collab-demo"
    ):
        raise RuntimeError("En producción define SEED_SYNER_PASSWORD, SEED_EXEC_PASSWORD y SEED_COLLAB_PASSWORD")
    syner = _org(db, "Syner", "syner", OrganizationKind.CONSULTANCY)
    hito = _org(db, "HiTO", "hito", OrganizationKind.CLIENT)
    admin = _user(db, syner, "admin@syner.demo", "Syner Admin", Role.SYNER_ADMIN, settings.seed_syner_password)
    _user(db, hito, "exec@hito.demo", "Dirección HiTO (demo)", Role.HITO_EXECUTIVE, settings.seed_exec_password)
    collab = _user(db, hito, "collab@hito.demo", "Colaborador HiTO (demo)", Role.HITO_COLLABORATOR, settings.seed_collab_password)

    engagement = db.scalar(select(Engagement).where(Engagement.organization_id == hito.id))
    if engagement is None:
        engagement = Engagement(
            organization_id=hito.id,
            name="Syner × HiTO Transformation Program",
            subtitle="Executive advisory, transformation & decision intelligence",
            health=Health.ON_TRACK,
            progress_pct=10,
            executive_summary="[Demo] Fase de discovery en curso. Se han realizado entrevistas iniciales y se está consolidando el diagnóstico.",
            start_date=date.today() - timedelta(days=14),
        )
        db.add(engagement)
        db.flush()
    db.commit()

    _seed_delivery(db, admin, collab, engagement)
    _seed_client_room(db, admin, collab, engagement)


if __name__ == "__main__":
    with SessionLocal() as session:
        seed(session)
    print("Seed completado.")
```

Antes de sobrescribir, verificar que el bloque `if __name__ == "__main__":` actual de `app/seed.py` imprime lo mismo (`sed -n '/__main__/,$p' app/seed.py`); si imprime otro texto, conservar el texto existente.

- [ ] **Step 6: Correr toda la suite y el seed en dev**

```bash
cd /mnt/d/Devs/HiTOxSyner
.venv/bin/pytest -q 2>&1 | tail -3
.venv/bin/python -m app.seed && .venv/bin/python -m app.seed
PGPASSWORD=hitoxsyner ~/.local/pg/bin/psql -h localhost -U hitoxsyner -d hitoxsyner_dev -tAc "SELECT (SELECT count(*) FROM milestones), (SELECT count(*) FROM meetings), (SELECT count(*) FROM decisions), (SELECT count(*) FROM documents), (SELECT count(*) FROM comments)"
```
Expected: `101 passed`; el seed corre dos veces sin error y la consulta devuelve `6|3|3|5|2`.

- [ ] **Step 7: README**

En `README.md`, en el paso 4 de "Desarrollo local", reemplazar la línea del seed por:

```
4. `python -m app.seed` (usuarios demo: `admin@syner.demo`, `exec@hito.demo`, `collab@hito.demo`; passwords desde `SEED_*_PASSWORD`). Crea datos `[Demo]` para findings, initiatives, actions, milestones, meetings, decisions, documents y comments; es idempotente por módulo, así que puede correrse de nuevo tras una migración para completar datos nuevos.
```

- [ ] **Step 8: Commit**

```bash
cd /mnt/d/Devs/HiTOxSyner
git add alembic app/seed.py tests/test_seed.py README.md
git commit -m "feat: migración del plan 2, seed demo por módulo y README"
```

---

### Task 7: Frontend: tipos, APIs, labels, página Roadmap y roadmap en el dashboard

**Files:**
- Modify: `frontend/src/types.ts`, `frontend/src/lib/labels.ts`, `frontend/src/lib/roles.ts`, `frontend/src/lib/dates.ts`, `frontend/src/components/StatusBadge.tsx`, `frontend/src/components/FormDrawer.tsx`, `frontend/src/api/actions.ts`, `frontend/src/pages/DashboardPage.tsx`, `frontend/src/router.tsx`
- Create: `frontend/src/api/milestones.ts`, `frontend/src/api/decisions.ts`, `frontend/src/api/meetings.ts`, `frontend/src/api/documents.ts`, `frontend/src/api/comments.ts`, `frontend/src/pages/RoadmapPage.tsx`

**Interfaces:**
- Produces (usadas por Tasks 8–11): tipos `Milestone`, `Decision`, `Meeting`, `MeetingDetail`, `Document`, `DocumentLink`, `Comment`; constantes `ROADMAP_PHASES`, `MILESTONE_STATUSES`, `DECISION_STATUSES`, `RESOLUTION_STATUSES`, `DOCUMENT_CATEGORIES`; `can(user, "comment")`; `toDateTimeInput(iso)`, `fromDateTimeInput(local)`; `FormDrawer` acepta `hideSubmit?: boolean`; `milestonesApi.{list, create, update}`, `decisionsApi.{list, create, update}`, `meetingsApi.{list, create, update, detail, createAction, createDecision}`, `documentsApi.{list, create, update, addLink, removeLink}`, `commentsApi.{list, create}`.

- [ ] **Step 1: Tipos**

Añadir a `frontend/src/types.ts` (y añadir `meeting_id: string | null;` a `Action` después de `initiative_id`):

```ts
export type RoadmapPhase = "Discover" | "Diagnose" | "Design" | "Prioritize" | "Execute" | "Measure";
export type MilestoneStatus = "Planned" | "In Progress" | "Done" | "Slipped";

export interface Milestone {
  id: string;
  engagement_id: string;
  name: string;
  description: string;
  phase: RoadmapPhase;
  due_date: string | null;
  status: MilestoneStatus;
  owner: string;
  initiative_id: string | null;
  deliverable: string;
  created_at: string;
  updated_at: string;
}

export type DecisionStatus = "Proposed" | "Under Review" | "Approved" | "Rejected" | "Deferred";

export interface Decision {
  id: string;
  engagement_id: string;
  title: string;
  context: string;
  alternatives: string;
  syner_recommendation: string;
  final_decision: string;
  owner_name: string;
  participants: string;
  decided_on: string | null;
  impact: string;
  status: DecisionStatus;
  initiative_id: string | null;
  meeting_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Meeting {
  id: string;
  engagement_id: string;
  title: string;
  held_on: string;
  participants: string;
  objective: string;
  summary: string;
  discussion: string;
  next_steps: string;
  created_at: string;
  updated_at: string;
}

export interface MeetingDetail {
  meeting: Meeting;
  decisions: Decision[];
  actions: Action[];
}

export type DocumentCategory = "Discovery" | "Assessment" | "Strategy" | "Process" | "Technology" | "Data" | "AI" | "Reports" | "Meetings" | "Deliverables" | "Evidence";

export interface DocumentLink {
  id: string;
  document_id: string;
  entity_type: string;
  entity_id: string;
}

export interface Document {
  id: string;
  engagement_id: string;
  name: string;
  description: string;
  category: DocumentCategory;
  version: string;
  url: string;
  doc_date: string | null;
  uploader_id: string | null;
  tags: string[];
  internal_only: boolean;
  links: DocumentLink[];
  created_at: string;
  updated_at: string;
}

export interface Comment {
  id: string;
  engagement_id: string;
  entity_type: string;
  entity_id: string;
  author_id: string | null;
  author_name: string;
  body: string;
  created_at: string;
}
```

Y reemplazar en `Dashboard` las tres líneas `roadmap`, `decisions_required`, `next_milestones` por:

```ts
  roadmap: { phase: RoadmapPhase; milestones: Milestone[] }[];
  decisions_required: Decision[];
  next_milestones: Milestone[];
```

Reemplazar `InitiativeDetail` por:

```ts
export interface InitiativeDetail {
  initiative: Initiative;
  findings: Finding[];
  milestones: Milestone[];
  actions: Action[];
  decisions: Decision[];
  documents: Document[];
  activity: Activity[];
}
```

- [ ] **Step 2: Labels, roles, fechas, badges, drawer**

Añadir al final de `frontend/src/lib/labels.ts`:

```ts
export const ROADMAP_PHASES = ["Discover", "Diagnose", "Design", "Prioritize", "Execute", "Measure"] as const;
export const MILESTONE_STATUSES = ["Planned", "In Progress", "Done", "Slipped"] as const;
export const DECISION_STATUSES = ["Proposed", "Under Review", "Approved", "Rejected", "Deferred"] as const;
export const RESOLUTION_STATUSES = ["Approved", "Rejected", "Deferred"] as const;
export const DOCUMENT_CATEGORIES = ["Discovery", "Assessment", "Strategy", "Process", "Technology", "Data", "AI", "Reports", "Meetings", "Deliverables", "Evidence"] as const;
export const ENTITY_LABELS: Record<string, string> = { finding: "Finding", initiative: "Initiative", meeting: "Meeting", decision: "Decision", action: "Action" };
```

`frontend/src/lib/roles.ts` completo:

```ts
import type { User } from "../types";

export type Capability = "write" | "approveDecision" | "comment" | "manageLab" | "viewLabSummary";

export function can(user: User | null, capability: Capability): boolean {
  if (!user) return false;
  switch (capability) {
    case "write":
    case "manageLab":
      return user.role === "SYNER_ADMIN";
    case "approveDecision":
    case "viewLabSummary":
      return user.role === "SYNER_ADMIN" || user.role === "HITO_EXECUTIVE";
    case "comment":
      return true;
  }
}
```

Añadir al final de `frontend/src/lib/dates.ts`:

```ts
function pad(n: number) {
  return String(n).padStart(2, "0");
}

/** ISO (UTC) → valor para <input type="datetime-local"> en hora local. */
export function toDateTimeInput(value: string | null | undefined): string {
  if (!value) return "";
  const d = new Date(value);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** Valor de <input type="datetime-local"> → ISO UTC para la API. */
export function fromDateTimeInput(value: string): string {
  return new Date(value).toISOString();
}
```

En `frontend/src/components/StatusBadge.tsx`, añadir dentro de `TONES`:

```ts
  Done: "bg-emerald-50 text-emerald-800 border-emerald-200",
  Approved: "bg-emerald-50 text-emerald-800 border-emerald-200",
  Slipped: "bg-red-50 text-red-800 border-red-200",
  Rejected: "bg-red-50 text-red-800 border-red-200",
  "Under Review": "bg-amber-50 text-amber-800 border-amber-200",
  Deferred: "bg-gray-100 text-gray-700 border-gray-200",
  Interno: "bg-amber-50 text-amber-800 border-amber-200",
```

`frontend/src/components/FormDrawer.tsx` completo (añade `hideSubmit`):

```tsx
import type { FormEvent, ReactNode } from "react";

export function FormDrawer({ open, title, onClose, onSubmit, submitting, error, children, footer, hideSubmit }: {
  open: boolean;
  title: string;
  onClose: () => void;
  onSubmit: (e: FormEvent) => void;
  submitting?: boolean;
  error?: string | null;
  children: ReactNode;
  footer?: ReactNode;
  hideSubmit?: boolean;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="flex-1 bg-black/20" onClick={onClose} />
      <form onSubmit={onSubmit} className="flex h-full w-full max-w-lg flex-col bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 className="text-base font-semibold">{title}</h2>
          <button type="button" className="btn" onClick={onClose}>Cerrar</button>
        </div>
        <div className="flex-1 space-y-4 overflow-y-auto px-5 py-4">{children}</div>
        <div className="flex items-center justify-between gap-3 border-t border-line px-5 py-3">
          <div className="text-sm text-danger">{error}</div>
          <div className="flex gap-2">
            {footer}
            {!hideSubmit && <button type="submit" className="btn btn-primary" disabled={submitting}>{submitting ? "Guardando…" : "Guardar"}</button>}
          </div>
        </div>
      </form>
    </div>
  );
}
```

- [ ] **Step 3: Archivos de API**

`frontend/src/api/milestones.ts`:

```ts
import { api } from "./client";
import type { Milestone, Page } from "../types";

export type MilestoneInput = Partial<Omit<Milestone, "id" | "engagement_id" | "created_at" | "updated_at">>;

export const milestonesApi = {
  list: (engagementId: string, params: { phase?: string; status?: string; initiative_id?: string } = {}) =>
    api.get<Page<Milestone>>(`/engagements/${engagementId}/milestones`, { params: { ...params, limit: 200 } }).then((r) => r.data),
  create: (engagementId: string, data: MilestoneInput) => api.post<Milestone>(`/engagements/${engagementId}/milestones`, data).then((r) => r.data),
  update: (id: string, data: MilestoneInput) => api.patch<Milestone>(`/milestones/${id}`, data).then((r) => r.data),
};
```

`frontend/src/api/decisions.ts`:

```ts
import { api } from "./client";
import type { Decision, Page } from "../types";

export type DecisionInput = Partial<Omit<Decision, "id" | "engagement_id" | "created_at" | "updated_at">>;

export const decisionsApi = {
  list: (engagementId: string, params: { status?: string; initiative_id?: string; meeting_id?: string } = {}) =>
    api.get<Page<Decision>>(`/engagements/${engagementId}/decisions`, { params: { ...params, limit: 200 } }).then((r) => r.data),
  create: (engagementId: string, data: DecisionInput) => api.post<Decision>(`/engagements/${engagementId}/decisions`, data).then((r) => r.data),
  update: (id: string, data: DecisionInput) => api.patch<Decision>(`/decisions/${id}`, data).then((r) => r.data),
};
```

`frontend/src/api/meetings.ts`:

```ts
import { api } from "./client";
import type { ActionInput } from "./actions";
import type { DecisionInput } from "./decisions";
import type { Action, Decision, Meeting, MeetingDetail, Page } from "../types";

export type MeetingInput = Partial<Omit<Meeting, "id" | "engagement_id" | "created_at" | "updated_at">>;

export const meetingsApi = {
  list: (engagementId: string) => api.get<Page<Meeting>>(`/engagements/${engagementId}/meetings`, { params: { limit: 200 } }).then((r) => r.data),
  create: (engagementId: string, data: MeetingInput) => api.post<Meeting>(`/engagements/${engagementId}/meetings`, data).then((r) => r.data),
  update: (id: string, data: MeetingInput) => api.patch<Meeting>(`/meetings/${id}`, data).then((r) => r.data),
  detail: (id: string) => api.get<MeetingDetail>(`/meetings/${id}/detail`).then((r) => r.data),
  createAction: (id: string, data: ActionInput) => api.post<Action>(`/meetings/${id}/actions`, data).then((r) => r.data),
  createDecision: (id: string, data: DecisionInput) => api.post<Decision>(`/meetings/${id}/decisions`, data).then((r) => r.data),
};
```

`frontend/src/api/documents.ts`:

```ts
import { api } from "./client";
import type { Document, DocumentLink, Page } from "../types";

export type DocumentInput = Partial<Omit<Document, "id" | "engagement_id" | "uploader_id" | "links" | "created_at" | "updated_at">>;

export const documentsApi = {
  list: (engagementId: string, params: { category?: string } = {}) =>
    api.get<Page<Document>>(`/engagements/${engagementId}/documents`, { params: { ...params, limit: 200 } }).then((r) => r.data),
  create: (engagementId: string, data: DocumentInput) => api.post<Document>(`/engagements/${engagementId}/documents`, data).then((r) => r.data),
  update: (id: string, data: DocumentInput) => api.patch<Document>(`/documents/${id}`, data).then((r) => r.data),
  addLink: (id: string, data: { entity_type: string; entity_id: string }) => api.post<DocumentLink>(`/documents/${id}/links`, data).then((r) => r.data),
  removeLink: (id: string, linkId: string) => api.delete<void>(`/documents/${id}/links/${linkId}`).then(() => undefined),
};
```

`frontend/src/api/comments.ts`:

```ts
import { api } from "./client";
import type { Comment, Page } from "../types";

export const commentsApi = {
  list: (engagementId: string, entityType: string, entityId: string) =>
    api.get<Page<Comment>>(`/engagements/${engagementId}/comments`, { params: { entity_type: entityType, entity_id: entityId, limit: 200 } }).then((r) => r.data),
  create: (engagementId: string, data: { entity_type: string; entity_id: string; body: string }) =>
    api.post<Comment>(`/engagements/${engagementId}/comments`, data).then((r) => r.data),
};
```

En `frontend/src/api/actions.ts`, ampliar los params de `list` a `{ status?: string; initiative_id?: string; meeting_id?: string; mine?: boolean }`.

- [ ] **Step 4: Página Roadmap**

`frontend/src/pages/RoadmapPage.tsx`:

```tsx
import { FormEvent, useState } from "react";
import { errorMessage } from "../api/client";
import { initiativesApi } from "../api/initiatives";
import { milestonesApi, MilestoneInput } from "../api/milestones";
import { EmptyState } from "../components/EmptyState";
import { Field, Select } from "../components/Field";
import { FormDrawer } from "../components/FormDrawer";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { useResource } from "../hooks/useResource";
import { formatDate } from "../lib/dates";
import { MILESTONE_STATUSES, ROADMAP_PHASES } from "../lib/labels";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";
import type { Milestone, RoadmapPhase } from "../types";

const EMPTY: MilestoneInput = { name: "", description: "", phase: "Discover", due_date: null, status: "Planned", owner: "", initiative_id: null, deliverable: "" };

export function RoadmapPage() {
  const user = useAuthStore((s) => s.user);
  const engagementId = useEngagementStore((s) => s.current?.id ?? "");
  const { data, loading, error, reload } = useResource(() => milestonesApi.list(engagementId), [engagementId]);
  const initiatives = useResource(() => initiativesApi.list(engagementId), [engagementId]);
  const writable = can(user, "write");
  const [editing, setEditing] = useState<Milestone | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<MilestoneInput>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  function openCreate(phase: RoadmapPhase = "Discover") { setEditing(null); setForm({ ...EMPTY, phase }); setFormError(null); setOpen(true); }
  function openEdit(m: Milestone) {
    if (!writable) return;
    setEditing(m);
    setForm({ name: m.name, description: m.description, phase: m.phase, due_date: m.due_date, status: m.status, owner: m.owner, initiative_id: m.initiative_id, deliverable: m.deliverable });
    setFormError(null); setOpen(true);
  }
  const set = (key: keyof MilestoneInput, value: unknown) => setForm((f) => ({ ...f, [key]: value }));

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    try {
      if (editing) await milestonesApi.update(editing.id, form);
      else await milestonesApi.create(engagementId, form);
      setOpen(false);
      await reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  const items = data?.items ?? [];
  const initiativeName = (id: string | null) => initiatives.data?.items.find((i) => i.id === id)?.name;

  return (
    <>
      <PageHeader title="Transformation Roadmap" subtitle="Seis fases del programa y sus milestones" action={writable && <button className="btn btn-primary" onClick={() => openCreate()}>Nuevo milestone</button>} />
      {error && <p className="mb-4 text-sm text-danger">{error}</p>}
      {loading && !data ? <p className="text-sm text-muted">Cargando…</p> : items.length === 0 ? (
        <EmptyState title="Sin milestones" hint={writable ? "Crea el primer milestone del roadmap." : undefined} />
      ) : (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
          {ROADMAP_PHASES.map((phase) => {
            const inPhase = items.filter((m) => m.phase === phase);
            const done = inPhase.filter((m) => m.status === "Done").length;
            return (
              <section key={phase} className="card flex flex-col p-3">
                <div className="mb-2 flex items-center justify-between">
                  <h2 className="text-sm font-semibold">{phase}</h2>
                  <span className="text-xs tabular-nums text-muted">{done}/{inPhase.length}</span>
                </div>
                <ul className="flex-1 space-y-2">
                  {inPhase.map((m) => (
                    <li key={m.id} onClick={() => openEdit(m)} className={`rounded border border-line p-2 text-sm ${writable ? "cursor-pointer hover:bg-canvas" : ""}`}>
                      <div className="font-medium leading-5">{m.name}</div>
                      <div className="mt-1 flex items-center justify-between gap-2">
                        <span className="text-xs tabular-nums text-muted">{formatDate(m.due_date)}</span>
                        <StatusBadge value={m.status} />
                      </div>
                      {m.initiative_id && <div className="mt-1 truncate text-xs text-muted">{initiativeName(m.initiative_id)}</div>}
                    </li>
                  ))}
                </ul>
                {writable && <button className="btn mt-3 w-full justify-center text-xs" onClick={() => openCreate(phase)}>+ Milestone</button>}
              </section>
            );
          })}
        </div>
      )}
      <FormDrawer open={open} title={editing ? "Editar milestone" : "Nuevo milestone"} onClose={() => setOpen(false)} onSubmit={submit} submitting={busy} error={formError}>
        <Field label="Nombre"><input className="input" value={form.name ?? ""} onChange={(e) => set("name", e.target.value)} required maxLength={200} /></Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Phase"><Select value={form.phase ?? "Discover"} onChange={(v) => set("phase", v)} options={ROADMAP_PHASES} /></Field>
          <Field label="Status"><Select value={form.status ?? "Planned"} onChange={(v) => set("status", v)} options={MILESTONE_STATUSES} /></Field>
          <Field label="Fecha objetivo"><input className="input" type="date" value={form.due_date ?? ""} onChange={(e) => set("due_date", e.target.value || null)} /></Field>
          <Field label="Owner"><input className="input" value={form.owner ?? ""} onChange={(e) => set("owner", e.target.value)} maxLength={200} /></Field>
          <Field label="Initiative">
            <select className="input" value={form.initiative_id ?? ""} onChange={(e) => set("initiative_id", e.target.value || null)}>
              <option value="">Sin initiative</option>
              {initiatives.data?.items.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
            </select>
          </Field>
        </div>
        <Field label="Deliverable"><textarea className="input" rows={2} value={form.deliverable ?? ""} onChange={(e) => set("deliverable", e.target.value)} /></Field>
        <Field label="Descripción"><textarea className="input" rows={3} value={form.description ?? ""} onChange={(e) => set("description", e.target.value)} /></Field>
      </FormDrawer>
    </>
  );
}
```

En `frontend/src/router.tsx`: importar `RoadmapPage` y reemplazar la ruta `/roadmap` por `{ path: "/roadmap", element: <RoadmapPage /> }`.

- [ ] **Step 5: Dashboard: roadmap con milestones y Next Milestones**

En `frontend/src/pages/DashboardPage.tsx`, reemplazar la sección `Transformation Roadmap` por:

```tsx
      <Section title="Transformation Roadmap">
        <div className="grid grid-cols-3 gap-2 md:grid-cols-6">
          {data.roadmap.map((phase) => {
            const done = phase.milestones.filter((m) => m.status === "Done").length;
            return (
              <Link key={phase.phase} to="/roadmap" className="rounded border border-line px-3 py-2 hover:bg-canvas">
                <div className="text-sm font-medium">{phase.phase}</div>
                <div className="text-xs tabular-nums text-muted">{done}/{phase.milestones.length} milestones</div>
                <ul className="mt-1 space-y-0.5">
                  {phase.milestones.slice(0, 3).map((m) => (
                    <li key={m.id} className="truncate text-xs" title={m.name}>{m.name}</li>
                  ))}
                </ul>
              </Link>
            );
          })}
        </div>
      </Section>
```

y la sección `Next Milestones` por:

```tsx
        <Section title="Next Milestones">
          {data.next_milestones.length === 0 ? <p className="text-sm text-muted">Sin milestones programados.</p> : (
            <ul className="space-y-2">
              {data.next_milestones.map((m) => (
                <li key={m.id} className="flex items-start justify-between gap-3 text-sm">
                  <span>{m.name}<span className="block text-xs text-muted">{m.phase}</span></span>
                  <span className="flex items-center gap-2 text-xs tabular-nums text-muted">{formatDate(m.due_date)}<StatusBadge value={m.status} /></span>
                </li>
              ))}
            </ul>
          )}
        </Section>
```

- [ ] **Step 6: Build y verificación manual**

```bash
cd /mnt/d/Devs/HiTOxSyner/frontend && npm run build
```
Expected: `tsc` sin errores y build de Vite OK. Manual (API con `.venv/bin/uvicorn app.main:app --reload` y `npm run dev`): como `admin@syner.demo` entrar a Roadmap, ver las seis columnas con los 6 milestones del seed, crear uno en "Design", editarlo a "Done"; el dashboard muestra `1/1` en Discover y la lista Next Milestones. Como `exec@hito.demo` no hay botones de crear ni se abre el drawer.

- [ ] **Step 7: Commit**

```bash
cd /mnt/d/Devs/HiTOxSyner
git add frontend
git commit -m "feat(frontend): tipos y APIs del plan 2, página Roadmap y roadmap con milestones en dashboard"
```

---

### Task 8: Frontend: página Decisions con aprobación ejecutiva y "Decisions Required" en dashboard

**Files:**
- Create: `frontend/src/components/DecisionForm.tsx`, `frontend/src/pages/DecisionsPage.tsx`
- Modify: `frontend/src/pages/DashboardPage.tsx`, `frontend/src/router.tsx`

**Interfaces:**
- Produces: `DecisionForm({ form, onChange, initiatives, meetings? })`, `EMPTY_DECISION`, `decisionToInput(d)`.

- [ ] **Step 1: Formulario reutilizable**

`frontend/src/components/DecisionForm.tsx`:

```tsx
import type { DecisionInput } from "../api/decisions";
import type { Decision, Initiative, Meeting } from "../types";
import { formatDateTime } from "../lib/dates";
import { DECISION_STATUSES } from "../lib/labels";
import { Field, Select } from "./Field";

export const EMPTY_DECISION: DecisionInput = { title: "", context: "", alternatives: "", syner_recommendation: "", final_decision: "", owner_name: "", participants: "", decided_on: null, impact: "", status: "Proposed", initiative_id: null, meeting_id: null };

export function decisionToInput(d: Decision): DecisionInput {
  const { title, context, alternatives, syner_recommendation, final_decision, owner_name, participants, decided_on, impact, status, initiative_id, meeting_id } = d;
  return { title, context, alternatives, syner_recommendation, final_decision, owner_name, participants, decided_on, impact, status, initiative_id, meeting_id };
}

export function DecisionForm({ form, onChange, initiatives, meetings }: {
  form: DecisionInput;
  onChange: (next: DecisionInput) => void;
  initiatives: Initiative[];
  meetings?: Meeting[];
}) {
  const set = (key: keyof DecisionInput, value: unknown) => onChange({ ...form, [key]: value });
  const text = (key: keyof DecisionInput, label: string, rows = 2) => (
    <Field label={label}><textarea className="input" rows={rows} value={(form[key] as string) ?? ""} onChange={(e) => set(key, e.target.value)} /></Field>
  );
  return (
    <>
      <Field label="Decisión"><input className="input" value={form.title ?? ""} onChange={(e) => set("title", e.target.value)} required maxLength={200} /></Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Status"><Select value={form.status ?? "Proposed"} onChange={(v) => set("status", v)} options={DECISION_STATUSES} /></Field>
        <Field label="Fecha de decisión"><input className="input" type="date" value={form.decided_on ?? ""} onChange={(e) => set("decided_on", e.target.value || null)} /></Field>
        <Field label="Owner"><input className="input" value={form.owner_name ?? ""} onChange={(e) => set("owner_name", e.target.value)} maxLength={200} /></Field>
        <Field label="Initiative">
          <select className="input" value={form.initiative_id ?? ""} onChange={(e) => set("initiative_id", e.target.value || null)}>
            <option value="">Sin initiative</option>
            {initiatives.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
          </select>
        </Field>
        {meetings && (
          <Field label="Meeting">
            <select className="input" value={form.meeting_id ?? ""} onChange={(e) => set("meeting_id", e.target.value || null)}>
              <option value="">Sin meeting</option>
              {meetings.map((m) => <option key={m.id} value={m.id}>{m.title} · {formatDateTime(m.held_on)}</option>)}
            </select>
          </Field>
        )}
      </div>
      {text("context", "Contexto", 3)}
      {text("alternatives", "Alternativas", 3)}
      {text("syner_recommendation", "Recomendación Syner", 3)}
      {text("final_decision", "Decisión final")}
      {text("participants", "Participantes")}
      {text("impact", "Impacto")}
    </>
  );
}
```

- [ ] **Step 2: Página Decisions**

`frontend/src/pages/DecisionsPage.tsx`:

```tsx
import { FormEvent, useState } from "react";
import { errorMessage } from "../api/client";
import { decisionsApi, DecisionInput } from "../api/decisions";
import { initiativesApi } from "../api/initiatives";
import { meetingsApi } from "../api/meetings";
import { DataTable } from "../components/DataTable";
import { DecisionForm, EMPTY_DECISION, decisionToInput } from "../components/DecisionForm";
import { EmptyState } from "../components/EmptyState";
import { Select } from "../components/Field";
import { FormDrawer } from "../components/FormDrawer";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { useResource } from "../hooks/useResource";
import { formatDate } from "../lib/dates";
import { DECISION_STATUSES, RESOLUTION_STATUSES } from "../lib/labels";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";
import type { Decision, DecisionStatus } from "../types";

function Prose({ label, text }: { label: string; text: string }) {
  return (
    <div>
      <div className="label">{label}</div>
      <p className="whitespace-pre-line text-sm leading-6">{text || <span className="text-muted">Sin contenido.</span>}</p>
    </div>
  );
}

export function DecisionsPage() {
  const user = useAuthStore((s) => s.user);
  const engagementId = useEngagementStore((s) => s.current?.id ?? "");
  const [status, setStatus] = useState("");
  const { data, loading, error, reload } = useResource(() => decisionsApi.list(engagementId, { status: status || undefined }), [engagementId, status]);
  const initiatives = useResource(() => initiativesApi.list(engagementId), [engagementId]);
  const meetings = useResource(() => meetingsApi.list(engagementId), [engagementId]);
  const writable = can(user, "write");
  const approver = can(user, "approveDecision");
  const [selected, setSelected] = useState<Decision | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<DecisionInput>(EMPTY_DECISION);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  function openCreate() { setSelected(null); setForm(EMPTY_DECISION); setFormError(null); setOpen(true); }
  function openRow(d: Decision) {
    if (!writable && !approver) return;
    setSelected(d); setForm(decisionToInput(d)); setFormError(null); setOpen(true);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!writable) return;
    setBusy(true); setFormError(null);
    try {
      if (selected) await decisionsApi.update(selected.id, form);
      else await decisionsApi.create(engagementId, form);
      setOpen(false);
      await reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  async function resolve(next: DecisionStatus) {
    if (!selected) return;
    setBusy(true); setFormError(null);
    try {
      await decisionsApi.update(selected.id, { status: next });
      setOpen(false);
      await reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  const initiativeName = (id: string | null) => initiatives.data?.items.find((i) => i.id === id)?.name ?? "—";
  const pending = !!selected && (selected.status === "Proposed" || selected.status === "Under Review");
  const resolutionButtons = selected && approver && pending && (
    <>
      {RESOLUTION_STATUSES.map((s) => (
        <button key={s} type="button" className={`btn ${s === "Approved" ? "btn-primary" : ""}`} disabled={busy} onClick={() => resolve(s)}>{s}</button>
      ))}
    </>
  );

  return (
    <>
      <PageHeader title="Decision Log" subtitle="Decisiones estratégicas con contexto, alternativas y recomendación Syner" action={writable && <button className="btn btn-primary" onClick={openCreate}>Nueva decision</button>} />
      <div className="mb-4 w-48"><Select value={status} onChange={setStatus} options={DECISION_STATUSES} allowEmpty="Todos los estados" /></div>
      {error && <p className="mb-4 text-sm text-danger">{error}</p>}
      {loading && !data ? <p className="text-sm text-muted">Cargando…</p> : (
        <DataTable<Decision>
          rows={data?.items ?? []}
          onRowClick={writable || approver ? openRow : undefined}
          empty={<EmptyState title="Sin decisiones registradas" hint={writable ? "Registra la primera decisión del engagement." : undefined} />}
          columns={[
            { key: "title", header: "Decision", render: (d) => <span className="font-medium">{d.title}<span className="block text-xs text-muted">{initiativeName(d.initiative_id)}</span></span> },
            { key: "owner", header: "Owner", render: (d) => d.owner_name || "—" },
            { key: "status", header: "Status", render: (d) => <StatusBadge value={d.status} /> },
            { key: "decided", header: "Decidida", render: (d) => formatDate(d.decided_on), className: "tabular-nums" },
          ]}
        />
      )}
      <FormDrawer
        open={open}
        title={selected ? (writable ? "Editar decision" : "Decision") : "Nueva decision"}
        onClose={() => setOpen(false)}
        onSubmit={submit}
        submitting={busy}
        error={formError}
        hideSubmit={!writable}
        footer={resolutionButtons}
      >
        {writable ? (
          <DecisionForm form={form} onChange={setForm} initiatives={initiatives.data?.items ?? []} meetings={meetings.data?.items ?? []} />
        ) : selected && (
          <div className="space-y-4">
            <div>
              <h3 className="text-base font-semibold">{selected.title}</h3>
              <div className="mt-1 flex items-center gap-2 text-xs text-muted"><StatusBadge value={selected.status} /><span>Owner: {selected.owner_name || "—"}</span></div>
            </div>
            <Prose label="Contexto" text={selected.context} />
            <Prose label="Alternativas" text={selected.alternatives} />
            <Prose label="Recomendación Syner" text={selected.syner_recommendation} />
            <Prose label="Decisión final" text={selected.final_decision} />
            <Prose label="Impacto" text={selected.impact} />
          </div>
        )}
      </FormDrawer>
    </>
  );
}
```

En `frontend/src/router.tsx`: importar `DecisionsPage` y reemplazar la ruta `/decisions` por `{ path: "/decisions", element: <DecisionsPage /> }`.

- [ ] **Step 3: Dashboard: Decisions Required**

En `frontend/src/pages/DashboardPage.tsx`, reemplazar la sección `Decisions Required` por:

```tsx
        <Section title="Decisions Required">
          {data.decisions_required.length === 0 ? (
            <p className="text-sm text-muted">Sin decisiones pendientes de aprobación.</p>
          ) : (
            <ul className="space-y-2">
              {data.decisions_required.map((d) => (
                <li key={d.id} className="flex items-start justify-between gap-3 text-sm">
                  <Link to="/decisions" className="hover:underline">{d.title}<span className="block text-xs text-muted">{d.owner_name || "Sin owner"}</span></Link>
                  <StatusBadge value={d.status} />
                </li>
              ))}
            </ul>
          )}
        </Section>
```

- [ ] **Step 4: Build y verificación manual**

```bash
cd /mnt/d/Devs/HiTOxSyner/frontend && npm run build
```
Expected: sin errores. Manual: como `admin@syner.demo` crear una decision "Proposed"; como `exec@hito.demo` abrirla desde Decisions (drawer de solo lectura con botones Approved/Rejected/Deferred, sin "Guardar"), aprobarla y ver que desaparece de "Decisions Required" del dashboard y el tile baja. Como `collab@hito.demo` la fila no abre drawer.

- [ ] **Step 5: Commit**

```bash
cd /mnt/d/Devs/HiTOxSyner
git add frontend
git commit -m "feat(frontend): decision log con aprobación ejecutiva y Decisions Required en dashboard"
```

---

### Task 9: Frontend: Meetings (lista) y Meeting Detail con registro de decisiones y acciones

**Files:**
- Create: `frontend/src/components/ActionForm.tsx`, `frontend/src/pages/MeetingsPage.tsx`, `frontend/src/pages/MeetingDetailPage.tsx`
- Modify: `frontend/src/router.tsx`

**Interfaces:**
- Consumes: `DecisionForm`, `EMPTY_DECISION` (Task 8); `meetingsApi`, `toDateTimeInput`, `fromDateTimeInput` (Task 7).
- Produces: `ActionForm({ form, onChange, users, initiatives })`, `EMPTY_ACTION`; rutas `/meetings`, `/meetings/:id`. Task 11 añade comentarios al detalle.

- [ ] **Step 1: Formulario de action reutilizable**

`frontend/src/components/ActionForm.tsx`:

```tsx
import type { ActionInput } from "../api/actions";
import type { Initiative, User } from "../types";
import { LEVELS } from "../lib/labels";
import { Field, Select } from "./Field";

export const EMPTY_ACTION: ActionInput = { title: "", description: "", owner_name: "", owner_user_id: null, organization_side: "CLIENT", initiative_id: null, due_date: null, priority: "Medium", status: "Open", evidence: "" };

export function ActionForm({ form, onChange, users, initiatives }: {
  form: ActionInput;
  onChange: (next: ActionInput) => void;
  users: User[];
  initiatives: Initiative[];
}) {
  const set = (key: keyof ActionInput, value: unknown) => onChange({ ...form, [key]: value });
  return (
    <>
      <Field label="Acción"><input className="input" value={form.title ?? ""} onChange={(e) => set("title", e.target.value)} required maxLength={200} /></Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Responsable (usuario)">
          <select className="input" value={form.owner_user_id ?? ""} onChange={(e) => set("owner_user_id", e.target.value || null)}>
            <option value="">Sin usuario</option>
            {users.map((u) => <option key={u.id} value={u.id}>{u.full_name}</option>)}
          </select>
        </Field>
        {!form.owner_user_id && (
          <Field label="Responsable (nombre)"><input className="input" value={form.owner_name ?? ""} onChange={(e) => set("owner_name", e.target.value)} maxLength={200} /></Field>
        )}
        <Field label="Organización"><Select value={form.organization_side ?? "CLIENT"} onChange={(v) => set("organization_side", v)} options={["CLIENT", "SYNER"]} /></Field>
        <Field label="Initiative">
          <select className="input" value={form.initiative_id ?? ""} onChange={(e) => set("initiative_id", e.target.value || null)}>
            <option value="">Sin initiative</option>
            {initiatives.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
          </select>
        </Field>
        <Field label="Fecha compromiso"><input className="input" type="date" value={form.due_date ?? ""} onChange={(e) => set("due_date", e.target.value || null)} /></Field>
        <Field label="Priority"><Select value={form.priority ?? "Medium"} onChange={(v) => set("priority", v)} options={LEVELS} /></Field>
      </div>
      <Field label="Descripción"><textarea className="input" rows={3} value={form.description ?? ""} onChange={(e) => set("description", e.target.value)} /></Field>
    </>
  );
}
```

- [ ] **Step 2: Página Meetings**

`frontend/src/pages/MeetingsPage.tsx`:

```tsx
import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { errorMessage } from "../api/client";
import { meetingsApi, MeetingInput } from "../api/meetings";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { Field } from "../components/Field";
import { FormDrawer } from "../components/FormDrawer";
import { PageHeader } from "../components/PageHeader";
import { useResource } from "../hooks/useResource";
import { formatDateTime, fromDateTimeInput, toDateTimeInput } from "../lib/dates";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";
import type { Meeting } from "../types";

export const EMPTY_MEETING: MeetingInput = { title: "", held_on: "", participants: "", objective: "", summary: "", discussion: "", next_steps: "" };

export function MeetingForm({ form, onChange }: { form: MeetingInput; onChange: (next: MeetingInput) => void }) {
  const set = (key: keyof MeetingInput, value: unknown) => onChange({ ...form, [key]: value });
  const text = (key: keyof MeetingInput, label: string, rows = 3) => (
    <Field label={label}><textarea className="input" rows={rows} value={(form[key] as string) ?? ""} onChange={(e) => set(key, e.target.value)} /></Field>
  );
  return (
    <>
      <Field label="Título"><input className="input" value={form.title ?? ""} onChange={(e) => set("title", e.target.value)} required maxLength={200} /></Field>
      <Field label="Fecha y hora">
        <input className="input" type="datetime-local" required value={toDateTimeInput(form.held_on)} onChange={(e) => set("held_on", e.target.value ? fromDateTimeInput(e.target.value) : "")} />
      </Field>
      {text("participants", "Participantes", 2)}
      {text("objective", "Objetivo", 2)}
      {text("summary", "Resumen")}
      {text("discussion", "Discusión", 5)}
      {text("next_steps", "Next steps")}
    </>
  );
}

export function MeetingsPage() {
  const user = useAuthStore((s) => s.user);
  const engagementId = useEngagementStore((s) => s.current?.id ?? "");
  const navigate = useNavigate();
  const { data, loading, error, reload } = useResource(() => meetingsApi.list(engagementId), [engagementId]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<MeetingInput>(EMPTY_MEETING);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const writable = can(user, "write");

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    try {
      const created = await meetingsApi.create(engagementId, form);
      setOpen(false); setForm(EMPTY_MEETING);
      await reload();
      navigate(`/meetings/${created.id}`);
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  return (
    <>
      <PageHeader title="Meetings" subtitle="Minutas, acuerdos y siguientes pasos" action={writable && <button className="btn btn-primary" onClick={() => { setForm(EMPTY_MEETING); setFormError(null); setOpen(true); }}>Nueva meeting</button>} />
      {error && <p className="mb-4 text-sm text-danger">{error}</p>}
      {loading && !data ? <p className="text-sm text-muted">Cargando…</p> : (
        <DataTable<Meeting>
          rows={data?.items ?? []}
          onRowClick={(m) => navigate(`/meetings/${m.id}`)}
          empty={<EmptyState title="Sin reuniones registradas" hint={writable ? "Registra la primera reunión del engagement." : undefined} />}
          columns={[
            { key: "title", header: "Meeting", render: (m) => <span className="font-medium">{m.title}<span className="block text-xs text-muted">{m.objective || "—"}</span></span> },
            { key: "held", header: "Fecha", render: (m) => formatDateTime(m.held_on), className: "tabular-nums" },
            { key: "participants", header: "Participantes", render: (m) => <span className="text-muted">{m.participants || "—"}</span> },
          ]}
        />
      )}
      <FormDrawer open={open} title="Nueva meeting" onClose={() => setOpen(false)} onSubmit={submit} submitting={busy} error={formError}>
        <MeetingForm form={form} onChange={setForm} />
      </FormDrawer>
    </>
  );
}
```

- [ ] **Step 3: Página Meeting Detail**

`frontend/src/pages/MeetingDetailPage.tsx`:

```tsx
import { FormEvent, useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import { ActionInput } from "../api/actions";
import { errorMessage } from "../api/client";
import { DecisionInput } from "../api/decisions";
import { engagementsApi } from "../api/engagements";
import { initiativesApi } from "../api/initiatives";
import { meetingsApi, MeetingInput } from "../api/meetings";
import { ActionForm, EMPTY_ACTION } from "../components/ActionForm";
import { DecisionForm, EMPTY_DECISION } from "../components/DecisionForm";
import { EmptyState } from "../components/EmptyState";
import { FormDrawer } from "../components/FormDrawer";
import { StatusBadge } from "../components/StatusBadge";
import { useResource } from "../hooks/useResource";
import { formatDate, formatDateTime } from "../lib/dates";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";
import { MeetingForm } from "./MeetingsPage";

type Drawer = "none" | "edit" | "decision" | "action";

function Block({ title, children, action }: { title: string; children: ReactNode; action?: ReactNode }) {
  return (
    <section className="card p-5">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">{title}</h2>
        {action}
      </div>
      {children}
    </section>
  );
}

function Prose({ text }: { text: string }) {
  return <p className="whitespace-pre-line text-sm leading-6">{text || <span className="text-muted">Sin contenido.</span>}</p>;
}

export function MeetingDetailPage() {
  const { id = "" } = useParams();
  const user = useAuthStore((s) => s.user);
  const engagementId = useEngagementStore((s) => s.current?.id ?? "");
  const { data, loading, error, reload } = useResource(() => meetingsApi.detail(id), [id]);
  const writable = can(user, "write");
  const initiatives = useResource(() => initiativesApi.list(engagementId), [engagementId]);
  const users = useResource(() => (writable ? engagementsApi.users(engagementId) : Promise.resolve([])), [engagementId, writable]);
  const [drawer, setDrawer] = useState<Drawer>("none");
  const [meetingForm, setMeetingForm] = useState<MeetingInput>({});
  const [decisionForm, setDecisionForm] = useState<DecisionInput>(EMPTY_DECISION);
  const [actionForm, setActionForm] = useState<ActionInput>(EMPTY_ACTION);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  if (loading && !data) return <p className="text-sm text-muted">Cargando…</p>;
  if (error || !data) return <EmptyState title="Meeting no encontrada" hint={error ?? undefined} />;
  const m = data.meeting;

  function openDrawer(kind: Drawer) {
    if (kind === "edit") setMeetingForm({ title: m.title, held_on: m.held_on, participants: m.participants, objective: m.objective, summary: m.summary, discussion: m.discussion, next_steps: m.next_steps });
    if (kind === "decision") setDecisionForm(EMPTY_DECISION);
    if (kind === "action") setActionForm(EMPTY_ACTION);
    setFormError(null); setDrawer(kind);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    try {
      if (drawer === "edit") await meetingsApi.update(id, meetingForm);
      if (drawer === "decision") await meetingsApi.createDecision(id, decisionForm);
      if (drawer === "action") await meetingsApi.createAction(id, actionForm);
      setDrawer("none");
      await reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  const titles: Record<Drawer, string> = { none: "", edit: "Editar meeting", decision: "Registrar decisión", action: "Registrar acción" };

  return (
    <div className="space-y-6">
      <div className="card p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <Link to="/meetings" className="text-xs text-muted hover:underline">← Meetings</Link>
            <h1 className="mt-1 text-xl font-semibold tracking-tight">{m.title}</h1>
            <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-muted">
              <span className="tabular-nums">{formatDateTime(m.held_on)}</span>
              <span>Participantes: {m.participants || "—"}</span>
            </div>
          </div>
          {writable && <button className="btn" onClick={() => openDrawer("edit")}>Editar</button>}
        </div>
        {m.objective && <p className="mt-4 text-sm leading-6"><span className="font-medium">Objetivo: </span>{m.objective}</p>}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Block title="Summary"><Prose text={m.summary} /></Block>
        <Block title="Discussion"><Prose text={m.discussion} /></Block>
        <Block title="Decisions" action={writable && <button className="btn" onClick={() => openDrawer("decision")}>Registrar decisión</button>}>
          {data.decisions.length === 0 ? <p className="text-sm text-muted">Sin decisiones registradas en esta reunión.</p> : (
            <ul className="space-y-2">
              {data.decisions.map((d) => (
                <li key={d.id} className="flex items-start justify-between gap-3 text-sm">
                  <Link to="/decisions" className="hover:underline">{d.title}<span className="block text-xs text-muted">{d.owner_name || "Sin owner"}</span></Link>
                  <StatusBadge value={d.status} />
                </li>
              ))}
            </ul>
          )}
        </Block>
        <Block title="Action Items" action={writable && <button className="btn" onClick={() => openDrawer("action")}>Registrar acción</button>}>
          {data.actions.length === 0 ? <p className="text-sm text-muted">Sin acciones derivadas.</p> : (
            <ul className="space-y-2">
              {data.actions.map((a) => (
                <li key={a.id} className="flex items-start justify-between gap-3 text-sm">
                  <span>{a.title}<span className="block text-xs text-muted">{a.owner_name || "Sin responsable"} · {formatDate(a.due_date)}</span></span>
                  <StatusBadge value={a.status} />
                </li>
              ))}
            </ul>
          )}
        </Block>
        <Block title="Next Steps"><Prose text={m.next_steps} /></Block>
      </div>

      <FormDrawer open={drawer !== "none"} title={titles[drawer]} onClose={() => setDrawer("none")} onSubmit={submit} submitting={busy} error={formError}>
        {drawer === "edit" && <MeetingForm form={meetingForm} onChange={setMeetingForm} />}
        {drawer === "decision" && <DecisionForm form={decisionForm} onChange={setDecisionForm} initiatives={initiatives.data?.items ?? []} />}
        {drawer === "action" && <ActionForm form={actionForm} onChange={setActionForm} users={users.data ?? []} initiatives={initiatives.data?.items ?? []} />}
      </FormDrawer>
    </div>
  );
}
```

En `frontend/src/router.tsx`: importar `MeetingsPage` y `MeetingDetailPage`; reemplazar la ruta `/meetings` por `{ path: "/meetings", element: <MeetingsPage /> }` y añadir `{ path: "/meetings/:id", element: <MeetingDetailPage /> }` justo después.

- [ ] **Step 4: Build y verificación manual**

```bash
cd /mnt/d/Devs/HiTOxSyner/frontend && npm run build
```
Expected: sin errores. Manual: como Syner crear una meeting (la fecha se guarda y se muestra en hora local), entrar al detalle, "Registrar decisión" y "Registrar acción"; ambas aparecen en el detalle, la decision en Decisions y la action en Actions. Como exec/collab se ve el detalle sin botones.

- [ ] **Step 5: Commit**

```bash
cd /mnt/d/Devs/HiTOxSyner
git add frontend
git commit -m "feat(frontend): meetings con detalle y registro de decisiones y acciones derivadas"
```

---

### Task 10: Frontend: página Documents

**Files:**
- Create: `frontend/src/pages/DocumentsPage.tsx`
- Modify: `frontend/src/router.tsx`

**Interfaces:**
- Consumes: `documentsApi`, `DocumentInput`, `DOCUMENT_CATEGORIES`, `ENTITY_LABELS` (Task 7).

- [ ] **Step 1: Página Documents**

`frontend/src/pages/DocumentsPage.tsx`:

```tsx
import { FormEvent, useState } from "react";
import { errorMessage } from "../api/client";
import { documentsApi, DocumentInput } from "../api/documents";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { Field, Select } from "../components/Field";
import { FormDrawer } from "../components/FormDrawer";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { useResource } from "../hooks/useResource";
import { formatDate } from "../lib/dates";
import { DOCUMENT_CATEGORIES, ENTITY_LABELS } from "../lib/labels";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";
import type { Document } from "../types";

const EMPTY: DocumentInput = { name: "", description: "", category: "Discovery", version: "", url: "", doc_date: null, tags: [], internal_only: false };

function parseTags(value: string): string[] {
  return value.split(",").map((t) => t.trim()).filter(Boolean).slice(0, 20);
}

export function DocumentsPage() {
  const user = useAuthStore((s) => s.user);
  const engagementId = useEngagementStore((s) => s.current?.id ?? "");
  const [category, setCategory] = useState("");
  const { data, loading, error, reload } = useResource(() => documentsApi.list(engagementId, { category: category || undefined }), [engagementId, category]);
  const writable = can(user, "write");
  const [editing, setEditing] = useState<Document | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<DocumentInput>(EMPTY);
  const [tagsText, setTagsText] = useState("");
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  function openCreate() { setEditing(null); setForm(EMPTY); setTagsText(""); setFormError(null); setOpen(true); }
  function openEdit(d: Document) {
    if (!writable) return;
    setEditing(d);
    setForm({ name: d.name, description: d.description, category: d.category, version: d.version, url: d.url, doc_date: d.doc_date, tags: d.tags, internal_only: d.internal_only });
    setTagsText(d.tags.join(", "));
    setFormError(null); setOpen(true);
  }
  const set = (key: keyof DocumentInput, value: unknown) => setForm((f) => ({ ...f, [key]: value }));

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    const payload = { ...form, tags: parseTags(tagsText) };
    try {
      if (editing) await documentsApi.update(editing.id, payload);
      else await documentsApi.create(engagementId, payload);
      setOpen(false);
      await reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  return (
    <>
      <PageHeader title="Documents" subtitle="Repositorio del engagement: entregables, evidencia y minutas" action={writable && <button className="btn btn-primary" onClick={openCreate}>Nuevo documento</button>} />
      <div className="mb-4 w-48"><Select value={category} onChange={setCategory} options={DOCUMENT_CATEGORIES} allowEmpty="Todas las categorías" /></div>
      {error && <p className="mb-4 text-sm text-danger">{error}</p>}
      {loading && !data ? <p className="text-sm text-muted">Cargando…</p> : (
        <DataTable<Document>
          rows={data?.items ?? []}
          onRowClick={writable ? openEdit : undefined}
          empty={<EmptyState title="Sin documentos" hint={writable ? "Registra el primer documento del engagement." : undefined} />}
          columns={[
            { key: "name", header: "Documento", render: (d) => (
              <span className="font-medium">
                {d.url ? <a href={d.url} target="_blank" rel="noreferrer" className="hover:underline" onClick={(e) => e.stopPropagation()}>{d.name}</a> : d.name}
                <span className="block text-xs text-muted">{d.category}{d.version ? ` · v${d.version}` : ""}</span>
              </span>
            ) },
            { key: "date", header: "Fecha", render: (d) => formatDate(d.doc_date), className: "tabular-nums" },
            { key: "tags", header: "Tags", render: (d) => <span className="text-xs text-muted">{d.tags.join(", ") || "—"}</span> },
            { key: "links", header: "Vinculado a", render: (d) => <span className="text-xs text-muted">{d.links.length === 0 ? "—" : d.links.map((l) => ENTITY_LABELS[l.entity_type] ?? l.entity_type).join(", ")}</span> },
            { key: "visibility", header: "Visibilidad", render: (d) => d.internal_only ? <StatusBadge value="Interno" /> : <span className="text-xs text-muted">Compartido</span> },
          ]}
        />
      )}
      <FormDrawer open={open} title={editing ? "Editar documento" : "Nuevo documento"} onClose={() => setOpen(false)} onSubmit={submit} submitting={busy} error={formError}>
        <Field label="Nombre"><input className="input" value={form.name ?? ""} onChange={(e) => set("name", e.target.value)} required maxLength={200} /></Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Categoría"><Select value={form.category ?? "Discovery"} onChange={(v) => set("category", v)} options={DOCUMENT_CATEGORIES} /></Field>
          <Field label="Versión"><input className="input" value={form.version ?? ""} onChange={(e) => set("version", e.target.value)} maxLength={50} /></Field>
          <Field label="Fecha del documento"><input className="input" type="date" value={form.doc_date ?? ""} onChange={(e) => set("doc_date", e.target.value || null)} /></Field>
          <Field label="Visibilidad">
            <Select value={form.internal_only ? "Solo Syner" : "Compartido con el cliente"} onChange={(v) => set("internal_only", v === "Solo Syner")} options={["Compartido con el cliente", "Solo Syner"]} />
          </Field>
        </div>
        <Field label="URL"><input className="input" type="url" value={form.url ?? ""} onChange={(e) => set("url", e.target.value)} maxLength={2000} placeholder="https://" /></Field>
        <Field label="Tags (separados por coma)"><input className="input" value={tagsText} onChange={(e) => setTagsText(e.target.value)} /></Field>
        <Field label="Descripción"><textarea className="input" rows={3} value={form.description ?? ""} onChange={(e) => set("description", e.target.value)} /></Field>
      </FormDrawer>
    </>
  );
}
```

En `frontend/src/router.tsx`: importar `DocumentsPage` y reemplazar la ruta `/documents` por `{ path: "/documents", element: <DocumentsPage /> }`.

- [ ] **Step 2: Build y verificación manual**

```bash
cd /mnt/d/Devs/HiTOxSyner/frontend && npm run build
```
Expected: sin errores. Manual: como Syner ver los 5 documentos del seed (uno con badge "Interno"), crear uno con tags "a, b" y URL; como `collab@hito.demo` ver solo 4 (sin el interno); el nombre con URL abre en pestaña nueva sin abrir el drawer.

- [ ] **Step 3: Commit**

```bash
cd /mnt/d/Devs/HiTOxSyner
git add frontend
git commit -m "feat(frontend): página de documents con categorías, tags y visibilidad interna"
```

---

### Task 11: Frontend: Comments y Initiative Detail completo (milestones, decisions, documents vinculados)

**Files:**
- Create: `frontend/src/components/Comments.tsx`
- Modify: `frontend/src/pages/InitiativeDetailPage.tsx`, `frontend/src/pages/MeetingDetailPage.tsx`, `frontend/src/components/Sidebar.tsx` (sin cambios funcionales: verificar que los NAV_ITEMS ya apuntan a páginas reales)

**Interfaces:**
- Produces: `Comments({ entityType, entityId })`.

- [ ] **Step 1: Componente Comments**

`frontend/src/components/Comments.tsx`:

```tsx
import { FormEvent, useState } from "react";
import { errorMessage } from "../api/client";
import { commentsApi } from "../api/comments";
import { useResource } from "../hooks/useResource";
import { formatDateTime } from "../lib/dates";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";

export function Comments({ entityType, entityId }: { entityType: string; entityId: string }) {
  const user = useAuthStore((s) => s.user);
  const engagementId = useEngagementStore((s) => s.current?.id ?? "");
  const { data, loading, error, reload } = useResource(() => commentsApi.list(engagementId, entityType, entityId), [engagementId, entityType, entityId]);
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!body.trim()) return;
    setBusy(true); setSendError(null);
    try {
      await commentsApi.create(engagementId, { entity_type: entityType, entity_id: entityId, body: body.trim() });
      setBody("");
      await reload();
    } catch (err) { setSendError(errorMessage(err)); } finally { setBusy(false); }
  }

  return (
    <section className="card p-5">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">Comments</h2>
      {error && <p className="mb-3 text-sm text-danger">{error}</p>}
      {loading && !data ? <p className="text-sm text-muted">Cargando…</p> : (data?.items.length ?? 0) === 0 ? (
        <p className="text-sm text-muted">Sin comentarios.</p>
      ) : (
        <ul className="space-y-3">
          {data?.items.map((c) => (
            <li key={c.id} className="text-sm">
              <div className="flex items-baseline justify-between gap-3">
                <span className="font-medium">{c.author_name}</span>
                <span className="text-xs tabular-nums text-muted">{formatDateTime(c.created_at)}</span>
              </div>
              <p className="whitespace-pre-line leading-6">{c.body}</p>
            </li>
          ))}
        </ul>
      )}
      {can(user, "comment") && (
        <form onSubmit={submit} className="mt-4 space-y-2">
          <textarea className="input" rows={2} value={body} onChange={(e) => setBody(e.target.value)} placeholder="Escribe un comentario…" maxLength={10000} />
          {sendError && <p className="text-sm text-danger">{sendError}</p>}
          <div className="flex justify-end"><button type="submit" className="btn btn-primary" disabled={busy || !body.trim()}>Comentar</button></div>
        </form>
      )}
    </section>
  );
}
```

- [ ] **Step 2: Initiative Detail con milestones, decisions, documents vinculados y comments**

Reemplazar `frontend/src/pages/InitiativeDetailPage.tsx` completo:

```tsx
import { FormEvent, useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import { errorMessage } from "../api/client";
import { documentsApi } from "../api/documents";
import { initiativesApi, InitiativeInput } from "../api/initiatives";
import { Comments } from "../components/Comments";
import { EmptyState } from "../components/EmptyState";
import { FormDrawer } from "../components/FormDrawer";
import { InitiativeForm, initiativeToInput } from "../components/InitiativeForm";
import { ProgressBar } from "../components/ProgressBar";
import { StatusBadge } from "../components/StatusBadge";
import { useResource } from "../hooks/useResource";
import { formatDate, formatDateTime } from "../lib/dates";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";

function Block({ title, children, action }: { title: string; children: ReactNode; action?: ReactNode }) {
  return (
    <section className="card p-5">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">{title}</h2>
        {action}
      </div>
      {children}
    </section>
  );
}

function Prose({ text }: { text: string }) {
  return <p className="whitespace-pre-line text-sm leading-6">{text || <span className="text-muted">Sin contenido.</span>}</p>;
}

export function InitiativeDetailPage() {
  const { id = "" } = useParams();
  const user = useAuthStore((s) => s.user);
  const engagementId = useEngagementStore((s) => s.current?.id ?? "");
  const { data, loading, error, reload } = useResource(() => initiativesApi.detail(id), [id]);
  const writable = can(user, "write");
  const allDocuments = useResource(() => (writable ? documentsApi.list(engagementId) : Promise.resolve(null)), [engagementId, writable]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<InitiativeInput>({});
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [linkId, setLinkId] = useState("");
  const [linkError, setLinkError] = useState<string | null>(null);

  if (loading && !data) return <p className="text-sm text-muted">Cargando…</p>;
  if (error || !data) return <EmptyState title="Initiative no encontrada" hint={error ?? undefined} />;
  const i = data.initiative;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    try {
      await initiativesApi.update(id, form);
      setOpen(false);
      await reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  async function link() {
    if (!linkId) return;
    setLinkError(null);
    try {
      await documentsApi.addLink(linkId, { entity_type: "initiative", entity_id: id });
      setLinkId("");
      await Promise.all([reload(), allDocuments.reload()]);
    } catch (err) { setLinkError(errorMessage(err)); }
  }

  async function unlink(documentId: string) {
    const doc = data?.documents.find((d) => d.id === documentId);
    const docLink = doc?.links.find((l) => l.entity_type === "initiative" && l.entity_id === id);
    if (!docLink) return;
    setLinkError(null);
    try {
      await documentsApi.removeLink(documentId, docLink.id);
      await Promise.all([reload(), allDocuments.reload()]);
    } catch (err) { setLinkError(errorMessage(err)); }
  }

  const linkedIds = new Set(data.documents.map((d) => d.id));
  const linkable = allDocuments.data?.items.filter((d) => !linkedIds.has(d.id)) ?? [];

  return (
    <div className="space-y-6">
      <div className="card p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <Link to="/initiatives" className="text-xs text-muted hover:underline">← Initiatives</Link>
            <h1 className="mt-1 text-xl font-semibold tracking-tight">{i.name}</h1>
            <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-muted">
              <StatusBadge value={i.status} />
              <StatusBadge value={i.priority} />
              <span>Owner HiTO: {i.hito_owner || "—"}</span>
              <span>Target: {formatDate(i.target_date)}</span>
            </div>
          </div>
          {writable && <button className="btn" onClick={() => { setForm(initiativeToInput(i)); setFormError(null); setOpen(true); }}>Editar</button>}
        </div>
        <div className="mt-4 flex items-center gap-3">
          <ProgressBar value={i.progress_pct} />
          <span className="text-sm tabular-nums">{i.progress_pct}%</span>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Block title="Objective"><Prose text={i.objective} /></Block>
        <Block title="Expected Outcome"><Prose text={i.expected_outcome} /></Block>
        <Block title="Milestones" action={<Link to="/roadmap" className="text-xs text-muted hover:underline">Roadmap →</Link>}>
          {data.milestones.length === 0 ? <p className="text-sm text-muted">Sin milestones vinculados.</p> : (
            <ul className="space-y-2">
              {data.milestones.map((m) => (
                <li key={m.id} className="flex items-start justify-between gap-3 text-sm">
                  <span>{m.name}<span className="block text-xs text-muted">{m.phase} · {formatDate(m.due_date)}</span></span>
                  <StatusBadge value={m.status} />
                </li>
              ))}
            </ul>
          )}
        </Block>
        <Block title="Actions" action={<Link to="/actions" className="text-xs text-muted hover:underline">Actions →</Link>}>
          {data.actions.length === 0 ? <p className="text-sm text-muted">Sin acciones vinculadas.</p> : (
            <ul className="space-y-2">
              {data.actions.map((a) => (
                <li key={a.id} className="flex items-start justify-between gap-3 text-sm">
                  <span>{a.title}<span className="block text-xs text-muted">{a.owner_name || "Sin responsable"} · {formatDate(a.due_date)}</span></span>
                  <StatusBadge value={a.status} />
                </li>
              ))}
            </ul>
          )}
        </Block>
        <Block title="Decisions" action={<Link to="/decisions" className="text-xs text-muted hover:underline">Decision Log →</Link>}>
          {data.decisions.length === 0 ? <p className="text-sm text-muted">Sin decisiones vinculadas.</p> : (
            <ul className="space-y-2">
              {data.decisions.map((d) => (
                <li key={d.id} className="flex items-start justify-between gap-3 text-sm">
                  <span>{d.title}<span className="block text-xs text-muted">{d.owner_name || "Sin owner"} · {formatDate(d.decided_on)}</span></span>
                  <StatusBadge value={d.status} />
                </li>
              ))}
            </ul>
          )}
        </Block>
        <Block title="Risks"><Prose text={i.risks} /></Block>
        <Block title="Findings origen">
          {data.findings.length === 0 ? <p className="text-sm text-muted">Esta iniciativa no proviene de un finding.</p> : (
            <ul className="space-y-2">
              {data.findings.map((f) => (
                <li key={f.id} className="flex items-start justify-between gap-3 text-sm"><span>{f.title}</span><StatusBadge value={f.impact} /></li>
              ))}
            </ul>
          )}
        </Block>
        <Block title="Documents">
          {data.documents.length === 0 ? <p className="text-sm text-muted">Sin documentos vinculados.</p> : (
            <ul className="space-y-2">
              {data.documents.map((d) => (
                <li key={d.id} className="flex items-start justify-between gap-3 text-sm">
                  <span>
                    {d.url ? <a href={d.url} target="_blank" rel="noreferrer" className="hover:underline">{d.name}</a> : d.name}
                    <span className="block text-xs text-muted">{d.category}{d.version ? ` · v${d.version}` : ""}{d.internal_only ? " · Interno" : ""}</span>
                  </span>
                  {writable && <button className="btn text-xs" onClick={() => unlink(d.id)}>Quitar</button>}
                </li>
              ))}
            </ul>
          )}
          {writable && (
            <div className="mt-3 flex gap-2">
              <select className="input" value={linkId} onChange={(e) => setLinkId(e.target.value)}>
                <option value="">Vincular documento…</option>
                {linkable.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
              <button className="btn" onClick={link} disabled={!linkId}>Vincular</button>
            </div>
          )}
          {linkError && <p className="mt-2 text-sm text-danger">{linkError}</p>}
        </Block>
        <Block title="Activity">
          {data.activity.length === 0 ? <p className="text-sm text-muted">Sin actividad.</p> : (
            <ul className="space-y-2">
              {data.activity.map((a) => (
                <li key={a.id} className="text-sm">{a.summary}<span className="block text-xs text-muted">{formatDateTime(a.created_at)}</span></li>
              ))}
            </ul>
          )}
        </Block>
        <Comments entityType="initiative" entityId={id} />
      </div>

      <FormDrawer open={open} title="Editar initiative" onClose={() => setOpen(false)} onSubmit={submit} submitting={busy} error={formError}>
        <InitiativeForm form={form} onChange={setForm} />
      </FormDrawer>
    </div>
  );
}
```

- [ ] **Step 3: Comments en Meeting Detail**

En `frontend/src/pages/MeetingDetailPage.tsx`: añadir `import { Comments } from "../components/Comments";` y, dentro del `<div className="grid gap-6 lg:grid-cols-2">`, después de `<Block title="Next Steps">…</Block>`, añadir `<Comments entityType="meeting" entityId={id} />`.

- [ ] **Step 4: Build, typecheck y verificación manual**

```bash
cd /mnt/d/Devs/HiTOxSyner/frontend && npm run build
grep -n "ComingSoonPage" src/router.tsx
```
Expected: build sin errores; `ComingSoonPage` solo aparece en el import y en la ruta `/lab` (plan 3). Manual: en una initiative del seed se ven milestones, decisions y documentos vinculados; como Syner vincular un documento y quitarlo; como `collab@hito.demo` comentar en la initiative y ver el comentario; el comentario aparece en Activity del detalle (`… commented on Initiative "…"`).

- [ ] **Step 5: Commit**

```bash
cd /mnt/d/Devs/HiTOxSyner
git add frontend
git commit -m "feat(frontend): comments por entidad e initiative detail con milestones, decisions y documents"
```

---

### Task 12: Suite completa, PR, merge y despliegue en Railway

**Files:** ninguno nuevo. Verifica y despliega.

- [ ] **Step 1: Suite backend, build frontend y smoke local**

```bash
cd /mnt/d/Devs/HiTOxSyner
.venv/bin/pytest -q 2>&1 | tail -3
cd frontend && npm run build && cd ..
.venv/bin/uvicorn app.main:app --port 8010 &
sleep 3
curl -s localhost:8010/api/health
TOKEN=$(curl -s -X POST localhost:8010/api/auth/login -H 'content-type: application/json' -d '{"email":"admin@syner.demo","password":"syner-demo"}' | .venv/bin/python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
ENG=$(curl -s localhost:8010/api/engagements -H "Authorization: Bearer $TOKEN" | .venv/bin/python -c 'import json,sys; print(json.load(sys.stdin)[0]["id"])')
curl -s "localhost:8010/api/engagements/$ENG/dashboard" -H "Authorization: Bearer $TOKEN" | .venv/bin/python -c 'import json,sys; d=json.load(sys.stdin); print(d["tiles"], len(d["next_milestones"]), len(d["decisions_required"]))'
kill %1
```
Expected: `101 passed`; build OK; `{"status":"ok","database":"ok"}`; tiles con `decisions_required: 2`, `next_milestones` 5 y `decisions_required` 2 (datos del seed en dev). Si la password del seed en `.env` es otra, usar esa.

- [ ] **Step 2: Push y PR**

```bash
cd /mnt/d/Devs/HiTOxSyner
git push -u origin feat/plan-2-client-room
gh pr create --base docs/material-hito-syner --title "Plan 2 — Client room: milestones, meetings, decisions, comments, documents" --body "$(cat <<'EOF'
## Resumen
- Milestones con roadmap por fase (dashboard, página Roadmap, initiative detail).
- Meetings con detalle y acuerdos que crean actions y decisions con `meeting_id`.
- Decision log con aprobación ejecutiva (HITO_EXECUTIVE solo resuelve status); tile y lista "Decisions Required".
- Comments por entidad con activity trail.
- Documents con vínculos a entidades, `internal_only` oculto a HITO_COLLABORATOR, tags.
- Migración Alembic única, seed demo por módulo, README.

## Verificación
- `pytest`: 101 passed.
- `npm run build` en verde.
- Smoke local del dashboard con datos del seed.

Spec: docs/superpowers/specs/2026-10-11-transformation-room-design.md
Plan: docs/superpowers/plans/2026-10-16-plan-2-client-room-modules.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: Revisión y merge**

Pasar la revisión de la rama con `superpowers:requesting-code-review` (o la revisión final del flujo SDD). Corregir hallazgos en commits adicionales. Después:

```bash
cd /mnt/d/Devs/HiTOxSyner
gh pr merge --merge --delete-branch
git checkout docs/material-hito-syner && git pull --ff-only
```

- [ ] **Step 4: Despliegue en Railway**

Seguir las notas del README y de la memoria del proyecto (subir desde el filesystem nativo, nunca desde `/mnt/d`; siempre con `--service`, `--project` y `--environment` explícitos):

```bash
rsync -a --delete --exclude .venv --exclude node_modules --exclude .git --exclude frontend/dist --exclude .pytest_cache /mnt/d/Devs/HiTOxSyner/ ~/hitoxsyner-upload/
cd ~/hitoxsyner-upload
railway up --service HiTOxSyner --project 712a7fba-0fe2-4284-b4cd-edfb9c8990fb --environment production --detach
```
Esperar a que el deploy esté `SUCCESS` (`railway status` o el dashboard). El contenedor ejecuta `alembic upgrade head` al arrancar, así que la migración del plan 2 se aplica sola. Luego completar el seed de demo (idempotente por módulo; solo añade los datos nuevos):

```bash
cd ~/hitoxsyner-upload
railway ssh --service HiTOxSyner --project 712a7fba-0fe2-4284-b4cd-edfb9c8990fb --environment production -i ~/.ssh/id_railway_atlas -- python -m app.seed
curl -s https://hitoxsyner-production.up.railway.app/api/health
```
Expected: `Seed completado.` y `{"status":"ok","database":"ok"}`. Verificación manual en https://hitoxsyner-production.up.railway.app: login como Syner, Roadmap con 6 milestones, Decisions con 3, Meetings con 3 y detalle, Documents con 5; login como exec y aprobar la decision "Proposed".

- [ ] **Step 5: Actualizar la memoria del proyecto**

Actualizar `/home/ecamposg/.claude/projects/-mnt-d-Devs-HiTOxSyner/memory/hito-transformation-room-project.md` con: plan 2 completo y mergeado (número de PR, commit de merge), deployment verificado, y "Siguiente: plan 3 (Leadership Lab core, PDFs de ORION como Documents internos, DoD)".

---

## Verificación final del plan 2

- `pytest` en verde: 101 tests (65 del plan 1 + 36 nuevos).
- `npm run build` en verde; ninguna ruta del sidebar salvo `/lab` cae en `ComingSoonPage`.
- Alembic: `upgrade head` → `downgrade -1` → `upgrade head` reproducible en dev; aplicado en producción por el arranque del contenedor.
- Seed idempotente por módulo en dev y en producción.
- Matriz RBAC de la spec 5.3 cubierta por tests: clientes no escriben milestones/meetings/decisions/documents; exec solo resuelve decisions; collab no ve `internal_only`; todos comentan.
- Aislamiento por organización probado en cada listado nuevo y en cada `GET` por id.
- Desplegado en Railway con `/api/health` en verde y flujo manual verificado con los tres roles.
