from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import lab as lab_crud
from app.database import get_db
from app.dependencies import get_engagement, require_roles, scoped
from app.models.engagement import Engagement
from app.models.enums import Role
from app.models.lab import LabSession, Pod
from app.models.user import User
from app.schemas.common import Page, Pagination, pagination_params
from app.schemas.lab import LabSessionCreate, LabSessionRead, LabSessionUpdate, PodCreate, PodRead, PodUpdate
from app.services import lab as lab_service

router = APIRouter(tags=["lab"])

# Orden de dependencias: el engagement o la entidad (404 para otra organización) se resuelve antes que el rol (403).
syner_only = Depends(require_roles(Role.SYNER_ADMIN))
scoped_session = Depends(scoped(LabSession, "session_id"))
scoped_pod = Depends(scoped(Pod, "pod_id"))


@router.get("/engagements/{engagement_id}/lab/sessions", response_model=Page[LabSessionRead])
def list_sessions(
    engagement: Engagement = Depends(get_engagement),
    _: User = syner_only,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = lab_crud.list_sessions(db, engagement.id, limit=pagination.limit, offset=pagination.offset)
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/lab/sessions", response_model=LabSessionRead, status_code=201)
def create_session(
    data: LabSessionCreate,
    engagement: Engagement = Depends(get_engagement),
    user: User = syner_only,
    db: Session = Depends(get_db),
):
    return lab_service.create_session(db, user=user, engagement=engagement, data=data)


@router.patch("/lab/sessions/{session_id}", response_model=LabSessionRead)
def update_session(
    data: LabSessionUpdate,
    session: LabSession = scoped_session,
    user: User = syner_only,
    db: Session = Depends(get_db),
):
    return lab_service.update_session(db, user=user, session=session, data=data)


@router.get("/engagements/{engagement_id}/lab/pods", response_model=Page[PodRead])
def list_pods(
    engagement: Engagement = Depends(get_engagement),
    _: User = syner_only,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = lab_crud.list_pods(db, engagement.id, limit=pagination.limit, offset=pagination.offset)
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/lab/pods", response_model=PodRead, status_code=201)
def create_pod(
    data: PodCreate,
    engagement: Engagement = Depends(get_engagement),
    user: User = syner_only,
    db: Session = Depends(get_db),
):
    return lab_service.create_pod(db, user=user, engagement=engagement, data=data)


@router.patch("/lab/pods/{pod_id}", response_model=PodRead)
def update_pod(
    data: PodUpdate,
    pod: Pod = scoped_pod,
    user: User = syner_only,
    db: Session = Depends(get_db),
):
    return lab_service.update_pod(db, user=user, pod=pod, data=data)
