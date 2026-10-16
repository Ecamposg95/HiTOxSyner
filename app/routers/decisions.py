import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import decisions as decisions_crud
from app.database import get_db
from app.dependencies import get_current_user, get_engagement, require_roles, scoped
from app.models.decision import Decision
from app.models.engagement import Engagement
from app.models.enums import RESOLUTION_STATUSES, DecisionStatus, Role
from app.models.user import User
from app.schemas.common import Page, Pagination, pagination_params
from app.schemas.decision import DecisionCreate, DecisionRead, DecisionUpdate
from app.services import decisions as decisions_service

router = APIRouter(tags=["decisions"])
syner_only = Depends(require_roles(Role.SYNER_ADMIN))
scoped_decision = Depends(scoped(Decision, "decision_id"))
FORBIDDEN = HTTPException(status_code=403, detail="No tienes permisos para esta acción")


@router.get("/engagements/{engagement_id}/decisions", response_model=Page[DecisionRead])
def list_decisions(
    engagement: Engagement = Depends(get_engagement),
    status: DecisionStatus | None = None,
    initiative_id: uuid.UUID | None = None,
    meeting_id: uuid.UUID | None = None,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = decisions_crud.list_for_engagement(
        db, engagement.id, status=status, initiative_id=initiative_id, meeting_id=meeting_id,
        limit=pagination.limit, offset=pagination.offset,
    )
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/decisions", response_model=DecisionRead, status_code=201)
def create_decision(
    data: DecisionCreate,
    user: User = syner_only,
    engagement: Engagement = Depends(get_engagement),
    db: Session = Depends(get_db),
):
    return decisions_service.create_decision(db, user=user, engagement=engagement, data=data)


@router.get("/decisions/{decision_id}", response_model=DecisionRead)
def read_decision(decision: Decision = scoped_decision):
    return decision


@router.patch("/decisions/{decision_id}", response_model=DecisionRead)
def update_decision(
    data: DecisionUpdate,
    decision: Decision = scoped_decision,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role == Role.HITO_EXECUTIVE:
        sent = data.model_dump(exclude_unset=True)
        if set(sent) != {"status"} or sent["status"] not in RESOLUTION_STATUSES:
            raise FORBIDDEN
    elif user.role != Role.SYNER_ADMIN:
        raise FORBIDDEN
    return decisions_service.update_decision(db, user=user, decision=decision, data=data)
