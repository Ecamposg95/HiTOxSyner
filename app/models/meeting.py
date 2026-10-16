from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import EngagementScopedMixin


class Meeting(EngagementScopedMixin, Base):
    __tablename__ = "meetings"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    held_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    participants: Mapped[str] = mapped_column(Text, default="", nullable=False)
    objective: Mapped[str] = mapped_column(Text, default="", nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    discussion: Mapped[str] = mapped_column(Text, default="", nullable=False)
    next_steps: Mapped[str] = mapped_column(Text, default="", nullable=False)
