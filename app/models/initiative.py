import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import EngagementScopedMixin, db_enum
from app.models.enums import InitiativeStatus, Level


class Initiative(EngagementScopedMixin, Base):
    __tablename__ = "initiatives"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    objective: Mapped[str] = mapped_column(Text, default="", nullable=False)
    expected_outcome: Mapped[str] = mapped_column(Text, default="", nullable=False)
    hito_owner: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    syner_owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    area: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    priority: Mapped[Level] = mapped_column(db_enum(Level, "initiative_priority"), default=Level.MEDIUM, nullable=False)
    status: Mapped[InitiativeStatus] = mapped_column(
        db_enum(InitiativeStatus, "initiative_status"), default=InitiativeStatus.DISCOVERY, nullable=False
    )
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    progress_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expected_impact: Mapped[str] = mapped_column(Text, default="", nullable=False)
    kpis: Mapped[str] = mapped_column(Text, default="", nullable=False)
    risks: Mapped[str] = mapped_column(Text, default="", nullable=False)
    dependencies: Mapped[str] = mapped_column(Text, default="", nullable=False)
