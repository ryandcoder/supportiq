import { describe, expect, it } from "vitest";
import { hours, int, monthLabel, monthLong, pct, score, shortDate } from "./format";

describe("number formatting", () => {
  it("formats percentages and handles missing values", () => {
    expect(pct(0.4321, 1)).toBe("43.2%");
    expect(pct(0.5)).toBe("50%");
    expect(pct(null)).toBe("–");
    expect(pct(undefined)).toBe("–");
  });

  it("keeps zero as a real value, not as missing", () => {
    expect(pct(0)).toBe("0%");
    expect(int(0)).toBe("0");
    expect(hours(0)).toBe("0.0h");
  });

  it("formats hours, counts and scores", () => {
    expect(hours(26.04)).toBe("26.0h");
    expect(int(2057)).toBe("2,057");
    expect(score(0.7456)).toBe("0.75");
    expect(hours(null)).toBe("–");
  });
});

describe("date formatting", () => {
  it("turns YYYY-MM into labels", () => {
    expect(monthLabel("2026-06")).toBe("Jun 26");
    expect(monthLong("2025-01")).toBe("January 2025");
  });

  it("cuts timestamps to the date", () => {
    expect(shortDate("2025-05-13T02:10:36")).toBe("2025-05-13");
  });
});
