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
