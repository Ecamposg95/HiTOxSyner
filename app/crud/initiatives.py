import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import InitiativeStatus
from app.models.initiative import Initiative

INACTIVE = (InitiativeStatus.COMPLETED, InitiativeStatus.ON_HOLD)


def list_for_engagement(
    db: Session, engagement_id: uuid.UUID, *, status: InitiativeStatus | None = None, limit: int = 50, offset: int = 0
) -> tuple[list[Initiative], int]:
    query = select(Initiative).where(Initiative.engagement_id == engagement_id)
    if status:
        query = query.where(Initiative.status == status)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Initiative.created_at.desc()).limit(limit).offset(offset)))
    return items, total


def active(db: Session, engagement_id: uuid.UUID) -> list[Initiative]:
    query = (
        select(Initiative)
        .where(Initiative.engagement_id == engagement_id)
        .where(Initiative.status.not_in(INACTIVE))
        .order_by(Initiative.priority.desc(), Initiative.target_date.nulls_last())
    )
    return list(db.scalars(query))


def count_active(db: Session, engagement_id: uuid.UUID) -> int:
    query = (
        select(func.count()).select_from(Initiative)
        .where(Initiative.engagement_id == engagement_id)
        .where(Initiative.status.not_in(INACTIVE))
    )
    return db.scalar(query) or 0
