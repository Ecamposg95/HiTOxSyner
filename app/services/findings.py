from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.engagement import Engagement
from app.models.enums import ActivityAction, FindingStatus, InitiativeStatus, Role
from app.models.finding import Finding
from app.models.initiative import Initiative
from app.models.user import User
from app.schemas.common import updates
from app.schemas.finding import FindingCreate, FindingUpdate
from app.services.activity import diff_changes, log_activity


def validate_syner_owner(db: Session, owner_id) -> None:
    if owner_id is None:
        return
    owner = db.get(User, owner_id)
    if owner is None or owner.role != Role.SYNER_ADMIN:
        raise HTTPException(status_code=422, detail="syner_owner_id debe ser un usuario Syner")



def create_finding(db: Session, *, user: User, engagement: Engagement, data: FindingCreate) -> Finding:
    validate_syner_owner(db, data.syner_owner_id)
    finding = Finding(
        organization_id=engagement.organization_id,
        engagement_id=engagement.id,
        created_by=user.id,
        **data.model_dump(),
    )
    db.add(finding)
    db.flush()
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.CREATED, entity_type="finding",
        entity_id=finding.id, summary=f'{user.full_name} created Finding "{finding.title}"',
    )
    db.commit()
    db.refresh(finding)
    return finding


def update_finding(db: Session, *, user: User, finding: Finding, data: FindingUpdate) -> Finding:
    payload = updates(data, nullable={"syner_owner_id"})
    validate_syner_owner(db, payload.get("syner_owner_id"))
    changes = diff_changes(finding, payload)
    if not changes:
        return finding
    for field, value in payload.items():
        setattr(finding, field, value)
    engagement = db.get(Engagement, finding.engagement_id)
    status_change = next((c for c in changes if c["field"] == "status"), None)
    if status_change:
        action = ActivityAction.STATUS_CHANGED
        summary = f'{user.full_name} updated Finding "{finding.title}" from {status_change["before"]} to {status_change["after"]}'
    else:
        action = ActivityAction.UPDATED
        summary = f'{user.full_name} updated Finding "{finding.title}"'
    log_activity(
        db, user=user, engagement=engagement, action=action, entity_type="finding",
        entity_id=finding.id, summary=summary, changes=changes,
    )
    db.commit()
    db.refresh(finding)
    return finding


class FindingAlreadyConverted(Exception):
    pass


def convert_finding(db: Session, *, user: User, finding: Finding) -> Initiative:
    if finding.initiative_id is not None:
        raise FindingAlreadyConverted
    engagement = db.get(Engagement, finding.engagement_id)
    initiative = Initiative(
        organization_id=engagement.organization_id,
        engagement_id=engagement.id,
        created_by=user.id,
        name=finding.title,
        description=finding.description,
        objective=finding.recommendation,
        area=finding.area,
        priority=finding.impact,
        status=InitiativeStatus.DISCOVERY,
    )
    db.add(initiative)
    db.flush()
    before_status = finding.status.value
    finding.initiative_id = initiative.id
    finding.status = FindingStatus.CONVERTED
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.CONVERTED, entity_type="finding",
        entity_id=finding.id,
        summary=f'{user.full_name} converted Finding "{finding.title}" into Initiative "{initiative.name}"',
        changes=[
            {"field": "status", "before": before_status, "after": FindingStatus.CONVERTED.value},
            {"field": "initiative_id", "before": None, "after": str(initiative.id)},
        ],
    )
    db.commit()
    db.refresh(initiative)
    return initiative
