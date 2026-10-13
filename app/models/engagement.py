import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, db_enum
from app.models.enums import EngagementStatus, Health


class Engagement(TimestampMixin, Base):
    __tablename__ = "engagements"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(300), nullable=True)
    status: Mapped[EngagementStatus] = mapped_column(
        db_enum(EngagementStatus, "engagement_status"), default=EngagementStatus.ACTIVE, nullable=False
    )
    health: Mapped[Health] = mapped_column(db_enum(Health, "engagement_health"), default=Health.ON_TRACK, nullable=False)
    progress_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    executive_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    target_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
