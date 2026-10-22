import { NavLink } from "react-router-dom";
import { NAV_GROUPS } from "../lib/labels";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const user = useAuthStore((s) => s.user);
  const groups = NAV_GROUPS.map((g) => ({
    ...g,
    items: g.items.filter((item) => item.to !== "/lab" || can(user, "viewLabSummary")),
  })).filter((g) => g.items.length > 0);
  return (
    <aside className="flex h-full w-60 flex-col bg-nav text-nav-ink">
      <div className="px-5 py-6">
        <div className="font-display text-2xl">HiTO</div>
        <div className="eyebrow mt-1 text-nav-ink/60">TRANSFORMATION ROOM</div>
      </div>
      <nav className="flex-1 space-y-5 overflow-y-auto py-2">
        {groups.map((group, i) => (
          <div key={group.label ?? i}>
            {group.label && <div className="eyebrow mb-1 px-5 text-nav-ink/60">{group.label}</div>}
            <div className="space-y-0.5">
              {group.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  onClick={onNavigate}
                  className={({ isActive }) =>
                    `block border-l-2 px-5 py-2 text-sm ${
                      isActive
                        ? "border-nav-accent font-medium text-nav-accent"
                        : "border-transparent text-nav-ink/70 hover:text-nav-ink"
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>
      <div className="px-5 py-4 text-[11px] text-nav-ink/60">Syner × HiTO</div>
    </aside>
  );
}
