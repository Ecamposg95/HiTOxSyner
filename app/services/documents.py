import uuid

from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.crud import documents as documents_crud
from app.models.activity import Activity
from app.models.document import Document, DocumentLink
from app.models.engagement import Engagement
from app.models.enums import ActivityAction, Role
from app.models.user import User
from app.schemas.common import updates
from app.schemas.document import DocumentCreate, DocumentLinkCreate, DocumentUpdate
from app.services.activity import diff_changes, log_activity
from app.services.entities import entity_label, resolve_entity


def can_see_internal(user: User) -> bool:
    return user.role == Role.SYNER_ADMIN


def create_document(db: Session, *, user: User, engagement: Engagement, data: DocumentCreate) -> Document:
    document = Document(
        organization_id=engagement.organization_id, engagement_id=engagement.id, created_by=user.id,
        uploader_id=user.id, **data.model_dump(),
    )
    db.add(document)
    db.flush()
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="document",
        entity_id=document.id, summary=f'{user.full_name} created Document "{document.name}"',
        internal_only=document.internal_only,
    )
    db.commit()
    db.refresh(document)
    return document


def update_document(db: Session, *, user: User, document: Document, data: DocumentUpdate) -> Document:
    payload = updates(data, nullable={"doc_date"})
    changes = diff_changes(document, payload)
    if not changes:
        return document
    for field, value in payload.items():
        setattr(document, field, value)
    if "internal_only" in payload:
        db.execute(
            update(Activity)
            .where(Activity.entity_type == "document", Activity.entity_id == document.id)
            .values(internal_only=document.internal_only)
        )
    engagement = db.get(Engagement, document.engagement_id)
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.UPDATED, entity_type="document",
        entity_id=document.id, summary=f'{user.full_name} updated Document "{document.name}"', changes=changes,
        internal_only=document.internal_only,
    )
    db.commit()
    db.refresh(document)
    return document


def add_link(db: Session, *, user: User, document: Document, data: DocumentLinkCreate) -> DocumentLink:
    engagement = db.get(Engagement, document.engagement_id)
    _, title = resolve_entity(db, engagement, data.entity_type, data.entity_id)
    if documents_crud.find_link(db, document.id, data.entity_type, data.entity_id) is not None:
        raise HTTPException(status_code=409, detail="El documento ya está vinculado a esta entidad")
    link = DocumentLink(document_id=document.id, entity_type=data.entity_type, entity_id=data.entity_id)
    db.add(link)
    db.flush()
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.UPDATED, entity_type="document",
        entity_id=document.id,
        summary=f'{user.full_name} linked Document "{document.name}" to {entity_label(data.entity_type)} "{title}"',
        changes=[{"field": "links", "before": None, "after": f"{data.entity_type}:{data.entity_id}"}],
        internal_only=document.internal_only,
    )
    db.commit()
    db.refresh(link)
    return link


def remove_link(db: Session, *, user: User, document: Document, link_id: uuid.UUID) -> None:
    link = db.get(DocumentLink, link_id)
    if link is None or link.document_id != document.id:
        raise HTTPException(status_code=404, detail="DocumentLink not found")
    engagement = db.get(Engagement, document.engagement_id)
    db.delete(link)
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.UPDATED, entity_type="document",
        entity_id=document.id, summary=f'{user.full_name} unlinked Document "{document.name}" from {entity_label(link.entity_type)}',
        changes=[{"field": "links", "before": f"{link.entity_type}:{link.entity_id}", "after": None}],
        internal_only=document.internal_only,
    )
    db.commit()
