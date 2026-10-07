import { describe, expect, it } from "vitest";
import { errorMessages, toQuery } from "./api";

const parse = (q: string) => new URLSearchParams(q.startsWith("?") ? q.slice(1) : q);

describe("toQuery", () => {
  it("returns an empty string when there is nothing to send", () => {
    expect(toQuery({})).toBe("");
    expect(toQuery({ category: [], date_from: undefined })).toBe("");
  });

  it("repeats a parameter for every value in a list (what the API expects)", () => {
    const p = parse(toQuery({ category: ["Payments & Checkout", "Notifications"], agent_id: [1, 2] }));
    expect(p.getAll("category")).toEqual(["Payments & Checkout", "Notifications"]);
    expect(p.getAll("agent_id")).toEqual(["1", "2"]);
  });

  it("encodes special characters so they survive the round trip", () => {
    expect(toQuery({ category: ["A & B"] })).not.toContain("A & B");
  });

  it("adds extra parameters but skips empty ones", () => {
    const p = parse(toQuery({ priority: ["P1"] }, { search: "", page: 2, sort_by: "created_at" }));
    expect(p.has("search")).toBe(false);
    expect(p.get("page")).toBe("2");
    expect(p.get("priority")).toBe("P1");
  });
});

describe("errorMessages", () => {
  it("reads the API's error list", () => {
    expect(errorMessages({ response: { data: { detail: { errors: ["a", "b"] } } } })).toEqual(["a", "b"]);
  });
  it("reads a plain string detail", () => {
    expect(errorMessages({ response: { data: { detail: "date_from must be YYYY-MM-DD" } } })).toEqual(["date_from must be YYYY-MM-DD"]);
  });
  it("falls back to a friendly message", () => {
    expect(errorMessages(new Error("Network Error"))).toEqual(["Network Error"]);
    expect(errorMessages({})[0]).toMatch(/API running/);
  });
});
