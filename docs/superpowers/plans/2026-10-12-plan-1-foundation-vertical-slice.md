# Transformation Room — Plan 1: Foundation + Vertical Slice

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dejar desplegada en Railway la base de Syner × HiTO Transformation Room con el vertical slice `login → dashboard → finding → initiative → action → dashboard update`, con tenancy, RBAC y activity trail reales.

**Architecture:** Un solo servicio: FastAPI sirve la API bajo `/api` y el build de React desde `frontend/dist`. Backend "brief literal": por módulo un archivo en `models/`, `schemas/`, `crud/`, `routers/`, `services/`. Todo query de entidad recibe `engagement_id`; el acceso se resuelve con las dependencias `get_engagement` y `scoped(Model)`. Los services escriben el activity trail.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2, Pydantic v2, Alembic, PostgreSQL (Railway), bcrypt, PyJWT, pytest + httpx. React 18, TypeScript, Vite 5, React Router 6, Zustand 4, Axios, Tailwind 3. Railway + Docker multi-stage.

**Spec:** `docs/superpowers/specs/2026-10-11-transformation-room-design.md`

Este es el plan 1 de 3. Plan 2 cubre milestones/roadmap, decisions, meetings, documents y comments. Plan 3 cubre el módulo Leadership Lab, el seed completo y el cierre del Definition of Done.

## Global Constraints

- Python 3.12; Node 22 o superior; Postgres es la única base soportada (UUID, enums nativos, ARRAY). No hay SQLite ni en tests. Desarrollo y tests usan un Postgres local en WSL (`localhost:5432`, rol `hitoxsyner`); producción usa el Postgres de Railway, alcanzable solo desde la red interna de Railway.
- Todos los endpoints viven bajo `/api`. Listados paginados de entidades (findings, initiatives, actions, activity y los módulos siguientes) devuelven `{"items": [...], "total": n}` con `limit` default 50, máximo 200, y `offset` default 0. Las colecciones acotadas `GET /engagements` y `GET /engagements/{id}/users` devuelven arrays planos.
- Un PATCH con `null` explícito en un campo que no admite null responde 422 vía `updates(data, nullable=...)` de `app/schemas/common.py` (nunca 500).
- Errores siempre con envelope `{"detail": "..."}`; los 500 no exponen trazas.
- Nada en el código menciona HiTO como constante salvo los nombres de rol del brief (`SYNER_ADMIN`, `HITO_EXECUTIVE`, `HITO_COLLABORATOR`) y el seed.
- Valores de enums exactamente como el brief: `On Track`, `Attention`, `At Risk`; `New`, `Under Analysis`, `Validated`, `Converted to Initiative`, `Accepted`, `Closed`; `Discovery`, `Design`, `Validation`, `Execution`, `Monitoring`, `Completed`, `On Hold`; `Open`, `In Progress`, `Blocked`, `Completed`, `Cancelled`; `Low`, `Medium`, `High`, `Critical`.
- JWT HS256, 12 horas, en cookie `access_token` httpOnly SameSite=Lax (Secure en producción) y también aceptado como `Authorization: Bearer`.
- Secretos solo por variables de entorno. `.env` está en `.gitignore`. Nunca pegar `DATABASE_URL` en commits, docs ni mensajes.
- UI en español; nombres de módulos, estados y términos de la metodología en inglés. Textos de login exactos: `SYNER × HiTO`, `Transformation Room`, `Sign in`, `Private advisory workspace`.
- Sin soft-delete. Sin registro público. Usuarios creados por SYNER_ADMIN.
- Cada columna enum usa un tipo de Postgres con nombre propio `<tabla>_<columna>` (nunca compartir un tipo entre columnas o tablas): evita que Alembic intente crear el mismo tipo dos veces en una migración.
- Commits pequeños por tarea. Mensajes de commit terminan con la línea de atribución indicada por la sesión.

## Review Focus

1. Token válido de un usuario que luego fue desactivado: `/api/auth/me` debe responder 401, no 200. (Test en Task 3.)
2. Token expirado o firmado con otro secreto: 401 con `{"detail": "Invalid or expired token"}`, nunca 500. (Test en Task 3.)
3. HITO_EXECUTIVE haciendo PATCH a su propio engagement: 403 (no 404, no éxito). (Test en Task 4.)
4. `progress_pct` fuera de 0–100 o `executive_summary` de más de 2 000 caracteres: 422. (Test en Task 4.)
5. Ruta `/api/no-existe` con el frontend montado: 404 JSON, no `index.html`. (Test en Task 16.)

---

### Task 1: Backend scaffold, health endpoint y harness de tests

**Files:**
- Create: `requirements.txt`, `.gitignore`, `.env.example`, `app/__init__.py`, `app/core/__init__.py`, `app/core/config.py`, `app/database.py`, `app/main.py`, `app/models/__init__.py`, `app/routers/__init__.py`, `app/routers/health.py`
- Create: `tests/__init__.py`, `tests/conftest.py`, `tests/test_health.py`

**Interfaces:**
- Produces: `get_settings() -> Settings` (campos `environment`, `database_url`, `test_database_url`, `jwt_secret`, `jwt_expire_hours`, `cors_origins`, `rate_limit_enabled`, `rate_limit_per_minute`, `seed_syner_password`, `seed_exec_password`, `seed_collab_password`, propiedad `is_production`); `Base`, `engine`, `SessionLocal`, `get_db()` en `app/database.py`; `app` en `app/main.py`; fixtures `client`, `db` en tests.

- [ ] **Step 1: Crear venv e instalar dependencias**

`requirements.txt`:

```
fastapi>=0.115,<1.0
uvicorn[standard]>=0.30,<1.0
sqlalchemy>=2.0,<2.1
psycopg[binary]>=3.2,<4.0
alembic>=1.13,<2.0
pydantic>=2.9,<3.0
pydantic-settings>=2.5,<3.0
email-validator>=2.2,<3.0
bcrypt>=4.2,<5.0
pyjwt>=2.9,<3.0
pytest>=8.3,<9.0
httpx>=0.27,<1.0
```

`.gitignore`:

```
.venv/
__pycache__/
*.pyc
.env
.pytest_cache/
frontend/node_modules/
frontend/dist/
frontend/tsconfig.tsbuildinfo
```

Run:
```bash
cd /mnt/d/Devs/HiTOxSyner
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
```
Expected: instalación sin errores. Si `python3 -m venv` falla por falta de `python3.12-venv`, usar `uv venv --python 3.12 .venv && uv pip install -r requirements.txt` (uv ya está instalado). Usar `.venv/bin/python` y `.venv/bin/pytest` en todos los pasos siguientes.

- [ ] **Step 2: Verificar el Postgres local y crear las bases `hitoxsyner_dev` y `hitoxsyner_test`**

Postgres corre localmente en WSL (lo instaló el usuario con sudo; rol `hitoxsyner` con password `hitoxsyner` y permiso CREATEDB). El Postgres de Railway no es alcanzable desde esta máquina (sin TCP proxy); la base de producción `hitoxsyner` se crea en Railway en Task 16.

```bash
cd /mnt/d/Devs/HiTOxSyner
pg_isready -h localhost
for db in hitoxsyner_dev hitoxsyner_test; do
  PGPASSWORD=hitoxsyner psql -h localhost -U hitoxsyner -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$db'" | grep -q 1 \
    || PGPASSWORD=hitoxsyner createdb -h localhost -U hitoxsyner "$db"
done
PGPASSWORD=hitoxsyner psql -h localhost -U hitoxsyner -d postgres -tAc "SELECT datname FROM pg_database WHERE datname LIKE 'hitoxsyner%'"
cat > .env <<EOF
ENVIRONMENT=development
DATABASE_URL=postgresql://hitoxsyner:hitoxsyner@localhost:5432/hitoxsyner_dev
TEST_DATABASE_URL=postgresql://hitoxsyner:hitoxsyner@localhost:5432/hitoxsyner_test
JWT_SECRET=dev-only-change-me
EOF
```
Expected: `localhost:5432 - accepting connections` y el listado muestra `hitoxsyner_dev` y `hitoxsyner_test`. Si `pg_isready` falla, el servicio no está arriba: reportar BLOCKED pidiendo `sudo service postgresql start`. `.env` no se commitea.

- [ ] **Step 3: Escribir `.env.example`**

```
ENVIRONMENT=development
DATABASE_URL=postgresql://hitoxsyner:hitoxsyner@localhost:5432/hitoxsyner_dev
TEST_DATABASE_URL=postgresql://hitoxsyner:hitoxsyner@localhost:5432/hitoxsyner_test
JWT_SECRET=change-me
JWT_EXPIRE_HOURS=12
CORS_ORIGINS=http://localhost:5173
RATE_LIMIT_ENABLED=false
RATE_LIMIT_PER_MINUTE=120
SEED_SYNER_PASSWORD=change-me
SEED_EXEC_PASSWORD=change-me
SEED_COLLAB_PASSWORD=change-me
```

- [ ] **Step 4: Escribir el test de health (falla porque no existe la app)**

`tests/__init__.py` vacío. `tests/test_health.py`:

```python
def test_health_reports_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
```

`tests/conftest.py`:

```python
import os

from app.core.config import Settings

_boot = Settings()
if not _boot.test_database_url:
    raise RuntimeError("TEST_DATABASE_URL no está definido; ponlo en .env")
os.environ["DATABASE_URL"] = _boot.test_database_url
os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["RATE_LIMIT_ENABLED"] = "false"

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

import app.models  # noqa: E402,F401
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def schema():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def clean_tables():
    yield
    tables = ", ".join(f'"{t.name}"' for t in reversed(Base.metadata.sorted_tables))
    if tables:
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
```

- [ ] **Step 5: Correr el test para verificar que falla**

Run: `.venv/bin/pytest tests/test_health.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'app'`.

- [ ] **Step 6: Escribir config, database, main y health**

`app/__init__.py`, `app/core/__init__.py`, `app/models/__init__.py`, `app/routers/__init__.py` vacíos.

`app/core/config.py`:

```python
from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_pg(value: str | None) -> str | None:
    """Railway expone URLs sin sufijo de driver; SQLAlchemy necesita psycopg."""
    if value is None:
        return None
    if value.startswith("postgres://"):
        return "postgresql+psycopg://" + value.removeprefix("postgres://")
    if value.startswith("postgresql://"):
        return "postgresql+psycopg://" + value.removeprefix("postgresql://")
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/hitoxsyner"
    test_database_url: str | None = None
    jwt_secret: str = "change-me"
    jwt_expire_hours: int = 12
    cors_origins: list[str] = []
    rate_limit_enabled: bool = False
    rate_limit_per_minute: int = 120
    seed_syner_password: str = "syner-demo"
    seed_exec_password: str = "exec-demo"
    seed_collab_password: str = "collab-demo"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        return value

    @field_validator("database_url", "test_database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str | None) -> str | None:
        return _normalize_pg(value)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

`app/database.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

`app/routers/health.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "ok", "database": "ok"}
```

`app/main.py`:

```python
import logging
import time
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.routers import health

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("hitoxsyner")
settings = get_settings()

app = FastAPI(title="Syner × HiTO Transformation Room API", docs_url="/api/docs", openapi_url="/api/openapi.json")

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

_hits: dict[str, deque] = defaultdict(deque)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if settings.rate_limit_enabled and request.url.path.startswith("/api/"):
        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = _hits[ip]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= settings.rate_limit_per_minute:
            return JSONResponse(status_code=429, content={"detail": "Too many requests"})
        window.append(now)
    return await call_next(request)


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(health.router, prefix="/api")
```

- [ ] **Step 7: Correr el test para verificar que pasa**

Run: `.venv/bin/pytest tests/test_health.py -v`
Expected: PASS (1 passed).

- [ ] **Step 8: Commit**

```bash
git add requirements.txt .gitignore .env.example app tests
git commit -m "feat: scaffold FastAPI, settings, health endpoint y harness de tests"
```

---

### Task 2: Modelos core (Organization, Engagement, User, Activity) y seguridad

**Files:**
- Create: `app/models/enums.py`, `app/models/base.py`, `app/models/organization.py`, `app/models/engagement.py`, `app/models/user.py`, `app/models/activity.py`, `app/core/security.py`
- Modify: `app/models/__init__.py`
- Test: `tests/test_security.py`, `tests/test_models.py`

**Interfaces:**
- Produces: enums `OrganizationKind`, `Role`, `EngagementStatus`, `Health`, `Level`, `FindingType`, `FindingStatus`, `InitiativeStatus`, `ActionStatus`, `OrganizationSide`, `ActivityAction`, `RoadmapPhase`; mixins `TimestampMixin`, `EngagementScopedMixin`; helper `db_enum(enum_cls, name)`; modelos `Organization`, `Engagement`, `User` (relación `organization`), `Activity`; funciones `hash_password(str) -> str`, `verify_password(str, str) -> bool`, `create_access_token(*, user_id: str, organization_id: str, role: str, expires_hours: int | None = None) -> str`, `decode_access_token(str) -> dict` (lanza `ValueError`).

- [ ] **Step 1: Escribir los tests de seguridad y de modelos (fallan)**

`tests/test_security.py`:

```python
import pytest

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_roundtrip():
    hashed = hash_password("s3cret-pass")
    assert hashed != "s3cret-pass"
    assert verify_password("s3cret-pass", hashed)
    assert not verify_password("otra", hashed)


def test_verify_password_with_garbage_hash_is_false():
    assert verify_password("x", "not-a-hash") is False


def test_token_roundtrip():
    token = create_access_token(user_id="u1", organization_id="o1", role="SYNER_ADMIN")
    payload = decode_access_token(token)
    assert payload["sub"] == "u1"
    assert payload["org"] == "o1"
    assert payload["role"] == "SYNER_ADMIN"


def test_expired_token_raises():
    token = create_access_token(user_id="u1", organization_id="o1", role="SYNER_ADMIN", expires_hours=-1)
    with pytest.raises(ValueError):
        decode_access_token(token)
```

`tests/test_models.py`:

```python
import uuid

from app.models.engagement import Engagement
from app.models.enums import Health, OrganizationKind, Role
from app.models.organization import Organization
from app.models.user import User


def test_models_persist_with_defaults(db):
    org = Organization(name="Cliente Demo", slug="cliente-demo", kind=OrganizationKind.CLIENT)
    db.add(org)
    db.flush()
    engagement = Engagement(organization_id=org.id, name="Programa")
    user = User(organization_id=org.id, email="a@b.com", full_name="A", password_hash="x", role=Role.HITO_EXECUTIVE)
    db.add_all([engagement, user])
    db.commit()
    db.refresh(engagement)
    assert isinstance(engagement.id, uuid.UUID)
    assert engagement.health == Health.ON_TRACK
    assert engagement.progress_pct == 0
    assert engagement.executive_summary == ""
    assert user.is_active is True
    assert user.organization.slug == "cliente-demo"
```

- [ ] **Step 2: Correr para verificar que fallan**

Run: `.venv/bin/pytest tests/test_security.py tests/test_models.py -v`
Expected: FAIL con `ModuleNotFoundError` en `app.core.security` y `app.models.engagement`.

- [ ] **Step 3: Escribir enums, base, modelos y seguridad**

`app/models/enums.py`:

```python
import enum


class OrganizationKind(str, enum.Enum):
    CONSULTANCY = "CONSULTANCY"
    CLIENT = "CLIENT"


class Role(str, enum.Enum):
    SYNER_ADMIN = "SYNER_ADMIN"
    HITO_EXECUTIVE = "HITO_EXECUTIVE"
    HITO_COLLABORATOR = "HITO_COLLABORATOR"


class EngagementStatus(str, enum.Enum):
    ACTIVE = "Active"
    PAUSED = "Paused"
    CLOSED = "Closed"


class Health(str, enum.Enum):
    ON_TRACK = "On Track"
    ATTENTION = "Attention"
    AT_RISK = "At Risk"


class Level(str, enum.Enum):
    """Impacto, severidad y prioridad comparten escala."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class FindingType(str, enum.Enum):
    OPPORTUNITY = "Opportunity"
    RISK = "Risk"
    GAP = "Gap"
    FINDING = "Finding"
    QUICK_WIN = "Quick Win"
    STRATEGIC_INSIGHT = "Strategic Insight"


class FindingStatus(str, enum.Enum):
    NEW = "New"
    UNDER_ANALYSIS = "Under Analysis"
    VALIDATED = "Validated"
    CONVERTED = "Converted to Initiative"
    ACCEPTED = "Accepted"
    CLOSED = "Closed"


class InitiativeStatus(str, enum.Enum):
    DISCOVERY = "Discovery"
    DESIGN = "Design"
    VALIDATION = "Validation"
    EXECUTION = "Execution"
    MONITORING = "Monitoring"
    COMPLETED = "Completed"
    ON_HOLD = "On Hold"


class ActionStatus(str, enum.Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    BLOCKED = "Blocked"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class OrganizationSide(str, enum.Enum):
    SYNER = "SYNER"
    CLIENT = "CLIENT"


class ActivityAction(str, enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    STATUS_CHANGED = "status_changed"
    CONVERTED = "converted"
    COMMENTED = "commented"


class RoadmapPhase(str, enum.Enum):
    DISCOVER = "Discover"
    DIAGNOSE = "Diagnose"
    DESIGN = "Design"
    PRIORITIZE = "Prioritize"
    EXECUTE = "Execute"
    MEASURE = "Measure"
```

`app/models/base.py`:

```python
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column


def db_enum(enum_cls: type[enum.Enum], name: str) -> Enum:
    """Enum de Postgres que guarda los valores (con espacios) y no los nombres."""
    return Enum(enum_cls, name=name, values_callable=lambda e: [m.value for m in e])


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class EngagementScopedMixin(TimestampMixin):
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True, nullable=False)
    engagement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("engagements.id"), index=True, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
```

`app/models/organization.py`:

```python
import uuid

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, db_enum
from app.models.enums import OrganizationKind


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    kind: Mapped[OrganizationKind] = mapped_column(db_enum(OrganizationKind, "organization_kind"), nullable=False)
```

`app/models/engagement.py`:

```python
import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, db_enum
from app.models.enums import EngagementStatus, Health


class Engagement(TimestampMixin, Base):
    __tablename__ = "engagements"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(300), nullable=True)
    status: Mapped[EngagementStatus] = mapped_column(
        db_enum(EngagementStatus, "engagement_status"), default=EngagementStatus.ACTIVE, nullable=False
    )
    health: Mapped[Health] = mapped_column(db_enum(Health, "engagement_health"), default=Health.ON_TRACK, nullable=False)
    progress_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    executive_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    target_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
```

`app/models/user.py`:

```python
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, db_enum
from app.models.enums import Role
from app.models.organization import Organization


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[Role] = mapped_column(db_enum(Role, "user_role"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization: Mapped[Organization] = relationship(Organization, lazy="joined")
```

`app/models/activity.py`:

```python
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import db_enum
from app.models.enums import ActivityAction


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True, nullable=False)
    engagement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("engagements.id"), index=True, nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    user_name: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    action: Mapped[ActivityAction] = mapped_column(db_enum(ActivityAction, "activity_action"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    changes: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

`app/models/__init__.py`:

```python
from app.models.activity import Activity
from app.models.engagement import Engagement
from app.models.organization import Organization
from app.models.user import User

__all__ = ["Activity", "Engagement", "Organization", "User"]
```

`app/core/security.py`:

```python
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(*, user_id: str, organization_id: str, role: str, expires_hours: int | None = None) -> str:
    settings = get_settings()
    hours = settings.jwt_expire_hours if expires_hours is None else expires_hours
    expires = datetime.now(timezone.utc) + timedelta(hours=hours)
    payload = {"sub": user_id, "org": organization_id, "role": role, "exp": expires}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise ValueError("invalid token") from exc
```

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `.venv/bin/pytest tests -v`
Expected: PASS (6 passed).

- [ ] **Step 5: Commit**

```bash
git add app tests
git commit -m "feat: modelos core (organization, engagement, user, activity) y seguridad JWT/bcrypt"
```

---

### Task 3: Autenticación (login, logout, me) y `get_current_user`

**Files:**
- Create: `app/dependencies.py`, `app/schemas/__init__.py`, `app/schemas/common.py`, `app/schemas/auth.py`, `app/schemas/user.py`, `app/crud/__init__.py`, `app/crud/users.py`, `app/routers/auth.py`
- Modify: `app/main.py`
- Create: `tests/factories.py`
- Test: `tests/test_auth.py`

**Interfaces:**
- Produces: `get_current_user(...) -> User`; `can_access_organization(user, organization_id) -> bool`; `COOKIE_NAME = "access_token"`; `Page[T]` y `pagination_params() -> Pagination(limit, offset)` en `schemas/common.py`; `UserRead` con `from_user(user)`; `crud.users.get_by_email(db, email)`, `get(db, user_id)`, `list_by_organization(db, organization_id)`, `create(db, **fields)`; fixtures/helper de tests `make_org`, `make_engagement`, `make_user`, `login(client, email, password="pass1234") -> dict` (headers Bearer) y fixture `world`.

- [ ] **Step 1: Escribir factories y tests de auth (fallan)**

`tests/factories.py`:

```python
from types import SimpleNamespace

