import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import MilestoneStatus, RoadmapPhase
from app.models.milestone import Milestone


def list_for_engagement(
    db: Session, engagement_id: uuid.UUID, *, phase: RoadmapPhase | None = None,
    status: MilestoneStatus | None = None, initiative_id: uuid.UUID | None = None,
    limit: int = 50, offset: int = 0,
) -> tuple[list[Milestone], int]:
    query = select(Milestone).where(Milestone.engagement_id == engagement_id)
    if phase:
        query = query.where(Milestone.phase == phase)
    if status:
        query = query.where(Milestone.status == status)
    if initiative_id:
        query = query.where(Milestone.initiative_id == initiative_id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Milestone.due_date.nulls_last(), Milestone.created_at).limit(limit).offset(offset)))
    return items, total


def list_all(db: Session, engagement_id: uuid.UUID) -> list[Milestone]:
    query = select(Milestone).where(Milestone.engagement_id == engagement_id).order_by(Milestone.due_date.nulls_last(), Milestone.created_at)
    return list(db.scalars(query))


def upcoming(db: Session, engagement_id: uuid.UUID, limit: int = 5) -> list[Milestone]:
    query = (
        select(Milestone)
        .where(Milestone.engagement_id == engagement_id)
        .where(Milestone.status != MilestoneStatus.DONE)
        .where(Milestone.due_date.is_not(None))
        .order_by(Milestone.due_date, Milestone.created_at)
        .limit(limit)
    )
    return list(db.scalars(query))


def list_by_initiative(db: Session, initiative_id: uuid.UUID) -> list[Milestone]:
    query = select(Milestone).where(Milestone.initiative_id == initiative_id).order_by(Milestone.due_date.nulls_last(), Milestone.created_at)
    return list(db.scalars(query))
