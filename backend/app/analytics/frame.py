"""
Builds the single analysis DataFrame (one row per ticket, joined with agent + merchant info).

Two ways to get the same frame:
  - from_csv()                      -> straight from data/clean/*.csv (no database needed)
  - repository.load_tickets(...)    -> from PostgreSQL (SQL does the join + filtering)
Both go through normalize() so every analytics function sees identical column names and dtypes.
"""
from pathlib import Path

import pandas as pd

DATE_COLS = ["created_at", "first_response_at", "closed_at"]
BOOL_COLS = ["is_legacy", "response_breached", "resolution_breached",
             "is_reopened", "is_reopen_child", "is_incident_ticket"]


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in DATE_COLS:
        df[c] = pd.to_datetime(df[c], errors="coerce")
    for c in BOOL_COLS:
        df[c] = df[c].fillna(False).astype(bool)
    # category_mismatch stays nullable: it is unknown (NA) for unassigned tickets
    df["category_mismatch"] = df["category_mismatch"].astype("boolean")
    return df


def from_csv(clean_dir: Path) -> pd.DataFrame:
    clean_dir = Path(clean_dir)
    t = pd.read_csv(clean_dir / "tickets.csv")
    a = pd.read_csv(clean_dir / "agents.csv").rename(columns={
        "tier": "agent_tier", "primary_category": "agent_primary_category", "shift_region": "agent_region"})
    m = pd.read_csv(clean_dir / "merchants.csv").rename(columns={
        "sector": "merchant_sector", "tier": "merchant_tier", "region": "merchant_region"})
    a = a.drop(columns=["efficiency_multiplier"])
    df = (t.merge(a, left_on="assigned_agent_id", right_on="agent_id", how="left")
            .drop(columns=["agent_id"])
            .merge(m, on="merchant_id", how="left"))
    return normalize(df)
