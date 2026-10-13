import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import Role


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: Role
    organization_id: uuid.UUID
    organization_name: str
    is_active: bool

    @classmethod
    def from_user(cls, user) -> "UserRead":
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            organization_id=user.organization_id,
            organization_name=user.organization.name,
            is_active=user.is_active,
        )


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=8, max_length=72)
    role: Role


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    password: str | None = Field(default=None, min_length=8, max_length=72)
    role: Role | None = None
    is_active: bool | None = None
