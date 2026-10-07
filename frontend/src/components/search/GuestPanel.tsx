"use client";

import { Stepper } from "@/components/ui/Stepper";

export type Guests = { adults: number; children: number; infants: number; pets: number };

const ROWS: { key: keyof Guests; title: string; hint: string; max: number }[] = [
  { key: "adults", title: "Adults", hint: "Ages 13 or above", max: 16 },
  { key: "children", title: "Children", hint: "Ages 2–12", max: 15 },
  { key: "infants", title: "Infants", hint: "Under 2", max: 5 },
  { key: "pets", title: "Pets", hint: "Bringing a service animal?", max: 5 },
];

type Props = {
  value: Guests;
  onChange: (next: Guests) => void;
  /** A listing's guest limit (adults + children; infants and pets don't count). */
  maxGuests?: number;
  /** Hide the pets row for listings that don't allow them. */
  allowPets?: boolean;
  /** Bookings need at least one adult. */
  minAdults?: number;
};

/** Who's coming: adult / child / infant / pet steppers. Adding a child or infant implies at least one adult. */
export function GuestPanel({ value, onChange, maxGuests, allowPets = true, minAdults = 0 }: Props) {
  const set = (key: keyof Guests, n: number) => {
    const next = { ...value, [key]: n };
    if ((key === "children" || key === "infants") && n > 0 && next.adults === 0) next.adults = 1;
    onChange(next);
  };
  const counted = value.adults + value.children;
  const rows = ROWS.filter((row) => row.key !== "pets" || allowPets);

  return (
    <ul className="divide-y divide-line-soft">
      {rows.map((row) => {
        const room = maxGuests !== undefined && (row.key === "adults" || row.key === "children") ? value[row.key] + Math.max(0, maxGuests - counted) : row.max;
        const needsAdult = row.key === "adults" && (value.children > 0 || value.infants > 0);
        return (
          <li key={row.key} className="flex items-center justify-between py-4 first:pt-0 last:pb-0">
            <div>
              <p className="text-base font-medium">{row.title}</p>
              <p className="text-sm text-muted">{row.hint}</p>
            </div>
            <Stepper
              label={row.title.toLowerCase()}
              value={value[row.key]}
              min={row.key === "adults" ? Math.max(minAdults, needsAdult ? 1 : 0) : 0}
              max={Math.min(row.max, room)}
              onChange={(n) => set(row.key, n)}
            />
          </li>
        );
      })}
      {maxGuests !== undefined && <li className="pt-4 text-xs text-muted">This place has a maximum of {maxGuests} guests, not including infants.</li>}
    </ul>
  );
}
