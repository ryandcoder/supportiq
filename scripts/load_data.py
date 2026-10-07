"""
SupportIQ - Phase 3: load cleaned CSVs into PostgreSQL.

Run (after `docker compose up -d db` and `python scripts/clean_data.py`):
    pip install -r backend/requirements.txt
    python scripts/load_data.py

Safe to re-run: tables are dropped and reloaded in one transaction.
"""
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.data_pipeline.loader import replace_all  # noqa: E402
from app.database.session import engine  # noqa: E402

CLEAN = ROOT / "data" / "clean"


def main():
    if not (CLEAN / "tickets.csv").exists():
        sys.exit("data/clean/ not found. Run: python scripts/clean_data.py")

    agents = pd.read_csv(CLEAN / "agents.csv")
    merchants = pd.read_csv(CLEAN / "merchants.csv")
    tickets = pd.read_csv(CLEAN / "tickets.csv")
    replace_all(engine, agents, merchants, tickets)

    with engine.connect() as conn:
        print("Loaded rows:")
        for t in ["agents", "merchants", "tickets"]:
            n = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            print(f"  {t:<10} {n:,}")
        print("Tickets by status:")
        for status, n in conn.execute(text("SELECT status, COUNT(*) FROM tickets GROUP BY status ORDER BY 2 DESC")):
            print(f"  {status:<10} {n:,}")


if __name__ == "__main__":
    main()
