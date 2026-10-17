from pydantic import BaseModel

from app.models.enums import Health
from app.schemas.action import ActionRead
from app.schemas.activity import ActivityRead
from app.schemas.decision import DecisionRead
from app.schemas.engagement import EngagementRead
from app.schemas.finding import FindingRead
from app.schemas.initiative import InitiativeRead
from app.schemas.milestone import MilestoneRead


class DashboardTiles(BaseModel):
    health: Health
    progress_pct: int
    active_initiatives: int
    open_actions: int
    decisions_required: int
    critical_findings: int


class RoadmapPhaseRead(BaseModel):
    phase: str
    milestones: list[MilestoneRead] = []


class DashboardRead(BaseModel):
    engagement: EngagementRead
    tiles: DashboardTiles
    active_initiatives: list[InitiativeRead]
    key_findings: list[FindingRead]
    next_actions: list[ActionRead]
    recent_activity: list[ActivityRead]
    roadmap: list[RoadmapPhaseRead]
    decisions_required: list[DecisionRead]
    next_milestones: list[MilestoneRead]
