type Tone = "ok" | "warn" | "danger" | "neutral";

export const TONE: Record<string, Tone> = {
  "On Track": "ok",
  Attention: "warn",
  "At Risk": "danger",
  Critical: "danger",
  High: "warn",
  Blocked: "danger",
  Completed: "ok",
  Closed: "neutral",
  Cancelled: "neutral",
  "On Hold": "neutral",
  Done: "ok",
  Approved: "ok",
  Slipped: "danger",
  Rejected: "danger",
  "Under Review": "warn",
  Deferred: "neutral",
  Interno: "warn",
  Evidenced: "ok",
  Dropped: "neutral",
  Active: "ok",
  Draft: "neutral",
  "Reviewed 30": "warn",
  "Reviewed 60": "warn",
};

export function StatusBadge({ value }: { value: string }) {
  const tone = TONE[value] ?? "neutral";
  return <span className={`badge badge-${tone}`}>{value}</span>;
}
