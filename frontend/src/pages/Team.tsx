import AgentTable from "../components/AgentTable";
import ChartCard from "../components/ChartCard";
import DashboardGate from "../components/DashboardGate";
import PageHeader from "../components/PageHeader";
import { VBar } from "../charts/ChartBlocks";
import { usePalette } from "../charts/palette";
import { hours, pct } from "../lib/format";
import type { GroupRow } from "../types";

/** One sentence worked out from the rows (nothing hardcoded). */
function best(rows: GroupRow[], key: "sla_compliance" | "median_resolution_hours", what: string, higherIsBetter: boolean) {
  const usable = rows.filter((r) => r[key] != null && r.resolved >= 30);
  if (usable.length < 2) return undefined;
  const pick = usable.reduce((a, b) => ((b[key] as number) > (a[key] as number) === higherIsBetter ? b : a));
  const v = pick[key] as number;
  return `${pick.name} agents have the ${higherIsBetter ? "highest" : "shortest"} ${what} (${key === "sla_compliance" ? pct(v) : hours(v)}).`;
}

export default function Team() {
  const p = usePalette();
  return (
    <>
      <PageHeader eyebrow="Who handles what" title="Team" subtitle="Agent performance and how the support tiers compare. Click a column header to sort." />
      <DashboardGate>
        {(d) => (
          <>
            <div className="grid gap-4 md:grid-cols-2">
              <ChartCard title="SLA compliance by agent tier" caption={best(d.by_agent_tier, "sla_compliance", "SLA compliance", true)}>
                <VBar label="SLA compliance" color={p.sage} yDomain={[0, 1]} format={(v) => pct(v)} data={d.by_agent_tier.map((t) => ({ name: t.name, value: t.sla_compliance }))} />
              </ChartCard>
              <ChartCard title="Median resolution time by agent tier" caption={best(d.by_agent_tier, "median_resolution_hours", "median resolution time", false)}>
                <VBar label="Median resolution" color={p.amber} format={(v) => `${v.toFixed(0)}h`} data={d.by_agent_tier.map((t) => ({ name: t.name, value: t.median_resolution_hours }))} />
              </ChartCard>
            </div>
            <ChartCard title="Agent performance" caption={d.captions.agents}>
              <AgentTable agents={d.agents} />
            </ChartCard>
          </>
        )}
      </DashboardGate>
    </>
  );
}
