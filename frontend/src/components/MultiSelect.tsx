import { useEffect, useRef, useState } from "react";
import { Icon, IconName } from "./Icons";

export interface Option<T> {
  value: T;
  label: string;
}

/** Pill button that opens a checkbox list (with a search box for long lists). No selection = no filter. */
export default function MultiSelect<T extends string | number>({ label, icon, options, selected, onChange }: {
  label: string;
  icon?: IconName;
  options: Option<T>[];
  selected: T[];
  onChange: (next: T[]) => void;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  useEffect(() => {
    if (!open) setQuery("");
  }, [open]);

  const toggle = (v: T) => onChange(selected.includes(v) ? selected.filter((x) => x !== v) : [...selected, v]);
  const visible = options.filter((o) => o.label.toLowerCase().includes(query.trim().toLowerCase()));
  const active = selected.length > 0;

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className={`pill ${active ? "!border-teal !bg-teal-soft font-medium text-teal" : ""}`}
      >
        {icon && <Icon name={icon} className="h-4 w-4" />}
        <span>{label}</span>
        {active && <span className="rounded-full bg-teal px-1.5 text-xs font-semibold text-paper">{selected.length}</span>}
        <Icon name="chevronDown" className={`h-3.5 w-3.5 opacity-60 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div className="absolute left-0 z-40 mt-2 w-64 rounded-xl border border-line bg-card p-2 shadow-xl">
          {options.length > 8 && (
            <div className="relative mb-2">
              <Icon name="search" className="pointer-events-none absolute left-2.5 top-2 h-4 w-4 text-muted" />
              <input
                autoFocus
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={`Search ${label.toLowerCase()}…`}
                className="input w-full !py-1.5 pl-8"
              />
            </div>
          )}
          <div className="max-h-60 overflow-auto">
            {visible.map((o) => (
              <label key={String(o.value)} className="flex cursor-pointer items-center gap-2.5 rounded-lg px-2 py-1.5 text-sm hover:bg-teal-soft">
                <input type="checkbox" className="h-4 w-4 accent-teal" checked={selected.includes(o.value)} onChange={() => toggle(o.value)} />
                <span className="truncate">{o.label}</span>
              </label>
            ))}
            {visible.length === 0 && <p className="px-2 py-3 text-sm text-muted">Nothing found</p>}
          </div>
          {active && (
            <button type="button" className="btn-ghost mt-1 w-full justify-center" onClick={() => onChange([])}>
              Clear {label.toLowerCase()}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
