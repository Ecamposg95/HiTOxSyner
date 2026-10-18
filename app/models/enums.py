import enum


class OrganizationKind(str, enum.Enum):
    CONSULTANCY = "CONSULTANCY"
    CLIENT = "CLIENT"


class Role(str, enum.Enum):
    SYNER_ADMIN = "SYNER_ADMIN"
    HITO_EXECUTIVE = "HITO_EXECUTIVE"
    HITO_COLLABORATOR = "HITO_COLLABORATOR"


class EngagementStatus(str, enum.Enum):
    ACTIVE = "Active"
    PAUSED = "Paused"
    CLOSED = "Closed"


class Health(str, enum.Enum):
    ON_TRACK = "On Track"
    ATTENTION = "Attention"
    AT_RISK = "At Risk"


class Level(str, enum.Enum):
    """Impacto, severidad y prioridad comparten escala."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class FindingType(str, enum.Enum):
    OPPORTUNITY = "Opportunity"
    RISK = "Risk"
    GAP = "Gap"
    FINDING = "Finding"
    QUICK_WIN = "Quick Win"
    STRATEGIC_INSIGHT = "Strategic Insight"


class FindingStatus(str, enum.Enum):
    NEW = "New"
    UNDER_ANALYSIS = "Under Analysis"
    VALIDATED = "Validated"
    CONVERTED = "Converted to Initiative"
    ACCEPTED = "Accepted"
    CLOSED = "Closed"


class InitiativeStatus(str, enum.Enum):
    DISCOVERY = "Discovery"
    DESIGN = "Design"
    VALIDATION = "Validation"
    EXECUTION = "Execution"
    MONITORING = "Monitoring"
    COMPLETED = "Completed"
    ON_HOLD = "On Hold"


class ActionStatus(str, enum.Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    BLOCKED = "Blocked"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class OrganizationSide(str, enum.Enum):
    SYNER = "SYNER"
    CLIENT = "CLIENT"


class ActivityAction(str, enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    STATUS_CHANGED = "status_changed"
    CONVERTED = "converted"
    COMMENTED = "commented"


class RoadmapPhase(str, enum.Enum):
    DISCOVER = "Discover"
    DIAGNOSE = "Diagnose"
    DESIGN = "Design"
    PRIORITIZE = "Prioritize"
    EXECUTE = "Execute"
    MEASURE = "Measure"


class MilestoneStatus(str, enum.Enum):
    PLANNED = "Planned"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    SLIPPED = "Slipped"


class DecisionStatus(str, enum.Enum):
    PROPOSED = "Proposed"
    UNDER_REVIEW = "Under Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    DEFERRED = "Deferred"


RESOLUTION_STATUSES = (DecisionStatus.APPROVED, DecisionStatus.REJECTED, DecisionStatus.DEFERRED)
PENDING_DECISION_STATUSES = (DecisionStatus.PROPOSED, DecisionStatus.UNDER_REVIEW)


class DocumentCategory(str, enum.Enum):
    DISCOVERY = "Discovery"
    ASSESSMENT = "Assessment"
    STRATEGY = "Strategy"
    PROCESS = "Process"
    TECHNOLOGY = "Technology"
    DATA = "Data"
    AI = "AI"
    REPORTS = "Reports"
    MEETINGS = "Meetings"
    DELIVERABLES = "Deliverables"
    EVIDENCE = "Evidence"


class LabSessionTheme(str, enum.Enum):
    DECIDIR = "DECIDIR"
    CONFRONTAR = "CONFRONTAR"
    ALINEAR = "ALINEAR"
    TRANSFORMAR = "TRANSFORMAR"


class LabSessionStatus(str, enum.Enum):
    PLANNED = "Planned"
    DONE = "Done"
    CANCELLED = "Cancelled"


class CtaStatus(str, enum.Enum):
    COMMITTED = "Committed"
    IN_PROGRESS = "In Progress"
    EVIDENCED = "Evidenced"
    DROPPED = "Dropped"


class ContractStatus(str, enum.Enum):
    DRAFT = "Draft"
    ACTIVE = "Active"
    REVIEWED_30 = "Reviewed 30"
    REVIEWED_60 = "Reviewed 60"
    CLOSED = "Closed"


ACTIVE_CTA_STATUSES = (CtaStatus.COMMITTED, CtaStatus.IN_PROGRESS)
ACTIVE_CONTRACT_STATUSES = (ContractStatus.ACTIVE, ContractStatus.REVIEWED_30, ContractStatus.REVIEWED_60)

LAB_SESSION_NAMES = {
    1: "The Brain Under Pressure",
    2: "Trust, Conflict & Difficult Conversations",
    3: "From Silos to Flow",
    4: "AI, Judgment & Collective Accountability",
}
LAB_SESSION_THEMES = {
    1: LabSessionTheme.DECIDIR,
    2: LabSessionTheme.CONFRONTAR,
    3: LabSessionTheme.ALINEAR,
    4: LabSessionTheme.TRANSFORMAR,
}
