import uuid

from fastapi import Cookie, Depends, Header, HTTPException, Path
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.models.engagement import Engagement
from app.models.enums import Role
from app.models.user import User

COOKIE_NAME = "access_token"


def get_current_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    access_token: str | None = Cookie(default=None),
) -> User:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif access_token:
        token = access_token
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_access_token(token)
        user_id = uuid.UUID(str(payload.get("sub", "")))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


def can_access_organization(user: User, organization_id: uuid.UUID) -> bool:
    return user.role == Role.SYNER_ADMIN or user.organization_id == organization_id


def require_roles(*roles: Role):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")
        return user

    return dependency


def get_engagement(
    engagement_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Engagement:
    engagement = db.get(Engagement, engagement_id)
    if engagement is None or not can_access_organization(user, engagement.organization_id):
        raise HTTPException(status_code=404, detail="Engagement not found")
    return engagement


def scoped(model, param: str):
    """Dependencia que carga una entidad por id y verifica acceso por organización (404 si no)."""

    def dependency(
        entity_id: uuid.UUID = Path(alias=param),
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        obj = db.get(model, entity_id)
        if obj is None or not can_access_organization(user, obj.organization_id):
            raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
        return obj

    return dependency
