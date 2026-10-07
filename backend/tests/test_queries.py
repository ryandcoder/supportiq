"""
Tests the SQL builders (app/database/queries.py) against an in-memory SQLite copy of the cleaned data.
No PostgreSQL needed. Run from backend/:  pytest -v
"""
import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.analytics import build_captions, build_dashboard, build_insights  # noqa: E402
from app.analytics.frame import from_csv  # noqa: E402
from app.database.queries import BASE_SELECT, FROM_JOINS, build_where, tickets_page_queries  # noqa: E402

CLEAN = Path(__file__).resolve().parents[2] / "data" / "clean"
pytestmark = pytest.mark.skipif(not (CLEAN / "tickets.csv").exists(), reason="run scripts/clean_data.py first")


@pytest.fixture(scope="module")
def con():
    c = sqlite3.connect(":memory:")
    for name in ["agents", "merchants", "tickets"]:
        pd.read_csv(CLEAN / f"{name}.csv").to_sql(name, c, index=False)
    return c


@pytest.fixture(scope="module")
def pdf():
    return from_csv(CLEAN)


def count(con, filters=None, search=None):
    where, params = build_where(filters, search)
    return con.execute(f"SELECT COUNT(*) {FROM_JOINS}{where}", params).fetchone()[0]


def page(con, **kw):
    args = dict(filters={}, search=None, sort_by="created_at", sort_dir="desc", page=1, page_size=25)
    args.update(kw)
    data_sql, count_sql, data_params, count_params, p, ps = tickets_page_queries(**args)
    cur = con.execute(data_sql, data_params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()], con.execute(count_sql, count_params).fetchone()[0]


def test_no_filters_counts_everything(con):
    assert count(con) == 2057


def test_list_filter_matches_pandas(con, pdf):
    f = {"category": ["Payments & Checkout", "Notifications"]}
    assert count(con, f) == pdf["category"].isin(f["category"]).sum()


def test_combined_filters_match_pandas(con, pdf):
    f = {"priority": ["P1", "P2"], "status": ["Resolved"], "merchant_sector": ["Fashion"]}
    expected = pdf[pdf.priority.isin(["P1", "P2"]) & (pdf.status == "Resolved") & (pdf.merchant_sector == "Fashion")]
    assert count(con, f) == len(expected)


def test_agent_filter(con, pdf):
    assert count(con, {"agent_id": [1, 2]}) == pdf["assigned_agent_id"].isin([1, 2]).sum()


def test_date_range_is_inclusive_of_end_day(con, pdf):
    f = {"date_from": "2025-03-01", "date_to": "2025-03-31"}
    expected = ((pdf.created_at >= "2025-03-01") & (pdf.created_at < "2025-04-01")).sum()
    assert count(con, f) == expected and expected > 0


def test_search_matches_and_escapes_wildcards(con, pdf):
    assert count(con, search="payments") == (pdf.category.str.lower().str.contains("payments")
                                              | pdf.sub_category.str.lower().str.contains("payments")
                                              | pdf.merchant_name.str.lower().str.contains("payments")
                                              | pdf.agent_name.fillna("").str.lower().str.contains("payments")
                                              | pdf.ticket_id.astype(str).str.contains("payments")).sum()
    assert count(con, search="%") == 0          # a literal %, not "match everything"
    assert count(con, search="_") == 0


def test_search_by_ticket_id(con):
    rows, total = page(con, search="848701")
    assert total >= 1 and any(r["ticket_id"] == 848701 for r in rows)


def test_pagination_has_no_overlap_and_correct_total(con):
    p1, total = page(con, page=1, page_size=50, sort_by="ticket_id", sort_dir="asc")
    p2, _ = page(con, page=2, page_size=50, sort_by="ticket_id", sort_dir="asc")
    assert total == 2057 and len(p1) == 50 and len(p2) == 50
    assert not {r["ticket_id"] for r in p1} & {r["ticket_id"] for r in p2}
    assert p1[-1]["ticket_id"] < p2[0]["ticket_id"]


def test_page_size_is_capped(con):
    rows, _ = page(con, page_size=5000)
    assert len(rows) == 100


