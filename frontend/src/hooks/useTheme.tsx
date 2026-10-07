import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from "react";

export type Theme = "light" | "dark";

interface ThemeCtx {
  theme: Theme;
  toggle: () => void;
}

const Ctx = createContext<ThemeCtx>({ theme: "light", toggle: () => {} });

/** One shared theme state so the toggle, the page and every chart switch together. */
export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() =>
    document.documentElement.classList.contains("dark") ? "dark" : "light",
  );

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    try {
      localStorage.setItem("supportiq-theme", theme);
    } catch {
      /* storage can be unavailable; the theme still works for this session */
    }
  }, [theme]);

  const toggle = useCallback(() => setTheme((t) => (t === "dark" ? "light" : "dark")), []);
  return <Ctx.Provider value={{ theme, toggle }}>{children}</Ctx.Provider>;
}

export const useTheme = () => useContext(Ctx);

/** Renders children as if the app were in `theme` (used by the always-light report page). */
export function ForceTheme({ theme, children }: { theme: Theme; children: ReactNode }) {
  return <Ctx.Provider value={{ theme, toggle: () => {} }}>{children}</Ctx.Provider>;
}
