from collections.abc import Callable
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.crud import lab as lab_crud
from app.models.engagement import Engagement
from app.models.enums import LAB_SESSION_NAMES, LAB_SESSION_THEMES, ActivityAction
from app.models.lab import ActionContract, ActionContractCta, Cta, LabSession, Participant, Pod
from app.models.user import User
from app.schemas.common import updates
from app.schemas.lab import ActionContractCreate, ActionContractUpdate, CtaCreate, CtaUpdate, LabSessionCreate, LabSessionUpdate, ParticipantCreate, ParticipantUpdate, PodCreate, PodUpdate
from app.services.activity import diff_changes, log_activity
from app.services.links import require_in_engagement


def _log(db: Session, *, user: User, engagement: Engagement, action: ActivityAction, entity_type: str, entity_id, summary: str, changes=None) -> None:
    """Toda la actividad del Lab es internal_only: nombres de participantes y textos de CTAs solo los ve Syner."""
    log_activity(
        db, user=user, engagement=engagement, action=action, entity_type=entity_type, entity_id=entity_id,
        summary=summary, changes=changes, internal_only=True,
    )


def _apply_update(db: Session, *, user: User, engagement: Engagement, entity, payload: dict, entity_type: str, label: Callable[[], str], extra_changes: list[dict] | None = None) -> bool:
    """Aplica un PATCH ya validado y registra activity. Devuelve False si no hubo cambios."""
    changes = diff_changes(entity, payload) + list(extra_changes or [])
    if not changes:
        return False
    for field, value in payload.items():
        setattr(entity, field, value)
    status_change = next((c for c in changes if c["field"] == "status"), None)
    if status_change:
        action = ActivityAction.STATUS_CHANGED
        summary = f'{user.full_name} updated {label()} from {status_change["before"]} to {status_change["after"]}'
    else:
        action = ActivityAction.UPDATED
        summary = f'{user.full_name} updated {label()}'
    _log(db, user=user, engagement=engagement, action=action, entity_type=entity_type, entity_id=entity.id, summary=summary, changes=changes)
    return True


def _scoped_kwargs(engagement: Engagement, user: User) -> dict:
    return dict(organization_id=engagement.organization_id, engagement_id=engagement.id, created_by=user.id)


# --- Sessions ---------------------------------------------------------------

def session_label(session: LabSession) -> str:
    return f'Lab Session {session.number} "{session.name}"'


def create_session(db: Session, *, user: User, engagement: Engagement, data: LabSessionCreate) -> LabSession:
    if lab_crud.get_session_by_number(db, engagement.id, data.number) is not None:
        raise HTTPException(status_code=409, detail=f"La sesión {data.number} ya existe en este engagement")
    payload = data.model_dump()
    payload["name"] = payload["name"] or LAB_SESSION_NAMES[data.number]
    payload["theme"] = payload["theme"] or LAB_SESSION_THEMES[data.number]
    session = LabSession(**_scoped_kwargs(engagement, user), **payload)
    db.add(session)
    db.flush()
    _log(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="lab_session",
        entity_id=session.id, summary=f"{user.full_name} created {session_label(session)}",
    )
    db.commit()
    db.refresh(session)
    return session


def update_session(db: Session, *, user: User, session: LabSession, data: LabSessionUpdate) -> LabSession:
    payload = updates(data, nullable={"held_on", "attendance_count"})
    engagement = db.get(Engagement, session.engagement_id)
    if _apply_update(db, user=user, engagement=engagement, entity=session, payload=payload, entity_type="lab_session", label=lambda: session_label(session)):
        db.commit()
        db.refresh(session)
    return session


# --- Pods -------------------------------------------------------------------

