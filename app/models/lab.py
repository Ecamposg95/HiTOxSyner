import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import EngagementScopedMixin, db_enum
from app.models.enums import ContractStatus, CtaStatus, LabSessionStatus, LabSessionTheme


class LabSession(EngagementScopedMixin, Base):
    __tablename__ = "lab_sessions"
    __table_args__ = (UniqueConstraint("engagement_id", "number", name="uq_lab_sessions_engagement_number"),)

    number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    theme: Mapped[LabSessionTheme] = mapped_column(db_enum(LabSessionTheme, "lab_session_theme"), nullable=False)
    held_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[LabSessionStatus] = mapped_column(
        db_enum(LabSessionStatus, "lab_session_status"), default=LabSessionStatus.PLANNED, nullable=False
    )
    attendance_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    syner_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)


class Pod(EngagementScopedMixin, Base):
    __tablename__ = "pods"
    __table_args__ = (UniqueConstraint("engagement_id", "number", name="uq_pods_engagement_number"),)

    number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)


class Participant(EngagementScopedMixin, Base):
    __tablename__ = "participants"

    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    area: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    title: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    pod_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("pods.id"), index=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Cta(EngagementScopedMixin, Base):
    __tablename__ = "ctas"

    participant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("participants.id"), index=True, nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lab_sessions.id"), index=True, nullable=False)
    trigger: Mapped[str] = mapped_column(Text, default="", nullable=False)
    behavior: Mapped[str] = mapped_column(Text, nullable=False)
    stakeholder: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    evidence_expected: Mapped[str] = mapped_column(Text, default="", nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    accountability_partner: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    impact: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[CtaStatus] = mapped_column(db_enum(CtaStatus, "cta_status"), default=CtaStatus.COMMITTED, nullable=False)
    evidence_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)


class ActionContract(EngagementScopedMixin, Base):
    __tablename__ = "action_contracts"
    __table_args__ = (UniqueConstraint("engagement_id", "participant_id", name="uq_action_contracts_participant"),)

    participant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("participants.id"), index=True, nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_30_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_60_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    success_signal: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[ContractStatus] = mapped_column(
        db_enum(ContractStatus, "action_contract_status"), default=ContractStatus.DRAFT, nullable=False
    )

    ctas: Mapped[list["ActionContractCta"]] = relationship(
        "ActionContractCta", back_populates="contract", lazy="selectin", cascade="all, delete-orphan",
        order_by="ActionContractCta.created_at",
    )

    @property
    def cta_ids(self) -> list[uuid.UUID]:
        return [link.cta_id for link in self.ctas]


class ActionContractCta(Base):
    __tablename__ = "action_contract_ctas"
    __table_args__ = (UniqueConstraint("contract_id", "cta_id", name="uq_action_contract_ctas"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    contract_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("action_contracts.id", ondelete="CASCADE"), index=True, nullable=False)
    cta_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ctas.id"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    contract: Mapped[ActionContract] = relationship(ActionContract, back_populates="ctas")
