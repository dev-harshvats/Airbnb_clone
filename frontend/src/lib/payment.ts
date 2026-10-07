/**
 * Client-side checks for the mocked payment step. Nothing here is sent anywhere: the backend only
 * learns whether the guest chose "card" or "upi".
 */

export type CardInput = { number: string; expiry: string; cvv: string; name: string };
export type CardErrors = Partial<Record<keyof CardInput, string>>;

function passesLuhn(digits: string): boolean {
  let sum = 0;
  for (let i = 0; i < digits.length; i++) {
    let n = Number(digits[digits.length - 1 - i]);
    if (i % 2 === 1) {
      n *= 2;
      if (n > 9) n -= 9;
    }
    sum += n;
  }
  return sum % 10 === 0;
}

export function validateCard(card: CardInput, now: Date = new Date()): CardErrors {
  const errors: CardErrors = {};
  const digits = card.number.replace(/\s/g, "");
  if (!/^\d{13,19}$/.test(digits) || !passesLuhn(digits)) errors.number = "Enter a valid card number.";

  const match = /^(0[1-9]|1[0-2])\/(\d{2})$/.exec(card.expiry.trim());
  // A card works through the last day of its expiry month.
  const lastDay = match ? new Date(Date.UTC(2000 + Number(match[2]), Number(match[1]), 0, 23, 59, 59)) : null;
  if (!lastDay || lastDay < now) errors.expiry = "Enter a valid expiry date (MM/YY).";

  if (!/^\d{3,4}$/.test(card.cvv)) errors.cvv = "Enter the 3 or 4 digit security code.";
  if (!card.name.trim()) errors.name = "Enter the name on the card.";
  return errors;
}

export const isValidUpi = (id: string) => /^[a-zA-Z0-9._-]{2,}@[a-zA-Z]{2,}$/.test(id.trim());