def create_pod(db: Session, *, user: User, engagement: Engagement, data: PodCreate) -> Pod:
    if lab_crud.get_pod_by_number(db, engagement.id, data.number) is not None:
        raise HTTPException(status_code=409, detail=f"El pod {data.number} ya existe en este engagement")
    pod = Pod(**_scoped_kwargs(engagement, user), **data.model_dump())
    db.add(pod)
    db.flush()
    _log(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="pod",
        entity_id=pod.id, summary=f'{user.full_name} created Pod "{pod.name}"',
    )
    db.commit()
    db.refresh(pod)
    return pod


def update_pod(db: Session, *, user: User, pod: Pod, data: PodUpdate) -> Pod:
    payload = updates(data)
    engagement = db.get(Engagement, pod.engagement_id)
    new_number = payload.get("number")
    if new_number is not None and new_number != pod.number and lab_crud.get_pod_by_number(db, engagement.id, new_number) is not None:
        raise HTTPException(status_code=409, detail=f"El pod {new_number} ya existe en este engagement")
    if _apply_update(db, user=user, engagement=engagement, entity=pod, payload=payload, entity_type="pod", label=lambda: f'Pod "{pod.name}"'):
        db.commit()
        db.refresh(pod)
    return pod


# --- Participants -----------------------------------------------------------

def create_participant(db: Session, *, user: User, engagement: Engagement, data: ParticipantCreate) -> Participant:
    require_in_engagement(db, Pod, data.pod_id, engagement, "pod_id")
    participant = Participant(**_scoped_kwargs(engagement, user), **data.model_dump())
    db.add(participant)
    db.flush()
    _log(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="participant",
        entity_id=participant.id, summary=f'{user.full_name} created Participant "{participant.full_name}"',
    )
    db.commit()
    db.refresh(participant)
    return participant


def update_participant(db: Session, *, user: User, participant: Participant, data: ParticipantUpdate) -> Participant:
    payload = updates(data, nullable={"pod_id"})
    engagement = db.get(Engagement, participant.engagement_id)
    require_in_engagement(db, Pod, payload.get("pod_id"), engagement, "pod_id")
    if _apply_update(db, user=user, engagement=engagement, entity=participant, payload=payload, entity_type="participant", label=lambda: f'Participant "{participant.full_name}"'):
        db.commit()
        db.refresh(participant)
    return participant


# --- CTAs -------------------------------------------------------------------

def cta_label(db: Session, cta: Cta) -> str:
    participant = db.get(Participant, cta.participant_id)
    return f'CTA of Participant "{participant.full_name}"'


def create_cta(db: Session, *, user: User, engagement: Engagement, data: CtaCreate) -> Cta:
    participant = require_in_engagement(db, Participant, data.participant_id, engagement, "participant_id")
    session = require_in_engagement(db, LabSession, data.session_id, engagement, "session_id")
    cta = Cta(**_scoped_kwargs(engagement, user), **data.model_dump())
    db.add(cta)
    db.flush()
    _log(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="cta", entity_id=cta.id,
        summary=f'{user.full_name} created CTA for Participant "{participant.full_name}" in Lab Session {session.number}',
    )
    db.commit()
    db.refresh(cta)
    return cta


def update_cta(db: Session, *, user: User, cta: Cta, data: CtaUpdate) -> Cta:
    payload = updates(data, nullable={"due_date"})
    engagement = db.get(Engagement, cta.engagement_id)
    require_in_engagement(db, Participant, payload.get("participant_id"), engagement, "participant_id")
    require_in_engagement(db, LabSession, payload.get("session_id"), engagement, "session_id")
    if _apply_update(db, user=user, engagement=engagement, entity=cta, payload=payload, entity_type="cta", label=lambda: cta_label(db, cta)):
        db.commit()
        db.refresh(cta)
    return cta


# --- Leadership Action Contracts -------------------------------------------

REVIEW_OFFSETS = (("review_30_date", 30), ("review_60_date", 60))


def _contract_label(db: Session, contract: ActionContract) -> str:
    participant = db.get(Participant, contract.participant_id)
    return f'Action Contract of Participant "{participant.full_name}"'


