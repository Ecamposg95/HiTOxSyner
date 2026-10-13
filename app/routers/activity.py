import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import activities as activities_crud
from app.database import get_db
from app.dependencies import get_engagement
from app.models.engagement import Engagement
from app.schemas.activity import ActivityRead
from app.schemas.common import Page, Pagination, pagination_params

router = APIRouter(tags=["activity"])


@router.get("/engagements/{engagement_id}/activity", response_model=Page[ActivityRead])
def list_activity(
    engagement: Engagement = Depends(get_engagement),
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = activities_crud.list_for_engagement(
        db, engagement.id, entity_type=entity_type, entity_id=entity_id,
        limit=pagination.limit, offset=pagination.offset,
    )
    return Page(items=items, total=total)