from app.core.security import hash_password
from app.models.engagement import Engagement
from app.models.enums import OrganizationKind, Role
from app.models.organization import Organization
from app.models.user import User

PASSWORD = "pass1234"


def make_org(db, name, slug, kind=OrganizationKind.CLIENT):
    org = Organization(name=name, slug=slug, kind=kind)
    db.add(org)
    db.flush()
    return org


def make_engagement(db, org, name="Programa de transformación"):
    engagement = Engagement(organization_id=org.id, name=name)
    db.add(engagement)
    db.flush()
    return engagement


def make_user(db, org, email, role, full_name=None, password=PASSWORD, is_active=True):
    user = User(
        organization_id=org.id,
        email=email,
        full_name=full_name or email.split("@")[0],
        password_hash=hash_password(password),
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.flush()
    return user


def build_world(db):
    syner = make_org(db, "Syner", "syner", OrganizationKind.CONSULTANCY)
    admin = make_user(db, syner, "admin@syner.example", Role.SYNER_ADMIN, "Syner Admin")
    org_a = make_org(db, "Cliente A", "cliente-a")
    org_b = make_org(db, "Cliente B", "cliente-b")
    eng_a = make_engagement(db, org_a, "Programa A")
    eng_b = make_engagement(db, org_b, "Programa B")
    exec_a = make_user(db, org_a, "exec@a.example", Role.HITO_EXECUTIVE, "Exec A")
    collab_a = make_user(db, org_a, "collab@a.example", Role.HITO_COLLABORATOR, "Collab A")
    exec_b = make_user(db, org_b, "exec@b.example", Role.HITO_EXECUTIVE, "Exec B")
    collab_b = make_user(db, org_b, "collab@b.example", Role.HITO_COLLABORATOR, "Collab B")
    db.commit()
    for obj in (syner, admin, org_a, org_b, eng_a, eng_b, exec_a, collab_a, exec_b, collab_b):
        db.refresh(obj)
    return SimpleNamespace(
        syner=syner, admin=admin, org_a=org_a, org_b=org_b, eng_a=eng_a, eng_b=eng_b,
        exec_a=exec_a, collab_a=collab_a, exec_b=exec_b, collab_b=collab_b,
    )


def login(client, email, password=PASSWORD):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
```

Agregar al final de `tests/conftest.py`:

```python
from tests.factories import build_world  # noqa: E402


@pytest.fixture
def world(db):
    return build_world(db)
```

`tests/test_auth.py`:

```python
from app.core.security import create_access_token
from tests.factories import PASSWORD, login, make_user
from app.models.enums import Role


def test_login_returns_token_and_sets_cookie(client, world):
    response = client.post("/api/auth/login", json={"email": "admin@syner.example", "password": PASSWORD})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "admin@syner.example"
    assert body["user"]["role"] == "SYNER_ADMIN"
    assert body["user"]["organization_name"] == "Syner"
    assert "access_token" in response.cookies


def test_login_is_case_insensitive_on_email(client, world):
    response = client.post("/api/auth/login", json={"email": "ADMIN@Syner.example", "password": PASSWORD})
    assert response.status_code == 200


def test_login_rejects_wrong_password(client, world):
    response = client.post("/api/auth/login", json={"email": "admin@syner.example", "password": "nope"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Credenciales inválidas"}


def test_login_rejects_inactive_user(client, db, world):
    make_user(db, world.org_a, "off@a.example", Role.HITO_COLLABORATOR, is_active=False)
    db.commit()
    response = client.post("/api/auth/login", json={"email": "off@a.example", "password": PASSWORD})
    assert response.status_code == 401


def test_me_with_bearer(client, world):
    headers = login(client, "exec@a.example")
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["role"] == "HITO_EXECUTIVE"


def test_me_with_cookie_only(client, world):
    client.post("/api/auth/login", json={"email": "exec@a.example", "password": PASSWORD})
    response = client.get("/api/auth/me")
    assert response.status_code == 200


def test_me_without_credentials_is_401(client, world):
    assert client.get("/api/auth/me").status_code == 401


def test_me_with_expired_token_is_401(client, world):
    token = create_access_token(user_id=str(world.admin.id), organization_id=str(world.syner.id), role="SYNER_ADMIN", expires_hours=-1)
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired token"}


def test_me_for_deactivated_user_is_401(client, db, world):
    headers = login(client, "collab@a.example")
    world.collab_a.is_active = False
    db.commit()
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_logout_clears_cookie(client, world):
    client.post("/api/auth/login", json={"email": "exec@a.example", "password": PASSWORD})
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401
```

- [ ] **Step 2: Correr para verificar que fallan**

Run: `.venv/bin/pytest tests/test_auth.py -v`
Expected: FAIL con 404 en `/api/auth/login` (ruta no existe).

- [ ] **Step 3: Escribir schemas comunes, auth, usuarios, crud, dependencias y router**

`app/schemas/__init__.py` vacío. `app/schemas/common.py`:

```python
from dataclasses import dataclass
from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int


@dataclass
class Pagination:
    limit: int
    offset: int


def pagination_params(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)) -> Pagination:
    return Pagination(limit=limit, offset=offset)
```

`app/schemas/user.py`:

```python
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import Role


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: Role
    organization_id: uuid.UUID
    organization_name: str
    is_active: bool

    @classmethod
    def from_user(cls, user) -> "UserRead":
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            organization_id=user.organization_id,
            organization_name=user.organization.name,
            is_active=user.is_active,
        )


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=8, max_length=72)
    role: Role


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    password: str | None = Field(default=None, min_length=8, max_length=72)
    role: Role | None = None
    is_active: bool | None = None
```

`app/schemas/auth.py`:

```python
from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserRead


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
```

`app/crud/__init__.py` vacío. `app/crud/users.py`:

```python
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def get(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def list_by_organization(db: Session, organization_id: uuid.UUID) -> list[User]:
    return list(db.scalars(select(User).where(User.organization_id == organization_id).order_by(User.full_name)))


def create(db: Session, **fields) -> User:
    fields["email"] = fields["email"].lower()
    user = User(**fields)
    db.add(user)
    db.flush()
    return user
```

`app/dependencies.py`:

```python
import uuid

from fastapi import Cookie, Depends, Header, HTTPException, Path
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.models.engagement import Engagement
from app.models.enums import Role
from app.models.user import User

COOKIE_NAME = "access_token"


def get_current_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    access_token: str | None = Cookie(default=None),
) -> User:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif access_token:
        token = access_token
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_access_token(token)
        user_id = uuid.UUID(str(payload.get("sub", "")))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


def can_access_organization(user: User, organization_id: uuid.UUID) -> bool:
    return user.role == Role.SYNER_ADMIN or user.organization_id == organization_id


def require_roles(*roles: Role):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")
        return user

    return dependency


