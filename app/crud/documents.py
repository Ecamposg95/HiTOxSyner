import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentLink
from app.models.enums import DocumentCategory


def list_for_engagement(
    db: Session, engagement_id: uuid.UUID, *, category: DocumentCategory | None = None,
    include_internal: bool, limit: int = 50, offset: int = 0,
) -> tuple[list[Document], int]:
    query = select(Document).where(Document.engagement_id == engagement_id)
    if category:
        query = query.where(Document.category == category)
    if not include_internal:
        query = query.where(Document.internal_only.is_(False))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Document.doc_date.desc().nulls_last(), Document.created_at.desc()).limit(limit).offset(offset)))
    return items, total


def list_by_entity(
    db: Session, engagement_id: uuid.UUID, entity_type: str, entity_id: uuid.UUID, *, include_internal: bool,
) -> list[Document]:
    query = (
        select(Document)
        .join(DocumentLink, DocumentLink.document_id == Document.id)
        .where(Document.engagement_id == engagement_id)
        .where(DocumentLink.entity_type == entity_type)
        .where(DocumentLink.entity_id == entity_id)
    )
    if not include_internal:
        query = query.where(Document.internal_only.is_(False))
    return list(db.scalars(query.order_by(Document.doc_date.desc().nulls_last(), Document.created_at.desc())))


def find_link(db: Session, document_id: uuid.UUID, entity_type: str, entity_id: uuid.UUID) -> DocumentLink | None:
    query = (
        select(DocumentLink)
        .where(DocumentLink.document_id == document_id)
        .where(DocumentLink.entity_type == entity_type)
        .where(DocumentLink.entity_id == entity_id)
    )
    return db.scalar(query)
