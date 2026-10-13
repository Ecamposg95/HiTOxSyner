from sqlalchemy.orm import Session

from app.models.engagement import Engagement
from app.models.enums import ActivityAction
from app.models.initiative import Initiative
from app.models.user import User
from app.schemas.common import updates
from app.schemas.initiative import InitiativeCreate, InitiativeUpdate
from app.services.activity import diff_changes, log_activity
from app.services.findings import validate_syner_owner


def create_initiative(db: Session, *, user: User, engagement: Engagement, data: InitiativeCreate) -> Initiative:
    validate_syner_owner(db, data.syner_owner_id)
    initiative = Initiative(
        organization_id=engagement.organization_id, engagement_id=engagement.id, created_by=user.id, **data.model_dump()
    )
    db.add(initiative)
    db.flush()
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="initiative",
        entity_id=initiative.id, summary=f'{user.full_name} created Initiative "{initiative.name}"',
    )
    db.commit()
    db.refresh(initiative)
    return initiative


def update_initiative(db: Session, *, user: User, initiative: Initiative, data: InitiativeUpdate) -> Initiative:
    payload = updates(data, nullable={"syner_owner_id", "start_date", "target_date"})
    validate_syner_owner(db, payload.get("syner_owner_id"))
    changes = diff_changes(initiative, payload)
    if not changes:
        return initiative
    for field, value in payload.items():
        setattr(initiative, field, value)
    engagement = db.get(Engagement, initiative.engagement_id)
    status_change = next((c for c in changes if c["field"] == "status"), None)
    if status_change:
        action = ActivityAction.STATUS_CHANGED
        summary = f'{user.full_name} updated Initiative "{initiative.name}" from {status_change["before"]} to {status_change["after"]}'
    else:
        action = ActivityAction.UPDATED
        summary = f'{user.full_name} updated Initiative "{initiative.name}"'
    log_activity(
        db, user=user, engagement=engagement, action=action, entity_type="initiative",
        entity_id=initiative.id, summary=summary, changes=changes,
    )
    db.commit()
    db.refresh(initiative)
    return initiative
