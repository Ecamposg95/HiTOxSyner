# Transformation Room — Plan 3: Leadership Lab core, material ORION y cierre del Definition of Done

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar el módulo Leadership Lab "core" (sesiones, pods, participantes, CTA tracker, Leadership Action Contract y resumen agregado), registrar los PDFs de Project ORION como Documents internos, cerrar los minors diferidos de los planes 1 y 2 y verificar el Definition of Done del primer release en producción.

**Architecture:** Mismo servicio único FastAPI + React de los planes 1 y 2. El Lab es un módulo: `app/models/lab.py`, `app/schemas/lab.py`, `app/crud/lab.py`, `app/services/lab.py`, `app/routers/lab.py`. Toda entidad del Lab lleva `EngagementScopedMixin`; el acceso se resuelve con `get_engagement` y `scoped(Model, param)`; las referencias cruzadas se validan con un helper nuevo `require_in_engagement` en `app/services/links.py` que después reutilizan actions, decisions y milestones. Toda la actividad del Lab se escribe con `internal_only=True`: nombres de participantes y textos de CTAs solo los ve Syner. El resumen agregado (`/lab/summary`) y la tarjeta del dashboard son las únicas vistas del Lab para HITO_EXECUTIVE. Frontend: página `/lab` con pestañas para Syner y vista de resumen para dirección, componentes en `frontend/src/components/lab/`.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2, Pydantic v2, Alembic, PostgreSQL, pytest + httpx. React 18, TypeScript, Vite 5, React Router 6, Zustand 4, Axios, Tailwind 3. Railway + Docker multi-stage.

**Spec:** `docs/superpowers/specs/2026-10-11-transformation-room-design.md` (secciones 2 "Visibilidad del Lab", 4.4, 5.3, 5.4, 5.5, 5.7, 6.2, 6.4, 7, 8, 10). Planes anteriores (ya mergeados): `docs/superpowers/plans/2026-10-12-plan-1-foundation-vertical-slice.md`, `docs/superpowers/plans/2026-10-16-plan-2-client-room-modules.md`.

Este es el plan 3 de 3 del primer release.

## Global Constraints

- Rama de trabajo: `feat/plan-3-leadership-lab`, creada desde `docs/material-hito-syner` (rama default del remoto; no existe `main`). Al terminar se abre PR contra `docs/material-hito-syner`.
- Entorno: `.venv/bin/python`, `.venv/bin/pytest`, `.venv/bin/alembic` (venv ya creada). Postgres 16 local en espacio de usuario: si `~/.local/pg/bin/pg_isready -h localhost` falla, arrancar con `~/.local/pg/bin/pg_ctl -D ~/.local/pgdata -l ~/.local/pgdata/server.log -o "-p 5432 -k /tmp" start`. Bases `hitoxsyner_dev` (Alembic, seed, uvicorn) y `hitoxsyner_test` (pytest, esquema desde `Base.metadata.create_all`). `.env` ya existe y no se commitea. La sesión de Postgres corre en zona horaria America/Mexico_City: en tests compara fechas (`date`), nunca cadenas de datetime.
- La suite corre con `.venv/bin/pytest -q -W error`: ningún warning nuevo.
- Postgres es la única base soportada (UUID, enums nativos, ARRAY). No hay SQLite ni en tests.
- Todos los endpoints viven bajo `/api`. Listados paginados devuelven `{"items": [...], "total": n}` con `limit` default 50, máximo 200, `offset` default 0, usando `Page`, `Pagination`, `pagination_params` de `app/schemas/common.py`.
- Un PATCH con `null` explícito en un campo que no admite null responde 422 vía `updates(data, nullable=...)` de `app/schemas/common.py` (nunca 500).
- Referencias cruzadas (`pod_id`, `participant_id`, `session_id`, `cta_ids`, `initiative_id`, `meeting_id`) que apuntan a una entidad de otro engagement responden 422 con `{"detail": "<campo> no pertenece a este engagement"}`; nunca se revela la existencia de la entidad ajena con un 404 distinto. Helper único: `require_in_engagement(db, Model, entity_id, engagement, "campo")` en `app/services/links.py`.
- Duplicados de negocio (número de sesión o de pod repetido en el engagement, segundo contrato para un participante) responden 409 con detalle en español, comprobados en el service antes del `flush` (el handler global de `IntegrityError` devuelve 422 genérico y no debe ser la primera línea de defensa).
- Orden de dependencias en los routers del Lab: primero `get_engagement` o `scoped(...)`, después `require_roles(...)`. Así un usuario de otra organización recibe 404 y uno de la misma organización sin permiso recibe 403.
- RBAC del Lab (spec 5.3 y sección 7): sessions, pods, participants, ctas y contracts (listar, crear, editar) solo SYNER_ADMIN (403 para HITO_EXECUTIVE y HITO_COLLABORATOR). `GET /lab/summary`: SYNER_ADMIN y HITO_EXECUTIVE; HITO_COLLABORATOR 403. La tarjeta `lab` del dashboard es `null` para HITO_COLLABORATOR y cuando el engagement no tiene sesiones.
- `/lab/summary` y `dashboard.lab` nunca contienen las claves `participant`, `trigger`, `behavior`, `full_name` a ninguna profundidad, ni texto libre de CTAs, ni nombres de participantes. Los pods aparecen solo con `pod_number` y `pod_name`.
- Activity trail: todo `log_activity` del Lab lleva `internal_only=True`. Summaries en inglés con el formato de los planes anteriores: `{user.full_name} created Lab Session 1 "The Brain Under Pressure"`, `{user.full_name} created Pod "Pod Norte"`, `{user.full_name} created Participant "Ana Ruiz"`, `{user.full_name} created CTA for Participant "Ana Ruiz" in Lab Session 1`, `{user.full_name} created Action Contract for Participant "Ana Ruiz"`; cambios de status `{user.full_name} updated <etiqueta> from <antes> to <después>`.
- Errores siempre con envelope `{"detail": "..."}`; los 500 no exponen trazas.
- Nada en el código menciona HiTO como constante salvo los nombres de rol (`SYNER_ADMIN`, `HITO_EXECUTIVE`, `HITO_COLLABORATOR`) y el seed.
- Valores de enums exactamente como la spec 4.4: theme `DECIDIR`, `CONFRONTAR`, `ALINEAR`, `TRANSFORMAR`; session status `Planned`, `Done`, `Cancelled`; CTA status `Committed`, `In Progress`, `Evidenced`, `Dropped`; contract status `Draft`, `Active`, `Reviewed 30`, `Reviewed 60`, `Closed`. Nombres de sesión fijos por número: 1 "The Brain Under Pressure", 2 "Trust, Conflict & Difficult Conversations", 3 "From Silos to Flow", 4 "AI, Judgment & Collective Accountability".
- Cada columna enum usa un tipo de Postgres con nombre propio vía `db_enum(EnumCls, "nombre")`: `lab_session_theme`, `lab_session_status`, `cta_status`, `action_contract_status`. La migración los elimina en `downgrade()`.
- Longitudes: nombres y títulos 200, `area` 120, textos largos 10 000. `number` de sesión entre 1 y 4; `number` de pod ≥ 1; `attendance_count` ≥ 0 o null. Un Leadership Action Contract admite entre 0 y 3 CTAs, todos del mismo participante del contrato.
- UI en español; nombres de módulos, estados y términos de la metodología en inglés. `can(user, "manageLab")` y `can(user, "viewLabSummary")` de `frontend/src/lib/roles.ts` (ya existen) solo ocultan UI; el backend es la autoridad. El sidebar no muestra "Leadership Lab" a HITO_COLLABORATOR.
- Sin soft-delete. Commits pequeños por tarea. Mensajes de commit terminan con la línea de atribución indicada por la sesión.

## Review Focus

1. HITO_EXECUTIVE pide `GET /api/engagements/{A}/lab/summary` con participantes y CTAs cargados: 200 y el JSON no contiene en ninguna profundidad las claves `participant`, `trigger`, `behavior`, `full_name`, ni el nombre de ningún participante, ni el texto de ningún CTA. HITO_COLLABORATOR recibe 403. (Test en Task 4.)
2. `POST /lab/contracts` con 4 `cta_ids`: 422; con un CTA de otro participante del mismo engagement: 422; segundo contrato para el mismo participante: 409 y el primero sigue intacto. (Test en Task 3.)
3. `POST /engagements/{A}/lab/ctas` con `participant_id` de un participante que existe en el engagement B: 422 (no 404), sin crear CTA ni activity. (Test en Task 2.)
4. Después de crear participantes y CTAs y cambiar el status de un CTA, el activity feed y `dashboard.recent_activity` de HITO_EXECUTIVE y HITO_COLLABORATOR no contienen ninguna fila del Lab; el de SYNER_ADMIN sí. (Test en Task 2.)
5. `POST /documents` con `url` igual a `javascript:alert(1)` o `ftp://x`: 422; con `""` o `https://...`: 201; lo mismo en PATCH. (Test en Task 9.)

---

### Task 0: Rama de trabajo y verificación del punto de partida

**Files:** ninguno.

- [ ] **Step 1: Crear la rama desde la rama default**

```bash
cd /mnt/d/Devs/HiTOxSyner
git checkout docs/material-hito-syner && git pull --ff-only
git checkout -b feat/plan-3-leadership-lab
```

- [ ] **Step 2: Verificar Postgres, Alembic y la suite de los planes 1 y 2**

```bash
cd /mnt/d/Devs/HiTOxSyner
~/.local/pg/bin/pg_isready -h localhost || ~/.local/pg/bin/pg_ctl -D ~/.local/pgdata -l ~/.local/pgdata/server.log -o "-p 5432 -k /tmp" start
.venv/bin/alembic current
.venv/bin/pytest -q -W error 2>&1 | tail -3
```
Expected: `alembic current` muestra `10b8bdbecacd (head)`; `104 passed`.

---

### Task 1: Enums, modelos del Lab, helper `require_in_engagement`, y endpoints de sessions y pods

**Files:**
- Modify: `app/models/enums.py` (añadir al final)
- Create: `app/models/lab.py`
- Modify: `app/models/__init__.py`
- Create: `app/services/links.py`
- Create: `app/schemas/lab.py`, `app/crud/lab.py`, `app/services/lab.py`, `app/routers/lab.py`
- Modify: `app/main.py` (registrar router)
- Test: `tests/test_lab_models.py`, `tests/test_lab_sessions_pods.py`

**Interfaces:**
- Consumes: `EngagementScopedMixin`, `db_enum` (`app/models/base.py`); `get_engagement`, `require_roles`, `scoped` (`app/dependencies.py`); `Page`, `Pagination`, `pagination_params`, `updates` (`app/schemas/common.py`); `log_activity`, `diff_changes` (`app/services/activity.py`).
- Produces:
  - Enums `LabSessionTheme`, `LabSessionStatus`, `CtaStatus`, `ContractStatus`, tuplas `ACTIVE_CTA_STATUSES`, `ACTIVE_CONTRACT_STATUSES`, dicts `LAB_SESSION_NAMES`, `LAB_SESSION_THEMES`.
  - Modelos `LabSession`, `Pod`, `Participant`, `Cta`, `ActionContract` (con propiedad `cta_ids: list[uuid.UUID]`), `ActionContractCta`.
  - `require_in_engagement(db, model, entity_id, engagement, field) -> entity | None` (422 si no es del engagement).
  - Services: `create_session(db, *, user, engagement, data) -> LabSession`, `update_session(db, *, user, session, data)`, `create_pod(...)`, `update_pod(...)`, helpers privados `_log(...)` y `_apply_update(...)` reutilizados por las Tasks 2 y 3.
  - Rutas: `GET|POST /api/engagements/{engagement_id}/lab/sessions`, `PATCH /api/lab/sessions/{session_id}`, `GET|POST /api/engagements/{engagement_id}/lab/pods`, `PATCH /api/lab/pods/{pod_id}`.

- [ ] **Step 1: Añadir los enums del Lab al final de `app/models/enums.py`**

```python
class LabSessionTheme(str, enum.Enum):
    DECIDIR = "DECIDIR"
    CONFRONTAR = "CONFRONTAR"
    ALINEAR = "ALINEAR"
    TRANSFORMAR = "TRANSFORMAR"


class LabSessionStatus(str, enum.Enum):
    PLANNED = "Planned"
    DONE = "Done"
    CANCELLED = "Cancelled"


class CtaStatus(str, enum.Enum):
    COMMITTED = "Committed"
    IN_PROGRESS = "In Progress"
    EVIDENCED = "Evidenced"
    DROPPED = "Dropped"


class ContractStatus(str, enum.Enum):
    DRAFT = "Draft"
    ACTIVE = "Active"
    REVIEWED_30 = "Reviewed 30"
    REVIEWED_60 = "Reviewed 60"
    CLOSED = "Closed"


ACTIVE_CTA_STATUSES = (CtaStatus.COMMITTED, CtaStatus.IN_PROGRESS)
ACTIVE_CONTRACT_STATUSES = (ContractStatus.ACTIVE, ContractStatus.REVIEWED_30, ContractStatus.REVIEWED_60)

LAB_SESSION_NAMES = {
    1: "The Brain Under Pressure",
    2: "Trust, Conflict & Difficult Conversations",
    3: "From Silos to Flow",
    4: "AI, Judgment & Collective Accountability",
}
LAB_SESSION_THEMES = {
    1: LabSessionTheme.DECIDIR,
    2: LabSessionTheme.CONFRONTAR,
    3: LabSessionTheme.ALINEAR,
    4: LabSessionTheme.TRANSFORMAR,
}
```

- [ ] **Step 2: Escribir el test de modelos**

`tests/test_lab_models.py`:

```python
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.enums import ContractStatus, CtaStatus, LabSessionStatus, LabSessionTheme
from app.models.lab import ActionContract, ActionContractCta, Cta, LabSession, Participant, Pod


def _common(world, engagement):
    return dict(organization_id=engagement.organization_id, engagement_id=engagement.id, created_by=world.admin.id)


def test_lab_models_persist_with_defaults_and_contract_exposes_cta_ids(db, world):
    common = _common(world, world.eng_a)
    session = LabSession(number=1, name="The Brain Under Pressure", theme=LabSessionTheme.DECIDIR, **common)
    pod = Pod(number=1, name="Pod Norte", **common)
    db.add_all([session, pod])
    db.flush()
    participant = Participant(full_name="Ana Ruiz", pod_id=pod.id, **common)
    db.add(participant)
    db.flush()
    cta = Cta(participant_id=participant.id, session_id=session.id, behavior="Dar feedback directo", **common)
    db.add(cta)
    db.flush()
    contract = ActionContract(participant_id=participant.id, **common)
    contract.ctas.append(ActionContractCta(cta_id=cta.id))
    db.add(contract)
    db.commit()
    for obj in (session, participant, cta, contract):
        db.refresh(obj)
    assert session.status == LabSessionStatus.PLANNED
    assert session.held_on is None and session.attendance_count is None and session.syner_notes == ""
    assert participant.is_active is True and participant.area == "" and participant.title == ""
    assert cta.status == CtaStatus.COMMITTED and cta.trigger == "" and cta.evidence_notes == "" and cta.due_date is None
    assert contract.status == ContractStatus.DRAFT
    assert contract.start_date is None and contract.review_30_date is None and contract.review_60_date is None
    assert contract.cta_ids == [cta.id]


def test_session_and_pod_numbers_are_unique_per_engagement(db, world):
    a = _common(world, world.eng_a)
    b = _common(world, world.eng_b)
    db.add_all([
        LabSession(number=1, name="S", theme=LabSessionTheme.DECIDIR, **a),
        LabSession(number=1, name="S", theme=LabSessionTheme.DECIDIR, **b),
        Pod(number=1, name="P", **a),
        Pod(number=1, name="P", **b),
    ])
    db.commit()
    db.add(LabSession(number=1, name="dup", theme=LabSessionTheme.DECIDIR, **a))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()
    db.add(Pod(number=1, name="dup", **a))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()
```

- [ ] **Step 3: Correr el test para verificar que falla**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest tests/test_lab_models.py -q -W error`
Expected: FAIL con `ModuleNotFoundError: No module named 'app.models.lab'`.

- [ ] **Step 4: Crear `app/models/lab.py`**

```python
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import EngagementScopedMixin, db_enum
from app.models.enums import ContractStatus, CtaStatus, LabSessionStatus, LabSessionTheme


class LabSession(EngagementScopedMixin, Base):
    __tablename__ = "lab_sessions"
    __table_args__ = (UniqueConstraint("engagement_id", "number", name="uq_lab_sessions_engagement_number"),)

    number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    theme: Mapped[LabSessionTheme] = mapped_column(db_enum(LabSessionTheme, "lab_session_theme"), nullable=False)
    held_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[LabSessionStatus] = mapped_column(
        db_enum(LabSessionStatus, "lab_session_status"), default=LabSessionStatus.PLANNED, nullable=False
    )
    attendance_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    syner_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)


class Pod(EngagementScopedMixin, Base):
    __tablename__ = "pods"
    __table_args__ = (UniqueConstraint("engagement_id", "number", name="uq_pods_engagement_number"),)

    number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)


class Participant(EngagementScopedMixin, Base):
    __tablename__ = "participants"

    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    area: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    title: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    pod_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("pods.id"), index=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Cta(EngagementScopedMixin, Base):
    __tablename__ = "ctas"

    participant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("participants.id"), index=True, nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lab_sessions.id"), index=True, nullable=False)
    trigger: Mapped[str] = mapped_column(Text, default="", nullable=False)
    behavior: Mapped[str] = mapped_column(Text, nullable=False)
    stakeholder: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    evidence_expected: Mapped[str] = mapped_column(Text, default="", nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    accountability_partner: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    impact: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[CtaStatus] = mapped_column(db_enum(CtaStatus, "cta_status"), default=CtaStatus.COMMITTED, nullable=False)
    evidence_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)


class ActionContract(EngagementScopedMixin, Base):
    __tablename__ = "action_contracts"
    __table_args__ = (UniqueConstraint("engagement_id", "participant_id", name="uq_action_contracts_participant"),)

    participant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("participants.id"), index=True, nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_30_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_60_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    success_signal: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[ContractStatus] = mapped_column(
        db_enum(ContractStatus, "action_contract_status"), default=ContractStatus.DRAFT, nullable=False
    )

    ctas: Mapped[list["ActionContractCta"]] = relationship(
        "ActionContractCta", back_populates="contract", lazy="selectin", cascade="all, delete-orphan",
        order_by="ActionContractCta.created_at",
    )

    @property
    def cta_ids(self) -> list[uuid.UUID]:
        return [link.cta_id for link in self.ctas]


