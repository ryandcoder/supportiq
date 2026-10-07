import { Link } from "react-router-dom";
import ChartCard from "../components/ChartCard";
import { Icon } from "../components/Icons";
import { TYPE_STYLE, FALLBACK } from "../components/InsightsPanel";
import { Donut, HBar, VBar, VolumeChart } from "../charts/ChartBlocks";
import { usePalette } from "../charts/palette";
import { useAppState } from "../context/AppState";
import { useInsights } from "../hooks/useInsights";
import { ForceTheme } from "../hooks/useTheme";
import { describeFilters } from "../lib/describe";
import { hours, int, pct, period, score } from "../lib/format";

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="avoid-break border-l-2 border-teal pl-3">
      <div className="text-[10px] font-semibold uppercase tracking-wider text-muted">{label}</div>
      <div className="font-serif text-2xl font-semibold leading-tight">{value}</div>
      {hint && <div className="text-[11px] text-muted">{hint}</div>}
    </div>
  );
}

function Section({ title, children, className = "" }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <section className={`mt-8 ${className}`}>
      <h2 className="mb-3 border-b border-line pb-1 font-serif text-xl font-semibold">{title}</h2>
      {children}
    </section>
  );
}

function ReportBody() {
  const p = usePalette();
  const { filters, dashboard: d } = useAppState();
  const ins = useInsights();

  if (!d) return <p className="text-muted">Loading…</p>;
  if (d.kpis.total_tickets === 0) return <p className="text-muted">No tickets match the current filters, so there is nothing to report.</p>;

  const k = d.kpis;
  const names = Object.fromEntries(d.agents.map((a) => [a.agent_id, a.agent_name]));
  const scope = describeFilters(filters, names);
  const today = new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });

  return (
    <>
      <header className="border-b-2 border-teal pb-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="font-serif text-lg font-semibold text-teal">SupportIQ</div>
            <h1 className="mt-1 font-serif text-3xl font-semibold">Support performance report</h1>
          </div>
          <div className="text-right text-xs text-muted">
            <div>Generated {today}</div>
            <div>Tickets created {period(d.volume_by_month)}</div>
          </div>
        </div>
        <p className="mt-3 text-sm">
          <span className="font-semibold">Scope:</span> {scope.length ? scope.join(" · ") : "all tickets"} ({int(k.total_tickets)} tickets)
        </p>
      </header>

      <Section title="Headline numbers">
        <div className="grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-4">
          <Stat label="Total tickets" value={int(k.total_tickets)} />
          <Stat label="Open" value={int(k.open_tickets)} hint={`${int(k.resolved_tickets)} resolved`} />
          <Stat label="SLA compliance" value={pct(k.sla_compliance, 1)} hint={`First response on time ${pct(k.response_sla_compliance)}`} />
          <Stat label="Resolution rate" value={pct(k.resolution_rate, 1)} />
          <Stat label="Avg resolution" value={hours(k.avg_resolution_hours)} hint={`Median ${hours(k.median_resolution_hours)}`} />
          <Stat label="Avg CSAT (0–1)" value={score(k.avg_csat)} hint={`${int(k.csat_responses)} responses`} />
          <Stat label="Reopen rate" value={pct(k.reopen_rate, 1)} />
          <Stat label="First response" value={hours(k.avg_first_response_hours)} hint="average" />
        </div>
      </Section>

      <Section title="Key insights">
        {!ins.data ? (
          <p className="text-sm text-muted">Calculating…</p>
        ) : ins.data.insights.length === 0 ? (
          <p className="text-sm text-muted">Not enough resolved tickets in this selection to draw reliable conclusions.</p>
        ) : (
          <ul className="space-y-2.5">
            {ins.data.insights.map((i) => (
              <li key={i.id} className={`avoid-break border-l-4 pl-3 text-sm leading-relaxed ${(TYPE_STYLE[i.type] ?? FALLBACK).border}`}>
                <span className="mr-2 text-[10px] font-semibold uppercase tracking-wider text-muted">{(TYPE_STYLE[i.type] ?? FALLBACK).label}</span>
                {i.text}
              </li>
            ))}
          </ul>
        )}
      </Section>

      {ins.data && ins.data.recommendations.length > 0 && (
        <Section title="Recommendations">
          <ol className="space-y-2">
            {ins.data.recommendations.map((r, i) => (
              <li key={i} className="avoid-break flex gap-3 text-sm leading-relaxed">
                <span className="font-serif text-lg font-semibold text-teal">{i + 1}</span>
                <span>{r.text}</span>
              </li>
            ))}
          </ol>
        </Section>
      )}

      <Section title="Charts" className="print-break">
        <div className="space-y-5">
          <ChartCard title="Ticket volume over time" caption={d.captions.volume}>
            <VolumeChart data={d.volume_by_month} height={200} />
          </ChartCard>
          <ChartCard title="Tickets by category" caption={d.captions.category}>
            <HBar label="Tickets" height={250} format={int} data={d.by_category.map((c) => ({ name: c.name, value: c.tickets }))} />
          </ChartCard>
          <div className="grid gap-5 sm:grid-cols-2">
            <ChartCard title="Tickets by priority" caption={d.captions.priority}>
              <VBar label="Tickets" height={200} format={int} colors={p.priority} data={d.by_priority.map((c) => ({ name: c.name, value: c.tickets }))} />
            </ChartCard>
            <ChartCard title="SLA compliance" caption={d.captions.sla}>
              <Donut
                height={200}
                data={[
                  { name: "Within SLA", value: d.sla.within_sla, color: p.sage },
                  { name: "SLA breached", value: d.sla.breached, color: p.rust },
                ]}
                centerValue={pct(k.sla_compliance)}
                centerLabel="within SLA"
              />
            </ChartCard>
          </div>
          <ChartCard title="Average resolution time by category" caption={d.captions.resolution}>
            <HBar label="Avg resolution" height={250} color={p.amber} format={(v) => `${v.toFixed(0)}h`} data={d.by_category.map((c) => ({ name: c.name, value: c.avg_resolution_hours }))} />
          </ChartCard>
        </div>
      </Section>

      {d.agents.length > 0 && (
        <Section title="Agent performance (top 10 by tickets resolved)" className="avoid-break">
          <table className="w-full text-sm">
            <thead className="border-b border-line">
              <tr>
                <th className="th">Agent</th><th className="th">Tier</th>
                <th className="th text-right">Resolved</th><th className="th text-right">Avg resolution</th>
                <th className="th text-right">SLA</th><th className="th text-right">CSAT</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {d.agents.slice(0, 10).map((a) => (
                <tr key={a.agent_id}>
                  <td className="td font-medium">{a.agent_name}</td>
                  <td className="td text-muted">{a.tier}</td>
                  <td className="td text-right">{int(a.tickets_resolved)}</td>
                  <td className="td text-right">{hours(a.avg_resolution_hours)}</td>
                  <td className="td text-right">{pct(a.sla_compliance)}</td>
                  <td className="td text-right">{score(a.avg_csat)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      )}

      <p className="mt-8 border-t border-line pt-3 text-[11px] leading-relaxed text-muted">
        Definitions: resolution time, SLA compliance and CSAT use resolved tickets only. SLA compliance is the share of resolved tickets
        that did not breach their resolution target. CSAT is on a 0–1 scale and averages only tickets with a survey response. Reopen rate is
        reopened tickets divided by original tickets. Insights are calculated from the data; comparisons need at least 30 resolved tickets per group.
      </p>
      <div className="print-footer">SupportIQ · Support performance report · generated {today}</div>
    </>
  );
}

export default function Report() {
  return (
    <ForceTheme theme="light">
      <div className="force-light min-h-screen bg-line pb-10 text-ink print:bg-white print:pb-0">
        <div className="no-print sticky top-0 z-30 border-b border-line bg-card/95 backdrop-blur">
          <div className="mx-auto flex max-w-[860px] flex-wrap items-center justify-between gap-3 px-4 py-3">
            <Link to="/" className="btn"><Icon name="arrowLeft" /> Back to dashboard</Link>
            <div className="flex items-center gap-3">
              <span className="hidden text-xs text-muted sm:inline">In the print window choose “Save as PDF”.</span>
              <button className="btn-primary" onClick={() => window.print()}>
                <Icon name="printer" /> Print / Save as PDF
              </button>
            </div>
          </div>
        </div>

        <article className="mx-auto mt-6 max-w-[860px] rounded-xl border border-line bg-card p-8 shadow-xl sm:p-12 print:mt-0 print:max-w-none print:rounded-none print:border-0 print:p-0 print:shadow-none">
          <ReportBody />
        </article>
      </div>
    </ForceTheme>
  );
}