def get_engagement(
    engagement_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Engagement:
    engagement = db.get(Engagement, engagement_id)
    if engagement is None or not can_access_organization(user, engagement.organization_id):
        raise HTTPException(status_code=404, detail="Engagement not found")
    return engagement


def scoped(model, param: str):
    """Dependencia que carga una entidad por id y verifica acceso por organización (404 si no)."""

    def dependency(
        entity_id: uuid.UUID = Path(alias=param),
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        obj = db.get(model, entity_id)
        if obj is None or not can_access_organization(user, obj.organization_id):
            raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
        return obj

    return dependency
```

`app/routers/auth.py`:

```python
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, verify_password
from app.crud import users as users_crud
from app.database import get_db
from app.dependencies import COOKIE_NAME, get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = users_crud.get_by_email(db, data.email)
    if user is None or not user.is_active or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    token = create_access_token(user_id=str(user.id), organization_id=str(user.organization_id), role=user.role.value)
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    settings = get_settings()
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.jwt_expire_hours * 3600,
        path="/",
    )
    return TokenResponse(access_token=token, user=UserRead.from_user(user))


@router.post("/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    response.status_code = 204
    return response


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    return UserRead.from_user(user)
```

En `app/main.py` reemplazar `from app.routers import health` por `from app.routers import auth, health` y después de `app.include_router(health.router, prefix="/api")` agregar `app.include_router(auth.router, prefix="/api")`.

- [ ] **Step 4: Correr los tests**

Run: `.venv/bin/pytest tests -v`
Expected: PASS (16 passed).

- [ ] **Step 5: Commit**

```bash
git add app tests
git commit -m "feat: autenticación JWT (login, logout, me) con cookie httpOnly y Bearer"
```

---

### Task 4: Engagements, administración de usuarios y scope por organización

**Files:**
- Create: `app/schemas/engagement.py`, `app/crud/engagements.py`, `app/routers/engagements.py`
- Modify: `app/main.py`
- Test: `tests/test_engagements.py`

**Interfaces:**
- Consumes: `get_engagement`, `require_roles`, `can_access_organization`, `crud.users.*`, `UserCreate`, `UserUpdate`, `UserRead`.
- Produces: `EngagementRead`, `EngagementUpdate`; `crud.engagements.list_for_user(db, user) -> list[Engagement]`; rutas `/api/engagements`, `/api/engagements/{engagement_id}`, `/api/engagements/{engagement_id}/users`, `/api/engagements/{engagement_id}/users/{user_id}`.

- [ ] **Step 1: Escribir tests (fallan)**

`tests/test_engagements.py`:

```python
from tests.factories import login


def test_syner_lists_all_engagements(client, world):
    headers = login(client, "admin@syner.example")
    response = client.get("/api/engagements", headers=headers)
    assert response.status_code == 200
    assert {e["name"] for e in response.json()} == {"Programa A", "Programa B"}


def test_client_user_lists_only_own_engagements(client, world):
    headers = login(client, "exec@a.example")
    names = {e["name"] for e in client.get("/api/engagements", headers=headers).json()}
    assert names == {"Programa A"}


def test_client_user_cannot_read_other_org_engagement(client, world):
    headers = login(client, "exec@b.example")
    assert client.get(f"/api/engagements/{world.eng_a.id}", headers=headers).status_code == 404


def test_syner_updates_summary_health_and_progress(client, world):
    headers = login(client, "admin@syner.example")
    response = client.patch(
        f"/api/engagements/{world.eng_a.id}",
        headers=headers,
        json={"executive_summary": "Situación actual: arranque.", "health": "Attention", "progress_pct": 15},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["health"] == "Attention"
    assert body["progress_pct"] == 15
    assert body["executive_summary"] == "Situación actual: arranque."


def test_executive_patch_own_engagement_is_403(client, world):
    headers = login(client, "exec@a.example")
    response = client.patch(f"/api/engagements/{world.eng_a.id}", headers=headers, json={"progress_pct": 50})
    assert response.status_code == 403


def test_progress_out_of_range_is_422(client, world):
    headers = login(client, "admin@syner.example")
    assert client.patch(f"/api/engagements/{world.eng_a.id}", headers=headers, json={"progress_pct": 101}).status_code == 422
    assert client.patch(f"/api/engagements/{world.eng_a.id}", headers=headers, json={"executive_summary": "x" * 2001}).status_code == 422


def test_syner_creates_client_user(client, world):
    headers = login(client, "admin@syner.example")
    payload = {"email": "Nuevo@A.example", "full_name": "Nuevo", "password": "password123", "role": "HITO_COLLABORATOR"}
    response = client.post(f"/api/engagements/{world.eng_a.id}/users", headers=headers, json=payload)
    assert response.status_code == 201
    assert response.json()["email"] == "nuevo@a.example"
    assert response.json()["organization_id"] == str(world.org_a.id)
    assert client.post(f"/api/engagements/{world.eng_a.id}/users", headers=headers, json=payload).status_code == 409
    assert login(client, "nuevo@a.example", "password123")


def test_cannot_create_syner_admin_inside_client_engagement(client, world):
    headers = login(client, "admin@syner.example")
    payload = {"email": "x@a.example", "full_name": "X", "password": "password123", "role": "SYNER_ADMIN"}
    assert client.post(f"/api/engagements/{world.eng_a.id}/users", headers=headers, json=payload).status_code == 422


def test_executive_cannot_manage_users(client, world):
    headers = login(client, "exec@a.example")
    assert client.get(f"/api/engagements/{world.eng_a.id}/users", headers=headers).status_code == 403


def test_syner_deactivates_user(client, world):
    headers = login(client, "admin@syner.example")
    response = client.patch(
        f"/api/engagements/{world.eng_a.id}/users/{world.collab_a.id}", headers=headers, json={"is_active": False}
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert client.patch(
        f"/api/engagements/{world.eng_a.id}/users/{world.exec_b.id}", headers=headers, json={"is_active": False}
    ).status_code == 404
```

- [ ] **Step 2: Correr para verificar que fallan**

Run: `.venv/bin/pytest tests/test_engagements.py -v`
Expected: FAIL con 404 en `/api/engagements`.

- [ ] **Step 3: Escribir schemas, crud y router**

`app/schemas/engagement.py`:

```python
import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EngagementStatus, Health


class EngagementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    subtitle: str | None
    status: EngagementStatus
    health: Health
    progress_pct: int
    executive_summary: str
    start_date: date | None
    target_end_date: date | None


class EngagementUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    subtitle: str | None = Field(default=None, max_length=300)
    status: EngagementStatus | None = None
    health: Health | None = None
    progress_pct: int | None = Field(default=None, ge=0, le=100)
    executive_summary: str | None = Field(default=None, max_length=2000)
    start_date: date | None = None
    target_end_date: date | None = None
```

`app/crud/engagements.py`:

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.engagement import Engagement
from app.models.enums import Role
from app.models.user import User


def list_for_user(db: Session, user: User) -> list[Engagement]:
    query = select(Engagement).order_by(Engagement.name)
    if user.role != Role.SYNER_ADMIN:
        query = query.where(Engagement.organization_id == user.organization_id)
    return list(db.scalars(query))
```

`app/routers/engagements.py`:

```python
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.crud import engagements as engagements_crud
from app.crud import users as users_crud
from app.database import get_db
from app.dependencies import get_current_user, get_engagement, require_roles
from app.models.engagement import Engagement
from app.models.enums import Role
from app.models.user import User
from app.schemas.engagement import EngagementRead, EngagementUpdate
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/engagements", tags=["engagements"])
syner_only = Depends(require_roles(Role.SYNER_ADMIN))


@router.get("", response_model=list[EngagementRead])
def list_engagements(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return engagements_crud.list_for_user(db, user)


@router.get("/{engagement_id}", response_model=EngagementRead)
def read_engagement(engagement: Engagement = Depends(get_engagement)):
    return engagement


@router.patch("/{engagement_id}", response_model=EngagementRead)
def update_engagement(
    data: EngagementUpdate,
    user: User = syner_only,
    engagement: Engagement = Depends(get_engagement),
    db: Session = Depends(get_db),
):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(engagement, field, value)
    db.commit()
    db.refresh(engagement)
    return engagement


@router.get("/{engagement_id}/users", response_model=list[UserRead])
def list_users(user: User = syner_only, engagement: Engagement = Depends(get_engagement), db: Session = Depends(get_db)):
    return [UserRead.from_user(u) for u in users_crud.list_by_organization(db, engagement.organization_id)]


@router.post("/{engagement_id}/users", response_model=UserRead, status_code=201)
def create_user(
    data: UserCreate,
    user: User = syner_only,
    engagement: Engagement = Depends(get_engagement),
    db: Session = Depends(get_db),
):
    if data.role == Role.SYNER_ADMIN:
        raise HTTPException(status_code=422, detail="Un engagement de cliente solo admite roles HITO_EXECUTIVE o HITO_COLLABORATOR")
    if users_crud.get_by_email(db, data.email) is not None:
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese email")
    created = users_crud.create(
        db,
        organization_id=engagement.organization_id,
        email=data.email,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.commit()
    db.refresh(created)
    return UserRead.from_user(created)


@router.patch("/{engagement_id}/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    user: User = syner_only,
    engagement: Engagement = Depends(get_engagement),
    db: Session = Depends(get_db),
):
    target = users_crud.get(db, user_id)
    if target is None or target.organization_id != engagement.organization_id:
        raise HTTPException(status_code=404, detail="User not found")
    if data.role == Role.SYNER_ADMIN:
        raise HTTPException(status_code=422, detail="Un engagement de cliente solo admite roles HITO_EXECUTIVE o HITO_COLLABORATOR")
    payload = data.model_dump(exclude_unset=True)
    if "password" in payload:
        target.password_hash = hash_password(payload.pop("password"))
    for field, value in payload.items():
        setattr(target, field, value)
    db.commit()
    db.refresh(target)
    return UserRead.from_user(target)
```

En `app/main.py`: importar `engagements` junto a `auth, health` e incluir `app.include_router(engagements.router, prefix="/api")`.

- [ ] **Step 4: Correr los tests**

Run: `.venv/bin/pytest tests -v`
Expected: PASS (26 passed).

- [ ] **Step 5: Commit**

```bash
git add app tests
git commit -m "feat: engagements con scope por organización y administración de usuarios"
```

---

### Task 5: Activity trail (service, crud, router)

**Files:**
- Create: `app/schemas/activity.py`, `app/crud/activities.py`, `app/services/__init__.py`, `app/services/activity.py`, `app/routers/activity.py`
- Modify: `app/main.py`
- Test: `tests/test_activity.py`

**Interfaces:**
- Produces: `log_activity(db, *, user, engagement, action: ActivityAction, entity_type: str, entity_id: uuid.UUID, summary: str, changes: list[dict] | None = None) -> Activity` (hace `db.add` y `db.flush`, NO commit); `diff_changes(entity, payload: dict) -> list[dict]` con elementos `{"field", "before", "after"}`; `ActivityRead`; `crud.activities.list_for_engagement(db, engagement_id, *, entity_type=None, entity_id=None, limit=50, offset=0) -> tuple[list[Activity], int]`; `crud.activities.recent(db, engagement_id, limit) -> list[Activity]`; ruta `GET /api/engagements/{engagement_id}/activity`.

- [ ] **Step 1: Escribir tests (fallan)**

`tests/test_activity.py`:

```python
import uuid
from datetime import date

from app.models.enums import ActivityAction, Health
from app.services.activity import diff_changes, log_activity
from tests.factories import login


def test_diff_changes_serializes_enums_dates_and_ignores_equal_values(world):
    payload = {"health": Health.AT_RISK, "start_date": date(2026, 10, 1), "name": "Programa A"}
    changes = diff_changes(world.eng_a, payload)
    assert changes == [
        {"field": "health", "before": "On Track", "after": "At Risk"},
        {"field": "start_date", "before": None, "after": "2026-10-01"},
    ]


def test_log_activity_and_list_scoped(client, db, world):
    entity_id = uuid.uuid4()
    log_activity(
        db, user=world.admin, engagement=world.eng_a, action=ActivityAction.CREATED,
        entity_type="finding", entity_id=entity_id, summary='Syner Admin created Finding "X"',
    )
    log_activity(
        db, user=world.admin, engagement=world.eng_b, action=ActivityAction.CREATED,
        entity_type="finding", entity_id=uuid.uuid4(), summary="other org",
    )
    db.commit()
    headers = login(client, "exec@a.example")
    response = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["summary"] == 'Syner Admin created Finding "X"'
    assert body["items"][0]["user_name"] == "Syner Admin"
    assert body["items"][0]["entity_id"] == str(entity_id)
    filtered = client.get(
        f"/api/engagements/{world.eng_a.id}/activity",
        headers=headers, params={"entity_type": "finding", "entity_id": str(uuid.uuid4())},
    ).json()
    assert filtered["total"] == 0
    assert client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=login(client, "exec@b.example")).status_code == 404
```

- [ ] **Step 2: Correr para verificar que fallan**

Run: `.venv/bin/pytest tests/test_activity.py -v`
Expected: FAIL con `ModuleNotFoundError: app.services`.

- [ ] **Step 3: Escribir schema, crud, service y router**

`app/schemas/activity.py`:

```python
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ActivityAction


class ActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID | None
    user_name: str
    action: ActivityAction
    entity_type: str
    entity_id: uuid.UUID
    summary: str
    changes: list[dict]
    created_at: datetime
```

`app/crud/activities.py`:

```python
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.activity import Activity


def list_for_engagement(
    db: Session, engagement_id: uuid.UUID, *, entity_type: str | None = None,
    entity_id: uuid.UUID | None = None, limit: int = 50, offset: int = 0,
) -> tuple[list[Activity], int]:
    query = select(Activity).where(Activity.engagement_id == engagement_id)
    if entity_type:
        query = query.where(Activity.entity_type == entity_type)
    if entity_id:
        query = query.where(Activity.entity_id == entity_id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Activity.created_at.desc()).limit(limit).offset(offset)))
    return items, total


def recent(db: Session, engagement_id: uuid.UUID, limit: int = 15) -> list[Activity]:
    return list_for_engagement(db, engagement_id, limit=limit)[0]
```

`app/services/__init__.py` vacío. `app/services/activity.py`:

```python
import enum
import uuid
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.engagement import Engagement
from app.models.enums import ActivityAction
from app.models.user import User


def _plain(value):
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


def diff_changes(entity, payload: dict) -> list[dict]:
    changes = []
    for field, new_value in payload.items():
        before = _plain(getattr(entity, field))
        after = _plain(new_value)
        if before != after:
            changes.append({"field": field, "before": before, "after": after})
    return changes


def log_activity(
    db: Session, *, user: User, engagement: Engagement, action: ActivityAction,
    entity_type: str, entity_id: uuid.UUID, summary: str, changes: list[dict] | None = None,
) -> Activity:
    activity = Activity(
        organization_id=engagement.organization_id,
        engagement_id=engagement.id,
        user_id=user.id,
        user_name=user.full_name,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary[:500],
        changes=changes or [],
    )
    db.add(activity)
    db.flush()
    return activity
```

`app/routers/activity.py`:

```python
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import activities as activities_crud
from app.database import get_db
from app.dependencies import get_engagement
from app.models.engagement import Engagement
from app.schemas.activity import ActivityRead
from app.schemas.common import Page, Pagination, pagination_params

router = APIRouter(tags=["activity"])


@router.get("/engagements/{engagement_id}/activity", response_model=Page[ActivityRead])
def list_activity(
    engagement: Engagement = Depends(get_engagement),
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = activities_crud.list_for_engagement(
        db, engagement.id, entity_type=entity_type, entity_id=entity_id,
        limit=pagination.limit, offset=pagination.offset,
    )
    return Page(items=items, total=total)
```

En `app/main.py`: importar `activity` e incluir `app.include_router(activity.router, prefix="/api")`.

- [ ] **Step 4: Correr los tests**

Run: `.venv/bin/pytest tests -v`
Expected: PASS (28 passed).

- [ ] **Step 5: Commit**

```bash
git add app tests
git commit -m "feat: activity trail con diff de cambios y listado por engagement"
```

---

### Task 6: Findings (model, schema, crud, service, router)

**Files:**
- Create: `app/models/finding.py`, `app/schemas/finding.py`, `app/crud/findings.py`, `app/services/findings.py`, `app/routers/findings.py`
- Modify: `app/models/__init__.py`, `app/main.py`
- Test: `tests/test_findings.py`

**Interfaces:**
- Consumes: `EngagementScopedMixin`, `db_enum`, `log_activity`, `diff_changes`, `get_engagement`, `scoped`, `require_roles`, `Page`, `pagination_params`.
- Produces: modelo `Finding`; `FindingCreate`, `FindingUpdate`, `FindingRead`; `crud.findings.list_for_engagement(db, engagement_id, *, status=None, type=None, limit, offset) -> (items, total)`, `crud.findings.key_findings(db, engagement_id, limit=6)`, `crud.findings.count_critical_open(db, engagement_id) -> int`, `crud.findings.list_by_initiative(db, initiative_id)`; `services.findings.create_finding(db, *, user, engagement, data) -> Finding`, `services.findings.update_finding(db, *, user, finding, data) -> Finding`; rutas `GET|POST /api/engagements/{engagement_id}/findings`, `GET|PATCH /api/findings/{finding_id}`.

- [ ] **Step 1: Escribir tests (fallan)**

`tests/test_findings.py`:

```python
from tests.factories import login

PAYLOAD = {
    "title": "Conciliación manual diaria",
    "description": "El cierre diario depende de hojas de cálculo.",
    "type": "Quick Win",
    "area": "Operaciones",
    "impact": "High",
    "severity": "Medium",
    "recommendation": "Automatizar la conciliación.",
}


def test_syner_creates_finding_and_logs_activity(client, world):
    headers = login(client, "admin@syner.example")
    response = client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=headers, json=PAYLOAD)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "New"
    assert body["type"] == "Quick Win"
    assert body["engagement_id"] == str(world.eng_a.id)
    assert body["initiative_id"] is None
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=headers).json()
    assert activity["items"][0]["summary"] == 'Syner Admin created Finding "Conciliación manual diaria"'


def test_client_roles_cannot_create_findings(client, world):
    for email in ("exec@a.example", "collab@a.example"):
        response = client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=login(client, email), json=PAYLOAD)
        assert response.status_code == 403


def test_findings_are_isolated_by_organization(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, json=PAYLOAD).json()
    client.post(f"/api/engagements/{world.eng_b.id}/findings", headers=admin, json={**PAYLOAD, "title": "De B"})
    listing = client.get(f"/api/engagements/{world.eng_a.id}/findings", headers=login(client, "collab@a.example")).json()
    assert listing["total"] == 1
    assert listing["items"][0]["title"] == "Conciliación manual diaria"
    assert client.get(f"/api/findings/{created['id']}", headers=login(client, "exec@b.example")).status_code == 404
    assert client.get(f"/api/engagements/{world.eng_b.id}/findings", headers=login(client, "exec@a.example")).status_code == 404


def test_status_change_logs_before_and_after(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, json=PAYLOAD).json()
    response = client.patch(f"/api/findings/{created['id']}", headers=admin, json={"status": "Validated"})
    assert response.status_code == 200
    assert response.json()["status"] == "Validated"
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["action"] == "status_changed"
    assert activity["summary"] == 'Syner Admin updated Finding "Conciliación manual diaria" from New to Validated'
    assert activity["changes"] == [{"field": "status", "before": "New", "after": "Validated"}]


def test_list_filters_by_status_and_type(client, world):
    admin = login(client, "admin@syner.example")
    client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, json=PAYLOAD)
    client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, json={**PAYLOAD, "title": "Otro", "type": "Gap"})
    by_type = client.get(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, params={"type": "Gap"}).json()
    assert by_type["total"] == 1 and by_type["items"][0]["title"] == "Otro"
    by_status = client.get(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, params={"status": "Closed"}).json()
    assert by_status["total"] == 0


def test_title_is_required_and_limited(client, world):
    admin = login(client, "admin@syner.example")
    assert client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, json={}).status_code == 422
    assert client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, json={"title": "x" * 201}).status_code == 422


def test_explicit_null_on_required_field_is_422_but_nullable_is_allowed(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, json=PAYLOAD).json()
    assert client.patch(f"/api/findings/{created['id']}", headers=admin, json={"title": None}).status_code == 422
    assert client.patch(f"/api/findings/{created['id']}", headers=admin, json={"syner_owner_id": None}).status_code == 200
```

- [ ] **Step 2: Correr para verificar que fallan**

Run: `.venv/bin/pytest tests/test_findings.py -v`
Expected: FAIL con 404 en `/api/engagements/{id}/findings`.

- [ ] **Step 3: Escribir model, schema, crud, service y router**

`app/models/finding.py`:

```python
import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import EngagementScopedMixin, db_enum
from app.models.enums import FindingStatus, FindingType, Level


class Finding(EngagementScopedMixin, Base):
    __tablename__ = "findings"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    context: Mapped[str] = mapped_column(Text, default="", nullable=False)
    type: Mapped[FindingType] = mapped_column(db_enum(FindingType, "finding_type"), default=FindingType.FINDING, nullable=False)
    area: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    source: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    impact: Mapped[Level] = mapped_column(db_enum(Level, "finding_impact"), default=Level.MEDIUM, nullable=False)
    severity: Mapped[Level] = mapped_column(db_enum(Level, "finding_severity"), default=Level.MEDIUM, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, default="", nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    syner_owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    found_on: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    status: Mapped[FindingStatus] = mapped_column(db_enum(FindingStatus, "finding_status"), default=FindingStatus.NEW, nullable=False)
```

`app/schemas/finding.py`:

```python
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import FindingStatus, FindingType, Level


class FindingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10000)
    context: str = Field(default="", max_length=10000)
    type: FindingType = FindingType.FINDING
    area: str = Field(default="", max_length=120)
    source: str = Field(default="", max_length=200)
    impact: Level = Level.MEDIUM
    severity: Level = Level.MEDIUM
    evidence: str = Field(default="", max_length=10000)
    recommendation: str = Field(default="", max_length=10000)
    syner_owner_id: uuid.UUID | None = None
    found_on: date = Field(default_factory=date.today)
    status: FindingStatus = FindingStatus.NEW


class FindingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    context: str | None = Field(default=None, max_length=10000)
    type: FindingType | None = None
    area: str | None = Field(default=None, max_length=120)
    source: str | None = Field(default=None, max_length=200)
    impact: Level | None = None
    severity: Level | None = None
    evidence: str | None = Field(default=None, max_length=10000)
    recommendation: str | None = Field(default=None, max_length=10000)
    syner_owner_id: uuid.UUID | None = None
    found_on: date | None = None
    status: FindingStatus | None = None


class FindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    engagement_id: uuid.UUID
    title: str
    description: str
    context: str
    type: FindingType
    area: str
    source: str
    impact: Level
    severity: Level
    evidence: str
    recommendation: str
    syner_owner_id: uuid.UUID | None
    found_on: date
    status: FindingStatus
    initiative_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
```

`app/crud/findings.py`:

```python
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import FindingStatus, FindingType, Level
from app.models.finding import Finding


def list_for_engagement(
    db: Session, engagement_id: uuid.UUID, *, status: FindingStatus | None = None,
    type: FindingType | None = None, limit: int = 50, offset: int = 0,
) -> tuple[list[Finding], int]:
    query = select(Finding).where(Finding.engagement_id == engagement_id)
    if status:
        query = query.where(Finding.status == status)
    if type:
        query = query.where(Finding.type == type)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Finding.created_at.desc()).limit(limit).offset(offset)))
    return items, total


def key_findings(db: Session, engagement_id: uuid.UUID, limit: int = 6) -> list[Finding]:
    query = (
        select(Finding)
        .where(Finding.engagement_id == engagement_id)
        .where(Finding.impact.in_([Level.HIGH, Level.CRITICAL]))
        .where(Finding.status != FindingStatus.CLOSED)
        .order_by(Finding.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(query))


def count_critical_open(db: Session, engagement_id: uuid.UUID) -> int:
    query = (
        select(func.count())
        .select_from(Finding)
        .where(Finding.engagement_id == engagement_id)
        .where(Finding.impact == Level.CRITICAL)
        .where(Finding.status != FindingStatus.CLOSED)
    )
    return db.scalar(query) or 0


def list_by_initiative(db: Session, initiative_id: uuid.UUID) -> list[Finding]:
    return list(db.scalars(select(Finding).where(Finding.initiative_id == initiative_id).order_by(Finding.created_at)))
```

Nota: `Finding.initiative_id` se agrega en Task 7; `list_by_initiative` se escribe aquí pero solo se usa desde Task 8. Si el linter se queja antes de Task 7, es esperado.

`app/services/findings.py`:

```python
from sqlalchemy.orm import Session

from app.models.engagement import Engagement
from app.models.enums import ActivityAction
from app.models.finding import Finding
from app.models.user import User
from app.schemas.common import updates
from app.schemas.finding import FindingCreate, FindingUpdate
from app.services.activity import diff_changes, log_activity


def create_finding(db: Session, *, user: User, engagement: Engagement, data: FindingCreate) -> Finding:
    finding = Finding(
        organization_id=engagement.organization_id,
        engagement_id=engagement.id,
        created_by=user.id,
        **data.model_dump(),
    )
    db.add(finding)
    db.flush()
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="finding",
        entity_id=finding.id, summary=f'{user.full_name} created Finding "{finding.title}"',
    )
    db.commit()
    db.refresh(finding)
    return finding


def update_finding(db: Session, *, user: User, finding: Finding, data: FindingUpdate) -> Finding:
    payload = updates(data, nullable={"syner_owner_id"})
    changes = diff_changes(finding, payload)
    if not changes:
        return finding
    for field, value in payload.items():
        setattr(finding, field, value)
    engagement = db.get(Engagement, finding.engagement_id)
    status_change = next((c for c in changes if c["field"] == "status"), None)
    if status_change:
        action = ActivityAction.STATUS_CHANGED
        summary = f'{user.full_name} updated Finding "{finding.title}" from {status_change["before"]} to {status_change["after"]}'
    else:
        action = ActivityAction.UPDATED
        summary = f'{user.full_name} updated Finding "{finding.title}"'
    log_activity(
        db, user=user, engagement=engagement, action=action, entity_type="finding",
        entity_id=finding.id, summary=summary, changes=changes,
    )
    db.commit()
    db.refresh(finding)
    return finding
```

`app/routers/findings.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import findings as findings_crud
from app.database import get_db
from app.dependencies import get_engagement, require_roles, scoped
from app.models.engagement import Engagement
from app.models.enums import FindingStatus, FindingType, Role
from app.models.finding import Finding
from app.models.user import User
from app.schemas.common import Page, Pagination, pagination_params
from app.schemas.finding import FindingCreate, FindingRead, FindingUpdate
from app.services import findings as findings_service

router = APIRouter(tags=["findings"])
syner_only = Depends(require_roles(Role.SYNER_ADMIN))
scoped_finding = Depends(scoped(Finding, "finding_id"))


@router.get("/engagements/{engagement_id}/findings", response_model=Page[FindingRead])
def list_findings(
    engagement: Engagement = Depends(get_engagement),
    status: FindingStatus | None = None,
    type: FindingType | None = None,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = findings_crud.list_for_engagement(
        db, engagement.id, status=status, type=type, limit=pagination.limit, offset=pagination.offset
    )
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/findings", response_model=FindingRead, status_code=201)
def create_finding(
    data: FindingCreate,
    user: User = syner_only,
    engagement: Engagement = Depends(get_engagement),
    db: Session = Depends(get_db),
):
    return findings_service.create_finding(db, user=user, engagement=engagement, data=data)


@router.get("/findings/{finding_id}", response_model=FindingRead)
def read_finding(finding: Finding = scoped_finding):
    return finding


@router.patch("/findings/{finding_id}", response_model=FindingRead)
def update_finding(
    data: FindingUpdate,
    user: User = syner_only,
    finding: Finding = scoped_finding,
    db: Session = Depends(get_db),
):
    return findings_service.update_finding(db, user=user, finding=finding, data=data)
```

En `app/models/__init__.py` agregar `from app.models.finding import Finding` y `"Finding"` a `__all__`. En `app/main.py` importar `findings` e incluir `app.include_router(findings.router, prefix="/api")`.

- [ ] **Step 4: Correr los tests**

Run: `.venv/bin/pytest tests -v`
Expected: PASS (35 passed).

- [ ] **Step 5: Commit**

```bash
git add app tests
git commit -m "feat: módulo findings con RBAC, scope y activity trail"
```

---

### Task 7: Initiatives y conversión Finding → Initiative

**Files:**
- Create: `app/models/initiative.py`, `app/schemas/initiative.py`, `app/crud/initiatives.py`, `app/services/initiatives.py`, `app/routers/initiatives.py`
- Modify: `app/models/finding.py`, `app/models/__init__.py`, `app/services/findings.py`, `app/routers/findings.py`, `app/main.py`
- Test: `tests/test_initiatives.py`

**Interfaces:**
- Consumes: Task 6 completo.
- Produces: modelo `Initiative`; `Finding.initiative_id`; `InitiativeCreate`, `InitiativeUpdate`, `InitiativeRead`; `crud.initiatives.list_for_engagement(db, engagement_id, *, status=None, limit, offset)`, `crud.initiatives.active(db, engagement_id) -> list[Initiative]`, `crud.initiatives.count_active(db, engagement_id) -> int`; `services.initiatives.create_initiative(db, *, user, engagement, data)`, `services.initiatives.update_initiative(db, *, user, initiative, data)`; `services.findings.convert_finding(db, *, user, finding) -> Initiative` que lanza `FindingAlreadyConverted`; rutas `GET|POST /api/engagements/{engagement_id}/initiatives`, `GET|PATCH /api/initiatives/{initiative_id}`, `POST /api/findings/{finding_id}/convert`.

- [ ] **Step 1: Escribir tests (fallan)**

`tests/test_initiatives.py`:

```python
from tests.factories import login

INITIATIVE = {"name": "Automatización de conciliación", "objective": "Eliminar el cierre manual", "area": "Operaciones", "priority": "High"}
FINDING = {"title": "Conciliación manual diaria", "description": "Depende de Excel.", "area": "Operaciones", "impact": "High", "recommendation": "Automatizar."}


def test_syner_creates_and_updates_initiative(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/initiatives", headers=admin, json=INITIATIVE)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] == "Discovery"
    assert body["progress_pct"] == 0
    updated = client.patch(f"/api/initiatives/{body['id']}", headers=admin, json={"status": "Design", "progress_pct": 20})
    assert updated.status_code == 200
    assert updated.json()["status"] == "Design"
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["summary"] == 'Syner Admin updated Initiative "Automatización de conciliación" from Discovery to Design'


def test_client_roles_cannot_write_initiatives(client, world):
    for email in ("exec@a.example", "collab@a.example"):
        assert client.post(f"/api/engagements/{world.eng_a.id}/initiatives", headers=login(client, email), json=INITIATIVE).status_code == 403


def test_initiatives_isolated_by_organization(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/initiatives", headers=admin, json=INITIATIVE).json()
    assert client.get(f"/api/initiatives/{created['id']}", headers=login(client, "exec@b.example")).status_code == 404
    listing = client.get(f"/api/engagements/{world.eng_a.id}/initiatives", headers=login(client, "exec@a.example")).json()
    assert listing["total"] == 1


def test_progress_out_of_range_is_422(client, world):
    admin = login(client, "admin@syner.example")
    assert client.post(f"/api/engagements/{world.eng_a.id}/initiatives", headers=admin, json={**INITIATIVE, "progress_pct": 120}).status_code == 422


def test_explicit_null_rules_on_update(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/initiatives", headers=admin, json={**INITIATIVE, "target_date": "2026-12-01"}).json()
    assert client.patch(f"/api/initiatives/{created['id']}", headers=admin, json={"name": None}).status_code == 422
    cleared = client.patch(f"/api/initiatives/{created['id']}", headers=admin, json={"target_date": None})
    assert cleared.status_code == 200 and cleared.json()["target_date"] is None


def test_convert_finding_creates_initiative_once(client, world):
    admin = login(client, "admin@syner.example")
    finding = client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, json=FINDING).json()
    response = client.post(f"/api/findings/{finding['id']}/convert", headers=admin)
    assert response.status_code == 201, response.text
    initiative = response.json()
    assert initiative["name"] == "Conciliación manual diaria"
    assert initiative["objective"] == "Automatizar."
    assert initiative["area"] == "Operaciones"
    assert initiative["priority"] == "High"
    assert initiative["status"] == "Discovery"
    refreshed = client.get(f"/api/findings/{finding['id']}", headers=admin).json()
    assert refreshed["status"] == "Converted to Initiative"
    assert refreshed["initiative_id"] == initiative["id"]
    assert client.post(f"/api/findings/{finding['id']}/convert", headers=admin).status_code == 409
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["action"] == "converted"
    assert activity["summary"] == 'Syner Admin converted Finding "Conciliación manual diaria" into Initiative "Conciliación manual diaria"'


def test_only_syner_can_convert(client, world):
    admin = login(client, "admin@syner.example")
    finding = client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, json=FINDING).json()
    assert client.post(f"/api/findings/{finding['id']}/convert", headers=login(client, "exec@a.example")).status_code == 403
```

- [ ] **Step 2: Correr para verificar que fallan**

Run: `.venv/bin/pytest tests/test_initiatives.py -v`
Expected: FAIL con 404 en `/api/engagements/{id}/initiatives`.

- [ ] **Step 3: Escribir model, schema, crud, service y router; añadir `initiative_id` a Finding**

`app/models/initiative.py`:

```python
import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import EngagementScopedMixin, db_enum
from app.models.enums import InitiativeStatus, Level


class Initiative(EngagementScopedMixin, Base):
    __tablename__ = "initiatives"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    objective: Mapped[str] = mapped_column(Text, default="", nullable=False)
    expected_outcome: Mapped[str] = mapped_column(Text, default="", nullable=False)
    hito_owner: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    syner_owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    area: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    priority: Mapped[Level] = mapped_column(db_enum(Level, "initiative_priority"), default=Level.MEDIUM, nullable=False)
    status: Mapped[InitiativeStatus] = mapped_column(
        db_enum(InitiativeStatus, "initiative_status"), default=InitiativeStatus.DISCOVERY, nullable=False
    )
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    progress_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expected_impact: Mapped[str] = mapped_column(Text, default="", nullable=False)
    kpis: Mapped[str] = mapped_column(Text, default="", nullable=False)
    risks: Mapped[str] = mapped_column(Text, default="", nullable=False)
    dependencies: Mapped[str] = mapped_column(Text, default="", nullable=False)
```

En `app/models/finding.py` agregar al final de la clase:

```python
    initiative_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("initiatives.id"), index=True, nullable=True)
```

En `app/models/__init__.py`, importar `Initiative` ANTES que `Finding` (el FK lo requiere al crear tablas) y añadirlo a `__all__`:

```python
from app.models.activity import Activity
from app.models.engagement import Engagement
from app.models.initiative import Initiative
from app.models.finding import Finding
from app.models.organization import Organization
from app.models.user import User

__all__ = ["Activity", "Engagement", "Finding", "Initiative", "Organization", "User"]
```

`app/schemas/initiative.py`:

```python
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import InitiativeStatus, Level


class InitiativeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10000)
    objective: str = Field(default="", max_length=10000)
    expected_outcome: str = Field(default="", max_length=10000)
    hito_owner: str = Field(default="", max_length=200)
    syner_owner_id: uuid.UUID | None = None
    area: str = Field(default="", max_length=120)
    priority: Level = Level.MEDIUM
    status: InitiativeStatus = InitiativeStatus.DISCOVERY
    start_date: date | None = None
    target_date: date | None = None
    progress_pct: int = Field(default=0, ge=0, le=100)
    expected_impact: str = Field(default="", max_length=10000)
    kpis: str = Field(default="", max_length=10000)
    risks: str = Field(default="", max_length=10000)
    dependencies: str = Field(default="", max_length=10000)


class InitiativeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    objective: str | None = Field(default=None, max_length=10000)
    expected_outcome: str | None = Field(default=None, max_length=10000)
    hito_owner: str | None = Field(default=None, max_length=200)
    syner_owner_id: uuid.UUID | None = None
    area: str | None = Field(default=None, max_length=120)
    priority: Level | None = None
    status: InitiativeStatus | None = None
    start_date: date | None = None
    target_date: date | None = None
    progress_pct: int | None = Field(default=None, ge=0, le=100)
    expected_impact: str | None = Field(default=None, max_length=10000)
    kpis: str | None = Field(default=None, max_length=10000)
    risks: str | None = Field(default=None, max_length=10000)
    dependencies: str | None = Field(default=None, max_length=10000)


class InitiativeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    engagement_id: uuid.UUID
    name: str
    description: str
    objective: str
    expected_outcome: str
    hito_owner: str
    syner_owner_id: uuid.UUID | None
    area: str
    priority: Level
    status: InitiativeStatus
    start_date: date | None
    target_date: date | None
    progress_pct: int
    expected_impact: str
    kpis: str
    risks: str
    dependencies: str
    created_at: datetime
    updated_at: datetime
```

`app/crud/initiatives.py`:

```python
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import InitiativeStatus
from app.models.initiative import Initiative

INACTIVE = (InitiativeStatus.COMPLETED, InitiativeStatus.ON_HOLD)


def list_for_engagement(
    db: Session, engagement_id: uuid.UUID, *, status: InitiativeStatus | None = None, limit: int = 50, offset: int = 0
) -> tuple[list[Initiative], int]:
    query = select(Initiative).where(Initiative.engagement_id == engagement_id)
    if status:
        query = query.where(Initiative.status == status)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Initiative.created_at.desc()).limit(limit).offset(offset)))
    return items, total


def active(db: Session, engagement_id: uuid.UUID) -> list[Initiative]:
    query = (
        select(Initiative)
        .where(Initiative.engagement_id == engagement_id)
        .where(Initiative.status.not_in(INACTIVE))
        .order_by(Initiative.priority.desc(), Initiative.target_date.nulls_last())
    )
    return list(db.scalars(query))


def count_active(db: Session, engagement_id: uuid.UUID) -> int:
    query = (
        select(func.count()).select_from(Initiative)
        .where(Initiative.engagement_id == engagement_id)
        .where(Initiative.status.not_in(INACTIVE))
    )
    return db.scalar(query) or 0
```

`app/services/initiatives.py`:

```python
from sqlalchemy.orm import Session

from app.models.engagement import Engagement
from app.models.enums import ActivityAction
from app.models.initiative import Initiative
from app.models.user import User
from app.schemas.common import updates
from app.schemas.initiative import InitiativeCreate, InitiativeUpdate
from app.services.activity import diff_changes, log_activity


def create_initiative(db: Session, *, user: User, engagement: Engagement, data: InitiativeCreate) -> Initiative:
    initiative = Initiative(
        organization_id=engagement.organization_id, engagement_id=engagement.id, created_by=user.id, **data.model_dump()
    )
    db.add(initiative)
    db.flush()
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="initiative",
        entity_id=initiative.id, summary=f'{user.full_name} created Initiative "{initiative.name}"',
    )
    db.commit()
    db.refresh(initiative)
    return initiative


def update_initiative(db: Session, *, user: User, initiative: Initiative, data: InitiativeUpdate) -> Initiative:
    payload = updates(data, nullable={"syner_owner_id", "start_date", "target_date"})
    changes = diff_changes(initiative, payload)
    if not changes:
        return initiative
    for field, value in payload.items():
        setattr(initiative, field, value)
    engagement = db.get(Engagement, initiative.engagement_id)
    status_change = next((c for c in changes if c["field"] == "status"), None)
    if status_change:
        action = ActivityAction.STATUS_CHANGED
        summary = f'{user.full_name} updated Initiative "{initiative.name}" from {status_change["before"]} to {status_change["after"]}'
    else:
        action = ActivityAction.UPDATED
        summary = f'{user.full_name} updated Initiative "{initiative.name}"'
    log_activity(
        db, user=user, engagement=engagement, action=action, entity_type="initiative",
        entity_id=initiative.id, summary=summary, changes=changes,
    )
    db.commit()
    db.refresh(initiative)
    return initiative
```

Agregar al final de `app/services/findings.py`:

```python
from app.models.enums import FindingStatus, InitiativeStatus  # noqa: E402
from app.models.initiative import Initiative  # noqa: E402


class FindingAlreadyConverted(Exception):
    pass


def convert_finding(db: Session, *, user: User, finding: Finding) -> Initiative:
    if finding.initiative_id is not None:
        raise FindingAlreadyConverted
    engagement = db.get(Engagement, finding.engagement_id)
    initiative = Initiative(
        organization_id=engagement.organization_id,
        engagement_id=engagement.id,
        created_by=user.id,
        name=finding.title,
        description=finding.description,
        objective=finding.recommendation,
        area=finding.area,
        priority=finding.impact,
        status=InitiativeStatus.DISCOVERY,
    )
    db.add(initiative)
    db.flush()
    before_status = finding.status.value
    finding.initiative_id = initiative.id
    finding.status = FindingStatus.CONVERTED
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.CONVERTED, entity_type="finding",
        entity_id=finding.id,
        summary=f'{user.full_name} converted Finding "{finding.title}" into Initiative "{initiative.name}"',
        changes=[
            {"field": "status", "before": before_status, "after": FindingStatus.CONVERTED.value},
            {"field": "initiative_id", "before": None, "after": str(initiative.id)},
        ],
    )
    db.commit()
    db.refresh(initiative)
    return initiative
```

(Mover esos dos imports al bloque de imports superior del archivo; los `noqa` solo indican dónde van si se pega al final.)

`app/routers/initiatives.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import initiatives as initiatives_crud
from app.database import get_db
from app.dependencies import get_engagement, require_roles, scoped
from app.models.engagement import Engagement
from app.models.enums import InitiativeStatus, Role
from app.models.initiative import Initiative
from app.models.user import User
from app.schemas.common import Page, Pagination, pagination_params
from app.schemas.initiative import InitiativeCreate, InitiativeRead, InitiativeUpdate
from app.services import initiatives as initiatives_service

router = APIRouter(tags=["initiatives"])
syner_only = Depends(require_roles(Role.SYNER_ADMIN))
scoped_initiative = Depends(scoped(Initiative, "initiative_id"))


@router.get("/engagements/{engagement_id}/initiatives", response_model=Page[InitiativeRead])
def list_initiatives(
    engagement: Engagement = Depends(get_engagement),
    status: InitiativeStatus | None = None,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = initiatives_crud.list_for_engagement(
        db, engagement.id, status=status, limit=pagination.limit, offset=pagination.offset
    )
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/initiatives", response_model=InitiativeRead, status_code=201)
def create_initiative(
    data: InitiativeCreate,
    user: User = syner_only,
    engagement: Engagement = Depends(get_engagement),
    db: Session = Depends(get_db),
):
    return initiatives_service.create_initiative(db, user=user, engagement=engagement, data=data)


@router.get("/initiatives/{initiative_id}", response_model=InitiativeRead)
def read_initiative(initiative: Initiative = scoped_initiative):
    return initiative


@router.patch("/initiatives/{initiative_id}", response_model=InitiativeRead)
def update_initiative(
    data: InitiativeUpdate,
    user: User = syner_only,
    initiative: Initiative = scoped_initiative,
    db: Session = Depends(get_db),
):
    return initiatives_service.update_initiative(db, user=user, initiative=initiative, data=data)
```

Agregar en `app/routers/findings.py` (imports: `HTTPException`, `InitiativeRead`, `FindingAlreadyConverted`):

```python
@router.post("/findings/{finding_id}/convert", response_model=InitiativeRead, status_code=201)
def convert_finding(
    user: User = syner_only,
    finding: Finding = scoped_finding,
    db: Session = Depends(get_db),
):
    try:
        return findings_service.convert_finding(db, user=user, finding=finding)
    except findings_service.FindingAlreadyConverted:
        raise HTTPException(status_code=409, detail="El finding ya fue convertido en initiative")
```

En `app/main.py` importar `initiatives` e incluir `app.include_router(initiatives.router, prefix="/api")`.

- [ ] **Step 4: Correr los tests**

Run: `.venv/bin/pytest tests -v`
Expected: PASS (42 passed).

- [ ] **Step 5: Commit**

```bash
git add app tests
git commit -m "feat: módulo initiatives y conversión finding → initiative sin duplicar información"
```

---

### Task 8: Actions, "My Actions" y detalle de Initiative

**Files:**
- Create: `app/models/action.py`, `app/schemas/action.py`, `app/crud/actions.py`, `app/services/actions.py`, `app/routers/actions.py`
- Modify: `app/models/__init__.py`, `app/schemas/initiative.py`, `app/routers/initiatives.py`, `app/main.py`
- Test: `tests/test_actions.py`

**Interfaces:**
- Consumes: Tasks 5–7.
- Produces: modelo `Action`; `ActionCreate`, `ActionUpdate`, `ActionRead`; `crud.actions.list_for_engagement(db, engagement_id, *, status=None, initiative_id=None, owner_user_id=None, limit, offset)`, `crud.actions.count_open(db, engagement_id) -> int`, `crud.actions.next_open(db, engagement_id, limit=5)`, `crud.actions.list_by_initiative(db, initiative_id)`; `services.actions.create_action`, `services.actions.update_action`; `InitiativeDetail(initiative, findings, actions, activity)`; rutas `GET|POST /api/engagements/{engagement_id}/actions`, `PATCH /api/actions/{action_id}`, `GET /api/initiatives/{initiative_id}/detail`.

- [ ] **Step 1: Escribir tests (fallan)**

`tests/test_actions.py`:

```python
from tests.factories import login

ACTION = {"title": "Levantar inventario de hojas de cálculo", "organization_side": "CLIENT", "priority": "High", "due_date": "2026-10-30"}


def _initiative(client, world):
    admin = login(client, "admin@syner.example")
    return admin, client.post(f"/api/engagements/{world.eng_a.id}/initiatives", headers=admin, json={"name": "Automatización"}).json()


def test_syner_creates_action_linked_to_initiative_and_owner(client, world):
    admin, initiative = _initiative(client, world)
    payload = {**ACTION, "initiative_id": initiative["id"], "owner_user_id": str(world.collab_a.id)}
    response = client.post(f"/api/engagements/{world.eng_a.id}/actions", headers=admin, json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "Open"
    assert body["owner_name"] == "Collab A"
    assert body["initiative_id"] == initiative["id"]


def test_client_roles_cannot_create_actions(client, world):
    for email in ("exec@a.example", "collab@a.example"):
        assert client.post(f"/api/engagements/{world.eng_a.id}/actions", headers=login(client, email), json=ACTION).status_code == 403


def test_collaborator_updates_only_own_actions_and_only_status_evidence(client, world):
    admin = login(client, "admin@syner.example")
    mine = client.post(f"/api/engagements/{world.eng_a.id}/actions", headers=admin, json={**ACTION, "owner_user_id": str(world.collab_a.id)}).json()
    other = client.post(f"/api/engagements/{world.eng_a.id}/actions", headers=admin, json={**ACTION, "title": "Otra"}).json()
    collab = login(client, "collab@a.example")
    response = client.patch(f"/api/actions/{mine['id']}", headers=collab, json={"status": "In Progress", "evidence": "Inventario iniciado", "title": "Hackeado"})
    assert response.status_code == 200
    assert response.json()["status"] == "In Progress"
    assert response.json()["evidence"] == "Inventario iniciado"
    assert response.json()["title"] == ACTION["title"]
    assert client.patch(f"/api/actions/{other['id']}", headers=collab, json={"status": "Completed"}).status_code == 403
    assert client.patch(f"/api/actions/{mine['id']}", headers=login(client, "exec@a.example"), json={"status": "Completed"}).status_code == 403


def test_my_actions_filter(client, world):
    admin = login(client, "admin@syner.example")
    client.post(f"/api/engagements/{world.eng_a.id}/actions", headers=admin, json={**ACTION, "owner_user_id": str(world.collab_a.id)})
    client.post(f"/api/engagements/{world.eng_a.id}/actions", headers=admin, json={**ACTION, "title": "Otra"})
    collab = login(client, "collab@a.example")
    assert client.get(f"/api/engagements/{world.eng_a.id}/actions", headers=collab).json()["total"] == 2
    mine = client.get(f"/api/engagements/{world.eng_a.id}/actions", headers=collab, params={"mine": "true"}).json()
    assert mine["total"] == 1 and mine["items"][0]["owner_user_id"] == str(world.collab_a.id)


def test_actions_isolated_by_organization(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/actions", headers=admin, json=ACTION).json()
    assert client.patch(f"/api/actions/{created['id']}", headers=login(client, "collab@b.example"), json={"status": "Completed"}).status_code == 404
    assert client.get(f"/api/engagements/{world.eng_a.id}/actions", headers=login(client, "exec@b.example")).status_code == 404


def test_explicit_null_rules_on_update(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/actions", headers=admin, json=ACTION).json()
    assert client.patch(f"/api/actions/{created['id']}", headers=admin, json={"status": None}).status_code == 422
    cleared = client.patch(f"/api/actions/{created['id']}", headers=admin, json={"due_date": None})
    assert cleared.status_code == 200 and cleared.json()["due_date"] is None


def test_status_change_logs_activity(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/actions", headers=admin, json=ACTION).json()
    client.patch(f"/api/actions/{created['id']}", headers=admin, json={"status": "Blocked"})
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["summary"] == f'Syner Admin updated Action "{ACTION["title"]}" from Open to Blocked'


def test_initiative_detail_aggregates_related_entities(client, world):
    admin, initiative = _initiative(client, world)
    finding = client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, json={"title": "Hallazgo origen"}).json()
    converted = client.post(f"/api/findings/{finding['id']}/convert", headers=admin).json()
    client.post(f"/api/engagements/{world.eng_a.id}/actions", headers=admin, json={**ACTION, "initiative_id": converted["id"]})
    detail = client.get(f"/api/initiatives/{converted['id']}/detail", headers=login(client, "exec@a.example"))
    assert detail.status_code == 200
    body = detail.json()
    assert body["initiative"]["id"] == converted["id"]
    assert [f["id"] for f in body["findings"]] == [finding["id"]]
    assert len(body["actions"]) == 1
    assert any(a["entity_id"] == converted["id"] or a["entity_id"] == finding["id"] for a in body["activity"])
    assert client.get(f"/api/initiatives/{initiative['id']}/detail", headers=login(client, "exec@b.example")).status_code == 404
```

- [ ] **Step 2: Correr para verificar que fallan**

Run: `.venv/bin/pytest tests/test_actions.py -v`
Expected: FAIL con 404 en `/api/engagements/{id}/actions`.

- [ ] **Step 3: Escribir model, schema, crud, service, router y detalle**

`app/models/action.py`:

```python
import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import EngagementScopedMixin, db_enum
from app.models.enums import ActionStatus, Level, OrganizationSide


class Action(EngagementScopedMixin, Base):
    __tablename__ = "actions"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
    owner_name: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    organization_side: Mapped[OrganizationSide] = mapped_column(
        db_enum(OrganizationSide, "organization_side"), default=OrganizationSide.CLIENT, nullable=False
    )
    initiative_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("initiatives.id"), index=True, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    priority: Mapped[Level] = mapped_column(db_enum(Level, "action_priority"), default=Level.MEDIUM, nullable=False)
    status: Mapped[ActionStatus] = mapped_column(db_enum(ActionStatus, "action_status"), default=ActionStatus.OPEN, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, default="", nullable=False)
```

Añadir `from app.models.action import Action` y `"Action"` en `app/models/__init__.py` (después de `Initiative`).

`app/schemas/action.py`:

```python
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ActionStatus, Level, OrganizationSide


class ActionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10000)
    owner_user_id: uuid.UUID | None = None
    owner_name: str = Field(default="", max_length=200)
    organization_side: OrganizationSide = OrganizationSide.CLIENT
    initiative_id: uuid.UUID | None = None
    due_date: date | None = None
    priority: Level = Level.MEDIUM
    status: ActionStatus = ActionStatus.OPEN
    evidence: str = Field(default="", max_length=10000)


class ActionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    owner_user_id: uuid.UUID | None = None
    owner_name: str | None = Field(default=None, max_length=200)
    organization_side: OrganizationSide | None = None
    initiative_id: uuid.UUID | None = None
    due_date: date | None = None
    priority: Level | None = None
    status: ActionStatus | None = None
    evidence: str | None = Field(default=None, max_length=10000)


class ActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    engagement_id: uuid.UUID
    title: str
    description: str
    owner_user_id: uuid.UUID | None
    owner_name: str
    organization_side: OrganizationSide
    initiative_id: uuid.UUID | None
    due_date: date | None
    priority: Level
    status: ActionStatus
    evidence: str
    created_at: datetime
    updated_at: datetime
```

`app/crud/actions.py`:

```python
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.action import Action
from app.models.enums import ActionStatus

OPEN_STATUSES = (ActionStatus.OPEN, ActionStatus.IN_PROGRESS, ActionStatus.BLOCKED)


def list_for_engagement(
    db: Session, engagement_id: uuid.UUID, *, status: ActionStatus | None = None,
    initiative_id: uuid.UUID | None = None, owner_user_id: uuid.UUID | None = None,
    limit: int = 50, offset: int = 0,
) -> tuple[list[Action], int]:
    query = select(Action).where(Action.engagement_id == engagement_id)
    if status:
        query = query.where(Action.status == status)
    if initiative_id:
        query = query.where(Action.initiative_id == initiative_id)
    if owner_user_id:
        query = query.where(Action.owner_user_id == owner_user_id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Action.due_date.nulls_last(), Action.created_at.desc()).limit(limit).offset(offset)))
    return items, total


def count_open(db: Session, engagement_id: uuid.UUID) -> int:
    query = select(func.count()).select_from(Action).where(Action.engagement_id == engagement_id).where(Action.status.in_(OPEN_STATUSES))
    return db.scalar(query) or 0


def next_open(db: Session, engagement_id: uuid.UUID, limit: int = 5) -> list[Action]:
    query = (
        select(Action).where(Action.engagement_id == engagement_id).where(Action.status.in_(OPEN_STATUSES))
        .order_by(Action.due_date.nulls_last(), Action.priority.desc()).limit(limit)
    )
    return list(db.scalars(query))


def list_by_initiative(db: Session, initiative_id: uuid.UUID) -> list[Action]:
    return list(db.scalars(select(Action).where(Action.initiative_id == initiative_id).order_by(Action.due_date.nulls_last())))
```

`app/services/actions.py`:

```python
from sqlalchemy.orm import Session

from app.models.action import Action
from app.models.engagement import Engagement
from app.models.enums import ActivityAction
from app.models.user import User
from app.schemas.action import ActionCreate, ActionUpdate
from app.schemas.common import updates
from app.services.activity import diff_changes, log_activity


def _resolve_owner_name(db: Session, payload: dict) -> None:
    owner_id = payload.get("owner_user_id")
    if owner_id and not payload.get("owner_name"):
        owner = db.get(User, owner_id)
        if owner is not None:
            payload["owner_name"] = owner.full_name


def create_action(db: Session, *, user: User, engagement: Engagement, data: ActionCreate) -> Action:
    payload = data.model_dump()
    _resolve_owner_name(db, payload)
    action = Action(organization_id=engagement.organization_id, engagement_id=engagement.id, created_by=user.id, **payload)
    db.add(action)
    db.flush()
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="action",
        entity_id=action.id, summary=f'{user.full_name} created Action "{action.title}"',
    )
    db.commit()
    db.refresh(action)
    return action


def update_action(db: Session, *, user: User, action: Action, data: ActionUpdate) -> Action:
    payload = updates(data, nullable={"owner_user_id", "initiative_id", "due_date"})
    _resolve_owner_name(db, payload)
    changes = diff_changes(action, payload)
    if not changes:
        return action
    for field, value in payload.items():
        setattr(action, field, value)
    engagement = db.get(Engagement, action.engagement_id)
    status_change = next((c for c in changes if c["field"] == "status"), None)
    if status_change:
        activity_action = ActivityAction.STATUS_CHANGED
        summary = f'{user.full_name} updated Action "{action.title}" from {status_change["before"]} to {status_change["after"]}'
    else:
        activity_action = ActivityAction.UPDATED
        summary = f'{user.full_name} updated Action "{action.title}"'
    log_activity(
        db, user=user, engagement=engagement, action=activity_action, entity_type="action",
        entity_id=action.id, summary=summary, changes=changes,
    )
    db.commit()
    db.refresh(action)
    return action
```

`app/routers/actions.py`:

```python
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import actions as actions_crud
from app.database import get_db
from app.dependencies import get_current_user, get_engagement, require_roles, scoped
from app.models.action import Action
from app.models.engagement import Engagement
from app.models.enums import ActionStatus, Role
from app.models.user import User
from app.schemas.action import ActionCreate, ActionRead, ActionUpdate
from app.schemas.common import Page, Pagination, pagination_params
from app.services import actions as actions_service

router = APIRouter(tags=["actions"])
syner_only = Depends(require_roles(Role.SYNER_ADMIN))
scoped_action = Depends(scoped(Action, "action_id"))


@router.get("/engagements/{engagement_id}/actions", response_model=Page[ActionRead])
def list_actions(
    engagement: Engagement = Depends(get_engagement),
    user: User = Depends(get_current_user),
    status: ActionStatus | None = None,
    initiative_id: uuid.UUID | None = None,
    owner_user_id: uuid.UUID | None = None,
    mine: bool = False,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    if mine:
        owner_user_id = user.id
    items, total = actions_crud.list_for_engagement(
        db, engagement.id, status=status, initiative_id=initiative_id, owner_user_id=owner_user_id,
        limit=pagination.limit, offset=pagination.offset,
    )
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/actions", response_model=ActionRead, status_code=201)
def create_action(
    data: ActionCreate,
    user: User = syner_only,
    engagement: Engagement = Depends(get_engagement),
    db: Session = Depends(get_db),
):
    return actions_service.create_action(db, user=user, engagement=engagement, data=data)


@router.patch("/actions/{action_id}", response_model=ActionRead)
def update_action(
    data: ActionUpdate,
    action: Action = scoped_action,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role == Role.SYNER_ADMIN:
        payload = data
    elif user.role == Role.HITO_COLLABORATOR and action.owner_user_id == user.id:
        payload = ActionUpdate(**data.model_dump(include={"status", "evidence"}, exclude_unset=True))
    else:
        raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")
    return actions_service.update_action(db, user=user, action=action, data=payload)
```

Agregar a `app/schemas/initiative.py` (imports: `ActivityRead`, `ActionRead`, `FindingRead`):

```python
from app.schemas.action import ActionRead
from app.schemas.activity import ActivityRead
from app.schemas.finding import FindingRead


class InitiativeDetail(BaseModel):
    initiative: InitiativeRead
    findings: list[FindingRead]
    actions: list[ActionRead]
    activity: list[ActivityRead]
```

Agregar a `app/routers/initiatives.py` (imports: `InitiativeDetail`, `ActionRead`, `ActivityRead`, `FindingRead`, `actions_crud`, `activities_crud`, `findings_crud`):

```python
@router.get("/initiatives/{initiative_id}/detail", response_model=InitiativeDetail)
def initiative_detail(initiative: Initiative = scoped_initiative, db: Session = Depends(get_db)):
    findings = findings_crud.list_by_initiative(db, initiative.id)
    actions = actions_crud.list_by_initiative(db, initiative.id)
    own_activity, _ = activities_crud.list_for_engagement(db, initiative.engagement_id, entity_type="initiative", entity_id=initiative.id, limit=20)
    finding_activity = []
    for finding in findings:
        items, _ = activities_crud.list_for_engagement(db, initiative.engagement_id, entity_type="finding", entity_id=finding.id, limit=5)
        finding_activity.extend(items)
    activity = sorted(own_activity + finding_activity, key=lambda a: a.created_at, reverse=True)[:20]
    return InitiativeDetail(
        initiative=InitiativeRead.model_validate(initiative),
        findings=[FindingRead.model_validate(f) for f in findings],
        actions=[ActionRead.model_validate(a) for a in actions],
        activity=[ActivityRead.model_validate(a) for a in activity],
    )
```

En `app/main.py` importar `actions` e incluir `app.include_router(actions.router, prefix="/api")`.

- [ ] **Step 4: Correr los tests**

Run: `.venv/bin/pytest tests -v`
Expected: PASS (53 passed).

- [ ] **Step 5: Commit**

```bash
git add app tests
git commit -m "feat: módulo actions con My Actions, regla de colaborador y detalle de initiative"
```

---

### Task 9: Dashboard ejecutivo (`GET /api/engagements/{id}/dashboard`)

**Files:**
- Create: `app/schemas/dashboard.py`, `app/services/dashboard.py`, `app/routers/dashboard.py`
- Modify: `app/main.py`
- Test: `tests/test_dashboard.py`

**Interfaces:**
- Consumes: `crud.initiatives.active/count_active`, `crud.actions.count_open/next_open`, `crud.findings.key_findings/count_critical_open`, `crud.activities.recent`, `EngagementRead`, `RoadmapPhase`.
- Produces: `DashboardRead` con `engagement`, `tiles`, `active_initiatives`, `key_findings`, `next_actions`, `recent_activity`, `roadmap`, `decisions_required`, `next_milestones`; `services.dashboard.build_dashboard(db, engagement) -> DashboardRead`. El plan 2 reemplaza `decisions_required: list[dict]` y `next_milestones: list[dict]` por schemas tipados y llena `roadmap[*].milestones`.

- [ ] **Step 1: Escribir tests (fallan)**

`tests/test_dashboard.py`:

```python
from tests.factories import login


def test_dashboard_tiles_and_sections(client, world):
    admin = login(client, "admin@syner.example")
    eng = world.eng_a.id
    client.patch(f"/api/engagements/{eng}", headers=admin, json={"health": "Attention", "progress_pct": 35, "executive_summary": "Arranque."})
    client.post(f"/api/engagements/{eng}/findings", headers=admin, json={"title": "Crítico", "impact": "Critical"})
    client.post(f"/api/engagements/{eng}/findings", headers=admin, json={"title": "Alto", "impact": "High"})
    client.post(f"/api/engagements/{eng}/findings", headers=admin, json={"title": "Bajo", "impact": "Low"})
    active = client.post(f"/api/engagements/{eng}/initiatives", headers=admin, json={"name": "Activa", "status": "Execution"}).json()
    client.post(f"/api/engagements/{eng}/initiatives", headers=admin, json={"name": "Pausada", "status": "On Hold"})
    client.post(f"/api/engagements/{eng}/actions", headers=admin, json={"title": "Abierta", "due_date": "2026-11-01", "initiative_id": active["id"]})
    client.post(f"/api/engagements/{eng}/actions", headers=admin, json={"title": "Hecha", "status": "Completed"})

    response = client.get(f"/api/engagements/{eng}/dashboard", headers=login(client, "exec@a.example"))
    assert response.status_code == 200
    body = response.json()
    assert body["engagement"]["executive_summary"] == "Arranque."
    assert body["tiles"] == {
        "health": "Attention", "progress_pct": 35, "active_initiatives": 1,
        "open_actions": 1, "decisions_required": 0, "critical_findings": 1,
    }
    assert [i["name"] for i in body["active_initiatives"]] == ["Activa"]
    assert {f["title"] for f in body["key_findings"]} == {"Crítico", "Alto"}
    assert [a["title"] for a in body["next_actions"]] == ["Abierta"]
    assert len(body["recent_activity"]) >= 7
    assert [p["phase"] for p in body["roadmap"]] == ["Discover", "Diagnose", "Design", "Prioritize", "Execute", "Measure"]
    assert body["decisions_required"] == []
    assert body["next_milestones"] == []


def test_dashboard_is_scoped(client, world):
    assert client.get(f"/api/engagements/{world.eng_a.id}/dashboard", headers=login(client, "collab@b.example")).status_code == 404
```

- [ ] **Step 2: Correr para verificar que fallan**

Run: `.venv/bin/pytest tests/test_dashboard.py -v`
Expected: FAIL con 404 en `/dashboard`.

- [ ] **Step 3: Escribir schema, service y router**

`app/schemas/dashboard.py`:

```python
from pydantic import BaseModel

from app.models.enums import Health
from app.schemas.action import ActionRead
from app.schemas.activity import ActivityRead
from app.schemas.engagement import EngagementRead
from app.schemas.finding import FindingRead
from app.schemas.initiative import InitiativeRead


class DashboardTiles(BaseModel):
    health: Health
    progress_pct: int
    active_initiatives: int
    open_actions: int
    decisions_required: int
    critical_findings: int


class RoadmapPhaseRead(BaseModel):
    phase: str
    milestones: list[dict] = []


class DashboardRead(BaseModel):
    engagement: EngagementRead
    tiles: DashboardTiles
    active_initiatives: list[InitiativeRead]
    key_findings: list[FindingRead]
    next_actions: list[ActionRead]
    recent_activity: list[ActivityRead]
    roadmap: list[RoadmapPhaseRead]
    decisions_required: list[dict]
    next_milestones: list[dict]
```

`app/services/dashboard.py`:

```python
from sqlalchemy.orm import Session

from app.crud import actions as actions_crud
from app.crud import activities as activities_crud
from app.crud import findings as findings_crud
from app.crud import initiatives as initiatives_crud
from app.models.engagement import Engagement
from app.models.enums import RoadmapPhase
from app.schemas.action import ActionRead
from app.schemas.activity import ActivityRead
from app.schemas.dashboard import DashboardRead, DashboardTiles, RoadmapPhaseRead
from app.schemas.engagement import EngagementRead
from app.schemas.finding import FindingRead
from app.schemas.initiative import InitiativeRead


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
        roadmap=[RoadmapPhaseRead(phase=phase.value) for phase in RoadmapPhase],
        decisions_required=[],
        next_milestones=[],
    )
```

`app/routers/dashboard.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_engagement
from app.models.engagement import Engagement
from app.schemas.dashboard import DashboardRead
from app.services.dashboard import build_dashboard

router = APIRouter(tags=["dashboard"])


@router.get("/engagements/{engagement_id}/dashboard", response_model=DashboardRead)
def dashboard(engagement: Engagement = Depends(get_engagement), db: Session = Depends(get_db)):
    return build_dashboard(db, engagement)
```

En `app/main.py` importar `dashboard` e incluir `app.include_router(dashboard.router, prefix="/api")`.

- [ ] **Step 4: Correr los tests**

Run: `.venv/bin/pytest tests -v`
Expected: PASS (55 passed).

- [ ] **Step 5: Commit**

```bash
git add app tests
git commit -m "feat: endpoint de dashboard ejecutivo con tiles y secciones"
```

---

### Task 10: Alembic, migración inicial, seed demo y README

**Files:**
- Create: `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`, `alembic/versions/<rev>_initial.py` (autogenerado), `app/seed.py`, `README.md`
- Test: `tests/test_seed.py`

**Interfaces:**
- Produces: `app.seed.seed(db) -> None` idempotente; comando `python -m app.seed`; `alembic upgrade head` reproducible.

- [ ] **Step 1: Escribir test del seed (falla)**

`tests/test_seed.py`:

```python
from sqlalchemy import func, select

from app.models.action import Action
from app.models.finding import Finding
from app.models.initiative import Initiative
from app.models.user import User
from app.seed import seed


def test_seed_is_idempotent_and_creates_demo_data(db, client):
    seed(db)
    seed(db)
    assert db.scalar(select(func.count()).select_from(User)) == 3
    assert db.scalar(select(func.count()).select_from(Finding)) == 5
    assert db.scalar(select(func.count()).select_from(Initiative)) == 4
    assert db.scalar(select(func.count()).select_from(Action)) == 8
    titles = list(db.scalars(select(Finding.title)))
    assert all(t.startswith("[Demo]") for t in titles)
    response = client.post("/api/auth/login", json={"email": "admin@syner.demo", "password": "syner-demo"})
    assert response.status_code == 200
```

- [ ] **Step 2: Correr para verificar que falla**

Run: `.venv/bin/pytest tests/test_seed.py -v`
Expected: FAIL con `ModuleNotFoundError: app.seed`.

- [ ] **Step 3: Escribir `app/seed.py`**

```python
"""Seed demo: python -m app.seed. Idempotente por slug/email. Todo el contenido es ficticio y lleva prefijo [Demo]."""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.database import SessionLocal
from app.models.engagement import Engagement
from app.models.enums import Health, Level, OrganizationKind, Role
from app.models.finding import Finding
from app.models.organization import Organization
from app.models.user import User
from app.schemas.action import ActionCreate
from app.schemas.finding import FindingCreate
from app.schemas.initiative import InitiativeCreate
from app.services import actions as actions_service
from app.services import findings as findings_service
from app.services import initiatives as initiatives_service


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


def seed(db: Session) -> None:
    settings = get_settings()
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

    if db.scalar(select(Finding).where(Finding.engagement_id == engagement.id)) is not None:
        return

    findings_data = [
        ("[Demo] Conciliación diaria dependiente de hojas de cálculo", "Quick Win", "Operaciones", Level.HIGH),
        ("[Demo] Reportes a clientes institucionales generados manualmente", "Opportunity", "Operaciones", Level.HIGH),
        ("[Demo] Sin inventario único de procesos críticos", "Gap", "Procesos", Level.MEDIUM),
        ("[Demo] Aprobaciones concentradas en pocas personas", "Risk", "Gobierno", Level.CRITICAL),
        ("[Demo] Datos de cartera replicados en varios sistemas", "Strategic Insight", "Datos", Level.HIGH),
    ]
    findings = []
    for title, ftype, area, impact in findings_data:
        findings.append(findings_service.create_finding(
            db, user=admin, engagement=engagement,
            data=FindingCreate(title=title, type=ftype, area=area, impact=impact, description="Contenido ficticio de demostración.", recommendation="Recomendación ficticia de demostración."),
        ))

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


if __name__ == "__main__":
    with SessionLocal() as session:
        seed(session)
    print("Seed completado.")
```

- [ ] **Step 4: Correr el test del seed**

Run: `.venv/bin/pytest tests -v`
Expected: PASS (53 passed).

- [ ] **Step 5: Inicializar Alembic y generar la migración inicial contra la base de desarrollo**

```bash
cd /mnt/d/Devs/HiTOxSyner
.venv/bin/alembic init alembic
```
Reemplazar `alembic/env.py` por:

```python
from alembic import context
from sqlalchemy import engine_from_config, pool

import app.models  # noqa: F401
from app.core.config import get_settings
from app.database import Base

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)
target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(config.get_section(config.config_ini_section), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```
En `alembic.ini` dejar `script_location = alembic` y borrar la línea `sqlalchemy.url = ...` (la pone `env.py`). Luego:

```bash
.venv/bin/alembic revision --autogenerate -m "initial"
.venv/bin/alembic upgrade head
.venv/bin/python -m app.seed
```
Expected: se crea `alembic/versions/*_initial.py` con las tablas `organizations`, `engagements`, `users`, `activities`, `findings`, `initiatives`, `actions` y los enums; `upgrade head` termina sin error; seed imprime `Seed completado.`. Abrir el archivo de migración y verificar que no contiene `op.drop_*` ni tablas inesperadas.

- [ ] **Step 6: Escribir README.md**

```markdown
# Syner × HiTO — Transformation Room

Workspace privado de advisory para el engagement de Grupo Syner con HiTO. API FastAPI + frontend React servidos desde un solo contenedor.

## Desarrollo local

1. `python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`
2. Copiar `.env.example` a `.env` y definir `DATABASE_URL`, `TEST_DATABASE_URL` y `JWT_SECRET` (Postgres obligatorio).
3. `alembic upgrade head`
4. `python -m app.seed` (usuarios demo: `admin@syner.demo`, `exec@hito.demo`, `collab@hito.demo`; passwords desde `SEED_*_PASSWORD`).
5. `uvicorn app.main:app --reload` → API en `http://localhost:8000/api`, docs en `/api/docs`.
6. Frontend: `cd frontend && npm install && npm run dev` → `http://localhost:5173` con proxy a `/api`.

## Tests

`pytest` usa `TEST_DATABASE_URL`, crea el esquema desde los modelos y trunca tablas entre tests.

## Build y deploy

- `cd frontend && npm run build` genera `frontend/dist`, que FastAPI sirve en `/`.
- Railway construye con el `Dockerfile`; el contenedor ejecuta `alembic upgrade head` y luego `uvicorn`.
- Variables en Railway: `DATABASE_URL`, `JWT_SECRET`, `ENVIRONMENT=production`, `SEED_*_PASSWORD` (solo si se corre el seed).
- Health: `GET /api/health`.
```

- [ ] **Step 7: Commit**

```bash
git add alembic.ini alembic app/seed.py tests/test_seed.py README.md
git commit -m "feat: migración inicial Alembic, seed demo idempotente y README"
```

---

### Task 11: Frontend scaffold, login, shell y stores

**Files:**
- Create: `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/tsconfig.node.json`, `frontend/index.html`, `frontend/tailwind.config.js`, `frontend/postcss.config.js`
- Create: `frontend/src/index.css`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/router.tsx`, `frontend/src/types.ts`
- Create: `frontend/src/api/client.ts`, `frontend/src/api/auth.ts`, `frontend/src/api/engagements.ts`
- Create: `frontend/src/stores/auth.ts`, `frontend/src/stores/engagement.ts`, `frontend/src/hooks/useResource.ts`
- Create: `frontend/src/lib/labels.ts`, `frontend/src/lib/roles.ts`, `frontend/src/lib/dates.ts`
- Create: `frontend/src/components/AppShell.tsx`, `Sidebar.tsx`, `Header.tsx`, `PageHeader.tsx`, `Tile.tsx`, `StatusBadge.tsx`, `DataTable.tsx`, `FormDrawer.tsx`, `EmptyState.tsx`, `Field.tsx`
- Create: `frontend/src/pages/LoginPage.tsx`, `frontend/src/pages/ComingSoonPage.tsx`

**Interfaces:**
- Produces: `api` (axios con `baseURL "/api"`, `withCredentials`), `errorMessage(err) -> string`; `useAuthStore` (`user`, `status`, `bootstrap`, `login`, `logout`); `useEngagementStore` (`engagements`, `current`, `loaded`, `load`, `select`, `refreshCurrent`); `useResource<T>(loader, deps)`; tipos en `types.ts`; componentes listados; `can(user, "write")`.

- [ ] **Step 1: Crear el proyecto y la configuración**

`frontend/package.json`:

```json
{
  "name": "hitoxsyner-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc --noEmit && vite build",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "axios": "^1.7.7",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.26.2",
    "recharts": "^2.12.7",
    "zustand": "^4.5.5"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.2",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.13",
    "typescript": "^5.6.2",
    "vite": "^5.4.8"
  }
}
```

`frontend/vite.config.ts`:

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://localhost:8000" } },
});
```

`frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "Bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
```

`frontend/tsconfig.node.json`:

```json
{
  "compilerOptions": { "composite": true, "skipLibCheck": true, "module": "ESNext", "moduleResolution": "Bundler", "allowSyntheticDefaultImports": true },
  "include": ["vite.config.ts"]
}
```

`frontend/index.html`:

```html
<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>SYNER × HiTO · Transformation Room</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
  </head>
  <body class="bg-white text-ink antialiased">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

`frontend/tailwind.config.js`:

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#111827",
        muted: "#6B7280",
        line: "#E5E7EB",
        canvas: "#F9FAFB",
        accent: "#0F766E",
        warn: "#B45309",
        danger: "#B91C1C",
      },
      fontFamily: { sans: ["Inter", "system-ui", "sans-serif"] },
    },
  },
  plugins: [],
};
```

`frontend/postcss.config.js`:

```js
export default { plugins: { tailwindcss: {}, autoprefixer: {} } };
```

`frontend/src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer components {
  .card { @apply rounded-md border border-line bg-white; }
  .btn { @apply inline-flex items-center gap-2 rounded-md border border-line bg-white px-3 py-1.5 text-sm font-medium text-ink hover:bg-canvas disabled:opacity-50; }
  .btn-primary { @apply border-ink bg-ink text-white hover:bg-gray-800; }
  .input { @apply w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-ink focus:border-ink focus:outline-none; }
  .label { @apply mb-1 block text-xs font-medium uppercase tracking-wide text-muted; }
}
```

Run:
```bash
cd /mnt/d/Devs/HiTOxSyner/frontend && npm install
```
Expected: `node_modules` creado y `package-lock.json` generado.

- [ ] **Step 2: Tipos, cliente API y stores**

`frontend/src/types.ts`:

```ts
export type Role = "SYNER_ADMIN" | "HITO_EXECUTIVE" | "HITO_COLLABORATOR";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  organization_id: string;
  organization_name: string;
  is_active: boolean;
}

