import { effectiveAt, firedEvents, formatClock, getAct, type SimState } from "../../lib/pressureRoom";

export function ObserverNotes({ state }: { state: SimState }) {
  const notes = firedEvents(state).filter((e) => e.kind === "observer").reverse();
  const start = getAct(state.actId).startMinutes;
  return (
    <section className="panel p-5" aria-label="Observador">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="font-display text-[15px] font-medium text-ink">Agente Observador</h2>
        <span className="badge badge-neutral">solo Syner</span>
      </div>
      <p className="mb-3 text-xs text-muted">Nombra patrones y consecuencias, nunca personalidades. Evidencia para el debrief y los CTA.</p>
      {notes.length === 0 ? (
        <p className="text-sm text-muted">Sin notas todavía.</p>
      ) : (
        <ol className="space-y-3">
          {notes.map((n) => (
            <li key={n.id} className="border-l-2 border-line pl-3">
              <div className="flex flex-wrap items-center gap-x-2 text-[11px] text-muted">
                <span className="tabular-nums">{formatClock(start + effectiveAt(n, state))}</span>
                {n.pod && <span className="text-ink">Pod {n.pod}</span>}
              </div>
              <p className="mt-0.5 text-sm leading-5 text-ink">{n.text}</p>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
