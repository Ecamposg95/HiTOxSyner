import { useEffect, useReducer } from "react";
import { Navigate } from "react-router-dom";
import { AgentFeed } from "../components/pressure/AgentFeed";
import { ControlTower } from "../components/pressure/ControlTower";
import { DirectorPanel } from "../components/pressure/DirectorPanel";
import { ObserverNotes } from "../components/pressure/ObserverNotes";
import { PodDesk } from "../components/pressure/PodDesk";
import { PageHeader } from "../components/PageHeader";
import { initialState, reduce } from "../lib/pressureRoom";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";

/** 1 segundo real = 1 minuto del caso a ×1. */
const TICK_MS = 1000;

export function PressureRoomPage() {
  const user = useAuthStore((s) => s.user);
  const [state, dispatch] = useReducer(reduce, "I", initialState);
  useEffect(() => {
    if (!state.running) return;
    const id = window.setInterval(() => dispatch({ type: "tick", dt: state.speed }), TICK_MS);
    return () => window.clearInterval(id);
  }, [state.running, state.speed]);
  if (!can(user, "manageLab")) return <Navigate to="/" replace />;
  return (
    <>
      <PageHeader
        eyebrow="Liderazgo · Project ORION"
        title="Pressure Room · Torre de Control"
        subtitle="Simulación en cuatro actos para someter a presión a los Pressure Pods. Los agentes proponen; el facilitador decide."
        action={<span className="badge badge-warn">Simulación demo · datos ficticios</span>}
      />
      <div className="space-y-5">
        <ControlTower state={state} dispatch={dispatch} />
        <div className="grid gap-5 lg:grid-cols-12">
          <div className="lg:col-span-5 lg:h-[640px]">
            <AgentFeed state={state} />
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:col-span-4 lg:grid-cols-1 xl:grid-cols-2">
            {state.pods.map((pod) => (
              <PodDesk key={pod.number} pod={pod} state={state} />
            ))}
          </div>
          <div className="space-y-5 lg:col-span-3">
            <DirectorPanel state={state} dispatch={dispatch} />
            <ObserverNotes state={state} />
          </div>
        </div>
      </div>
    </>
  );
}
