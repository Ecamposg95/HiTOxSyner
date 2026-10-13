import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.crud import engagements as engagements_crud
from app.crud import users as users_crud
from app.database import get_db
from app.dependencies import get_current_user, get_engagement, require_roles
from app.models.engagement import Engagement
from app.models.enums import Role
from app.models.user import User
from app.schemas.engagement import EngagementRead, EngagementUpdate
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/engagements", tags=["engagements"])
syner_only = Depends(require_roles(Role.SYNER_ADMIN))


@router.get("", response_model=list[EngagementRead])
def list_engagements(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return engagements_crud.list_for_user(db, user)


@router.get("/{engagement_id}", response_model=EngagementRead)
def read_engagement(engagement: Engagement = Depends(get_engagement)):
    return engagement


@router.patch("/{engagement_id}", response_model=EngagementRead)
def update_engagement(
    data: EngagementUpdate,
    user: User = syner_only,
    engagement: Engagement = Depends(get_engagement),
    db: Session = Depends(get_db),
):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(engagement, field, value)
    db.commit()
    db.refresh(engagement)
    return engagement


@router.get("/{engagement_id}/users", response_model=list[UserRead])
def list_users(user: User = syner_only, engagement: Engagement = Depends(get_engagement), db: Session = Depends(get_db)):
    return [UserRead.from_user(u) for u in users_crud.list_by_organization(db, engagement.organization_id)]


@router.post("/{engagement_id}/users", response_model=UserRead, status_code=201)
def create_user(
    data: UserCreate,
    user: User = syner_only,
    engagement: Engagement = Depends(get_engagement),
    db: Session = Depends(get_db),
):
    if data.role == Role.SYNER_ADMIN:
        raise HTTPException(status_code=422, detail="Un engagement de cliente solo admite roles HITO_EXECUTIVE o HITO_COLLABORATOR")
    if users_crud.get_by_email(db, data.email) is not None:
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese email")
    created = users_crud.create(
        db,
        organization_id=engagement.organization_id,
        email=data.email,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.commit()
    db.refresh(created)
    return UserRead.from_user(created)


@router.patch("/{engagement_id}/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    user: User = syner_only,
    engagement: Engagement = Depends(get_engagement),
    db: Session = Depends(get_db),
):
    target = users_crud.get(db, user_id)
    if target is None or target.organization_id != engagement.organization_id:
        raise HTTPException(status_code=404, detail="User not found")
    if data.role == Role.SYNER_ADMIN:
        raise HTTPException(status_code=422, detail="Un engagement de cliente solo admite roles HITO_EXECUTIVE o HITO_COLLABORATOR")
    payload = data.model_dump(exclude_unset=True)
    if "password" in payload:
        target.password_hash = hash_password(payload.pop("password"))
    for field, value in payload.items():
        setattr(target, field, value)
    db.commit()
    db.refresh(target)
    return UserRead.from_user(target)
