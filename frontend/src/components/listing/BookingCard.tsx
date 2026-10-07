"use client";

import { ChevronDown, Star } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { GuestPanel, type Guests } from "@/components/search/GuestPanel";
import { Button } from "@/components/ui/Button";
import { useQuote } from "@/hooks/useQuote";
import { formatDate, formatINR, formatRange } from "@/lib/format";
import { plural } from "@/lib/listing";
import type { ListingDetail, Quote } from "@/types/api";

export type Trip = { checkIn?: string; checkOut?: string; guests: Guests };

export function checkoutHref(listingId: number, trip: Trip) {
  const params = new URLSearchParams();
  if (trip.checkIn) params.set("check_in", trip.checkIn);
  if (trip.checkOut) params.set("check_out", trip.checkOut);
  for (const [key, value] of Object.entries(trip.guests)) if (value) params.set(key, String(value));
  return `/book/stays/${listingId}?${params}`;
}

export const guestCount = (g: Guests) => g.adults + g.children;
export const guestLabel = (g: Guests) => {
  const parts = [plural(guestCount(g) || 1, "guest")];
  if (g.infants) parts.push(plural(g.infants, "infant"));
  if (g.pets) parts.push(plural(g.pets, "pet"));
  return parts.join(", ");
};

/** The itemised price. Every number comes from the server's quote. */
export function PriceBreakdown({ quote }: { quote: Quote }) {
  const row = "flex justify-between";
  return (
    <div className="space-y-3 text-base">
      <p className={row}>
        <span className="underline">
          {formatINR(quote.nightly_rate)} x {plural(quote.nights, "night")}
        </span>
        <span>{formatINR(quote.subtotal)}</span>
      </p>
      {quote.cleaning_fee > 0 && (
        <p className={row}>
          <span className="underline">Cleaning fee</span>
          <span>{formatINR(quote.cleaning_fee)}</span>
        </p>
      )}
      <p className={row}>
        <span className="underline">Airbnb service fee</span>
        <span>{formatINR(quote.service_fee)}</span>
      </p>
      <p className={row}>
        <span className="underline">Taxes</span>
        <span>{formatINR(quote.taxes)}</span>
      </p>
      <p className={`${row} border-t border-line-soft pt-4 font-semibold`}>
        <span>Total (INR)</span>
        <span>{formatINR(quote.total)}</span>
      </p>
    </div>
  );
}

type Props = {
  listing: ListingDetail;
  trip: Trip;
  onTripChange: (trip: Trip) => void;
  onPickDates: () => void;
  /** The mobile bottom bar renders only the price and the button. */
  compact?: boolean;
};

export function BookingCard({ listing, trip, onTripChange, onPickDates, compact }: Props) {
  const [guestsOpen, setGuestsOpen] = useState(false);
  const { quote, loading, error } = useQuote(listing.id, trip.checkIn, trip.checkOut);
  const hasDates = !!(trip.checkIn && trip.checkOut);
  const ready = hasDates && !!trip.guests.adults && !!quote && !error;

  const reserve = ready ? (
    <Link href={checkoutHref(listing.id, trip)} className="contents">
      <Button size="lg" fullWidth>Reserve</Button>
    </Link>
  ) : (
    <Button size="lg" fullWidth onClick={() => (hasDates ? setGuestsOpen(true) : onPickDates())} disabled={hasDates && !!error}>
      {hasDates ? "Reserve" : "Check availability"}
    </Button>
  );

  if (compact) {
    return (
      <div className="flex items-center justify-between gap-4">
        <div>
          <p>
            <span className="text-base font-semibold">{formatINR(quote ? quote.total : listing.price_per_night)}</span>{" "}
            <span className="text-sm">{quote ? `for ${plural(quote.nights, "night")}` : "night"}</span>
          </p>
          <button onClick={onPickDates} className="text-sm font-semibold underline">
            {hasDates ? formatRange(trip.checkIn!, trip.checkOut!) : "Add dates"}
          </button>
        </div>
        <div className="w-40">{reserve}</div>
      </div>
    );
  }

  const field = "px-3 py-2.5 text-left";
  return (
    <aside className="rounded-[12px] border border-line p-6 shadow-card lg:sticky lg:top-28">
      <div className="flex items-baseline justify-between">
        <p>
          {hasDates && quote ? (
            <>
              <span className="text-[22px] font-semibold">{formatINR(quote.total)}</span>{" "}
              <span className="text-muted">for {plural(quote.nights, "night")}</span>
            </>
          ) : (
            <>
              <span className="text-[22px] font-semibold">{formatINR(listing.price_per_night)}</span> <span>night</span>
            </>
          )}
        </p>
        {listing.rating_avg !== null && (
          <a href="#reviews" className="flex items-center gap-1 text-sm">
            <Star size={12} className="fill-ink" /> {listing.rating_avg.toFixed(2)} · <span className="underline">{listing.review_count}</span>
          </a>
        )}
      </div>

      <div className="mt-5 rounded-control border border-muted">
        <div className="grid grid-cols-2 border-b border-muted">
          <button type="button" onClick={onPickDates} className={`${field} border-r border-muted`}>
            <span className="block text-[10px] font-bold uppercase">Check-in</span>
            <span className={`text-sm ${trip.checkIn ? "" : "text-muted"}`}>{trip.checkIn ? formatDate(trip.checkIn) : "Add date"}</span>
          </button>
          <button type="button" onClick={onPickDates} className={field}>
            <span className="block text-[10px] font-bold uppercase">Checkout</span>
            <span className={`text-sm ${trip.checkOut ? "" : "text-muted"}`}>{trip.checkOut ? formatDate(trip.checkOut) : "Add date"}</span>
          </button>
        </div>
        <button type="button" onClick={() => setGuestsOpen((v) => !v)} aria-expanded={guestsOpen} className={`${field} flex w-full items-center justify-between`}>
          <span>
            <span className="block text-[10px] font-bold uppercase">Guests</span>
            <span className="text-sm">{guestLabel(trip.guests)}</span>
          </span>
          <ChevronDown size={16} className={guestsOpen ? "rotate-180" : ""} />
        </button>
        {guestsOpen && (
          <div className="border-t border-muted p-4">
            <GuestPanel
              value={trip.guests}
              minAdults={1}
              maxGuests={listing.max_guests}
              allowPets={listing.pets_allowed}
              onChange={(guests) => onTripChange({ ...trip, guests })}
            />
          </div>
        )}
      </div>

      <div className="mt-4">{reserve}</div>

      {hasDates && loading && <p className="mt-4 text-center text-sm text-muted">Checking the price…</p>}
      {hasDates && error && <p role="alert" className="mt-4 text-center text-sm text-[#c13515]">{error}</p>}
      {quote && !error && (
        <>
          <p className="mt-3 text-center text-sm text-muted">You won&apos;t be charged yet</p>
          <div className="mt-6">
            <PriceBreakdown quote={quote} />
          </div>
        </>
      )}
    </aside>
  );
}
