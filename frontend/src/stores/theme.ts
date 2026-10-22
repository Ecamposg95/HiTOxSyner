import { create } from "zustand";
import { parseTheme, THEME_KEY, type Theme } from "../lib/theme.ts";

interface ThemeState {
  theme: Theme;
  toggle: () => void;
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  theme: parseTheme(document.documentElement.dataset.theme),
  toggle: () => {
    const next: Theme = get().theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch {
      /* almacenamiento no disponible */
    }
    set({ theme: next });
  },
}));
