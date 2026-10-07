"""
Container start-up step (run before the API starts):  python -m app.data_pipeline.bootstrap

  * database empty (first start)  -> clean the CSV files in DATA_DIR and load them
  * database already has data     -> leave it alone (your upload or earlier load is kept)
  * RELOAD_DATA=true              -> clean and reload from the CSV files even if data exists
  * report file missing           -> (re)create the data-quality report so the Data quality page works

The decision logic is in run() and takes plain functions, so it can be tested without a database.
"""
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd

from .cleaning import DataValidationError, clean

ROOT = Path(__file__).resolve().parents[3]          # /app inside the container
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "data"))
REPORT_PATH = Path(os.getenv("DATA_QUALITY_PATH", ROOT / "data" / "clean" / "data_quality_report.json"))
NAMES = ("agents", "merchants", "tickets")


def run(*, data_dir: Path, report_path: Path, force: bool, db_has_data, replace) -> str:
    """Returns 'loaded', 'report-only' or 'skipped'."""
    need_load = force or not db_has_data()
    need_report = not report_path.exists()
    if not need_load and not need_report:
        print("bootstrap: database already holds data, nothing to do")
        return "skipped"

    files = {n: Path(data_dir) / f"{n}.csv" for n in NAMES}
    missing = [f.name for f in files.values() if not f.exists()]
    if missing:
        if not need_load:  # data is in the database already; only the report could not be rebuilt
            print(f"bootstrap: {', '.join(missing)} not found in {data_dir}; data quality report not rebuilt")
            return "skipped"
        raise FileNotFoundError(f"Missing {', '.join(missing)} in {data_dir}. Put agents.csv, merchants.csv and tickets.csv in the ./data folder.")

    try:
        agents, merchants, tickets, report = clean(*(pd.read_csv(files[n]) for n in NAMES))
    except DataValidationError as e:
        raise SystemExit("bootstrap: cannot use the CSV files:\n - " + "\n - ".join(e.errors))

    if need_load:
        replace(agents, merchants, tickets)
        print(f"bootstrap: loaded {len(agents)} agents, {len(merchants)} merchants, {len(tickets)} tickets")
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, default=str))
    except OSError as e:
        print(f"bootstrap: could not write the data quality report ({e})")
    return "loaded" if need_load else "report-only"


def main():
    from sqlalchemy import text

    from app.database.session import engine

    from .loader import replace_all

    for attempt in range(1, 31):  # the database container may still be starting
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            break
        except Exception:
            print(f"bootstrap: waiting for the database ({attempt}/30)")
            time.sleep(2)
    else:
        sys.exit("bootstrap: database not reachable")

    def db_has_data() -> bool:
        try:
            with engine.connect() as conn:
                return (conn.execute(text("SELECT COUNT(*) FROM tickets")).scalar() or 0) > 0
        except Exception:  # table does not exist yet
            return False

    try:
        run(data_dir=DATA_DIR, report_path=REPORT_PATH,
            force=os.getenv("RELOAD_DATA", "").strip().lower() in ("1", "true", "yes"),
            db_has_data=db_has_data, replace=lambda a, m, t: replace_all(engine, a, m, t))
    except FileNotFoundError as e:
        sys.exit(f"bootstrap: {e}")


if __name__ == "__main__":
    main()
