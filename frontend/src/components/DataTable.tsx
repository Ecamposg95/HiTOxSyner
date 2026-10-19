import type { ReactNode } from "react";

export interface Column<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  className?: string;
}

export function DataTable<T extends { id: string }>({ columns, rows, onRowClick, empty }: {
  columns: Column<T>[];
  rows: T[];
  onRowClick?: (row: T) => void;
  empty?: ReactNode;
}) {
  if (rows.length === 0) return <>{empty ?? null}</>;
  return (
    <div className="card overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-line text-left text-[11px] uppercase tracking-wide text-muted">
            {columns.map((c) => (
              <th key={c.key} className={`px-4 py-2 font-medium ${c.className ?? ""}`}>{c.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.id}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              onKeyDown={onRowClick ? (e) => { if (e.target !== e.currentTarget) return; if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onRowClick(row); } } : undefined}
              tabIndex={onRowClick ? 0 : undefined}
              role={onRowClick ? "button" : undefined}
              className={`border-b border-line last:border-0 ${onRowClick ? "cursor-pointer hover:bg-canvas focus:bg-canvas focus:outline-none" : ""}`}
            >
              {columns.map((c) => (
                <td key={c.key} className={`px-4 py-2.5 align-top ${c.className ?? ""}`}>{c.render(row)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
