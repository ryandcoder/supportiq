from datetime import date

from fastapi import HTTPException, Query


def _check_date(value: str | None, name: str) -> str | None:
    if value is None:
        return None
    try:
        date.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"{name} must be YYYY-MM-DD")
    return value


def get_filters(
    date_from: str | None = Query(None, description="YYYY-MM-DD, inclusive"),
    date_to: str | None = Query(None, description="YYYY-MM-DD, inclusive"),
    category: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    status: list[str] = Query(default=[]),
    agent_id: list[int] = Query(default=[]),
    merchant_sector: list[str] = Query(default=[]),
    merchant_region: list[str] = Query(default=[]),
    merchant_tier: list[str] = Query(default=[]),
) -> dict:
    """Shared by every endpoint, so KPIs, charts, insights and the table always use the same filters.
    Repeat a parameter for multiple values: ?category=Payments%20%26%20Checkout&category=Notifications"""
    df, dt = _check_date(date_from, "date_from"), _check_date(date_to, "date_to")
    if df and dt and df > dt:
        raise HTTPException(status_code=422, detail="date_from must be on or before date_to")
    return {
        "date_from": df, "date_to": dt, "category": category, "priority": priority, "status": status,
        "agent_id": agent_id, "merchant_sector": merchant_sector,
        "merchant_region": merchant_region, "merchant_tier": merchant_tier,
    }
