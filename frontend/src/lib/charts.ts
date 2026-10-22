import type { CtaStatusTotals } from "../types";

export type CtaKey = "evidenced" | "in_progress" | "committed" | "dropped";

export const CTA_LABELS: Record<CtaKey, string> = {
  evidenced: "Evidenced",
  in_progress: "In Progress",
  committed: "Committed",
  dropped: "Dropped",
};

const ORDER: CtaKey[] = ["evidenced", "in_progress", "committed", "dropped"];

export function ctaSlices(t: CtaStatusTotals): { key: CtaKey; label: string; value: number }[] {
  if (t.total === 0) return [];
  return ORDER.filter((k) => t[k] > 0).map((k) => ({ key: k, label: CTA_LABELS[k], value: t[k] }));
}

export interface ChartColors {
  evidenced: string;
  in_progress: string;
  committed: string;
  dropped: string;
  grid: string;
  text: string;
}

export function chartColors(): ChartColors {
  const style = getComputedStyle(document.documentElement);
  const v = (name: string) => style.getPropertyValue(name).trim();
  return {
    evidenced: `rgb(${v("--accent-fill")})`,
    in_progress: `rgb(${v("--warn")})`,
    committed: `rgb(${v("--muted")})`,
    dropped: `rgb(${v("--muted")} / 0.4)`,
    grid: `rgb(${v("--line")})`,
    text: `rgb(${v("--muted")})`,
  };
}
