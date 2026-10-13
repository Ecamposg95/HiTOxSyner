import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import actions as actions_crud
from app.database import get_db
from app.dependencies import get_current_user, get_engagement, require_roles, scoped
from app.models.action import Action
from app.models.engagement import Engagement
from app.models.enums import ActionStatus, Role
from app.models.user import User
from app.schemas.action import ActionCreate, ActionRead, ActionUpdate
from app.schemas.common import Page, Pagination, pagination_params
from app.services import actions as actions_service

router = APIRouter(tags=["actions"])
syner_only = Depends(require_roles(Role.SYNER_ADMIN))
scoped_action = Depends(scoped(Action, "action_id"))


@router.get("/engagements/{engagement_id}/actions", response_model=Page[ActionRead])
def list_actions(
    engagement: Engagement = Depends(get_engagement),
    user: User = Depends(get_current_user),
    status: ActionStatus | None = None,
    initiative_id: uuid.UUID | None = None,
    owner_user_id: uuid.UUID | None = None,
    mine: bool = False,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    if mine:
        owner_user_id = user.id
    items, total = actions_crud.list_for_engagement(
        db, engagement.id, status=status, initiative_id=initiative_id, owner_user_id=owner_user_id,
        limit=pagination.limit, offset=pagination.offset,
    )
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/actions", response_model=ActionRead, status_code=201)
def create_action(
    data: ActionCreate,
    user: User = syner_only,
    engagement: Engagement = Depends(get_engagement),
    db: Session = Depends(get_db),
):
    return actions_service.create_action(db, user=user, engagement=engagement, data=data)


@router.patch("/actions/{action_id}", response_model=ActionRead)
def update_action(
    data: ActionUpdate,
    action: Action = scoped_action,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role == Role.SYNER_ADMIN:
        payload = data
    elif user.role == Role.HITO_COLLABORATOR and action.owner_user_id == user.id:
        payload = ActionUpdate(**data.model_dump(include={"status", "evidence"}, exclude_unset=True))
    else:
        raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")
    return actions_service.update_action(db, user=user, action=action, data=payload)
