"use client";

import { CheckCircle2, ChevronLeft, CreditCard, Smartphone } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import { PriceBreakdown, guestLabel } from "@/components/listing/BookingCard";
import { DateRangePanel } from "@/components/search/DateRangePanel";
import { GuestPanel } from "@/components/search/GuestPanel";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Skeleton } from "@/components/ui/Skeleton";
import { TextField } from "@/components/ui/TextField";
import { toast } from "@/components/ui/Toast";
import { useQuote } from "@/hooks/useQuote";
import { ApiError } from "@/lib/api/client";
import { bookingsApi } from "@/lib/api/bookings";
import { listingsApi } from "@/lib/api/listings";
import type { BookedRange } from "@/lib/availability";
import { formatDate, formatRange, formatTime } from "@/lib/format";
import { placeHeading } from "@/lib/listing";
import { isValidUpi, validateCard, type CardErrors } from "@/lib/payment";
import { parseSearch, toSearchParams } from "@/lib/searchState";
import type { Booking, ListingDetail, PaymentMethod } from "@/types/api";

type Data = { id: string; listing: ListingDetail; booked: BookedRange[] } | { id: string; listing: null };

function Row({ title, value, onEdit }: { title: string; value: string; onEdit?: () => void }) {
  return (
    <div className="flex items-start justify-between py-3">
      <div>
        <p className="font-semibold">{title}</p>
        <p className="text-muted">{value}</p>
      </div>
      {onEdit && (
        <button type="button" onClick={onEdit} className="font-semibold underline">
          Edit
        </button>
      )}
    </div>
  );
}

function Confirmation({ booking }: { booking: Booking }) {
  return (
    <main className="mx-auto max-w-[640px] px-6 py-12 text-center">
      <CheckCircle2 size={56} className="mx-auto text-[#008a05]" />
      <h1 className="mt-4 text-[32px] font-semibold">Your reservation is confirmed</h1>
      <p className="mt-2 text-muted">
        Confirmation code <strong className="text-ink">{booking.code}</strong>
      </p>
      <div className="mt-8 rounded-[16px] border border-line p-6 text-left">
        <p className="text-lg font-semibold">{booking.listing.title}</p>
        <p className="text-muted">{booking.listing.city}, {booking.listing.state}</p>
        <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="font-semibold">Check-in</p>
            <p>{formatDate(booking.check_in)}</p>
          </div>
          <div>
            <p className="font-semibold">Checkout</p>
            <p>{formatDate(booking.check_out)}</p>
          </div>
          <div>
            <p className="font-semibold">Guests</p>
            <p>{guestLabel(booking)}</p>
          </div>
          <div>
            <p className="font-semibold">Total paid</p>
            <p>₹{booking.total.toLocaleString("en-IN")}</p>
          </div>
        </div>
      </div>
      <div className="mt-8 flex justify-center gap-3">
        <Link href={`/trips/${booking.code}`}>
          <Button size="lg">View trip</Button>
        </Link>
        <Link href="/">
          <Button size="lg" variant="secondary">Keep exploring</Button>
        </Link>
      </div>
    </main>
  );
}