export type Health = "On Track" | "Attention" | "At Risk";
export type Level = "Low" | "Medium" | "High" | "Critical";

export interface Engagement {
  id: string;
  organization_id: string;
  name: string;
  subtitle: string | null;
  status: "Active" | "Paused" | "Closed";
  health: Health;
  progress_pct: number;
  executive_summary: string;
  start_date: string | null;
  target_end_date: string | null;
}

export type FindingType = "Opportunity" | "Risk" | "Gap" | "Finding" | "Quick Win" | "Strategic Insight";
export type FindingStatus = "New" | "Under Analysis" | "Validated" | "Converted to Initiative" | "Accepted" | "Closed";

export interface Finding {
  id: string;
  engagement_id: string;
  title: string;
  description: string;
  context: string;
  type: FindingType;
  area: string;
  source: string;
  impact: Level;
  severity: Level;
  evidence: string;
  recommendation: string;
  syner_owner_id: string | null;
  found_on: string;
  status: FindingStatus;
  initiative_id: string | null;
  created_at: string;
  updated_at: string;
}

export type InitiativeStatus = "Discovery" | "Design" | "Validation" | "Execution" | "Monitoring" | "Completed" | "On Hold";

export interface Initiative {
  id: string;
  engagement_id: string;
  name: string;
  description: string;
  objective: string;
  expected_outcome: string;
  hito_owner: string;
  syner_owner_id: string | null;
  area: string;
  priority: Level;
  status: InitiativeStatus;
  start_date: string | null;
  target_date: string | null;
  progress_pct: number;
  expected_impact: string;
  kpis: string;
  risks: string;
  dependencies: string;
  created_at: string;
  updated_at: string;
}

