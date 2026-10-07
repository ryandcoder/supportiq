"""
API integration tests. They call the real FastAPI app against the real PostgreSQL database.

Needs: `docker compose up -d db`, `python scripts/load_data.py` (database loaded from data/clean).
If the database is not reachable these tests are SKIPPED, so `pytest` still passes without Docker.
"""
import csv
import io
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.analytics import kpis  # noqa: E402
from app.analytics.frame import from_csv  # noqa: E402
from app.database.session import engine  # noqa: E402
from app.main import app  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CLEAN, RAW = ROOT / "data" / "clean", ROOT / "data"


def _db_rows():
    try:
        with engine.connect() as conn:
            return conn.execute(text("SELECT COUNT(*) FROM tickets")).scalar()
    except Exception:
        return None


EXPECTED = from_csv(CLEAN) if (CLEAN / "tickets.csv").exists() else None
pytestmark = pytest.mark.skipif(
    EXPECTED is None or _db_rows() != len(EXPECTED),
    reason="database not running, or it does not contain data/clean (run scripts/load_data.py)",
)

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_dashboard_kpis_equal_pandas_on_the_csv():
    """Whole chain: PostgreSQL -> SQL join -> Pandas -> JSON equals Pandas computed straight from the CSV."""
    r = client.get("/api/dashboard")
    assert r.status_code == 200
    assert r.json()["kpis"] == kpis(EXPECTED)


def test_filter_changes_dashboard_and_matches_pandas():
    r = client.get("/api/dashboard", params={"category": "Notifications"})
    assert r.status_code == 200
    assert r.json()["kpis"]["total_tickets"] == int((EXPECTED["category"] == "Notifications").sum())


def test_repeated_parameters_combine_as_or():
    r = client.get("/api/dashboard", params=[("priority", "P1"), ("priority", "P2")])
    assert r.json()["kpis"]["total_tickets"] == int(EXPECTED["priority"].isin(["P1", "P2"]).sum())


def test_tickets_pagination_and_totals():
    first = client.get("/api/tickets", params={"page": 1, "page_size": 10, "sort_by": "ticket_id", "sort_dir": "asc"}).json()
    second = client.get("/api/tickets", params={"page": 2, "page_size": 10, "sort_by": "ticket_id", "sort_dir": "asc"}).json()
    assert first["total"] == len(EXPECTED) and len(first["items"]) == 10
    assert not {t["ticket_id"] for t in first["items"]} & {t["ticket_id"] for t in second["items"]}


def test_ticket_search():
    data = client.get("/api/tickets", params={"search": "payments", "page_size": 100}).json()
    assert 0 < data["total"] < len(EXPECTED)


@pytest.mark.parametrize("params", [
    {"date_from": "not-a-date"},
    {"date_from": "2026-06-30", "date_to": "2025-01-01"},
    {"sort_dir": "sideways"},
    {"page": 0},
    {"page_size": 5000},
])
def test_bad_input_is_rejected_with_422(params):
    assert client.get("/api/tickets", params=params).status_code == 422


def test_insights_shape():
    body = client.get("/api/insights").json()
    assert body["insights"] and len(body["recommendations"]) <= 6
    assert all(i["text"] for i in body["insights"])


def test_csv_export_row_count_matches_filtered_total():
    params = {"priority": "P1"}
    total = client.get("/api/tickets", params=params).json()["total"]
    r = client.get("/api/export/tickets.csv", params=params)
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    assert "attachment" in r.headers["content-disposition"]
    rows = list(csv.reader(io.StringIO(r.text)))
    assert len(rows) - 1 == total


def _files(drop_column=None):
    import pandas as pd
    out = {}
    for name in ("agents", "merchants", "tickets"):
        df = pd.read_csv(RAW / f"{name}.csv")
        if name == "tickets" and drop_column:
            df = df.drop(columns=[drop_column])
        out[name] = (f"{name}.csv", df.to_csv(index=False).encode(), "text/csv")
    return out


def test_upload_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ALLOW_UPLOAD", raising=False)
    assert client.post("/api/upload", files=_files()).status_code == 403
    assert client.get("/api/upload/status").json()["enabled"] is False


def test_upload_check_refuses_missing_column_and_changes_nothing(monkeypatch):
    monkeypatch.setenv("ALLOW_UPLOAD", "true")
    r = client.post("/api/upload", files=_files(drop_column="priority"))
    assert r.status_code == 422
    assert any("priority" in e for e in r.json()["detail"]["errors"])
    assert _db_rows() == len(EXPECTED)


def test_upload_dry_run_accepts_real_data_without_committing(monkeypatch):
    monkeypatch.setenv("ALLOW_UPLOAD", "true")
    r = client.post("/api/upload", files=_files())          # dry_run defaults to true
    body = r.json()
    assert r.status_code == 200 and body["committed"] is False
    assert body["report"]["records_clean"]["tickets"] == len(EXPECTED)
    assert _db_rows() == len(EXPECTED)
