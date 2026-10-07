"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Skeleton } from "@/components/ui/Skeleton";
import { bookingsApi } from "@/lib/api/bookings";
import { formatRange } from "@/lib/format";
import type { Booking, TripScope } from "@/types/api";

const TABS: [TripScope, string, string][] = [
  ["upcoming", "Upcoming", "No trips booked… yet!"],
  ["past", "Past", "No past trips yet."],
  ["cancelled", "Cancelled", "No cancelled trips."],
];

type Loaded = { scope: TripScope; trips: Booking[] | null };

/** /trips: the guest's reservations, split into Upcoming, Past and Cancelled. */
export function TripsPage() {
  const [scope, setScope] = useState<TripScope>("upcoming");
  const [loaded, setLoaded] = useState<Loaded>({ scope: "upcoming", trips: null });

  useEffect(() => {
    let current = true;
    bookingsApi
      .list(scope)
      .then((trips) => current && setLoaded({ scope, trips }))
      .catch(() => current && setLoaded({ scope, trips: [] }));
    return () => {
      current = false;
    };
  }, [scope]);

  const trips = loaded.scope === scope ? loaded.trips : null;
  const empty = TABS.find(([key]) => key === scope)![2];

  return (
    <main className="mx-auto max-w-[1040px] px-6 py-10">
      <h1 className="mb-6 text-[32px] font-semibold">Trips</h1>
      <div role="tablist" className="mb-8 flex gap-2 border-b border-line">
        {TABS.map(([key, label]) => (
          <button
            key={key}
            role="tab"
            aria-selected={scope === key}
            onClick={() => setScope(key)}
            className={`-mb-px border-b-2 px-4 pb-3 text-sm font-medium transition ${scope === key ? "border-ink text-ink" : "border-transparent text-muted hover:text-ink"}`}
          >
            {label}
          </button>
        ))}
      </div>

      {trips === null && (
        <div className="space-y-4">
          {[0, 1].map((i) => (
            <Skeleton key={i} className="h-32 w-full rounded-[16px]" />
          ))}
        </div>
      )}
      {trips?.length === 0 && (
        <div className="py-8">
          <h2 className="text-xl font-semibold">{empty}</h2>
          {scope === "upcoming" && (
            <>
              <p className="mt-1 text-muted">Time to dust off your bags and start planning your next adventure.</p>
              <Link href="/homes" className="mt-5 inline-block rounded-control border border-ink px-5 py-3 font-semibold hover:bg-surface">
                Start searching
              </Link>
            </>
          )}
        </div>
      )}
      <ul className="space-y-4">
        {trips?.map((trip) => (
          <li key={trip.code}>
            <Link href={`/trips/${trip.code}`} className="flex gap-5 rounded-[16px] border border-line p-4 transition hover:shadow-card">
              {trip.listing.photo_url ? (
                // eslint-disable-next-line @next/next/no-img-element -- local media through the proxy
                <img src={trip.listing.photo_url} alt="" className="size-28 shrink-0 rounded-[12px] object-cover" />
              ) : (
                <div className="size-28 shrink-0 rounded-[12px] bg-surface" />
              )}
              <div className="min-w-0">
                <p className="truncate text-lg font-semibold">{trip.listing.title}</p>
                <p className="text-muted">{trip.listing.city}, {trip.listing.state} · Hosted by {trip.listing.host_first_name}</p>
                <p className="mt-2 font-medium">{formatRange(trip.check_in, trip.check_out)}</p>
                <p className="mt-1 text-sm text-muted">Confirmation code {trip.code}</p>
                {trip.can_review && <p className="mt-1 text-sm font-semibold text-rausch">Leave a review</p>}
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