export type ActionStatus = "Open" | "In Progress" | "Blocked" | "Completed" | "Cancelled";

export interface Action {
  id: string;
  engagement_id: string;
  title: string;
  description: string;
  owner_user_id: string | null;
  owner_name: string;
  organization_side: "SYNER" | "CLIENT";
  initiative_id: string | null;
  due_date: string | null;
  priority: Level;
  status: ActionStatus;
  evidence: string;
  created_at: string;
  updated_at: string;
}

export interface Activity {
  id: string;
  user_id: string | null;
  user_name: string;
  action: string;
  entity_type: string;
  entity_id: string;
  summary: string;
  changes: { field: string; before: unknown; after: unknown }[];
  created_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
}

export interface Dashboard {
  engagement: Engagement;
  tiles: {
    health: Health;
    progress_pct: number;
    active_initiatives: number;
    open_actions: number;
    decisions_required: number;
    critical_findings: number;
  };
  active_initiatives: Initiative[];
  key_findings: Finding[];
  next_actions: Action[];
  recent_activity: Activity[];
  roadmap: { phase: string; milestones: unknown[] }[];
  decisions_required: unknown[];
  next_milestones: unknown[];
}

export interface InitiativeDetail {
  initiative: Initiative;
  findings: Finding[];
  actions: Action[];
  activity: Activity[];
}
```

`frontend/src/api/client.ts`:

```ts
import axios from "axios";

