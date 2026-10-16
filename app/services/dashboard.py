from sqlalchemy.orm import Session

from app.crud import actions as actions_crud
from app.crud import activities as activities_crud
from app.crud import decisions as decisions_crud
from app.crud import findings as findings_crud
from app.crud import initiatives as initiatives_crud
from app.crud import milestones as milestones_crud
from app.models.engagement import Engagement
from app.models.enums import RoadmapPhase
from app.models.user import User
from app.schemas.action import ActionRead
from app.schemas.activity import ActivityRead
from app.schemas.dashboard import DashboardRead, DashboardTiles, RoadmapPhaseRead
from app.schemas.decision import DecisionRead
from app.schemas.engagement import EngagementRead
from app.schemas.finding import FindingRead
from app.schemas.initiative import InitiativeRead
from app.schemas.milestone import MilestoneRead
from app.services.documents import can_see_internal


def build_roadmap(db: Session, engagement: Engagement) -> list[RoadmapPhaseRead]:
    by_phase: dict[RoadmapPhase, list[MilestoneRead]] = {phase: [] for phase in RoadmapPhase}
    for milestone in milestones_crud.list_all(db, engagement.id):
        by_phase[milestone.phase].append(MilestoneRead.model_validate(milestone))
    return [RoadmapPhaseRead(phase=phase.value, milestones=items) for phase, items in by_phase.items()]


def build_dashboard(db: Session, engagement: Engagement, user: User) -> DashboardRead:
    tiles = DashboardTiles(
        health=engagement.health,
        progress_pct=engagement.progress_pct,
        active_initiatives=initiatives_crud.count_active(db, engagement.id),
        open_actions=actions_crud.count_open(db, engagement.id),
        decisions_required=decisions_crud.count_required(db, engagement.id),
        critical_findings=findings_crud.count_critical_open(db, engagement.id),
    )
    return DashboardRead(
        engagement=EngagementRead.model_validate(engagement),
        tiles=tiles,
        active_initiatives=[InitiativeRead.model_validate(i) for i in initiatives_crud.active(db, engagement.id)],
        key_findings=[FindingRead.model_validate(f) for f in findings_crud.key_findings(db, engagement.id)],
        next_actions=[ActionRead.model_validate(a) for a in actions_crud.next_open(db, engagement.id)],
        recent_activity=[ActivityRead.model_validate(a) for a in activities_crud.recent(db, engagement.id, limit=15, include_internal=can_see_internal(user))],
        roadmap=build_roadmap(db, engagement),
        decisions_required=[DecisionRead.model_validate(d) for d in decisions_crud.required(db, engagement.id)],
        next_milestones=[MilestoneRead.model_validate(m) for m in milestones_crud.upcoming(db, engagement.id)],
    )
