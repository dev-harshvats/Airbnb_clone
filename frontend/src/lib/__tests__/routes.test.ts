import { describe, expect, it } from "vitest";

import { isLanding, placeFromPath, searchPath, sectionOf, slugToPlace } from "@/lib/routes";

describe("routes", () => {
  it("builds the same search URLs as the original site", () => {
    expect(searchPath("homes", "Goa")).toBe("/s/Goa/homes");
    expect(searchPath("experiences", "North Goa")).toBe("/s/North-Goa/experiences");
    expect(searchPath("services", null, { service_type: "chefs" })).toBe("/s/services?service_type=chefs");
  });

  it("reads places back from slugs, with or without the country suffix", () => {
    expect(slugToPlace("Goa--India")).toBe("Goa");
    expect(slugToPlace("North-Goa")).toBe("North Goa");
    expect(placeFromPath("/s/Jaipur/homes")).toBe("Jaipur");
    expect(placeFromPath("/s/homes")).toBeNull();
  });

  it("knows which header tab a page belongs to", () => {
    expect(sectionOf("/")).toBe("all");
    expect(sectionOf("/homes")).toBe("homes");
    expect(sectionOf("/rooms/12")).toBe("homes");
    expect(sectionOf("/experiences/5")).toBe("experiences");
    expect(sectionOf("/s/Goa/services")).toBe("services");
    expect(sectionOf("/s/experiences")).toBe("experiences");
    expect(sectionOf("/trips")).toBe("all");
  });

  it("shows the tall header only on the four landing pages", () => {
    expect(["/", "/homes", "/experiences", "/services"].every(isLanding)).toBe(true);
    expect(isLanding("/s/Goa/homes")).toBe(false);
  });
});
