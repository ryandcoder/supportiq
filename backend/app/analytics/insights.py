"""
Dynamic insights, chart captions and recommendations.

Every sentence is generated from calculated numbers (nothing hardcoded). A comparison is only
reported when each group has enough tickets (MIN_N) so small samples are not over-interpreted.
Recommendations only point at what the data shows; they make no cost or savings claims.
"""
import pandas as pd

from .metrics import (PRIORITY_ORDER, csat_by_resolution_band, group_summary,
                      kpis, reopen_rate, resolved, routing_comparison, volume_by_month)

MIN_N = 30          # minimum resolved tickets in a group before comparing it
MIN_BAND_N = 10     # minimum CSAT responses in a resolution band
SLA_GAP = 0.05      # difference (5 points) before calling two SLA rates different


def pct(x) -> str:
    return f"{x * 100:.0f}%"


def hrs(x) -> str:
    return f"{x:.1f}h"


def _frame(rows: list[dict], min_resolved: int = 0) -> pd.DataFrame:
    d = pd.DataFrame(rows)
    return d[d["resolved"] >= min_resolved] if not d.empty and min_resolved else d


def _trend(df: pd.DataFrame):
    """Latest month vs average of the previous 3 months."""
    months = volume_by_month(df)
    if len(months) < 4:
        return None
    latest, prev = months[-1], months[-4:-1]
    base = sum(m["tickets"] for m in prev) / 3
    if base == 0:
        return None
    return {"month": latest["month"], "tickets": latest["tickets"], "open": latest["open"],
            "baseline": base, "ratio": latest["tickets"] / base}


