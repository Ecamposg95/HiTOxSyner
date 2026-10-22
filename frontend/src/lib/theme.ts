export type Theme = "dark" | "light";
export const THEME_KEY = "hito-theme";

export function parseTheme(raw: string | null | undefined): Theme {
  return raw === "light" ? "light" : "dark";
}
