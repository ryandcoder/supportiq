"""
Cleaning + validation shared by scripts/clean_data.py (command line) and POST /api/upload (browser).

clean() never changes data silently: every change is written to report["change_log"].
It raises DataValidationError (with readable messages) when the files cannot be used at all,
for example when a required column is missing.
"""
import numpy as np
import pandas as pd

VALID_PRIORITY = {"P1", "P2", "P3", "P4"}

REQUIRED = {
    "agents": ["agent_id", "agent_name", "tier", "primary_category", "shift_region", "efficiency_multiplier"],
    "merchants": ["merchant_id", "merchant_name", "sector", "tier", "region"],
    "tickets": ["ticket_id", "merchant_id", "category", "sub_category", "priority", "created_at", "is_legacy",
                "assigned_agent_id", "category_mismatch", "first_response_at", "closed_at", "ttfr_hours",
                "resolution_hours", "response_breached", "resolution_breached", "is_reopened",
                "is_reopen_child", "is_incident_ticket", "csat_score"],
}
TEXT_COLS = {
    "agents": ["agent_name", "tier", "primary_category", "shift_region"],
    "merchants": ["merchant_name", "sector", "tier", "region"],
    "tickets": ["category", "sub_category", "priority"],
}
NUMERIC_COLS = {
    "agents": ["agent_id", "efficiency_multiplier"],
    "merchants": ["merchant_id"],
    "tickets": ["ticket_id", "merchant_id", "assigned_agent_id", "ttfr_hours", "resolution_hours", "csat_score"],
}
KEY = {"agents": "agent_id", "merchants": "merchant_id", "tickets": "ticket_id"}
NOT_NULL = {
    "agents": ["agent_name", "tier", "primary_category", "shift_region", "efficiency_multiplier"],
    "merchants": ["merchant_name", "sector", "tier", "region"],
    "tickets": ["merchant_id", "category", "sub_category", "priority", "created_at"],
}
BOOL_COLS = ["is_legacy", "category_mismatch", "response_breached", "resolution_breached",
             "is_reopened", "is_reopen_child", "is_incident_ticket"]
DATE_COLS = ["created_at", "first_response_at", "closed_at"]
TRUE_WORDS, FALSE_WORDS = {"true", "t", "1", "yes", "y"}, {"false", "f", "0", "no", "n"}


class DataValidationError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def _bool_value(v):
    if v is None or (not isinstance(v, str) and pd.isna(v)):
        return pd.NA
    if isinstance(v, (bool, np.bool_)):
        return bool(v)
    s = str(v).strip().lower()
    return True if s in TRUE_WORDS else False if s in FALSE_WORDS else None  # None = unrecognised


