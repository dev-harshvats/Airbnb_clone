import { describe, expect, it } from "vitest";

import { placeHeading, priceCaption, roomSummary } from "@/lib/listing";

describe("listing captions", () => {
  it("names the place the way Airbnb does", () => {
    expect(placeHeading({ property_type: "flat", place_type: "entire", city: "Anjuna" })).toBe("Flat in Anjuna");
    expect(placeHeading({ property_type: "guest_house", place_type: "private_room", city: "Leh" })).toBe(
      "Room in guest house in Leh",
    );
  });

  it("shows the total for the searched dates, or the nightly rate", () => {
    expect(priceCaption({ price_per_night: 5000, total_for_dates: 10446 }, 2)).toEqual({
      amount: "₹10,446",
      suffix: "for 2 nights",
    });
    expect(priceCaption({ price_per_night: 5000, total_for_dates: null })).toEqual({ amount: "₹5,000", suffix: "night" });
  });

  it("summarises the rooms", () => {
    expect(roomSummary({ bedrooms: 1, beds: 2, bathrooms: 1.5 })).toBe("1 bedroom · 2 beds · 1.5 bathrooms");
  });
});
