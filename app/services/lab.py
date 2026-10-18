from collections.abc import Callable

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.crud import lab as lab_crud
from app.models.engagement import Engagement
from app.models.enums import LAB_SESSION_NAMES, LAB_SESSION_THEMES, ActivityAction
from app.models.lab import LabSession, Pod
from app.models.user import User
from app.schemas.common import updates
from app.schemas.lab import LabSessionCreate, LabSessionUpdate, PodCreate, PodUpdate
from app.services.activity import diff_changes, log_activity


def _log(db: Session, *, user: User, engagement: Engagement, action: ActivityAction, entity_type: str, entity_id, summary: str, changes=None) -> None:
    """Toda la actividad del Lab es internal_only: nombres de participantes y textos de CTAs solo los ve Syner."""
    log_activity(
        db, user=user, engagement=engagement, action=action, entity_type=entity_type, entity_id=entity_id,
        summary=summary, changes=changes, internal_only=True,
    )


def _apply_update(db: Session, *, user: User, engagement: Engagement, entity, payload: dict, entity_type: str, label: Callable[[], str]) -> bool:
    """Aplica un PATCH ya validado y registra activity. Devuelve False si no hubo cambios."""
    changes = diff_changes(entity, payload)
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
