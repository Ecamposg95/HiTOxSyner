import { create } from "zustand";
import { engagementsApi } from "../api/engagements";
import type { Engagement } from "../types";

const STORAGE_KEY = "tr.engagement";

interface EngagementState {
  engagements: Engagement[];
  current: Engagement | null;
  loaded: boolean;
  load: () => Promise<void>;
  select: (id: string) => void;
  refreshCurrent: () => Promise<void>;
  reset: () => void;
}

function readSaved(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

export const useEngagementStore = create<EngagementState>((set, get) => ({
  engagements: [],
  current: null,
  loaded: false,
  async load() {
    const engagements = await engagementsApi.list();
    const saved = readSaved();
    const current = engagements.find((e) => e.id === saved) ?? engagements[0] ?? null;
    set({ engagements, current, loaded: true });
  },
  reset() {
    set({ engagements: [], current: null, loaded: false });
  },
  select(id) {
    const current = get().engagements.find((e) => e.id === id) ?? null;
    set({ current });
    try {
      localStorage.setItem(STORAGE_KEY, id);
    } catch {
      /* almacenamiento no disponible */
    }
  },
  async refreshCurrent() {
    const current = get().current;
    if (!current) return;
    const fresh = await engagementsApi.get(current.id);
    set({ current: fresh, engagements: get().engagements.map((e) => (e.id === fresh.id ? fresh : e)) });
  },
}));
