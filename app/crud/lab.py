import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.lab import LabSession, Pod


def _page(db: Session, query, order_by, limit: int, offset: int):
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(*order_by).limit(limit).offset(offset)))
    return items, total


def list_sessions(db: Session, engagement_id: uuid.UUID, *, limit: int = 50, offset: int = 0) -> tuple[list[LabSession], int]:
    query = select(LabSession).where(LabSession.engagement_id == engagement_id)
    return _page(db, query, (LabSession.number,), limit, offset)


def list_all_sessions(db: Session, engagement_id: uuid.UUID) -> list[LabSession]:
    return list(db.scalars(select(LabSession).where(LabSession.engagement_id == engagement_id).order_by(LabSession.number)))


def get_session_by_number(db: Session, engagement_id: uuid.UUID, number: int) -> LabSession | None:
    return db.scalar(select(LabSession).where(LabSession.engagement_id == engagement_id, LabSession.number == number))


def list_pods(db: Session, engagement_id: uuid.UUID, *, limit: int = 50, offset: int = 0) -> tuple[list[Pod], int]:
    query = select(Pod).where(Pod.engagement_id == engagement_id)
    return _page(db, query, (Pod.number,), limit, offset)


def list_all_pods(db: Session, engagement_id: uuid.UUID) -> list[Pod]:
    return list(db.scalars(select(Pod).where(Pod.engagement_id == engagement_id).order_by(Pod.number)))


def get_pod_by_number(db: Session, engagement_id: uuid.UUID, number: int) -> Pod | None:
    return db.scalar(select(Pod).where(Pod.engagement_id == engagement_id, Pod.number == number))
