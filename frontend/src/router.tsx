import { useEffect } from "react";
import { createBrowserRouter, Navigate, Outlet } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { ActionsPage } from "./pages/ActionsPage";
import { ComingSoonPage } from "./pages/ComingSoonPage";
import { FindingsPage } from "./pages/FindingsPage";
import { InitiativesPage } from "./pages/InitiativesPage";
import { InitiativeDetailPage } from "./pages/InitiativeDetailPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { useAuthStore } from "./stores/auth";
import { useEngagementStore } from "./stores/engagement";

function RequireAuth() {
  const status = useAuthStore((s) => s.status);
  const { loaded, load } = useEngagementStore();
  useEffect(() => {
    if (status === "authenticated" && !loaded) void load();
  }, [status, loaded, load]);
  if (status === "unknown") return <div className="p-8 text-sm text-muted">Cargando…</div>;
  if (status === "anonymous") return <Navigate to="/login" replace />;
  if (!loaded) return <div className="p-8 text-sm text-muted">Cargando engagement…</div>;
  return <Outlet />;
}

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    element: <RequireAuth />,
    children: [
      {
        element: <AppShell />,
        children: [
          { path: "/", element: <DashboardPage /> },
          { path: "/findings", element: <FindingsPage /> },
          { path: "/initiatives", element: <InitiativesPage /> },
          { path: "/initiatives/:id", element: <InitiativeDetailPage /> },
          { path: "/roadmap", element: <ComingSoonPage title="Roadmap" /> },
          { path: "/actions", element: <ActionsPage /> },
          { path: "/actions/mine", element: <ActionsPage mine /> },
          { path: "/decisions", element: <ComingSoonPage title="Decisions" /> },
          { path: "/meetings", element: <ComingSoonPage title="Meetings" /> },
          { path: "/documents", element: <ComingSoonPage title="Documents" /> },
          { path: "/lab", element: <ComingSoonPage title="Leadership Lab" /> },
          { path: "*", element: <Navigate to="/" replace /> },
        ],
      },
    ],
  },
]);
