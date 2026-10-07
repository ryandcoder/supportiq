"""CSV export of the filtered ticket list."""
import numpy as np
import pandas as pd

EXPORT_COLUMNS = [
    "ticket_id", "created_at", "closed_at", "category", "sub_category", "priority", "status", "sla_status",
    "merchant_name", "merchant_sector", "merchant_region", "agent_name", "agent_tier",
    "ttfr_hours", "resolution_hours", "response_breached", "resolution_breached",
    "is_reopened", "csat_score", "category_mismatch",
]


def _spreadsheet_safe(value):
    """Text starting with = + - @ can run as a formula when the CSV is opened in Excel; prefix it with an apostrophe."""
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@"):
        return "'" + value
    return value


def tickets_to_csv(df: pd.DataFrame) -> str:
    out = df.sort_values(["created_at", "ticket_id"], ascending=[False, True]).copy()
    out["sla_status"] = np.select([out["status"] == "Open", out["resolution_breached"]], ["Open", "Breached"], "Within SLA")
    for col in ("created_at", "closed_at"):
        out[col] = out[col].dt.strftime("%Y-%m-%d %H:%M:%S")
    out = out[EXPORT_COLUMNS]
    for col in out.columns:
        if pd.api.types.is_object_dtype(out[col]) or pd.api.types.is_string_dtype(out[col]):
            out[col] = out[col].map(_spreadsheet_safe)
    return out.to_csv(index=False)
