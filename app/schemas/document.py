import uuid
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import DocumentCategory

Tag = Annotated[str, Field(min_length=1, max_length=50)]


def _check_url(value: str | None) -> str | None:
    if value and not value.lower().startswith(("http://", "https://")):
        raise ValueError("url debe estar vacía o empezar por http:// o https://")
    return value


class DocumentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10000)
    category: DocumentCategory = DocumentCategory.DISCOVERY
    version: str = Field(default="", max_length=50)
    url: str = Field(default="", max_length=2000)
    doc_date: date | None = None
    tags: list[Tag] = Field(default_factory=list, max_length=20)
    internal_only: bool = False

    @field_validator("url")
    @classmethod
    def validate_url(cls, value):
        return _check_url(value)


class DocumentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    category: DocumentCategory | None = None
    version: str | None = Field(default=None, max_length=50)
    url: str | None = Field(default=None, max_length=2000)
    doc_date: date | None = None
    tags: list[Tag] | None = Field(default=None, max_length=20)
    internal_only: bool | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, value):
        return _check_url(value)


class DocumentLinkCreate(BaseModel):
    entity_type: str = Field(min_length=1, max_length=50)
    entity_id: uuid.UUID


class DocumentLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    engagement_id: uuid.UUID
    name: str
    description: str
    category: DocumentCategory
    version: str
    url: str
    doc_date: date | None
    uploader_id: uuid.UUID | None
    tags: list[str]
    internal_only: bool
    links: list[DocumentLinkRead]
    created_at: datetime
    updated_at: datetime
