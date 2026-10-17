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
