import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.action import Action
from app.models.enums import ActionStatus

OPEN_STATUSES = (ActionStatus.OPEN, ActionStatus.IN_PROGRESS, ActionStatus.BLOCKED)


def list_for_engagement(
    db: Session, engagement_id: uuid.UUID, *, status: ActionStatus | None = None,
    initiative_id: uuid.UUID | None = None, owner_user_id: uuid.UUID | None = None,
    meeting_id: uuid.UUID | None = None, limit: int = 50, offset: int = 0,
) -> tuple[list[Action], int]:
    query = select(Action).where(Action.engagement_id == engagement_id)
    if status:
        query = query.where(Action.status == status)
    if initiative_id:
        query = query.where(Action.initiative_id == initiative_id)
    if owner_user_id:
        query = query.where(Action.owner_user_id == owner_user_id)
    if meeting_id:
        query = query.where(Action.meeting_id == meeting_id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Action.due_date.nulls_last(), Action.created_at.desc()).limit(limit).offset(offset)))
    return items, total


def count_open(db: Session, engagement_id: uuid.UUID) -> int:
    query = select(func.count()).select_from(Action).where(Action.engagement_id == engagement_id).where(Action.status.in_(OPEN_STATUSES))
    return db.scalar(query) or 0


def next_open(db: Session, engagement_id: uuid.UUID, limit: int = 5) -> list[Action]:
    query = (
        select(Action).where(Action.engagement_id == engagement_id).where(Action.status.in_(OPEN_STATUSES))
        .order_by(Action.due_date.nulls_last(), Action.priority.desc()).limit(limit)
    )
    return list(db.scalars(query))


def list_by_initiative(db: Session, initiative_id: uuid.UUID) -> list[Action]:
    return list(db.scalars(select(Action).where(Action.initiative_id == initiative_id).order_by(Action.due_date.nulls_last())))


def list_by_meeting(db: Session, meeting_id: uuid.UUID) -> list[Action]:
    return list(db.scalars(select(Action).where(Action.meeting_id == meeting_id).order_by(Action.due_date.nulls_last(), Action.created_at)))
