import { useTheme } from "../hooks/useTheme";

/** Concrete colours for Recharts (SVG), chosen per theme so charts stay readable in dark mode. */
export function usePalette() {
  const { theme } = useTheme();
  const dark = theme === "dark";
  return {
    teal: dark ? "#4fb3ae" : "#0f5f63",
    tealLight: dark ? "#2d6f6c" : "#7fb5b0",
    amber: dark ? "#e0a64a" : "#b7791f",
    rust: dark ? "#e07a68" : "#a63d2f",
    sage: dark ? "#5fb98d" : "#2f7d5b",
    slate: dark ? "#8a9aa3" : "#5b6b73",
    grid: dark ? "#2b3337" : "#e3dac9",
    axis: dark ? "#9aa29f" : "#6b6f6c",
    tooltipBg: dark ? "#1b2124" : "#fcfaf5",
    tooltipBorder: dark ? "#2b3337" : "#e3dac9",
    ink: dark ? "#ece6d8" : "#1f2a2e",
    priority: {
      P1: dark ? "#e07a68" : "#a63d2f",
      P2: dark ? "#e0a64a" : "#b7791f",
      P3: dark ? "#4fb3ae" : "#0f5f63",
      P4: dark ? "#8a9aa3" : "#5b6b73",
    } as Record<string, string>,
  };
}
