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
    meeting_id: uuid.UUID | None = None
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
    meeting_id: uuid.UUID | None = None
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
    meeting_id: uuid.UUID | None
    due_date: date | None
    priority: Level
    status: ActionStatus
    evidence: str
    created_at: datetime
    updated_at: datetime
