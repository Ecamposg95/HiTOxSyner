const TONES: Record<string, string> = {
  "On Track": "bg-emerald-50 text-emerald-800 border-emerald-200",
  Attention: "bg-amber-50 text-amber-800 border-amber-200",
  "At Risk": "bg-red-50 text-red-800 border-red-200",
  Critical: "bg-red-50 text-red-800 border-red-200",
  High: "bg-amber-50 text-amber-800 border-amber-200",
  Blocked: "bg-red-50 text-red-800 border-red-200",
  Completed: "bg-emerald-50 text-emerald-800 border-emerald-200",
  Closed: "bg-gray-100 text-gray-700 border-gray-200",
  Cancelled: "bg-gray-100 text-gray-700 border-gray-200",
  "On Hold": "bg-gray-100 text-gray-700 border-gray-200",
  Done: "bg-emerald-50 text-emerald-800 border-emerald-200",
  Approved: "bg-emerald-50 text-emerald-800 border-emerald-200",
  Slipped: "bg-red-50 text-red-800 border-red-200",
  Rejected: "bg-red-50 text-red-800 border-red-200",
  "Under Review": "bg-amber-50 text-amber-800 border-amber-200",
  Deferred: "bg-gray-100 text-gray-700 border-gray-200",
  Interno: "bg-amber-50 text-amber-800 border-amber-200",
};

export function StatusBadge({ value }: { value: string }) {
  const tone = TONES[value] ?? "bg-canvas text-ink border-line";
  return <span className={`inline-block rounded border px-2 py-0.5 text-xs font-medium ${tone}`}>{value}</span>;
}
