import axios from "axios";
import type { AgentRow, Dashboard, DataQuality, FilterOptions, Filters, InsightsResponse, TicketPage, UploadResult, UploadStatus } from "../types";

export const API_URL: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const http = axios.create({ baseURL: API_URL });

/** Builds ?a=1&a=2 style query strings (the API expects repeated parameters for lists). */
export function toQuery(filters: Filters, extra: Record<string, string | number | undefined> = {}): string {
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (Array.isArray(value)) value.forEach((v) => qs.append(key, String(v)));
    else if (value) qs.append(key, String(value));
  }
  for (const [key, value] of Object.entries(extra)) {
    if (value !== undefined && value !== "") qs.append(key, String(value));
  }
  const s = qs.toString();
  return s ? `?${s}` : "";
}

export const getDashboard = (f: Filters) =>
  http.get<Dashboard>(`/api/dashboard${toQuery(f)}`).then((r) => r.data);

export const getInsights = (f: Filters) =>
  http.get<InsightsResponse>(`/api/insights${toQuery(f)}`).then((r) => r.data);

export const getAgents = (f: Filters) =>
  http.get<AgentRow[]>(`/api/agents${toQuery(f)}`).then((r) => r.data);

export const getFilterOptions = () => http.get<FilterOptions>("/api/filters").then((r) => r.data);

export const getDataQuality = () => http.get<DataQuality>("/api/data-quality").then((r) => r.data);

export const getTickets = (
  f: Filters,
  opts: { search: string; sortBy: string; sortDir: "asc" | "desc"; page: number; pageSize: number },
) =>
  http
    .get<TicketPage>(
      `/api/tickets${toQuery(f, {
        search: opts.search.trim(),
        sort_by: opts.sortBy,
        sort_dir: opts.sortDir,
        page: opts.page,
        page_size: opts.pageSize,
      })}`,
    )
    .then((r) => r.data);

/** Plain link: the browser downloads the CSV directly. */
export const exportTicketsUrl = (f: Filters) => `${API_URL}/api/export/tickets.csv${toQuery(f)}`;

export const getUploadStatus = () => http.get<UploadStatus>("/api/upload/status").then((r) => r.data);

export const uploadFiles = (files: { agents: File; merchants: File; tickets: File }, dryRun: boolean) => {
  const body = new FormData();
  body.append("agents", files.agents);
  body.append("merchants", files.merchants);
  body.append("tickets", files.tickets);
  return http.post<UploadResult>(`/api/upload?dry_run=${dryRun}`, body).then((r) => r.data);
};

/** Turns any API error into a list of readable messages. */
export function errorMessages(e: unknown): string[] {
  const err = e as { response?: { data?: { detail?: unknown } }; message?: string };
  const detail = err?.response?.data?.detail;
  if (detail && typeof detail === "object" && "errors" in detail) return (detail as { errors: string[] }).errors;
  if (typeof detail === "string") return [detail];
  if (Array.isArray(detail)) return detail.map((d) => (typeof d === "string" ? d : (d as { msg?: string }).msg ?? "Invalid request"));
  return [err?.message ?? "Request failed. Is the API running?"];
}