export const api = axios.create({ baseURL: "/api", withCredentials: true });

let onUnauthorized: (() => void) | null = null;
export function setUnauthorizedHandler(handler: () => void) {
  onUnauthorized = handler;
}

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401 && onUnauthorized) onUnauthorized();
    return Promise.reject(error);
  },
);

export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (error.response?.status === 403) return "No tienes permisos para esta acción";
    if (error.response?.status === 422) return "Revisa los campos del formulario";
  }
  return "Ocurrió un error inesperado";
}
```

`frontend/src/api/auth.ts`:

```ts
import { api } from "./client";
import type { User } from "../types";

export const authApi = {
  login: (email: string, password: string) =>
    api.post<{ access_token: string; user: User }>("/auth/login", { email, password }).then((r) => r.data),
  logout: () => api.post("/auth/logout").then(() => undefined),
  me: () => api.get<User>("/auth/me").then((r) => r.data),
};
```

`frontend/src/api/engagements.ts`:

```ts
import { api } from "./client";
import type { Dashboard, Engagement } from "../types";

export const engagementsApi = {
  list: () => api.get<Engagement[]>("/engagements").then((r) => r.data),
  get: (id: string) => api.get<Engagement>(`/engagements/${id}`).then((r) => r.data),
  update: (id: string, data: Partial<Engagement>) => api.patch<Engagement>(`/engagements/${id}`, data).then((r) => r.data),
  dashboard: (id: string) => api.get<Dashboard>(`/engagements/${id}/dashboard`).then((r) => r.data),
};
```

`frontend/src/stores/auth.ts`:

```ts
import { create } from "zustand";
import { authApi } from "../api/auth";
import { setUnauthorizedHandler } from "../api/client";
import type { User } from "../types";

type Status = "unknown" | "anonymous" | "authenticated";

interface AuthState {
  user: User | null;
  status: Status;
  bootstrap: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  status: "unknown",
  async bootstrap() {
    try {
      const user = await authApi.me();
      set({ user, status: "authenticated" });
    } catch {
      set({ user: null, status: "anonymous" });
    }
  },
  async login(email, password) {
    const result = await authApi.login(email, password);
    set({ user: result.user, status: "authenticated" });
  },
  async logout() {
    await authApi.logout();
    set({ user: null, status: "anonymous" });
  },
}));

setUnauthorizedHandler(() => useAuthStore.setState({ user: null, status: "anonymous" }));
```

`frontend/src/stores/engagement.ts`:

```ts
import { create } from "zustand";
import { engagementsApi } from "../api/engagements";
import type { Engagement } from "../types";

const STORAGE_KEY = "tr.engagement";

interface EngagementState {
  engagements: Engagement[];
  current: Engagement | null;
  loaded: boolean;
  load: () => Promise<void>;
  select: (id: string) => void;
  refreshCurrent: () => Promise<void>;
}

function readSaved(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

export const useEngagementStore = create<EngagementState>((set, get) => ({
  engagements: [],
  current: null,
  loaded: false,
  async load() {
    const engagements = await engagementsApi.list();
    const saved = readSaved();
    const current = engagements.find((e) => e.id === saved) ?? engagements[0] ?? null;
    set({ engagements, current, loaded: true });
  },
  select(id) {
    const current = get().engagements.find((e) => e.id === id) ?? null;
    set({ current });
    try {
      localStorage.setItem(STORAGE_KEY, id);
    } catch {
      /* almacenamiento no disponible */
    }
  },
  async refreshCurrent() {
    const current = get().current;
    if (!current) return;
    const fresh = await engagementsApi.get(current.id);
    set({ current: fresh, engagements: get().engagements.map((e) => (e.id === fresh.id ? fresh : e)) });
  },
}));
```

`frontend/src/hooks/useResource.ts`:

```ts
import { useCallback, useEffect, useState } from "react";
import { errorMessage } from "../api/client";

export function useResource<T>(loader: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(() => {
    setLoading(true);
    setError(null);
    return loader()
      .then(setData)
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { data, loading, error, reload };
}
```

- [ ] **Step 3: Utilidades (labels, roles, dates)**

`frontend/src/lib/labels.ts`:

```ts
import type { Role } from "../types";

export const NAV_ITEMS = [
  { to: "/", label: "Overview", end: true },
  { to: "/findings", label: "Findings" },
  { to: "/initiatives", label: "Initiatives" },
  { to: "/roadmap", label: "Roadmap" },
  { to: "/actions", label: "Actions" },
  { to: "/decisions", label: "Decisions" },
  { to: "/meetings", label: "Meetings" },
  { to: "/documents", label: "Documents" },
  { to: "/lab", label: "Leadership Lab" },
];

export const ROLE_LABELS: Record<Role, string> = {
  SYNER_ADMIN: "Equipo Syner",
  HITO_EXECUTIVE: "Dirección",
  HITO_COLLABORATOR: "Colaborador",
};

export const FINDING_TYPES = ["Opportunity", "Risk", "Gap", "Finding", "Quick Win", "Strategic Insight"] as const;
export const FINDING_STATUSES = ["New", "Under Analysis", "Validated", "Converted to Initiative", "Accepted", "Closed"] as const;
export const INITIATIVE_STATUSES = ["Discovery", "Design", "Validation", "Execution", "Monitoring", "Completed", "On Hold"] as const;
export const ACTION_STATUSES = ["Open", "In Progress", "Blocked", "Completed", "Cancelled"] as const;
export const LEVELS = ["Low", "Medium", "High", "Critical"] as const;
export const HEALTHS = ["On Track", "Attention", "At Risk"] as const;
```

`frontend/src/lib/roles.ts`:

```ts
import type { User } from "../types";

export type Capability = "write" | "approveDecision" | "manageLab" | "viewLabSummary";

export function can(user: User | null, capability: Capability): boolean {
  if (!user) return false;
  switch (capability) {
    case "write":
    case "manageLab":
      return user.role === "SYNER_ADMIN";
    case "approveDecision":
    case "viewLabSummary":
      return user.role === "SYNER_ADMIN" || user.role === "HITO_EXECUTIVE";
  }
}
```

`frontend/src/lib/dates.ts`:

```ts
const dateFormatter = new Intl.DateTimeFormat("es-MX", { day: "2-digit", month: "short", year: "numeric" });
const dateTimeFormatter = new Intl.DateTimeFormat("es-MX", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  return dateFormatter.format(new Date(value.length === 10 ? `${value}T00:00:00` : value));
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  return dateTimeFormatter.format(new Date(value));
}
```

- [ ] **Step 4: Componentes del shell**

`frontend/src/components/Sidebar.tsx`:

```tsx
import { NavLink } from "react-router-dom";
import { NAV_ITEMS } from "../lib/labels";

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <aside className="flex h-full w-60 flex-col border-r border-line bg-white">
      <div className="border-b border-line px-5 py-4">
        <div className="text-xs font-semibold tracking-[0.2em] text-ink">SYNER × HiTO</div>
        <div className="mt-1 text-xs text-muted">Transformation Room</div>
      </div>
      <nav className="flex-1 space-y-0.5 px-3 py-3">
        {NAV_ITEMS.map((item) => (
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

`frontend/src/components/Header.tsx`:

```tsx
import { useNavigate } from "react-router-dom";
import { ROLE_LABELS } from "../lib/labels";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";

export function Header({ onMenu }: { onMenu: () => void }) {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const { engagements, current, select } = useEngagementStore();
  const navigate = useNavigate();

  return (
    <header className="flex h-14 items-center gap-3 border-b border-line bg-white px-4">
      <button className="btn lg:hidden" onClick={onMenu} aria-label="Abrir menú">☰</button>
      <select
        className="input max-w-xs"
        value={current?.id ?? ""}
        onChange={(e) => select(e.target.value)}
        aria-label="Engagement"
      >
        {engagements.map((e) => (
          <option key={e.id} value={e.id}>{e.name}</option>
        ))}
      </select>
      <input className="input hidden max-w-xs md:block" placeholder="Buscar (próximamente)" disabled title="Próximamente" />
      <div className="ml-auto flex items-center gap-3">
        <button className="btn" disabled title="Notificaciones (próximamente)" aria-label="Notificaciones">○</button>
        {user && (
          <div className="text-right leading-tight">
            <div className="text-sm font-medium">{user.full_name}</div>
            <div className="text-[11px] text-muted">{ROLE_LABELS[user.role]} · {user.organization_name}</div>
          </div>
        )}
        <button className="btn" onClick={() => logout().then(() => navigate("/login"))}>Salir</button>
      </div>
    </header>
  );
}
```

`frontend/src/components/AppShell.tsx`:

```tsx
import { useState } from "react";
import { Outlet } from "react-router-dom";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

export function AppShell() {
  const [open, setOpen] = useState(false);
  return (
    <div className="flex h-screen bg-canvas">
      <div className="hidden lg:block">
        <Sidebar />
      </div>
      {open && (
        <div className="fixed inset-0 z-40 flex lg:hidden">
          <Sidebar onNavigate={() => setOpen(false)} />
          <div className="flex-1 bg-black/20" onClick={() => setOpen(false)} />
        </div>
      )}
      <div className="flex min-w-0 flex-1 flex-col">
        <Header onMenu={() => setOpen(true)} />
        <main className="flex-1 overflow-y-auto px-4 py-6 md:px-8">
          <div className="mx-auto max-w-6xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
```

`frontend/src/components/PageHeader.tsx`:

```tsx
import type { ReactNode } from "react";

export function PageHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-muted">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
```

`frontend/src/components/Tile.tsx`:

```tsx
export function Tile({ label, value, tone = "default" }: { label: string; value: string | number; tone?: "default" | "ok" | "warn" | "danger" }) {
  const color = { default: "text-ink", ok: "text-accent", warn: "text-warn", danger: "text-danger" }[tone];
  return (
    <div className="card px-4 py-3">
      <div className="text-[11px] font-medium uppercase tracking-wide text-muted">{label}</div>
      <div className={`mt-1 text-2xl font-semibold tabular-nums ${color}`}>{value}</div>
    </div>
  );
}
```

`frontend/src/components/StatusBadge.tsx`:

```tsx
const TONES: Record<string, string> = {
  "On Track": "bg-emerald-50 text-emerald-800 border-emerald-200",
  Attention: "bg-amber-50 text-amber-800 border-amber-200",
  "At Risk": "bg-red-50 text-red-800 border-red-200",
  Critical: "bg-red-50 text-red-800 border-red-200",
  High: "bg-amber-50 text-amber-800 border-amber-200",
  Blocked: "bg-red-50 text-red-800 border-red-200",
  Completed: "bg-emerald-50 text-emerald-800 border-emerald-200",
  Closed: "bg-gray-100 text-gray-700 border-gray-200",
  Cancelled: "bg-gray-100 text-gray-700 border-gray-200",
  "On Hold": "bg-gray-100 text-gray-700 border-gray-200",
};

export function StatusBadge({ value }: { value: string }) {
  const tone = TONES[value] ?? "bg-canvas text-ink border-line";
  return <span className={`inline-block rounded border px-2 py-0.5 text-xs font-medium ${tone}`}>{value}</span>;
}
```

`frontend/src/components/DataTable.tsx`:

```tsx
import type { ReactNode } from "react";

export interface Column<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  className?: string;
}

export function DataTable<T extends { id: string }>({ columns, rows, onRowClick, empty }: {
  columns: Column<T>[];
  rows: T[];
  onRowClick?: (row: T) => void;
  empty?: ReactNode;
}) {
  if (rows.length === 0) return <>{empty ?? null}</>;
  return (
    <div className="card overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-line text-left text-[11px] uppercase tracking-wide text-muted">
            {columns.map((c) => (
              <th key={c.key} className={`px-4 py-2 font-medium ${c.className ?? ""}`}>{c.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.id}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              className={`border-b border-line last:border-0 ${onRowClick ? "cursor-pointer hover:bg-canvas" : ""}`}
            >
              {columns.map((c) => (
                <td key={c.key} className={`px-4 py-2.5 align-top ${c.className ?? ""}`}>{c.render(row)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

`frontend/src/components/FormDrawer.tsx`:

```tsx
import type { FormEvent, ReactNode } from "react";

export function FormDrawer({ open, title, onClose, onSubmit, submitting, error, children, footer }: {
  open: boolean;
  title: string;
  onClose: () => void;
  onSubmit: (e: FormEvent) => void;
  submitting?: boolean;
  error?: string | null;
  children: ReactNode;
  footer?: ReactNode;
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
            <button type="submit" className="btn btn-primary" disabled={submitting}>{submitting ? "Guardando…" : "Guardar"}</button>
          </div>
        </div>
      </form>
    </div>
  );
}
```

`frontend/src/components/Field.tsx`:

```tsx
import type { ReactNode } from "react";

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="label">{label}</span>
      {children}
    </label>
  );
}

export function Select({ value, onChange, options, allowEmpty }: {
  value: string;
  onChange: (v: string) => void;
  options: readonly string[];
  allowEmpty?: string;
}) {
  return (
    <select className="input" value={value} onChange={(e) => onChange(e.target.value)}>
      {allowEmpty !== undefined && <option value="">{allowEmpty}</option>}
      {options.map((o) => (
        <option key={o} value={o}>{o}</option>
      ))}
    </select>
  );
}
```

`frontend/src/components/EmptyState.tsx`:

```tsx
export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="card px-6 py-10 text-center">
      <div className="text-sm font-medium">{title}</div>
      {hint && <div className="mt-1 text-xs text-muted">{hint}</div>}
    </div>
  );
}
```

- [ ] **Step 5: Páginas de login y placeholder, router y arranque**

`frontend/src/pages/LoginPage.tsx`:

```tsx
import { FormEvent, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { errorMessage } from "../api/client";
import { useAuthStore } from "../stores/auth";

export function LoginPage() {
  const { status, login } = useAuthStore();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (status === "authenticated") return <Navigate to="/" replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-white px-4">
      <form onSubmit={submit} className="w-full max-w-sm">
        <div className="text-xs font-semibold tracking-[0.3em]">SYNER × HiTO</div>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">Transformation Room</h1>
        <div className="mt-8 space-y-4">
          <label className="block">
            <span className="label">Email</span>
            <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
          </label>
          <label className="block">
            <span className="label">Password</span>
            <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" />
          </label>
          {error && <p className="text-sm text-danger">{error}</p>}
          <button className="btn btn-primary w-full justify-center" type="submit" disabled={busy}>Sign in</button>
        </div>
        <p className="mt-6 text-center text-xs text-muted">Private advisory workspace</p>
      </form>
    </div>
  );
}
```

`frontend/src/pages/ComingSoonPage.tsx`:

```tsx
import { EmptyState } from "../components/EmptyState";
import { PageHeader } from "../components/PageHeader";

export function ComingSoonPage({ title }: { title: string }) {
  return (
    <>
      <PageHeader title={title} />
      <EmptyState title="Disponible en la siguiente entrega" hint="Este módulo se habilita en el segundo release." />
    </>
  );
}
```

`frontend/src/router.tsx`:

```tsx
import { useEffect } from "react";
import { createBrowserRouter, Navigate, Outlet } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { ComingSoonPage } from "./pages/ComingSoonPage";
import { LoginPage } from "./pages/LoginPage";
import { useAuthStore } from "./stores/auth";
import { useEngagementStore } from "./stores/engagement";

function RequireAuth() {
  const status = useAuthStore((s) => s.status);
  const { loaded, load } = useEngagementStore();
  useEffect(() => {
    if (status === "authenticated" && !loaded) void load();
  }, [status, loaded, load]);
  if (status === "unknown") return <div className="p-8 text-sm text-muted">Cargando…</div>;
  if (status === "anonymous") return <Navigate to="/login" replace />;
  if (!loaded) return <div className="p-8 text-sm text-muted">Cargando engagement…</div>;
  return <Outlet />;
}

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    element: <RequireAuth />,
    children: [
      {
        element: <AppShell />,
        children: [
          { path: "/", element: <ComingSoonPage title="Overview" /> },
          { path: "/findings", element: <ComingSoonPage title="Findings" /> },
          { path: "/initiatives", element: <ComingSoonPage title="Initiatives" /> },
          { path: "/roadmap", element: <ComingSoonPage title="Roadmap" /> },
          { path: "/actions", element: <ComingSoonPage title="Actions" /> },
          { path: "/decisions", element: <ComingSoonPage title="Decisions" /> },
          { path: "/meetings", element: <ComingSoonPage title="Meetings" /> },
          { path: "/documents", element: <ComingSoonPage title="Documents" /> },
          { path: "/lab", element: <ComingSoonPage title="Leadership Lab" /> },
          { path: "*", element: <Navigate to="/" replace /> },
        ],
      },
    ],
  },
]);
```

`frontend/src/App.tsx`:

```tsx
import { useEffect } from "react";
import { RouterProvider } from "react-router-dom";
import { router } from "./router";
import { useAuthStore } from "./stores/auth";

