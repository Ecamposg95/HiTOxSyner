import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.decision import Decision
from app.models.enums import PENDING_DECISION_STATUSES, DecisionStatus


def list_for_engagement(
    db: Session, engagement_id: uuid.UUID, *, status: DecisionStatus | None = None,
    initiative_id: uuid.UUID | None = None, meeting_id: uuid.UUID | None = None,
    limit: int = 50, offset: int = 0,
) -> tuple[list[Decision], int]:
    query = select(Decision).where(Decision.engagement_id == engagement_id)
    if status:
        query = query.where(Decision.status == status)
    if initiative_id:
        query = query.where(Decision.initiative_id == initiative_id)
    if meeting_id:
        query = query.where(Decision.meeting_id == meeting_id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Decision.created_at.desc()).limit(limit).offset(offset)))
    return items, total


def _pending(engagement_id: uuid.UUID):
    return select(Decision).where(Decision.engagement_id == engagement_id).where(Decision.status.in_(PENDING_DECISION_STATUSES))


def count_required(db: Session, engagement_id: uuid.UUID) -> int:
    return db.scalar(select(func.count()).select_from(_pending(engagement_id).subquery())) or 0


def required(db: Session, engagement_id: uuid.UUID, limit: int = 5) -> list[Decision]:
    return list(db.scalars(_pending(engagement_id).order_by(Decision.created_at).limit(limit)))


def list_by_initiative(db: Session, initiative_id: uuid.UUID) -> list[Decision]:
    return list(db.scalars(select(Decision).where(Decision.initiative_id == initiative_id).order_by(Decision.created_at)))


def list_by_meeting(db: Session, meeting_id: uuid.UUID) -> list[Decision]:
    return list(db.scalars(select(Decision).where(Decision.meeting_id == meeting_id).order_by(Decision.created_at)))
