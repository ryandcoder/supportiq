import { useEffect, useState } from "react";
import { useApi, useDebounced } from "../hooks/useApi";
import { hours, int, score, shortDate } from "../lib/format";
import { getTickets } from "../services/api";
import type { Filters } from "../types";
import { PriorityBadge, SlaBadge, StatusBadge } from "./Badges";
import { Icon } from "./Icons";

const PAGE_SIZE = 15;

const COLUMNS: { key: string; label: string; align?: "right" }[] = [
  { key: "ticket_id", label: "Ticket" },
  { key: "created_at", label: "Created" },
  { key: "category", label: "Category" },
  { key: "priority", label: "Priority" },
  { key: "status", label: "Status" },
  { key: "agent_name", label: "Agent" },
  { key: "merchant_name", label: "Merchant" },
  { key: "resolution_hours", label: "Resolution", align: "right" },
  { key: "sla_status", label: "SLA" },
  { key: "csat_score", label: "CSAT", align: "right" },
];

/** Search, sorting and pagination all run on the server (SQL), so only one page is ever loaded. */
export default function TicketTable({ filters }: { filters: Filters }) {
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const q = useDebounced(search, 300);
  const filterKey = JSON.stringify(filters);

  // any change to search / sort / filters returns to page 1
  useEffect(() => setPage(1), [q, sortBy, sortDir, filterKey]);

  const { data, loading, error } = useApi(
    () => getTickets(filters, { search: q, sortBy, sortDir, page, pageSize: PAGE_SIZE }),
    [filterKey, q, sortBy, sortDir, page],
  );

  const onSort = (key: string) => {
    if (key === sortBy) setSortDir(sortDir === "asc" ? "desc" : "asc");
    else {
      setSortBy(key);
      setSortDir("asc");
    }
  };

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="relative w-full max-w-sm">
          <Icon name="search" className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search ticket, category, merchant or agent…"
            className="input w-full !py-2 pl-9"
          />
        </div>
        <span className="text-sm text-muted">{data ? `${int(data.total)} tickets` : ""}</span>
      </div>

      {error && <p className="mb-2 text-sm text-bad">{error}</p>}

      <div className={`overflow-x-auto transition-opacity ${loading ? "opacity-60" : ""}`}>
        <table className="w-full">
          <thead className="border-b border-line">
            <tr>
              {COLUMNS.map((c) => (
                <th key={c.key} onClick={() => onSort(c.key)} className={`th cursor-pointer select-none ${c.align === "right" ? "text-right" : ""}`}>
                  {c.label} {sortBy === c.key ? (sortDir === "asc" ? "↑" : "↓") : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {data?.items.map((t) => (
              <tr key={t.ticket_id} className="hover:bg-paper">
                <td className="td font-medium">#{t.ticket_id}</td>
                <td className="td text-muted">{shortDate(t.created_at)}</td>
                <td className="td">{t.category}</td>
                <td className="td"><PriorityBadge value={t.priority} /></td>
                <td className="td"><StatusBadge value={t.status} /></td>
                <td className="td text-muted">{t.agent_name ?? "Unassigned"}</td>
                <td className="td">{t.merchant_name}</td>
                <td className="td text-right">{hours(t.resolution_hours)}</td>
                <td className="td"><SlaBadge value={t.sla_status} /></td>
                <td className="td text-right">{score(t.csat_score)}</td>
              </tr>
            ))}
            {data && data.items.length === 0 && (
              <tr><td className="td text-muted" colSpan={COLUMNS.length}>No tickets match.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {data && (
        <div className="mt-3 flex items-center justify-between text-sm">
          <span className="text-muted">Page {data.page} of {data.total_pages}</span>
          <div className="flex gap-2">
            <button className="btn" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
            <button className="btn" disabled={page >= data.total_pages} onClick={() => setPage(page + 1)}>Next</button>
          </div>
        </div>
      )}
    </div>
  );
}
