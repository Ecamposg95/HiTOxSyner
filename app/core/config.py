from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
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

    @model_validator(mode="after")
    def reject_insecure_production(self) -> "Settings":
        if self.environment == "production" and (self.jwt_secret == "change-me" or len(self.jwt_secret) < 32):
            raise ValueError("En producción JWT_SECRET debe definirse y tener al menos 32 caracteres")
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
