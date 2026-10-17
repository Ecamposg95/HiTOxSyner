import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.meeting import Meeting


def list_for_engagement(db: Session, engagement_id: uuid.UUID, *, limit: int = 50, offset: int = 0) -> tuple[list[Meeting], int]:
    query = select(Meeting).where(Meeting.engagement_id == engagement_id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Meeting.held_on.desc(), Meeting.created_at.desc()).limit(limit).offset(offset)))
    return items, total
