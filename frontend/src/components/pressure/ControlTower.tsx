import { ACTS, caseClock, formatCountdown, getAct, isFinished, minutesToDeadline, type SimAction, type SimState } from "../../lib/pressureRoom";

const SPEEDS = [1, 2, 4] as const;

export function ControlTower({ state, dispatch }: { state: SimState; dispatch: (a: SimAction) => void }) {
  const act = getAct(state.actId);
  const remaining = minutesToDeadline(state);
  const total = act.deadlineMinutes - act.startMinutes;
  const progress = Math.min(100, (state.clock / total) * 100);
  const finished = isFinished(state);
  const late = remaining < 0;
  return (
    <section className="panel p-5" aria-label="Torre de control">
      <nav className="mb-4 flex flex-wrap gap-1 border-b border-line" aria-label="Actos">
        {ACTS.map((a) => (
          <button
            key={a.id}
            type="button"
            className={`-mb-px border-b-2 px-3 py-2 text-sm ${a.id === state.actId ? "border-accent font-medium text-ink" : "border-transparent text-muted hover:text-ink"}`}
            aria-current={a.id === state.actId ? "page" : undefined}
            onClick={() => dispatch({ type: "act", actId: a.id })}
          >
            <span className="font-display">{a.id}</span> · {a.name}
          </button>
        ))}
      </nav>
      <div className="grid gap-5 md:grid-cols-[auto_1fr_auto] md:items-center">
        <div>
          <div className="eyebrow">{act.day} · reloj del caso</div>
          <div className="mt-1 flex items-baseline gap-3">
            <span className="font-display text-[44px] font-medium leading-none tabular-nums text-ink">{caseClock(state)}</span>
            <span className={`text-sm tabular-nums ${late ? "text-danger" : remaining <= 15 ? "text-warn" : "text-muted"}`}>
              {late ? "fuera de tiempo" : "faltan"} {formatCountdown(remaining)}
            </span>
          </div>
          <div className="mt-1 text-xs text-muted">Límite {act.deadlineLabel.toLowerCase()} · {act.mix}</div>
        </div>
        <div className="min-w-0">
          <p className="font-display text-[15px] text-ink">“{act.question}”</p>
          <p className="mt-1 text-xs text-muted">Entregable del acto: {act.deliverable}</p>
          <div className="mt-3 h-1.5 w-full rounded bg-line" role="progressbar" aria-valuenow={Math.round(progress)} aria-valuemin={0} aria-valuemax={100} aria-label="Avance del acto">
            <div className={`h-1.5 rounded ${late ? "bg-danger" : "bg-accent-fill"}`} style={{ width: `${progress}%` }} />
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {state.running ? (
            <button type="button" className="btn" onClick={() => dispatch({ type: "pause" })}>⏸ Pausar</button>
          ) : (
            <button type="button" className="btn btn-primary" disabled={!!state.pending || finished} onClick={() => dispatch({ type: "play" })}>
              ▶ {state.clock === 0 ? "Iniciar" : "Continuar"}
            </button>
          )}
          <div className="inline-flex rounded-md border border-line" role="group" aria-label="Velocidad">
            {SPEEDS.map((s) => (
              <button
                key={s}
                type="button"
                className={`px-2.5 py-1.5 text-xs tabular-nums ${state.speed === s ? "bg-surface-2 font-medium text-ink" : "text-muted hover:text-ink"}`}
                aria-pressed={state.speed === s}
                onClick={() => dispatch({ type: "speed", speed: s })}
              >
                ×{s}
              </button>
            ))}
          </div>
          <button type="button" className="btn btn-ghost" onClick={() => dispatch({ type: "reset" })}>Reiniciar</button>
        </div>
      </div>
    </section>
  );
}
