export type Role = "SYNER_ADMIN" | "HITO_EXECUTIVE" | "HITO_COLLABORATOR";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  organization_id: string;
  organization_name: string;
  is_active: boolean;
}

export type Health = "On Track" | "Attention" | "At Risk";
export type Level = "Low" | "Medium" | "High" | "Critical";

export interface Engagement {
  id: string;
  organization_id: string;
  name: string;
  subtitle: string | null;
  status: "Active" | "Paused" | "Closed";
  health: Health;
  progress_pct: number;
  executive_summary: string;
  start_date: string | null;
  target_end_date: string | null;
}

export type FindingType = "Opportunity" | "Risk" | "Gap" | "Finding" | "Quick Win" | "Strategic Insight";
export type FindingStatus = "New" | "Under Analysis" | "Validated" | "Converted to Initiative" | "Accepted" | "Closed";

export interface Finding {
  id: string;
  engagement_id: string;
  title: string;
  description: string;
  context: string;
  type: FindingType;
  area: string;
  source: string;
  impact: Level;
  severity: Level;
  evidence: string;
  recommendation: string;
  syner_owner_id: string | null;
  found_on: string;
  status: FindingStatus;
  initiative_id: string | null;
  created_at: string;
  updated_at: string;
}

export type InitiativeStatus = "Discovery" | "Design" | "Validation" | "Execution" | "Monitoring" | "Completed" | "On Hold";

export interface Initiative {
  id: string;
  engagement_id: string;
  name: string;
  description: string;
  objective: string;
  expected_outcome: string;
  hito_owner: string;
  syner_owner_id: string | null;
  area: string;
  priority: Level;
  status: InitiativeStatus;
  start_date: string | null;
  target_date: string | null;
  progress_pct: number;
  expected_impact: string;
  kpis: string;
  risks: string;
  dependencies: string;
  created_at: string;
  updated_at: string;
}

export type ActionStatus = "Open" | "In Progress" | "Blocked" | "Completed" | "Cancelled";

export interface Action {
  id: string;
  engagement_id: string;
  title: string;
  description: string;
  owner_user_id: string | null;
  owner_name: string;
  organization_side: "SYNER" | "CLIENT";
  initiative_id: string | null;
  meeting_id: string | null;
  due_date: string | null;
  priority: Level;
  status: ActionStatus;
  evidence: string;
  created_at: string;
  updated_at: string;
}

export interface Activity {
  id: string;
  user_id: string | null;
  user_name: string;
  action: string;
  entity_type: string;
  entity_id: string;
  summary: string;
  changes: { field: string; before: unknown; after: unknown }[];
  created_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
}

export interface Dashboard {
  engagement: Engagement;
  tiles: {
    health: Health;
    progress_pct: number;
    active_initiatives: number;
    open_actions: number;
    decisions_required: number;
    critical_findings: number;
  };
  active_initiatives: Initiative[];
  key_findings: Finding[];
  next_actions: Action[];
  recent_activity: Activity[];
  roadmap: { phase: RoadmapPhase; milestones: Milestone[] }[];
  decisions_required: Decision[];
  next_milestones: Milestone[];
  lab: LabDashboard | null;
}

export interface InitiativeDetail {
  initiative: Initiative;
  findings: Finding[];
  milestones: Milestone[];
  actions: Action[];
  decisions: Decision[];
  documents: Document[];
  activity: Activity[];
}

export type RoadmapPhase = "Discover" | "Diagnose" | "Design" | "Prioritize" | "Execute" | "Measure";
export type MilestoneStatus = "Planned" | "In Progress" | "Done" | "Slipped";

export interface Milestone {
  id: string;
  engagement_id: string;
  name: string;
  description: string;
  phase: RoadmapPhase;
  due_date: string | null;
  status: MilestoneStatus;
  owner: string;
  initiative_id: string | null;
  deliverable: string;
  created_at: string;
  updated_at: string;
}

export type DecisionStatus = "Proposed" | "Under Review" | "Approved" | "Rejected" | "Deferred";

