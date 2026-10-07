import { addDays, format, parseISO } from "date-fns";

/** A booked stay, as the API reports it: [check_in, check_out), the guest leaves on check_out. */
export type BookedRange = { check_in: string; check_out: string };

/**
 * Would a stay from `checkIn` to `checkOut` share a night with any booking? Same half-open rule as
 * the backend: a stay may start on another's check-out day and end on another's check-in day.
 * ISO dates compare correctly as strings.
 */
export function isRangeBlocked(checkIn: string, checkOut: string, booked: BookedRange[]): boolean {
  return booked.some((range) => checkIn < range.check_out && checkOut > range.check_in);
}

/** Calendar matchers for the nights that are taken. The check-out day itself stays pickable. */
export function disabledDays(booked: BookedRange[]) {
  return booked.map((range) => ({ from: parseISO(range.check_in), to: addDays(parseISO(range.check_out), -1) }));
}

/** The first night on or after `date` that is not inside a booking. */
export function nextFreeNight(date: string, booked: BookedRange[]): string {
  let day = date;
  for (let moved = true; moved; ) {
    moved = false;
    for (const range of booked) {
      if (day >= range.check_in && day < range.check_out) {
        day = range.check_out;
        moved = true;
      }
    }
  }
  return day;
}

export const toIso = (date: Date) => format(date, "yyyy-MM-dd");
