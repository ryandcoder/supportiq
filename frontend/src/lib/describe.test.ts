import { describe, expect, it } from "vitest";
import { period } from "./format";
import { describeFilters } from "./describe";

describe("describeFilters", () => {
  it("returns nothing when no filter is set", () => {
    expect(describeFilters({})).toEqual([]);
  });

  it("describes lists, dates and agent names", () => {
    const out = describeFilters(
      { priority: ["P1", "P2"], date_from: "2025-06-01", agent_id: [3, 9] },
      { 3: "Ana" },
    );
    expect(out).toEqual(["Created from 2025-06-01", "Priority: P1, P2", "Agent: Ana, #9"]);
  });

  it("describes a date range with both ends", () => {
    expect(describeFilters({ date_from: "2025-01-01", date_to: "2025-03-31" })).toEqual(["Created from 2025-01-01 to 2025-03-31"]);
  });
});

describe("period", () => {
  it("spans the first and last month", () => {
    expect(period([{ month: "2025-01" }, { month: "2025-02" }, { month: "2026-06" }])).toBe("January 2025 – June 2026");
    expect(period([])).toBe("");
  });
});
