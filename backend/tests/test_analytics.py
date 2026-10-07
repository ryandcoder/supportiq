"""Run from the backend/ folder:  pytest -v"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.analytics import build_captions, build_dashboard, build_insights, kpis  # noqa: E402
from app.analytics.frame import from_csv, normalize  # noqa: E402

CLEAN = Path(__file__).resolve().parents[2] / "data" / "clean"


def make_df(rows: list[dict]) -> pd.DataFrame:
    base = dict(
        ticket_id=0, merchant_id=101, category="A", sub_category="a1", priority="P3",
        created_at="2026-01-10 10:00:00", is_legacy=True, assigned_agent_id=1, category_mismatch=False,
        first_response_at="2026-01-10 11:00:00", closed_at="2026-01-10 12:00:00", ttfr_hours=1.0,
        resolution_hours=2.0, response_breached=False, resolution_breached=False, is_reopened=False,
        is_reopen_child=False, is_incident_ticket=False, csat_score=np.nan, status="Resolved",
        created_month="2026-01", agent_name="Ann", agent_tier="L1", agent_primary_category="A",
        agent_region="EU", merchant_name="M1", merchant_sector="Fashion", merchant_tier="Foundation",
        merchant_region="EU",
    )
    out = []
    for i, r in enumerate(rows, start=1):
        d = {**base, "ticket_id": i, **r}
        out.append(d)
    return normalize(pd.DataFrame(out))


@pytest.fixture
def small():
    # 6 tickets: 5 resolved, 1 open. SLA breached on 2 of the 5 resolved.
    return make_df([
        dict(category="A", priority="P1", resolution_hours=1.0, csat_score=0.9),
        dict(category="A", priority="P1", resolution_hours=3.0, resolution_breached=True),
        dict(category="B", priority="P2", resolution_hours=5.0, csat_score=0.5),
        dict(category="B", priority="P2", status="Open", closed_at=None, resolution_hours=np.nan,
             first_response_at=None, ttfr_hours=np.nan, assigned_agent_id=None, category_mismatch=None),
        dict(category="B", priority="P3", resolution_hours=10.0, resolution_breached=True, is_reopened=True),
        dict(category="A", priority="P3", resolution_hours=2.0, is_reopen_child=True),
    ])


def test_kpis(small):
    k = kpis(small)
    assert k["total_tickets"] == 6
    assert k["open_tickets"] == 1
    assert k["resolved_tickets"] == 5
    assert k["resolution_rate"] == pytest.approx(5 / 6, abs=1e-4)
    assert k["sla_compliance"] == pytest.approx(0.6)          # 3 of 5 resolved met SLA
    assert k["avg_resolution_hours"] == pytest.approx(4.2)    # (1+3+5+10+2)/5
    assert k["median_resolution_hours"] == pytest.approx(3.0)
    assert k["avg_csat"] == pytest.approx(0.7)                # only 2 responses count
    assert k["csat_responses"] == 2
    assert k["reopen_rate"] == pytest.approx(0.2)             # 1 reopened / 5 original tickets


def test_groups_sum_to_total(small):
    d = build_dashboard(small)
    assert sum(r["tickets"] for r in d["by_category"]) == 6
    assert sum(r["tickets"] for r in d["by_priority"]) == 6
    assert [r["name"] for r in d["by_priority"]] == ["P1", "P2", "P3"]
    assert d["sla"] == {"within_sla": 3, "breached": 2, "resolved": 5}


def test_agents_exclude_unassigned(small):
    agents = build_dashboard(small)["agents"]
    assert sum(a["tickets_assigned"] for a in agents) == 5   # the open ticket has no agent


def test_empty_frame_is_safe(small):
    empty = small.iloc[0:0]
    k = kpis(empty)
    assert k["total_tickets"] == 0 and k["sla_compliance"] is None
    assert build_dashboard(empty)["by_category"] == []
    assert build_insights(empty) == {"insights": [], "recommendations": []}
    assert build_captions(empty) == {}


def test_small_samples_are_not_compared(small):
    # every group has far fewer than MIN_N tickets, so no comparison insights should appear
    ids = {i["id"] for i in build_insights(small)["insights"]}
    assert "slowest_category" not in ids and "routing" not in ids


@pytest.mark.skipif(not (CLEAN / "tickets.csv").exists(), reason="run scripts/clean_data.py first")
def test_real_data_matches_cleaning_report():
    df = from_csv(CLEAN)
    k = kpis(df)
    assert k["total_tickets"] == 2057
    assert k["open_tickets"] == 250
    assert k["resolved_tickets"] == 1807
    d = build_dashboard(df)
    assert sum(r["tickets"] for r in d["by_category"]) == 2057
    assert sum(r["tickets"] for r in d["volume_by_month"]) == 2057
    ins = build_insights(df)
    assert len(ins["insights"]) > 0 and len(ins["recommendations"]) <= 6
