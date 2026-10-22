import { useCallback, useEffect, useState } from "react";
import { createBrowserRouter, Navigate, Outlet } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { ActionsPage } from "./pages/ActionsPage";
import { LabPage } from "./pages/LabPage";
import { DecisionsPage } from "./pages/DecisionsPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { FindingsPage } from "./pages/FindingsPage";
import { InitiativesPage } from "./pages/InitiativesPage";
import { InitiativeDetailPage } from "./pages/InitiativeDetailPage";
import { DashboardPage } from "./pages/DashboardPage";
import { MeetingsPage } from "./pages/MeetingsPage";
import { MeetingDetailPage } from "./pages/MeetingDetailPage";
import { RoadmapPage } from "./pages/RoadmapPage";
import { LoginPage } from "./pages/LoginPage";
import { PressureRoomPage } from "./pages/PressureRoomPage";
import { useAuthStore } from "./stores/auth";
import { useEngagementStore } from "./stores/engagement";

function RequireAuth() {
  const status = useAuthStore((s) => s.status);
  const { loaded, load } = useEngagementStore();
  const [error, setError] = useState(false);
  const attempt = useCallback(() => {
    setError(false);
    load().catch(() => setError(true));
  }, [load]);
  useEffect(() => {
    if (status === "authenticated" && !loaded && !error) attempt();
  }, [status, loaded, error, attempt]);
  if (status === "unknown") return <div className="p-8 text-sm text-muted">Cargando…</div>;
  if (status === "anonymous") return <Navigate to="/login" replace />;
  if (error) {
    return (
      <div className="p-8">
        <p className="text-sm text-danger">No se pudieron cargar los engagements.</p>
        <button className="btn mt-3" onClick={attempt}>Reintentar</button>
      </div>
    );
  }
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
          { path: "/roadmap", element: <RoadmapPage /> },
          { path: "/actions", element: <ActionsPage /> },
          { path: "/actions/mine", element: <ActionsPage mine /> },
          { path: "/decisions", element: <DecisionsPage /> },
          { path: "/meetings", element: <MeetingsPage /> },
          { path: "/meetings/:id", element: <MeetingDetailPage /> },
          { path: "/documents", element: <DocumentsPage /> },
          { path: "/lab", element: <LabPage /> },
          { path: "/pressure-room", element: <PressureRoomPage /> },
          { path: "*", element: <Navigate to="/" replace /> },
        ],
      },
    ],
  },
]);
