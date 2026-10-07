import io
import json
import os
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy import text

from app.analytics import build_captions, build_dashboard, build_insights
from app.analytics import repository
from app.analytics.export import tickets_to_csv
from app.analytics.metrics import agent_performance
from app.data_pipeline.cleaning import DataValidationError, clean
from app.data_pipeline.loader import replace_all
from app.database.session import engine

from .deps import get_filters

router = APIRouter(prefix="/api")

# copy of the report shipped with the code, used on hosts where the runtime file does not exist
BUNDLED_REPORT = Path(__file__).resolve().parents[1] / "data_pipeline" / "data_quality_report.json"
QUALITY_REPORT = Path(os.getenv(
    "DATA_QUALITY_PATH", Path(__file__).resolve().parents[3] / "data" / "clean" / "data_quality_report.json"))


@router.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}


@router.get("/filters")
def filter_options():
    """Values for the filter dropdowns."""
    return repository.get_filter_options()


@router.get("/dashboard")
def dashboard(filters: dict = Depends(get_filters)):
    """KPI cards + every chart dataset + one caption sentence per chart."""
    df = repository.load_tickets(filters)
    payload = build_dashboard(df)
    payload["captions"] = build_captions(df)
    payload["filters_applied"] = {k: v for k, v in filters.items() if v}
    return payload


@router.get("/insights")
def insights(filters: dict = Depends(get_filters)):
    """Key Insights + Recommendations, generated from the filtered data."""
    return build_insights(repository.load_tickets(filters))


@router.get("/agents")
def agents(filters: dict = Depends(get_filters)):
    """Agent performance table."""
    return agent_performance(repository.load_tickets(filters))


@router.get("/tickets")
def tickets(
    filters: dict = Depends(get_filters),
    search: str | None = Query(None, max_length=100, description="ticket id, category, sub-category, merchant or agent"),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
):
    """One page of tickets (server-side search, sorting and pagination)."""
    return repository.list_tickets(filters, search, sort_by, sort_dir, page, page_size)


@router.get("/data-quality")
def data_quality():
    """Report written by scripts/clean_data.py."""
    for path in (QUALITY_REPORT, BUNDLED_REPORT):
        if path.exists():
            return json.loads(path.read_text())
    raise HTTPException(status_code=404, detail="Run scripts/clean_data.py first")


# ---------------- export ----------------
@router.get("/export/tickets.csv")
def export_tickets(filters: dict = Depends(get_filters)):
    """The tickets matching the current filters, as a CSV download."""
    csv = tickets_to_csv(repository.load_tickets(filters))
    return Response(content=csv, media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="supportiq_tickets.csv"'})


# ---------------- upload ----------------
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))


def _upload_enabled() -> bool:
    # Off unless you switch it on: with no login, anyone who can reach a public API could replace the data.
    return os.getenv("ALLOW_UPLOAD", "false").strip().lower() in ("1", "true", "yes")


@router.get("/upload/status")
def upload_status():
    return {"enabled": _upload_enabled(), "max_mb": MAX_UPLOAD_MB}


def _read_csv(upload: UploadFile, name: str) -> pd.DataFrame:
    limit = MAX_UPLOAD_MB * 1024 * 1024
    raw = upload.file.read(limit + 1)
    if len(raw) > limit:
        raise HTTPException(413, detail={"errors": [f"{name}.csv is larger than {MAX_UPLOAD_MB} MB"]})
    try:
        return pd.read_csv(io.BytesIO(raw))
    except Exception as e:  # empty file, binary file, broken quoting ...
        raise HTTPException(422, detail={"errors": [f"{name}.csv could not be read as a CSV file ({type(e).__name__})"]})


@router.post("/upload")
def upload(
    agents: UploadFile = File(...),
    merchants: UploadFile = File(...),
    tickets: UploadFile = File(...),
    dry_run: bool = Query(True, description="true = validate and report only; false = replace the database data"),
):
    """Runs the same cleaning as scripts/clean_data.py on the three uploaded files.
    dry_run=true changes nothing. dry_run=false replaces all data in one transaction."""
    if not _upload_enabled():
        raise HTTPException(403, detail={"errors": ["Uploads are disabled. Set ALLOW_UPLOAD=true in .env and restart the API."]})

    frames = {n: _read_csv(f, n) for n, f in (("agents", agents), ("merchants", merchants), ("tickets", tickets))}
    try:
        a, m, t, report = clean(frames["agents"], frames["merchants"], frames["tickets"])
    except DataValidationError as e:
        raise HTTPException(422, detail={"errors": e.errors})

    if dry_run:
        return {"committed": False, "report": report}

    try:
        loaded = replace_all(engine, a, m, t)
    except Exception as e:
        raise HTTPException(500, detail={"errors": [f"Database load failed, existing data was not changed ({type(e).__name__})"]})
    try:  # keep the Data quality page in sync (best effort: the folder may be read-only)
        QUALITY_REPORT.parent.mkdir(parents=True, exist_ok=True)
        QUALITY_REPORT.write_text(json.dumps(report, indent=2, default=str))
    except OSError:
        pass
    return {"committed": True, "report": report, "loaded": loaded}
