import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MeetingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    held_on: datetime
    participants: str = Field(default="", max_length=10000)
    objective: str = Field(default="", max_length=10000)
    summary: str = Field(default="", max_length=10000)
    discussion: str = Field(default="", max_length=10000)
    next_steps: str = Field(default="", max_length=10000)


class MeetingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    held_on: datetime | None = None
    participants: str | None = Field(default=None, max_length=10000)
    objective: str | None = Field(default=None, max_length=10000)
    summary: str | None = Field(default=None, max_length=10000)
    discussion: str | None = Field(default=None, max_length=10000)
    next_steps: str | None = Field(default=None, max_length=10000)


class MeetingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    engagement_id: uuid.UUID
    title: str
    held_on: datetime
    participants: str
    objective: str
    summary: str
    discussion: str
    next_steps: str
    created_at: datetime
    updated_at: datetime
