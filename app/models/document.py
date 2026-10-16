import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import EngagementScopedMixin, db_enum
from app.models.enums import DocumentCategory


class Document(EngagementScopedMixin, Base):
    __tablename__ = "documents"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    category: Mapped[DocumentCategory] = mapped_column(
        db_enum(DocumentCategory, "document_category"), default=DocumentCategory.DISCOVERY, nullable=False
    )
    version: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    url: Mapped[str] = mapped_column(String(2000), default="", nullable=False)
    doc_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    uploader_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(50)), default=list, nullable=False)
    internal_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    links: Mapped[list["DocumentLink"]] = relationship(
        "DocumentLink", back_populates="document", lazy="selectin", cascade="all, delete-orphan", order_by="DocumentLink.created_at"
    )


class DocumentLink(Base):
    __tablename__ = "document_links"
    __table_args__ = (UniqueConstraint("document_id", "entity_type", "entity_id", name="uq_document_links_target"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    document: Mapped[Document] = relationship(Document, back_populates="links")
