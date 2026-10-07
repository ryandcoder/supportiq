import ChartCard from "../components/ChartCard";
import DashboardGate from "../components/DashboardGate";
import PageHeader from "../components/PageHeader";
import { HBar, VBar } from "../charts/ChartBlocks";
import { usePalette } from "../charts/palette";
import { int } from "../lib/format";

export default function Breakdowns() {
  const p = usePalette();
  return (
    <>
      <PageHeader eyebrow="Where tickets come from" title="Breakdowns" subtitle="Volume and resolution time by category, priority and merchant." />
      <DashboardGate>
        {(d) => (
          <div className="grid gap-4 lg:grid-cols-3">
            <ChartCard title="Tickets by category" caption={d.captions.category} className="lg:col-span-2">
              <HBar label="Tickets" format={int} data={d.by_category.map((c) => ({ name: c.name, value: c.tickets }))} />
            </ChartCard>
            <ChartCard title="Tickets by priority" caption={d.captions.priority}>
              <VBar label="Tickets" format={int} colors={p.priority} data={d.by_priority.map((c) => ({ name: c.name, value: c.tickets }))} />
            </ChartCard>

            <ChartCard title="Average resolution time by category" caption={d.captions.resolution} className="lg:col-span-2">
              <HBar label="Avg resolution" color={p.amber} format={(v) => `${v.toFixed(0)}h`} data={d.by_category.map((c) => ({ name: c.name, value: c.avg_resolution_hours }))} />
            </ChartCard>
            <ChartCard
              title="CSAT by resolution time"
              caption={d.csat_by_resolution_band.length ? "Average satisfaction for each resolution-time band (resolved tickets with a survey response)." : undefined}
            >
              <VBar label="Avg CSAT" color={p.tealLight} yDomain={[0, 1]} format={(v) => v.toFixed(1)} data={d.csat_by_resolution_band.map((b) => ({ name: b.band, value: b.avg_csat }))} />
            </ChartCard>

            <ChartCard title="Tickets by merchant sector" caption={d.captions.sector} className="lg:col-span-2">
              <HBar label="Tickets" color={p.slate} format={int} data={d.by_merchant_sector.map((c) => ({ name: c.name, value: c.tickets }))} />
            </ChartCard>
            <ChartCard title="Tickets by merchant region">
              <HBar label="Tickets" color={p.slate} format={int} data={d.by_merchant_region.map((c) => ({ name: c.name, value: c.tickets }))} />
            </ChartCard>
          </div>
        )}
      </DashboardGate>
    </>
  );
}
