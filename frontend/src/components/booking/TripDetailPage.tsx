"use client";

import { ChevronLeft } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { PriceBreakdown, guestLabel } from "@/components/listing/BookingCard";
import { ReviewForm } from "@/components/review/ReviewForm";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Skeleton } from "@/components/ui/Skeleton";
import { toast } from "@/components/ui/Toast";
import { ApiError } from "@/lib/api/client";
import { bookingsApi } from "@/lib/api/bookings";
import { formatDate } from "@/lib/format";
import type { Booking } from "@/types/api";

/** /trips/{code}: one reservation, with cancel (before check-in) and review (after the stay). */
export function TripDetailPage({ code }: { code: string }) {
  const [booking, setBooking] = useState<Booking | null>(null);
  const [missing, setMissing] = useState(false);
  const [dialog, setDialog] = useState<"cancel" | "review" | null>(null);
  const [busy, setBusy] = useState(false);

  const reload = () =>
    bookingsApi
      .get(code)
      .then(setBooking)
      .catch(() => setMissing(true));

  useEffect(() => {
    let current = true;
    bookingsApi
      .get(code)
      .then((result) => current && setBooking(result))
      .catch(() => current && setMissing(true));
    return () => {
      current = false;
    };
  }, [code]);

  const cancel = async () => {
    setBusy(true);
    try {
      setBooking(await bookingsApi.cancel(code));
      toast.success("Your reservation was cancelled");
      setDialog(null);
    } catch (error) {
      toast.error(error instanceof ApiError ? error.detail : "We couldn't cancel this reservation.");
    } finally {
      setBusy(false);
    }
  };

  if (missing) {
    return (
      <main className="mx-auto max-w-[560px] px-6 py-24 text-center">
        <h1 className="text-[28px] font-bold">We couldn&apos;t find that trip</h1>
        <Link href="/trips" className="mt-4 inline-block font-semibold underline">Back to trips</Link>
      </main>
    );
  }
  if (!booking) {
    return (
      <main className="mx-auto max-w-[1040px] space-y-4 px-6 py-10">
        <Skeleton className="h-9 w-64" />
        <Skeleton className="h-64 w-full" />
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-[1040px] px-6 py-10">
      <Link href="/trips" className="mb-4 inline-flex items-center gap-1 text-sm font-medium hover:underline">
        <ChevronLeft size={16} /> Trips
      </Link>
      <div className="grid gap-12 lg:grid-cols-[1fr_380px]">
        <div>
          <p className={`mb-2 inline-block rounded-full px-3 py-1 text-xs font-semibold ${booking.status === "cancelled" ? "bg-[#fff0ef] text-[#c13515]" : "bg-[#e6f4ea] text-[#0a6b1f]"}`}>
            {booking.status === "cancelled" ? "Cancelled" : booking.can_review || booking.has_review ? "Completed" : "Confirmed"}
          </p>
          <h1 className="text-[32px] font-semibold leading-tight">{booking.listing.title}</h1>
          <p className="mt-1 text-muted">{booking.listing.city}, {booking.listing.state} · Hosted by {booking.listing.host_first_name}</p>

          <dl className="mt-8 grid grid-cols-2 gap-6 border-y border-line-soft py-6">
            <div>
              <dt className="font-semibold">Check-in</dt>
              <dd>{formatDate(booking.check_in)}</dd>
            </div>
            <div>
              <dt className="font-semibold">Checkout</dt>
              <dd>{formatDate(booking.check_out)}</dd>
            </div>
            <div>
              <dt className="font-semibold">Guests</dt>
              <dd>{guestLabel(booking)}</dd>
            </div>
            <div>
              <dt className="font-semibold">Confirmation code</dt>
              <dd>{booking.code}</dd>
            </div>
          </dl>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link href={`/rooms/${booking.listing.id}`}>
              <Button variant="secondary" size="lg">View listing</Button>
            </Link>
            {booking.can_review && (
              <Button size="lg" onClick={() => setDialog("review")}>Write a review</Button>
            )}
            {booking.has_review && <p className="self-center text-sm text-muted">You reviewed this stay.</p>}
            {booking.can_cancel && (
              <Button variant="secondary" size="lg" onClick={() => setDialog("cancel")}>Cancel reservation</Button>
            )}
          </div>
        </div>

        <aside className="h-fit rounded-[16px] border border-line p-6">
          <h2 className="mb-4 text-[22px] font-semibold">Price details</h2>
          <PriceBreakdown quote={booking} />
          <p className="mt-4 text-sm text-muted">Paid by {booking.payment_method === "upi" ? "UPI" : "card"}</p>
        </aside>
      </div>

      <Modal open={dialog === "cancel"} onClose={() => setDialog(null)} title="Cancel this reservation?" className="md:!max-w-[460px]">
        <div className="p-6">
          <p>
            Your stay at <strong>{booking.listing.title}</strong> on {formatDate(booking.check_in)} will be cancelled and the dates will be released. This can&apos;t be undone.
          </p>
          <div className="mt-6 flex justify-between">
            <Button variant="ghost" onClick={() => setDialog(null)}>Keep reservation</Button>
            <Button variant="dark" loading={busy} onClick={cancel}>Cancel reservation</Button>
          </div>
        </div>
      </Modal>
      <Modal open={dialog === "review"} onClose={() => setDialog(null)} title="Review your stay" className="md:!max-w-[560px]">
        <ReviewForm
          code={code}
          onDone={() => {
            setDialog(null);
            void reload();
          }}
        />
      </Modal>
    </main>
  );
}
