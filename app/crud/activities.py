import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.activity import Activity


def list_for_engagement(
    db: Session, engagement_id: uuid.UUID, *, entity_type: str | None = None,
    entity_id: uuid.UUID | None = None, limit: int = 50, offset: int = 0,
) -> tuple[list[Activity], int]:
    query = select(Activity).where(Activity.engagement_id == engagement_id)
    if entity_type:
        query = query.where(Activity.entity_type == entity_type)
    if entity_id:
        query = query.where(Activity.entity_id == entity_id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Activity.created_at.desc()).limit(limit).offset(offset)))
    return items, total


def recent(db: Session, engagement_id: uuid.UUID, limit: int = 15) -> list[Activity]:
    return list_for_engagement(db, engagement_id, limit=limit)[0]
