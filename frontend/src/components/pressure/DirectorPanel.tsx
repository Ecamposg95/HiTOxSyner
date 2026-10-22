import { HOLD_MINUTES, isFinished, nextRelease, pendingEvent, releaseMap, type SimAction, type SimState } from "../../lib/pressureRoom";

const STATUS = {
  fired: { mark: "✓", className: "border-accent/40 bg-accent/10 text-accent" },
  pending: { mark: "!", className: "border-warn bg-warn/15 text-warn" },
  next: { mark: "·", className: "border-line text-ink" },
  later: { mark: "·", className: "border-line text-muted" },
} as const;

export function DirectorPanel({ state, dispatch }: { state: SimState; dispatch: (a: SimAction) => void }) {
  const pending = pendingEvent(state);
  const next = nextRelease(state);
  return (
    <section className="panel p-5" aria-label="Director del caso">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="font-display text-[15px] font-medium text-ink">Agente Director del caso</h2>
        <span className="badge badge-neutral">simulado</span>
      </div>
      {pending ? (
        <div className="rounded-md border border-warn bg-warn/10 p-3" role="alert">
          <div className="eyebrow text-warn">Propone liberar {pending.code}</div>
          <div className="mt-1 font-display text-[15px] font-medium text-ink">{pending.title}</div>
          <p className="mt-1 text-sm text-ink">{pending.reason}</p>
          <p className="mt-2 text-xs text-muted">El reloj está detenido hasta que decidas. Nada se libera sin el facilitador.</p>
          <div className="mt-3 flex gap-2">
            <button type="button" className="btn btn-primary" onClick={() => dispatch({ type: "approve" })}>Aprobar</button>
            <button type="button" className="btn" onClick={() => dispatch({ type: "hold" })}>Frenar {HOLD_MINUTES} min</button>
          </div>
        </div>
      ) : isFinished(state) ? (
        <p className="text-sm text-muted">Acto cerrado. Cambia de acto o reinicia para repetir la corrida.</p>
      ) : next ? (
        <p className="text-sm text-muted">
          Siguiente propuesta: <span className="text-ink">{next.event.code} · {next.event.title}</span>{" "}
          <span className="tabular-nums">en ~{next.inMinutes} min</span> del caso.
        </p>
      ) : (
        <p className="text-sm text-muted">Sin liberaciones pendientes.</p>
      )}
      <ol className="mt-4 grid grid-cols-4 gap-2" aria-label="Mapa de liberación">
        {releaseMap(state).map((r) => {
          const s = STATUS[r.status];
          return (
            <li key={r.code} className={`rounded-md border px-2 py-1.5 text-center text-xs ${s.className}`} title={r.title}>
              <span className="font-display font-medium">{r.code}</span> <span aria-hidden="true">{s.mark}</span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
