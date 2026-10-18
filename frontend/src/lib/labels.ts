import type { Role } from "../types";

export const NAV_ITEMS = [
  { to: "/", label: "Overview", end: true },
  { to: "/findings", label: "Findings" },
  { to: "/initiatives", label: "Initiatives" },
  { to: "/roadmap", label: "Roadmap" },
  { to: "/actions", label: "Actions" },
  { to: "/decisions", label: "Decisions" },
  { to: "/meetings", label: "Meetings" },
  { to: "/documents", label: "Documents" },
  { to: "/lab", label: "Leadership Lab" },
];

export const ROLE_LABELS: Record<Role, string> = {
  SYNER_ADMIN: "Equipo Syner",
  HITO_EXECUTIVE: "Dirección",
  HITO_COLLABORATOR: "Colaborador",
};

export const FINDING_TYPES = ["Opportunity", "Risk", "Gap", "Finding", "Quick Win", "Strategic Insight"] as const;
export const FINDING_STATUSES = ["New", "Under Analysis", "Validated", "Converted to Initiative", "Accepted", "Closed"] as const;
export const INITIATIVE_STATUSES = ["Discovery", "Design", "Validation", "Execution", "Monitoring", "Completed", "On Hold"] as const;
export const ACTION_STATUSES = ["Open", "In Progress", "Blocked", "Completed", "Cancelled"] as const;
export const LEVELS = ["Low", "Medium", "High", "Critical"] as const;
export const HEALTHS = ["On Track", "Attention", "At Risk"] as const;

export const ROADMAP_PHASES = ["Discover", "Diagnose", "Design", "Prioritize", "Execute", "Measure"] as const;
export const MILESTONE_STATUSES = ["Planned", "In Progress", "Done", "Slipped"] as const;
export const DECISION_STATUSES = ["Proposed", "Under Review", "Approved", "Rejected", "Deferred"] as const;
export const RESOLUTION_STATUSES = ["Approved", "Rejected", "Deferred"] as const;
export const DOCUMENT_CATEGORIES = ["Discovery", "Assessment", "Strategy", "Process", "Technology", "Data", "AI", "Reports", "Meetings", "Deliverables", "Evidence"] as const;
export const ENTITY_LABELS: Record<string, string> = { finding: "Finding", initiative: "Initiative", meeting: "Meeting", decision: "Decision", action: "Action" };

export const LAB_SESSION_STATUSES = ["Planned", "Done", "Cancelled"] as const;
export const CTA_STATUSES = ["Committed", "In Progress", "Evidenced", "Dropped"] as const;
export const CONTRACT_STATUSES = ["Draft", "Active", "Reviewed 30", "Reviewed 60", "Closed"] as const;
export const LAB_THEMES = ["DECIDIR", "CONFRONTAR", "ALINEAR", "TRANSFORMAR"] as const;
export const LAB_SESSION_CATALOG = [
  { number: 1, name: "The Brain Under Pressure", theme: "DECIDIR" },
  { number: 2, name: "Trust, Conflict & Difficult Conversations", theme: "CONFRONTAR" },
  { number: 3, name: "From Silos to Flow", theme: "ALINEAR" },
  { number: 4, name: "AI, Judgment & Collective Accountability", theme: "TRANSFORMAR" },
] as const;

export type LabTab = "sessions" | "participants" | "ctas" | "contracts";
export const LAB_TABS: { key: LabTab; label: string }[] = [
  { key: "sessions", label: "Sessions" },
  { key: "participants", label: "Participants & Pods" },
];
