// The old single-page dashboard was split into Overview, Breakdowns, Insights, Team and Tickets.
// This file only re-exports Overview so nothing still importing "Dashboard" breaks.
export { default } from "./Overview";