export default function App() {
  const bootstrap = useAuthStore((s) => s.bootstrap);
  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);
  return <RouterProvider router={router} />;
}
```

`frontend/src/main.tsx`:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

- [ ] **Step 6: Verificar build y login manual**

Run: `cd /mnt/d/Devs/HiTOxSyner/frontend && npm run build`
Expected: `tsc` sin errores y `dist/` generado.

Verificación manual: en una terminal `.venv/bin/uvicorn app.main:app --reload`, en otra `npm run dev`; abrir `http://localhost:5173/login`, entrar con `admin@syner.demo` / valor de `SEED_SYNER_PASSWORD` (default `syner-demo`). Debe verse el shell con el selector mostrando "Syner × HiTO Transformation Program" y el placeholder de Overview.

- [ ] **Step 7: Commit**

```bash
git add frontend
git commit -m "feat(frontend): scaffold Vite/React/Tailwind, login, shell y stores"
```

---

### Task 12: Página Dashboard (Executive Cockpit)

**Files:**
- Create: `frontend/src/pages/DashboardPage.tsx`, `frontend/src/components/ProgressBar.tsx`
- Modify: `frontend/src/router.tsx`

**Interfaces:**
- Consumes: `engagementsApi.dashboard/update`, `useEngagementStore`, `Tile`, `StatusBadge`, `EmptyState`, `can`.

- [ ] **Step 1: Escribir componentes y página**

`frontend/src/components/ProgressBar.tsx`:

```tsx
export function ProgressBar({ value }: { value: number }) {
  return (
    <div className="h-1.5 w-full rounded bg-line">
      <div className="h-1.5 rounded bg-ink" style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
    </div>
  );
}
```

`frontend/src/pages/DashboardPage.tsx`:

```tsx
import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { engagementsApi } from "../api/engagements";
import { errorMessage } from "../api/client";
import { EmptyState } from "../components/EmptyState";
import { ProgressBar } from "../components/ProgressBar";
import { StatusBadge } from "../components/StatusBadge";
import { Tile } from "../components/Tile";
import { useResource } from "../hooks/useResource";
import { formatDate, formatDateTime } from "../lib/dates";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="card p-5">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">{title}</h2>
      {children}
    </section>
  );
}

export function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const { current, refreshCurrent } = useEngagementStore();
  const engagementId = current?.id ?? "";
  const { data, loading, error, reload } = useResource(() => engagementsApi.dashboard(engagementId), [engagementId]);
  const [editing, setEditing] = useState(false);
  const [summary, setSummary] = useState("");
  const [saveError, setSaveError] = useState<string | null>(null);

  if (!current) return <EmptyState title="Sin engagement asignado" />;
  if (loading && !data) return <p className="text-sm text-muted">Cargando…</p>;
  if (error || !data) return <p className="text-sm text-danger">{error}</p>;

  const healthTone = data.tiles.health === "On Track" ? "ok" : data.tiles.health === "Attention" ? "warn" : "danger";

  async function saveSummary() {
    try {
      await engagementsApi.update(engagementId, { executive_summary: summary });
      setEditing(false);
      await Promise.all([reload(), refreshCurrent()]);
    } catch (err) {
      setSaveError(errorMessage(err));
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="text-xs font-semibold tracking-[0.3em]">SYNER × HiTO</div>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">{data.engagement.name}</h1>
        {data.engagement.subtitle && <p className="text-sm text-muted">{data.engagement.subtitle}</p>}
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        <Tile label="Engagement Health" value={data.tiles.health} tone={healthTone} />
        <Tile label="Progress" value={`${data.tiles.progress_pct}%`} />
        <Tile label="Active Initiatives" value={data.tiles.active_initiatives} />
        <Tile label="Open Actions" value={data.tiles.open_actions} />
        <Tile label="Decisions Required" value={data.tiles.decisions_required} tone={data.tiles.decisions_required > 0 ? "warn" : "default"} />
        <Tile label="Critical Findings" value={data.tiles.critical_findings} tone={data.tiles.critical_findings > 0 ? "danger" : "default"} />
      </div>

      <Section title="Executive Summary">
        {editing ? (
          <div className="space-y-2">
            <textarea className="input min-h-[120px]" value={summary} onChange={(e) => setSummary(e.target.value)} maxLength={2000} />
            {saveError && <p className="text-sm text-danger">{saveError}</p>}
            <div className="flex gap-2">
              <button className="btn btn-primary" onClick={saveSummary}>Guardar</button>
              <button className="btn" onClick={() => setEditing(false)}>Cancelar</button>
            </div>
          </div>
        ) : (
          <div className="flex items-start justify-between gap-4">
            <p className="whitespace-pre-line text-sm leading-6">{data.engagement.executive_summary || "Sin resumen ejecutivo todavía."}</p>
            {can(user, "write") && (
              <button className="btn" onClick={() => { setSummary(data.engagement.executive_summary); setEditing(true); }}>Editar</button>
            )}
          </div>
        )}
      </Section>

      <Section title="Transformation Roadmap">
        <div className="grid grid-cols-3 gap-2 md:grid-cols-6">
          {data.roadmap.map((phase) => (
            <div key={phase.phase} className="rounded border border-line px-3 py-2">
              <div className="text-sm font-medium">{phase.phase}</div>
              <div className="text-xs text-muted">{phase.milestones.length} milestones</div>
            </div>
          ))}
        </div>
      </Section>

      <div className="grid gap-6 lg:grid-cols-2">
        <Section title="Active Initiatives">
          {data.active_initiatives.length === 0 ? (
            <p className="text-sm text-muted">Sin iniciativas activas.</p>
          ) : (
            <ul className="space-y-3">
              {data.active_initiatives.map((i) => (
                <li key={i.id}>
                  <div className="flex items-center justify-between gap-3">
                    <Link to={`/initiatives/${i.id}`} className="text-sm font-medium hover:underline">{i.name}</Link>
                    <StatusBadge value={i.status} />
                  </div>
                  <div className="mt-1 flex items-center gap-3">
                    <ProgressBar value={i.progress_pct} />
                    <span className="text-xs tabular-nums text-muted">{i.progress_pct}%</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section title="Decisions Required">
          {data.decisions_required.length === 0 ? (
            <p className="text-sm text-muted">Sin decisiones pendientes de aprobación.</p>
          ) : null}
        </Section>

        <Section title="Key Findings">
          {data.key_findings.length === 0 ? (
            <p className="text-sm text-muted">Sin hallazgos de alto impacto.</p>
          ) : (
            <ul className="space-y-2">
              {data.key_findings.map((f) => (
                <li key={f.id} className="flex items-start justify-between gap-3 text-sm">
                  <span>{f.title}</span>
                  <StatusBadge value={f.impact} />
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section title="Next">
          {data.next_actions.length === 0 ? (
            <p className="text-sm text-muted">Sin acciones abiertas.</p>
          ) : (
            <ul className="space-y-2">
              {data.next_actions.map((a) => (
                <li key={a.id} className="flex items-start justify-between gap-3 text-sm">
                  <span>{a.title}<span className="block text-xs text-muted">{a.owner_name || "Sin responsable"}</span></span>
                  <span className="text-xs tabular-nums text-muted">{formatDate(a.due_date)}</span>
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section title="Recent Activity">
          {data.recent_activity.length === 0 ? (
            <p className="text-sm text-muted">Sin actividad.</p>
          ) : (
            <ul className="space-y-2">
              {data.recent_activity.map((a) => (
                <li key={a.id} className="text-sm">
                  {a.summary}
                  <span className="block text-xs text-muted">{formatDateTime(a.created_at)}</span>
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section title="Next Milestones">
          {data.next_milestones.length === 0 ? <p className="text-sm text-muted">Sin milestones programados.</p> : null}
        </Section>
      </div>
    </div>
  );
}
```

En `frontend/src/router.tsx` importar `DashboardPage` y reemplazar la ruta `/` por `{ path: "/", element: <DashboardPage /> }`.

- [ ] **Step 2: Verificar build y vista**

Run: `cd /mnt/d/Devs/HiTOxSyner/frontend && npm run build`
Expected: sin errores. Manual: con el seed, el dashboard muestra 6 tiles (Progress 10%, Active Initiatives 4, Open Actions 8, Critical Findings 1), el resumen editable para Syner y no editable para `exec@hito.demo`.

- [ ] **Step 3: Commit**

```bash
git add frontend
git commit -m "feat(frontend): dashboard ejecutivo con tiles, resumen editable y secciones"
```

---

### Task 13: Página Findings (tabla, drawer, conversión)

**Files:**
- Create: `frontend/src/api/findings.ts`, `frontend/src/pages/FindingsPage.tsx`
- Modify: `frontend/src/router.tsx`

**Interfaces:**
- Produces: `findingsApi.list(engagementId, params)`, `create`, `update`, `convert`.

- [ ] **Step 1: Escribir API y página**

`frontend/src/api/findings.ts`:

```ts
import { api } from "./client";
import type { Finding, Initiative, Page } from "../types";

export type FindingInput = Partial<Omit<Finding, "id" | "engagement_id" | "created_at" | "updated_at" | "initiative_id">>;

export const findingsApi = {
  list: (engagementId: string, params: { status?: string; type?: string } = {}) =>
    api.get<Page<Finding>>(`/engagements/${engagementId}/findings`, { params: { ...params, limit: 200 } }).then((r) => r.data),
  create: (engagementId: string, data: FindingInput) => api.post<Finding>(`/engagements/${engagementId}/findings`, data).then((r) => r.data),
  update: (id: string, data: FindingInput) => api.patch<Finding>(`/findings/${id}`, data).then((r) => r.data),
  convert: (id: string) => api.post<Initiative>(`/findings/${id}/convert`).then((r) => r.data),
};
```

`frontend/src/pages/FindingsPage.tsx`:

```tsx
import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { errorMessage } from "../api/client";
import { findingsApi, FindingInput } from "../api/findings";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { Field, Select } from "../components/Field";
import { FormDrawer } from "../components/FormDrawer";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { useResource } from "../hooks/useResource";
import { formatDate } from "../lib/dates";
import { FINDING_STATUSES, FINDING_TYPES, LEVELS } from "../lib/labels";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";
import type { Finding } from "../types";

const EMPTY: FindingInput = { title: "", description: "", context: "", type: "Finding", area: "", source: "", impact: "Medium", severity: "Medium", evidence: "", recommendation: "", status: "New" };

export function FindingsPage() {
  const user = useAuthStore((s) => s.user);
  const engagementId = useEngagementStore((s) => s.current?.id ?? "");
  const navigate = useNavigate();
  const [status, setStatus] = useState("");
  const [type, setType] = useState("");
  const { data, loading, error, reload } = useResource(
    () => findingsApi.list(engagementId, { status: status || undefined, type: type || undefined }),
    [engagementId, status, type],
  );
  const [editing, setEditing] = useState<Finding | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<FindingInput>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const writable = can(user, "write");

  function openCreate() { setEditing(null); setForm(EMPTY); setFormError(null); setOpen(true); }
  function openEdit(f: Finding) {
    if (!writable) return;
    setEditing(f);
    setForm({ title: f.title, description: f.description, context: f.context, type: f.type, area: f.area, source: f.source, impact: f.impact, severity: f.severity, evidence: f.evidence, recommendation: f.recommendation, status: f.status });
    setFormError(null);
    setOpen(true);
  }
  const set = (key: keyof FindingInput) => (value: string) => setForm((f) => ({ ...f, [key]: value }));

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    try {
      if (editing) await findingsApi.update(editing.id, form);
      else await findingsApi.create(engagementId, form);
      setOpen(false);
      await reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  async function convert() {
    if (!editing) return;
    setBusy(true); setFormError(null);
    try {
      const initiative = await findingsApi.convert(editing.id);
      setOpen(false);
      navigate(`/initiatives/${initiative.id}`);
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  return (
    <>
      <PageHeader title="Findings" subtitle="Hallazgos, riesgos y oportunidades del diagnóstico" action={writable && <button className="btn btn-primary" onClick={openCreate}>Nuevo finding</button>} />
      <div className="mb-4 flex flex-wrap gap-2">
        <div className="w-48"><Select value={status} onChange={setStatus} options={FINDING_STATUSES} allowEmpty="Todos los estados" /></div>
        <div className="w-48"><Select value={type} onChange={setType} options={FINDING_TYPES} allowEmpty="Todos los tipos" /></div>
      </div>
      {error && <p className="mb-4 text-sm text-danger">{error}</p>}
      {loading && !data ? <p className="text-sm text-muted">Cargando…</p> : (
        <DataTable<Finding>
          rows={data?.items ?? []}
          onRowClick={writable ? openEdit : undefined}
          empty={<EmptyState title="Sin findings" hint={writable ? "Registra el primer hallazgo del diagnóstico." : undefined} />}
          columns={[
            { key: "title", header: "Finding", render: (f) => <span className="font-medium">{f.title}<span className="block text-xs text-muted">{f.area || "—"}</span></span> },
            { key: "type", header: "Type", render: (f) => f.type },
            { key: "impact", header: "Impact", render: (f) => <StatusBadge value={f.impact} /> },
            { key: "status", header: "Status", render: (f) => <StatusBadge value={f.status} /> },
            { key: "date", header: "Fecha", render: (f) => formatDate(f.found_on), className: "tabular-nums" },
          ]}
        />
      )}
      <FormDrawer
        open={open}
        title={editing ? "Editar finding" : "Nuevo finding"}
        onClose={() => setOpen(false)}
        onSubmit={submit}
        submitting={busy}
        error={formError}
        footer={editing && editing.status !== "Converted to Initiative" && (
          <button type="button" className="btn" onClick={convert} disabled={busy}>Convertir a Initiative</button>
        )}
      >
        <Field label="Título"><input className="input" value={form.title ?? ""} onChange={(e) => set("title")(e.target.value)} required maxLength={200} /></Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Type"><Select value={form.type ?? "Finding"} onChange={set("type")} options={FINDING_TYPES} /></Field>
          <Field label="Status"><Select value={form.status ?? "New"} onChange={set("status")} options={FINDING_STATUSES} /></Field>
          <Field label="Impact"><Select value={form.impact ?? "Medium"} onChange={set("impact")} options={LEVELS} /></Field>
          <Field label="Severity"><Select value={form.severity ?? "Medium"} onChange={set("severity")} options={LEVELS} /></Field>
          <Field label="Área"><input className="input" value={form.area ?? ""} onChange={(e) => set("area")(e.target.value)} maxLength={120} /></Field>
          <Field label="Origen"><input className="input" value={form.source ?? ""} onChange={(e) => set("source")(e.target.value)} maxLength={200} /></Field>
        </div>
        <Field label="Descripción"><textarea className="input min-h-[80px]" value={form.description ?? ""} onChange={(e) => set("description")(e.target.value)} /></Field>
        <Field label="Contexto"><textarea className="input min-h-[60px]" value={form.context ?? ""} onChange={(e) => set("context")(e.target.value)} /></Field>
        <Field label="Evidencia"><textarea className="input min-h-[60px]" value={form.evidence ?? ""} onChange={(e) => set("evidence")(e.target.value)} /></Field>
        <Field label="Recomendación Syner"><textarea className="input min-h-[80px]" value={form.recommendation ?? ""} onChange={(e) => set("recommendation")(e.target.value)} /></Field>
      </FormDrawer>
    </>
  );
}
```

En `router.tsx` importar `FindingsPage` y reemplazar la ruta `/findings` por `{ path: "/findings", element: <FindingsPage /> }`.

- [ ] **Step 2: Verificar build y flujo manual**

Run: `cd /mnt/d/Devs/HiTOxSyner/frontend && npm run build`
Expected: sin errores. Manual: como Syner crear un finding, editarlo, cambiar status, y convertirlo (redirige a `/initiatives/:id`, que en esta tarea todavía cae en el placeholder de Initiatives; se completa en Task 14). Como `exec@hito.demo` no aparece el botón "Nuevo finding" ni se abre el drawer.

- [ ] **Step 3: Commit**

```bash
git add frontend
git commit -m "feat(frontend): página de findings con filtros, drawer y conversión"
```

---

### Task 14: Páginas Initiatives (lista) e Initiative Detail (mission control)

**Files:**
- Create: `frontend/src/api/initiatives.ts`, `frontend/src/api/actions.ts`, `frontend/src/pages/InitiativesPage.tsx`, `frontend/src/pages/InitiativeDetailPage.tsx`, `frontend/src/components/InitiativeForm.tsx`
- Modify: `frontend/src/router.tsx`

**Interfaces:**
- Produces: `initiativesApi.list/create/update/detail`, `actionsApi.list/create/update` (usados también en Task 15), `InitiativeForm` (campos del drawer compartidos por lista y detalle).

- [ ] **Step 1: Escribir APIs**

`frontend/src/api/initiatives.ts`:

```ts
import { api } from "./client";
import type { Initiative, InitiativeDetail, Page } from "../types";

export type InitiativeInput = Partial<Omit<Initiative, "id" | "engagement_id" | "created_at" | "updated_at">>;

export const initiativesApi = {
  list: (engagementId: string, params: { status?: string } = {}) =>
    api.get<Page<Initiative>>(`/engagements/${engagementId}/initiatives`, { params: { ...params, limit: 200 } }).then((r) => r.data),
  create: (engagementId: string, data: InitiativeInput) => api.post<Initiative>(`/engagements/${engagementId}/initiatives`, data).then((r) => r.data),
  update: (id: string, data: InitiativeInput) => api.patch<Initiative>(`/initiatives/${id}`, data).then((r) => r.data),
  detail: (id: string) => api.get<InitiativeDetail>(`/initiatives/${id}/detail`).then((r) => r.data),
};
```

`frontend/src/api/actions.ts`:

```ts
import { api } from "./client";
import type { Action, Page } from "../types";

export type ActionInput = Partial<Omit<Action, "id" | "engagement_id" | "created_at" | "updated_at">>;

export const actionsApi = {
  list: (engagementId: string, params: { status?: string; initiative_id?: string; mine?: boolean } = {}) =>
    api.get<Page<Action>>(`/engagements/${engagementId}/actions`, { params: { ...params, limit: 200 } }).then((r) => r.data),
  create: (engagementId: string, data: ActionInput) => api.post<Action>(`/engagements/${engagementId}/actions`, data).then((r) => r.data),
  update: (id: string, data: ActionInput) => api.patch<Action>(`/actions/${id}`, data).then((r) => r.data),
};
```

- [ ] **Step 2: Escribir formulario compartido y páginas**

`frontend/src/components/InitiativeForm.tsx`:

