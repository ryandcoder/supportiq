import { ReactNode, useState } from "react";
import { Link } from "react-router-dom";
import { useInsights } from "../hooks/useInsights";
import type { Insight } from "../types";
import { Icon } from "./Icons";

// full class names so Tailwind includes them
export const TYPE_STYLE: Record<string, { label: string; border: string }> = {
  volume: { label: "Volume", border: "border-l-teal" },
  speed: { label: "Speed", border: "border-l-warn" },
  sla: { label: "SLA", border: "border-l-bad" },
  trend: { label: "Trend", border: "border-l-warn" },
  routing: { label: "Routing", border: "border-l-bad" },
  csat: { label: "Satisfaction", border: "border-l-teal" },
  quality: { label: "Quality", border: "border-l-warn" },
  data: { label: "Data note", border: "border-l-muted" },
};
export const FALLBACK = { label: "Insight", border: "border-l-teal" };

export function InsightCard({ insight }: { insight: Insight }) {
  const t = TYPE_STYLE[insight.type] ?? FALLBACK;
  return (
    <article className={`card border-l-4 p-4 ${t.border}`}>
      <div className="text-xs font-medium uppercase tracking-wide text-muted">{t.label}</div>
      <p className="mt-1 text-sm leading-relaxed">{insight.text}</p>
    </article>
  );
}

function Collapsible({ title, subtitle, count, children }: { title: string; subtitle: string; count: number; children: ReactNode }) {
  const [open, setOpen] = useState(true);
  return (
    <section>
      <button type="button" onClick={() => setOpen(!open)} aria-expanded={open} className="flex w-full items-center justify-between gap-3 text-left">
        <span className="flex items-center gap-3">
          <span className="font-serif text-2xl font-semibold">{title}</span>
          <span className="chip">{count}</span>
        </span>
        <Icon name="chevronDown" className={`h-5 w-5 text-muted transition-transform ${open ? "" : "-rotate-90"}`} />
      </button>
      <p className="mb-3 mt-0.5 text-sm italic text-muted">{subtitle}</p>
      {open && children}
    </section>
  );
}

/** Full page: Key insights + Recommendations (each can be hidden). Every sentence is calculated from the filtered tickets. */
export default function InsightsPanel() {
  const { data, loading, error } = useInsights();

  if (error && !data) return <p className="card p-4 text-sm text-bad">Could not load insights: {error}</p>;
  if (!data) return <p className="text-sm text-muted">{loading ? "Calculating insights…" : ""}</p>;

  const { insights, recommendations } = data;
  const typeOf = (id: string) => TYPE_STYLE[insights.find((i) => i.id === id)?.type ?? ""] ?? FALLBACK;

  return (
    <div className={`space-y-8 transition-opacity ${loading ? "opacity-60" : ""}`}>
      <Collapsible
        title="Key insights"
        count={insights.length}
        subtitle="Calculated from the tickets currently in view. A comparison only appears when each group has at least 30 resolved tickets."
      >
        {insights.length === 0 ? (
          <p className="card p-4 text-sm text-muted">Not enough resolved tickets in this selection to draw reliable conclusions.</p>
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            {insights.map((i) => <InsightCard key={i.id} insight={i} />)}
          </div>
        )}
      </Collapsible>

      {recommendations.length > 0 && (
        <Collapsible
          title="Recommendations"
          count={recommendations.length}
          subtitle="Suggested follow-ups based on the findings above. They point to what to investigate and make no savings estimates."
        >
          <ol className="space-y-2">
            {recommendations.map((r, idx) => (
              <li key={idx} className="card flex gap-3 p-4">
                <span className="font-serif text-xl font-semibold text-teal">{idx + 1}</span>
                <div>
                  <p className="text-sm leading-relaxed">{r.text}</p>
                  <p className="mt-1 text-xs text-muted">Based on: {typeOf(r.basis).label.toLowerCase()} insight</p>
                </div>
              </li>
            ))}
          </ol>
        </Collapsible>
      )}
    </div>
  );
}

/** Short version for the Overview page. */
export function InsightsPreview({ limit = 4 }: { limit?: number }) {
  const { data, loading } = useInsights();
  const items = data?.insights.slice(0, limit) ?? [];
  return (
    <section className="card h-full p-4">
      <div className="flex items-start justify-between gap-3">
        <h2 className="text-lg font-semibold">Top insights</h2>
        <Link to="/insights" className="btn-ghost no-print -mr-1 -mt-1">
          See all {data ? data.insights.length : ""} <Icon name="arrowLeft" className="h-4 w-4 rotate-180" />
        </Link>
      </div>
      <p className="mt-0.5 text-sm italic text-muted">Calculated from the tickets in view.</p>
      {loading && !data && <p className="mt-3 text-sm text-muted">Calculating…</p>}
      {data && items.length === 0 && <p className="mt-3 text-sm text-muted">Not enough resolved tickets for reliable conclusions.</p>}
      <ul className="mt-3 space-y-3">
        {items.map((i) => (
          <li key={i.id} className={`border-l-4 pl-3 text-sm leading-relaxed ${(TYPE_STYLE[i.type] ?? FALLBACK).border}`}>
            {i.text}
          </li>
        ))}
      </ul>
    </section>
  );
}
