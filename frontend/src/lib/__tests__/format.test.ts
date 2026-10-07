import { describe, expect, it } from "vitest";

import { formatDuration, formatINR, formatRange, formatTime, nightsBetween } from "@/lib/format";

describe("formatINR", () => {
  it("uses rupees with Indian digit grouping", () => {
    expect(formatINR(12500)).toBe("₹12,500");
    expect(formatINR(1250000)).toBe("₹12,50,000");
    expect(formatINR(0)).toBe("₹0");
  });
});

describe("formatRange", () => {
  it("collapses the month when both dates share it", () => {
    expect(formatRange("2026-10-12", "2026-10-17")).toBe("12–17 Oct");
  });

  it("shows both months when the stay crosses a month boundary", () => {
    expect(formatRange("2026-10-28", "2026-11-02")).toBe("28 Oct – 2 Nov");
  });

  it("adds the years when the stay crosses a year boundary", () => {
    expect(formatRange("2026-12-30", "2027-01-02")).toBe("30 Dec 2026 – 2 Jan 2027");
  });
});

describe("nightsBetween", () => {
  it("counts nights across a month boundary", () => {
    expect(nightsBetween("2026-10-30", "2026-11-02")).toBe(3);
  });
});

describe("time and duration", () => {
  it("writes start times the way the experiences cards do", () => {
    expect(formatTime("08:30")).toBe("8:30 am");
    expect(formatTime("19:05")).toBe("7:05 pm");
    expect(formatTime("00:15")).toBe("12:15 am");
  });

  it("writes durations in hours", () => {
    expect(formatDuration(60)).toBe("1 hour");
    expect(formatDuration(150)).toBe("2.5 hours");
    expect(formatDuration(240)).toBe("4 hours");
  });
});
