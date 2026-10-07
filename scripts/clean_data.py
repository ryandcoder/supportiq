"""
SupportIQ - Phase 1: data cleaning + data-quality report (command line).

Reads  : data/agents.csv, data/merchants.csv, data/tickets.csv   (raw, never modified)
Writes : data/clean/agents.csv, merchants.csv, tickets.csv
         data/clean/data_quality_report.json
Run    : python scripts/clean_data.py

The cleaning rules live in backend/app/data_pipeline/cleaning.py (shared with the upload page).
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.data_pipeline.cleaning import DataValidationError, clean  # noqa: E402

RAW, OUT = ROOT / "data", ROOT / "data" / "clean"
OUT.mkdir(parents=True, exist_ok=True)

try:
    agents, merchants, tickets, report = clean(
        pd.read_csv(RAW / "agents.csv"), pd.read_csv(RAW / "merchants.csv"), pd.read_csv(RAW / "tickets.csv"))
except DataValidationError as e:
    print("Cannot clean the data:")
    for msg in e.errors:
        print(" -", msg)
    sys.exit(1)

agents.to_csv(OUT / "agents.csv", index=False)
merchants.to_csv(OUT / "merchants.csv", index=False)
tickets.to_csv(OUT / "tickets.csv", index=False)
(OUT / "data_quality_report.json").write_text(json.dumps(report, indent=2, default=str))

print("=" * 60)
print("SUPPORTIQ - DATA QUALITY REPORT")
print("=" * 60)
for k, v in report["records_raw"].items():
    print(f"{k:<10} raw records : {v:,}")
print(f"Duplicates removed      : {report['duplicates_removed']}")
print(f"Invalid records flagged : {report['invalid_records_flagged']}")
print(f"Rows dropped            : {report['dropped_records']}")
print(f"Date range              : {report['date_range'][0][:10]} -> {report['date_range'][1][:10]}")
print(f"Status                  : {report['status_counts']}")
print("\nMissing values (raw, tickets):")
for c, n in report["missing_values_raw"]["tickets"].items():
    print(f"  {c:<20} {n:,}")
print("\nChange log:")
for l in report["change_log"]:
    print(f"  [{l['table']}] {l['action']}: {l['rows_affected']:,}")
print(f"\nClean files saved to {OUT.relative_to(ROOT)}/")
