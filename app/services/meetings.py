from sqlalchemy.orm import Session

from app.models.engagement import Engagement
from app.models.enums import ActivityAction
from app.models.meeting import Meeting
from app.models.user import User
from app.schemas.common import updates
from app.schemas.meeting import MeetingCreate, MeetingUpdate
from app.services.activity import diff_changes, log_activity


def create_meeting(db: Session, *, user: User, engagement: Engagement, data: MeetingCreate) -> Meeting:
    meeting = Meeting(organization_id=engagement.organization_id, engagement_id=engagement.id, created_by=user.id, **data.model_dump())
    db.add(meeting)
    db.flush()
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="meeting",
        entity_id=meeting.id, summary=f'{user.full_name} created Meeting "{meeting.title}"',
    )
    db.commit()
    db.refresh(meeting)
    return meeting


def update_meeting(db: Session, *, user: User, meeting: Meeting, data: MeetingUpdate) -> Meeting:
    payload = updates(data)
    changes = diff_changes(meeting, payload)
    if not changes:
        return meeting
    for field, value in payload.items():
        setattr(meeting, field, value)
    engagement = db.get(Engagement, meeting.engagement_id)
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.UPDATED, entity_type="meeting",
        entity_id=meeting.id, summary=f'{user.full_name} updated Meeting "{meeting.title}"', changes=changes,
    )
    db.commit()
    db.refresh(meeting)
    return meeting
