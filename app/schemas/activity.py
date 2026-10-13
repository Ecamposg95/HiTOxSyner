import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ActivityAction


class ActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID | None
    user_name: str
    action: ActivityAction
    entity_type: str
    entity_id: uuid.UUID
    summary: str
    changes: list[dict]
    created_at: datetime
