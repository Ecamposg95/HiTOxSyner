import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import lab as lab_crud
from app.database import get_db
from app.dependencies import get_engagement, require_roles, scoped
from app.models.engagement import Engagement
from app.models.enums import ContractStatus, CtaStatus, Role
from app.models.lab import ActionContract, Cta, LabSession, Participant, Pod
from app.models.user import User
from app.schemas.common import Page, Pagination, pagination_params
from app.schemas.lab import (
    ActionContractCreate, ActionContractRead, ActionContractUpdate, CtaCreate, CtaRead, CtaUpdate, LabSessionCreate, LabSessionRead, LabSessionUpdate, ParticipantCreate, ParticipantRead,
    ParticipantUpdate, PodCreate, PodRead, PodUpdate,
)
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


scoped_participant = Depends(scoped(Participant, "participant_id"))
scoped_cta = Depends(scoped(Cta, "cta_id"))


@router.get("/engagements/{engagement_id}/lab/participants", response_model=Page[ParticipantRead])
def list_participants(
    engagement: Engagement = Depends(get_engagement),
    _: User = syner_only,
    pod_id: uuid.UUID | None = None,
    is_active: bool | None = None,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = lab_crud.list_participants(db, engagement.id, pod_id=pod_id, is_active=is_active, limit=pagination.limit, offset=pagination.offset)
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/lab/participants", response_model=ParticipantRead, status_code=201)
def create_participant(
    data: ParticipantCreate,
    engagement: Engagement = Depends(get_engagement),
    user: User = syner_only,
    db: Session = Depends(get_db),
):
    return lab_service.create_participant(db, user=user, engagement=engagement, data=data)


@router.patch("/lab/participants/{participant_id}", response_model=ParticipantRead)
def update_participant(
    data: ParticipantUpdate,
    participant: Participant = scoped_participant,
    user: User = syner_only,
    db: Session = Depends(get_db),
):
    return lab_service.update_participant(db, user=user, participant=participant, data=data)


@router.get("/engagements/{engagement_id}/lab/ctas", response_model=Page[CtaRead])
def list_ctas(
    engagement: Engagement = Depends(get_engagement),
    _: User = syner_only,
    session_id: uuid.UUID | None = None,
    pod_id: uuid.UUID | None = None,
    status: CtaStatus | None = None,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = lab_crud.list_ctas(
        db, engagement.id, session_id=session_id, pod_id=pod_id, status=status, limit=pagination.limit, offset=pagination.offset,
    )
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/lab/ctas", response_model=CtaRead, status_code=201)
def create_cta(
    data: CtaCreate,
    engagement: Engagement = Depends(get_engagement),
    user: User = syner_only,
    db: Session = Depends(get_db),
):
    return lab_service.create_cta(db, user=user, engagement=engagement, data=data)


@router.patch("/lab/ctas/{cta_id}", response_model=CtaRead)
def update_cta(
    data: CtaUpdate,
    cta: Cta = scoped_cta,
    user: User = syner_only,
    db: Session = Depends(get_db),
):
    return lab_service.update_cta(db, user=user, cta=cta, data=data)


scoped_contract = Depends(scoped(ActionContract, "contract_id"))


@router.get("/engagements/{engagement_id}/lab/contracts", response_model=Page[ActionContractRead])
def list_contracts(
    engagement: Engagement = Depends(get_engagement),
    _: User = syner_only,
    status: ContractStatus | None = None,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = lab_crud.list_contracts(db, engagement.id, status=status, limit=pagination.limit, offset=pagination.offset)
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/lab/contracts", response_model=ActionContractRead, status_code=201)
def create_contract(
    data: ActionContractCreate,
    engagement: Engagement = Depends(get_engagement),
    user: User = syner_only,
    db: Session = Depends(get_db),
):
    return lab_service.create_contract(db, user=user, engagement=engagement, data=data)


@router.patch("/lab/contracts/{contract_id}", response_model=ActionContractRead)
def update_contract(
    data: ActionContractUpdate,
    contract: ActionContract = scoped_contract,
    user: User = syner_only,
    db: Session = Depends(get_db),
):
    return lab_service.update_contract(db, user=user, contract=contract, data=data)
