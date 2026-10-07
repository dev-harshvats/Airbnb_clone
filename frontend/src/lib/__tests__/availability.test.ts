import { describe, expect, it } from "vitest";

import { disabledDays, isRangeBlocked, nextFreeNight } from "@/lib/availability";

const booked = [{ check_in: "2026-11-10", check_out: "2026-11-13" }];

describe("availability", () => {
  it("lets a stay start on the day another one checks out, and end on the day one checks in", () => {
    expect(isRangeBlocked("2026-11-13", "2026-11-15", booked)).toBe(false);
    expect(isRangeBlocked("2026-11-08", "2026-11-10", booked)).toBe(false);
  });

  it("blocks a stay that shares even one night with a booking", () => {
    expect(isRangeBlocked("2026-11-12", "2026-11-14", booked)).toBe(true);
    expect(isRangeBlocked("2026-11-09", "2026-11-11", booked)).toBe(true);
  });

  it("blocks a stay that spans a whole booking", () => {
    expect(isRangeBlocked("2026-11-05", "2026-11-20", booked)).toBe(true);
  });

  it("greys out the nights that are taken but not the check-out day", () => {
    const [rule] = disabledDays(booked) as { from: Date; to: Date }[];
    expect(rule.from.getDate()).toBe(10);
    expect(rule.to.getDate()).toBe(12); // the 13th is a free check-in
  });

  it("finds the first night after a booking that a stay can start", () => {
    expect(nextFreeNight("2026-11-10", booked)).toBe("2026-11-13");
    expect(nextFreeNight("2026-11-20", booked)).toBe("2026-11-20");
  });
});
