from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import meetings as meetings_crud
from app.database import get_db
from app.dependencies import get_engagement, require_roles, scoped
from app.models.engagement import Engagement
from app.models.enums import Role
from app.models.meeting import Meeting
from app.models.user import User
from app.schemas.action import ActionCreate, ActionRead
from app.schemas.common import Page, Pagination, pagination_params
from app.schemas.meeting import MeetingCreate, MeetingRead, MeetingUpdate
from app.services import actions as actions_service
from app.services import meetings as meetings_service

router = APIRouter(tags=["meetings"])
syner_only = Depends(require_roles(Role.SYNER_ADMIN))
scoped_meeting = Depends(scoped(Meeting, "meeting_id"))


@router.get("/engagements/{engagement_id}/meetings", response_model=Page[MeetingRead])
def list_meetings(
    engagement: Engagement = Depends(get_engagement),
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
):
    items, total = meetings_crud.list_for_engagement(db, engagement.id, limit=pagination.limit, offset=pagination.offset)
    return Page(items=items, total=total)


@router.post("/engagements/{engagement_id}/meetings", response_model=MeetingRead, status_code=201)
def create_meeting(
    data: MeetingCreate,
    user: User = syner_only,
    engagement: Engagement = Depends(get_engagement),
    db: Session = Depends(get_db),
):
    return meetings_service.create_meeting(db, user=user, engagement=engagement, data=data)


@router.get("/meetings/{meeting_id}", response_model=MeetingRead)
def read_meeting(meeting: Meeting = scoped_meeting):
    return meeting


@router.patch("/meetings/{meeting_id}", response_model=MeetingRead)
def update_meeting(
    data: MeetingUpdate,
    user: User = syner_only,
    meeting: Meeting = scoped_meeting,
    db: Session = Depends(get_db),
):
    return meetings_service.update_meeting(db, user=user, meeting=meeting, data=data)


@router.post("/meetings/{meeting_id}/actions", response_model=ActionRead, status_code=201)
def create_action_from_meeting(
    data: ActionCreate,
    user: User = syner_only,
    meeting: Meeting = scoped_meeting,
    db: Session = Depends(get_db),
):
    engagement = db.get(Engagement, meeting.engagement_id)
    payload = data.model_copy(update={"meeting_id": meeting.id})
    return actions_service.create_action(db, user=user, engagement=engagement, data=payload)
