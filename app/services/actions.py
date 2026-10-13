from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.action import Action
from app.models.engagement import Engagement
from app.models.enums import ActivityAction, Role
from app.models.initiative import Initiative
from app.models.user import User
from app.schemas.action import ActionCreate, ActionUpdate
from app.schemas.common import updates
from app.services.activity import diff_changes, log_activity


def _validate_links(db: Session, engagement: Engagement, payload: dict) -> None:
    """initiative_id debe ser del mismo engagement; owner_user_id debe ser de la organización del engagement o un SYNER_ADMIN."""
    initiative_id = payload.get("initiative_id")
    if initiative_id is not None:
        initiative = db.get(Initiative, initiative_id)
        if initiative is None or initiative.engagement_id != engagement.id:
            raise HTTPException(status_code=422, detail="initiative_id no pertenece a este engagement")
    owner_id = payload.get("owner_user_id")
    if owner_id is not None:
        owner = db.get(User, owner_id)
        if owner is None or (owner.organization_id != engagement.organization_id and owner.role != Role.SYNER_ADMIN):
            raise HTTPException(status_code=422, detail="owner_user_id no pertenece a este engagement")


def _resolve_owner_name(db: Session, payload: dict) -> None:
    owner_id = payload.get("owner_user_id")
    if owner_id and not payload.get("owner_name"):
        owner = db.get(User, owner_id)
        if owner is not None:
            payload["owner_name"] = owner.full_name


def create_action(db: Session, *, user: User, engagement: Engagement, data: ActionCreate) -> Action:
    payload = data.model_dump()
    _validate_links(db, engagement, payload)
    _resolve_owner_name(db, payload)
    action = Action(organization_id=engagement.organization_id, engagement_id=engagement.id, created_by=user.id, **payload)
    db.add(action)
    db.flush()
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="action",
        entity_id=action.id, summary=f'{user.full_name} created Action "{action.title}"',
    )
    db.commit()
    db.refresh(action)
    return action


def update_action(db: Session, *, user: User, action: Action, data: ActionUpdate) -> Action:
    payload = updates(data, nullable={"owner_user_id", "initiative_id", "due_date"})
    engagement = db.get(Engagement, action.engagement_id)
    _validate_links(db, engagement, payload)
    _resolve_owner_name(db, payload)
    changes = diff_changes(action, payload)
    if not changes:
        return action
    for field, value in payload.items():
        setattr(action, field, value)
    status_change = next((c for c in changes if c["field"] == "status"), None)
    if status_change:
        activity_action = ActivityAction.STATUS_CHANGED
        summary = f'{user.full_name} updated Action "{action.title}" from {status_change["before"]} to {status_change["after"]}'
    else:
        activity_action = ActivityAction.UPDATED
        summary = f'{user.full_name} updated Action "{action.title}"'
    log_activity(
        db, user=user, engagement=engagement, action=activity_action, entity_type="action",
        entity_id=action.id, summary=summary, changes=changes,
    )
    db.commit()
    db.refresh(action)
    return action
