from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.engagement import Engagement
from app.models.enums import Role
from app.models.user import User


def list_for_user(db: Session, user: User) -> list[Engagement]:
    query = select(Engagement).order_by(Engagement.name)
    if user.role != Role.SYNER_ADMIN:
        query = query.where(Engagement.organization_id == user.organization_id)
    return list(db.scalars(query))
