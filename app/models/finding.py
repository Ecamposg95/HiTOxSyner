import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import EngagementScopedMixin, db_enum
from app.models.enums import FindingStatus, FindingType, Level


class Finding(EngagementScopedMixin, Base):
    __tablename__ = "findings"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    context: Mapped[str] = mapped_column(Text, default="", nullable=False)
    type: Mapped[FindingType] = mapped_column(db_enum(FindingType, "finding_type"), default=FindingType.FINDING, nullable=False)
    area: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    source: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    impact: Mapped[Level] = mapped_column(db_enum(Level, "finding_impact"), default=Level.MEDIUM, nullable=False)
    severity: Mapped[Level] = mapped_column(db_enum(Level, "finding_severity"), default=Level.MEDIUM, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, default="", nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    syner_owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    found_on: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    status: Mapped[FindingStatus] = mapped_column(db_enum(FindingStatus, "finding_status"), default=FindingStatus.NEW, nullable=False)
    initiative_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("initiatives.id"), index=True, nullable=True)
