import pytest

from app.core.config import Settings


def test_production_rejects_default_jwt_secret():
    with pytest.raises(ValueError):
        Settings(environment="production", jwt_secret="change-me", _env_file=None)


def test_production_rejects_short_jwt_secret():
    with pytest.raises(ValueError):
        Settings(environment="production", jwt_secret="x" * 31, _env_file=None)


def test_production_accepts_long_secret():
    Settings(environment="production", jwt_secret="x" * 40, _env_file=None)


def test_development_allows_default_secret():
    Settings(environment="development", jwt_secret="change-me", _env_file=None)


def test_seed_refuses_default_passwords_in_production(db, monkeypatch):
    import app.seed as seed_module

    prod = Settings(environment="production", jwt_secret="x" * 40, _env_file=None)
    monkeypatch.setattr(seed_module, "get_settings", lambda: prod)
    with pytest.raises(RuntimeError, match="SEED_SYNER_PASSWORD"):
        seed_module.seed(db)