def test_sorting_and_nulls_last(con):
    rows, _ = page(con, sort_by="resolution_hours", sort_dir="desc", page_size=100)
    vals = [r["resolution_hours"] for r in rows]
    assert vals == sorted(vals, reverse=True)
    rows, _ = page(con, sort_by="resolution_hours", sort_dir="asc", page=21, page_size=100)
    assert rows[-1]["resolution_hours"] is None       # open tickets (no resolution time) come last


def test_sla_status_values(con):
    rows, _ = page(con, page_size=100, sort_by="sla_status")
    assert {r["sla_status"] for r in rows} <= {"Open", "Breached", "Within SLA"}


def test_bad_sort_column_falls_back_safely(con):
    rows, total = page(con, sort_by="created_at; DROP TABLE tickets;--")
    assert total == 2057 and len(rows) == 25
    assert count(con) == 2057                         # table still there


def test_filter_values_are_bound_not_pasted(con):
    assert count(con, {"category": ["x' OR '1'='1"]}) == 0


def test_payloads_are_json_serialisable(pdf):
    json.dumps(build_dashboard(pdf))
    json.dumps(build_insights(pdf))
    json.dumps(build_captions(pdf))


def test_filtered_kpis_match_pandas_filtering(con, pdf):
    """End to end: SQL filter -> Pandas KPIs must equal Pandas filter -> Pandas KPIs."""
    from app.analytics import kpis
    from app.analytics.frame import normalize

    f = {"priority": ["P1", "P2"], "category": ["Payments & Checkout"], "date_from": "2025-06-01", "date_to": "2026-03-31"}
    where, params = build_where(f)
    via_sql = normalize(pd.read_sql(BASE_SELECT + FROM_JOINS + where, con, params=params))

    expected = pdf[pdf.priority.isin(f["priority"]) & pdf.category.isin(f["category"])
                   & (pdf.created_at >= "2025-06-01") & (pdf.created_at < "2026-04-01")]
    assert len(via_sql) == len(expected) > 0
    assert kpis(via_sql) == kpis(expected)


def test_filters_that_match_nothing_are_safe(con):
    from app.analytics import build_captions, build_dashboard, build_insights
    from app.analytics.frame import normalize

    where, params = build_where({"status": ["Open"], "date_to": "2025-12-31"})
    df = normalize(pd.read_sql(BASE_SELECT + FROM_JOINS + where, con, params=params))
    assert len(df) == 0
    assert build_dashboard(df)["kpis"]["total_tickets"] == 0
    assert build_insights(df) == {"insights": [], "recommendations": []}
    assert build_captions(df) == {}


def _frames_for_many_filters(con):
    """A spread of realistic filter selections, loaded through SQL like the API does."""
    from app.analytics.frame import normalize

    combos = [{}, {"status": ["Open"]}, {"status": ["Resolved"]}, {"priority": ["P1"]},
              {"date_from": "2026-06-01"}, {"date_from": "2025-01-01", "date_to": "2025-01-31"}]
    combos += [{"agent_id": [i]} for i in range(1, 21)]
    combos += [{"category": [c]} for c in ["Payments & Checkout", "Notifications", "Account Access"]]
    for f in combos:
        where, params = build_where(f)
        yield f, normalize(pd.read_sql(BASE_SELECT + FROM_JOINS + where, con, params=params))


def test_insights_are_clean_text_for_any_filter(con):
    from app.analytics import build_captions, build_insights

    for f, df in _frames_for_many_filters(con):
        out = build_insights(df)
        ids = [i["id"] for i in out["insights"]]
        assert len(ids) == len(set(ids)), f
        assert len(out["recommendations"]) <= 6, f
        texts = [i["text"] for i in out["insights"]] + [r["text"] for r in out["recommendations"]] \
            + list(build_captions(df).values())
        for t in texts:
            assert t.strip(), f
            assert "nan" not in t.lower().split() and "None" not in t and "inf" not in t.lower().split(), (f, t)
        basis_ok = {r["basis"] for r in out["recommendations"]} <= set(ids)
        assert basis_ok, f"recommendation without matching insight for {f}"


def test_insights_respond_to_filters(con):
    from app.analytics import build_insights
    from app.analytics.frame import normalize

    def top_text(f):
        where, params = build_where(f)
        df = normalize(pd.read_sql(BASE_SELECT + FROM_JOINS + where, con, params=params))
        return build_insights(df)["insights"][0]["text"]

    assert top_text({}) != top_text({"category": ["Notifications"]})
    assert "Notifications" in top_text({"category": ["Notifications"]})
