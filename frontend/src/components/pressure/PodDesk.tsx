import { formatClock, getAct, pressureLevel, type PodState, type SimState } from "../../lib/pressureRoom";

const LEVEL = {
  low: { label: "Presión baja", bar: "bg-accent-fill", text: "text-accent" },
  mid: { label: "Presión media", bar: "bg-warn", text: "text-warn" },
  high: { label: "Presión alta", bar: "bg-danger", text: "text-danger" },
} as const;

function Meter({ label, value, className }: { label: string; value: number; className: string }) {
  return (
    <div>
      <div className="flex items-center justify-between text-[11px] text-muted">
        <span>{label}</span>
        <span className="tabular-nums text-ink">{value}%</span>
      </div>
      <div className="mt-1 h-1.5 w-full rounded bg-line" role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={100} aria-label={label}>
        <div className={`h-1.5 rounded ${className}`} style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

export function PodDesk({ pod, state }: { pod: PodState; state: SimState }) {
  const level = LEVEL[pressureLevel(pod.pressure)];
  const start = getAct(state.actId).startMinutes;
  const gap = pod.certainty - pod.evidence;
  return (
    <article className="card p-4" aria-label={pod.name}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="font-display text-[15px] font-medium text-ink">{pod.name}</div>
          <div className={`text-[11px] ${level.text}`}>{level.label}</div>
        </div>
        {pod.decidedAt === null ? (
          <span className="badge badge-warn">Sin decidir · {state.clock} min</span>
        ) : (
          <span className="badge badge-ok">Decidió {formatClock(start + pod.decidedAt)}</span>
        )}
      </div>
      <div className="mt-3 space-y-2">
        <Meter label="Presión" value={pod.pressure} className={level.bar} />
        <Meter label="Certeza proyectada" value={pod.certainty} className={gap >= 30 ? "bg-danger" : "bg-accent-fill"} />
        <Meter label="Evidencia disponible" value={pod.evidence} className="bg-muted" />
      </div>
      {pod.deliverable && <p className="mt-3 text-xs text-muted">En curso: {pod.deliverable}</p>}
      {pod.alerts.length > 0 && (
        <ul className="mt-2 flex flex-wrap gap-1" aria-label="Alertas">
          {pod.alerts.map((a) => (
            <li key={a} className="badge badge-danger">{a}</li>
          ))}
        </ul>
      )}
    </article>
  );
}
