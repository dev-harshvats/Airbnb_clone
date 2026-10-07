import { describe, expect, it } from "vitest";

import { activeFilterCount, parseSearch, toListingQuery, toSearchParams, withoutPaging } from "@/lib/searchState";

describe("search state", () => {
  it("round-trips every filter through the URL", () => {
    const url = new URLSearchParams(
      "check_in=2026-11-10&check_out=2026-11-13&adults=2&children=1&infants=1&pets=1&min_price=2000&max_price=9000" +
        "&place_type=entire&property_types=villa&property_types=cabin&bedrooms=2&beds=3&bathrooms=2" +
        "&amenities=wifi&amenities=pool&category=beachfront&superhost=true&guest_favourite=true&sort=price_asc",
    );
    const state = parseSearch(url);
    expect(state).toMatchObject({ adults: 2, children: 1, minPrice: 2000, maxPrice: 9000, propertyTypes: ["villa", "cabin"] });
    expect(parseSearch(toSearchParams(state))).toEqual(state);
  });

  it("leaves out anything that is not set", () => {
    expect(toSearchParams(parseSearch(new URLSearchParams())).toString()).toBe("");
    expect(toSearchParams(parseSearch(new URLSearchParams("adults=0&bedrooms=0"))).toString()).toBe("");
  });

  it("counts the filters the Filters button should badge, not search or category", () => {
    const state = parseSearch(
      new URLSearchParams("adults=2&category=cabins&min_price=1000&amenities=wifi&amenities=pool&superhost=true&bedrooms=2"),
    );
    // price (1) + amenities (2) + superhost (1) + bedrooms (1)
    expect(activeFilterCount(state)).toBe(5);
  });

  it("builds the API query, joining guests and dropping paging", () => {
    const state = parseSearch(new URLSearchParams("adults=3&children=1&min_price=500&page=4"));
    expect(toListingQuery(state, "Goa")).toMatchObject({ location: "Goa", adults: 3, children: 1, min_price: 500 });
    expect(withoutPaging(new URLSearchParams("page=4&adults=2")).toString()).toBe("adults=2");
  });
});
