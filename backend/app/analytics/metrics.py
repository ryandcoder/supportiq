"""
Pandas analytics. Every function takes the (already filtered) frame from frame.py and returns plain
Python dicts/lists (JSON-safe). Nothing here knows about the database or the web framework.

Definitions
  Resolved ticket      status == 'Resolved' (has closed_at)
  SLA compliance       share of RESOLVED tickets with resolution_breached == False
  Response SLA         share of tickets that got a first response with response_breached == False
  Reopen rate          tickets flagged is_reopened / original tickets (is_reopen_child == False)
  CSAT                 csat_score on a 0-1 scale; tickets without a survey are excluded from averages
  Category mismatch    share of assigned tickets flagged category_mismatch
"""
import numpy as np
import pandas as pd

PRIORITY_ORDER = ["P1", "P2", "P3", "P4"]
CSAT_BINS = [0, 4, 12, 24, 48, np.inf]
CSAT_LABELS = ["0-4h", "4-12h", "12-24h", "24-48h", "48h+"]


# ---------- helpers ----------
def num(x, nd=2):
    """float rounded, or None for NaN/None (so JSON shows null instead of NaN)."""
    if x is None or pd.isna(x):
        return None
    return round(float(x), nd)


def resolved(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["status"] == "Resolved"]


def sla_compliance(res: pd.DataFrame):
    return None if res.empty else 1 - res["resolution_breached"].mean()


def reopen_rate(df: pd.DataFrame):
    originals = int((~df["is_reopen_child"]).sum())
    return None if originals == 0 else df["is_reopened"].sum() / originals


# ---------- KPI cards ----------
def kpis(df: pd.DataFrame) -> dict:
    total = len(df)
    res = resolved(df)
    responded = df[df["first_response_at"].notna()]
    csat = res["csat_score"].dropna()
    assigned = df[df["assigned_agent_id"].notna()]
    return {
        "total_tickets": total,
        "open_tickets": int((df["status"] == "Open").sum()),
        "resolved_tickets": len(res),
        "resolution_rate": num(len(res) / total, 4) if total else None,
        "sla_compliance": num(sla_compliance(res), 4),
        "response_sla_compliance": num(None if responded.empty else 1 - responded["response_breached"].mean(), 4),
        "avg_resolution_hours": num(res["resolution_hours"].mean()),
        "median_resolution_hours": num(res["resolution_hours"].median()),
        "avg_first_response_hours": num(responded["ttfr_hours"].mean()),
        "avg_csat": num(csat.mean(), 3),
        "csat_responses": int(csat.size),
        "csat_response_rate": num(csat.size / len(res), 4) if len(res) else None,
        "reopen_rate": num(reopen_rate(df), 4),
        "category_mismatch_rate": num(assigned["category_mismatch"].mean(), 4) if len(assigned) else None,
    }


# ---------- generic group summary (used by category, priority, sector, tier, ...) ----------
def group_summary(df: pd.DataFrame, by: str, order: list | None = None) -> list[dict]:
    if df.empty:
        return []
    total = len(df)
    rows = []
    for key, g in df.groupby(by, dropna=True):
        r = resolved(g)
        rows.append({
            "name": key if not isinstance(key, (np.integer, np.floating)) else key.item(),
            "tickets": len(g),
            "share": num(len(g) / total, 4),
            "open": int((g["status"] == "Open").sum()),
            "resolved": len(r),
            "avg_resolution_hours": num(r["resolution_hours"].mean()),
            "median_resolution_hours": num(r["resolution_hours"].median()),
            "sla_compliance": num(sla_compliance(r), 4),
            "avg_csat": num(g["csat_score"].mean(), 3),
            "csat_responses": int(g["csat_score"].notna().sum()),
            "reopen_rate": num(reopen_rate(g), 4),
        })
    if order:
        rows.sort(key=lambda x: order.index(x["name"]) if x["name"] in order else 99)
    else:
        rows.sort(key=lambda x: x["tickets"], reverse=True)
    return rows


