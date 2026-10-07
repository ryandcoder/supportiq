export interface Kpis {
  total_tickets: number;
  open_tickets: number;
  resolved_tickets: number;
  resolution_rate: number | null;
  sla_compliance: number | null;
  response_sla_compliance: number | null;
  avg_resolution_hours: number | null;
  median_resolution_hours: number | null;
  avg_first_response_hours: number | null;
  avg_csat: number | null;
  csat_responses: number;
  csat_response_rate: number | null;
  reopen_rate: number | null;
  category_mismatch_rate: number | null;
}

export interface GroupRow {
  name: string;
  tickets: number;
  share: number | null;
  open: number;
  resolved: number;
  avg_resolution_hours: number | null;
  median_resolution_hours: number | null;
  sla_compliance: number | null;
  avg_csat: number | null;
  csat_responses: number;
  reopen_rate: number | null;
}

export interface AgentRow {
  agent_id: number;
  agent_name: string;
  tier: string;
  primary_category: string;
  tickets_assigned: number;
  tickets_resolved: number;
  avg_resolution_hours: number | null;
  median_resolution_hours: number | null;
  sla_compliance: number | null;
  avg_csat: number | null;
  csat_responses: number;
  reopen_rate: number | null;
  mismatch_rate: number | null;
}

export interface Dashboard {
  kpis: Kpis;
  volume_by_month: { month: string; tickets: number; open: number }[];
  by_category: GroupRow[];
  by_priority: GroupRow[];
  by_status: { name: string; tickets: number }[];
  sla: { within_sla: number; breached: number; resolved: number };
  by_merchant_sector: GroupRow[];
  by_merchant_region: GroupRow[];
  by_merchant_tier: GroupRow[];
  by_agent_tier: GroupRow[];
  csat_by_resolution_band: { band: string; responses: number; avg_csat: number | null }[];
  routing: { name: string; tickets: number; resolved: number; median_resolution_hours: number | null; sla_compliance: number | null }[];
  agents: AgentRow[];
  captions: Partial<Record<"volume" | "category" | "priority" | "resolution" | "sla" | "status" | "sector" | "agents", string>>;
  filters_applied: Record<string, unknown>;
}

export interface TicketRow {
  ticket_id: number;
  created_at: string;
  category: string;
  sub_category: string;
  priority: string;
  status: string;
  agent_name: string | null;
  merchant_name: string;
  merchant_sector: string;
  resolution_hours: number | null;
  csat_score: number | null;
  is_reopened: boolean;
  sla_status: "Open" | "Breached" | "Within SLA";
}

export interface TicketPage {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  items: TicketRow[];
}

export interface Filters {
  date_from?: string;
  date_to?: string;
  category?: string[];
  priority?: string[];
  status?: string[];
  agent_id?: number[];
  merchant_sector?: string[];
  merchant_region?: string[];
  merchant_tier?: string[];
}

export interface DataQuality {
  records_raw: Record<string, number>;
  records_clean: Record<string, number>;
  missing_values_raw: Record<string, Record<string, number>>;
  duplicates_removed: number;
  invalid_records_flagged: number;
  date_range: [string, string];
  status_counts: Record<string, number>;
  change_log: { table: string; action: string; rows_affected: number; detail: string }[];
}

export interface FilterOptions {
  date_min: string;
  date_max: string;
  categories: string[];
  priorities: string[];
  statuses: string[];
  agents: { id: number; name: string }[];
  merchant_sectors: string[];
  merchant_regions: string[];
  merchant_tiers: string[];
}

export interface Insight {
  id: string;
  type: string;
  text: string;
  evidence: Record<string, unknown>;
}

export interface Recommendation {
  text: string;
  basis: string; // id of the insight this recommendation comes from
}

export interface InsightsResponse {
  insights: Insight[];
  recommendations: Recommendation[];
}

export interface UploadStatus {
  enabled: boolean;
  max_mb: number;
}

export interface UploadResult {
  committed: boolean;
  report: DataQuality & { dropped_records: number };
  loaded?: { agents: number; merchants: number; tickets: number };
}
