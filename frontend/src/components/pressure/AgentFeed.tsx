import { useEffect, useRef } from "react";
import { ACTORS, effectiveAt, firedEvents, formatClock, getAct, typingActor, type ActorKind, type SimEvent, type SimState } from "../../lib/pressureRoom";
import { initials } from "../../lib/format";

const KIND_CLASS: Record<ActorKind, string> = {
  client: "bg-danger/15 text-danger",
  vendor: "bg-warn/15 text-warn",
  hito: "bg-accent/15 text-accent",
  facilitator: "bg-surface-2 text-muted",
};

function stamp(ev: SimEvent, state: SimState): string {
  return formatClock(getAct(state.actId).startMinutes + effectiveAt(ev, state));
}

function Entry({ ev, state }: { ev: SimEvent; state: SimState }) {
  if (ev.kind === "release" || ev.kind === "end") {
    return (
      <li className="rounded-md border border-accent/40 bg-accent/5 p-3">
        <div className="flex items-center justify-between gap-2">
          <span className="eyebrow text-accent">{ev.kind === "end" ? "Cierre" : `Liberación ${ev.code}`}</span>
          <span className="text-[11px] tabular-nums text-muted">{stamp(ev, state)}</span>
        </div>
        {ev.title && <div className="mt-1 font-display text-[15px] font-medium text-ink">{ev.title}</div>}
        <p className="mt-1 text-sm leading-5 text-ink">{ev.text}</p>
      </li>
    );
  }
  if (ev.kind === "observer") return null;
  const actor = ev.actor ? ACTORS[ev.actor] : null;
  if (!actor) return null;
  return (
    <li className="flex gap-3">
      <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-full text-[11px] font-semibold ${KIND_CLASS[actor.kind]}`} aria-hidden="true">
        {initials(actor.name)}
      </span>
      <div className="min-w-0">
        <div className="flex flex-wrap items-baseline gap-x-2">
          <span className="text-sm font-medium text-ink">{actor.name}</span>
          <span className="text-[11px] text-muted">{actor.role}</span>
          <span className="text-[11px] tabular-nums text-muted">{stamp(ev, state)}</span>
        </div>
        <p className="mt-0.5 text-sm leading-5 text-ink">{ev.text}</p>
      </div>
    </li>
  );
}

export function AgentFeed({ state }: { state: SimState }) {
  const items = firedEvents(state).filter((e) => e.kind !== "observer");
  const typing = typingActor(state);
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "nearest" });
  }, [items.length, typing?.id]);
  return (
    <section className="panel flex h-full flex-col p-5" aria-label="Feed de agentes">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-display text-[15px] font-medium text-ink">Sala · personajes del caso</h2>
        <span className="text-[11px] text-muted">{items.length} eventos</span>
      </div>
      <ol className="min-h-0 flex-1 space-y-4 overflow-y-auto pr-1" aria-live="polite">
        {items.map((ev) => (
          <Entry key={ev.id} ev={ev} state={state} />
        ))}
        {typing && (
          <li className="flex items-center gap-3 text-xs text-muted" aria-label={`${typing.name} está escribiendo`}>
            <span className={`grid h-8 w-8 place-items-center rounded-full text-[11px] font-semibold ${KIND_CLASS[typing.kind]}`} aria-hidden="true">
              {initials(typing.name)}
            </span>
            <span>
              {typing.name} está escribiendo<span className="animate-pulse">…</span>
            </span>
          </li>
        )}
        <div ref={endRef} />
      </ol>
    </section>
  );
}