def clean(agents: pd.DataFrame, merchants: pd.DataFrame, tickets: pd.DataFrame):
    frames = {"agents": agents.copy(), "merchants": merchants.copy(), "tickets": tickets.copy()}
    log: list[dict] = []
    stats = {"invalid": 0, "dropped": 0}

    def note(table, action, count, detail="", invalid=False, dropped=False):
        log.append({"table": table, "action": action, "rows_affected": int(count), "detail": detail})
        if invalid:
            stats["invalid"] += int(count)
        if dropped:
            stats["dropped"] += int(count)

    # ---------- required columns ----------
    errors = []
    for name, df in frames.items():
        df.columns = [str(c).strip() for c in df.columns]
        missing = [c for c in REQUIRED[name] if c not in df.columns]
        if missing:
            errors.append(f"{name}.csv is missing required column(s): {', '.join(missing)}")
        if df.empty:
            errors.append(f"{name}.csv has no rows")
    if errors:
        raise DataValidationError(errors)

    raw_counts = {k: len(v) for k, v in frames.items()}
    missing_before = {n: {c: int(v) for c, v in d.isna().sum().items() if v} for n, d in frames.items()}
    for name, df in frames.items():
        extra = [c for c in df.columns if c not in REQUIRED[name]]
        if extra:
            note(name, "ignored extra columns", 0, ", ".join(extra))
        frames[name] = df = df[REQUIRED[name]].copy()

    # ---------- text hygiene ----------
    for name, df in frames.items():
        for col in TEXT_COLS[name]:
            original = df[col].astype("string")
            stripped = original.str.strip()
            changed = int((stripped.notna() & (stripped != original)).sum())
            if changed:
                note(name, f"trimmed whitespace in {col}", changed)
            df[col] = stripped

    # ---------- numbers ----------
    for name, df in frames.items():
        for col in NUMERIC_COLS[name]:
            coerced = pd.to_numeric(df[col], errors="coerce")
            bad = int((coerced.isna() & df[col].notna()).sum())
            if bad:
                note(name, f"non-numeric {col} set to null", bad, invalid=True)
            df[col] = coerced
        key = KEY[name]
        no_key = df[key].isna()
        if no_key.any():
            note(name, f"dropped rows without a valid {key}", no_key.sum(), invalid=True, dropped=True)
            frames[name] = df = df[~no_key].copy()
        df[key] = df[key].astype("int64")

    agents, merchants, tickets = frames["agents"], frames["merchants"], frames["tickets"]

    # ---------- duplicates ----------
    for name in frames:
        df = frames[name]
        n = int(df.duplicated(subset=KEY[name]).sum())
        if n:
            frames[name] = df.drop_duplicates(subset=KEY[name], keep="first").copy()
            note(name, f"dropped duplicate {KEY[name]}", n, dropped=True)
    agents, merchants, tickets = frames["agents"], frames["merchants"], frames["tickets"]

    # ---------- dates ----------
    for col in DATE_COLS:
        parsed = pd.to_datetime(tickets[col], errors="coerce", format="mixed")  # each value parsed on its own
        bad = int((parsed.isna() & tickets[col].notna()).sum())
        if bad:
            note("tickets", f"unparseable {col} set to null", bad, invalid=True)
        tickets[col] = parsed
    bad_order = tickets["closed_at"].notna() & (tickets["closed_at"] < tickets["created_at"])
    if bad_order.any():
        tickets.loc[bad_order, ["closed_at", "resolution_hours"]] = np.nan
        tickets["closed_at"] = pd.to_datetime(tickets["closed_at"])
        note("tickets", "closed_at before created_at -> closed_at and resolution_hours nulled", bad_order.sum(), invalid=True)

    # ---------- values ----------
    bad_pri = ~tickets["priority"].isin(VALID_PRIORITY)
    if bad_pri.any():
        note("tickets", "dropped rows with invalid priority (expected P1-P4)", bad_pri.sum(), invalid=True, dropped=True)
        tickets = tickets[~bad_pri].copy()
    for col in ["ttfr_hours", "resolution_hours"]:
        neg = tickets[col] < 0
        if neg.any():
            tickets.loc[neg, col] = np.nan
            note("tickets", f"negative {col} set to null", neg.sum(), invalid=True)
    bad_csat = tickets["csat_score"].notna() & ~tickets["csat_score"].between(0, 1)
    if bad_csat.any():
        tickets.loc[bad_csat, "csat_score"] = np.nan
        note("tickets", "csat_score outside 0-1 set to null", bad_csat.sum(), invalid=True)

    for name, df in (("agents", agents), ("merchants", merchants), ("tickets", tickets)):
        missing_required = df[NOT_NULL[name]].isna().any(axis=1)
        if missing_required.any():
            note(name, f"dropped rows missing a required value ({', '.join(NOT_NULL[name])})", missing_required.sum(),
                 invalid=True, dropped=True)
            df = df[~missing_required].copy()
            if name == "agents": agents = df
            elif name == "merchants": merchants = df
            else: tickets = df
    tickets["merchant_id"] = tickets["merchant_id"].astype("int64")

    for col in BOOL_COLS:
        values = tickets[col].map(_bool_value)
        unknown = int(values.map(lambda v: v is None).sum())
        if unknown:
            note("tickets", f"unrecognised true/false values in {col} set to null", unknown, invalid=True)
        tickets[col] = values.map(lambda v: pd.NA if v is None else v).astype("boolean")

    # ---------- referential integrity ----------
    bad_m = ~tickets["merchant_id"].isin(merchants["merchant_id"])
    if bad_m.any():
        note("tickets", "dropped tickets whose merchant_id is not in merchants", bad_m.sum(), invalid=True, dropped=True)
        tickets = tickets[~bad_m].copy()
    bad_a = tickets["assigned_agent_id"].notna() & ~tickets["assigned_agent_id"].isin(agents["agent_id"])
    if bad_a.any():
        tickets.loc[bad_a, "assigned_agent_id"] = np.nan
        note("tickets", "unknown assigned_agent_id set to unassigned", bad_a.sum(), invalid=True)
    unassigned = int(tickets["assigned_agent_id"].isna().sum())
    note("tickets", "unassigned (no agent yet) - legitimate, kept", unassigned)
    tickets["assigned_agent_id"] = tickets["assigned_agent_id"].astype("Int64")

    if tickets.empty:
        raise DataValidationError(["tickets.csv has no usable rows after cleaning"])

    # ---------- derived columns (originals untouched) ----------
    tickets["status"] = tickets["closed_at"].notna().map({True: "Resolved", False: "Open"})
    note("tickets", "added derived column status (Resolved if closed_at exists, else Open)", len(tickets))
    tickets["created_month"] = tickets["created_at"].dt.to_period("M").astype(str)
    note("tickets", "added derived column created_month", len(tickets))

    open_n = int((tickets["status"] == "Open").sum())
    closed_no_csat = int(((tickets["status"] == "Resolved") & tickets["csat_score"].isna()).sum())
    note("tickets", "open tickets: nulls in closed_at/resolution_hours/ttfr are expected", open_n,
         "backlog of tickets created in the last days of the dataset")
    note("tickets", "resolved tickets without CSAT survey response (kept null, excluded from CSAT averages)", closed_no_csat)

    report = {
        "records_raw": raw_counts,
        "records_clean": {"agents": len(agents), "merchants": len(merchants), "tickets": len(tickets)},
        "missing_values_raw": missing_before,
        "duplicates_removed": sum(l["rows_affected"] for l in log if "duplicate" in l["action"]),
        "invalid_records_flagged": stats["invalid"],
        "dropped_records": stats["dropped"],
        "date_range": [str(tickets["created_at"].min()), str(tickets["created_at"].max())],
        "status_counts": tickets["status"].value_counts().to_dict(),
        "change_log": log,
    }
    return agents.reset_index(drop=True), merchants.reset_index(drop=True), tickets.reset_index(drop=True), report