def build_insights(df: pd.DataFrame) -> dict:
    out = {"insights": [], "recommendations": []}
    if df.empty:
        return out
    ins, rec = out["insights"], out["recommendations"]
    k = kpis(df)
    res = resolved(df)

    cat_all = _frame(group_summary(df, "category"))
    cat = _frame(group_summary(df, "category"), MIN_N)
    pri = _frame(group_summary(df, "priority", PRIORITY_ORDER), MIN_N)
    tier = _frame(group_summary(df, "agent_tier"), MIN_N)
    routing = {r["name"]: r for r in routing_comparison(df)}
    trend = _trend(df)

    # 1. Volume: largest category
    top = cat_all.iloc[0]
    ins.append({"id": "top_category", "type": "volume",
                "text": f"{top['name']} is the largest category with {int(top['tickets']):,} tickets "
                        f"({pct(top['share'])} of all tickets in view).",
                "evidence": {"category": top["name"], "tickets": int(top["tickets"]), "share": top["share"]}})

    # 2. Speed: slowest vs fastest category (median)
    if len(cat) >= 2:
        slow = cat.loc[cat["median_resolution_hours"].idxmax()]
        fast = cat.loc[cat["median_resolution_hours"].idxmin()]
        ratio = slow["median_resolution_hours"] / fast["median_resolution_hours"]
        ins.append({"id": "slowest_category", "type": "speed",
                    "text": f"{slow['name']} takes the longest to resolve (median {hrs(slow['median_resolution_hours'])}), "
                            f"{ratio:.1f}x the fastest category, {fast['name']} ({hrs(fast['median_resolution_hours'])}).",
                    "evidence": {"slowest": slow["name"], "fastest": fast["name"], "ratio": round(ratio, 2)}})

        # 3. SLA by category
        worst = cat.loc[cat["sla_compliance"].idxmin()]
        best = cat.loc[cat["sla_compliance"].idxmax()]
        ins.append({"id": "sla_by_category", "type": "sla",
                    "text": f"{worst['name']} has the lowest SLA compliance ({pct(worst['sla_compliance'])}), "
                            f"compared with {pct(best['sla_compliance'])} for {best['name']}.",
                    "evidence": {"worst": worst["name"], "best": best["name"]}})

    # 4. SLA by priority (highest vs lowest priority present)
    if len(pri) >= 2:
        hi, lo = pri.iloc[0], pri.iloc[-1]
        gap = hi["sla_compliance"] - lo["sla_compliance"]
        if gap < -SLA_GAP:
            text = (f"Higher-priority tickets miss SLA more often: {hi['name']} compliance is "
                    f"{pct(hi['sla_compliance'])} versus {pct(lo['sla_compliance'])} for {lo['name']}.")
        elif gap > SLA_GAP:
            text = (f"Higher-priority tickets meet SLA more reliably: {hi['name']} compliance is "
                    f"{pct(hi['sla_compliance'])} versus {pct(lo['sla_compliance'])} for {lo['name']}.")
        else:
            text = (f"SLA compliance is similar across priorities ({hi['name']}: {pct(hi['sla_compliance'])}, "
                    f"{lo['name']}: {pct(lo['sla_compliance'])}).")
        ins.append({"id": "sla_by_priority", "type": "sla", "text": text,
                    "evidence": {"highest": hi["name"], "lowest": lo["name"], "gap": round(float(gap), 4)}})

    # 5. Overall SLA + response SLA gap
    if k["sla_compliance"] is not None:
        text = f"Overall, {pct(k['sla_compliance'])} of resolved tickets met their resolution SLA."
        if k["response_sla_compliance"] is not None and k["response_sla_compliance"] - k["sla_compliance"] > 0.10:
            text += (f" First responses are on time {pct(k['response_sla_compliance'])} of the time, "
                     f"so the delay is mostly in resolution, not in responding.")
        ins.append({"id": "overall_sla", "type": "sla", "text": text, "evidence": {}})

    # 6. Trend: latest month vs previous 3-month average
    if trend:
        r = trend["ratio"]
        word = "above" if r >= 1.25 else "below" if r <= 0.8 else "in line with"
        text = (f"{trend['month']} had {trend['tickets']:,} tickets, {word} the previous three-month "
                f"average of {trend['baseline']:.0f} ({r:.1f}x).")
        if trend["open"] and trend["tickets"]:
            text += f" {trend['open']:,} of them ({pct(trend['open'] / trend['tickets'])}) are still open."
        ins.append({"id": "volume_trend", "type": "trend", "text": text,
                    "evidence": {"month": trend["month"], "ratio": round(r, 2), "open": trend["open"]}})

    # 7. Agent tier
    if len(tier) >= 2:
        lo_t = tier.loc[tier["sla_compliance"].idxmin()]
        hi_t = tier.loc[tier["sla_compliance"].idxmax()]
        if hi_t["sla_compliance"] - lo_t["sla_compliance"] > SLA_GAP:
            ins.append({"id": "tier_sla", "type": "sla",
                        "text": f"{lo_t['name']} agents meet SLA on {pct(lo_t['sla_compliance'])} of resolved tickets "
                                f"versus {pct(hi_t['sla_compliance'])} for {hi_t['name']}.",
                        "evidence": {"lowest": lo_t["name"], "highest": hi_t["name"]}})

    # 8. Routing (category mismatch)
    if "Matched" in routing and "Mismatched" in routing:
        m, mm = routing["Matched"], routing["Mismatched"]
        if m["resolved"] >= MIN_N and mm["resolved"] >= MIN_N and k["category_mismatch_rate"] is not None:
            ins.append({"id": "routing", "type": "routing",
                        "text": f"{pct(k['category_mismatch_rate'])} of assigned tickets were handled outside the agent's "
                                f"primary category. They meet SLA on {pct(mm['sla_compliance'])} of resolved tickets "
                                f"versus {pct(m['sla_compliance'])} for matched tickets "
                                f"(median {hrs(mm['median_resolution_hours'])} vs {hrs(m['median_resolution_hours'])}).",
                        "evidence": {"mismatch_rate": k["category_mismatch_rate"]}})

    # 9. CSAT vs resolution time
    r_csat = res[res["csat_score"].notna()]
    if len(r_csat) >= 30:
        rho = r_csat["resolution_hours"].rank().corr(r_csat["csat_score"].rank())
        bands = [b for b in csat_by_resolution_band(df) if b["responses"] >= MIN_BAND_N]
        direction = ("tends to fall as resolution time rises" if rho <= -0.2
                     else "tends to rise as resolution time rises" if rho >= 0.2
                     else "shows no clear relationship with resolution time")
        text = f"Customer satisfaction {direction} (rank correlation {rho:.2f}, {len(r_csat):,} responses)."
        if len(bands) >= 2:
            best = max(bands, key=lambda b: b["avg_csat"])
            worst = min(bands, key=lambda b: b["avg_csat"])
            text += (f" The highest CSAT is in the {best['band']} band ({best['avg_csat']:.2f}) and the lowest "
                     f"in the {worst['band']} band ({worst['avg_csat']:.2f}).")
        ins.append({"id": "csat_vs_resolution", "type": "csat", "text": text, "evidence": {"rho": round(float(rho), 3)}})

    # 10. CSAT coverage (data caveat)
    if k["csat_response_rate"] is not None and k["csat_response_rate"] < 0.5:
        ins.append({"id": "csat_coverage", "type": "data",
                    "text": f"Only {pct(k['csat_response_rate'])} of resolved tickets have a CSAT score "
                            f"({k['csat_responses']:,} of {k['resolved_tickets']:,}), so satisfaction figures rest on a small sample.",
                    "evidence": {"responses": k["csat_responses"], "rate": k["csat_response_rate"]}})

    # 11. Reopens
    if k["reopen_rate"]:
        c = cat[cat["reopen_rate"].notna()] if not cat.empty else cat
        text = f"{pct(k['reopen_rate'])} of original tickets were reopened."
        if not c.empty:
            hi_r = c.loc[c["reopen_rate"].idxmax()]
            text += f" {hi_r['name']} has the highest reopen rate ({pct(hi_r['reopen_rate'])})."
        ins.append({"id": "reopens", "type": "quality", "text": text, "evidence": {"reopen_rate": k["reopen_rate"]}})

    # ---------------- recommendations ----------------
    if len(cat) >= 2:
        worst = cat.loc[cat["sla_compliance"].idxmin()]
        if worst["sla_compliance"] < 0.8:
            rec.append({"text": f"Review the SLA target and staffing for {worst['name']}: only "
                                f"{pct(worst['sla_compliance'])} of its {int(worst['resolved']):,} resolved tickets met SLA.",
                        "basis": "sla_by_category"})
        slow = cat.loc[cat["median_resolution_hours"].idxmax()]
        sub = res[res["category"] == slow["name"]].groupby("sub_category")["resolution_hours"].agg(["count", "median"])
        sub = sub[sub["count"] >= 15]
        if not sub.empty:
            s = sub["median"].idxmax()
            rec.append({"text": f"Review troubleshooting steps for {s} in {slow['name']}: median resolution is "
                                f"{hrs(sub.loc[s, 'median'])}, the longest sub-category in the slowest category.",
                        "basis": "slowest_category"})

    if "Matched" in routing and "Mismatched" in routing:
        m, mm = routing["Matched"], routing["Mismatched"]
        if (mm["resolved"] >= MIN_N and m["resolved"] >= MIN_N
                and m["sla_compliance"] - mm["sla_compliance"] > SLA_GAP):
            rec.append({"text": f"Review ticket routing rules: tickets handled outside an agent's primary category meet SLA "
                                f"less often ({pct(mm['sla_compliance'])} vs {pct(m['sla_compliance'])}).",
                        "basis": "routing"})

    if len(tier) >= 2:
        lo_t = tier.loc[tier["sla_compliance"].idxmin()]
        hi_t = tier.loc[tier["sla_compliance"].idxmax()]
        if hi_t["sla_compliance"] - lo_t["sla_compliance"] > 0.10:
            rec.append({"text": f"Check escalation and coaching for {lo_t['name']} agents: they meet SLA on "
                                f"{pct(lo_t['sla_compliance'])} of resolved tickets versus {pct(hi_t['sla_compliance'])} for {hi_t['name']}.",
                        "basis": "tier_sla"})

    if len(pri) >= 2 and pri.iloc[0]["sla_compliance"] - pri.iloc[-1]["sla_compliance"] < -SLA_GAP:
        hi, lo = pri.iloc[0], pri.iloc[-1]
        rec.append({"text": f"Compare {hi['name']} SLA targets with available capacity: {hi['name']} tickets meet SLA "
                            f"{pct(hi['sla_compliance'])} of the time, below {lo['name']} ({pct(lo['sla_compliance'])}).",
                    "basis": "sla_by_priority"})

    if trend and trend["ratio"] >= 1.25 and trend["open"] > 0:
        rec.append({"text": f"Work through the {trend['open']:,} tickets from {trend['month']} that are still open; "
                            f"volume that month was {trend['ratio']:.1f}x the recent average.",
                    "basis": "volume_trend"})

    if k["csat_response_rate"] is not None and k["csat_response_rate"] < 0.25:
        rec.append({"text": f"Increase the CSAT survey response rate (currently {pct(k['csat_response_rate'])}) "
                            f"before relying on satisfaction as a performance measure.",
                    "basis": "csat_coverage"})

    del rec[6:]
    return out


