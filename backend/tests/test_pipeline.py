"""Cleaning/validation (shared by the script and the upload page) and CSV export. Pandas only, no database."""
import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.analytics.export import EXPORT_COLUMNS, tickets_to_csv  # noqa: E402
from app.analytics.frame import from_csv  # noqa: E402
from app.data_pipeline.cleaning import DataValidationError, clean  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RAW, CLEAN = ROOT / "data", ROOT / "data" / "clean"
pytestmark = pytest.mark.skipif(not (RAW / "tickets.csv").exists(), reason="CSV files not in data/")


@pytest.fixture
def raw():
    return pd.read_csv(RAW / "agents.csv"), pd.read_csv(RAW / "merchants.csv"), pd.read_csv(RAW / "tickets.csv")


def actions(report):
    return {l["action"]: l["rows_affected"] for l in report["change_log"]}


def test_clean_real_data_has_nothing_to_fix(raw):
    a, m, t, report = clean(*raw)
    assert (len(a), len(m), len(t)) == (20, 112, 2057)
    assert report["duplicates_removed"] == 0 and report["invalid_records_flagged"] == 0 and report["dropped_records"] == 0
    assert report["status_counts"] == {"Resolved": 1807, "Open": 250}


def test_missing_columns_are_reported_by_name(raw):
    a, m, t = raw
    with pytest.raises(DataValidationError) as e:
        clean(a, m.drop(columns=["sector"]), t.drop(columns=["priority", "csat_score"]))
    text = " ".join(e.value.errors)
    assert "merchants.csv" in text and "sector" in text
    assert "tickets.csv" in text and "priority" in text and "csat_score" in text


def test_empty_file_is_rejected(raw):
    a, m, t = raw
    with pytest.raises(DataValidationError):
        clean(a, m, t.iloc[0:0])


def test_messy_tickets_are_fixed_and_documented(raw):
    a, m, t = raw
    t = t.head(60).copy()
    t["category"] = t["category"].astype(object)
    t.loc[t.index[0], "category"] = "  " + t.loc[t.index[0], "category"] + "  "      # whitespace
    t = pd.concat([t, t.iloc[[1]]])                                                  # duplicate ticket_id
    t.loc[t.index[2], "priority"] = "P9"                                              # invalid priority
    t.loc[t.index[3], "merchant_id"] = 999999                                         # unknown merchant
    t.loc[t.index[4], "assigned_agent_id"] = 777                                      # unknown agent
    t["csat_score"] = t["csat_score"].astype(float)
    t.loc[t.index[5], "csat_score"] = 1.7                                             # out of range
    t["is_legacy"] = ["TRUE" if i % 2 else "false" for i in range(len(t))]            # text booleans
    t["unexpected_extra"] = 1                                                         # extra column
    t["closed_at"] = t["closed_at"].astype(object)
    t.loc[t.index[6], "created_at"] = "2030-01-01 00:00:00"                           # closed before created
    t.loc[t.index[6], "closed_at"] = "2029-01-01 00:00:00"

    _, _, out, report = clean(a, m, t)
    log = actions(report)

    assert log["dropped duplicate ticket_id"] == 1
    assert log["dropped rows with invalid priority (expected P1-P4)"] == 1
    assert log["dropped tickets whose merchant_id is not in merchants"] == 1
    assert log["unknown assigned_agent_id set to unassigned"] == 1
    assert log["csat_score outside 0-1 set to null"] == 1
    assert log["closed_at before created_at -> closed_at and resolution_hours nulled"] == 1
    assert log["trimmed whitespace in category"] == 1
    assert "ignored extra columns" in log
    assert report["dropped_records"] == 3                       # duplicate, bad priority, unknown merchant
    assert len(out) == 60 - 2                                   # 60 originals, 2 of them dropped (dup is an extra row)
    assert "unexpected_extra" not in out.columns
    assert out["is_legacy"].dtype == "boolean" and out["is_legacy"].notna().all()
    assert out["priority"].isin({"P1", "P2", "P3", "P4"}).all()
    assert out["csat_score"].dropna().between(0, 1).all()
    assert (out["category"] == out["category"].str.strip()).all()


def test_export_matches_filtered_frame_and_is_spreadsheet_safe():
    df = from_csv(CLEAN)
    sub = df[df["priority"] == "P1"].copy()
    sub.loc[sub.index[0], "merchant_name"] = "=HYPERLINK(\"http://x\")"
    csv = tickets_to_csv(sub)
    back = pd.read_csv(io.StringIO(csv))
    assert list(back.columns) == EXPORT_COLUMNS
    assert len(back) == len(sub)
    assert set(back["sla_status"]) <= {"Open", "Breached", "Within SLA"}
    assert "nan" not in csv.lower().split(",")                   # blanks stay blank
    assert not any(str(v).startswith("=") for v in back["merchant_name"])
