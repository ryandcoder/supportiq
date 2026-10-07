import { useMemo, useState } from "react";
import { hours, int, pct, score } from "../lib/format";
import type { AgentRow } from "../types";

type Key = "agent_name" | "tier" | "tickets_resolved" | "avg_resolution_hours" | "sla_compliance" | "avg_csat" | "reopen_rate";

const COLUMNS: { key: Key; label: string; align?: "right" }[] = [
  { key: "agent_name", label: "Agent" },
  { key: "tier", label: "Tier" },
  { key: "tickets_resolved", label: "Resolved", align: "right" },
  { key: "avg_resolution_hours", label: "Avg resolution", align: "right" },
  { key: "sla_compliance", label: "SLA compliance", align: "right" },
  { key: "avg_csat", label: "Avg CSAT", align: "right" },
  { key: "reopen_rate", label: "Reopen rate", align: "right" },
];

export default function AgentTable({ agents }: { agents: AgentRow[] }) {
  const [sortKey, setSortKey] = useState<Key>("tickets_resolved");
  const [desc, setDesc] = useState(true);

  const rows = useMemo(() => {
    const sorted = [...agents].sort((a, b) => {
      const x = a[sortKey], y = b[sortKey];
      if (x == null) return 1; // nulls last
      if (y == null) return -1;
      const cmp = typeof x === "string" && typeof y === "string" ? x.localeCompare(y) : Number(x) - Number(y);
      return desc ? -cmp : cmp;
    });
    return sorted;
  }, [agents, sortKey, desc]);

  const onSort = (k: Key) => {
    if (k === sortKey) setDesc(!desc);
    else {
      setSortKey(k);
      setDesc(k !== "agent_name" && k !== "tier");
    }
  };

  if (!agents.length) return <p className="text-sm text-muted">No assigned tickets for the current selection.</p>;

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="border-b border-line">
          <tr>
            {COLUMNS.map((c) => (
              <th key={c.key} className={`th cursor-pointer select-none ${c.align === "right" ? "text-right" : ""}`} onClick={() => onSort(c.key)}>
                {c.label} {sortKey === c.key ? (desc ? "↓" : "↑") : ""}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {rows.map((a) => (
            <tr key={a.agent_id} className="hover:bg-paper">
              <td className="td font-medium">{a.agent_name}</td>
              <td className="td text-muted">{a.tier}</td>
              <td className="td text-right">{int(a.tickets_resolved)}</td>
              <td className="td text-right">{hours(a.avg_resolution_hours)}</td>
              <td className="td text-right">{pct(a.sla_compliance)}</td>
              <td className="td text-right" title={`${a.csat_responses} responses`}>{score(a.avg_csat)}</td>
              <td className="td text-right">{pct(a.reopen_rate)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
