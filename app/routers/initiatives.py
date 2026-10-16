from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import actions as actions_crud
from app.crud import activities as activities_crud
from app.crud import findings as findings_crud
from app.crud import initiatives as initiatives_crud
from app.crud import milestones as milestones_crud
from app.database import get_db
from app.dependencies import get_engagement, require_roles, scoped
from app.models.engagement import Engagement
from app.models.enums import InitiativeStatus, Role
from app.models.initiative import Initiative
from app.models.user import User
from app.schemas.common import Page, Pagination, pagination_params
from app.schemas.action import ActionRead
from app.schemas.activity import ActivityRead
from app.schemas.finding import FindingRead
from app.schemas.milestone import MilestoneRead
from app.schemas.initiative import InitiativeCreate, InitiativeDetail, InitiativeRead, InitiativeUpdate
from app.services import initiatives as initiatives_service

router = APIRouter(tags=["initiatives"])
syner_only = Depends(require_roles(Role.SYNER_ADMIN))
scoped_initiative = Depends(scoped(Initiative, "initiative_id"))


@router.get("/engagements/{engagement_id}/initiatives", response_model=Page[InitiativeRead])
def list_initiatives(
    engagement: Engagement = Depends(get_engagement),
    status: InitiativeStatus | None = None,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = initiatives_crud.list_for_engagement(
        db, engagement.id, status=status, limit=pagination.limit, offset=pagination.offset
    )
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/initiatives", response_model=InitiativeRead, status_code=201)
def create_initiative(
    data: InitiativeCreate,
    user: User = syner_only,
    engagement: Engagement = Depends(get_engagement),
    db: Session = Depends(get_db),
):
    return initiatives_service.create_initiative(db, user=user, engagement=engagement, data=data)


@router.get("/initiatives/{initiative_id}", response_model=InitiativeRead)
def read_initiative(initiative: Initiative = scoped_initiative):
    return initiative


@router.patch("/initiatives/{initiative_id}", response_model=InitiativeRead)
def update_initiative(
    data: InitiativeUpdate,
    user: User = syner_only,
    initiative: Initiative = scoped_initiative,
    db: Session = Depends(get_db),
):
    return initiatives_service.update_initiative(db, user=user, initiative=initiative, data=data)


@router.get("/initiatives/{initiative_id}/detail", response_model=InitiativeDetail)
def initiative_detail(initiative: Initiative = scoped_initiative, db: Session = Depends(get_db)):
    findings = findings_crud.list_by_initiative(db, initiative.id)
    milestones = milestones_crud.list_by_initiative(db, initiative.id)
    actions = actions_crud.list_by_initiative(db, initiative.id)
    own_activity, _ = activities_crud.list_for_engagement(
        db, initiative.engagement_id, entity_type="initiative", entity_id=initiative.id, limit=20
    )
    finding_activity = []
    for finding in findings:
        items, _ = activities_crud.list_for_engagement(
            db, initiative.engagement_id, entity_type="finding", entity_id=finding.id, limit=5
        )
        finding_activity.extend(items)
    activity = sorted(own_activity + finding_activity, key=lambda a: a.created_at, reverse=True)[:20]
    return InitiativeDetail(
        initiative=InitiativeRead.model_validate(initiative),
        findings=[FindingRead.model_validate(f) for f in findings],
        milestones=[MilestoneRead.model_validate(m) for m in milestones],
        actions=[ActionRead.model_validate(a) for a in actions],
        activity=[ActivityRead.model_validate(a) for a in activity],
    )
