import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import ACTIVE_CONTRACT_STATUSES, ContractStatus, CtaStatus
from app.models.lab import ActionContract, Cta, LabSession, Participant, Pod


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


def list_participants(
    db: Session, engagement_id: uuid.UUID, *, pod_id: uuid.UUID | None = None, is_active: bool | None = None,
    limit: int = 50, offset: int = 0,
) -> tuple[list[Participant], int]:
    query = select(Participant).where(Participant.engagement_id == engagement_id)
    if pod_id:
        query = query.where(Participant.pod_id == pod_id)
    if is_active is not None:
        query = query.where(Participant.is_active.is_(is_active))
    return _page(db, query, (Participant.full_name, Participant.created_at), limit, offset)


def list_ctas(
    db: Session, engagement_id: uuid.UUID, *, session_id: uuid.UUID | None = None, pod_id: uuid.UUID | None = None,
    status: CtaStatus | None = None, limit: int = 50, offset: int = 0,
) -> tuple[list[Cta], int]:
    query = select(Cta).where(Cta.engagement_id == engagement_id)
    if session_id:
        query = query.where(Cta.session_id == session_id)
    if pod_id:
        query = query.join(Participant, Participant.id == Cta.participant_id).where(Participant.pod_id == pod_id)
    if status:
        query = query.where(Cta.status == status)
    return _page(db, query, (Cta.due_date.nulls_last(), Cta.created_at), limit, offset)


def list_contracts(
    db: Session, engagement_id: uuid.UUID, *, status: ContractStatus | None = None, limit: int = 50, offset: int = 0,
) -> tuple[list[ActionContract], int]:
    query = select(ActionContract).where(ActionContract.engagement_id == engagement_id)
    if status:
        query = query.where(ActionContract.status == status)
    return _page(db, query, (ActionContract.created_at,), limit, offset)


def get_contract_by_participant(db: Session, engagement_id: uuid.UUID, participant_id: uuid.UUID) -> ActionContract | None:
    return db.scalar(
        select(ActionContract).where(ActionContract.engagement_id == engagement_id, ActionContract.participant_id == participant_id)
    )


def count_active_contracts(db: Session, engagement_id: uuid.UUID) -> int:
    query = select(func.count()).select_from(ActionContract).where(
        ActionContract.engagement_id == engagement_id, ActionContract.status.in_(ACTIVE_CONTRACT_STATUSES)
    )
    return db.scalar(query) or 0


def cta_counts(db: Session, engagement_id: uuid.UUID) -> dict[CtaStatus, int]:
    rows = db.execute(select(Cta.status, func.count()).where(Cta.engagement_id == engagement_id).group_by(Cta.status)).all()
    return {status: count for status, count in rows}


def cta_counts_by_session(db: Session, engagement_id: uuid.UUID) -> dict[uuid.UUID, dict[CtaStatus, int]]:
    rows = db.execute(
        select(Cta.session_id, Cta.status, func.count()).where(Cta.engagement_id == engagement_id).group_by(Cta.session_id, Cta.status)
    ).all()
    result: dict[uuid.UUID, dict[CtaStatus, int]] = {}
    for session_id, status, count in rows:
        result.setdefault(session_id, {})[status] = count
    return result


def cta_counts_by_pod(db: Session, engagement_id: uuid.UUID) -> dict[uuid.UUID, dict[CtaStatus, int]]:
    rows = db.execute(
        select(Participant.pod_id, Cta.status, func.count())
        .join(Participant, Participant.id == Cta.participant_id)
        .where(Cta.engagement_id == engagement_id, Participant.pod_id.is_not(None))
        .group_by(Participant.pod_id, Cta.status)
    ).all()
    result: dict[uuid.UUID, dict[CtaStatus, int]] = {}
    for pod_id, status, count in rows:
        result.setdefault(pod_id, {})[status] = count
    return result
