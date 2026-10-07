const PRIORITY: Record<string, string> = {
  P1: "bg-bad/15 text-bad",
  P2: "bg-warn/15 text-warn",
  P3: "bg-teal-soft text-teal",
  P4: "bg-line text-muted",
};
const SLA: Record<string, string> = {
  "Within SLA": "bg-good/15 text-good",
  Breached: "bg-bad/15 text-bad",
  Open: "bg-line text-muted",
};
const base = "inline-block rounded px-2 py-0.5 text-xs font-medium";

export const PriorityBadge = ({ value }: { value: string }) => (
  <span className={`${base} ${PRIORITY[value] ?? "bg-line text-muted"}`}>{value}</span>
);
export const SlaBadge = ({ value }: { value: string }) => (
  <span className={`${base} ${SLA[value] ?? "bg-line text-muted"}`}>{value}</span>
);
export const StatusBadge = ({ value }: { value: string }) => (
  <span className={`${base} ${value === "Open" ? "bg-warn/15 text-warn" : "bg-good/15 text-good"}`}>{value}</span>
);
