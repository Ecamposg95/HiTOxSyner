import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DecisionStatus


class DecisionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    context: str = Field(default="", max_length=10000)
    alternatives: str = Field(default="", max_length=10000)
    syner_recommendation: str = Field(default="", max_length=10000)
    final_decision: str = Field(default="", max_length=10000)
    owner_name: str = Field(default="", max_length=200)
    participants: str = Field(default="", max_length=10000)
    decided_on: date | None = None
    impact: str = Field(default="", max_length=10000)
    status: DecisionStatus = DecisionStatus.PROPOSED
    initiative_id: uuid.UUID | None = None
    meeting_id: uuid.UUID | None = None


class DecisionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    context: str | None = Field(default=None, max_length=10000)
    alternatives: str | None = Field(default=None, max_length=10000)
    syner_recommendation: str | None = Field(default=None, max_length=10000)
    final_decision: str | None = Field(default=None, max_length=10000)
    owner_name: str | None = Field(default=None, max_length=200)
    participants: str | None = Field(default=None, max_length=10000)
    decided_on: date | None = None
    impact: str | None = Field(default=None, max_length=10000)
    status: DecisionStatus | None = None
    initiative_id: uuid.UUID | None = None
    meeting_id: uuid.UUID | None = None


class DecisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    engagement_id: uuid.UUID
    title: str
    context: str
    alternatives: str
    syner_recommendation: str
    final_decision: str
    owner_name: str
    participants: str
    decided_on: date | None
    impact: str
    status: DecisionStatus
    initiative_id: uuid.UUID | None
    meeting_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
