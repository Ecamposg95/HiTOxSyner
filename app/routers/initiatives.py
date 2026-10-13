from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import initiatives as initiatives_crud
from app.database import get_db
from app.dependencies import get_engagement, require_roles, scoped
from app.models.engagement import Engagement
from app.models.enums import InitiativeStatus, Role
from app.models.initiative import Initiative
from app.models.user import User
from app.schemas.common import Page, Pagination, pagination_params
from app.schemas.initiative import InitiativeCreate, InitiativeRead, InitiativeUpdate
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
