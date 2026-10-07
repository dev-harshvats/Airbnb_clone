import { describe, expect, it } from "vitest";

import { WIZARD_STEPS, emptyDraft, firstInvalidStep, validateStep } from "@/lib/hosting";

const complete = {
  ...emptyDraft(),
  propertyType: "villa",
  addressLine: "12 Beach Road",
  city: "Anjuna",
  state: "Goa",
  postalCode: "403509",
  categoryId: 2,
  title: "Sunny villa by the sea",
  description: "A calm place close to the beach.",
  pricePerNight: 4500,
};

describe("wizard step validation", () => {
  it("has the 13 steps of the Airbnb flow, ending with the review", () => {
    expect(WIZARD_STEPS).toHaveLength(13);
    expect(WIZARD_STEPS.at(-1)).toBe("review");
  });

  it("limits the title to 50 characters and the description to 500", () => {
    expect(validateStep("title", { ...complete, title: "x".repeat(51) }, 5)).toMatch(/50/);
    expect(validateStep("title", { ...complete, title: "x".repeat(50) }, 5)).toBeNull();
    expect(validateStep("description", { ...complete, description: "x".repeat(501) }, 5)).toMatch(/500/);
  });

  it("needs at least five photos and a nightly price of at least ₹500", () => {
    expect(validateStep("photos", complete, 4)).toMatch(/5 photos/);
    expect(validateStep("photos", complete, 5)).toBeNull();
    expect(validateStep("price", { ...complete, pricePerNight: 499 }, 5)).toMatch(/500/);
    expect(validateStep("price", { ...complete, pricePerNight: 500 }, 5)).toBeNull();
  });

  it("finds the first step that still blocks publishing", () => {
    expect(firstInvalidStep(complete, 5)).toBeNull();
    expect(firstInvalidStep({ ...complete, city: "" }, 5)).toBe("location");
    expect(firstInvalidStep(complete, 2)).toBe("photos");
  });
});
