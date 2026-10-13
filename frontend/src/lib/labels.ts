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
