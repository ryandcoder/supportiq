import { createContext, ReactNode, useContext, useState } from "react";
import { useApi } from "../hooks/useApi";
import { getDashboard } from "../services/api";
import type { Dashboard, Filters } from "../types";

interface AppState {
  filters: Filters;
  setFilters: (f: Filters) => void;
  dashboard: Dashboard | null;
  loading: boolean;
  error: string | null;
}

const Ctx = createContext<AppState | null>(null);

/** Filters and dashboard data are shared by all analytics pages, so filters survive page changes. */
export function AppStateProvider({ children }: { children: ReactNode }) {
  const [filters, setFilters] = useState<Filters>({});
  const { data, loading, error } = useApi(() => getDashboard(filters), [JSON.stringify(filters)]);
  return <Ctx.Provider value={{ filters, setFilters, dashboard: data, loading, error }}>{children}</Ctx.Provider>;
}

export function useAppState(): AppState {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAppState must be used inside AppStateProvider");
  return v;
}