class ActionContractCta(Base):
    __tablename__ = "action_contract_ctas"
    __table_args__ = (UniqueConstraint("contract_id", "cta_id", name="uq_action_contract_ctas"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    contract_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("action_contracts.id", ondelete="CASCADE"), index=True, nullable=False)
    cta_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ctas.id"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    contract: Mapped[ActionContract] = relationship(ActionContract, back_populates="ctas")
```

- [ ] **Step 5: Registrar los modelos en `app/models/__init__.py`**

Reemplazar el archivo completo por:

```python
from app.models.activity import Activity
from app.models.action import Action
from app.models.comment import Comment
from app.models.decision import Decision
from app.models.document import Document, DocumentLink
from app.models.engagement import Engagement
from app.models.initiative import Initiative
from app.models.finding import Finding
from app.models.lab import ActionContract, ActionContractCta, Cta, LabSession, Participant, Pod
from app.models.meeting import Meeting
from app.models.milestone import Milestone
from app.models.organization import Organization
from app.models.user import User

__all__ = [
    "Action", "ActionContract", "ActionContractCta", "Activity", "Comment", "Cta", "Decision", "Document", "DocumentLink",
    "Engagement", "Finding", "Initiative", "LabSession", "Meeting", "Milestone", "Organization", "Participant", "Pod", "User",
]
```

- [ ] **Step 6: Correr el test de modelos**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest tests/test_lab_models.py -q -W error`
Expected: `2 passed`.

- [ ] **Step 7: Escribir los tests de sessions y pods**

`tests/test_lab_sessions_pods.py`:

```python
from tests.factories import login


def _sessions(world, engagement=None):
    return f"/api/engagements/{(engagement or world.eng_a).id}/lab/sessions"


def _pods(world, engagement=None):
    return f"/api/engagements/{(engagement or world.eng_a).id}/lab/pods"


def _feed(client, world, headers):
    return client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=headers).json()


def test_syner_creates_session_with_catalog_defaults_and_internal_activity(client, world):
    admin = login(client, "admin@syner.example")
    response = client.post(_sessions(world), headers=admin, json={"number": 2, "held_on": "2026-11-05"})
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["name"] == "Trust, Conflict & Difficult Conversations"
    assert body["theme"] == "CONFRONTAR"
    assert body["status"] == "Planned" and body["attendance_count"] is None and body["syner_notes"] == ""
    assert body["held_on"] == "2026-11-05" and body["engagement_id"] == str(world.eng_a.id)
    assert _feed(client, world, admin)["items"][0]["summary"] == 'Syner Admin created Lab Session 2 "Trust, Conflict & Difficult Conversations"'
    assert _feed(client, world, login(client, "exec@a.example"))["total"] == 0
    assert _feed(client, world, login(client, "collab@a.example"))["total"] == 0


def test_session_number_is_unique_per_engagement_and_within_range(client, world):
    admin = login(client, "admin@syner.example")
    assert client.post(_sessions(world), headers=admin, json={"number": 1}).status_code == 201
    assert client.post(_sessions(world), headers=admin, json={"number": 1}).status_code == 409
    assert client.post(_sessions(world), headers=admin, json={"number": 5}).status_code == 422
    assert client.post(_sessions(world), headers=admin, json={"number": 0}).status_code == 422
    assert client.post(_sessions(world, world.eng_b), headers=admin, json={"number": 1}).status_code == 201
    listing = client.get(_sessions(world), headers=admin).json()
    assert listing["total"] == 1 and listing["items"][0]["number"] == 1


def test_sessions_list_ordered_by_number_and_custom_name_kept(client, world):
    admin = login(client, "admin@syner.example")
    client.post(_sessions(world), headers=admin, json={"number": 3})
    client.post(_sessions(world), headers=admin, json={"number": 1, "name": "Sesión inaugural", "theme": "DECIDIR"})
    items = client.get(_sessions(world), headers=admin).json()["items"]
    assert [s["number"] for s in items] == [1, 3]
    assert items[0]["name"] == "Sesión inaugural" and items[1]["name"] == "From Silos to Flow" and items[1]["theme"] == "ALINEAR"


def test_session_update_marks_done_and_logs_status_change_internally(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(_sessions(world), headers=admin, json={"number": 1}).json()
    response = client.patch(
        f"/api/lab/sessions/{created['id']}", headers=admin,
        json={"status": "Done", "attendance_count": 18, "held_on": "2026-10-20", "syner_notes": "Buena energía en el grupo."},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "Done" and response.json()["attendance_count"] == 18
    activity = _feed(client, world, admin)["items"][0]
    assert activity["action"] == "status_changed"
    assert activity["summary"] == 'Syner Admin updated Lab Session 1 "The Brain Under Pressure" from Planned to Done'
    assert _feed(client, world, login(client, "exec@a.example"))["total"] == 0
    assert client.patch(f"/api/lab/sessions/{created['id']}", headers=admin, json={"attendance_count": -1}).status_code == 422
    assert client.patch(f"/api/lab/sessions/{created['id']}", headers=admin, json={"name": None}).status_code == 422
    cleared = client.patch(f"/api/lab/sessions/{created['id']}", headers=admin, json={"held_on": None, "attendance_count": None})
    assert cleared.status_code == 200 and cleared.json()["held_on"] is None and cleared.json()["attendance_count"] is None


def test_only_syner_manages_sessions_and_pods(client, world):
    admin = login(client, "admin@syner.example")
    session = client.post(_sessions(world), headers=admin, json={"number": 1}).json()
    pod = client.post(_pods(world), headers=admin, json={"number": 1, "name": "Pod Norte"}).json()
    for email in ("exec@a.example", "collab@a.example"):
        headers = login(client, email)
        assert client.get(_sessions(world), headers=headers).status_code == 403
        assert client.post(_sessions(world), headers=headers, json={"number": 2}).status_code == 403
        assert client.patch(f"/api/lab/sessions/{session['id']}", headers=headers, json={"status": "Done"}).status_code == 403
        assert client.get(_pods(world), headers=headers).status_code == 403
        assert client.post(_pods(world), headers=headers, json={"number": 2, "name": "Pod Sur"}).status_code == 403
        assert client.patch(f"/api/lab/pods/{pod['id']}", headers=headers, json={"name": "Otro"}).status_code == 403
    exec_b = login(client, "exec@b.example")
    assert client.get(_sessions(world), headers=exec_b).status_code == 404
    assert client.post(_sessions(world), headers=exec_b, json={"number": 2}).status_code == 404
    assert client.patch(f"/api/lab/sessions/{session['id']}", headers=exec_b, json={"status": "Done"}).status_code == 404
    assert client.patch(f"/api/lab/pods/{pod['id']}", headers=exec_b, json={"name": "Otro"}).status_code == 404
    assert client.get(_sessions(world), headers=admin).json()["total"] == 1


def test_pods_crud_unique_number_and_isolation(client, world):
    admin = login(client, "admin@syner.example")
    response = client.post(_pods(world), headers=admin, json={"number": 1, "name": "Pod Norte"})
    assert response.status_code == 201, response.text
    pod = response.json()
    assert client.post(_pods(world), headers=admin, json={"number": 1, "name": "Repetido"}).status_code == 409
    assert client.post(_pods(world), headers=admin, json={"number": 0, "name": "Cero"}).status_code == 422
    assert client.post(_pods(world, world.eng_b), headers=admin, json={"number": 1, "name": "De B"}).status_code == 201
    assert _feed(client, world, admin)["items"][0]["summary"] == 'Syner Admin created Pod "Pod Norte"'
    renamed = client.patch(f"/api/lab/pods/{pod['id']}", headers=admin, json={"name": "Pod Norte+"})
    assert renamed.status_code == 200 and renamed.json()["name"] == "Pod Norte+"
    other = client.post(_pods(world), headers=admin, json={"number": 2, "name": "Pod Sur"}).json()
    assert client.patch(f"/api/lab/pods/{other['id']}", headers=admin, json={"number": 1}).status_code == 409
    listing = client.get(_pods(world), headers=admin).json()
    assert listing["total"] == 2 and [p["name"] for p in listing["items"]] == ["Pod Norte+", "Pod Sur"]
```

- [ ] **Step 8: Correr los tests para verificar que fallan**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest tests/test_lab_sessions_pods.py -q -W error`
Expected: FAIL (404 en todos los endpoints `/lab/...`).

- [ ] **Step 9: Crear `app/services/links.py`**

```python
import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.engagement import Engagement


def require_in_engagement(db: Session, model, entity_id: uuid.UUID | None, engagement: Engagement, field: str):
    """Carga la entidad referenciada y exige que sea del mismo engagement.

    Devuelve None si entity_id es None. Responde 422 (nunca 404) cuando la entidad no existe o es de otro
    engagement, para no revelar la existencia de datos ajenos.
    """
    if entity_id is None:
        return None
    entity = db.get(model, entity_id)
    if entity is None or entity.engagement_id != engagement.id:
        raise HTTPException(status_code=422, detail=f"{field} no pertenece a este engagement")
    return entity
```

- [ ] **Step 10: Crear `app/schemas/lab.py` (sessions y pods; las Tasks 2 y 3 añaden el resto)**

```python
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import LabSessionStatus, LabSessionTheme


class LabSessionCreate(BaseModel):
    number: int = Field(ge=1, le=4)
    name: str = Field(default="", max_length=200)
    theme: LabSessionTheme | None = None
    held_on: date | None = None
    status: LabSessionStatus = LabSessionStatus.PLANNED
    attendance_count: int | None = Field(default=None, ge=0)
    syner_notes: str = Field(default="", max_length=10000)


class LabSessionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    theme: LabSessionTheme | None = None
    held_on: date | None = None
    status: LabSessionStatus | None = None
    attendance_count: int | None = Field(default=None, ge=0)
    syner_notes: str | None = Field(default=None, max_length=10000)


class LabSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    engagement_id: uuid.UUID
    number: int
    name: str
    theme: LabSessionTheme
    held_on: date | None
    status: LabSessionStatus
    attendance_count: int | None
    syner_notes: str
    created_at: datetime
    updated_at: datetime


class PodCreate(BaseModel):
    number: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=200)


class PodUpdate(BaseModel):
    number: int | None = Field(default=None, ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=200)


class PodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    engagement_id: uuid.UUID
    number: int
    name: str
    created_at: datetime
    updated_at: datetime
```

- [ ] **Step 11: Crear `app/crud/lab.py` (sessions y pods)**

```python
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.lab import LabSession, Pod


def _page(db: Session, query, order_by, limit: int, offset: int):
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(*order_by).limit(limit).offset(offset)))
    return items, total


def list_sessions(db: Session, engagement_id: uuid.UUID, *, limit: int = 50, offset: int = 0) -> tuple[list[LabSession], int]:
    query = select(LabSession).where(LabSession.engagement_id == engagement_id)
    return _page(db, query, (LabSession.number,), limit, offset)


def list_all_sessions(db: Session, engagement_id: uuid.UUID) -> list[LabSession]:
    return list(db.scalars(select(LabSession).where(LabSession.engagement_id == engagement_id).order_by(LabSession.number)))


def get_session_by_number(db: Session, engagement_id: uuid.UUID, number: int) -> LabSession | None:
    return db.scalar(select(LabSession).where(LabSession.engagement_id == engagement_id, LabSession.number == number))


def list_pods(db: Session, engagement_id: uuid.UUID, *, limit: int = 50, offset: int = 0) -> tuple[list[Pod], int]:
    query = select(Pod).where(Pod.engagement_id == engagement_id)
    return _page(db, query, (Pod.number,), limit, offset)


def list_all_pods(db: Session, engagement_id: uuid.UUID) -> list[Pod]:
    return list(db.scalars(select(Pod).where(Pod.engagement_id == engagement_id).order_by(Pod.number)))


def get_pod_by_number(db: Session, engagement_id: uuid.UUID, number: int) -> Pod | None:
    return db.scalar(select(Pod).where(Pod.engagement_id == engagement_id, Pod.number == number))
```

- [ ] **Step 12: Crear `app/services/lab.py` (helpers, sessions y pods)**

```python
from collections.abc import Callable

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.crud import lab as lab_crud
from app.models.engagement import Engagement
from app.models.enums import LAB_SESSION_NAMES, LAB_SESSION_THEMES, ActivityAction
from app.models.lab import LabSession, Pod
from app.models.user import User
from app.schemas.common import updates
from app.schemas.lab import LabSessionCreate, LabSessionUpdate, PodCreate, PodUpdate
from app.services.activity import diff_changes, log_activity


def _log(db: Session, *, user: User, engagement: Engagement, action: ActivityAction, entity_type: str, entity_id, summary: str, changes=None) -> None:
    """Toda la actividad del Lab es internal_only: nombres de participantes y textos de CTAs solo los ve Syner."""
    log_activity(
        db, user=user, engagement=engagement, action=action, entity_type=entity_type, entity_id=entity_id,
        summary=summary, changes=changes, internal_only=True,
    )


def _apply_update(db: Session, *, user: User, engagement: Engagement, entity, payload: dict, entity_type: str, label: Callable[[], str]) -> bool:
    """Aplica un PATCH ya validado y registra activity. Devuelve False si no hubo cambios."""
    changes = diff_changes(entity, payload)
    if not changes:
        return False
    for field, value in payload.items():
        setattr(entity, field, value)
    status_change = next((c for c in changes if c["field"] == "status"), None)
    if status_change:
        action = ActivityAction.STATUS_CHANGED
        summary = f'{user.full_name} updated {label()} from {status_change["before"]} to {status_change["after"]}'
    else:
        action = ActivityAction.UPDATED
        summary = f'{user.full_name} updated {label()}'
    _log(db, user=user, engagement=engagement, action=action, entity_type=entity_type, entity_id=entity.id, summary=summary, changes=changes)
    return True


def _scoped_kwargs(engagement: Engagement, user: User) -> dict:
    return dict(organization_id=engagement.organization_id, engagement_id=engagement.id, created_by=user.id)


# --- Sessions ---------------------------------------------------------------

def session_label(session: LabSession) -> str:
    return f'Lab Session {session.number} "{session.name}"'


def create_session(db: Session, *, user: User, engagement: Engagement, data: LabSessionCreate) -> LabSession:
    if lab_crud.get_session_by_number(db, engagement.id, data.number) is not None:
        raise HTTPException(status_code=409, detail=f"La sesión {data.number} ya existe en este engagement")
    payload = data.model_dump()
    payload["name"] = payload["name"] or LAB_SESSION_NAMES[data.number]
    payload["theme"] = payload["theme"] or LAB_SESSION_THEMES[data.number]
    session = LabSession(**_scoped_kwargs(engagement, user), **payload)
    db.add(session)
    db.flush()
    _log(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="lab_session",
        entity_id=session.id, summary=f"{user.full_name} created {session_label(session)}",
    )
    db.commit()
    db.refresh(session)
    return session


def update_session(db: Session, *, user: User, session: LabSession, data: LabSessionUpdate) -> LabSession:
    payload = updates(data, nullable={"held_on", "attendance_count"})
    engagement = db.get(Engagement, session.engagement_id)
    if _apply_update(db, user=user, engagement=engagement, entity=session, payload=payload, entity_type="lab_session", label=lambda: session_label(session)):
        db.commit()
        db.refresh(session)
    return session


# --- Pods -------------------------------------------------------------------

def create_pod(db: Session, *, user: User, engagement: Engagement, data: PodCreate) -> Pod:
    if lab_crud.get_pod_by_number(db, engagement.id, data.number) is not None:
        raise HTTPException(status_code=409, detail=f"El pod {data.number} ya existe en este engagement")
    pod = Pod(**_scoped_kwargs(engagement, user), **data.model_dump())
    db.add(pod)
    db.flush()
    _log(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="pod",
        entity_id=pod.id, summary=f'{user.full_name} created Pod "{pod.name}"',
    )
    db.commit()
    db.refresh(pod)
    return pod


def update_pod(db: Session, *, user: User, pod: Pod, data: PodUpdate) -> Pod:
    payload = updates(data)
    engagement = db.get(Engagement, pod.engagement_id)
    new_number = payload.get("number")
    if new_number is not None and new_number != pod.number and lab_crud.get_pod_by_number(db, engagement.id, new_number) is not None:
        raise HTTPException(status_code=409, detail=f"El pod {new_number} ya existe en este engagement")
    if _apply_update(db, user=user, engagement=engagement, entity=pod, payload=payload, entity_type="pod", label=lambda: f'Pod "{pod.name}"'):
        db.commit()
        db.refresh(pod)
    return pod
```

- [ ] **Step 13: Crear `app/routers/lab.py` (sessions y pods)**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import lab as lab_crud
from app.database import get_db
from app.dependencies import get_engagement, require_roles, scoped
from app.models.engagement import Engagement
from app.models.enums import Role
from app.models.lab import LabSession, Pod
from app.models.user import User
from app.schemas.common import Page, Pagination, pagination_params
from app.schemas.lab import LabSessionCreate, LabSessionRead, LabSessionUpdate, PodCreate, PodRead, PodUpdate
from app.services import lab as lab_service

router = APIRouter(tags=["lab"])

# Orden de dependencias: el engagement o la entidad (404 para otra organización) se resuelve antes que el rol (403).
syner_only = Depends(require_roles(Role.SYNER_ADMIN))
scoped_session = Depends(scoped(LabSession, "session_id"))
scoped_pod = Depends(scoped(Pod, "pod_id"))


@router.get("/engagements/{engagement_id}/lab/sessions", response_model=Page[LabSessionRead])
def list_sessions(
    engagement: Engagement = Depends(get_engagement),
    _: User = syner_only,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = lab_crud.list_sessions(db, engagement.id, limit=pagination.limit, offset=pagination.offset)
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/lab/sessions", response_model=LabSessionRead, status_code=201)
def create_session(
    data: LabSessionCreate,
    engagement: Engagement = Depends(get_engagement),
    user: User = syner_only,
    db: Session = Depends(get_db),
):
    return lab_service.create_session(db, user=user, engagement=engagement, data=data)


@router.patch("/lab/sessions/{session_id}", response_model=LabSessionRead)
def update_session(
    data: LabSessionUpdate,
    session: LabSession = scoped_session,
    user: User = syner_only,
    db: Session = Depends(get_db),
):
    return lab_service.update_session(db, user=user, session=session, data=data)


@router.get("/engagements/{engagement_id}/lab/pods", response_model=Page[PodRead])
def list_pods(
    engagement: Engagement = Depends(get_engagement),
    _: User = syner_only,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = lab_crud.list_pods(db, engagement.id, limit=pagination.limit, offset=pagination.offset)
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/lab/pods", response_model=PodRead, status_code=201)
def create_pod(
    data: PodCreate,
    engagement: Engagement = Depends(get_engagement),
    user: User = syner_only,
    db: Session = Depends(get_db),
):
    return lab_service.create_pod(db, user=user, engagement=engagement, data=data)


@router.patch("/lab/pods/{pod_id}", response_model=PodRead)
def update_pod(
    data: PodUpdate,
    pod: Pod = scoped_pod,
    user: User = syner_only,
    db: Session = Depends(get_db),
):
    return lab_service.update_pod(db, user=user, pod=pod, data=data)
```

- [ ] **Step 14: Registrar el router en `app/main.py`**

En la línea de imports de routers añadir `lab`:

```python
from app.routers import actions, activity, auth, comments, dashboard, decisions, documents, engagements, findings, health, initiatives, lab, meetings, milestones
```

Y después de `app.include_router(documents.router, prefix="/api")` añadir:

```python
app.include_router(lab.router, prefix="/api")
```

- [ ] **Step 15: Correr los tests de la tarea y la suite completa**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest tests/test_lab_models.py tests/test_lab_sessions_pods.py -q -W error && .venv/bin/pytest -q -W error 2>&1 | tail -2`
Expected: `8 passed` y luego `112 passed`.

- [ ] **Step 16: Commit**

```bash
cd /mnt/d/Devs/HiTOxSyner
git add app/models/enums.py app/models/lab.py app/models/__init__.py app/services/links.py app/schemas/lab.py app/crud/lab.py app/services/lab.py app/routers/lab.py app/main.py tests/test_lab_models.py tests/test_lab_sessions_pods.py
git commit -m "feat(lab): modelos del Leadership Lab, helper require_in_engagement y endpoints de sessions y pods"
```

---

### Task 2: Participants y CTAs (CTA tracker) con activity interna

**Files:**
- Modify: `app/schemas/lab.py` (añadir al final), `app/crud/lab.py` (añadir al final), `app/services/lab.py` (añadir al final y ampliar imports), `app/routers/lab.py` (añadir al final y ampliar imports)
- Test: `tests/test_lab_participants_ctas.py`

**Interfaces:**
- Consumes: modelos `Participant`, `Cta`, `Pod`, `LabSession` (Task 1); `require_in_engagement` (Task 1); `_log`, `_apply_update`, `_scoped_kwargs` de `app/services/lab.py` (Task 1).
- Produces:
  - Schemas `ParticipantCreate`, `ParticipantUpdate`, `ParticipantRead`, `CtaCreate`, `CtaUpdate`, `CtaRead`.
  - Crud `list_participants(db, engagement_id, *, pod_id, is_active, limit, offset)`, `list_ctas(db, engagement_id, *, session_id, pod_id, status, limit, offset)`.
  - Services `create_participant`, `update_participant`, `create_cta`, `update_cta`, `cta_label(db, cta) -> str`.
  - Rutas: `GET|POST /api/engagements/{engagement_id}/lab/participants` (filtros `pod_id`, `is_active`), `PATCH /api/lab/participants/{participant_id}`, `GET|POST /api/engagements/{engagement_id}/lab/ctas` (filtros `session_id`, `pod_id`, `status`), `PATCH /api/lab/ctas/{cta_id}`.

- [ ] **Step 1: Escribir los tests**

`tests/test_lab_participants_ctas.py`:

```python
from tests.factories import login

CTA = {
    "trigger": "Cuando el comité semanal se desvía hacia culpas personales",
    "behavior": "Dar feedback directo y específico en el momento",
    "stakeholder": "Equipo de operaciones",
    "evidence_expected": "Minuta del comité con el feedback registrado",
    "due_date": "2026-11-30",
    "accountability_partner": "Luis Mora",
    "impact": "Reducir retrabajo por acuerdos ambiguos",
}


def _base(world, segment, engagement=None):
    return f"/api/engagements/{(engagement or world.eng_a).id}/lab/{segment}"


def _feed(client, world, headers):
    return client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=headers).json()


def _setup(client, world):
    admin = login(client, "admin@syner.example")
    s1 = client.post(_base(world, "sessions"), headers=admin, json={"number": 1}).json()
    s2 = client.post(_base(world, "sessions"), headers=admin, json={"number": 2}).json()
    pod1 = client.post(_base(world, "pods"), headers=admin, json={"number": 1, "name": "Pod Norte"}).json()
    pod2 = client.post(_base(world, "pods"), headers=admin, json={"number": 2, "name": "Pod Sur"}).json()
    return admin, s1, s2, pod1, pod2


def _participant(client, world, admin, name, pod_id=None):
    return client.post(_base(world, "participants"), headers=admin, json={"full_name": name, "area": "Operaciones", "title": "Gerente", "pod_id": pod_id}).json()


def test_syner_creates_participant_assigns_pod_and_toggles_active(client, world):
    admin, _, _, pod1, _ = _setup(client, world)
    response = client.post(_base(world, "participants"), headers=admin, json={"full_name": "Ana Ruiz", "area": "Operaciones", "title": "Directora", "pod_id": pod1["id"]})
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["is_active"] is True and body["pod_id"] == pod1["id"] and body["engagement_id"] == str(world.eng_a.id)
    assert _feed(client, world, admin)["items"][0]["summary"] == 'Syner Admin created Participant "Ana Ruiz"'
    assert _feed(client, world, login(client, "exec@a.example"))["total"] == 0
    updated = client.patch(f"/api/lab/participants/{body['id']}", headers=admin, json={"is_active": False, "pod_id": None})
    assert updated.status_code == 200 and updated.json()["is_active"] is False and updated.json()["pod_id"] is None
    assert client.get(_base(world, "participants"), headers=admin, params={"is_active": "true"}).json()["total"] == 0
    assert client.get(_base(world, "participants"), headers=admin, params={"pod_id": pod1["id"]}).json()["total"] == 0
    assert client.get(_base(world, "participants"), headers=admin).json()["total"] == 1
    assert client.patch(f"/api/lab/participants/{body['id']}", headers=admin, json={"full_name": None}).status_code == 422
    assert client.post(_base(world, "participants"), headers=admin, json={"full_name": ""}).status_code == 422


def test_participant_pod_must_belong_to_engagement(client, world):
    admin, _, _, pod1, _ = _setup(client, world)
    foreign_pod = client.post(_base(world, "pods", world.eng_b), headers=admin, json={"number": 1, "name": "De B"}).json()
    assert client.post(_base(world, "participants"), headers=admin, json={"full_name": "Ana Ruiz", "pod_id": foreign_pod["id"]}).status_code == 422
    participant = _participant(client, world, admin, "Ana Ruiz", pod1["id"])
    assert client.patch(f"/api/lab/participants/{participant['id']}", headers=admin, json={"pod_id": foreign_pod["id"]}).status_code == 422
    assert client.get(_base(world, "participants"), headers=admin).json()["items"][0]["pod_id"] == pod1["id"]


def test_cta_requires_behavior_and_links_within_engagement(client, world):
    admin, s1, _, pod1, _ = _setup(client, world)
    ana = _participant(client, world, admin, "Ana Ruiz", pod1["id"])
    response = client.post(_base(world, "ctas"), headers=admin, json={**CTA, "participant_id": ana["id"], "session_id": s1["id"]})
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "Committed" and body["evidence_notes"] == "" and body["due_date"] == "2026-11-30"
    assert body["participant_id"] == ana["id"] and body["session_id"] == s1["id"]
    assert _feed(client, world, admin)["items"][0]["summary"] == 'Syner Admin created CTA for Participant "Ana Ruiz" in Lab Session 1'
    assert client.post(_base(world, "ctas"), headers=admin, json={"participant_id": ana["id"], "session_id": s1["id"]}).status_code == 422
    assert client.post(_base(world, "ctas"), headers=admin, json={"participant_id": ana["id"], "session_id": s1["id"], "behavior": ""}).status_code == 422
    foreign_session = client.post(_base(world, "sessions", world.eng_b), headers=admin, json={"number": 1}).json()
    foreign_participant = client.post(_base(world, "participants", world.eng_b), headers=admin, json={"full_name": "De B"}).json()
    before = _feed(client, world, admin)["total"]
    assert client.post(_base(world, "ctas"), headers=admin, json={**CTA, "participant_id": foreign_participant["id"], "session_id": s1["id"]}).status_code == 422
    assert client.post(_base(world, "ctas"), headers=admin, json={**CTA, "participant_id": ana["id"], "session_id": foreign_session["id"]}).status_code == 422
    assert client.patch(f"/api/lab/ctas/{body['id']}", headers=admin, json={"participant_id": foreign_participant["id"]}).status_code == 422
    assert client.patch(f"/api/lab/ctas/{body['id']}", headers=admin, json={"behavior": None}).status_code == 422
    assert client.get(_base(world, "ctas"), headers=admin).json()["total"] == 1
    assert _feed(client, world, admin)["total"] == before


