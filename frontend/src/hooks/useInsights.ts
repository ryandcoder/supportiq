import { useAppState } from "../context/AppState";
import { getInsights } from "../services/api";
import { useApi } from "./useApi";

export function useInsights() {
  const { filters } = useAppState();
  return useApi(() => getInsights(filters), [JSON.stringify(filters)]);
}
