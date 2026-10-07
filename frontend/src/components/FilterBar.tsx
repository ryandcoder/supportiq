import { useState } from "react";
import { useAppState } from "../context/AppState";
import { useApi } from "../hooks/useApi";
import { int } from "../lib/format";
import { getFilterOptions } from "../services/api";
import type { Filters } from "../types";
import { Icon } from "./Icons";
import MultiSelect from "./MultiSelect";

export function countActive(f: Filters): number {
  return Object.values(f).filter((v) => (Array.isArray(v) ? v.length > 0 : Boolean(v))).length;
}

type ListKey = "category" | "priority" | "status" | "agent_id" | "merchant_sector";

export default function FilterBar() {
  const { filters: value, setFilters, dashboard } = useAppState();
  const { data: opts, error } = useApi(getFilterOptions, []);
  const [open, setOpen] = useState(() => typeof window !== "undefined" && window.innerWidth >= 1024);
  const active = countActive(value);
  const matching = dashboard?.kpis.total_tickets;

  // keep the object free of empty values so the same selection always produces the same request
  const set = (patch: Partial<Filters>) => {
    const next: Record<string, unknown> = { ...value, ...patch };
    for (const k of Object.keys(next)) {
      const v = next[k];
      if (v === undefined || v === "" || (Array.isArray(v) && v.length === 0)) delete next[k];
    }
    setFilters(next as Filters);
  };

  const strOptions = (xs: string[]) => xs.map((x) => ({ value: x, label: x }));
  const list = (key: ListKey) => (value[key] ?? []) as never;
  const agentName = (id: number) => opts?.agents.find((a) => a.id === id)?.name ?? `#${id}`;

  // removable chips for every active filter
  const chips: { key: string; label: string; remove: () => void }[] = [];
  if (value.date_from) chips.push({ key: "from", label: `From ${value.date_from}`, remove: () => set({ date_from: undefined }) });
  if (value.date_to) chips.push({ key: "to", label: `To ${value.date_to}`, remove: () => set({ date_to: undefined }) });
  const listChips: [ListKey, string][] = [["category", "Category"], ["priority", "Priority"], ["status", "Status"], ["agent_id", "Agent"], ["merchant_sector", "Sector"]];
  for (const [key, title] of listChips) {
    for (const v of (value[key] ?? []) as (string | number)[]) {
      chips.push({
        key: `${key}-${v}`,
        label: `${title}: ${key === "agent_id" ? agentName(Number(v)) : v}`,
        remove: () => set({ [key]: (value[key] as (string | number)[]).filter((x) => x !== v) } as Partial<Filters>),
      });
    }
  }

  return (
    <section className="card no-print relative" aria-label="Filters">
      <div className="absolute inset-y-0 left-0 w-1 rounded-l-xl bg-teal" />

      <div className="flex flex-wrap items-center justify-between gap-3 py-3 pl-6 pr-4">
        <div className="flex items-center gap-3">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-teal-soft text-teal">
            <Icon name="filter" className="h-4 w-4" />
          </span>
          <div>
            <div className="text-sm font-semibold leading-tight">Filters</div>
            <div className="text-xs text-muted">
              {active === 0 ? "Showing all tickets" : `${active} active`}
              {matching !== undefined && <> · <span className="font-medium text-ink">{int(matching)}</span> tickets match</>}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button type="button" className="btn-ghost" disabled={active === 0} onClick={() => setFilters({})}>
            <Icon name="x" className="h-3.5 w-3.5" /> Reset
          </button>
          <button type="button" className="btn-ghost" onClick={() => setOpen(!open)} aria-expanded={open}>
            {open ? "Hide" : "Show"}
            <Icon name="chevronDown" className={`h-4 w-4 transition-transform ${open ? "rotate-180" : ""}`} />
          </button>
        </div>
      </div>

      {open && (
        <div className="flex flex-wrap items-center gap-2 border-t border-line py-3 pl-6 pr-4">
          {error && <span className="text-sm text-bad">Could not load filter options: {error}</span>}

          <div className={`pill ${value.date_from || value.date_to ? "!border-teal !bg-teal-soft" : ""}`}>
            <Icon name="calendar" className="h-4 w-4 text-muted" />
            <input
              type="date"
              aria-label="From date"
              className="bg-transparent text-sm outline-none"
              value={value.date_from ?? ""}
              min={opts?.date_min}
              max={value.date_to ?? opts?.date_max}
              onChange={(e) => set({ date_from: e.target.value || undefined })}
            />
            <span className="text-muted">to</span>
            <input
              type="date"
              aria-label="To date"
              className="bg-transparent text-sm outline-none"
              value={value.date_to ?? ""}
              min={value.date_from ?? opts?.date_min}
              max={opts?.date_max}
              onChange={(e) => set({ date_to: e.target.value || undefined })}
            />
          </div>

          <MultiSelect label="Category" icon="list" options={strOptions(opts?.categories ?? [])} selected={list("category")} onChange={(v) => set({ category: v as string[] })} />
          <MultiSelect label="Priority" icon="bulb" options={strOptions(opts?.priorities ?? [])} selected={list("priority")} onChange={(v) => set({ priority: v as string[] })} />
          <MultiSelect label="Status" icon="check" options={strOptions(opts?.statuses ?? [])} selected={list("status")} onChange={(v) => set({ status: v as string[] })} />
          <MultiSelect label="Agent" icon="users" options={(opts?.agents ?? []).map((a) => ({ value: a.id, label: a.name }))} selected={list("agent_id")} onChange={(v) => set({ agent_id: v as number[] })} />
          <MultiSelect label="Sector" icon="grid" options={strOptions(opts?.merchant_sectors ?? [])} selected={list("merchant_sector")} onChange={(v) => set({ merchant_sector: v as string[] })} />
        </div>
      )}

      {chips.length > 0 && (
        <div className="flex flex-wrap gap-2 border-t border-line py-3 pl-6 pr-4">
          {chips.map((c) => (
            <span key={c.key} className="chip">
              {c.label}
              <button type="button" onClick={c.remove} aria-label={`Remove ${c.label}`} className="rounded-full p-0.5 hover:bg-teal hover:text-paper">
                <Icon name="x" className="h-3 w-3" />
              </button>
            </span>
          ))}
        </div>
      )}
    </section>
  );
}