def test_cta_filters_by_session_pod_and_status(client, world):
    admin, s1, s2, pod1, pod2 = _setup(client, world)
    ana = _participant(client, world, admin, "Ana Ruiz", pod1["id"])
    luis = _participant(client, world, admin, "Luis Mora", pod2["id"])
    base = _base(world, "ctas")
    c1 = client.post(base, headers=admin, json={**CTA, "participant_id": ana["id"], "session_id": s1["id"]}).json()
    c2 = client.post(base, headers=admin, json={**CTA, "participant_id": ana["id"], "session_id": s2["id"], "behavior": "Cerrar cada reunión con acuerdos escritos"}).json()
    client.post(base, headers=admin, json={**CTA, "participant_id": luis["id"], "session_id": s1["id"], "behavior": "Escalar bloqueos en 24 horas"})
    client.patch(f"/api/lab/ctas/{c2['id']}", headers=admin, json={"status": "Evidenced", "evidence_notes": "Minutas de tres reuniones"})
    assert client.get(base, headers=admin, params={"session_id": s1["id"]}).json()["total"] == 2
    assert client.get(base, headers=admin, params={"pod_id": pod1["id"]}).json()["total"] == 2
    evidenced = client.get(base, headers=admin, params={"status": "Evidenced"}).json()
    assert evidenced["total"] == 1 and evidenced["items"][0]["id"] == c2["id"]
    only = client.get(base, headers=admin, params={"pod_id": pod2["id"], "session_id": s1["id"]}).json()
    assert only["total"] == 1 and only["items"][0]["behavior"] == "Escalar bloqueos en 24 horas"
    assert client.get(base, headers=admin, params={"status": "Dropped"}).json()["total"] == 0
    assert client.get(base, headers=admin).json()["items"][0]["id"] == c1["id"]


def test_cta_status_change_logs_internal_activity_only(client, world):
    admin, s1, _, pod1, _ = _setup(client, world)
    ana = _participant(client, world, admin, "Ana Ruiz", pod1["id"])
    cta = client.post(_base(world, "ctas"), headers=admin, json={**CTA, "participant_id": ana["id"], "session_id": s1["id"]}).json()
    response = client.patch(f"/api/lab/ctas/{cta['id']}", headers=admin, json={"status": "Evidenced", "evidence_notes": "Minuta del comité del 12 de noviembre"})
    assert response.status_code == 200 and response.json()["status"] == "Evidenced"
    admin_feed = _feed(client, world, admin)
    assert admin_feed["items"][0]["action"] == "status_changed"
    assert admin_feed["items"][0]["summary"] == 'Syner Admin updated CTA of Participant "Ana Ruiz" from Committed to Evidenced'
    assert admin_feed["total"] >= 6
    for email in ("exec@a.example", "collab@a.example"):
        headers = login(client, email)
        feed = _feed(client, world, headers)
        assert feed["total"] == 0
        dashboard = client.get(f"/api/engagements/{world.eng_a.id}/dashboard", headers=headers).json()
        assert all("Ana Ruiz" not in a["summary"] and "CTA" not in a["summary"] for a in dashboard["recent_activity"])
    cleared = client.patch(f"/api/lab/ctas/{cta['id']}", headers=admin, json={"due_date": None})
    assert cleared.status_code == 200 and cleared.json()["due_date"] is None


def test_client_roles_cannot_access_participants_and_ctas(client, world):
    admin, s1, _, pod1, _ = _setup(client, world)
    ana = _participant(client, world, admin, "Ana Ruiz", pod1["id"])
    cta = client.post(_base(world, "ctas"), headers=admin, json={**CTA, "participant_id": ana["id"], "session_id": s1["id"]}).json()
    for email in ("exec@a.example", "collab@a.example"):
        headers = login(client, email)
        assert client.get(_base(world, "participants"), headers=headers).status_code == 403
        assert client.post(_base(world, "participants"), headers=headers, json={"full_name": "X"}).status_code == 403
        assert client.patch(f"/api/lab/participants/{ana['id']}", headers=headers, json={"is_active": False}).status_code == 403
        assert client.get(_base(world, "ctas"), headers=headers).status_code == 403
        assert client.post(_base(world, "ctas"), headers=headers, json={**CTA, "participant_id": ana["id"], "session_id": s1["id"]}).status_code == 403
        assert client.patch(f"/api/lab/ctas/{cta['id']}", headers=headers, json={"status": "Dropped"}).status_code == 403
    exec_b = login(client, "exec@b.example")
    assert client.get(_base(world, "participants"), headers=exec_b).status_code == 404
    assert client.get(_base(world, "ctas"), headers=exec_b).status_code == 404
    assert client.patch(f"/api/lab/participants/{ana['id']}", headers=exec_b, json={"is_active": False}).status_code == 404
    assert client.patch(f"/api/lab/ctas/{cta['id']}", headers=exec_b, json={"status": "Dropped"}).status_code == 404
    assert client.get(_base(world, "ctas"), headers=admin).json()["items"][0]["status"] == "Committed"
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest tests/test_lab_participants_ctas.py -q -W error`
Expected: FAIL (404 en `/lab/participants` y `/lab/ctas`).

- [ ] **Step 3: Añadir schemas al final de `app/schemas/lab.py`**

Ampliar el import de enums a `from app.models.enums import CtaStatus, LabSessionStatus, LabSessionTheme` y añadir:

```python
class ParticipantCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    area: str = Field(default="", max_length=120)
    title: str = Field(default="", max_length=200)
    pod_id: uuid.UUID | None = None
    is_active: bool = True


class ParticipantUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    area: str | None = Field(default=None, max_length=120)
    title: str | None = Field(default=None, max_length=200)
    pod_id: uuid.UUID | None = None
    is_active: bool | None = None


class ParticipantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    engagement_id: uuid.UUID
    full_name: str
    area: str
    title: str
    pod_id: uuid.UUID | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CtaCreate(BaseModel):
    participant_id: uuid.UUID
    session_id: uuid.UUID
    trigger: str = Field(default="", max_length=10000)
    behavior: str = Field(min_length=1, max_length=10000)
    stakeholder: str = Field(default="", max_length=200)
    evidence_expected: str = Field(default="", max_length=10000)
    due_date: date | None = None
    accountability_partner: str = Field(default="", max_length=200)
    impact: str = Field(default="", max_length=10000)
    status: CtaStatus = CtaStatus.COMMITTED
    evidence_notes: str = Field(default="", max_length=10000)


class CtaUpdate(BaseModel):
    participant_id: uuid.UUID | None = None
    session_id: uuid.UUID | None = None
    trigger: str | None = Field(default=None, max_length=10000)
    behavior: str | None = Field(default=None, min_length=1, max_length=10000)
    stakeholder: str | None = Field(default=None, max_length=200)
    evidence_expected: str | None = Field(default=None, max_length=10000)
    due_date: date | None = None
    accountability_partner: str | None = Field(default=None, max_length=200)
    impact: str | None = Field(default=None, max_length=10000)
    status: CtaStatus | None = None
    evidence_notes: str | None = Field(default=None, max_length=10000)


class CtaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    engagement_id: uuid.UUID
    participant_id: uuid.UUID
    session_id: uuid.UUID
    trigger: str
    behavior: str
    stakeholder: str
    evidence_expected: str
    due_date: date | None
    accountability_partner: str
    impact: str
    status: CtaStatus
    evidence_notes: str
    created_at: datetime
    updated_at: datetime
```

- [ ] **Step 4: Añadir crud al final de `app/crud/lab.py`**

Ampliar imports a `from app.models.enums import CtaStatus` y `from app.models.lab import Cta, LabSession, Participant, Pod`, y añadir:

```python
def list_participants(
    db: Session, engagement_id: uuid.UUID, *, pod_id: uuid.UUID | None = None, is_active: bool | None = None,
    limit: int = 50, offset: int = 0,
) -> tuple[list[Participant], int]:
    query = select(Participant).where(Participant.engagement_id == engagement_id)
    if pod_id:
        query = query.where(Participant.pod_id == pod_id)
    if is_active is not None:
        query = query.where(Participant.is_active.is_(is_active))
    return _page(db, query, (Participant.full_name, Participant.created_at), limit, offset)


def list_ctas(
    db: Session, engagement_id: uuid.UUID, *, session_id: uuid.UUID | None = None, pod_id: uuid.UUID | None = None,
    status: CtaStatus | None = None, limit: int = 50, offset: int = 0,
) -> tuple[list[Cta], int]:
    query = select(Cta).where(Cta.engagement_id == engagement_id)
    if session_id:
        query = query.where(Cta.session_id == session_id)
    if pod_id:
        query = query.join(Participant, Participant.id == Cta.participant_id).where(Participant.pod_id == pod_id)
    if status:
        query = query.where(Cta.status == status)
    return _page(db, query, (Cta.due_date.nulls_last(), Cta.created_at), limit, offset)
```

- [ ] **Step 5: Añadir services al final de `app/services/lab.py`**

Ampliar imports: `from app.models.lab import Cta, LabSession, Participant, Pod`; `from app.schemas.lab import CtaCreate, CtaUpdate, LabSessionCreate, LabSessionUpdate, ParticipantCreate, ParticipantUpdate, PodCreate, PodUpdate`; y añadir `from app.services.links import require_in_engagement`. Luego:

```python
# --- Participants -----------------------------------------------------------

def create_participant(db: Session, *, user: User, engagement: Engagement, data: ParticipantCreate) -> Participant:
    require_in_engagement(db, Pod, data.pod_id, engagement, "pod_id")
    participant = Participant(**_scoped_kwargs(engagement, user), **data.model_dump())
    db.add(participant)
    db.flush()
    _log(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="participant",
        entity_id=participant.id, summary=f'{user.full_name} created Participant "{participant.full_name}"',
    )
    db.commit()
    db.refresh(participant)
    return participant


def update_participant(db: Session, *, user: User, participant: Participant, data: ParticipantUpdate) -> Participant:
    payload = updates(data, nullable={"pod_id"})
    engagement = db.get(Engagement, participant.engagement_id)
    require_in_engagement(db, Pod, payload.get("pod_id"), engagement, "pod_id")
    if _apply_update(db, user=user, engagement=engagement, entity=participant, payload=payload, entity_type="participant", label=lambda: f'Participant "{participant.full_name}"'):
        db.commit()
        db.refresh(participant)
    return participant


# --- CTAs -------------------------------------------------------------------

def cta_label(db: Session, cta: Cta) -> str:
    participant = db.get(Participant, cta.participant_id)
    return f'CTA of Participant "{participant.full_name}"'


def create_cta(db: Session, *, user: User, engagement: Engagement, data: CtaCreate) -> Cta:
    participant = require_in_engagement(db, Participant, data.participant_id, engagement, "participant_id")
    session = require_in_engagement(db, LabSession, data.session_id, engagement, "session_id")
    cta = Cta(**_scoped_kwargs(engagement, user), **data.model_dump())
    db.add(cta)
    db.flush()
    _log(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="cta", entity_id=cta.id,
        summary=f'{user.full_name} created CTA for Participant "{participant.full_name}" in Lab Session {session.number}',
    )
    db.commit()
    db.refresh(cta)
    return cta


def update_cta(db: Session, *, user: User, cta: Cta, data: CtaUpdate) -> Cta:
    payload = updates(data, nullable={"due_date"})
    engagement = db.get(Engagement, cta.engagement_id)
    require_in_engagement(db, Participant, payload.get("participant_id"), engagement, "participant_id")
    require_in_engagement(db, LabSession, payload.get("session_id"), engagement, "session_id")
    if _apply_update(db, user=user, engagement=engagement, entity=cta, payload=payload, entity_type="cta", label=lambda: cta_label(db, cta)):
        db.commit()
        db.refresh(cta)
    return cta
```

- [ ] **Step 6: Añadir rutas al final de `app/routers/lab.py`**

Ampliar imports: `import uuid`; `from app.models.enums import CtaStatus, Role`; `from app.models.lab import Cta, LabSession, Participant, Pod`; y en el import de schemas añadir `CtaCreate, CtaRead, CtaUpdate, ParticipantCreate, ParticipantRead, ParticipantUpdate`. Luego:

```python
scoped_participant = Depends(scoped(Participant, "participant_id"))
scoped_cta = Depends(scoped(Cta, "cta_id"))


