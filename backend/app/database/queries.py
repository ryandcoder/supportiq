"""
SQL builders (no SQLAlchemy import, so they can be unit-tested against SQLite).
All user input goes in as bound parameters. Column names and sort columns come from whitelists,
so user input is never pasted into the SQL text.
"""
from datetime import date, timedelta

BASE_SELECT = """
SELECT t.*,
       a.agent_name,
       a.tier             AS agent_tier,
       a.primary_category AS agent_primary_category,
       a.shift_region     AS agent_region,
       m.merchant_name,
       m.sector           AS merchant_sector,
       m.tier             AS merchant_tier,
       m.region           AS merchant_region
"""

FROM_JOINS = """
FROM tickets t
LEFT JOIN agents a    ON a.agent_id = t.assigned_agent_id
JOIN      merchants m ON m.merchant_id = t.merchant_id
"""

# filter name -> SQL column
LIST_FILTERS = {
    "category": "t.category",
    "priority": "t.priority",
    "status": "t.status",
    "agent_id": "t.assigned_agent_id",
    "merchant_sector": "m.sector",
    "merchant_region": "m.region",
    "merchant_tier": "m.tier",
}

# sort key (from the URL) -> SQL expression
SORT_COLUMNS = {
    "ticket_id": "t.ticket_id",
    "created_at": "t.created_at",
    "category": "t.category",
    "priority": "t.priority",
    "status": "t.status",
    "agent_name": "a.agent_name",
    "merchant_name": "m.merchant_name",
    "resolution_hours": "t.resolution_hours",
    "sla_status": "sla_status",
    "csat_score": "t.csat_score",
}

TICKET_COLUMNS = """
SELECT t.ticket_id, t.created_at, t.category, t.sub_category, t.priority, t.status,
       a.agent_name, m.merchant_name, m.sector AS merchant_sector,
       t.resolution_hours, t.csat_score, t.is_reopened,
       CASE WHEN t.status = 'Open' THEN 'Open'
            WHEN t.resolution_breached THEN 'Breached'
            ELSE 'Within SLA' END AS sla_status
"""

SEARCH_FIELDS = ["CAST(t.ticket_id AS TEXT)", "LOWER(t.category)", "LOWER(t.sub_category)",
                 "LOWER(m.merchant_name)", "LOWER(a.agent_name)"]

MAX_PAGE_SIZE = 100


def _escape_like(term: str) -> str:
    return term.replace("!", "!!").replace("%", "!%").replace("_", "!_")


def build_where(filters: dict | None = None, search: str | None = None) -> tuple[str, dict]:
    """Returns (' WHERE ...' or '', params). Filters: date_from/date_to ('YYYY-MM-DD', inclusive)
    plus lists for every key in LIST_FILTERS."""
    filters = filters or {}
    clauses, params = [], {}

    if filters.get("date_from"):
        clauses.append("t.created_at >= :date_from")
        params["date_from"] = filters["date_from"]
    if filters.get("date_to"):
        end = date.fromisoformat(filters["date_to"]) + timedelta(days=1)   # inclusive end date
        clauses.append("t.created_at < :date_to_excl")
        params["date_to_excl"] = end.isoformat()

    for key, col in LIST_FILTERS.items():
        values = filters.get(key)
        if values:
            names = []
            for i, v in enumerate(values):
                p = f"{key}_{i}"
                params[p] = v
                names.append(f":{p}")
            clauses.append(f"{col} IN ({', '.join(names)})")

    if search and search.strip():
        params["q"] = f"%{_escape_like(search.strip().lower())}%"
        ors = " OR ".join(f"{f} LIKE :q ESCAPE '!'" for f in SEARCH_FIELDS)
        clauses.append(f"({ors})")

    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def tickets_page_queries(filters, search, sort_by, sort_dir, page, page_size):
    """Returns (data_sql, count_sql, params) for one page of the ticket table."""
    where, params = build_where(filters, search)
    page_size = max(1, min(int(page_size), MAX_PAGE_SIZE))
    page = max(1, int(page))
    col = SORT_COLUMNS.get(sort_by, SORT_COLUMNS["created_at"])
    direction = "ASC" if str(sort_dir).lower() == "asc" else "DESC"

    data_sql = (f"{TICKET_COLUMNS}{FROM_JOINS}{where} "
                f"ORDER BY {col} {direction} NULLS LAST, t.ticket_id ASC LIMIT :limit OFFSET :offset")
    count_sql = f"SELECT COUNT(*) {FROM_JOINS}{where}"
    data_params = {**params, "limit": page_size, "offset": (page - 1) * page_size}
    return data_sql, count_sql, data_params, params, page, page_size
