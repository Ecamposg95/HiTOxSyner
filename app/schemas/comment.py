import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    entity_type: str = Field(min_length=1, max_length=50)
    entity_id: uuid.UUID
    body: str = Field(min_length=1, max_length=10000)


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    engagement_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    author_id: uuid.UUID | None
    author_name: str
    body: str
    created_at: datetime