def _validate_contract_ctas(db: Session, engagement: Engagement, participant_id, cta_ids: list) -> list:
    """Dedup, pertenencia al engagement y al participante del contrato. El máximo de 3 lo impone el schema."""
    unique_ids = list(dict.fromkeys(cta_ids))
    for cta_id in unique_ids:
        cta = require_in_engagement(db, Cta, cta_id, engagement, "cta_ids")
        if cta.participant_id != participant_id:
            raise HTTPException(status_code=422, detail="cta_ids deben pertenecer al participante del contrato")
    return unique_ids


def _fill_review_dates(payload: dict, *, only_missing: bool) -> None:
    start = payload.get("start_date")
    if start is None:
        return
    for field, days in REVIEW_OFFSETS:
        if only_missing and field in payload:
            continue
        if payload.get(field) is None:
            payload[field] = start + timedelta(days=days)


def _sync_contract_ctas(contract: ActionContract, cta_ids: list) -> None:
    """Quita y añade vínculos sin recrear los que se mantienen (evita chocar con uq_action_contract_ctas)."""
    current = {link.cta_id: link for link in contract.ctas}
    for cta_id, link in current.items():
        if cta_id not in cta_ids:
            contract.ctas.remove(link)
    for cta_id in cta_ids:
        if cta_id not in current:
            contract.ctas.append(ActionContractCta(cta_id=cta_id))


def create_contract(db: Session, *, user: User, engagement: Engagement, data: ActionContractCreate) -> ActionContract:
    participant = require_in_engagement(db, Participant, data.participant_id, engagement, "participant_id")
    if lab_crud.get_contract_by_participant(db, engagement.id, participant.id) is not None:
        raise HTTPException(status_code=409, detail="El participante ya tiene un Leadership Action Contract")
    cta_ids = _validate_contract_ctas(db, engagement, participant.id, data.cta_ids)
    payload = data.model_dump(exclude={"cta_ids"})
    _fill_review_dates(payload, only_missing=False)
    contract = ActionContract(**_scoped_kwargs(engagement, user), **payload)
    contract.ctas = [ActionContractCta(cta_id=cta_id) for cta_id in cta_ids]
    db.add(contract)
    db.flush()
    _log(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="action_contract",
        entity_id=contract.id, summary=f'{user.full_name} created Action Contract for Participant "{participant.full_name}"',
    )
    db.commit()
    db.refresh(contract)
    return contract


def update_contract(db: Session, *, user: User, contract: ActionContract, data: ActionContractUpdate) -> ActionContract:
    payload = updates(data, nullable={"start_date", "review_30_date", "review_60_date"})
    engagement = db.get(Engagement, contract.engagement_id)
    participant_id = payload.get("participant_id", contract.participant_id)
    if participant_id != contract.participant_id:
        require_in_engagement(db, Participant, participant_id, engagement, "participant_id")
        if lab_crud.get_contract_by_participant(db, engagement.id, participant_id) is not None:
            raise HTTPException(status_code=409, detail="El participante ya tiene un Leadership Action Contract")
    requested_ids = payload.pop("cta_ids", None)
    cta_ids = _validate_contract_ctas(db, engagement, participant_id, requested_ids if requested_ids is not None else contract.cta_ids)
    if "start_date" in payload:
        _fill_review_dates(payload, only_missing=True)
    extra = []
    if set(cta_ids) != set(contract.cta_ids):
        extra.append({"field": "cta_ids", "before": [str(i) for i in contract.cta_ids], "after": [str(i) for i in cta_ids]})
    changed = _apply_update(
        db, user=user, engagement=engagement, entity=contract, payload=payload, entity_type="action_contract",
        label=lambda: _contract_label(db, contract), extra_changes=extra,
    )
    if not changed:
        return contract
    _sync_contract_ctas(contract, cta_ids)
    db.commit()
    db.refresh(contract)
    return contract
