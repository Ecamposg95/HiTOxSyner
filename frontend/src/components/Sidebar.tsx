import { NavLink } from "react-router-dom";
import { NAV_ITEMS } from "../lib/labels";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const user = useAuthStore((s) => s.user);
  const items = NAV_ITEMS.filter((item) => item.to !== "/lab" || can(user, "viewLabSummary"));
  return (
    <aside className="flex h-full w-60 flex-col border-r border-line bg-white">
      <div className="border-b border-line px-5 py-4">
        <div className="text-xs font-semibold tracking-[0.2em] text-ink">SYNER × HiTO</div>
        <div className="mt-1 text-xs text-muted">Transformation Room</div>
      </div>
      <nav className="flex-1 space-y-0.5 px-3 py-3">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={onNavigate}
            className={({ isActive }) =>
              `block rounded-md px-3 py-2 text-sm ${isActive ? "bg-canvas font-medium text-ink" : "text-muted hover:bg-canvas hover:text-ink"}`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-line px-5 py-3 text-[11px] text-muted">Private advisory workspace</div>
    </aside>
  );
}
