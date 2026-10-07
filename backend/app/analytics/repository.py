"""
SQL layer: filtering and joining happen in PostgreSQL, calculations happen in Pandas (metrics.py).
"""
import pandas as pd
from sqlalchemy import text

from app.database.queries import BASE_SELECT, FROM_JOINS, build_where, tickets_page_queries
from app.database.session import engine

from .frame import normalize


def load_tickets(filters: dict | None = None) -> pd.DataFrame:
    """Filtered + joined tickets as one DataFrame (input for every analytics function)."""
    where, params = build_where(filters)
    with engine.connect() as conn:
        df = pd.read_sql(text(BASE_SELECT + FROM_JOINS + where), conn, params=params)
    return normalize(df)


def list_tickets(filters, search, sort_by, sort_dir, page, page_size) -> dict:
    """One page of the ticket table. Filtering, search, sorting and pagination all happen in SQL."""
    data_sql, count_sql, data_params, count_params, page, page_size = tickets_page_queries(
        filters, search, sort_by, sort_dir, page, page_size)
    with engine.connect() as conn:
        total = conn.execute(text(count_sql), count_params).scalar()
        rows = conn.execute(text(data_sql), data_params).mappings().all()
    return {
        "page": page,
        "page_size": page_size,
        "total": int(total),
        "total_pages": max(1, -(-int(total) // page_size)),
        "items": [dict(r) for r in rows],
    }


def get_filter_options() -> dict:
    """Distinct values for the dashboard filter dropdowns (plain SQL)."""
    q = lambda sql: pd.read_sql(text(sql), engine)  # noqa: E731
    dates = q("SELECT MIN(created_at) AS lo, MAX(created_at) AS hi FROM tickets").iloc[0]
    return {
        "date_min": str(dates["lo"].date()),
        "date_max": str(dates["hi"].date()),
        "categories": q("SELECT DISTINCT category FROM tickets ORDER BY 1")["category"].tolist(),
        "priorities": q("SELECT DISTINCT priority FROM tickets ORDER BY 1")["priority"].tolist(),
        "statuses": q("SELECT DISTINCT status FROM tickets ORDER BY 1")["status"].tolist(),
        "agents": q("SELECT agent_id AS id, agent_name AS name FROM agents ORDER BY agent_name").to_dict("records"),
        "merchant_sectors": q("SELECT DISTINCT sector FROM merchants ORDER BY 1")["sector"].tolist(),
        "merchant_regions": q("SELECT DISTINCT region FROM merchants ORDER BY 1")["region"].tolist(),
        "merchant_tiers": q("SELECT DISTINCT tier FROM merchants ORDER BY 1")["tier"].tolist(),
    }


def sql_monthly_volume() -> pd.DataFrame:
    """Pure-SQL aggregation. Used to cross-check the Pandas monthly volume (the two must match)."""
    return pd.read_sql(text("""
        SELECT created_month AS month,
               COUNT(*)                                AS tickets,
               COUNT(*) FILTER (WHERE status = 'Open') AS open_tickets
        FROM tickets
        GROUP BY created_month
        ORDER BY created_month
    """), engine)
