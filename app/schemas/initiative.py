import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import InitiativeStatus, Level
from app.schemas.action import ActionRead
from app.schemas.activity import ActivityRead
from app.schemas.decision import DecisionRead
from app.schemas.finding import FindingRead
from app.schemas.milestone import MilestoneRead


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


class InitiativeDetail(BaseModel):
    initiative: InitiativeRead
    findings: list[FindingRead]
    milestones: list[MilestoneRead]
    actions: list[ActionRead]
    decisions: list[DecisionRead]
    activity: list[ActivityRead]