```tsx
import type { InitiativeInput } from "../api/initiatives";
import type { Initiative } from "../types";
import { INITIATIVE_STATUSES, LEVELS } from "../lib/labels";
import { Field, Select } from "./Field";

export const EMPTY_INITIATIVE: InitiativeInput = { name: "", description: "", objective: "", expected_outcome: "", hito_owner: "", area: "", priority: "Medium", status: "Discovery", start_date: null, target_date: null, progress_pct: 0, expected_impact: "", kpis: "", risks: "", dependencies: "" };

export function initiativeToInput(i: Initiative): InitiativeInput {
  const { name, description, objective, expected_outcome, hito_owner, area, priority, status, start_date, target_date, progress_pct, expected_impact, kpis, risks, dependencies } = i;
  return { name, description, objective, expected_outcome, hito_owner, area, priority, status, start_date, target_date, progress_pct, expected_impact, kpis, risks, dependencies };
}

export function InitiativeForm({ form, onChange }: { form: InitiativeInput; onChange: (next: InitiativeInput) => void }) {
  const set = (key: keyof InitiativeInput, value: unknown) => onChange({ ...form, [key]: value });
  const text = (key: keyof InitiativeInput, label: string, rows = 2) => (
    <Field label={label}><textarea className="input" rows={rows} value={(form[key] as string) ?? ""} onChange={(e) => set(key, e.target.value)} /></Field>
  );
  return (
    <>
      <Field label="Nombre"><input className="input" value={form.name ?? ""} onChange={(e) => set("name", e.target.value)} required maxLength={200} /></Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Status"><Select value={form.status ?? "Discovery"} onChange={(v) => set("status", v)} options={INITIATIVE_STATUSES} /></Field>
        <Field label="Priority"><Select value={form.priority ?? "Medium"} onChange={(v) => set("priority", v)} options={LEVELS} /></Field>
        <Field label="Owner HiTO"><input className="input" value={form.hito_owner ?? ""} onChange={(e) => set("hito_owner", e.target.value)} maxLength={200} /></Field>
        <Field label="Área"><input className="input" value={form.area ?? ""} onChange={(e) => set("area", e.target.value)} maxLength={120} /></Field>
        <Field label="Fecha inicio"><input className="input" type="date" value={form.start_date ?? ""} onChange={(e) => set("start_date", e.target.value || null)} /></Field>
        <Field label="Target date"><input className="input" type="date" value={form.target_date ?? ""} onChange={(e) => set("target_date", e.target.value || null)} /></Field>
        <Field label="Progreso (%)"><input className="input" type="number" min={0} max={100} value={form.progress_pct ?? 0} onChange={(e) => set("progress_pct", Number(e.target.value))} /></Field>
      </div>
      {text("description", "Descripción")}
      {text("objective", "Objective")}
      {text("expected_outcome", "Expected Outcome")}
      {text("expected_impact", "Impacto esperado")}
      {text("kpis", "KPIs")}
      {text("risks", "Riesgos")}
      {text("dependencies", "Dependencias")}
    </>
  );
}
```

`frontend/src/pages/InitiativesPage.tsx`:

```tsx
import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { errorMessage } from "../api/client";
import { initiativesApi, InitiativeInput } from "../api/initiatives";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { Select } from "../components/Field";
import { FormDrawer } from "../components/FormDrawer";
import { EMPTY_INITIATIVE, InitiativeForm } from "../components/InitiativeForm";
import { PageHeader } from "../components/PageHeader";
import { ProgressBar } from "../components/ProgressBar";
import { StatusBadge } from "../components/StatusBadge";
import { useResource } from "../hooks/useResource";
import { formatDate } from "../lib/dates";
import { INITIATIVE_STATUSES } from "../lib/labels";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";
import type { Initiative } from "../types";

export function InitiativesPage() {
  const user = useAuthStore((s) => s.user);
  const engagementId = useEngagementStore((s) => s.current?.id ?? "");
  const navigate = useNavigate();
  const [status, setStatus] = useState("");
  const { data, loading, error, reload } = useResource(() => initiativesApi.list(engagementId, { status: status || undefined }), [engagementId, status]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<InitiativeInput>(EMPTY_INITIATIVE);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    try {
      await initiativesApi.create(engagementId, form);
      setOpen(false); setForm(EMPTY_INITIATIVE);
      await reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  return (
    <>
      <PageHeader title="Initiatives" subtitle="Workstreams derivados del diagnóstico" action={can(user, "write") && <button className="btn btn-primary" onClick={() => setOpen(true)}>Nueva initiative</button>} />
      <div className="mb-4 w-48"><Select value={status} onChange={setStatus} options={INITIATIVE_STATUSES} allowEmpty="Todos los estados" /></div>
      {error && <p className="mb-4 text-sm text-danger">{error}</p>}
      {loading && !data ? <p className="text-sm text-muted">Cargando…</p> : (
        <DataTable<Initiative>
          rows={data?.items ?? []}
          onRowClick={(i) => navigate(`/initiatives/${i.id}`)}
          empty={<EmptyState title="Sin initiatives" hint="Las iniciativas se crean aquí o convirtiendo un finding." />}
          columns={[
            { key: "name", header: "Initiative", render: (i) => <span className="font-medium">{i.name}<span className="block text-xs text-muted">{i.hito_owner || "Sin owner HiTO"}</span></span> },
            { key: "status", header: "Status", render: (i) => <StatusBadge value={i.status} /> },
            { key: "priority", header: "Priority", render: (i) => <StatusBadge value={i.priority} /> },
            { key: "progress", header: "Progress", render: (i) => <div className="flex w-32 items-center gap-2"><ProgressBar value={i.progress_pct} /><span className="text-xs tabular-nums">{i.progress_pct}%</span></div> },
            { key: "target", header: "Target", render: (i) => formatDate(i.target_date), className: "tabular-nums" },
          ]}
        />
      )}
      <FormDrawer open={open} title="Nueva initiative" onClose={() => setOpen(false)} onSubmit={submit} submitting={busy} error={formError}>
        <InitiativeForm form={form} onChange={setForm} />
      </FormDrawer>
    </>
  );
}
```

`frontend/src/pages/InitiativeDetailPage.tsx`:

```tsx
import { FormEvent, useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import { errorMessage } from "../api/client";
import { initiativesApi, InitiativeInput } from "../api/initiatives";
import { EmptyState } from "../components/EmptyState";
import { FormDrawer } from "../components/FormDrawer";
import { InitiativeForm, initiativeToInput } from "../components/InitiativeForm";
import { ProgressBar } from "../components/ProgressBar";
import { StatusBadge } from "../components/StatusBadge";
import { useResource } from "../hooks/useResource";
import { formatDate, formatDateTime } from "../lib/dates";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";

function Block({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="card p-5">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">{title}</h2>
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
  const { data, loading, error, reload } = useResource(() => initiativesApi.detail(id), [id]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<InitiativeInput>({});
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

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
          {can(user, "write") && <button className="btn" onClick={() => { setForm(initiativeToInput(i)); setFormError(null); setOpen(true); }}>Editar</button>}
        </div>
        <div className="mt-4 flex items-center gap-3">
          <ProgressBar value={i.progress_pct} />
          <span className="text-sm tabular-nums">{i.progress_pct}%</span>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Block title="Objective"><Prose text={i.objective} /></Block>
        <Block title="Expected Outcome"><Prose text={i.expected_outcome} /></Block>
        <Block title="Milestones"><p className="text-sm text-muted">Disponible en la siguiente entrega.</p></Block>
        <Block title="Actions">
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
        <Block title="Decisions"><p className="text-sm text-muted">Disponible en la siguiente entrega.</p></Block>
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
        <Block title="Documents"><p className="text-sm text-muted">Disponible en la siguiente entrega.</p></Block>
        <Block title="Activity">
          {data.activity.length === 0 ? <p className="text-sm text-muted">Sin actividad.</p> : (
            <ul className="space-y-2">
              {data.activity.map((a) => (
                <li key={a.id} className="text-sm">{a.summary}<span className="block text-xs text-muted">{formatDateTime(a.created_at)}</span></li>
              ))}
            </ul>
          )}
        </Block>
      </div>

      <FormDrawer open={open} title="Editar initiative" onClose={() => setOpen(false)} onSubmit={submit} submitting={busy} error={formError}>
        <InitiativeForm form={form} onChange={setForm} />
      </FormDrawer>
    </div>
  );
}
```

En `router.tsx` importar ambas páginas y reemplazar `/initiatives` por `{ path: "/initiatives", element: <InitiativesPage /> }` y agregar `{ path: "/initiatives/:id", element: <InitiativeDetailPage /> }`.

- [ ] **Step 3: Verificar build y flujo manual**

Run: `cd /mnt/d/Devs/HiTOxSyner/frontend && npm run build`
Expected: sin errores. Manual: lista de 4 iniciativas del seed; clic abre el detalle con acciones vinculadas; convertir un finding desde Findings aterriza en el detalle con el finding origen listado.

- [ ] **Step 4: Commit**

```bash
git add frontend
git commit -m "feat(frontend): initiatives (lista y mission control) y API de actions"
```

---

### Task 15: Página Actions y My Actions

**Files:**
- Create: `frontend/src/pages/ActionsPage.tsx`
- Modify: `frontend/src/router.tsx`

- [ ] **Step 1: Escribir la página**

`frontend/src/pages/ActionsPage.tsx`:

```tsx
import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { actionsApi, ActionInput } from "../api/actions";
import { errorMessage } from "../api/client";
import { initiativesApi } from "../api/initiatives";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { Field, Select } from "../components/Field";
import { FormDrawer } from "../components/FormDrawer";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { useResource } from "../hooks/useResource";
import { formatDate } from "../lib/dates";
import { ACTION_STATUSES, LEVELS } from "../lib/labels";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";
import type { Action } from "../types";

const EMPTY: ActionInput = { title: "", description: "", owner_name: "", organization_side: "CLIENT", initiative_id: null, due_date: null, priority: "Medium", status: "Open", evidence: "" };

export function ActionsPage({ mine = false }: { mine?: boolean }) {
  const user = useAuthStore((s) => s.user);
  const engagementId = useEngagementStore((s) => s.current?.id ?? "");
  const [status, setStatus] = useState("");
  const { data, loading, error, reload } = useResource(
    () => actionsApi.list(engagementId, { status: status || undefined, mine: mine || undefined }),
    [engagementId, status, mine],
  );
  const initiatives = useResource(() => initiativesApi.list(engagementId), [engagementId]);
  const [editing, setEditing] = useState<Action | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<ActionInput>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const writable = can(user, "write");

  function canEdit(a: Action) {
    return writable || (user?.role === "HITO_COLLABORATOR" && a.owner_user_id === user.id);
  }
  function openCreate() { setEditing(null); setForm(EMPTY); setFormError(null); setOpen(true); }
  function openEdit(a: Action) {
    if (!canEdit(a)) return;
    setEditing(a);
    setForm({ title: a.title, description: a.description, owner_name: a.owner_name, organization_side: a.organization_side, initiative_id: a.initiative_id, due_date: a.due_date, priority: a.priority, status: a.status, evidence: a.evidence });
    setFormError(null); setOpen(true);
  }
  const set = (key: keyof ActionInput, value: unknown) => setForm((f) => ({ ...f, [key]: value }));
  const limited = !!editing && !writable;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    try {
      if (editing) await actionsApi.update(editing.id, limited ? { status: form.status, evidence: form.evidence } : form);
      else await actionsApi.create(engagementId, form);
      setOpen(false);
      await reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  const initiativeName = (id: string | null) => initiatives.data?.items.find((i) => i.id === id)?.name ?? "—";

  return (
    <>
      <PageHeader
        title={mine ? "My Actions" : "Actions"}
        subtitle={mine ? "Compromisos asignados a ti" : "Registro de compromisos del engagement"}
        action={
          <div className="flex gap-2">
            <Link to={mine ? "/actions" : "/actions/mine"} className="btn">{mine ? "Ver todas" : "My Actions"}</Link>
            {writable && <button className="btn btn-primary" onClick={openCreate}>Nueva action</button>}
          </div>
        }
      />
      <div className="mb-4 w-48"><Select value={status} onChange={setStatus} options={ACTION_STATUSES} allowEmpty="Todos los estados" /></div>
      {error && <p className="mb-4 text-sm text-danger">{error}</p>}
      {loading && !data ? <p className="text-sm text-muted">Cargando…</p> : (
        <DataTable<Action>
          rows={data?.items ?? []}
          onRowClick={openEdit}
          empty={<EmptyState title={mine ? "No tienes acciones asignadas" : "Sin acciones"} />}
          columns={[
            { key: "title", header: "Action", render: (a) => <span className="font-medium">{a.title}<span className="block text-xs text-muted">{initiativeName(a.initiative_id)}</span></span> },
            { key: "owner", header: "Responsable", render: (a) => <span>{a.owner_name || "—"}<span className="block text-xs text-muted">{a.organization_side}</span></span> },
            { key: "due", header: "Fecha", render: (a) => formatDate(a.due_date), className: "tabular-nums" },
            { key: "priority", header: "Priority", render: (a) => <StatusBadge value={a.priority} /> },
            { key: "status", header: "Status", render: (a) => <StatusBadge value={a.status} /> },
          ]}
        />
      )}
      <FormDrawer open={open} title={editing ? "Actualizar action" : "Nueva action"} onClose={() => setOpen(false)} onSubmit={submit} submitting={busy} error={formError}>
        {!limited && (
          <>
            <Field label="Acción"><input className="input" value={form.title ?? ""} onChange={(e) => set("title", e.target.value)} required maxLength={200} /></Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Responsable (nombre)"><input className="input" value={form.owner_name ?? ""} onChange={(e) => set("owner_name", e.target.value)} maxLength={200} /></Field>
              <Field label="Organización"><Select value={form.organization_side ?? "CLIENT"} onChange={(v) => set("organization_side", v)} options={["CLIENT", "SYNER"]} /></Field>
              <Field label="Initiative">
                <select className="input" value={form.initiative_id ?? ""} onChange={(e) => set("initiative_id", e.target.value || null)}>
                  <option value="">Sin initiative</option>
                  {initiatives.data?.items.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
                </select>
              </Field>
              <Field label="Fecha compromiso"><input className="input" type="date" value={form.due_date ?? ""} onChange={(e) => set("due_date", e.target.value || null)} /></Field>
              <Field label="Priority"><Select value={form.priority ?? "Medium"} onChange={(v) => set("priority", v)} options={LEVELS} /></Field>
            </div>
            <Field label="Descripción"><textarea className="input" rows={3} value={form.description ?? ""} onChange={(e) => set("description", e.target.value)} /></Field>
          </>
        )}
        {limited && <p className="text-sm text-muted">{editing?.title}</p>}
        <Field label="Status"><Select value={form.status ?? "Open"} onChange={(v) => set("status", v)} options={ACTION_STATUSES} /></Field>
        <Field label="Evidencia"><textarea className="input" rows={3} value={form.evidence ?? ""} onChange={(e) => set("evidence", e.target.value)} /></Field>
      </FormDrawer>
    </>
  );
}
```

En `router.tsx` importar `ActionsPage`, reemplazar `/actions` por `{ path: "/actions", element: <ActionsPage /> }` y agregar `{ path: "/actions/mine", element: <ActionsPage mine /> }`.

- [ ] **Step 2: Verificar build y flujo manual**

Run: `cd /mnt/d/Devs/HiTOxSyner/frontend && npm run build`
Expected: sin errores. Manual: como `collab@hito.demo`, "My Actions" muestra 3 acciones del seed; al abrir una, el drawer solo permite Status y Evidencia; como `exec@hito.demo` las filas no abren drawer; como Syner se puede crear y editar todo. Al completar una acción, el tile "Open Actions" del dashboard baja en 1.

- [ ] **Step 3: Commit**

```bash
git add frontend
git commit -m "feat(frontend): actions y My Actions con edición limitada para colaboradores"
```

---

### Task 16: Servir el frontend desde FastAPI, Docker, Railway y verificación de deploy

**Files:**
- Modify: `app/main.py`
- Create: `Dockerfile`, `railway.json`, `.dockerignore`
- Test: `tests/test_spa.py`

**Interfaces:**
- Produces: la app sirve `frontend/dist` en `/` con fallback a `index.html`; `/api/*` desconocido responde 404 JSON; servicio Railway `HiTOxSyner` desplegado con dominio público.

- [ ] **Step 1: Escribir el test del catch-all (falla)**

`tests/test_spa.py`:

```python
def test_unknown_api_route_is_json_404_not_index_html(client):
    response = client.get("/api/no-existe")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"detail": "Not Found"}


def test_non_api_route_serves_spa_or_explicit_404(client):
    response = client.get("/initiatives/abc")
    assert response.status_code in (200, 404)
    if response.status_code == 404:
        assert response.json() == {"detail": "Frontend build not found"}
    else:
        assert "<div id=\"root\">" in response.text
```

- [ ] **Step 2: Correr para verificar que falla**

Run: `.venv/bin/pytest tests/test_spa.py -v`
Expected: el segundo test FALLA (404 con `{"detail": "Not Found"}` en vez del mensaje explícito).

- [ ] **Step 3: Montar el frontend en `app/main.py`**

Agregar imports `from pathlib import Path`, `from fastapi import HTTPException`, `from fastapi.responses import FileResponse`, `from fastapi.staticfiles import StaticFiles` y al final del archivo, después de todos los `include_router`:

```python
DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if (DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
def spa(full_path: str):
    if full_path.startswith("api/") or full_path == "api":
        raise HTTPException(status_code=404, detail="Not Found")
    index = DIST / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="Frontend build not found")
    return FileResponse(index)
```

- [ ] **Step 4: Correr todos los tests**

Run: `.venv/bin/pytest tests -v`
Expected: PASS (55 passed).

- [ ] **Step 5: Dockerfile, .dockerignore y railway.json**

`Dockerfile`:

```dockerfile
FROM node:22-bookworm-slim AS frontend-build
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY --from=frontend-build /build/frontend/dist ./frontend/dist
CMD ["/bin/sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
```

`.dockerignore`:

```
.venv
.git
.env
frontend/node_modules
frontend/dist
tests
docs
__pycache__
```

`railway.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": { "builder": "DOCKERFILE", "dockerfilePath": "Dockerfile" },
  "deploy": {
    "startCommand": "/bin/sh -c \"alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port $PORT\"",
    "healthcheckPath": "/api/health",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

- [ ] **Step 6: Configurar variables en Railway y desplegar**

El Postgres de Railway solo es alcanzable desde la red interna de Railway, así que la base de producción se crea con `railway ssh` dentro del contenedor de Postgres. Las passwords demo se generan aquí y se guardan como variables del servicio para que el usuario las consulte en el dashboard de Railway, nunca en el chat.

```bash
cd /mnt/d/Devs/HiTOxSyner
railway link --project 712a7fba-0fe2-4284-b4cd-edfb9c8990fb --environment production --service HiTOxSyner
railway ssh --service Postgres -- psql -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='hitoxsyner'" | grep -q 1 \
  || railway ssh --service Postgres -- psql -U postgres -c 'CREATE DATABASE "hitoxsyner"'
JWT_SECRET="$(openssl rand -base64 48)"
SYNER_PW="$(openssl rand -base64 12)"; EXEC_PW="$(openssl rand -base64 12)"; COLLAB_PW="$(openssl rand -base64 12)"
railway variables --service HiTOxSyner \
  --set "ENVIRONMENT=production" \
  --set "JWT_SECRET=${JWT_SECRET}" \
  --set 'DATABASE_URL=postgresql://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.RAILWAY_PRIVATE_DOMAIN}}:5432/hitoxsyner' \
  --set "SEED_SYNER_PASSWORD=${SYNER_PW}" --set "SEED_EXEC_PASSWORD=${EXEC_PW}" --set "SEED_COLLAB_PASSWORD=${COLLAB_PW}"
railway up --service HiTOxSyner --detach
railway domain --service HiTOxSyner
```
Si `psql -U postgres` dentro del contenedor pide password, usar `railway ssh --service Postgres -- sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -c "CREATE DATABASE \"hitoxsyner\""'`.
Expected: el deploy termina en estado SUCCESS (revisar con `railway logs --service HiTOxSyner` que aparece `Running upgrade  -> <rev>, initial` y luego `Uvicorn running`). `railway domain` imprime la URL pública.

- [ ] **Step 7: Sembrar datos demo en producción (dentro del contenedor) y verificar**

```bash
railway ssh --service HiTOxSyner -- python -m app.seed
DOMAIN="$(railway domain --service HiTOxSyner 2>/dev/null | grep -o 'https://[^ ]*' | head -1)"
curl -s "${DOMAIN}/api/health"
curl -s -o /dev/null -w "%{http_code}\n" "${DOMAIN}/login"
curl -s -X POST "${DOMAIN}/api/auth/login" -H 'Content-Type: application/json' -d "{\"email\":\"admin@syner.demo\",\"password\":\"${SYNER_PW}\"}" | grep -o '"role":"SYNER_ADMIN"'
```
Expected: `Seed completado.`, `{"status":"ok","database":"ok"}`, `200`, y `"role":"SYNER_ADMIN"`. Si `railway domain` no imprime la URL, tomarla del paso anterior o del dashboard.

Nota: Task 10 corrió migración y seed contra `hitoxsyner_dev` local. Producción (`hitoxsyner` en Railway) solo se toca desde dentro de Railway: migración en el arranque del contenedor y seed vía `railway ssh`.

- [ ] **Step 8: Commit**

```bash
git add app/main.py Dockerfile .dockerignore railway.json tests/test_spa.py
git commit -m "feat: servir frontend desde FastAPI, Dockerfile y configuración de Railway"
```

---

## Verificación final del plan 1

- `.venv/bin/pytest tests -v` → 55 passed (más los tests añadidos en fix rounds).
- `cd frontend && npm run build` → sin errores.
- `curl https://<dominio>/api/health` → `{"status":"ok","database":"ok"}`.
- Login en el dominio con los tres usuarios demo; el dashboard carga; crear finding → convertir → ver initiative → crear action → completar action → tile Open Actions cambia.
- `git log --oneline` muestra un commit por tarea.
