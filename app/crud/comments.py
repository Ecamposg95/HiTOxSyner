import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.comment import Comment


def list_for_entity(
    db: Session, engagement_id: uuid.UUID, entity_type: str, entity_id: uuid.UUID, *, limit: int = 50, offset: int = 0,
) -> tuple[list[Comment], int]:
    query = (
        select(Comment)
        .where(Comment.engagement_id == engagement_id)
        .where(Comment.entity_type == entity_type)
        .where(Comment.entity_id == entity_id)
    )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Comment.created_at, Comment.id).limit(limit).offset(offset)))
    return items, total
