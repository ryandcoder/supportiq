"""
Preview the analytics engine on data/clean/*.csv (no database needed).
    python scripts/preview_analytics.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.analytics import build_captions, build_dashboard, build_insights  # noqa: E402
from app.analytics.frame import from_csv  # noqa: E402

df = from_csv(ROOT / "data" / "clean")
d = build_dashboard(df)

print("=== KPIs ===")
print(json.dumps(d["kpis"], indent=2))
for key in ["by_category", "by_priority", "by_agent_tier", "by_merchant_sector", "routing", "csat_by_resolution_band"]:
    print(f"\n=== {key} ===")
    for r in d[key]:
        print({k: v for k, v in r.items() if k in ("name", "band", "tickets", "resolved", "responses", "share",
                                                    "median_resolution_hours", "sla_compliance", "avg_csat")})
print("\n=== Top 5 agents (by resolved) ===")
for a in d["agents"][:5]:
    print(a["agent_name"], a["tier"], a["tickets_resolved"], a["median_resolution_hours"], a["sla_compliance"], a["avg_csat"])

res = build_insights(df)
print("\n=== INSIGHTS ===")
for i in res["insights"]:
    print("-", i["text"])
print("\n=== RECOMMENDATIONS ===")
for r in res["recommendations"]:
    print("-", r["text"])
print("\n=== CAPTIONS ===")
for k, v in build_captions(df).items():
    print(f"{k}: {v}")