/** /book/stays/{id}: review the trip, pay (mocked) and get a confirmation code. */
export function CheckoutPage({ id }: { id: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const search = parseSearch(params);
  const trip = { checkIn: search.checkIn, checkOut: search.checkOut, guests: { adults: search.adults, children: search.children, infants: search.infants, pets: search.pets } };

  const [data, setData] = useState<Data | null>(null);
  const [editing, setEditing] = useState<"dates" | "guests" | null>(null);
  const [method, setMethod] = useState<PaymentMethod>("card");
  const [card, setCard] = useState({ number: "", expiry: "", cvv: "", name: "" });
  const [upi, setUpi] = useState("");
  const [errors, setErrors] = useState<CardErrors & { upi?: string }>({});
  const [busy, setBusy] = useState(false);
  const [booking, setBooking] = useState<Booking | null>(null);
  // One key per page load: pressing "Confirm" twice (or a network retry) can never book twice.
  const [idempotencyKey] = useState(() => crypto.randomUUID());

  useEffect(() => {
    let current = true;
    Promise.all([listingsApi.detail(id), listingsApi.availability(id)])
      .then(([listing, booked]) => current && setData({ id, listing, booked }))
      .catch(() => current && setData({ id, listing: null }));
    return () => {
      current = false;
    };
  }, [id]);

  const { quote, loading, error } = useQuote(id, trip.checkIn, trip.checkOut);

  const setTrip = (next: typeof trip) => {
    const query = toSearchParams({ ...search, checkIn: next.checkIn, checkOut: next.checkOut, ...next.guests });
    router.replace(`${pathname}?${query}`);
  };

  if (booking) return <Confirmation booking={booking} />;
  if (!data || data.id !== id) {
    return (
      <main className="mx-auto max-w-[1120px] space-y-4 px-6 py-10">
        <Skeleton className="h-9 w-64" />
        <Skeleton className="h-64 w-full" />
      </main>
    );
  }
  if (!data.listing) {
    return (
      <main className="mx-auto max-w-[560px] px-6 py-24 text-center">
        <h1 className="text-[28px] font-bold">That place isn&apos;t available</h1>
        <Link href="/homes" className="mt-4 inline-block font-semibold underline">Keep exploring</Link>
      </main>
    );
  }
  const { listing, booked } = data;
  const backToListing = `/rooms/${listing.id}?${toSearchParams({ ...search })}`;

  if (!trip.checkIn || !trip.checkOut || trip.guests.adults < 1) {
    return (
      <main className="mx-auto max-w-[560px] px-6 py-24 text-center">
        <h1 className="text-[28px] font-bold">Choose your dates and guests first</h1>
        <Link href={backToListing} className="mt-4 inline-block font-semibold underline">Back to the listing</Link>
      </main>
    );
  }

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const found: CardErrors & { upi?: string } = method === "card" ? validateCard(card) : isValidUpi(upi) ? {} : { upi: "Enter a valid UPI ID, like name@bank." };
    setErrors(found);
    if (Object.keys(found).length > 0 || !quote) return;

    setBusy(true);
    try {
      setBooking(
        await bookingsApi.create(
          { listing_id: listing.id, check_in: trip.checkIn!, check_out: trip.checkOut!, ...trip.guests, payment_method: method },
          idempotencyKey,
        ),
      );
      window.scrollTo({ top: 0 });
    } catch (err) {
      setBusy(false);
      if (err instanceof ApiError && err.status === 409) {
        toast.error("Those dates were just booked. Please pick other dates.");
        router.push(`${backToListing}#calendar`);
      } else {
        toast.error(err instanceof ApiError ? err.detail : "We couldn't complete your booking. Please try again.");
      }
    }
  };

  const tab = (active: boolean) => `flex flex-1 items-center justify-center gap-2 rounded-control border px-4 py-3 text-sm font-semibold transition ${active ? "border-2 border-ink" : "border-line hover:border-ink"}`;
  const updateCard = (key: keyof typeof card, value: string) => setCard((c) => ({ ...c, [key]: value }));

  return (
    <main className="mx-auto max-w-[1040px] px-4 py-8 md:px-6">
      <div className="mb-8 flex items-center gap-3">
        <Link href={backToListing} aria-label="Back to the listing" className="grid size-8 place-items-center rounded-full hover:bg-surface">
          <ChevronLeft size={20} />
        </Link>
        <h1 className="text-[32px] font-semibold">Confirm and pay</h1>
      </div>

      <div className="grid gap-12 lg:grid-cols-[1fr_420px]">
        <form onSubmit={submit} noValidate className="space-y-8">
          <section>
            <h2 className="mb-2 text-[22px] font-semibold">Your trip</h2>
            <div className="divide-y divide-line-soft">
              <Row title="Dates" value={formatRange(trip.checkIn, trip.checkOut)} onEdit={() => setEditing("dates")} />
              <Row title="Guests" value={guestLabel(trip.guests)} onEdit={() => setEditing("guests")} />
            </div>
          </section>

          <section className="border-t border-line-soft pt-8">
            <h2 className="mb-4 text-[22px] font-semibold">Pay with</h2>
            <div role="radiogroup" aria-label="Payment method" className="mb-5 flex gap-3">
              <button type="button" role="radio" aria-checked={method === "card"} onClick={() => setMethod("card")} className={tab(method === "card")}>
                <CreditCard size={18} /> Credit or debit card
              </button>
              <button type="button" role="radio" aria-checked={method === "upi"} onClick={() => setMethod("upi")} className={tab(method === "upi")}>
                <Smartphone size={18} /> UPI
              </button>
            </div>

            {method === "card" ? (
              <div className="space-y-3">
                <TextField
                  label="Card number"
                  inputMode="numeric"
                  autoComplete="cc-number"
                  placeholder="4242 4242 4242 4242"
                  value={card.number}
                  error={errors.number}
                  onChange={(e) => updateCard("number", e.target.value.replace(/\D/g, "").slice(0, 19).replace(/(\d{4})(?=\d)/g, "$1 "))}
                />
                <div className="grid grid-cols-2 gap-3">
                  <TextField
                    label="Expiry (MM/YY)"
                    inputMode="numeric"
                    autoComplete="cc-exp"
                    placeholder="12/28"
                    value={card.expiry}
                    error={errors.expiry}
                    onChange={(e) => {
                      const digits = e.target.value.replace(/\D/g, "").slice(0, 4);
                      updateCard("expiry", digits.length > 2 ? `${digits.slice(0, 2)}/${digits.slice(2)}` : digits);
                    }}
                  />
                  <TextField label="CVV" inputMode="numeric" autoComplete="cc-csc" placeholder="123" value={card.cvv} error={errors.cvv} onChange={(e) => updateCard("cvv", e.target.value.replace(/\D/g, "").slice(0, 4))} />
                </div>
                <TextField label="Name on card" autoComplete="cc-name" value={card.name} error={errors.name} onChange={(e) => updateCard("name", e.target.value)} />
              </div>
            ) : (
              <TextField label="UPI ID" placeholder="name@bank" value={upi} error={errors.upi} onChange={(e) => setUpi(e.target.value)} />
            )}
            <p className="mt-3 text-xs text-muted">This is a demo: no payment is taken and card details are never sent anywhere.</p>
          </section>

          <section className="border-t border-line-soft pt-8">
            <h2 className="mb-2 text-[22px] font-semibold">Cancellation policy</h2>
            <p className="text-sm">Free cancellation until check-in on {formatDate(trip.checkIn)}. After that the booking can no longer be cancelled.</p>
          </section>

          <section className="border-t border-line-soft pt-8">
            <p className="mb-4 text-xs text-muted">
              By selecting the button below, I agree to the host&apos;s house rules, check-in from {formatTime(listing.check_in_time)} and checkout by {formatTime(listing.check_out_time)}.
            </p>
            <Button type="submit" size="lg" loading={busy} disabled={!quote || !!error} className="w-full md:w-auto md:min-w-64">
              Confirm and pay
            </Button>
          </section>
        </form>

        <aside className="h-fit rounded-[16px] border border-line p-6 lg:sticky lg:top-28">
          <div className="mb-6 flex gap-4 border-b border-line-soft pb-6">
            {listing.photos[0] && (
              // eslint-disable-next-line @next/next/no-img-element -- local media through the proxy
              <img src={listing.photos[0].card_url} alt="" className="size-24 shrink-0 rounded-control object-cover" />
            )}
            <div>
              <p className="text-sm text-muted">{placeHeading(listing)}</p>
              <p className="font-semibold">{listing.title}</p>
              {listing.rating_avg !== null && <p className="mt-1 text-sm">★ {listing.rating_avg.toFixed(2)} ({listing.review_count})</p>}
            </div>
          </div>
          <h2 className="mb-4 text-[22px] font-semibold">Price details</h2>
          {loading && <Skeleton className="h-40 w-full" />}
          {error && <p role="alert" className="text-sm text-[#c13515]">{error}</p>}
          {quote && <PriceBreakdown quote={quote} />}
        </aside>
      </div>

      {editing === "dates" && (
        <Modal open onClose={() => setEditing(null)} title="Change dates" className="md:!max-w-[780px]">
          <div className="flex justify-center overflow-x-auto p-6">
            <DateRangePanel
              checkIn={trip.checkIn}
              checkOut={trip.checkOut}
              booked={booked}
              months={typeof window !== "undefined" && window.innerWidth < 768 ? 1 : 2}
              onChange={(checkIn, checkOut) => setTrip({ ...trip, checkIn, checkOut })}
            />
          </div>
          <footer className="flex justify-end border-t border-line-soft px-6 py-4">
            <Button variant="dark" size="lg" disabled={!trip.checkOut} onClick={() => setEditing(null)}>
              Save
            </Button>
          </footer>
        </Modal>
      )}
      {editing === "guests" && (
        <Modal open onClose={() => setEditing(null)} title="Change guests" className="md:!max-w-[460px]">
          <div className="p-6">
            <GuestPanel value={trip.guests} minAdults={1} maxGuests={listing.max_guests} allowPets={listing.pets_allowed} onChange={(guests) => setTrip({ ...trip, guests })} />
          </div>
          <footer className="flex justify-end border-t border-line-soft px-6 py-4">
            <Button variant="dark" size="lg" onClick={() => setEditing(null)}>Save</Button>
          </footer>
        </Modal>
      )}
    </main>
  );
}