# ---------- chart datasets ----------
def volume_by_month(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []
    months = pd.period_range(df["created_at"].min(), df["created_at"].max(), freq="M").astype(str)
    g = df.groupby("created_month")
    out = pd.DataFrame({"tickets": g.size(), "open": g["status"].apply(lambda s: (s == "Open").sum())})
    out = out.reindex(months, fill_value=0)
    return [{"month": m, "tickets": int(r.tickets), "open": int(r.open)} for m, r in out.iterrows()]


def by_status(df: pd.DataFrame) -> list[dict]:
    return [{"name": k, "tickets": int(v)} for k, v in df["status"].value_counts().items()]


def sla_breakdown(df: pd.DataFrame) -> dict:
    res = resolved(df)
    within = int((~res["resolution_breached"]).sum())
    return {"within_sla": within, "breached": len(res) - within, "resolved": len(res)}


def top_subcategories(df: pd.DataFrame, n: int = 10) -> list[dict]:
    rows = group_summary(df, "sub_category")[:n]
    cat = df.groupby("sub_category")["category"].first()
    for r in rows:
        r["category"] = cat.get(r["name"])
    return rows


def top_merchants(df: pd.DataFrame, n: int = 10) -> list[dict]:
    rows = group_summary(df, "merchant_name")[:n]
    for r in rows:
        r["sector"] = df.loc[df["merchant_name"] == r["name"], "merchant_sector"].iloc[0]
    return rows


def csat_by_resolution_band(df: pd.DataFrame) -> list[dict]:
    r = resolved(df)
    r = r[r["csat_score"].notna()].copy()
    if r.empty:
        return []
    r["band"] = pd.cut(r["resolution_hours"], CSAT_BINS, labels=CSAT_LABELS)
    g = r.groupby("band", observed=False)["csat_score"].agg(["count", "mean"])
    return [{"band": b, "responses": int(row["count"]), "avg_csat": num(row["mean"], 3)} for b, row in g.iterrows()]


def routing_comparison(df: pd.DataFrame) -> list[dict]:
    """Tickets handled inside vs outside the agent's primary category."""
    assigned = df[df["category_mismatch"].notna()]
    out = []
    for flag, label in [(False, "Matched"), (True, "Mismatched")]:
        g = assigned[assigned["category_mismatch"] == flag]
        if g.empty:
            continue
        r = resolved(g)
        out.append({"name": label, "tickets": len(g), "resolved": len(r),
                    "median_resolution_hours": num(r["resolution_hours"].median()),
                    "sla_compliance": num(sla_compliance(r), 4)})
    return out


def agent_performance(df: pd.DataFrame) -> list[dict]:
    assigned = df[df["assigned_agent_id"].notna()]
    rows = []
    for agent_id, g in assigned.groupby("assigned_agent_id"):
        r = resolved(g)
        rows.append({
            "agent_id": int(agent_id),
            "agent_name": g["agent_name"].iloc[0],
            "tier": g["agent_tier"].iloc[0],
            "primary_category": g["agent_primary_category"].iloc[0],
            "tickets_assigned": len(g),
            "tickets_resolved": len(r),
            "avg_resolution_hours": num(r["resolution_hours"].mean()),
            "median_resolution_hours": num(r["resolution_hours"].median()),
            "sla_compliance": num(sla_compliance(r), 4),
            "avg_csat": num(g["csat_score"].mean(), 3),
            "csat_responses": int(g["csat_score"].notna().sum()),
            "reopen_rate": num(reopen_rate(g), 4),
            "mismatch_rate": num(g["category_mismatch"].mean(), 4),
        })
    rows.sort(key=lambda x: x["tickets_resolved"], reverse=True)
    return rows


def build_dashboard(df: pd.DataFrame) -> dict:
    """Everything the dashboard page needs in one payload."""
    return {
        "kpis": kpis(df),
        "volume_by_month": volume_by_month(df),
        "by_category": group_summary(df, "category"),
        "by_priority": group_summary(df, "priority", order=PRIORITY_ORDER),
        "by_status": by_status(df),
        "sla": sla_breakdown(df),
        "by_merchant_sector": group_summary(df, "merchant_sector"),
        "by_merchant_region": group_summary(df, "merchant_region"),
        "by_merchant_tier": group_summary(df, "merchant_tier"),
        "by_agent_tier": group_summary(df, "agent_tier"),
        "top_subcategories": top_subcategories(df),
        "top_merchants": top_merchants(df),
        "csat_by_resolution_band": csat_by_resolution_band(df),
        "routing": routing_comparison(df),
        "agents": agent_performance(df),
    }
