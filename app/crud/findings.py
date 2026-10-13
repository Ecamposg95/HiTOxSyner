import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import FindingStatus, FindingType, Level
from app.models.finding import Finding


def list_for_engagement(
    db: Session, engagement_id: uuid.UUID, *, status: FindingStatus | None = None,
    type: FindingType | None = None, limit: int = 50, offset: int = 0,
) -> tuple[list[Finding], int]:
    query = select(Finding).where(Finding.engagement_id == engagement_id)
    if status:
        query = query.where(Finding.status == status)
    if type:
        query = query.where(Finding.type == type)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Finding.created_at.desc()).limit(limit).offset(offset)))
    return items, total


def key_findings(db: Session, engagement_id: uuid.UUID, limit: int = 6) -> list[Finding]:
    query = (
        select(Finding)
        .where(Finding.engagement_id == engagement_id)
        .where(Finding.impact.in_([Level.HIGH, Level.CRITICAL]))
        .where(Finding.status != FindingStatus.CLOSED)
        .order_by(Finding.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(query))


def count_critical_open(db: Session, engagement_id: uuid.UUID) -> int:
    query = (
        select(func.count())
        .select_from(Finding)
        .where(Finding.engagement_id == engagement_id)
        .where(Finding.impact == Level.CRITICAL)
        .where(Finding.status != FindingStatus.CLOSED)
    )
    return db.scalar(query) or 0


def list_by_initiative(db: Session, initiative_id: uuid.UUID) -> list[Finding]:
    return list(db.scalars(select(Finding).where(Finding.initiative_id == initiative_id).order_by(Finding.created_at)))
