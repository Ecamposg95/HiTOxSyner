import { EmptyState } from "../EmptyState";
import { formatDate } from "../../lib/dates";
import { MILESTONE_STATUSES, ROADMAP_PHASES } from "../../lib/labels";
import { buildTimeline, parseLocalDate, positionPct } from "../../lib/timeline";
import type { Milestone, MilestoneStatus } from "../../types";

const MARKER: Record<MilestoneStatus, string> = {
  Done: "bg-accent-fill",
  "In Progress": "bg-accent-fill/50 border border-accent",
  Planned: "bg-muted",
  Slipped: "bg-danger",
};

export function RoadmapTimeline({ milestones, onSelect }: { milestones: Milestone[]; onSelect: (m: Milestone) => void }) {
  const model = buildTimeline(milestones);
  if (!model) return <EmptyState title="Sin hitos con fecha" />;

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const showToday = today >= model.start && today < model.end;
  const todayPct = positionPct(model, today);

  return (
    <div className="space-y-3">
      <div className="panel overflow-x-auto">
        <div className="min-w-[720px] p-4">
          <div className="flex">
            <div className="w-[120px] shrink-0" />
            <div className="relative h-6 flex-1">
              {model.months.map((mo) => (
                <span key={mo.key} className="eyebrow absolute top-0 whitespace-nowrap" style={{ left: `${mo.leftPct}%` }}>{mo.label}</span>
              ))}
            </div>
          </div>
          <div className="relative">
            {ROADMAP_PHASES.map((phase) => (
              <div key={phase} className="flex border-t border-line">
                <div className="flex w-[120px] shrink-0 items-center text-sm font-medium">{phase}</div>
                <div className="relative h-10 flex-1">
                  {model.months.map((mo) => (
                    <span key={mo.key} className="absolute inset-y-0 border-l border-line/50" style={{ left: `${mo.leftPct}%` }} aria-hidden="true" />
                  ))}
                  {model.dated.filter((m) => m.phase === phase).map((m) => {
                    const label = `${m.name} · ${formatDate(m.due_date)} · ${m.status}`;
                    return (
                      <button
                        key={m.id}
                        type="button"
                        title={label}
                        aria-label={label}
                        onClick={() => onSelect(m)}
                        className={`absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rotate-45 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${MARKER[m.status]}`}
                        style={{ left: `${positionPct(model, parseLocalDate(m.due_date as string))}%` }}
                      />
                    );
                  })}
                </div>
              </div>
            ))}
            {showToday && (
              <div className="pointer-events-none absolute inset-y-0 right-0 left-[120px]" aria-hidden="true">
                <div className="absolute inset-y-0 w-px bg-accent" style={{ left: `${todayPct}%` }}>
                  <span className="eyebrow absolute -top-0 left-1 whitespace-nowrap text-accent">Hoy</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted" aria-label="Leyenda de estados">
        {MILESTONE_STATUSES.map((s) => (
          <li key={s} className="flex items-center gap-2">
            <span className={`inline-block h-2.5 w-2.5 rotate-45 ${MARKER[s]}`} aria-hidden="true" />
            {s}
          </li>
        ))}
      </ul>
      {model.undated.length > 0 && (
        <section className="panel p-4">
          <h2 className="eyebrow mb-2">Sin fecha</h2>
          <ul className="space-y-1 text-sm">
            {model.undated.map((m) => (
              <li key={m.id}>
                <button type="button" className="text-left hover:underline" onClick={() => onSelect(m)}>
                  {m.name} <span className="text-xs text-muted">· {m.phase} · {m.status}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
