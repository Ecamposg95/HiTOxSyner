import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def get(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def list_by_organization(db: Session, organization_id: uuid.UUID) -> list[User]:
    return list(db.scalars(select(User).where(User.organization_id == organization_id).order_by(User.full_name)))


def create(db: Session, **fields) -> User:
    fields["email"] = fields["email"].lower()
    user = User(**fields)
    db.add(user)
    db.flush()
    return user
