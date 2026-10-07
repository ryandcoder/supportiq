import { ReactNode } from "react";
import { useAppState } from "../context/AppState";
import type { Dashboard } from "../types";

/** Handles loading / error / "no tickets match" once, for every analytics page. */
export default function DashboardGate({ children }: { children: (d: Dashboard) => ReactNode }) {
  const { dashboard, loading, error } = useAppState();

  if (error && !dashboard) {
    return (
      <div className="card border-bad p-6">
        <h2 className="text-xl font-semibold">Could not load the data</h2>
        <p className="mt-2 text-sm text-muted">{error}</p>
        <p className="mt-2 text-sm text-muted">
          Check that the API is running on port 8000 and the database is up (<code>docker compose up</code>).
        </p>
      </div>
    );
  }
  if (!dashboard) return <p className="text-muted">{loading ? "Loading…" : ""}</p>;

  if (dashboard.kpis.total_tickets === 0) {
    return (
      <div className="card p-10 text-center">
        <h2 className="text-xl font-semibold">No tickets match these filters</h2>
        <p className="mt-1 text-sm text-muted">Widen the date range or use Reset in the filter bar.</p>
      </div>
    );
  }

  return (
    <div className={`space-y-6 transition-opacity ${loading ? "opacity-60" : ""}`}>
      {error && <p className="rounded-lg border border-bad p-3 text-sm text-bad">{error}</p>}
      {children(dashboard)}
    </div>
  );
}
