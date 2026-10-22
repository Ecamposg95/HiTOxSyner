import type { ReactNode } from "react";

export function Block({ title, children, action }: { title: string; children: ReactNode; action?: ReactNode }) {
  return (
    <section className="panel p-5">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="font-display text-[15px] font-medium text-ink">{title}</h2>
        {action}
      </div>
      {children}
    </section>
  );
}

export function Prose({ text, label }: { text: string; label?: string }) {
  const body = <p className="whitespace-pre-line text-sm leading-6">{text || <span className="text-muted">Sin contenido.</span>}</p>;
  if (!label) return body;
  return (
    <div>
      <div className="label">{label}</div>
      {body}
    </div>
  );
}
