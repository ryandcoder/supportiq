import type { Filters } from "../types";

/** Plain-English description of the active filters, e.g. ["Priority: P1, P2", "Created from 2025-06-01"]. */
export function describeFilters(f: Filters, agentNames: Record<number, string> = {}): string[] {
  const out: string[] = [];
  if (f.date_from || f.date_to) {
    out.push(`Created ${[f.date_from && `from ${f.date_from}`, f.date_to && `to ${f.date_to}`].filter(Boolean).join(" ")}`);
  }
  const lists: [string, string[] | undefined][] = [
    ["Category", f.category],
    ["Priority", f.priority],
    ["Status", f.status],
    ["Sector", f.merchant_sector],
    ["Region", f.merchant_region],
    ["Merchant tier", f.merchant_tier],
  ];
  for (const [label, values] of lists) if (values?.length) out.push(`${label}: ${values.join(", ")}`);
  if (f.agent_id?.length) out.push(`Agent: ${f.agent_id.map((id) => agentNames[id] ?? `#${id}`).join(", ")}`);
  return out;
}