def build_captions(df: pd.DataFrame) -> dict:
    """One sentence per chart (shown above each chart in the Editorial Analytics theme)."""
    caps = {}
    if df.empty:
        return caps
    cat_all = _frame(group_summary(df, "category"))
    cat = _frame(group_summary(df, "category"), MIN_N)
    pri = _frame(group_summary(df, "priority", PRIORITY_ORDER), MIN_N)
    k = kpis(df)
    t = _trend(df)

    if t:
        caps["volume"] = (f"{t['month']} had {t['tickets']:,} tickets, {t['ratio']:.1f}x the previous three-month average"
                          + (f", with {t['open']:,} still open." if t["open"] else "."))
    top = cat_all.iloc[0]
    caps["category"] = f"{top['name']} generates the most tickets ({pct(top['share'])} of the total)."
    top_p = _frame(group_summary(df, "priority", PRIORITY_ORDER))
    big = top_p.loc[top_p["tickets"].idxmax()]
    caps["priority"] = f"{big['name']} is the most common priority ({pct(big['share'])} of tickets)."
    if len(cat) >= 2:
        slow = cat.loc[cat["median_resolution_hours"].idxmax()]
        caps["resolution"] = f"{slow['name']} is slowest, with a median of {hrs(slow['median_resolution_hours'])} to resolve."
    if k["sla_compliance"] is not None:
        caps["sla"] = f"{pct(k['sla_compliance'])} of resolved tickets were resolved within their SLA."
    caps["status"] = f"{k['open_tickets']:,} of {k['total_tickets']:,} tickets are currently open."
    sec = _frame(group_summary(df, "merchant_sector"))
    if not sec.empty:
        caps["sector"] = f"{sec.iloc[0]['name']} merchants raise the most tickets ({pct(sec.iloc[0]['share'])})."
    ag = _frame(group_summary(df[df["assigned_agent_id"].notna()], "agent_name"), MIN_N)
    if not ag.empty:
        b = ag.loc[ag["resolved"].idxmax()]
        caps["agents"] = f"{b['name']} resolved the most tickets ({int(b['resolved']):,})."
    return caps
