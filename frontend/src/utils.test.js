import { describe, expect, it } from "vitest";
import { errorMessage } from "./api.js";
import { formatMinutes, percent, titleCase } from "./utils.js";

describe("utils", () => {
  it("formats minutes as hours and minutes", () => {
    expect(formatMinutes(535)).toBe("8h 55m");
    expect(formatMinutes(45)).toBe("45m");
    expect(formatMinutes(null)).toBe("-");
  });
  it("title-cases enum values", () => {
    expect(titleCase("IN_TRANSIT")).toBe("In Transit");
  });
  it("formats probabilities", () => {
    expect(percent(0.824)).toBe("82%");
    expect(percent(undefined)).toBe("-");
  });
});

describe("errorMessage", () => {
  it("shows validation errors from the API", () => {
    const err = { response: { data: { detail: "Invalid data", errors: [{ field: "distance_km", message: "must be > 0" }] } } };
    expect(errorMessage(err)).toContain("distance_km");
  });
  it("shows a friendly message when the server is unreachable", () => {
    expect(errorMessage({ code: "ERR_NETWORK" })).toMatch(/Cannot reach the server/);
  });
  it("uses the detail string for normal HTTP errors", () => {
    expect(errorMessage({ response: { status: 404, data: { detail: "Shipment not found" } } })).toBe("Shipment not found");
  });
});