@router.get("/engagements/{engagement_id}/lab/participants", response_model=Page[ParticipantRead])
def list_participants(
    engagement: Engagement = Depends(get_engagement),
    _: User = syner_only,
    pod_id: uuid.UUID | None = None,
    is_active: bool | None = None,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = lab_crud.list_participants(db, engagement.id, pod_id=pod_id, is_active=is_active, limit=pagination.limit, offset=pagination.offset)
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/lab/participants", response_model=ParticipantRead, status_code=201)
def create_participant(
    data: ParticipantCreate,
    engagement: Engagement = Depends(get_engagement),
    user: User = syner_only,
    db: Session = Depends(get_db),
):
    return lab_service.create_participant(db, user=user, engagement=engagement, data=data)


@router.patch("/lab/participants/{participant_id}", response_model=ParticipantRead)
def update_participant(
    data: ParticipantUpdate,
    participant: Participant = scoped_participant,
    user: User = syner_only,
    db: Session = Depends(get_db),
):
    return lab_service.update_participant(db, user=user, participant=participant, data=data)


@router.get("/engagements/{engagement_id}/lab/ctas", response_model=Page[CtaRead])
def list_ctas(
    engagement: Engagement = Depends(get_engagement),
    _: User = syner_only,
    session_id: uuid.UUID | None = None,
    pod_id: uuid.UUID | None = None,
    status: CtaStatus | None = None,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = lab_crud.list_ctas(
        db, engagement.id, session_id=session_id, pod_id=pod_id, status=status, limit=pagination.limit, offset=pagination.offset,
    )
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/lab/ctas", response_model=CtaRead, status_code=201)
def create_cta(
    data: CtaCreate,
    engagement: Engagement = Depends(get_engagement),
    user: User = syner_only,
    db: Session = Depends(get_db),
):
    return lab_service.create_cta(db, user=user, engagement=engagement, data=data)


@router.patch("/lab/ctas/{cta_id}", response_model=CtaRead)
def update_cta(
    data: CtaUpdate,
    cta: Cta = scoped_cta,
    user: User = syner_only,
    db: Session = Depends(get_db),
):
    return lab_service.update_cta(db, user=user, cta=cta, data=data)
```

- [ ] **Step 7: Correr los tests de la tarea y la suite completa**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest tests/test_lab_participants_ctas.py -q -W error && .venv/bin/pytest -q -W error 2>&1 | tail -2`
Expected: `6 passed` y luego `118 passed`.

- [ ] **Step 8: Commit**

```bash
cd /mnt/d/Devs/HiTOxSyner
git add app/schemas/lab.py app/crud/lab.py app/services/lab.py app/routers/lab.py tests/test_lab_participants_ctas.py
git commit -m "feat(lab): participantes con pods y CTA tracker con filtros y activity interna"
```

---

### Task 3: Leadership Action Contracts (máximo 3 CTAs, uno por participante, fechas +30 y +60)

**Files:**
- Modify: `app/schemas/lab.py`, `app/crud/lab.py`, `app/services/lab.py`, `app/routers/lab.py` (añadir al final de cada uno)
- Test: `tests/test_lab_contracts.py`

**Interfaces:**
- Consumes: modelos `ActionContract`, `ActionContractCta`, `Cta`, `Participant` (Task 1); `require_in_engagement`; `_log`, `_scoped_kwargs` (Task 1).
- Produces:
  - Schemas `ActionContractCreate` (con `cta_ids: list[uuid.UUID]`, máximo 3), `ActionContractUpdate`, `ActionContractRead` (con `cta_ids`).
  - Crud `list_contracts(db, engagement_id, *, status, limit, offset)`, `get_contract_by_participant(db, engagement_id, participant_id)`, `count_active_contracts(db, engagement_id)`.
  - Services `create_contract`, `update_contract`.
  - Rutas: `GET|POST /api/engagements/{engagement_id}/lab/contracts` (filtro `status`), `PATCH /api/lab/contracts/{contract_id}`.

- [ ] **Step 1: Escribir los tests**

`tests/test_lab_contracts.py`:

```python
from tests.factories import login

CTA = {"behavior": "Dar feedback directo", "trigger": "Comité semanal", "stakeholder": "Equipo", "due_date": "2026-11-30"}


def _base(world, segment, engagement=None):
    return f"/api/engagements/{(engagement or world.eng_a).id}/lab/{segment}"


def _feed(client, world, headers):
    return client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=headers).json()


def _setup(client, world):
    admin = login(client, "admin@syner.example")
    session = client.post(_base(world, "sessions"), headers=admin, json={"number": 1}).json()
    ana = client.post(_base(world, "participants"), headers=admin, json={"full_name": "Ana Ruiz"}).json()
    luis = client.post(_base(world, "participants"), headers=admin, json={"full_name": "Luis Mora"}).json()
    ana_ctas = [
        client.post(_base(world, "ctas"), headers=admin, json={**CTA, "participant_id": ana["id"], "session_id": session["id"], "behavior": f"Conducta {i}"}).json()["id"]
        for i in range(4)
    ]
    luis_cta = client.post(_base(world, "ctas"), headers=admin, json={**CTA, "participant_id": luis["id"], "session_id": session["id"]}).json()["id"]
    return admin, ana, luis, ana_ctas, luis_cta


def test_contract_defaults_review_dates_and_links_up_to_three_ctas(client, world):
    admin, ana, _, ana_ctas, _ = _setup(client, world)
    base = _base(world, "contracts")
    assert client.post(base, headers=admin, json={"participant_id": ana["id"], "cta_ids": ana_ctas}).status_code == 422
    response = client.post(base, headers=admin, json={"participant_id": ana["id"], "start_date": "2026-11-01", "success_signal": "El equipo reporta acuerdos claros", "cta_ids": ana_ctas[:3]})
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "Draft"
    assert body["review_30_date"] == "2026-12-01" and body["review_60_date"] == "2026-12-31"
    assert body["cta_ids"] == ana_ctas[:3]
    assert _feed(client, world, admin)["items"][0]["summary"] == 'Syner Admin created Action Contract for Participant "Ana Ruiz"'
    assert _feed(client, world, login(client, "exec@a.example"))["total"] == 0
    listing = client.get(base, headers=admin).json()
    assert listing["total"] == 1 and listing["items"][0]["cta_ids"] == ana_ctas[:3]


def test_contract_without_start_date_keeps_review_dates_null_and_explicit_dates_win(client, world):
    admin, ana, luis, ana_ctas, _ = _setup(client, world)
    base = _base(world, "contracts")
    blank = client.post(base, headers=admin, json={"participant_id": ana["id"]}).json()
    assert blank["start_date"] is None and blank["review_30_date"] is None and blank["review_60_date"] is None and blank["cta_ids"] == []
    explicit = client.post(base, headers=admin, json={"participant_id": luis["id"], "start_date": "2026-11-01", "review_30_date": "2026-12-05"}).json()
    assert explicit["review_30_date"] == "2026-12-05" and explicit["review_60_date"] == "2026-12-31"


def test_contract_is_unique_per_participant_and_ctas_must_belong_to_participant(client, world):
    admin, ana, luis, ana_ctas, luis_cta = _setup(client, world)
    base = _base(world, "contracts")
    first = client.post(base, headers=admin, json={"participant_id": ana["id"], "cta_ids": ana_ctas[:2]}).json()
    assert client.post(base, headers=admin, json={"participant_id": ana["id"]}).status_code == 409
    assert client.post(base, headers=admin, json={"participant_id": luis["id"], "cta_ids": [ana_ctas[0]]}).status_code == 422
    foreign = client.post(_base(world, "participants", world.eng_b), headers=admin, json={"full_name": "De B"}).json()
    assert client.post(base, headers=admin, json={"participant_id": foreign["id"]}).status_code == 422
    assert client.post(base, headers=admin, json={"participant_id": luis["id"], "cta_ids": [luis_cta, luis_cta]}).status_code == 201
    listing = client.get(base, headers=admin).json()
    assert listing["total"] == 2
    assert next(c for c in listing["items"] if c["id"] == first["id"])["cta_ids"] == ana_ctas[:2]
    assert next(c for c in listing["items"] if c["participant_id"] == luis["id"])["cta_ids"] == [luis_cta]


def test_contract_update_replaces_ctas_recomputes_dates_and_logs_status(client, world):
    admin, ana, _, ana_ctas, luis_cta = _setup(client, world)
    base = _base(world, "contracts")
    contract = client.post(base, headers=admin, json={"participant_id": ana["id"], "start_date": "2026-11-01", "cta_ids": ana_ctas[:2]}).json()
    url = f"/api/lab/contracts/{contract['id']}"
    replaced = client.patch(url, headers=admin, json={"cta_ids": [ana_ctas[1], ana_ctas[3]]})
    assert replaced.status_code == 200, replaced.text
    assert sorted(replaced.json()["cta_ids"]) == sorted([ana_ctas[1], ana_ctas[3]])
    moved = client.patch(url, headers=admin, json={"start_date": "2026-12-01"}).json()
    assert moved["review_30_date"] == "2026-12-31" and moved["review_60_date"] == "2027-01-30"
    pinned = client.patch(url, headers=admin, json={"review_30_date": "2027-01-05"}).json()
    assert pinned["review_30_date"] == "2027-01-05" and pinned["review_60_date"] == "2027-01-30"
    activated = client.patch(url, headers=admin, json={"status": "Active"})
    assert activated.status_code == 200 and activated.json()["status"] == "Active"
    activity = _feed(client, world, admin)["items"][0]
    assert activity["action"] == "status_changed"
    assert activity["summary"] == 'Syner Admin updated Action Contract of Participant "Ana Ruiz" from Draft to Active'
    assert client.patch(url, headers=admin, json={"cta_ids": ana_ctas}).status_code == 422
    assert client.patch(url, headers=admin, json={"cta_ids": [luis_cta]}).status_code == 422
    assert client.patch(url, headers=admin, json={"participant_id": None}).status_code == 422
    assert client.patch(url, headers=admin, json={"cta_ids": None}).status_code == 422
    assert sorted(client.get(base, headers=admin).json()["items"][0]["cta_ids"]) == sorted([ana_ctas[1], ana_ctas[3]])


def test_contracts_filter_by_status_and_client_roles_get_403(client, world):
    admin, ana, luis, ana_ctas, _ = _setup(client, world)
    base = _base(world, "contracts")
    active = client.post(base, headers=admin, json={"participant_id": ana["id"], "status": "Active"}).json()
    client.post(base, headers=admin, json={"participant_id": luis["id"]})
    filtered = client.get(base, headers=admin, params={"status": "Active"}).json()
    assert filtered["total"] == 1 and filtered["items"][0]["id"] == active["id"]
    for email in ("exec@a.example", "collab@a.example"):
        headers = login(client, email)
        assert client.get(base, headers=headers).status_code == 403
        assert client.post(base, headers=headers, json={"participant_id": ana["id"]}).status_code == 403
        assert client.patch(f"/api/lab/contracts/{active['id']}", headers=headers, json={"status": "Closed"}).status_code == 403
    exec_b = login(client, "exec@b.example")
    assert client.get(base, headers=exec_b).status_code == 404
    assert client.patch(f"/api/lab/contracts/{active['id']}", headers=exec_b, json={"status": "Closed"}).status_code == 404
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest tests/test_lab_contracts.py -q -W error`
Expected: FAIL (404 en `/lab/contracts`).

- [ ] **Step 3: Añadir schemas al final de `app/schemas/lab.py`**

Ampliar el import de enums a `from app.models.enums import ContractStatus, CtaStatus, LabSessionStatus, LabSessionTheme` y añadir:

```python
class ActionContractCreate(BaseModel):
    participant_id: uuid.UUID
    start_date: date | None = None
    review_30_date: date | None = None
    review_60_date: date | None = None
    success_signal: str = Field(default="", max_length=10000)
    status: ContractStatus = ContractStatus.DRAFT
    cta_ids: list[uuid.UUID] = Field(default_factory=list, max_length=3)


class ActionContractUpdate(BaseModel):
    participant_id: uuid.UUID | None = None
    start_date: date | None = None
    review_30_date: date | None = None
    review_60_date: date | None = None
    success_signal: str | None = Field(default=None, max_length=10000)
    status: ContractStatus | None = None
    cta_ids: list[uuid.UUID] | None = Field(default=None, max_length=3)


class ActionContractRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    engagement_id: uuid.UUID
    participant_id: uuid.UUID
    start_date: date | None
    review_30_date: date | None
    review_60_date: date | None
    success_signal: str
    status: ContractStatus
    cta_ids: list[uuid.UUID]
    created_at: datetime
    updated_at: datetime
```

- [ ] **Step 4: Añadir crud al final de `app/crud/lab.py`**

Ampliar imports: `from app.models.enums import ACTIVE_CONTRACT_STATUSES, ContractStatus, CtaStatus` y `from app.models.lab import ActionContract, Cta, LabSession, Participant, Pod`. Añadir:

```python
def list_contracts(
    db: Session, engagement_id: uuid.UUID, *, status: ContractStatus | None = None, limit: int = 50, offset: int = 0,
) -> tuple[list[ActionContract], int]:
    query = select(ActionContract).where(ActionContract.engagement_id == engagement_id)
    if status:
        query = query.where(ActionContract.status == status)
    return _page(db, query, (ActionContract.created_at,), limit, offset)


def get_contract_by_participant(db: Session, engagement_id: uuid.UUID, participant_id: uuid.UUID) -> ActionContract | None:
    return db.scalar(
        select(ActionContract).where(ActionContract.engagement_id == engagement_id, ActionContract.participant_id == participant_id)
    )


def count_active_contracts(db: Session, engagement_id: uuid.UUID) -> int:
    query = select(func.count()).select_from(ActionContract).where(
        ActionContract.engagement_id == engagement_id, ActionContract.status.in_(ACTIVE_CONTRACT_STATUSES)
    )
    return db.scalar(query) or 0
```

- [ ] **Step 5: Añadir services al final de `app/services/lab.py`**

Ampliar imports: `from datetime import timedelta`; `from app.models.lab import ActionContract, ActionContractCta, Cta, LabSession, Participant, Pod`; en el import de schemas añadir `ActionContractCreate, ActionContractUpdate`. Añadir:

```python
# --- Leadership Action Contracts -------------------------------------------

REVIEW_OFFSETS = (("review_30_date", 30), ("review_60_date", 60))


def _contract_label(db: Session, contract: ActionContract) -> str:
    participant = db.get(Participant, contract.participant_id)
    return f'Action Contract of Participant "{participant.full_name}"'


def _validate_contract_ctas(db: Session, engagement: Engagement, participant_id, cta_ids: list) -> list:
    """Dedup, pertenencia al engagement y al participante del contrato. El máximo de 3 lo impone el schema."""
    unique_ids = list(dict.fromkeys(cta_ids))
    for cta_id in unique_ids:
        cta = require_in_engagement(db, Cta, cta_id, engagement, "cta_ids")
        if cta.participant_id != participant_id:
            raise HTTPException(status_code=422, detail="cta_ids deben pertenecer al participante del contrato")
    return unique_ids


def _fill_review_dates(payload: dict, *, only_missing: bool) -> None:
    start = payload.get("start_date")
    if start is None:
        return
    for field, days in REVIEW_OFFSETS:
        if only_missing and field in payload:
            continue
        if payload.get(field) is None:
            payload[field] = start + timedelta(days=days)


def _sync_contract_ctas(contract: ActionContract, cta_ids: list) -> None:
    """Quita y añade vínculos sin recrear los que se mantienen (evita chocar con uq_action_contract_ctas)."""
    current = {link.cta_id: link for link in contract.ctas}
    for cta_id, link in current.items():
        if cta_id not in cta_ids:
            contract.ctas.remove(link)
    for cta_id in cta_ids:
        if cta_id not in current:
            contract.ctas.append(ActionContractCta(cta_id=cta_id))


def create_contract(db: Session, *, user: User, engagement: Engagement, data: ActionContractCreate) -> ActionContract:
    participant = require_in_engagement(db, Participant, data.participant_id, engagement, "participant_id")
    if lab_crud.get_contract_by_participant(db, engagement.id, participant.id) is not None:
        raise HTTPException(status_code=409, detail="El participante ya tiene un Leadership Action Contract")
    cta_ids = _validate_contract_ctas(db, engagement, participant.id, data.cta_ids)
    payload = data.model_dump(exclude={"cta_ids"})
    _fill_review_dates(payload, only_missing=False)
    contract = ActionContract(**_scoped_kwargs(engagement, user), **payload)
    contract.ctas = [ActionContractCta(cta_id=cta_id) for cta_id in cta_ids]
    db.add(contract)
    db.flush()
    _log(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="action_contract",
        entity_id=contract.id, summary=f'{user.full_name} created Action Contract for Participant "{participant.full_name}"',
    )
    db.commit()
    db.refresh(contract)
    return contract


def update_contract(db: Session, *, user: User, contract: ActionContract, data: ActionContractUpdate) -> ActionContract:
    payload = updates(data, nullable={"start_date", "review_30_date", "review_60_date"})
    engagement = db.get(Engagement, contract.engagement_id)
    participant_id = payload.get("participant_id", contract.participant_id)
    if participant_id != contract.participant_id:
        require_in_engagement(db, Participant, participant_id, engagement, "participant_id")
        if lab_crud.get_contract_by_participant(db, engagement.id, participant_id) is not None:
            raise HTTPException(status_code=409, detail="El participante ya tiene un Leadership Action Contract")
    requested_ids = payload.pop("cta_ids", None)
    cta_ids = _validate_contract_ctas(db, engagement, participant_id, requested_ids if requested_ids is not None else contract.cta_ids)
    if "start_date" in payload:
        _fill_review_dates(payload, only_missing=True)
    changes = diff_changes(contract, payload)
    if set(cta_ids) != set(contract.cta_ids):
        changes.append({"field": "cta_ids", "before": [str(i) for i in contract.cta_ids], "after": [str(i) for i in cta_ids]})
    if not changes:
        return contract
    for field, value in payload.items():
        setattr(contract, field, value)
    _sync_contract_ctas(contract, cta_ids)
    status_change = next((c for c in changes if c["field"] == "status"), None)
    label = _contract_label(db, contract)
    if status_change:
        action = ActivityAction.STATUS_CHANGED
        summary = f'{user.full_name} updated {label} from {status_change["before"]} to {status_change["after"]}'
    else:
        action = ActivityAction.UPDATED
        summary = f"{user.full_name} updated {label}"
    _log(db, user=user, engagement=engagement, action=action, entity_type="action_contract", entity_id=contract.id, summary=summary, changes=changes)
    db.commit()
    db.refresh(contract)
    return contract
```

- [ ] **Step 6: Añadir rutas al final de `app/routers/lab.py`**

Ampliar imports: `from app.models.enums import ContractStatus, CtaStatus, Role`; `from app.models.lab import ActionContract, Cta, LabSession, Participant, Pod`; en schemas añadir `ActionContractCreate, ActionContractRead, ActionContractUpdate`. Añadir:

```python
scoped_contract = Depends(scoped(ActionContract, "contract_id"))


@router.get("/engagements/{engagement_id}/lab/contracts", response_model=Page[ActionContractRead])
def list_contracts(
    engagement: Engagement = Depends(get_engagement),
    _: User = syner_only,
    status: ContractStatus | None = None,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = lab_crud.list_contracts(db, engagement.id, status=status, limit=pagination.limit, offset=pagination.offset)
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/lab/contracts", response_model=ActionContractRead, status_code=201)
def create_contract(
    data: ActionContractCreate,
    engagement: Engagement = Depends(get_engagement),
    user: User = syner_only,
    db: Session = Depends(get_db),
):
    return lab_service.create_contract(db, user=user, engagement=engagement, data=data)


@router.patch("/lab/contracts/{contract_id}", response_model=ActionContractRead)
def update_contract(
    data: ActionContractUpdate,
    contract: ActionContract = scoped_contract,
    user: User = syner_only,
    db: Session = Depends(get_db),
):
    return lab_service.update_contract(db, user=user, contract=contract, data=data)
```

- [ ] **Step 7: Correr los tests de la tarea y la suite completa**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest tests/test_lab_contracts.py -q -W error && .venv/bin/pytest -q -W error 2>&1 | tail -2`
Expected: `5 passed` y luego `123 passed`.

- [ ] **Step 8: Commit**

```bash
cd /mnt/d/Devs/HiTOxSyner
git add app/schemas/lab.py app/crud/lab.py app/services/lab.py app/routers/lab.py tests/test_lab_contracts.py
git commit -m "feat(lab): Leadership Action Contracts con máximo 3 CTAs, uno por participante y fechas de revisión +30/+60"
```

---

### Task 4: `/lab/summary` agregado para dirección y tarjeta Leadership Lab en el dashboard

**Files:**
- Modify: `app/schemas/lab.py`, `app/crud/lab.py`, `app/services/lab.py`, `app/routers/lab.py` (añadir al final de cada uno)
- Modify: `app/schemas/dashboard.py`, `app/services/dashboard.py`
- Test: `tests/test_lab_summary.py`

**Interfaces:**
- Consumes: crud y modelos del Lab (Tasks 1–3); `build_dashboard(db, engagement, user)` (`app/services/dashboard.py`).
- Produces:
  - Schemas `LabSessionSummary` (sin `syner_notes`), `CtaStatusTotals`, `SessionCtaBreakdown`, `PodCtaBreakdown`, `LabSummary`, `LabDashboard`.
  - Crud `cta_counts(db, engagement_id) -> dict[CtaStatus, int]`, `cta_counts_by_session(...) -> dict[session_id, dict]`, `cta_counts_by_pod(...) -> dict[pod_id, dict]`.
  - Services `build_summary(db, engagement) -> LabSummary`, `build_lab_dashboard(db, engagement, user) -> LabDashboard | None`, `can_view_lab(user) -> bool`.
  - Ruta `GET /api/engagements/{engagement_id}/lab/summary` (SYNER_ADMIN y HITO_EXECUTIVE).
  - `DashboardRead.lab: LabDashboard | None` (null para HITO_COLLABORATOR y cuando no hay sesiones).

- [ ] **Step 1: Escribir los tests**

`tests/test_lab_summary.py`:

```python
import json
from datetime import date, timedelta

from tests.factories import login

FORBIDDEN_KEYS = {"participant", "trigger", "behavior", "full_name", "syner_notes"}
SECRETS = ("Ana Ruiz", "Luis Mora", "Sofía León", "Dar feedback", "Escalar bloqueos", "Notas internas", "Cerrar reuniones", "Delegar")


def _keys(value, found=None):
    found = set() if found is None else found
    if isinstance(value, dict):
        for key, inner in value.items():
            found.add(key)
            _keys(inner, found)
    elif isinstance(value, list):
        for inner in value:
            _keys(inner, found)
    return found


def _lab(world, segment):
    return f"/api/engagements/{world.eng_a.id}/lab/{segment}"


def _populate(client, world):
    admin = login(client, "admin@syner.example")
    today = date.today()
    s1 = client.post(_lab(world, "sessions"), headers=admin, json={"number": 1, "held_on": (today - timedelta(days=7)).isoformat(), "status": "Done", "attendance_count": 18, "syner_notes": "Notas internas"}).json()
    s2 = client.post(_lab(world, "sessions"), headers=admin, json={"number": 2, "held_on": (today + timedelta(days=10)).isoformat()}).json()
    pod1 = client.post(_lab(world, "pods"), headers=admin, json={"number": 1, "name": "Pod Norte"}).json()
    pod2 = client.post(_lab(world, "pods"), headers=admin, json={"number": 2, "name": "Pod Sur"}).json()
    ana = client.post(_lab(world, "participants"), headers=admin, json={"full_name": "Ana Ruiz", "pod_id": pod1["id"]}).json()
    luis = client.post(_lab(world, "participants"), headers=admin, json={"full_name": "Luis Mora", "pod_id": pod2["id"]}).json()
    sofia = client.post(_lab(world, "participants"), headers=admin, json={"full_name": "Sofía León"}).json()

    def cta(participant, session, behavior, status=None):
        created = client.post(_lab(world, "ctas"), headers=admin, json={"participant_id": participant["id"], "session_id": session["id"], "behavior": behavior, "trigger": "Comité"}).json()
        if status:
            client.patch(f"/api/lab/ctas/{created['id']}", headers=admin, json={"status": status})
        return created

    cta(ana, s1, "Dar feedback directo", "Evidenced")
    cta(ana, s2, "Cerrar reuniones con acuerdos")
    cta(luis, s1, "Escalar bloqueos en 24 horas", "In Progress")
    cta(sofia, s1, "Delegar decisiones operativas", "Dropped")
    client.post(_lab(world, "contracts"), headers=admin, json={"participant_id": ana["id"], "status": "Active"})
    client.post(_lab(world, "contracts"), headers=admin, json={"participant_id": luis["id"]})
    return admin, s2


def test_summary_aggregates_and_hides_personal_data(client, world):
    _populate(client, world)
    response = client.get(_lab(world, "summary"), headers=login(client, "exec@a.example"))
    assert response.status_code == 200, response.text
    body = response.json()
    assert [s["number"] for s in body["sessions"]] == [1, 2]
    assert body["sessions"][0]["status"] == "Done" and body["sessions"][0]["attendance_count"] == 18
    assert body["sessions"][0]["name"] == "The Brain Under Pressure" and body["sessions"][0]["theme"] == "DECIDIR"
    assert body["sessions_done"] == 1
    assert body["cta_totals"] == {"committed": 1, "in_progress": 1, "evidenced": 1, "dropped": 1, "total": 4}
    assert body["evidenced_pct"] == 25
    assert [(b["session_number"], b["session_name"], b["totals"]["total"]) for b in body["by_session"]] == [(1, "The Brain Under Pressure", 3), (2, "Trust, Conflict & Difficult Conversations", 1)]
    assert body["by_session"][0]["totals"]["evidenced"] == 1 and body["by_session"][0]["totals"]["dropped"] == 1
    assert [(b["pod_number"], b["pod_name"], b["totals"]["total"]) for b in body["by_pod"]] == [(1, "Pod Norte", 2), (2, "Pod Sur", 1)]
    assert body["active_contracts"] == 1
    assert not (_keys(body) & FORBIDDEN_KEYS)
    text = json.dumps(body, ensure_ascii=False)
    assert all(secret not in text for secret in SECRETS)
    assert client.get(_lab(world, "summary"), headers=login(client, "admin@syner.example")).status_code == 200
    assert client.get(_lab(world, "summary"), headers=login(client, "collab@a.example")).status_code == 403
    assert client.get(_lab(world, "summary"), headers=login(client, "exec@b.example")).status_code == 404


def test_summary_for_empty_lab_returns_zeros(client, world):
    body = client.get(_lab(world, "summary"), headers=login(client, "exec@a.example")).json()
    assert body == {
        "sessions": [], "sessions_done": 0,
        "cta_totals": {"committed": 0, "in_progress": 0, "evidenced": 0, "dropped": 0, "total": 0},
        "evidenced_pct": 0, "by_session": [], "by_pod": [], "active_contracts": 0,
    }


def test_dashboard_lab_card_only_with_sessions_and_hidden_from_collaborators(client, world):
    dashboard = f"/api/engagements/{world.eng_a.id}/dashboard"
    exec_a = login(client, "exec@a.example")
    assert client.get(dashboard, headers=exec_a).json()["lab"] is None
    admin, s2 = _populate(client, world)
    lab = client.get(dashboard, headers=exec_a).json()["lab"]
    assert lab["next_session"]["number"] == 2 and lab["next_session"]["name"] == "Trust, Conflict & Difficult Conversations"
    assert lab["sessions_done"] == 1 and lab["sessions_total"] == 2
    assert lab["active_ctas"] == 2 and lab["evidenced_pct"] == 25 and lab["active_contracts"] == 1
    assert not (_keys(lab) & FORBIDDEN_KEYS)
    assert all(secret not in json.dumps(lab, ensure_ascii=False) for secret in SECRETS)
    assert client.get(dashboard, headers=login(client, "collab@a.example")).json()["lab"] is None
    assert client.get(dashboard, headers=admin).json()["lab"]["sessions_total"] == 2
    client.patch(f"/api/lab/sessions/{s2['id']}", headers=admin, json={"status": "Done"})
    after = client.get(dashboard, headers=exec_a).json()["lab"]
    assert after["next_session"] is None and after["sessions_done"] == 2
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest tests/test_lab_summary.py -q -W error`
Expected: FAIL (404 en `/lab/summary`; `KeyError: 'lab'` en el dashboard).

- [ ] **Step 3: Añadir schemas de resumen al final de `app/schemas/lab.py`**

```python
class LabSessionSummary(BaseModel):
    """Vista de sesión para dirección: calendario y asistencia, sin notas de Syner."""

    model_config = ConfigDict(from_attributes=True)

    number: int
    name: str
    theme: LabSessionTheme
    held_on: date | None
    status: LabSessionStatus
    attendance_count: int | None


class CtaStatusTotals(BaseModel):
    committed: int = 0
    in_progress: int = 0
    evidenced: int = 0
    dropped: int = 0
    total: int = 0


class SessionCtaBreakdown(BaseModel):
    session_number: int
    session_name: str
    totals: CtaStatusTotals


class PodCtaBreakdown(BaseModel):
    pod_number: int
    pod_name: str
    totals: CtaStatusTotals


class LabSummary(BaseModel):
    sessions: list[LabSessionSummary]
    sessions_done: int
    cta_totals: CtaStatusTotals
    evidenced_pct: int
    by_session: list[SessionCtaBreakdown]
    by_pod: list[PodCtaBreakdown]
    active_contracts: int


class LabDashboard(BaseModel):
    next_session: LabSessionSummary | None
    sessions_done: int
    sessions_total: int
    active_ctas: int
    evidenced_pct: int
    active_contracts: int
```

- [ ] **Step 4: Añadir agregados al final de `app/crud/lab.py`**

```python
def cta_counts(db: Session, engagement_id: uuid.UUID) -> dict[CtaStatus, int]:
    rows = db.execute(select(Cta.status, func.count()).where(Cta.engagement_id == engagement_id).group_by(Cta.status)).all()
    return {status: count for status, count in rows}


def cta_counts_by_session(db: Session, engagement_id: uuid.UUID) -> dict[uuid.UUID, dict[CtaStatus, int]]:
    rows = db.execute(
        select(Cta.session_id, Cta.status, func.count()).where(Cta.engagement_id == engagement_id).group_by(Cta.session_id, Cta.status)
    ).all()
    result: dict[uuid.UUID, dict[CtaStatus, int]] = {}
    for session_id, status, count in rows:
        result.setdefault(session_id, {})[status] = count
    return result


def cta_counts_by_pod(db: Session, engagement_id: uuid.UUID) -> dict[uuid.UUID, dict[CtaStatus, int]]:
    rows = db.execute(
        select(Participant.pod_id, Cta.status, func.count())
        .join(Participant, Participant.id == Cta.participant_id)
        .where(Cta.engagement_id == engagement_id, Participant.pod_id.is_not(None))
        .group_by(Participant.pod_id, Cta.status)
    ).all()
    result: dict[uuid.UUID, dict[CtaStatus, int]] = {}
    for pod_id, status, count in rows:
        result.setdefault(pod_id, {})[status] = count
    return result
```

- [ ] **Step 5: Añadir el resumen al final de `app/services/lab.py`**

Ampliar imports: `from app.models.enums import ACTIVE_CTA_STATUSES, LAB_SESSION_NAMES, LAB_SESSION_THEMES, ActivityAction, CtaStatus, LabSessionStatus, Role`; en schemas añadir `CtaStatusTotals, LabDashboard, LabSessionSummary, LabSummary, PodCtaBreakdown, SessionCtaBreakdown`. Añadir:

```python
# --- Resumen agregado (dirección) -------------------------------------------

def can_view_lab(user: User) -> bool:
    return user.role in (Role.SYNER_ADMIN, Role.HITO_EXECUTIVE)


def _totals(counts: dict) -> CtaStatusTotals:
    return CtaStatusTotals(
        committed=counts.get(CtaStatus.COMMITTED, 0),
        in_progress=counts.get(CtaStatus.IN_PROGRESS, 0),
        evidenced=counts.get(CtaStatus.EVIDENCED, 0),
        dropped=counts.get(CtaStatus.DROPPED, 0),
        total=sum(counts.values()),
    )


def _evidenced_pct(counts: dict) -> int:
    """Porcentaje de CTAs con status Evidenced sobre el total (incluye Dropped en el denominador)."""
    total = sum(counts.values())
    return round(100 * counts.get(CtaStatus.EVIDENCED, 0) / total) if total else 0


def build_summary(db: Session, engagement: Engagement) -> LabSummary:
    sessions = lab_crud.list_all_sessions(db, engagement.id)
    counts = lab_crud.cta_counts(db, engagement.id)
    by_session = lab_crud.cta_counts_by_session(db, engagement.id)
    by_pod = lab_crud.cta_counts_by_pod(db, engagement.id)
    return LabSummary(
        sessions=[LabSessionSummary.model_validate(s) for s in sessions],
        sessions_done=sum(1 for s in sessions if s.status == LabSessionStatus.DONE),
        cta_totals=_totals(counts),
        evidenced_pct=_evidenced_pct(counts),
        by_session=[SessionCtaBreakdown(session_number=s.number, session_name=s.name, totals=_totals(by_session.get(s.id, {}))) for s in sessions],
        by_pod=[PodCtaBreakdown(pod_number=p.number, pod_name=p.name, totals=_totals(by_pod.get(p.id, {}))) for p in lab_crud.list_all_pods(db, engagement.id)],
        active_contracts=lab_crud.count_active_contracts(db, engagement.id),
    )


def build_lab_dashboard(db: Session, engagement: Engagement, user: User) -> LabDashboard | None:
    """Tarjeta del dashboard: None para colaboradores y cuando el Lab no tiene sesiones."""
    if not can_view_lab(user):
        return None
    sessions = lab_crud.list_all_sessions(db, engagement.id)
    if not sessions:
        return None
    counts = lab_crud.cta_counts(db, engagement.id)
    next_session = next((s for s in sessions if s.status == LabSessionStatus.PLANNED), None)
    return LabDashboard(
        next_session=LabSessionSummary.model_validate(next_session) if next_session else None,
        sessions_done=sum(1 for s in sessions if s.status == LabSessionStatus.DONE),
        sessions_total=len(sessions),
        active_ctas=sum(counts.get(status, 0) for status in ACTIVE_CTA_STATUSES),
        evidenced_pct=_evidenced_pct(counts),
        active_contracts=lab_crud.count_active_contracts(db, engagement.id),
    )
```

- [ ] **Step 6: Añadir la ruta de resumen al final de `app/routers/lab.py`**

En el import de schemas añadir `LabSummary`. Añadir:

```python
summary_roles = Depends(require_roles(Role.SYNER_ADMIN, Role.HITO_EXECUTIVE))


@router.get("/engagements/{engagement_id}/lab/summary", response_model=LabSummary)
def lab_summary(
    engagement: Engagement = Depends(get_engagement),
    _: User = summary_roles,
    db: Session = Depends(get_db),
):
    return lab_service.build_summary(db, engagement)
```

- [ ] **Step 7: Añadir `lab` al dashboard**

En `app/schemas/dashboard.py` añadir el import `from app.schemas.lab import LabDashboard` y, como último campo de `DashboardRead`:

```python
    lab: LabDashboard | None = None
```

En `app/services/dashboard.py` añadir el import `from app.services.lab import build_lab_dashboard` y, como último argumento del `DashboardRead(...)` en `build_dashboard`:

```python
        lab=build_lab_dashboard(db, engagement, user),
```

- [ ] **Step 8: Correr los tests de la tarea y la suite completa**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest tests/test_lab_summary.py tests/test_dashboard.py -q -W error && .venv/bin/pytest -q -W error 2>&1 | tail -2`
Expected: `5 passed` y luego `126 passed`.

- [ ] **Step 9: Commit**

```bash
cd /mnt/d/Devs/HiTOxSyner
git add app/schemas/lab.py app/crud/lab.py app/services/lab.py app/routers/lab.py app/schemas/dashboard.py app/services/dashboard.py tests/test_lab_summary.py
git commit -m "feat(lab): resumen agregado para dirección sin datos personales y tarjeta Leadership Lab en el dashboard"
```

---

### Task 5: Migración Alembic del plan 3, seed del Lab, material ORION como Documents internos y README

**Files:**
- Create: `alembic/versions/<rev>_plan_3_leadership_lab.py` (autogenerada y revisada)
- Modify: `app/seed.py`, `tests/test_seed.py`, `README.md`

**Interfaces:**
- Consumes: services del Lab (Tasks 1–3), `documents_service.create_document`, `_is_demo_engagement`, `_has_rows`, `_initiatives` de `app/seed.py`.
- Produces: esquema de producción con `lab_sessions`, `pods`, `participants`, `ctas`, `action_contracts`, `action_contract_ctas`; seed con 4 sesiones, 4 pods, 20 participantes, 8 CTAs y 2 contratos demo (solo en el engagement demo) y 8 Documents internos de Project ORION (siempre, idempotente por nombre).

- [ ] **Step 1: Generar la migración sobre la base de desarrollo**

```bash
cd /mnt/d/Devs/HiTOxSyner
.venv/bin/alembic upgrade head
.venv/bin/alembic revision --autogenerate -m "plan 3 leadership lab"
ls alembic/versions
```
Expected: aparece `alembic/versions/<rev>_plan_3_leadership_lab.py`. Abrirlo y verificar que `upgrade()` contiene `op.create_table` para `lab_sessions`, `pods`, `participants`, `ctas`, `action_contracts`, `action_contract_ctas` (con `pods` antes que `participants`; `participants` y `lab_sessions` antes que `ctas`; `ctas` y `action_contracts` antes que `action_contract_ctas`), las `UniqueConstraint` `uq_lab_sessions_engagement_number`, `uq_pods_engagement_number`, `uq_action_contracts_participant`, `uq_action_contract_ctas`, y los índices `ix_*_engagement_id`, `ix_*_organization_id`, `ix_participants_pod_id`, `ix_ctas_participant_id`, `ix_ctas_session_id`, `ix_action_contracts_participant_id`, `ix_action_contract_ctas_contract_id`, `ix_action_contract_ctas_cta_id`. No debe haber ningún `op.add_column` ni `op.alter_column` sobre tablas existentes; si aparece alguno, el modelo y la base de desarrollo están desalineados: detenerse y revisar antes de seguir.

- [ ] **Step 2: Revisar a mano la migración**

Añadir debajo de los identificadores de revisión:

```python
ENUM_TYPES = ('lab_session_theme', 'lab_session_status', 'cta_status', 'action_contract_status')
```

Al final de `downgrade()`, después del último `op.drop_table`, añadir:

```python
    for enum_name in ENUM_TYPES:
        op.execute(f'DROP TYPE IF EXISTS "{enum_name}"')
```

Verificar que `downgrade()` elimina `action_contract_ctas` antes que `action_contracts` y `ctas`, y `ctas` antes que `participants` y `lab_sessions` (Alembic lo genera en orden inverso al `upgrade()`; si no, reordenar).

- [ ] **Step 3: Probar upgrade, downgrade y upgrade, y `alembic check`**

```bash
cd /mnt/d/Devs/HiTOxSyner
.venv/bin/alembic upgrade head
.venv/bin/alembic downgrade -1
.venv/bin/alembic upgrade head
.venv/bin/alembic check
PGPASSWORD=hitoxsyner ~/.local/pg/bin/psql -h localhost -U hitoxsyner -d hitoxsyner_dev -tAc "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('lab_sessions','pods','participants','ctas','action_contracts','action_contract_ctas') ORDER BY 1"
PGPASSWORD=hitoxsyner ~/.local/pg/bin/psql -h localhost -U hitoxsyner -d hitoxsyner_dev -tAc "SELECT typname FROM pg_type WHERE typname IN ('lab_session_theme','lab_session_status','cta_status','action_contract_status') ORDER BY 1"
```
Expected: sin errores; `alembic check` responde `No new upgrade operations detected.`; aparecen las seis tablas y los cuatro tipos enum.

- [ ] **Step 4: Actualizar `tests/test_seed.py`**

Reemplazar el archivo completo por:

```python
from sqlalchemy import delete, func, select

from app.models.action import Action
from app.models.comment import Comment
from app.models.decision import Decision
from app.models.document import Document, DocumentLink
from app.models.enums import DocumentCategory
from app.models.finding import Finding
from app.models.initiative import Initiative
from app.models.lab import ActionContract, ActionContractCta, Cta, LabSession, Participant, Pod
from app.models.meeting import Meeting
from app.models.milestone import Milestone
from app.models.user import User
from app.seed import ORION_DOCUMENTS, seed


def _count(db, model):
    return db.scalar(select(func.count()).select_from(model))


def _login(client, email, password):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


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
    assert _count(db, Document) == 5 + len(ORION_DOCUMENTS)
    assert _count(db, DocumentLink) == 3
    assert _count(db, Comment) == 2
    assert _count(db, LabSession) == 4
    assert _count(db, Pod) == 4
    assert _count(db, Participant) == 20
    assert _count(db, Cta) == 8
    assert _count(db, ActionContract) == 2
    assert _count(db, ActionContractCta) == 3
    titles = (
        list(db.scalars(select(Finding.title))) + list(db.scalars(select(Milestone.name)))
        + list(db.scalars(select(Participant.full_name))) + list(db.scalars(select(Pod.name)))
    )
    assert all(t.startswith("[Demo]") for t in titles)
    names = list(db.scalars(select(Document.name)))
    assert sum(1 for n in names if n.startswith("[Demo]")) == 5
    orion = list(db.scalars(select(Document).where(Document.category == DocumentCategory.DELIVERABLES, Document.internal_only.is_(True))))
    assert {d.name for d in orion} == {name for name, _, _ in ORION_DOCUMENTS}
    assert all("orion" in d.tags and d.url == "" for d in orion)
    assert db.scalar(select(func.count()).select_from(Document).where(Document.internal_only.is_(True))) == 1 + len(ORION_DOCUMENTS)
    admin = _login(client, "admin@syner.demo", "syner-demo")
    engagement_id = client.get("/api/engagements", headers=admin).json()[0]["id"]
    assert client.get(f"/api/engagements/{engagement_id}/documents", headers=admin).json()["total"] == 5 + len(ORION_DOCUMENTS)
    exec_headers = _login(client, "exec@hito.demo", "exec-demo")
    assert client.get(f"/api/engagements/{engagement_id}/documents", headers=exec_headers).json()["total"] == 4
    summary = client.get(f"/api/engagements/{engagement_id}/lab/summary", headers=exec_headers).json()
    assert summary["cta_totals"]["total"] == 8 and summary["sessions_done"] == 2 and summary["active_contracts"] == 1


def test_seed_skips_demo_modules_when_engagement_has_real_initiatives(db, client):
    seed(db)
    real = db.scalar(select(Initiative).order_by(Initiative.created_at))
    real.name = "Iniciativa real del cliente"
    for model in (ActionContractCta, ActionContract, Cta, Participant, Pod, LabSession, Milestone):
        db.execute(delete(model))
    db.commit()
    seed(db)
    assert _count(db, Milestone) == 0
    assert _count(db, LabSession) == 0
    assert _count(db, Participant) == 0
    assert _count(db, Meeting) == 3
    assert _count(db, Document) == 5 + len(ORION_DOCUMENTS)
```

- [ ] **Step 5: Correr el test de seed para verificar que falla**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest tests/test_seed.py -q -W error`
Expected: FAIL con `ImportError: cannot import name 'ORION_DOCUMENTS'`.

- [ ] **Step 6: Ampliar `app/seed.py`**

Añadir a los imports:

```python
from app.models.lab import LabSession
from app.schemas.lab import ActionContractCreate, CtaCreate, LabSessionCreate, ParticipantCreate, PodCreate
from app.services import lab as lab_service
```

Añadir después de `_is_demo_engagement` (antes de `_seed_client_room`) la constante y las dos funciones:

```python
ORION_DOCUMENTS = [
    ("Executive Leadership Lab — Facilitator Playbook", "0.9", "HITO_Executive_Leadership_Lab_Facilitator_Playbook_v0.9.pdf"),
    ("Project ORION — Leadership Pressure Room Case Book (ES)", "1.0", "HITO_Leadership_Pressure_Room_Project_ORION_Case_Book_ES_v1.0.pdf"),
    ("Project ORION — Participant Handout Master (ES)", "1.0", "HITO_Participant_Handout_Master_Project_ORION_ES_v1.0.pdf"),
    ("Project ORION — Participant Packet 00: Pre-Work (ES)", "1.0", "HITO_Participant_Packet_00_PreWork_ORION_ES_v1.0.pdf"),
    ("Project ORION — Participant Packet 01: Lab 01 DECIDIR (ES)", "1.0", "HITO_Participant_Packet_01_Lab01_DECIDIR_ORION_ES_v1.0.pdf"),
    ("Project ORION — Participant Packet 02: Lab 02 CONFRONTAR (ES)", "1.0", "HITO_Participant_Packet_02_Lab02_CONFRONTAR_ORION_ES_v1.0.pdf"),
    ("Project ORION — Participant Packet 03: Lab 03 ALINEAR (ES)", "1.0", "HITO_Participant_Packet_03_Lab03_ALINEAR_ORION_ES_v1.0.pdf"),
    ("Project ORION — Participant Packet 04: Lab 04 TRANSFORMAR (ES)", "1.0", "HITO_Participant_Packet_04_Lab04_TRANSFORMAR_ORION_ES_v1.0.pdf"),
]


def _seed_orion_documents(db: Session, admin: User, engagement: Engagement) -> None:
    """Material del Executive Leadership Lab / Project ORION registrado como Documents internos (spec sección 7).

    No es dato demo: se registra siempre, idempotente por nombre. La URL queda vacía porque el primer release
    no integra almacenamiento documental; Syner la completa desde la UI cuando publique los archivos.
    """
    existing = set(db.scalars(select(Document.name).where(Document.engagement_id == engagement.id)))
    for name, version, filename in ORION_DOCUMENTS:
        if name in existing:
            continue
        documents_service.create_document(
            db, user=admin, engagement=engagement,
            data=DocumentCreate(
                name=name, category="Deliverables", version=version, url="", tags=["orion", "leadership-lab"],
                internal_only=True, description=f"Material del Executive Leadership Lab / Project ORION. Archivo fuente: docs/{filename}",
            ),
        )
    db.commit()


def _seed_lab(db: Session, admin: User, engagement: Engagement) -> None:
    """Sesiones, pods, participantes, CTAs y contratos demo del plan 3. Todo ficticio, con prefijo [Demo]."""
    today = date.today()
    if not _is_demo_engagement(_initiatives(db, engagement)):
        print("Seed: el engagement no contiene el set demo de initiatives; se omiten los datos demo del Lab.")
        return
    if _has_rows(db, LabSession, engagement):
        return
    sessions = []
    for number, days, status, attendance in ((1, -20, "Done", 18), (2, -6, "Done", 17), (3, 8, "Planned", None), (4, 22, "Planned", None)):
        sessions.append(lab_service.create_session(
            db, user=admin, engagement=engagement,
            data=LabSessionCreate(number=number, held_on=today + timedelta(days=days), status=status, attendance_count=attendance, syner_notes="[Demo] Notas internas de facilitación." if status == "Done" else ""),
        ))
    pods = [
        lab_service.create_pod(db, user=admin, engagement=engagement, data=PodCreate(number=number, name=f"[Demo] Pod {name}"))
        for number, name in ((1, "Norte"), (2, "Sur"), (3, "Centro"), (4, "Bajío"))
    ]
    areas = ("Operaciones", "Finanzas", "Comercial", "Tecnología", "Personas")
    participants = [
        lab_service.create_participant(
            db, user=admin, engagement=engagement,
            data=ParticipantCreate(full_name=f"[Demo] Participante {i + 1:02d}", area=areas[i % 5], title="Gerente (demo)", pod_id=pods[i % 4].id),
        )
        for i in range(20)
    ]
    ctas = []
    for participant_idx, session_idx, status in ((0, 0, "Evidenced"), (0, 1, "In Progress"), (1, 0, "Evidenced"), (1, 1, "Committed"), (2, 0, "Evidenced"), (3, 0, "In Progress"), (4, 1, "In Progress"), (5, 0, "Dropped")):
        ctas.append(lab_service.create_cta(
            db, user=admin, engagement=engagement,
            data=CtaCreate(
                participant_id=participants[participant_idx].id, session_id=sessions[session_idx].id,
                trigger="[Demo] Situación de presión en comité.", behavior="[Demo] Conducta comprometida de demostración.",
                stakeholder="Equipo directo (demo)", evidence_expected="[Demo] Evidencia esperada.", due_date=today + timedelta(days=14),
                accountability_partner="[Demo] Partner", impact="[Demo] Impacto esperado.", status=status,
                evidence_notes="[Demo] Evidencia registrada." if status == "Evidenced" else "",
            ),
        ))
    lab_service.create_contract(
        db, user=admin, engagement=engagement,
        data=ActionContractCreate(participant_id=participants[0].id, start_date=today - timedelta(days=5), success_signal="[Demo] Señal de éxito observable.", status="Active", cta_ids=[ctas[0].id, ctas[1].id]),
    )
    lab_service.create_contract(
        db, user=admin, engagement=engagement,
        data=ActionContractCreate(participant_id=participants[1].id, success_signal="[Demo] Pendiente de activar.", status="Draft", cta_ids=[ctas[2].id]),
    )
    db.commit()
```

Y al final de `seed()`, después de `_seed_client_room(db, admin, collab, engagement)`:

```python
    _seed_lab(db, admin, engagement)
    _seed_orion_documents(db, admin, engagement)
```

- [ ] **Step 7: Correr la suite y el seed en dev**

```bash
cd /mnt/d/Devs/HiTOxSyner
.venv/bin/pytest tests/test_seed.py -q -W error
.venv/bin/pytest -q -W error 2>&1 | tail -2
.venv/bin/python -m app.seed
.venv/bin/python -m app.seed
PGPASSWORD=hitoxsyner ~/.local/pg/bin/psql -h localhost -U hitoxsyner -d hitoxsyner_dev -tAc "SELECT (SELECT count(*) FROM lab_sessions), (SELECT count(*) FROM participants), (SELECT count(*) FROM ctas), (SELECT count(*) FROM action_contracts), (SELECT count(*) FROM documents WHERE internal_only)"
```
Expected: `2 passed`; `126 passed`; dos veces `Seed completado.`; `4|20|8|2|9`.

- [ ] **Step 8: README**

En `README.md`, reemplazar el paso 4 de "Desarrollo local" por:

```markdown
4. `python -m app.seed` (usuarios demo: `admin@syner.demo`, `exec@hito.demo`, `collab@hito.demo`; passwords desde `SEED_*_PASSWORD`). Crea datos `[Demo]` para findings, initiatives, actions, milestones, meetings, decisions, documents, comments y Leadership Lab (4 sesiones, 4 pods, 20 participantes, 8 CTAs, 2 contratos); es idempotente por módulo y solo añade datos demo cuando el engagement contiene las 4 initiatives `[Demo]`. Además registra siempre (idempotente por nombre) los 8 PDFs de Project ORION de `docs/` como Documents internos de categoría Deliverables, con URL vacía hasta que Syner la complete.
```

- [ ] **Step 9: Commit**

```bash
cd /mnt/d/Devs/HiTOxSyner
git add alembic/versions app/seed.py tests/test_seed.py README.md
git commit -m "feat: migración del plan 3, seed del Leadership Lab y material ORION como Documents internos"
```

---

### Task 6: Frontend: tipos, API, labels, página `/lab` con pestañas Sessions y Participants & Pods, y vista de resumen para dirección

**Files:**
- Modify: `frontend/src/types.ts` (añadir al final y añadir `lab` a `Dashboard`), `frontend/src/lib/labels.ts` (añadir al final), `frontend/src/components/StatusBadge.tsx` (tonos), `frontend/src/components/Sidebar.tsx`, `frontend/src/router.tsx`
- Create: `frontend/src/api/lab.ts`, `frontend/src/pages/LabPage.tsx`, `frontend/src/components/lab/SessionsTab.tsx`, `frontend/src/components/lab/ParticipantsTab.tsx`, `frontend/src/components/lab/LabSummaryView.tsx`
- Delete: `frontend/src/pages/ComingSoonPage.tsx`

**Interfaces:**
- Consumes: rutas del backend de Tasks 1–4; `useResource`, `DataTable`, `FormDrawer`, `Field`, `Select`, `PageHeader`, `EmptyState`, `StatusBadge`; `can(user, "manageLab" | "viewLabSummary")` (ya existe en `lib/roles.ts`).
- Produces:
  - Tipos `LabTheme`, `LabSessionStatus`, `LabSession`, `Pod`, `Participant`, `CtaStatus`, `Cta`, `ContractStatus`, `ActionContract`, `CtaStatusTotals`, `LabSessionSummary`, `LabSummary`, `LabDashboard`; `Dashboard.lab: LabDashboard | null`.
  - `labApi` con `sessions`, `pods`, `participants`, `ctas`, `contracts` (cada uno `list(engagementId, params?)`, `create(engagementId, data)`, `update(id, data)`) y `summary(engagementId)`; tipos `LabSessionInput`, `PodInput`, `ParticipantInput`, `CtaInput`, `ContractInput`.
  - Labels `LAB_SESSION_STATUSES`, `CTA_STATUSES`, `CONTRACT_STATUSES`, `LAB_THEMES`, `LAB_SESSION_CATALOG`, `LabTab`, `LAB_TABS` (Task 7 añade dos pestañas).
  - `LabPage` (`/lab`): pestañas para SYNER_ADMIN; para HITO_EXECUTIVE renderiza `LabSummaryView` (tiles, sesiones y barras de CTAs por status, sin nombres ni textos); redirige a `/` a HITO_COLLABORATOR.
  - `CtaStatusBar({ totals })` exportado desde `components/lab/LabSummaryView.tsx` (barra apilada por status, reutilizable).

- [ ] **Step 1: Añadir tipos al final de `frontend/src/types.ts`**

```ts
export type LabTheme = "DECIDIR" | "CONFRONTAR" | "ALINEAR" | "TRANSFORMAR";
export type LabSessionStatus = "Planned" | "Done" | "Cancelled";

export interface LabSession {
  id: string;
  engagement_id: string;
  number: number;
  name: string;
  theme: LabTheme;
  held_on: string | null;
  status: LabSessionStatus;
  attendance_count: number | null;
  syner_notes: string;
  created_at: string;
  updated_at: string;
}

export interface Pod {
  id: string;
  engagement_id: string;
  number: number;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface Participant {
  id: string;
  engagement_id: string;
  full_name: string;
  area: string;
  title: string;
  pod_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type CtaStatus = "Committed" | "In Progress" | "Evidenced" | "Dropped";

export interface Cta {
  id: string;
  engagement_id: string;
  participant_id: string;
  session_id: string;
  trigger: string;
  behavior: string;
  stakeholder: string;
  evidence_expected: string;
  due_date: string | null;
  accountability_partner: string;
  impact: string;
  status: CtaStatus;
  evidence_notes: string;
  created_at: string;
  updated_at: string;
}

export type ContractStatus = "Draft" | "Active" | "Reviewed 30" | "Reviewed 60" | "Closed";

export interface ActionContract {
  id: string;
  engagement_id: string;
  participant_id: string;
  start_date: string | null;
  review_30_date: string | null;
  review_60_date: string | null;
  success_signal: string;
  status: ContractStatus;
  cta_ids: string[];
  created_at: string;
  updated_at: string;
}

export interface CtaStatusTotals {
  committed: number;
  in_progress: number;
  evidenced: number;
  dropped: number;
  total: number;
}

export interface LabSessionSummary {
  number: number;
  name: string;
  theme: LabTheme;
  held_on: string | null;
  status: LabSessionStatus;
  attendance_count: number | null;
}

export interface LabSummary {
  sessions: LabSessionSummary[];
  sessions_done: number;
  cta_totals: CtaStatusTotals;
  evidenced_pct: number;
  by_session: { session_number: number; session_name: string; totals: CtaStatusTotals }[];
  by_pod: { pod_number: number; pod_name: string; totals: CtaStatusTotals }[];
  active_contracts: number;
}

export interface LabDashboard {
  next_session: LabSessionSummary | null;
  sessions_done: number;
  sessions_total: number;
  active_ctas: number;
  evidenced_pct: number;
  active_contracts: number;
}
```

Y en la interfaz `Dashboard`, después de `next_milestones: Milestone[];`, añadir:

```ts
  lab: LabDashboard | null;
```

- [ ] **Step 2: Añadir labels al final de `frontend/src/lib/labels.ts`**

```ts
export const LAB_SESSION_STATUSES = ["Planned", "Done", "Cancelled"] as const;
export const CTA_STATUSES = ["Committed", "In Progress", "Evidenced", "Dropped"] as const;
export const CONTRACT_STATUSES = ["Draft", "Active", "Reviewed 30", "Reviewed 60", "Closed"] as const;
export const LAB_THEMES = ["DECIDIR", "CONFRONTAR", "ALINEAR", "TRANSFORMAR"] as const;
export const LAB_SESSION_CATALOG = [
  { number: 1, name: "The Brain Under Pressure", theme: "DECIDIR" },
  { number: 2, name: "Trust, Conflict & Difficult Conversations", theme: "CONFRONTAR" },
  { number: 3, name: "From Silos to Flow", theme: "ALINEAR" },
  { number: 4, name: "AI, Judgment & Collective Accountability", theme: "TRANSFORMAR" },
] as const;

export type LabTab = "sessions" | "participants" | "ctas" | "contracts";
export const LAB_TABS: { key: LabTab; label: string }[] = [
  { key: "sessions", label: "Sessions" },
  { key: "participants", label: "Participants & Pods" },
];
```

- [ ] **Step 3: Añadir tonos a `frontend/src/components/StatusBadge.tsx`**

Dentro del objeto `TONES`, después de la línea `Interno: ...`, añadir:

```ts
  Evidenced: "bg-emerald-50 text-emerald-800 border-emerald-200",
  Dropped: "bg-gray-100 text-gray-700 border-gray-200",
  Active: "bg-emerald-50 text-emerald-800 border-emerald-200",
  Draft: "bg-gray-100 text-gray-700 border-gray-200",
  "Reviewed 30": "bg-amber-50 text-amber-800 border-amber-200",
  "Reviewed 60": "bg-amber-50 text-amber-800 border-amber-200",
```

- [ ] **Step 4: Crear `frontend/src/api/lab.ts`**

```ts
import { api } from "./client";
import type { ActionContract, Cta, LabSession, LabSummary, Page, Participant, Pod } from "../types";

type Input<T> = Partial<Omit<T, "id" | "engagement_id" | "created_at" | "updated_at">>;
export type LabSessionInput = Input<LabSession>;
export type PodInput = Input<Pod>;
export type ParticipantInput = Input<Participant>;
export type CtaInput = Input<Cta>;
export type ContractInput = Input<ActionContract>;

function resource<T, I>(segment: string) {
  return {
    list: (engagementId: string, params: Record<string, string | undefined> = {}) =>
      api.get<Page<T>>(`/engagements/${engagementId}/lab/${segment}`, { params: { ...params, limit: 200 } }).then((r) => r.data),
    create: (engagementId: string, data: I) => api.post<T>(`/engagements/${engagementId}/lab/${segment}`, data).then((r) => r.data),
    update: (id: string, data: I) => api.patch<T>(`/lab/${segment}/${id}`, data).then((r) => r.data),
  };
}

export const labApi = {
  sessions: resource<LabSession, LabSessionInput>("sessions"),
  pods: resource<Pod, PodInput>("pods"),
  participants: resource<Participant, ParticipantInput>("participants"),
  ctas: resource<Cta, CtaInput>("ctas"),
  contracts: resource<ActionContract, ContractInput>("contracts"),
  summary: (engagementId: string) => api.get<LabSummary>(`/engagements/${engagementId}/lab/summary`).then((r) => r.data),
};
```

- [ ] **Step 5: Crear `frontend/src/components/lab/SessionsTab.tsx`**

```tsx
import { FormEvent, useState } from "react";
import { errorMessage } from "../../api/client";
import { labApi, LabSessionInput } from "../../api/lab";
import { useResource } from "../../hooks/useResource";
import { formatDate } from "../../lib/dates";
import { LAB_SESSION_CATALOG, LAB_SESSION_STATUSES } from "../../lib/labels";
import type { LabSession } from "../../types";
import { DataTable } from "../DataTable";
import { EmptyState } from "../EmptyState";
import { Field, Select } from "../Field";
import { FormDrawer } from "../FormDrawer";
import { StatusBadge } from "../StatusBadge";

const EMPTY: LabSessionInput = { number: 1, held_on: null, status: "Planned", attendance_count: null, syner_notes: "" };

export function SessionsTab({ engagementId }: { engagementId: string }) {
  const { data, loading, error, reload } = useResource(() => labApi.sessions.list(engagementId), [engagementId]);
  const [editing, setEditing] = useState<LabSession | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<LabSessionInput>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const items = data?.items ?? [];
  const used = new Set(items.map((s) => s.number));
  const available = LAB_SESSION_CATALOG.filter((c) => !used.has(c.number));
  const set = (key: keyof LabSessionInput, value: unknown) => setForm((f) => ({ ...f, [key]: value }));

  function openCreate() { setEditing(null); setForm({ ...EMPTY, number: available[0]?.number ?? 1 }); setFormError(null); setOpen(true); }
  function openEdit(s: LabSession) {
    setEditing(s);
    setForm({ held_on: s.held_on, status: s.status, attendance_count: s.attendance_count, syner_notes: s.syner_notes });
    setFormError(null); setOpen(true);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    try {
      if (editing) await labApi.sessions.update(editing.id, form);
      else await labApi.sessions.create(engagementId, form);
      setOpen(false);
      await reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  return (
    <>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted">Cuatro sesiones del programa: DECIDIR, CONFRONTAR, ALINEAR y TRANSFORMAR.</p>
        {available.length > 0 && <button className="btn btn-primary" onClick={openCreate}>Nueva sesión</button>}
      </div>
      {error && <p className="mb-4 text-sm text-danger">{error}</p>}
      {loading && !data ? <p className="text-sm text-muted">Cargando…</p> : (
        <DataTable<LabSession>
          rows={items}
          onRowClick={openEdit}
          empty={<EmptyState title="Sin sesiones" hint="Programa la primera sesión del Lab." />}
          columns={[
            { key: "number", header: "#", render: (s) => <span className="tabular-nums">{s.number}</span> },
            { key: "name", header: "Sesión", render: (s) => <span className="font-medium">{s.name}<span className="block text-xs font-normal text-muted">{s.theme}</span></span> },
            { key: "date", header: "Fecha", render: (s) => formatDate(s.held_on), className: "tabular-nums" },
            { key: "status", header: "Status", render: (s) => <StatusBadge value={s.status} /> },
            { key: "attendance", header: "Asistencia", render: (s) => <span className="tabular-nums">{s.attendance_count ?? "—"}</span> },
            { key: "notes", header: "Notas Syner", render: (s) => <span className="line-clamp-2 text-xs text-muted">{s.syner_notes || "—"}</span> },
          ]}
        />
      )}
      <FormDrawer open={open} title={editing ? `Sesión ${editing.number} · ${editing.name}` : "Nueva sesión"} onClose={() => setOpen(false)} onSubmit={submit} submitting={busy} error={formError}>
        {!editing && (
          <Field label="Sesión">
            <select className="input" value={form.number ?? 1} onChange={(e) => set("number", Number(e.target.value))}>
              {available.map((c) => <option key={c.number} value={c.number}>{c.number}. {c.name} · {c.theme}</option>)}
            </select>
          </Field>
        )}
        <div className="grid grid-cols-2 gap-3">
          <Field label="Fecha"><input className="input" type="date" value={form.held_on ?? ""} onChange={(e) => set("held_on", e.target.value || null)} /></Field>
          <Field label="Status"><Select value={form.status ?? "Planned"} onChange={(v) => set("status", v)} options={LAB_SESSION_STATUSES} /></Field>
          <Field label="Asistencia"><input className="input" type="number" min={0} value={form.attendance_count ?? ""} onChange={(e) => set("attendance_count", e.target.value === "" ? null : Number(e.target.value))} /></Field>
        </div>
        <Field label="Notas Syner (solo equipo Syner)"><textarea className="input" rows={4} value={form.syner_notes ?? ""} onChange={(e) => set("syner_notes", e.target.value)} maxLength={10000} /></Field>
      </FormDrawer>
    </>
  );
}
```

- [ ] **Step 6: Crear `frontend/src/components/lab/ParticipantsTab.tsx`**

```tsx
import { FormEvent, useState } from "react";
import { errorMessage } from "../../api/client";
import { labApi, ParticipantInput } from "../../api/lab";
import { useResource } from "../../hooks/useResource";
import type { Participant } from "../../types";
import { DataTable } from "../DataTable";
import { EmptyState } from "../EmptyState";
import { Field, Select } from "../Field";
import { FormDrawer } from "../FormDrawer";

const EMPTY: ParticipantInput = { full_name: "", area: "", title: "", pod_id: null, is_active: true };

export function ParticipantsTab({ engagementId }: { engagementId: string }) {
  const participants = useResource(() => labApi.participants.list(engagementId), [engagementId]);
  const pods = useResource(() => labApi.pods.list(engagementId), [engagementId]);
  const [editing, setEditing] = useState<Participant | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<ParticipantInput>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [rowError, setRowError] = useState<string | null>(null);
  const [newPodName, setNewPodName] = useState("");
  const [podError, setPodError] = useState<string | null>(null);

  const rows = participants.data?.items ?? [];
  const podList = pods.data?.items ?? [];
  const set = (key: keyof ParticipantInput, value: unknown) => setForm((f) => ({ ...f, [key]: value }));

  function openCreate() { setEditing(null); setForm(EMPTY); setFormError(null); setOpen(true); }
  function openEdit(p: Participant) {
    setEditing(p);
    setForm({ full_name: p.full_name, area: p.area, title: p.title, pod_id: p.pod_id, is_active: p.is_active });
    setFormError(null); setOpen(true);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    try {
      if (editing) await labApi.participants.update(editing.id, form);
      else await labApi.participants.create(engagementId, form);
      setOpen(false);
      await participants.reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  async function assignPod(p: Participant, podId: string | null) {
    setRowError(null);
    try {
      await labApi.participants.update(p.id, { pod_id: podId });
      await participants.reload();
    } catch (err) { setRowError(errorMessage(err)); }
  }

  async function addPod(e: FormEvent) {
    e.preventDefault();
    const name = newPodName.trim();
    if (!name) return;
    setPodError(null);
    try {
      await labApi.pods.create(engagementId, { number: Math.max(0, ...podList.map((p) => p.number)) + 1, name });
      setNewPodName("");
      await pods.reload();
    } catch (err) { setPodError(errorMessage(err)); }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2">
        <div className="mb-4 flex items-center justify-between gap-3">
          <p className="text-sm text-muted">{rows.filter((p) => p.is_active).length} participantes activos</p>
          <button className="btn btn-primary" onClick={openCreate}>Nuevo participante</button>
        </div>
        {(participants.error || rowError) && <p className="mb-4 text-sm text-danger">{participants.error ?? rowError}</p>}
        {participants.loading && !participants.data ? <p className="text-sm text-muted">Cargando…</p> : (
          <DataTable<Participant>
            rows={rows}
            onRowClick={openEdit}
            empty={<EmptyState title="Sin participantes" hint="Registra a los participantes del Lab." />}
            columns={[
              { key: "name", header: "Participante", render: (p) => (
                <span className="font-medium">
                  <span className={p.is_active ? "" : "text-muted line-through"}>{p.full_name}</span>
                  <span className="block text-xs font-normal text-muted">{p.title || "—"}</span>
                </span>
              ) },
              { key: "area", header: "Área", render: (p) => p.area || "—" },
              { key: "pod", header: "Pod", render: (p) => (
                <select
                  className="input py-1"
                  value={p.pod_id ?? ""}
                  aria-label={`Pod de ${p.full_name}`}
                  onClick={(e) => e.stopPropagation()}
                  onChange={(e) => assignPod(p, e.target.value || null)}
                >
                  <option value="">Sin pod</option>
                  {podList.map((pod) => <option key={pod.id} value={pod.id}>{pod.name}</option>)}
                </select>
              ) },
              { key: "active", header: "Estado", render: (p) => <span className="text-xs text-muted">{p.is_active ? "Activo" : "Inactivo"}</span> },
            ]}
          />
        )}
      </div>
      <section className="card p-5">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">Pods</h2>
        {pods.error && <p className="mb-3 text-sm text-danger">{pods.error}</p>}
        {podList.length === 0 ? <p className="text-sm text-muted">Sin pods.</p> : (
          <ul className="space-y-2">
            {podList.map((pod) => (
              <li key={pod.id} className="flex items-center justify-between text-sm">
                <span>{pod.number}. {pod.name}</span>
                <span className="text-xs tabular-nums text-muted">{rows.filter((p) => p.pod_id === pod.id).length} participantes</span>
              </li>
            ))}
          </ul>
        )}
        <form onSubmit={addPod} className="mt-4 flex gap-2">
          <input className="input" value={newPodName} onChange={(e) => setNewPodName(e.target.value)} placeholder="Nombre del pod" maxLength={200} aria-label="Nombre del nuevo pod" />
          <button type="submit" className="btn" disabled={!newPodName.trim()}>Añadir</button>
        </form>
        {podError && <p className="mt-2 text-sm text-danger">{podError}</p>}
      </section>
      <FormDrawer open={open} title={editing ? "Editar participante" : "Nuevo participante"} onClose={() => setOpen(false)} onSubmit={submit} submitting={busy} error={formError}>
        <Field label="Nombre"><input className="input" value={form.full_name ?? ""} onChange={(e) => set("full_name", e.target.value)} required maxLength={200} /></Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Cargo"><input className="input" value={form.title ?? ""} onChange={(e) => set("title", e.target.value)} maxLength={200} /></Field>
          <Field label="Área"><input className="input" value={form.area ?? ""} onChange={(e) => set("area", e.target.value)} maxLength={120} /></Field>
          <Field label="Pod">
            <select className="input" value={form.pod_id ?? ""} onChange={(e) => set("pod_id", e.target.value || null)}>
              <option value="">Sin pod</option>
              {podList.map((pod) => <option key={pod.id} value={pod.id}>{pod.name}</option>)}
            </select>
          </Field>
          <Field label="Estado"><Select value={form.is_active === false ? "Inactivo" : "Activo"} onChange={(v) => set("is_active", v === "Activo")} options={["Activo", "Inactivo"]} /></Field>
        </div>
      </FormDrawer>
    </div>
  );
}
```

- [ ] **Step 7: Crear `frontend/src/components/lab/LabSummaryView.tsx` (vista de dirección)**

```tsx
import { labApi } from "../../api/lab";
import { useResource } from "../../hooks/useResource";
import { formatDate } from "../../lib/dates";
import type { CtaStatusTotals } from "../../types";
import { EmptyState } from "../EmptyState";
import { PageHeader } from "../PageHeader";
import { StatusBadge } from "../StatusBadge";
import { Tile } from "../Tile";

const SEGMENTS: { key: keyof Omit<CtaStatusTotals, "total">; label: string; className: string }[] = [
  { key: "evidenced", label: "Evidenced", className: "bg-accent" },
  { key: "in_progress", label: "In Progress", className: "bg-warn" },
  { key: "committed", label: "Committed", className: "bg-gray-400" },
  { key: "dropped", label: "Dropped", className: "bg-gray-200" },
];

export function CtaStatusBar({ totals }: { totals: CtaStatusTotals }) {
  if (totals.total === 0) return <div className="h-2 w-full rounded bg-line" role="img" aria-label="Sin CTAs" />;
  return (
    <div className="flex h-2 w-full overflow-hidden rounded bg-line" role="img" aria-label={SEGMENTS.map((s) => `${s.label}: ${totals[s.key]}`).join(", ")}>
      {SEGMENTS.filter((s) => totals[s.key] > 0).map((s) => (
        <div key={s.key} className={s.className} style={{ width: `${(100 * totals[s.key]) / totals.total}%` }} title={`${s.label}: ${totals[s.key]}`} />
      ))}
    </div>
  );
}

export function CtaLegend() {
  return (
    <p className="flex flex-wrap gap-4 text-xs text-muted">
      {SEGMENTS.map((s) => (
        <span key={s.key} className="flex items-center gap-1"><span className={`inline-block h-2 w-2 rounded ${s.className}`} />{s.label}</span>
      ))}
    </p>
  );
}

function Breakdown({ title, rows }: { title: string; rows: { key: number; label: string; totals: CtaStatusTotals }[] }) {
  return (
    <section className="card p-5">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">{title}</h2>
      {rows.length === 0 ? <p className="text-sm text-muted">Sin datos.</p> : (
        <ul className="space-y-3">
          {rows.map((r) => (
            <li key={r.key} className="text-sm">
              <div className="mb-1 flex items-center justify-between gap-3">
                <span>{r.label}</span>
                <span className="text-xs tabular-nums text-muted">{r.totals.evidenced}/{r.totals.total} con evidencia</span>
              </div>
              <CtaStatusBar totals={r.totals} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function LabSummaryView({ engagementId }: { engagementId: string }) {
  const { data, loading, error } = useResource(() => labApi.summary(engagementId), [engagementId]);
  if (loading && !data) return <p className="text-sm text-muted">Cargando…</p>;
  if (error || !data) return <p className="text-sm text-danger">{error}</p>;
  const activeCtas = data.cta_totals.committed + data.cta_totals.in_progress;
  return (
    <>
      <PageHeader title="Executive Leadership Lab" subtitle="Avance agregado del programa de liderazgo" />
      {data.sessions.length === 0 ? <EmptyState title="El Lab aún no tiene sesiones programadas" /> : (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Tile label="Sesiones realizadas" value={`${data.sessions_done}/${data.sessions.length}`} />
            <Tile label="CTAs activos" value={activeCtas} />
            <Tile label="CTAs con evidencia" value={`${data.evidenced_pct}%`} tone={data.evidenced_pct >= 50 ? "ok" : "default"} />
            <Tile label="Contratos activos" value={data.active_contracts} />
          </div>
          <section className="card p-5">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">Sesiones</h2>
            <ul className="divide-y divide-line">
              {data.sessions.map((s) => (
                <li key={s.number} className="flex flex-wrap items-center justify-between gap-3 py-2 text-sm">
                  <span className="font-medium">{s.number}. {s.name}<span className="block text-xs font-normal text-muted">{s.theme}</span></span>
                  <span className="flex items-center gap-3 text-xs tabular-nums text-muted">
                    <span>{formatDate(s.held_on)}</span>
                    <span>{s.attendance_count !== null ? `${s.attendance_count} asistentes` : "—"}</span>
                    <StatusBadge value={s.status} />
                  </span>
                </li>
              ))}
            </ul>
          </section>
          <div className="grid gap-6 lg:grid-cols-2">
            <Breakdown title="CTAs por sesión" rows={data.by_session.map((b) => ({ key: b.session_number, label: `${b.session_number}. ${b.session_name}`, totals: b.totals }))} />
            <Breakdown title="CTAs por pod" rows={data.by_pod.map((b) => ({ key: b.pod_number, label: `${b.pod_number}. ${b.pod_name}`, totals: b.totals }))} />
          </div>
          <CtaLegend />
        </div>
      )}
    </>
  );
}
```

- [ ] **Step 8: Crear `frontend/src/pages/LabPage.tsx`**

```tsx
import { Navigate, useSearchParams } from "react-router-dom";
import { LabSummaryView } from "../components/lab/LabSummaryView";
import { ParticipantsTab } from "../components/lab/ParticipantsTab";
import { SessionsTab } from "../components/lab/SessionsTab";
import { PageHeader } from "../components/PageHeader";
import { LAB_TABS, type LabTab } from "../lib/labels";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";

export function LabPage() {
  const user = useAuthStore((s) => s.user);
  const engagementId = useEngagementStore((s) => s.current?.id ?? "");
  const [params, setParams] = useSearchParams();
  if (!can(user, "viewLabSummary")) return <Navigate to="/" replace />;
  if (!can(user, "manageLab")) return <LabSummaryView engagementId={engagementId} />;
  const tab: LabTab = LAB_TABS.find((t) => t.key === params.get("tab"))?.key ?? "sessions";
  return (
    <>
      <PageHeader title="Executive Leadership Lab" subtitle="Sesiones, participantes, CTA tracker y Leadership Action Contracts" />
      <nav className="mb-5 flex flex-wrap gap-1 border-b border-line" aria-label="Secciones del Lab">
        {LAB_TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            className={`-mb-px border-b-2 px-3 py-2 text-sm ${tab === t.key ? "border-ink font-medium text-ink" : "border-transparent text-muted hover:text-ink"}`}
            aria-current={tab === t.key ? "page" : undefined}
            onClick={() => setParams({ tab: t.key })}
          >
            {t.label}
          </button>
        ))}
      </nav>
      {tab === "sessions" && <SessionsTab engagementId={engagementId} />}
      {tab === "participants" && <ParticipantsTab engagementId={engagementId} />}
    </>
  );
}
```

- [ ] **Step 9: Sidebar según rol y ruta `/lab`**

Reemplazar `frontend/src/components/Sidebar.tsx` por:

```tsx
import { NavLink } from "react-router-dom";
import { NAV_ITEMS } from "../lib/labels";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const user = useAuthStore((s) => s.user);
  const items = NAV_ITEMS.filter((item) => item.to !== "/lab" || can(user, "viewLabSummary"));
  return (
    <aside className="flex h-full w-60 flex-col border-r border-line bg-white">
      <div className="border-b border-line px-5 py-4">
        <div className="text-xs font-semibold tracking-[0.2em] text-ink">SYNER × HiTO</div>
        <div className="mt-1 text-xs text-muted">Transformation Room</div>
      </div>
      <nav className="flex-1 space-y-0.5 px-3 py-3">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={onNavigate}
            className={({ isActive }) =>
              `block rounded-md px-3 py-2 text-sm ${isActive ? "bg-canvas font-medium text-ink" : "text-muted hover:bg-canvas hover:text-ink"}`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-line px-5 py-3 text-[11px] text-muted">Private advisory workspace</div>
    </aside>
  );
}
```

En `frontend/src/router.tsx`: sustituir el import `import { ComingSoonPage } from "./pages/ComingSoonPage";` por `import { LabPage } from "./pages/LabPage";` y la ruta `{ path: "/lab", element: <ComingSoonPage title="Leadership Lab" /> },` por `{ path: "/lab", element: <LabPage /> },`.

```bash
cd /mnt/d/Devs/HiTOxSyner
git rm frontend/src/pages/ComingSoonPage.tsx
grep -rn "ComingSoon" frontend/src || echo "sin referencias"
```
Expected: `sin referencias`.

- [ ] **Step 10: Build y prueba manual**

```bash
cd /mnt/d/Devs/HiTOxSyner/frontend && npm run build 2>&1 | tail -5
```
Expected: `tsc` sin errores y `✓ built`.

Prueba manual (dev): backend `.venv/bin/uvicorn app.main:app --reload` y `npm run dev`. Como `admin@syner.demo`: `/lab` muestra las pestañas Sessions (4 sesiones del seed; editar la 3 a `Done` con asistencia) y Participants & Pods (20 participantes; cambiar el pod de uno desde el select de la fila; añadir el pod "Pod Pacífico"). Como `exec@hito.demo`: `/lab` muestra tiles (2/4 sesiones, 4 CTAs activos, 38% con evidencia, 1 contrato), la lista de sesiones y las barras por sesión y por pod, sin ningún nombre de participante ni texto de CTA. Como `collab@hito.demo`: el sidebar no muestra "Leadership Lab" y `/lab` redirige a `/`.

- [ ] **Step 11: Commit**

```bash
cd /mnt/d/Devs/HiTOxSyner
git add frontend/src/types.ts frontend/src/lib/labels.ts frontend/src/components/StatusBadge.tsx frontend/src/api/lab.ts frontend/src/components/lab/SessionsTab.tsx frontend/src/components/lab/ParticipantsTab.tsx frontend/src/components/lab/LabSummaryView.tsx frontend/src/pages/LabPage.tsx frontend/src/components/Sidebar.tsx frontend/src/router.tsx
git commit -m "feat(frontend): página Leadership Lab con sesiones, participantes y pods para Syner y resumen agregado para dirección"
```

---

### Task 7: Frontend: pestañas CTA Tracker y Contracts

**Files:**
- Modify: `frontend/src/lib/labels.ts` (`LAB_TABS`), `frontend/src/pages/LabPage.tsx`
- Create: `frontend/src/components/lab/CtaTrackerTab.tsx`, `frontend/src/components/lab/ContractsTab.tsx`

**Interfaces:**
- Consumes: `labApi.ctas`, `labApi.contracts`, `labApi.sessions`, `labApi.pods`, `labApi.participants` (Task 6); `CTA_STATUSES`, `CONTRACT_STATUSES`.
- Produces: `CtaTrackerTab({ engagementId })` (filtros por sesión, pod y status; drawer con los siete campos del CTA más status y evidencia) y `ContractsTab({ engagementId })` (uno por participante, selección de hasta 3 CTAs del participante, fechas +30 y +60 automáticas, señal de éxito).

- [ ] **Step 1: Ampliar `LAB_TABS` en `frontend/src/lib/labels.ts`**

Reemplazar la constante por:

```ts
export const LAB_TABS: { key: LabTab; label: string }[] = [
  { key: "sessions", label: "Sessions" },
  { key: "participants", label: "Participants & Pods" },
  { key: "ctas", label: "CTA Tracker" },
  { key: "contracts", label: "Contracts" },
];
```

- [ ] **Step 2: Crear `frontend/src/components/lab/CtaTrackerTab.tsx`**

```tsx
import { FormEvent, useState } from "react";
import { errorMessage } from "../../api/client";
import { CtaInput, labApi } from "../../api/lab";
import { useResource } from "../../hooks/useResource";
import { formatDate } from "../../lib/dates";
import { CTA_STATUSES } from "../../lib/labels";
import type { Cta } from "../../types";
import { DataTable } from "../DataTable";
import { EmptyState } from "../EmptyState";
import { Field, Select } from "../Field";
import { FormDrawer } from "../FormDrawer";
import { StatusBadge } from "../StatusBadge";

const EMPTY: CtaInput = {
  participant_id: "", session_id: "", trigger: "", behavior: "", stakeholder: "", evidence_expected: "",
  due_date: null, accountability_partner: "", impact: "", status: "Committed", evidence_notes: "",
};

export function CtaTrackerTab({ engagementId }: { engagementId: string }) {
  const [sessionId, setSessionId] = useState("");
  const [podId, setPodId] = useState("");
  const [status, setStatus] = useState("");
  const { data, loading, error, reload } = useResource(
    () => labApi.ctas.list(engagementId, { session_id: sessionId || undefined, pod_id: podId || undefined, status: status || undefined }),
    [engagementId, sessionId, podId, status],
  );
  const sessions = useResource(() => labApi.sessions.list(engagementId), [engagementId]);
  const pods = useResource(() => labApi.pods.list(engagementId), [engagementId]);
  const participants = useResource(() => labApi.participants.list(engagementId), [engagementId]);
  const [editing, setEditing] = useState<Cta | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<CtaInput>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const sessionList = sessions.data?.items ?? [];
  const podList = pods.data?.items ?? [];
  const participantList = participants.data?.items ?? [];
  const participantName = (id: string) => participantList.find((p) => p.id === id)?.full_name ?? "—";
  const sessionLabel = (id: string) => {
    const s = sessionList.find((x) => x.id === id);
    return s ? `Sesión ${s.number} · ${s.theme}` : "—";
  };
  const set = (key: keyof CtaInput, value: unknown) => setForm((f) => ({ ...f, [key]: value }));

  function openCreate() {
    setEditing(null);
    setForm({ ...EMPTY, participant_id: participantList.find((p) => p.is_active)?.id ?? "", session_id: sessionId || (sessionList[0]?.id ?? "") });
    setFormError(null); setOpen(true);
  }
  function openEdit(c: Cta) {
    setEditing(c);
    const { participant_id, session_id, trigger, behavior, stakeholder, evidence_expected, due_date, accountability_partner, impact, status: ctaStatus, evidence_notes } = c;
    setForm({ participant_id, session_id, trigger, behavior, stakeholder, evidence_expected, due_date, accountability_partner, impact, status: ctaStatus, evidence_notes });
    setFormError(null); setOpen(true);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    try {
      if (editing) await labApi.ctas.update(editing.id, form);
      else await labApi.ctas.create(engagementId, form);
      setOpen(false);
      await reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  const text = (key: keyof CtaInput, label: string, rows = 2, required = false) => (
    <Field label={label}>
      <textarea className="input" rows={rows} value={(form[key] as string) ?? ""} onChange={(e) => set(key, e.target.value)} maxLength={10000} required={required} />
    </Field>
  );

  return (
    <>
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div className="flex flex-wrap gap-2">
          <select className="input w-56" value={sessionId} onChange={(e) => setSessionId(e.target.value)} aria-label="Filtrar por sesión">
            <option value="">Todas las sesiones</option>
            {sessionList.map((s) => <option key={s.id} value={s.id}>{s.number}. {s.name}</option>)}
          </select>
          <select className="input w-44" value={podId} onChange={(e) => setPodId(e.target.value)} aria-label="Filtrar por pod">
            <option value="">Todos los pods</option>
            {podList.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
          <div className="w-44"><Select value={status} onChange={setStatus} options={CTA_STATUSES} allowEmpty="Todos los estados" /></div>
        </div>
        <button className="btn btn-primary" onClick={openCreate} disabled={participantList.length === 0 || sessionList.length === 0}>Nuevo CTA</button>
      </div>
      {error && <p className="mb-4 text-sm text-danger">{error}</p>}
      {loading && !data ? <p className="text-sm text-muted">Cargando…</p> : (
        <DataTable<Cta>
          rows={data?.items ?? []}
          onRowClick={openEdit}
          empty={<EmptyState title="Sin CTAs" hint="Registra el primer Call to Action de una sesión." />}
          columns={[
            { key: "participant", header: "Participante", render: (c) => <span className="font-medium">{participantName(c.participant_id)}<span className="block text-xs font-normal text-muted">{sessionLabel(c.session_id)}</span></span> },
            { key: "behavior", header: "Behavior", render: (c) => <span className="line-clamp-2">{c.behavior}</span> },
            { key: "due", header: "Fecha", render: (c) => formatDate(c.due_date), className: "tabular-nums" },
            { key: "partner", header: "Accountability partner", render: (c) => c.accountability_partner || "—" },
            { key: "status", header: "Status", render: (c) => <StatusBadge value={c.status} /> },
          ]}
        />
      )}
      <FormDrawer open={open} title={editing ? "Editar CTA" : "Nuevo CTA"} onClose={() => setOpen(false)} onSubmit={submit} submitting={busy} error={formError}>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Participante">
            <select className="input" value={form.participant_id ?? ""} onChange={(e) => set("participant_id", e.target.value)} required>
              <option value="">Selecciona…</option>
              {participantList.filter((p) => p.is_active || p.id === form.participant_id).map((p) => <option key={p.id} value={p.id}>{p.full_name}</option>)}
            </select>
          </Field>
          <Field label="Sesión">
            <select className="input" value={form.session_id ?? ""} onChange={(e) => set("session_id", e.target.value)} required>
              <option value="">Selecciona…</option>
              {sessionList.map((s) => <option key={s.id} value={s.id}>{s.number}. {s.name}</option>)}
            </select>
          </Field>
        </div>
        {text("trigger", "Trigger (situación que activa la conducta)")}
        {text("behavior", "Behavior (conducta comprometida)", 3, true)}
        <div className="grid grid-cols-2 gap-3">
          <Field label="Stakeholder"><input className="input" value={form.stakeholder ?? ""} onChange={(e) => set("stakeholder", e.target.value)} maxLength={200} /></Field>
          <Field label="Accountability partner"><input className="input" value={form.accountability_partner ?? ""} onChange={(e) => set("accountability_partner", e.target.value)} maxLength={200} /></Field>
          <Field label="Fecha compromiso"><input className="input" type="date" value={form.due_date ?? ""} onChange={(e) => set("due_date", e.target.value || null)} /></Field>
          <Field label="Status"><Select value={form.status ?? "Committed"} onChange={(v) => set("status", v)} options={CTA_STATUSES} /></Field>
        </div>
        {text("evidence_expected", "Evidencia esperada")}
        {text("impact", "Impacto esperado")}
        {text("evidence_notes", "Evidencia registrada", 3)}
      </FormDrawer>
    </>
  );
}
```

- [ ] **Step 3: Crear `frontend/src/components/lab/ContractsTab.tsx`**

```tsx
import { FormEvent, useState } from "react";
import { errorMessage } from "../../api/client";
import { ContractInput, labApi } from "../../api/lab";
import { useResource } from "../../hooks/useResource";
import { formatDate } from "../../lib/dates";
import { CONTRACT_STATUSES } from "../../lib/labels";
import type { ActionContract } from "../../types";
import { DataTable } from "../DataTable";
import { EmptyState } from "../EmptyState";
import { Field, Select } from "../Field";
import { FormDrawer } from "../FormDrawer";
import { StatusBadge } from "../StatusBadge";

const EMPTY: ContractInput = { participant_id: "", start_date: null, review_30_date: null, review_60_date: null, success_signal: "", status: "Draft", cta_ids: [] };
const MAX_CTAS = 3;

export function ContractsTab({ engagementId }: { engagementId: string }) {
  const [status, setStatus] = useState("");
  const contracts = useResource(() => labApi.contracts.list(engagementId), [engagementId]);
  const participants = useResource(() => labApi.participants.list(engagementId), [engagementId]);
  const ctas = useResource(() => labApi.ctas.list(engagementId), [engagementId]);
  const [editing, setEditing] = useState<ActionContract | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<ContractInput>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const all = contracts.data?.items ?? [];
  const rows = status ? all.filter((c) => c.status === status) : all;
  const participantList = participants.data?.items ?? [];
  const ctaList = ctas.data?.items ?? [];
  const participantName = (id: string) => participantList.find((p) => p.id === id)?.full_name ?? "—";
  const withContract = new Set(all.map((c) => c.participant_id));
  const selectable = participantList.filter((p) => (p.is_active && !withContract.has(p.id)) || p.id === editing?.participant_id);
  const participantCtas = ctaList.filter((c) => c.participant_id === form.participant_id);
  const selected = form.cta_ids ?? [];
  const set = (key: keyof ContractInput, value: unknown) => setForm((f) => ({ ...f, [key]: value }));

  function openCreate() { setEditing(null); setForm({ ...EMPTY, participant_id: selectable[0]?.id ?? "" }); setFormError(null); setOpen(true); }
  function openEdit(c: ActionContract) {
    setEditing(c);
    setForm({ participant_id: c.participant_id, start_date: c.start_date, review_30_date: c.review_30_date, review_60_date: c.review_60_date, success_signal: c.success_signal, status: c.status, cta_ids: c.cta_ids });
    setFormError(null); setOpen(true);
  }
  function changeParticipant(id: string) { setForm((f) => ({ ...f, participant_id: id, cta_ids: [] })); }
  function toggleCta(id: string) { set("cta_ids", selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]); }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    try {
      if (editing) await labApi.contracts.update(editing.id, form);
      else await labApi.contracts.create(engagementId, form);
      setOpen(false);
      await contracts.reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  return (
    <>
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div className="w-48"><Select value={status} onChange={setStatus} options={CONTRACT_STATUSES} allowEmpty="Todos los estados" /></div>
        <button className="btn btn-primary" onClick={openCreate} disabled={selectable.length === 0}>Nuevo contract</button>
      </div>
      {contracts.error && <p className="mb-4 text-sm text-danger">{contracts.error}</p>}
      {contracts.loading && !contracts.data ? <p className="text-sm text-muted">Cargando…</p> : (
        <DataTable<ActionContract>
          rows={rows}
          onRowClick={openEdit}
          empty={<EmptyState title="Sin Leadership Action Contracts" hint="Cada participante firma un contrato con hasta 3 CTAs." />}
          columns={[
            { key: "participant", header: "Participante", render: (c) => <span className="font-medium">{participantName(c.participant_id)}<span className="line-clamp-1 block text-xs font-normal text-muted">{c.success_signal || "Sin señal de éxito"}</span></span> },
            { key: "start", header: "Inicio", render: (c) => formatDate(c.start_date), className: "tabular-nums" },
            { key: "r30", header: "Revisión +30", render: (c) => formatDate(c.review_30_date), className: "tabular-nums" },
            { key: "r60", header: "Revisión +60", render: (c) => formatDate(c.review_60_date), className: "tabular-nums" },
            { key: "ctas", header: "CTAs", render: (c) => <span className="tabular-nums">{c.cta_ids.length}/{MAX_CTAS}</span> },
            { key: "status", header: "Status", render: (c) => <StatusBadge value={c.status} /> },
          ]}
        />
      )}
      <FormDrawer open={open} title={editing ? "Editar Leadership Action Contract" : "Nuevo Leadership Action Contract"} onClose={() => setOpen(false)} onSubmit={submit} submitting={busy} error={formError}>
        <Field label="Participante">
          <select className="input" value={form.participant_id ?? ""} onChange={(e) => changeParticipant(e.target.value)} required>
            <option value="">Selecciona…</option>
            {selectable.map((p) => <option key={p.id} value={p.id}>{p.full_name}</option>)}
          </select>
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Inicio"><input className="input" type="date" value={form.start_date ?? ""} onChange={(e) => set("start_date", e.target.value || null)} /></Field>
          <Field label="Status"><Select value={form.status ?? "Draft"} onChange={(v) => set("status", v)} options={CONTRACT_STATUSES} /></Field>
          <Field label="Revisión +30 (automática si se deja vacía)"><input className="input" type="date" value={form.review_30_date ?? ""} onChange={(e) => set("review_30_date", e.target.value || null)} /></Field>
          <Field label="Revisión +60 (automática si se deja vacía)"><input className="input" type="date" value={form.review_60_date ?? ""} onChange={(e) => set("review_60_date", e.target.value || null)} /></Field>
        </div>
        <Field label="Señal de éxito"><textarea className="input" rows={3} value={form.success_signal ?? ""} onChange={(e) => set("success_signal", e.target.value)} maxLength={10000} /></Field>
        <fieldset>
          <legend className="label">CTAs del contrato ({selected.length}/{MAX_CTAS})</legend>
          {participantCtas.length === 0 ? <p className="text-sm text-muted">Este participante no tiene CTAs registrados.</p> : (
            <ul className="space-y-2">
              {participantCtas.map((c) => {
                const checked = selected.includes(c.id);
                return (
                  <li key={c.id}>
                    <label className={`flex items-start gap-2 text-sm ${!checked && selected.length >= MAX_CTAS ? "text-muted" : ""}`}>
                      <input type="checkbox" className="mt-1" checked={checked} disabled={!checked && selected.length >= MAX_CTAS} onChange={() => toggleCta(c.id)} />
                      <span className="flex-1">{c.behavior}</span>
                      <StatusBadge value={c.status} />
                    </label>
                  </li>
                );
              })}
            </ul>
          )}
        </fieldset>
      </FormDrawer>
    </>
  );
}
```

- [ ] **Step 4: Renderizar las pestañas en `frontend/src/pages/LabPage.tsx`**

Añadir los imports:

```tsx
import { ContractsTab } from "../components/lab/ContractsTab";
import { CtaTrackerTab } from "../components/lab/CtaTrackerTab";
```

Y después de `{tab === "participants" && <ParticipantsTab engagementId={engagementId} />}` añadir:

```tsx
      {tab === "ctas" && <CtaTrackerTab engagementId={engagementId} />}
      {tab === "contracts" && <ContractsTab engagementId={engagementId} />}
```

- [ ] **Step 5: Build y prueba manual**

```bash
cd /mnt/d/Devs/HiTOxSyner/frontend && npm run build 2>&1 | tail -5
```
Expected: `tsc` sin errores y `✓ built`.

Prueba manual como `admin@syner.demo`: CTA Tracker lista los 8 CTAs del seed; filtrar por sesión 1 (5), por pod y por status `Evidenced` (3); crear un CTA para la sesión 3 y marcarlo `In Progress`. Contracts lista 2; crear uno para "[Demo] Participante 03" eligiendo su único CTA; intentar marcar un cuarto CTA en el contrato de "[Demo] Participante 01" (el checkbox se deshabilita al llegar a 3); dejar las revisiones vacías con fecha de inicio y comprobar que vuelven rellenas a +30 y +60.

- [ ] **Step 6: Commit**

```bash
cd /mnt/d/Devs/HiTOxSyner
git add frontend/src/lib/labels.ts frontend/src/pages/LabPage.tsx frontend/src/components/lab/CtaTrackerTab.tsx frontend/src/components/lab/ContractsTab.tsx
git commit -m "feat(frontend): CTA tracker con filtros y Leadership Action Contracts con hasta 3 CTAs"
```

---

### Task 8: Frontend: tarjeta Leadership Lab en el dashboard y minors diferidos de UI

**Files:**
- Modify: `frontend/src/pages/DashboardPage.tsx`
- Create: `frontend/src/components/Block.tsx`
- Modify: `frontend/src/pages/InitiativeDetailPage.tsx`, `frontend/src/pages/MeetingDetailPage.tsx`, `frontend/src/pages/DecisionsPage.tsx` (usar `Block`/`Prose` compartidos), `frontend/src/pages/ActionsPage.tsx` (usar `ActionForm`), `frontend/src/components/DataTable.tsx` y `frontend/src/pages/RoadmapPage.tsx` (filas accesibles por teclado)

**Interfaces:**
- Consumes: `Dashboard.lab` (Task 6), `ActionForm` y `EMPTY_ACTION` (`components/ActionForm.tsx`, ya existen).
- Produces: `Block({ title, children, action? })` y `Prose({ text, label? })` en `components/Block.tsx`; `DataTable` con filas enfocables (`tabIndex=0`, `role="button"`, Enter/Espacio) cuando hay `onRowClick`.

- [ ] **Step 1: Crear `frontend/src/components/Block.tsx`**

```tsx
import type { ReactNode } from "react";

export function Block({ title, children, action }: { title: string; children: ReactNode; action?: ReactNode }) {
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

export function Prose({ text, label }: { text: string; label?: string }) {
  const body = <p className="whitespace-pre-line text-sm leading-6">{text || <span className="text-muted">Sin contenido.</span>}</p>;
  if (!label) return body;
  return (
    <div>
      <div className="label">{label}</div>
      {body}
    </div>
  );
}
```

- [ ] **Step 2: Usar `Block`/`Prose` compartidos**

En `frontend/src/pages/InitiativeDetailPage.tsx` y `frontend/src/pages/MeetingDetailPage.tsx`: borrar las funciones locales `Block` y `Prose`, añadir `import { Block, Prose } from "../components/Block";` y cambiar el primer import a `import { FormEvent, useState } from "react";` (ya no se usa `ReactNode`).

En `frontend/src/pages/DecisionsPage.tsx`: borrar la función local `Prose` y añadir `import { Prose } from "../components/Block";` (los usos `<Prose label="..." text={...} />` no cambian).

En `frontend/src/pages/DashboardPage.tsx`: borrar la función local `Section`, añadir `import { Block } from "../components/Block";`, sustituir todas las etiquetas `<Section` por `<Block` y `</Section>` por `</Block>`, y cambiar el primer import a `import { useState } from "react";`.

```bash
cd /mnt/d/Devs/HiTOxSyner/frontend
grep -n "function Block\|function Prose\|function Section" src/pages/*.tsx || echo "sin duplicados"
```
Expected: `sin duplicados`.

- [ ] **Step 3: Tarjeta Leadership Lab en `frontend/src/pages/DashboardPage.tsx`**

Después del bloque `<Block title="Next Milestones">…</Block>` (dentro del mismo `grid`), añadir:

```tsx
        {data.lab && (
          <Block title="Leadership Lab" action={<Link to="/lab" className="text-xs text-muted hover:underline">Leadership Lab →</Link>}>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-[11px] font-medium uppercase tracking-wide text-muted">Próxima sesión</div>
                {data.lab.next_session ? (
                  <>
                    <div className="mt-1 font-medium">{data.lab.next_session.number}. {data.lab.next_session.name}</div>
                    <div className="text-xs tabular-nums text-muted">{data.lab.next_session.theme} · {formatDate(data.lab.next_session.held_on)}</div>
                  </>
                ) : (
                  <div className="mt-1 text-muted">Sin sesiones pendientes</div>
                )}
              </div>
              <div>
                <div className="text-[11px] font-medium uppercase tracking-wide text-muted">CTAs con evidencia</div>
                <div className="mt-1 text-2xl font-semibold tabular-nums">{data.lab.evidenced_pct}%</div>
                <div className="text-xs text-muted">{data.lab.sessions_done}/{data.lab.sessions_total} sesiones · {data.lab.active_ctas} CTAs activos · {data.lab.active_contracts} contratos activos</div>
              </div>
            </div>
          </Block>
        )}
```

- [ ] **Step 4: `ActionsPage` reutiliza `ActionForm`**

En `frontend/src/pages/ActionsPage.tsx`:

1. Añadir `import { ActionForm, EMPTY_ACTION } from "../components/ActionForm";` y borrar la constante local `EMPTY`, usando `EMPTY_ACTION` en su lugar (`useState<ActionInput>(EMPTY_ACTION)` y `setForm(EMPTY_ACTION)`). `Field` y `Select` siguen importados porque los usan los campos Status y Evidencia.
2. Borrar el import `LEVELS` de `../lib/labels` (queda `import { ACTION_STATUSES } from "../lib/labels";`).
3. Reemplazar el bloque `{!limited && ( <> … </> )}` del drawer por:

```tsx
        {!limited && <ActionForm form={form} onChange={setForm} users={users.data ?? []} initiatives={initiatives.data?.items ?? []} />}
```

Los campos `Status` y `Evidencia` que siguen al bloque se mantienen (no forman parte de `ActionForm`).

- [ ] **Step 5: Filas accesibles por teclado**

En `frontend/src/components/DataTable.tsx`, reemplazar el `<tr>` del cuerpo por:

```tsx
            <tr
              key={row.id}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              onKeyDown={onRowClick ? (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onRowClick(row); } } : undefined}
              tabIndex={onRowClick ? 0 : undefined}
              role={onRowClick ? "button" : undefined}
              className={`border-b border-line last:border-0 ${onRowClick ? "cursor-pointer hover:bg-canvas focus:bg-canvas focus:outline-none" : ""}`}
            >
```

En `frontend/src/pages/RoadmapPage.tsx`, reemplazar el `<li key={m.id} onClick={() => openEdit(m)} className=…>` por:

```tsx
                    <li
                      key={m.id}
                      onClick={() => openEdit(m)}
                      onKeyDown={writable ? (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openEdit(m); } } : undefined}
                      tabIndex={writable ? 0 : undefined}
                      role={writable ? "button" : undefined}
                      className={`rounded border border-line p-2 text-sm ${writable ? "cursor-pointer hover:bg-canvas focus:bg-canvas focus:outline-none" : ""}`}
                    >
```

- [ ] **Step 6: Build y prueba manual**

```bash
cd /mnt/d/Devs/HiTOxSyner/frontend && npm run build 2>&1 | tail -5
```
Expected: `tsc` sin errores y `✓ built`.

Prueba manual: dashboard como `exec@hito.demo` muestra la tarjeta "Leadership Lab" con "3. From Silos to Flow" como próxima sesión y 38%; como `collab@hito.demo` la tarjeta no aparece. En Actions, tabular hasta una fila y pulsar Enter abre el drawer; crear una action desde Actions sigue funcionando con responsable, initiative y prioridad.

- [ ] **Step 7: Commit**

```bash
cd /mnt/d/Devs/HiTOxSyner
git add frontend/src/components/Block.tsx frontend/src/pages/DashboardPage.tsx frontend/src/pages/InitiativeDetailPage.tsx frontend/src/pages/MeetingDetailPage.tsx frontend/src/pages/DecisionsPage.tsx frontend/src/pages/ActionsPage.tsx frontend/src/components/DataTable.tsx frontend/src/pages/RoadmapPage.tsx
git commit -m "feat(frontend): tarjeta Leadership Lab en dashboard, Block/Prose compartidos, ActionForm en Actions y filas accesibles"
```

---

### Task 9: Backend: minors diferidos (URL de documentos, validación de vínculos unificada, `entity_type` en comments, tests de paginación)

**Files:**
- Modify: `app/schemas/document.py`, `app/services/actions.py`, `app/services/decisions.py`, `app/services/milestones.py`, `app/routers/comments.py`
- Test: `tests/test_documents.py` (añadir), `tests/test_comments.py` (añadir), `tests/test_pagination.py` (crear)

**Interfaces:**
- Consumes: `require_in_engagement` (Task 1), `ENTITY_MODELS` (`app/services/entities.py`).
- Produces: `url` de Document vacío o con esquema `http://`/`https://` (422 en otro caso); `_validate_links` de actions y decisions y `create/update_milestone` delegan en `require_in_engagement` (desaparece `validate_initiative`); `GET /comments` responde 422 si `entity_type` no está en `ENTITY_MODELS`.

- [ ] **Step 1: Escribir los tests**

Añadir al final de `tests/test_documents.py`:

```python
def test_document_url_must_be_empty_or_http(client, world):
    admin = login(client, "admin@syner.example")
    base = f"/api/engagements/{world.eng_a.id}/documents"
    for bad in ("javascript:alert(1)", "ftp://files.example.com/x", "drive.example.com/d/abc"):
        assert client.post(base, headers=admin, json={**DOCUMENT, "url": bad}).status_code == 422, bad
    created = client.post(base, headers=admin, json={**DOCUMENT, "url": ""})
    assert created.status_code == 201 and created.json()["url"] == ""
    assert client.post(base, headers=admin, json={**DOCUMENT, "url": "http://intranet.example/doc"}).status_code == 201
    assert client.patch(f"/api/documents/{created.json()['id']}", headers=admin, json={"url": "javascript:alert(1)"}).status_code == 422
    updated = client.patch(f"/api/documents/{created.json()['id']}", headers=admin, json={"url": "https://drive.example.com/d/abc"})
    assert updated.status_code == 200 and updated.json()["url"] == "https://drive.example.com/d/abc"
    assert client.get(base, headers=admin).json()["total"] == 2
```

Añadir al final de `tests/test_comments.py` (el archivo ya importa `uuid`):

```python
def test_listing_comments_rejects_unknown_entity_type(client, world):
    headers = login(client, "collab@a.example")
    response = client.get(
        f"/api/engagements/{world.eng_a.id}/comments", headers=headers,
        params={"entity_type": "unicorn", "entity_id": str(uuid.uuid4())},
    )
    assert response.status_code == 422
    assert "entity_type" in response.json()["detail"]
```

Crear `tests/test_pagination.py`:

```python
import pytest

from tests.factories import login

LISTINGS = ["findings", "initiatives", "actions", "milestones", "decisions", "meetings", "documents", "activity"]


@pytest.mark.parametrize("segment", LISTINGS)
def test_listing_pagination_limits_are_enforced(client, world, segment):
    headers = login(client, "exec@a.example")
    base = f"/api/engagements/{world.eng_a.id}/{segment}"
    assert client.get(base, headers=headers, params={"limit": 201}).status_code == 422
    assert client.get(base, headers=headers, params={"limit": 0}).status_code == 422
    assert client.get(base, headers=headers, params={"offset": -1}).status_code == 422
    response = client.get(base, headers=headers, params={"limit": 200, "offset": 0})
    assert response.status_code == 200 and response.json() == {"items": [], "total": 0}


def test_offset_and_limit_slice_results(client, world):
    admin = login(client, "admin@syner.example")
    base = f"/api/engagements/{world.eng_a.id}/findings"
    for i in range(3):
        client.post(base, headers=admin, json={"title": f"Hallazgo {i}"})
    page = client.get(base, headers=admin, params={"limit": 2, "offset": 2}).json()
    assert page["total"] == 3 and len(page["items"]) == 1
    assert client.get(base, headers=admin, params={"limit": 2, "offset": 10}).json() == {"items": [], "total": 3}
```

- [ ] **Step 2: Correr los tests para verificar qué falla**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest tests/test_documents.py::test_document_url_must_be_empty_or_http tests/test_comments.py::test_listing_comments_rejects_unknown_entity_type tests/test_pagination.py -q -W error`
Expected: fallan el test de URL (201 en vez de 422) y el de `entity_type` (200 en vez de 422); los de paginación pasan ya (confirman el comportamiento existente).

- [ ] **Step 3: Validar `url` en `app/schemas/document.py`**

Cambiar el import de pydantic a `from pydantic import BaseModel, ConfigDict, Field, field_validator` y añadir después de `Tag = ...`:

```python
def _check_url(value: str | None) -> str | None:
    if value and not value.startswith(("http://", "https://")):
        raise ValueError("url debe estar vacía o empezar por http:// o https://")
    return value
```

Dentro de `DocumentCreate` y de `DocumentUpdate` (en ambas clases) añadir al final:

```python
    @field_validator("url")
    @classmethod
    def validate_url(cls, value):
        return _check_url(value)
```

- [ ] **Step 4: Unificar la validación de vínculos**

`app/services/actions.py`: añadir `from app.services.links import require_in_engagement` y reemplazar `_validate_links` por:

```python
def _validate_links(db: Session, engagement: Engagement, payload: dict) -> None:
    """initiative_id y meeting_id deben ser del engagement; owner_user_id de la organización del engagement o un SYNER_ADMIN."""
    require_in_engagement(db, Initiative, payload.get("initiative_id"), engagement, "initiative_id")
    require_in_engagement(db, Meeting, payload.get("meeting_id"), engagement, "meeting_id")
    owner_id = payload.get("owner_user_id")
    if owner_id is not None:
        owner = db.get(User, owner_id)
        if owner is None or (owner.organization_id != engagement.organization_id and owner.role != Role.SYNER_ADMIN):
            raise HTTPException(status_code=422, detail="owner_user_id no pertenece a este engagement")
```

`app/services/decisions.py`: añadir `from app.services.links import require_in_engagement`, quitar `from fastapi import HTTPException` y reemplazar `_validate_links` por:

```python
def _validate_links(db: Session, engagement: Engagement, payload: dict) -> None:
    require_in_engagement(db, Initiative, payload.get("initiative_id"), engagement, "initiative_id")
    require_in_engagement(db, Meeting, payload.get("meeting_id"), engagement, "meeting_id")
```

`app/services/milestones.py`: añadir `from app.services.links import require_in_engagement`, quitar `from fastapi import HTTPException`, borrar la función `validate_initiative` y sustituir sus dos llamadas por `require_in_engagement(db, Initiative, data.initiative_id, engagement, "initiative_id")` (en `create_milestone`) y `require_in_engagement(db, Initiative, payload.get("initiative_id"), engagement, "initiative_id")` (en `update_milestone`).

```bash
cd /mnt/d/Devs/HiTOxSyner
grep -rn "validate_initiative" app tests || echo "sin referencias"
.venv/bin/python -c "import app.services.actions, app.services.decisions, app.services.milestones; print('imports ok')"
```
Expected: `sin referencias` e `imports ok`.

- [ ] **Step 5: Validar `entity_type` en `GET /comments`**

En `app/routers/comments.py`: cambiar el import a `from fastapi import APIRouter, Depends, HTTPException, Query`, añadir `from app.services.entities import ENTITY_MODELS` y, al inicio del cuerpo de `list_comments`, antes de llamar al crud:

```python
    if entity_type not in ENTITY_MODELS:
        raise HTTPException(status_code=422, detail=f"entity_type debe ser uno de: {', '.join(ENTITY_MODELS)}")
```

- [ ] **Step 6: Suite completa**

Run: `cd /mnt/d/Devs/HiTOxSyner && .venv/bin/pytest -q -W error 2>&1 | tail -2`
Expected: `137 passed` (126 + 1 URL + 1 comments + 8 parametrizados + 1 de slicing).

- [ ] **Step 7: Commit**

```bash
cd /mnt/d/Devs/HiTOxSyner
git add app/schemas/document.py app/services/actions.py app/services/decisions.py app/services/milestones.py app/routers/comments.py tests/test_documents.py tests/test_comments.py tests/test_pagination.py
git commit -m "fix: URL de documentos solo http(s), validación de vínculos unificada, entity_type validado en comments y tests de paginación"
```

---

### Task 10: Definition of Done, README, verificación completa, PR, merge y despliegue

**Files:**
- Modify: `README.md`, `docs/superpowers/specs/2026-10-11-transformation-room-design.md` (solo la línea `Estado:`)

**Interfaces:** ninguna nueva. Verifica el release completo contra la sección 10 de la spec.

- [ ] **Step 1: README**

Añadir a `README.md`, antes de la sección `## Tests`, la sección:

```markdown
## Leadership Lab

Módulo propio del Executive Leadership Lab (sesiones, pods, participantes, CTA tracker y Leadership Action Contracts) bajo `/api/engagements/{id}/lab/*` y la página `/lab`.

- SYNER_ADMIN administra todo. Los participantes son registros sin login.
- HITO_EXECUTIVE solo ve `GET /lab/summary` (calendario, asistencia y agregados de CTAs por status, sesión y pod) y la tarjeta Leadership Lab del dashboard. Nunca recibe nombres de participantes ni textos de CTAs.
- HITO_COLLABORATOR no ve el módulo; el backend responde 403.
- Toda la actividad del Lab se registra con `internal_only=true` y solo aparece en el activity trail de Syner.
- Los PDFs de Project ORION en `docs/` se registran con el seed como Documents internos (categoría Deliverables); el primer release no almacena archivos, solo su ficha.
```

Y en `docs/superpowers/specs/2026-10-11-transformation-room-design.md` cambiar la línea `Estado: aprobado en brainstorming, pendiente de revisión escrita` por `Estado: implementado en los planes 1, 2 y 3 (`docs/superpowers/plans/`); desviaciones registradas en cada plan`.

- [ ] **Step 2: Checklist del Definition of Done (spec sección 10)**

Verificar cada punto y anotar el resultado en el reporte de la tarea:

| DoD | Cómo se verifica |
|---|---|
| Desplegado en Railway con `/api/health` en verde | Step 6 de esta tarea (`curl` al health de producción) |
| Login funcional con los tres roles del seed | `tests/test_seed.py` (admin y exec) + smoke del Step 3 (collab) |
| Aislamiento por organización verificado por tests | `tests/test_*`: cada listado nuevo tiene un test con `exec@b.example` → 404 |
| Dashboard operativo con datos del seed | Smoke del Step 3: tiles, roadmap, decisions_required, next_milestones, lab |
| CRUD de findings, initiatives, milestones, actions, decisions, meetings, documents y módulo Lab core | Suite completa (137 tests) |
| Conversión finding → initiative y acuerdos de reunión → actions y decisions | `tests/test_findings.py`, `tests/test_meetings.py` (planes 1 y 2) |
| Activity trail visible en dashboard y en detalle de iniciativa | `tests/test_dashboard.py`, `tests/test_initiatives.py`, `tests/test_documents.py` |
| Responsive básico; dashboard legible en teléfono | Revisión manual en viewport 390 px: tiles en dos columnas, sidebar como drawer, tarjeta Lab apilada |
| Seed idempotente, `.env.example`, README, migración reproducible, tests backend en verde, build frontend en verde | `tests/test_seed.py`; `.env.example` sin cambios necesarios; README actualizado; `alembic upgrade/downgrade/upgrade` + `alembic check`; Step 3 |

- [ ] **Step 3: Suite backend, build frontend, Alembic y smoke local**

```bash
cd /mnt/d/Devs/HiTOxSyner
.venv/bin/pytest -q -W error 2>&1 | tail -2
cd frontend && npm run build 2>&1 | tail -3 && cd ..
.venv/bin/alembic check
.venv/bin/python -m app.seed
```
Expected: `137 passed`; `✓ built`; `No new upgrade operations detected.`; `Seed completado.`

Smoke con uvicorn en segundo plano (puerto 8010; usar las passwords del `.env` si difieren de las demo):

```bash
cd /mnt/d/Devs/HiTOxSyner
.venv/bin/uvicorn app.main:app --port 8010 > /dev/null 2>&1 &
sleep 3
J=".venv/bin/python -c"
login() { curl -s -X POST localhost:8010/api/auth/login -H 'content-type: application/json' -d "{\"email\":\"$1\",\"password\":\"$2\"}" | $J 'import json,sys; print(json.load(sys.stdin)["access_token"])'; }
ADMIN=$(login admin@syner.demo syner-demo); EXEC=$(login exec@hito.demo exec-demo); COLLAB=$(login collab@hito.demo collab-demo)
ENG=$(curl -s localhost:8010/api/engagements -H "Authorization: Bearer $ADMIN" | $J 'import json,sys; print(json.load(sys.stdin)[0]["id"])')
curl -s localhost:8010/api/health
curl -s "localhost:8010/api/engagements/$ENG/dashboard" -H "Authorization: Bearer $EXEC" | $J 'import json,sys; d=json.load(sys.stdin); print(d["tiles"]); print("lab", d["lab"])'
curl -s "localhost:8010/api/engagements/$ENG/dashboard" -H "Authorization: Bearer $COLLAB" | $J 'import json,sys; d=json.load(sys.stdin); print("collab lab", d["lab"])'
curl -s "localhost:8010/api/engagements/$ENG/lab/summary" -H "Authorization: Bearer $EXEC" | $J 'import json,sys; d=json.load(sys.stdin); print(d["cta_totals"], d["evidenced_pct"], d["active_contracts"]); t=json.dumps(d); print("leak", any(k in t for k in ("participant","trigger","behavior","full_name","[Demo] Participante")))'
curl -s -o /dev/null -w "collab summary %{http_code}\n" "localhost:8010/api/engagements/$ENG/lab/summary" -H "Authorization: Bearer $COLLAB"
curl -s -o /dev/null -w "exec ctas %{http_code}\n" "localhost:8010/api/engagements/$ENG/lab/ctas" -H "Authorization: Bearer $EXEC"
curl -s "localhost:8010/api/engagements/$ENG/documents" -H "Authorization: Bearer $EXEC" | $J 'import json,sys; print("exec docs", json.load(sys.stdin)["total"])'
curl -s "localhost:8010/api/engagements/$ENG/documents" -H "Authorization: Bearer $ADMIN" | $J 'import json,sys; print("admin docs", json.load(sys.stdin)["total"])'
curl -s -o /dev/null -w "spa /lab %{http_code}\n" localhost:8010/lab
pkill -f "uvicorn app.main:app --port 8010"
```
Expected: health ok; tiles con `decisions_required: 2`; `lab` del exec con `next_session` número 3, `sessions_done 2`, `active_ctas 4`, `evidenced_pct 38`, `active_contracts 1`; `collab lab None`; summary `{'committed': 1, 'in_progress': 3, 'evidenced': 3, 'dropped': 1, 'total': 8} 38 1` y `leak False`; `collab summary 403`; `exec ctas 403`; `exec docs 4`; `admin docs 13`; `spa /lab 200`.

- [ ] **Step 4: Commit de documentación y push**

```bash
cd /mnt/d/Devs/HiTOxSyner
git add README.md docs/superpowers/specs/2026-10-11-transformation-room-design.md
git commit -m "docs: Leadership Lab en README y estado de la spec tras los planes 1 a 3"
git push -u origin feat/plan-3-leadership-lab
```

- [ ] **Step 5: PR**

```bash
cd /mnt/d/Devs/HiTOxSyner
gh pr create --base docs/material-hito-syner --title "Plan 3 — Leadership Lab core, material ORION y cierre del Definition of Done" --body "$(cat <<'EOF'
## Resumen
- Leadership Lab core: sesiones (catálogo fijo 1–4), pods, participantes, CTA tracker con filtros y Leadership Action Contracts (máximo 3 CTAs, uno por participante, revisiones +30/+60).
- `/lab/summary` agregado para dirección sin nombres ni textos de CTAs; tarjeta Leadership Lab en el dashboard (null para colaboradores).
- Toda la actividad del Lab es `internal_only`.
- PDFs de Project ORION registrados por el seed como Documents internos (Deliverables).
- Minors diferidos: URL de documentos solo http(s), `require_in_engagement` unificado, `entity_type` validado en comments, tests de paginación, Block/Prose y ActionForm compartidos, filas accesibles por teclado.
- Migración Alembic única, seed demo del Lab, README y checklist del Definition of Done.

## Verificación
- `pytest -q -W error`: 137 passed.
- `npm run build` y `alembic check` en verde.
- Smoke local con los tres roles (summary sin fugas, 403 para colaboradores, documentos internos solo Syner).

Spec: docs/superpowers/specs/2026-10-11-transformation-room-design.md
Plan: docs/superpowers/plans/2026-10-17-plan-3-leadership-lab.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 6: Revisión, merge y despliegue (con confirmación del usuario)**

Pasar la revisión final de la rama (flujo SDD). Corregir hallazgos en commits adicionales. El merge y el despliegue son acciones hacia fuera: pedir confirmación al usuario antes de ejecutarlas.

```bash
cd /mnt/d/Devs/HiTOxSyner
gh pr merge --merge --delete-branch
git checkout docs/material-hito-syner && git pull --ff-only
rsync -a --delete --exclude .venv --exclude node_modules --exclude .git --exclude frontend/dist --exclude .pytest_cache --exclude .superpowers --exclude .env /mnt/d/Devs/HiTOxSyner/ ~/hitoxsyner-upload/
cd ~/hitoxsyner-upload
railway up --service HiTOxSyner --project 712a7fba-0fe2-4284-b4cd-edfb9c8990fb --environment production --detach
```
Esperar a que el deployment esté en `SUCCESS` (`railway deployment list --service HiTOxSyner --project 712a7fba-0fe2-4284-b4cd-edfb9c8990fb --environment production --json`). El contenedor ejecuta `alembic upgrade head` al arrancar. Después, el seed de producción lo corre el usuario desde la sesión con el prefijo `!` (el classifier de auto mode bloquea `railway ssh` ejecutado por Claude):

```bash
railway ssh --service HiTOxSyner --project 712a7fba-0fe2-4284-b4cd-edfb9c8990fb --environment production -i ~/.ssh/id_railway_atlas -- python -m app.seed
curl -s https://hitoxsyner-production.up.railway.app/api/health
curl -s -o /dev/null -w "%{http_code}\n" https://hitoxsyner-production.up.railway.app/lab
```
Expected: `Seed completado.`, `{"status":"ok","database":"ok"}`, `200`. Verificación manual en producción: login como Syner → `/lab` con cuatro pestañas y datos demo; login como exec → `/lab` muestra el resumen sin nombres; login como collab → sin "Leadership Lab" en el sidebar; Documents como Syner muestra los 8 PDFs de ORION como internos.

- [ ] **Step 7: Actualizar la memoria del proyecto**

Actualizar `/home/ecamposg/.claude/projects/-mnt-d-Devs-HiTOxSyner/memory/hito-transformation-room-project.md` con: plan 3 completo y mergeado (número de PR, commit de merge), deployment verificado, seed de producción corrido, DoD del primer release cumplido, y "Siguiente: fase 2 del brief (diagnostic, risks, opportunities, deliverables, KPIs) requiere brainstorming nuevo".

---

## Resumen

| Task | Entrega | Tests nuevos |
|---|---|---|
| 0 | Rama y baseline | 0 |
| 1 | Enums, modelos, `require_in_engagement`, sessions y pods | 8 |
| 2 | Participants y CTAs | 6 |
| 3 | Leadership Action Contracts | 5 |
| 4 | `/lab/summary` y tarjeta del dashboard | 3 |
| 5 | Migración, seed del Lab y ORION, README | 0 (2 reescritos) |
| 6 | Frontend: tipos, API, `/lab` con Sessions, Participants & Pods y resumen de dirección | build |
| 7 | Frontend: CTA Tracker y Contracts | build |
| 8 | Frontend: tarjeta del dashboard y minors de UI | build |
| 9 | Backend: minors diferidos | 11 |
| 10 | DoD, README, PR, merge y deploy | 0 |

Total esperado: 104 + 33 = 137 tests.

## Desviaciones y decisiones respecto a la spec

- `behavior` es el único campo obligatorio del CTA (un CTA sin conducta comprometida no tiene sentido); los otros seis son opcionales. La spec lista los siete campos sin marcar obligatoriedad.
- Los CTAs de un contrato deben pertenecer al participante del contrato (422 en otro caso). La spec solo fija el máximo de 3.
- `evidenced_pct` usa como denominador el total de CTAs, incluidos los `Dropped`.
- La "próxima sesión" del dashboard es la sesión `Planned` de menor número, sin mirar la fecha.
- La tarjeta `lab` del dashboard es `null` para HITO_COLLABORATOR, coherente con "no ve el módulo" aunque la spec 6.4 no lo diga explícitamente.
- Toda la actividad del Lab (incluidos cambios de status de sesiones) es `internal_only`; dirección ve el calendario por `/lab/summary`, no por el activity trail.
- El seed añade 2 Leadership Action Contracts demo (la spec 5.7 no los lista) para que el resumen y la pestaña Contracts no queden vacíos.
- Los Documents de ORION se registran con `url` vacía y sin prefijo `[Demo]` porque no son datos ficticios; son fichas del material real de Syner.
- Comments en Decisions sigue diferido: `Comments` renderiza un `<form>` y el drawer de decisiones ya es un `<form>`; anidarlos es HTML inválido y la spec 6.3 no define una vista de detalle para Decision.
- `scoped()` sigue filtrando por organización (diseño del plan 1): un usuario cliente puede leer entidades de otro engagement de su misma organización, lo cual es correcto para el modelo de tenencia actual (un engagement por organización cliente).

## Verificación final del plan 3

- `pytest -q -W error` en verde: 137 tests.
- `npm run build` en verde; ninguna ruta del sidebar cae en una página provisional; `ComingSoonPage.tsx` eliminado.
- Alembic: `upgrade head` → `downgrade -1` → `upgrade head` reproducible en dev; `alembic check` limpio; aplicado en producción por el arranque del contenedor.
- Seed idempotente por módulo en dev y en producción; ORION registrado en ambos.
- Matriz RBAC de la spec 5.3 cubierta por tests para el Lab: solo Syner administra; dirección solo ve el resumen; colaboradores reciben 403; otra organización recibe 404.
- `/lab/summary` y `dashboard.lab` sin claves ni valores personales (test recursivo de claves y de textos).
- Definition of Done de la spec sección 10 verificado punto por punto (Task 10, Step 2).
