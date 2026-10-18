import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ContractStatus, CtaStatus, LabSessionStatus, LabSessionTheme


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


class ParticipantCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    area: str = Field(default="", max_length=120)
    title: str = Field(default="", max_length=200)
    pod_id: uuid.UUID | None = None
    is_active: bool = True


class ParticipantUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    area: str | None = Field(default=None, max_length=120)
    title: str | None = Field(default=None, max_length=200)
    pod_id: uuid.UUID | None = None
    is_active: bool | None = None


class ParticipantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    engagement_id: uuid.UUID
    full_name: str
    area: str
    title: str
    pod_id: uuid.UUID | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CtaCreate(BaseModel):
    participant_id: uuid.UUID
    session_id: uuid.UUID
    trigger: str = Field(default="", max_length=10000)
    behavior: str = Field(min_length=1, max_length=10000)
    stakeholder: str = Field(default="", max_length=200)
    evidence_expected: str = Field(default="", max_length=10000)
    due_date: date | None = None
    accountability_partner: str = Field(default="", max_length=200)
    impact: str = Field(default="", max_length=10000)
    status: CtaStatus = CtaStatus.COMMITTED
    evidence_notes: str = Field(default="", max_length=10000)


class CtaUpdate(BaseModel):
    participant_id: uuid.UUID | None = None
    session_id: uuid.UUID | None = None
    trigger: str | None = Field(default=None, max_length=10000)
    behavior: str | None = Field(default=None, min_length=1, max_length=10000)
    stakeholder: str | None = Field(default=None, max_length=200)
    evidence_expected: str | None = Field(default=None, max_length=10000)
    due_date: date | None = None
    accountability_partner: str | None = Field(default=None, max_length=200)
    impact: str | None = Field(default=None, max_length=10000)
    status: CtaStatus | None = None
    evidence_notes: str | None = Field(default=None, max_length=10000)


class CtaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    engagement_id: uuid.UUID
    participant_id: uuid.UUID
    session_id: uuid.UUID
    trigger: str
    behavior: str
    stakeholder: str
    evidence_expected: str
    due_date: date | None
    accountability_partner: str
    impact: str
    status: CtaStatus
    evidence_notes: str
    created_at: datetime
    updated_at: datetime


class ActionContractCreate(BaseModel):
    participant_id: uuid.UUID
    start_date: date | None = None
    review_30_date: date | None = None
    review_60_date: date | None = None
    success_signal: str = Field(default="", max_length=10000)
    status: ContractStatus = ContractStatus.DRAFT
    cta_ids: list[uuid.UUID] = Field(default_factory=list, max_length=3)


class ActionContractUpdate(BaseModel):
    participant_id: uuid.UUID | None = None
    start_date: date | None = None
    review_30_date: date | None = None
    review_60_date: date | None = None
    success_signal: str | None = Field(default=None, max_length=10000)
    status: ContractStatus | None = None
    cta_ids: list[uuid.UUID] | None = Field(default=None, max_length=3)


class ActionContractRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    engagement_id: uuid.UUID
    participant_id: uuid.UUID
    start_date: date | None
    review_30_date: date | None
    review_60_date: date | None
    success_signal: str
    status: ContractStatus
    cta_ids: list[uuid.UUID]
    created_at: datetime
    updated_at: datetime
