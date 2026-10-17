import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.crud import comments as comments_crud
from app.database import get_db
from app.dependencies import get_current_user, get_engagement
from app.models.engagement import Engagement
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentRead
from app.schemas.common import Page, Pagination, pagination_params
from app.services import comments as comments_service

router = APIRouter(tags=["comments"])


@router.get("/engagements/{engagement_id}/comments", response_model=Page[CommentRead])
def list_comments(
    engagement: Engagement = Depends(get_engagement),
    entity_type: str = Query(min_length=1, max_length=50),
    entity_id: uuid.UUID = Query(),
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = comments_crud.list_for_entity(
        db, engagement.id, entity_type, entity_id, limit=pagination.limit, offset=pagination.offset
    )
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/comments", response_model=CommentRead, status_code=201)
def create_comment(
    data: CommentCreate,
    user: User = Depends(get_current_user),
    engagement: Engagement = Depends(get_engagement),
    db: Session = Depends(get_db),
):
    return comments_service.create_comment(db, user=user, engagement=engagement, data=data)
