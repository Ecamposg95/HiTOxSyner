import type { InitiativeStatus } from "../types";

export function avgProgress(items: { progress_pct: number }[]): number | null {
  if (items.length === 0) return null;
  return Math.round(items.reduce((sum, i) => sum + i.progress_pct, 0) / items.length);
}

export function phaseProgress(milestones: { status: string }[]): number | null {
  if (milestones.length === 0) return null;
  return Math.round((milestones.filter((m) => m.status === "Done").length / milestones.length) * 100);
}

export function initiativeTone(status: InitiativeStatus): "accent" | "muted" | "warn" {
  if (status === "On Hold") return "warn";
  if (status === "Execution" || status === "Monitoring" || status === "Completed") return "accent";
  return "muted";
}

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

export function isOverdue(date: string | null, today: Date): boolean {
  if (!date) return false;
  const todayStr = `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`;
  return date.slice(0, 10) < todayStr;
}

export function todayLocal(): Date {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), now.getDate());
}
