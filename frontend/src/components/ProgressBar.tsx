export function ProgressBar({ value }: { value: number }) {
  return (
    <div className="h-1.5 w-full rounded bg-line">
      <div className="h-1.5 rounded bg-ink" style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
    </div>
  );
}
