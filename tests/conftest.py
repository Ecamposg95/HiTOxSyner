import os

from app.core.config import Settings

_boot = Settings()
if not _boot.test_database_url:
    raise RuntimeError("TEST_DATABASE_URL no está definido; ponlo en .env")
if "test" not in _boot.test_database_url.rsplit("/", 1)[-1]:
    raise RuntimeError("TEST_DATABASE_URL debe apuntar a una base cuyo nombre contenga 'test'")
os.environ["DATABASE_URL"] = _boot.test_database_url
os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET"] = "test-secret-with-at-least-32-bytes-for-hs256"
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


from tests.factories import build_world  # noqa: E402


@pytest.fixture
def world(db):
    return build_world(db)
