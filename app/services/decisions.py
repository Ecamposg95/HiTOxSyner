from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.decision import Decision
from app.models.engagement import Engagement
from app.models.enums import RESOLUTION_STATUSES, ActivityAction
from app.models.initiative import Initiative
from app.models.meeting import Meeting
from app.models.user import User
from app.schemas.common import updates
from app.schemas.decision import DecisionCreate, DecisionUpdate
from app.services.activity import diff_changes, log_activity


def _validate_links(db: Session, engagement: Engagement, payload: dict) -> None:
    initiative_id = payload.get("initiative_id")
    if initiative_id is not None:
        initiative = db.get(Initiative, initiative_id)
        if initiative is None or initiative.engagement_id != engagement.id:
            raise HTTPException(status_code=422, detail="initiative_id no pertenece a este engagement")
    meeting_id = payload.get("meeting_id")
    if meeting_id is not None:
        meeting = db.get(Meeting, meeting_id)
        if meeting is None or meeting.engagement_id != engagement.id:
            raise HTTPException(status_code=422, detail="meeting_id no pertenece a este engagement")


def create_decision(db: Session, *, user: User, engagement: Engagement, data: DecisionCreate) -> Decision:
    payload = data.model_dump()
    _validate_links(db, engagement, payload)
    decision = Decision(organization_id=engagement.organization_id, engagement_id=engagement.id, created_by=user.id, **payload)
    db.add(decision)
    db.flush()
    summary = f'{user.full_name} created Decision "{decision.title}"'
    if decision.meeting_id is not None:
        meeting = db.get(Meeting, decision.meeting_id)
        summary += f' from Meeting "{meeting.title}"'
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="decision",
        entity_id=decision.id, summary=summary,
    )
    db.commit()
    db.refresh(decision)
    return decision


def update_decision(db: Session, *, user: User, decision: Decision, data: DecisionUpdate) -> Decision:
    payload = updates(data, nullable={"decided_on", "initiative_id", "meeting_id"})
    engagement = db.get(Engagement, decision.engagement_id)
    _validate_links(db, engagement, payload)
    new_status = payload.get("status")
    if new_status in RESOLUTION_STATUSES and "decided_on" not in payload and decision.decided_on is None:
        payload["decided_on"] = date.today()
    changes = diff_changes(decision, payload)
    if not changes:
        return decision
    for field, value in payload.items():
        setattr(decision, field, value)
    status_change = next((c for c in changes if c["field"] == "status"), None)
    if status_change:
        action = ActivityAction.STATUS_CHANGED
        summary = f'{user.full_name} updated Decision "{decision.title}" from {status_change["before"]} to {status_change["after"]}'
    else:
        action = ActivityAction.UPDATED
        summary = f'{user.full_name} updated Decision "{decision.title}"'
    log_activity(
        db, user=user, engagement=engagement, action=action, entity_type="decision",
        entity_id=decision.id, summary=summary, changes=changes,
    )
    db.commit()
    db.refresh(decision)
    return decision
