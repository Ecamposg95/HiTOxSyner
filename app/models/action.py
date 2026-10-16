import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import EngagementScopedMixin, db_enum
from app.models.enums import ActionStatus, Level, OrganizationSide


class Action(EngagementScopedMixin, Base):
    __tablename__ = "actions"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
    owner_name: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    organization_side: Mapped[OrganizationSide] = mapped_column(
        db_enum(OrganizationSide, "action_organization_side"), default=OrganizationSide.CLIENT, nullable=False
    )
    initiative_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("initiatives.id"), index=True, nullable=True)
    meeting_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("meetings.id"), index=True, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    priority: Mapped[Level] = mapped_column(db_enum(Level, "action_priority"), default=Level.MEDIUM, nullable=False)
    status: Mapped[ActionStatus] = mapped_column(db_enum(ActionStatus, "action_status"), default=ActionStatus.OPEN, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, default="", nullable=False)
