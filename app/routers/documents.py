import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.crud import documents as documents_crud
from app.database import get_db
from app.dependencies import get_current_user, get_engagement, require_roles, scoped
from app.models.document import Document
from app.models.engagement import Engagement
from app.models.enums import DocumentCategory, Role
from app.models.user import User
from app.schemas.common import Page, Pagination, pagination_params
from app.schemas.document import DocumentCreate, DocumentLinkCreate, DocumentLinkRead, DocumentRead, DocumentUpdate
from app.services import documents as documents_service

router = APIRouter(tags=["documents"])
syner_only = Depends(require_roles(Role.SYNER_ADMIN))
scoped_document = Depends(scoped(Document, "document_id"))


def visible_document(document: Document = scoped_document, user: User = Depends(get_current_user)) -> Document:
    if document.internal_only and not documents_service.can_see_internal(user):
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/engagements/{engagement_id}/documents", response_model=Page[DocumentRead])
def list_documents(
    engagement: Engagement = Depends(get_engagement),
    user: User = Depends(get_current_user),
    category: DocumentCategory | None = None,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = documents_crud.list_for_engagement(
        db, engagement.id, category=category, include_internal=documents_service.can_see_internal(user),
        limit=pagination.limit, offset=pagination.offset,
    )
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/documents", response_model=DocumentRead, status_code=201)
def create_document(
    data: DocumentCreate,
    user: User = syner_only,
    engagement: Engagement = Depends(get_engagement),
    db: Session = Depends(get_db),
):
    return documents_service.create_document(db, user=user, engagement=engagement, data=data)


@router.get("/documents/{document_id}", response_model=DocumentRead)
def read_document(document: Document = Depends(visible_document)):
    return document


@router.patch("/documents/{document_id}", response_model=DocumentRead)
def update_document(
    data: DocumentUpdate,
    user: User = syner_only,
    document: Document = scoped_document,
    db: Session = Depends(get_db),
):
    return documents_service.update_document(db, user=user, document=document, data=data)


@router.post("/documents/{document_id}/links", response_model=DocumentLinkRead, status_code=201)
def add_link(
    data: DocumentLinkCreate,
    user: User = syner_only,
    document: Document = scoped_document,
    db: Session = Depends(get_db),
):
    return documents_service.add_link(db, user=user, document=document, data=data)


@router.delete("/documents/{document_id}/links/{link_id}", status_code=204, response_class=Response)
def remove_link(
    link_id: uuid.UUID,
    user: User = syner_only,
    document: Document = scoped_document,
    db: Session = Depends(get_db),
):
    documents_service.remove_link(db, user=user, document=document, link_id=link_id)
    return Response(status_code=204)
