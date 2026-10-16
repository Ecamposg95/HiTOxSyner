from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.engagement import Engagement
from app.models.enums import ActivityAction
from app.models.initiative import Initiative
from app.models.milestone import Milestone
from app.models.user import User
from app.schemas.common import updates
from app.schemas.milestone import MilestoneCreate, MilestoneUpdate
from app.services.activity import diff_changes, log_activity


def validate_initiative(db: Session, engagement: Engagement, initiative_id) -> None:
    if initiative_id is None:
        return
    initiative = db.get(Initiative, initiative_id)
    if initiative is None or initiative.engagement_id != engagement.id:
        raise HTTPException(status_code=422, detail="initiative_id no pertenece a este engagement")


def create_milestone(db: Session, *, user: User, engagement: Engagement, data: MilestoneCreate) -> Milestone:
    validate_initiative(db, engagement, data.initiative_id)
    milestone = Milestone(organization_id=engagement.organization_id, engagement_id=engagement.id, created_by=user.id, **data.model_dump())
    db.add(milestone)
    db.flush()
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="milestone",
        entity_id=milestone.id, summary=f'{user.full_name} created Milestone "{milestone.name}"',
    )
    db.commit()
    db.refresh(milestone)
    return milestone


def update_milestone(db: Session, *, user: User, milestone: Milestone, data: MilestoneUpdate) -> Milestone:
    payload = updates(data, nullable={"due_date", "initiative_id"})
    engagement = db.get(Engagement, milestone.engagement_id)
    validate_initiative(db, engagement, payload.get("initiative_id"))
    changes = diff_changes(milestone, payload)
    if not changes:
        return milestone
    for field, value in payload.items():
        setattr(milestone, field, value)
    status_change = next((c for c in changes if c["field"] == "status"), None)
    if status_change:
        action = ActivityAction.STATUS_CHANGED
        summary = f'{user.full_name} updated Milestone "{milestone.name}" from {status_change["before"]} to {status_change["after"]}'
    else:
        action = ActivityAction.UPDATED
        summary = f'{user.full_name} updated Milestone "{milestone.name}"'
    log_activity(
        db, user=user, engagement=engagement, action=action, entity_type="milestone",
        entity_id=milestone.id, summary=summary, changes=changes,
    )
    db.commit()
    db.refresh(milestone)
    return milestone
