"use client";

import { parseISO, startOfDay } from "date-fns";
import { DayPicker, type DateRange } from "react-day-picker";
import "react-day-picker/style.css";

import { disabledDays, isRangeBlocked, toIso, type BookedRange } from "@/lib/availability";

type Props = {
  checkIn?: string;
  checkOut?: string;
  onChange: (checkIn?: string, checkOut?: string) => void;
  /** Taken nights of a listing: greyed out, and a range that would cross one starts over. */
  booked?: BookedRange[];
  /** One month on phones and inside narrow modals. */
  months?: 1 | 2;
};

/** A range calendar: the first click picks check-in, the second check-out. Past days are disabled. */
export function DateRangePanel({ checkIn, checkOut, onChange, booked = [], months = 2 }: Props) {
  const today = startOfDay(new Date());
  const selected: DateRange | undefined = checkIn ? { from: parseISO(checkIn), to: checkOut ? parseISO(checkOut) : undefined } : undefined;

  return (
    <DayPicker
      mode="range"
      numberOfMonths={months}
      selected={selected}
      defaultMonth={selected?.from ?? today}
      startMonth={today}
      disabled={[{ before: today }, ...disabledDays(booked)]}
      onSelect={(range, triggerDate) => {
        const from = range?.from ? toIso(range.from) : undefined;
        // Picking the same day twice would be a zero-night stay; treat it as just a check-in.
        const to = range?.to && from && toIso(range.to) !== from ? toIso(range.to) : undefined;
        if (from && to && isRangeBlocked(from, to, booked)) return onChange(toIso(triggerDate), undefined);
        onChange(from, to);
      }}
    />
  );
}
