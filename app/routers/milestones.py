import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import milestones as milestones_crud
from app.database import get_db
from app.dependencies import get_engagement, require_roles, scoped
from app.models.engagement import Engagement
from app.models.enums import MilestoneStatus, RoadmapPhase, Role
from app.models.milestone import Milestone
from app.models.user import User
from app.schemas.common import Page, Pagination, pagination_params
from app.schemas.milestone import MilestoneCreate, MilestoneRead, MilestoneUpdate
from app.services import milestones as milestones_service

router = APIRouter(tags=["milestones"])
syner_only = Depends(require_roles(Role.SYNER_ADMIN))
scoped_milestone = Depends(scoped(Milestone, "milestone_id"))


@router.get("/engagements/{engagement_id}/milestones", response_model=Page[MilestoneRead])
def list_milestones(
    engagement: Engagement = Depends(get_engagement),
    phase: RoadmapPhase | None = None,
    status: MilestoneStatus | None = None,
    initiative_id: uuid.UUID | None = None,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = milestones_crud.list_for_engagement(
        db, engagement.id, phase=phase, status=status, initiative_id=initiative_id,
        limit=pagination.limit, offset=pagination.offset,
    )
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/milestones", response_model=MilestoneRead, status_code=201)
def create_milestone(
    data: MilestoneCreate,
    user: User = syner_only,
    engagement: Engagement = Depends(get_engagement),
    db: Session = Depends(get_db),
):
    return milestones_service.create_milestone(db, user=user, engagement=engagement, data=data)


@router.get("/milestones/{milestone_id}", response_model=MilestoneRead)
def read_milestone(milestone: Milestone = scoped_milestone):
    return milestone


@router.patch("/milestones/{milestone_id}", response_model=MilestoneRead)
def update_milestone(
    data: MilestoneUpdate,
    user: User = syner_only,
    milestone: Milestone = scoped_milestone,
    db: Session = Depends(get_db),
):
    return milestones_service.update_milestone(db, user=user, milestone=milestone, data=data)
