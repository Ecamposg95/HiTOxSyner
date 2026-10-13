from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import findings as findings_crud
from app.database import get_db
from app.dependencies import get_engagement, require_roles, scoped
from app.models.engagement import Engagement
from app.models.enums import FindingStatus, FindingType, Role
from app.models.finding import Finding
from app.models.user import User
from app.schemas.common import Page, Pagination, pagination_params
from app.schemas.finding import FindingCreate, FindingRead, FindingUpdate
from app.services import findings as findings_service

router = APIRouter(tags=["findings"])
syner_only = Depends(require_roles(Role.SYNER_ADMIN))
scoped_finding = Depends(scoped(Finding, "finding_id"))


@router.get("/engagements/{engagement_id}/findings", response_model=Page[FindingRead])
def list_findings(
    engagement: Engagement = Depends(get_engagement),
    status: FindingStatus | None = None,
    type: FindingType | None = None,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = findings_crud.list_for_engagement(
        db, engagement.id, status=status, type=type, limit=pagination.limit, offset=pagination.offset
    )
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/findings", response_model=FindingRead, status_code=201)
def create_finding(
    data: FindingCreate,
    user: User = syner_only,
    engagement: Engagement = Depends(get_engagement),
    db: Session = Depends(get_db),
):
    return findings_service.create_finding(db, user=user, engagement=engagement, data=data)


@router.get("/findings/{finding_id}", response_model=FindingRead)
def read_finding(finding: Finding = scoped_finding):
    return finding


@router.patch("/findings/{finding_id}", response_model=FindingRead)
def update_finding(
    data: FindingUpdate,
    user: User = syner_only,
    finding: Finding = scoped_finding,
    db: Session = Depends(get_db),
):
    return findings_service.update_finding(db, user=user, finding=finding, data=data)
