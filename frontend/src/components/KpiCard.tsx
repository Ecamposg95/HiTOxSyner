import type { ReactNode } from "react";

const TONE = { default: "text-ink", ok: "text-accent", warn: "text-warn", danger: "text-danger" } as const;

export function KpiCard({ label, value, note, tone = "default", visual }: {
  label: string;
  value: ReactNode;
  note?: ReactNode;
  tone?: keyof typeof TONE;
  visual?: ReactNode;
}) {
  return (
    <div className="card px-4 py-4">
      <div className="eyebrow">{label}</div>
      <div className="mt-2 flex items-center gap-3">
        {visual}
        <div className={`kpi-value tabular-nums ${TONE[tone]}`}>{value}</div>
      </div>
      {note && <div className="mt-1 text-xs text-muted">{note}</div>}
    </div>
  );
}
