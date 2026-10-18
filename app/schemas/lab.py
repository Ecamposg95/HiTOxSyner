import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import LabSessionStatus, LabSessionTheme


class LabSessionCreate(BaseModel):
    number: int = Field(ge=1, le=4)
    name: str = Field(default="", max_length=200)
    theme: LabSessionTheme | None = None
    held_on: date | None = None
    status: LabSessionStatus = LabSessionStatus.PLANNED
    attendance_count: int | None = Field(default=None, ge=0)
    syner_notes: str = Field(default="", max_length=10000)


class LabSessionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    theme: LabSessionTheme | None = None
    held_on: date | None = None
    status: LabSessionStatus | None = None
    attendance_count: int | None = Field(default=None, ge=0)
    syner_notes: str | None = Field(default=None, max_length=10000)


class LabSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    engagement_id: uuid.UUID
    number: int
    name: str
    theme: LabSessionTheme
    held_on: date | None
    status: LabSessionStatus
    attendance_count: int | None
    syner_notes: str
    created_at: datetime
    updated_at: datetime


class PodCreate(BaseModel):
    number: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=200)


class PodUpdate(BaseModel):
    number: int | None = Field(default=None, ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=200)


class PodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    engagement_id: uuid.UUID
    number: int
    name: str
    created_at: datetime
    updated_at: datetime
