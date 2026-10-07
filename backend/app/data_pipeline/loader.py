"""Replaces the contents of the database with cleaned data (used by scripts/load_data.py and POST /api/upload)."""
import pandas as pd

from app.database.models import Base

BOOL_COLS = ["is_legacy", "category_mismatch", "response_breached", "resolution_breached",
             "is_reopened", "is_reopen_child", "is_incident_ticket"]
DATE_COLS = ["created_at", "first_response_at", "closed_at"]


def prepare_tickets(tickets: pd.DataFrame) -> pd.DataFrame:
    """Makes dtypes database-friendly. Safe to call on frames read from CSV or straight from clean()."""
    t = tickets.copy()
    for c in DATE_COLS:
        t[c] = pd.to_datetime(t[c], errors="coerce")
    for c in BOOL_COLS:
        t[c] = t[c].astype("boolean")
    t["assigned_agent_id"] = t["assigned_agent_id"].astype("Int64")
    return t


def replace_all(engine, agents: pd.DataFrame, merchants: pd.DataFrame, tickets: pd.DataFrame) -> dict:
    """Drops and recreates the tables and loads the data in ONE transaction:
    if anything fails, PostgreSQL rolls back and the existing data stays as it was."""
    tickets = prepare_tickets(tickets)
    with engine.begin() as conn:
        Base.metadata.drop_all(conn)
        Base.metadata.create_all(conn)
        agents.to_sql("agents", conn, if_exists="append", index=False)           # parents first (foreign keys)
        merchants.to_sql("merchants", conn, if_exists="append", index=False)
        tickets.to_sql("tickets", conn, if_exists="append", index=False, chunksize=500)
    return {"agents": len(agents), "merchants": len(merchants), "tickets": len(tickets)}
