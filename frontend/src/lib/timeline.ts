import type { Milestone } from "../types";

export interface TimelineModel {
  start: Date;
  end: Date;
  months: { key: string; label: string; leftPct: number }[];
  dated: Milestone[];
  undated: Milestone[];
}

const monthFormatter = new Intl.DateTimeFormat("es-MX", { month: "short", year: "2-digit" });

/** `YYYY-MM-DD` → medianoche local (sin corrimiento UTC). */
export function parseLocalDate(iso: string): Date {
  const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
  return new Date(y, m - 1, d);
}

export function positionPct(model: TimelineModel, date: Date): number {
  const span = model.end.getTime() - model.start.getTime();
  const pct = ((date.getTime() - model.start.getTime()) / span) * 100;
  return Math.min(100, Math.max(0, pct));
}

export function buildTimeline(milestones: Milestone[]): TimelineModel | null {
  const dated = milestones.filter((m) => m.due_date);
  const undated = milestones.filter((m) => !m.due_date);
  if (dated.length === 0) return null;
  const times = dated.map((m) => parseLocalDate(m.due_date as string).getTime());
  const min = new Date(Math.min(...times));
  const max = new Date(Math.max(...times));
  const start = new Date(min.getFullYear(), min.getMonth(), 1);
  // mes siguiente al máximo + 1 mes de margen
  const end = new Date(max.getFullYear(), max.getMonth() + 2, 1);
  const span = end.getTime() - start.getTime();
  const months: TimelineModel["months"] = [];
  for (let d = new Date(start); d < end; d = new Date(d.getFullYear(), d.getMonth() + 1, 1)) {
    months.push({
      key: `${d.getFullYear()}-${d.getMonth() + 1}`,
      label: monthFormatter.format(d),
      leftPct: ((d.getTime() - start.getTime()) / span) * 100,
    });
  }
  return { start, end, months, dated, undated };
}
