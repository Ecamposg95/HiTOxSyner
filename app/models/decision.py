import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import EngagementScopedMixin, db_enum
from app.models.enums import DecisionStatus


class Decision(EngagementScopedMixin, Base):
    __tablename__ = "decisions"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    context: Mapped[str] = mapped_column(Text, default="", nullable=False)
    alternatives: Mapped[str] = mapped_column(Text, default="", nullable=False)
    syner_recommendation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    final_decision: Mapped[str] = mapped_column(Text, default="", nullable=False)
    owner_name: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    participants: Mapped[str] = mapped_column(Text, default="", nullable=False)
    decided_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    impact: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[DecisionStatus] = mapped_column(
        db_enum(DecisionStatus, "decision_status"), default=DecisionStatus.PROPOSED, nullable=False
    )
    initiative_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("initiatives.id"), index=True, nullable=True)
    meeting_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("meetings.id"), index=True, nullable=True)
