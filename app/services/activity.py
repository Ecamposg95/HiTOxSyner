import enum
import uuid
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.engagement import Engagement
from app.models.enums import ActivityAction
from app.models.user import User


def _plain(value):
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


def diff_changes(entity, payload: dict) -> list[dict]:
    changes = []
    for field, new_value in payload.items():
        before = _plain(getattr(entity, field))
        after = _plain(new_value)
        if before != after:
            changes.append({"field": field, "before": before, "after": after})
    return changes


def log_activity(
    db: Session, *, user: User, engagement: Engagement, action: ActivityAction,
    entity_type: str, entity_id: uuid.UUID, summary: str, changes: list[dict] | None = None,
    internal_only: bool = False,
) -> Activity:
    activity = Activity(
        organization_id=engagement.organization_id,
        engagement_id=engagement.id,
        user_id=user.id,
        user_name=user.full_name,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary[:500],
        changes=changes or [],
        internal_only=internal_only,
    )
    db.add(activity)
    db.flush()
    return activity