export interface Decision {
  id: string;
  engagement_id: string;
  title: string;
  context: string;
  alternatives: string;
  syner_recommendation: string;
  final_decision: string;
  owner_name: string;
  participants: string;
  decided_on: string | null;
  impact: string;
  status: DecisionStatus;
  initiative_id: string | null;
  meeting_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Meeting {
  id: string;
  engagement_id: string;
  title: string;
  held_on: string;
  participants: string;
  objective: string;
  summary: string;
  discussion: string;
  next_steps: string;
  created_at: string;
  updated_at: string;
}

export interface MeetingDetail {
  meeting: Meeting;
  decisions: Decision[];
  actions: Action[];
}

export type DocumentCategory = "Discovery" | "Assessment" | "Strategy" | "Process" | "Technology" | "Data" | "AI" | "Reports" | "Meetings" | "Deliverables" | "Evidence";

export interface DocumentLink {
  id: string;
  document_id: string;
  entity_type: string;
  entity_id: string;
}

export interface Document {
  id: string;
  engagement_id: string;
  name: string;
  description: string;
  category: DocumentCategory;
  version: string;
  url: string;
  doc_date: string | null;
  uploader_id: string | null;
  tags: string[];
  internal_only: boolean;
  links: DocumentLink[];
  created_at: string;
  updated_at: string;
}

export interface Comment {
  id: string;
  engagement_id: string;
  entity_type: string;
  entity_id: string;
  author_id: string | null;
  author_name: string;
  body: string;
  created_at: string;
}

export type LabTheme = "DECIDIR" | "CONFRONTAR" | "ALINEAR" | "TRANSFORMAR";
export type LabSessionStatus = "Planned" | "Done" | "Cancelled";

export interface LabSession {
  id: string;
  engagement_id: string;
  number: number;
  name: string;
  theme: LabTheme;
  held_on: string | null;
  status: LabSessionStatus;
  attendance_count: number | null;
  syner_notes: string;
  created_at: string;
  updated_at: string;
}

export interface Pod {
  id: string;
  engagement_id: string;
  number: number;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface Participant {
  id: string;
  engagement_id: string;
  full_name: string;
  area: string;
  title: string;
  pod_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type CtaStatus = "Committed" | "In Progress" | "Evidenced" | "Dropped";

export interface Cta {
  id: string;
  engagement_id: string;
  participant_id: string;
  session_id: string;
  trigger: string;
  behavior: string;
  stakeholder: string;
  evidence_expected: string;
  due_date: string | null;
  accountability_partner: string;
  impact: string;
  status: CtaStatus;
  evidence_notes: string;
  created_at: string;
  updated_at: string;
}

export type ContractStatus = "Draft" | "Active" | "Reviewed 30" | "Reviewed 60" | "Closed";

export interface ActionContract {
  id: string;
  engagement_id: string;
  participant_id: string;
  start_date: string | null;
  review_30_date: string | null;
  review_60_date: string | null;
  success_signal: string;
  status: ContractStatus;
  cta_ids: string[];
  created_at: string;
  updated_at: string;
}

export interface CtaStatusTotals {
  committed: number;
  in_progress: number;
  evidenced: number;
  dropped: number;
  total: number;
}

export interface LabSessionSummary {
  number: number;
  name: string;
  theme: LabTheme;
  held_on: string | null;
  status: LabSessionStatus;
  attendance_count: number | null;
}

export interface LabSummary {
  sessions: LabSessionSummary[];
  sessions_done: number;
  cta_totals: CtaStatusTotals;
  evidenced_pct: number;
  by_session: { session_number: number; session_name: string; totals: CtaStatusTotals }[];
  by_pod: { pod_number: number; pod_name: string; totals: CtaStatusTotals }[];
  active_contracts: number;
}

export interface LabDashboard {
  next_session: LabSessionSummary | null;
  sessions_done: number;
  sessions_total: number;
  active_ctas: number;
  evidenced_pct: number;
  active_contracts: number;
}
