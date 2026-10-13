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
