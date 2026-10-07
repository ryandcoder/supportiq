import ChartCard from "../components/ChartCard";
import DashboardGate from "../components/DashboardGate";
import { InsightsPreview } from "../components/InsightsPanel";
import KpiCard from "../components/KpiCard";
import PageHeader from "../components/PageHeader";
import { Donut, VolumeChart } from "../charts/ChartBlocks";
import { usePalette } from "../charts/palette";
import { useAppState } from "../context/AppState";
import { hours, int, pct, period, score } from "../lib/format";

export default function Overview() {
  const p = usePalette();
  const { dashboard } = useAppState();

  return (
    <>
      <PageHeader
        eyebrow={dashboard ? period(dashboard.volume_by_month) : undefined}
        title="Support performance"
        subtitle="Resolution time, SLA compliance and CSAT use resolved tickets only. Open tickets are counted in volume."
      />
      <DashboardGate>
        {(d) => {
          const k = d.kpis;
          return (
            <>
              <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                <KpiCard label="Total tickets" value={int(k.total_tickets)} />
                <KpiCard label="Open tickets" value={int(k.open_tickets)} hint={`${pct(k.total_tickets ? k.open_tickets / k.total_tickets : null)} of all tickets`} />
                <KpiCard label="Resolved tickets" value={int(k.resolved_tickets)} />
                <KpiCard label="Resolution rate" value={pct(k.resolution_rate, 1)} />
                <KpiCard label="SLA compliance" value={pct(k.sla_compliance, 1)} hint={`First response on time: ${pct(k.response_sla_compliance)}`} />
                <KpiCard label="Avg resolution time" value={hours(k.avg_resolution_hours)} hint={`Median ${hours(k.median_resolution_hours)}`} />
                <KpiCard label="Avg CSAT (0–1)" value={score(k.avg_csat)} hint={`${int(k.csat_responses)} responses (${pct(k.csat_response_rate)} of resolved)`} />
                <KpiCard label="Reopen rate" value={pct(k.reopen_rate, 1)} hint="Reopened ÷ original tickets" />
              </div>

              <div className="grid gap-4 lg:grid-cols-3">
                <ChartCard title="Ticket volume over time" caption={d.captions.volume} className="lg:col-span-2">
                  <VolumeChart data={d.volume_by_month} />
                </ChartCard>
                <ChartCard title="Tickets by status" caption={d.captions.status}>
                  <Donut
                    data={d.by_status.map((s) => ({ name: s.name, value: s.tickets, color: s.name === "Open" ? p.amber : p.teal }))}
                    centerValue={int(k.total_tickets)}
                    centerLabel="tickets"
                  />
                </ChartCard>
              </div>

              <div className="grid gap-4 lg:grid-cols-3">
                <ChartCard title="SLA compliance" caption={d.captions.sla}>
                  <Donut
                    data={[
                      { name: "Within SLA", value: d.sla.within_sla, color: p.sage },
                      { name: "SLA breached", value: d.sla.breached, color: p.rust },
                    ]}
                    centerValue={pct(k.sla_compliance)}
                    centerLabel="within SLA"
                  />
                </ChartCard>
                <div className="lg:col-span-2">
                  <InsightsPreview />
                </div>
              </div>
            </>
          );
        }}
      </DashboardGate>
    </>
  );
}
