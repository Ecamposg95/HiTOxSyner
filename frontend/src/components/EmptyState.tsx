export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="card px-6 py-10 text-center">
      <svg className="mx-auto mb-3 stroke-muted" width="32" height="32" viewBox="0 0 32 32" fill="none" strokeWidth="1.5" aria-hidden="true">
        <circle cx="16" cy="16" r="12" />
      </svg>
      <div className="font-display text-base text-ink">{title}</div>
      {hint && <div className="mt-1 text-xs text-muted">{hint}</div>}
    </div>
  );
}
