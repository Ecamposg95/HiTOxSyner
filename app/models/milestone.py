import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import EngagementScopedMixin, db_enum
from app.models.enums import MilestoneStatus, RoadmapPhase


class Milestone(EngagementScopedMixin, Base):
    __tablename__ = "milestones"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    phase: Mapped[RoadmapPhase] = mapped_column(db_enum(RoadmapPhase, "milestone_phase"), default=RoadmapPhase.DISCOVER, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[MilestoneStatus] = mapped_column(
        db_enum(MilestoneStatus, "milestone_status"), default=MilestoneStatus.PLANNED, nullable=False
    )
    owner: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    initiative_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("initiatives.id"), index=True, nullable=True)
    deliverable: Mapped[str] = mapped_column(Text, default="", nullable=False)
