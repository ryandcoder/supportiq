export const pct = (x: number | null | undefined, digits = 0) =>
  x == null ? "–" : `${(x * 100).toFixed(digits)}%`;

export const hours = (x: number | null | undefined) => (x == null ? "–" : `${x.toFixed(1)}h`);

export const int = (x: number | null | undefined) => (x == null ? "–" : x.toLocaleString("en-US"));

export const score = (x: number | null | undefined) => (x == null ? "–" : x.toFixed(2));

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
/** "2026-06" -> "Jun 26" */
export const monthLabel = (ym: string) => {
  const [y, m] = ym.split("-");
  return `${MONTHS[Number(m) - 1] ?? m} ${y.slice(2)}`;
};
/** "2026-06" -> "June 2026" */
export const monthLong = (ym: string) => {
  const [y, m] = ym.split("-");
  const names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  return `${names[Number(m) - 1] ?? m} ${y}`;
};

export const shortDate = (iso: string) => iso.slice(0, 10);

/** [{month:"2025-01"}, ... {month:"2026-06"}] -> "January 2025 – June 2026" */
export const period = (months: { month: string }[]) =>
  months.length ? `${monthLong(months[0].month)} – ${monthLong(months[months.length - 1].month)}` : "";
