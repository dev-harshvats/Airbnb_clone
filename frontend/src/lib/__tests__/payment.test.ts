import { describe, expect, it } from "vitest";

import { isValidUpi, validateCard } from "@/lib/payment";

const now = new Date("2026-10-08T00:00:00Z");
const good = { number: "4242 4242 4242 4242", expiry: "12/28", cvv: "123", name: "Kavya Shah" };

describe("payment validation", () => {
  it("accepts a well-formed card and reports nothing", () => {
    expect(validateCard(good, now)).toEqual({});
  });

  it("rejects numbers that fail the Luhn check, an expired card, a short CVV and a missing name", () => {
    const errors = validateCard({ number: "4242 4242 4242 4241", expiry: "09/26", cvv: "12", name: " " }, now);
    expect(Object.keys(errors).sort()).toEqual(["cvv", "expiry", "name", "number"]);
  });

  it("treats the expiry month as valid until its last day", () => {
    expect(validateCard({ ...good, expiry: "10/26" }, now).expiry).toBeUndefined();
  });

  it("accepts name@bank UPI ids and nothing else", () => {
    expect(isValidUpi("kavya.shah@okhdfc")).toBe(true);
    expect(isValidUpi("kavya.shah")).toBe(false);
    expect(isValidUpi("@okhdfc")).toBe(false);
  });
});
