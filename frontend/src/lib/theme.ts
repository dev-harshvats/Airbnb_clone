"use client";

import { useSyncExternalStore } from "react";

export type Theme = "light" | "dark";
export const THEME_KEY = "airbnb:theme";
const EVENT = "airbnb:theme-change";

const current = (): Theme => (document.documentElement.dataset.theme === "dark" ? "dark" : "light");

export function setTheme(theme: Theme) {
  document.documentElement.dataset.theme = theme;
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch {
    /* private mode: the choice just won't survive a reload */
  }
  window.dispatchEvent(new Event(EVENT));
}

/** The active theme, kept in sync across components (and "light" while rendering on the server). */
export function useTheme(): Theme {
  return useSyncExternalStore(
    (notify) => {
      window.addEventListener(EVENT, notify);
      return () => window.removeEventListener(EVENT, notify);
    },
    current,
    () => "light",
  );
}
