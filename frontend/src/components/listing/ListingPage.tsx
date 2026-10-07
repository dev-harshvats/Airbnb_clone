"use client";

import { Award, CalendarCheck, Heart, Share, Star } from "lucide-react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { AmenityIcon } from "@/components/listing/AmenityIcon";
import { BookingCard, type Trip } from "@/components/listing/BookingCard";
import { PhotoGrid } from "@/components/listing/PhotoGrid";
import { ReviewsSection } from "@/components/listing/ReviewsSection";
import { DateRangePanel } from "@/components/search/DateRangePanel";
import { Avatar } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Skeleton } from "@/components/ui/Skeleton";
import { toast } from "@/components/ui/Toast";
import { listingsApi } from "@/lib/api/listings";
import type { BookedRange } from "@/lib/availability";
import { formatRange, formatTime, nightsBetween } from "@/lib/format";
import { placeHeading, roomSummary } from "@/lib/listing";
import { parseSearch } from "@/lib/searchState";
import { useWishlist } from "@/store/wishlist";
import type { ListingDetail } from "@/types/api";

const LocationMap = dynamic(() => import("@/components/listing/LocationMap"), { ssr: false, loading: () => <Skeleton className="size-full" /> });

type Loaded = { id: string; state: "ready"; listing: ListingDetail; booked: BookedRange[] } | { id: string; state: "missing" };

const GROUP_TITLES: Record<string, string> = { essentials: "Essentials", features: "Features", location: "Location", safety: "Safety" };

function Section({ title, children, id }: { title: string; children: React.ReactNode; id?: string }) {
  return (
    <section id={id} className="border-t border-line-soft py-8">
      <h2 className="mb-5 text-[22px] font-semibold">{title}</h2>
      {children}
    </section>
  );
}

function TitleRow({ listing }: { listing: ListingDetail }) {
  const saved = useWishlist((s) => s.savedIds.has(listing.id));
  const toggle = useWishlist((s) => s.toggle);
  const share = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      toast.success("Link copied to clipboard");
    } catch {
      toast.error("Could not copy the link");
    }
  };
  const action = "flex items-center gap-2 rounded-control px-3 py-2 text-sm font-medium underline hover:bg-surface";
  return (
    <div className="flex items-start justify-between gap-4">
      <h1 className="text-[26px] font-semibold leading-tight">{listing.title}</h1>
      <div className="flex shrink-0">
        <button onClick={share} className={action}>
          <Share size={16} /> Share
        </button>
        <button onClick={() => void toggle(listing.id)} aria-pressed={saved} className={action}>
          <Heart size={16} className={saved ? "fill-rausch stroke-rausch" : ""} /> {saved ? "Saved" : "Save"}
        </button>
      </div>
    </div>
  );
}

function Amenities({ listing }: { listing: ListingDetail }) {
  const [open, setOpen] = useState(false);
  const groups = Object.entries(Object.groupBy(listing.amenities, (a) => a.group));
  return (
    <Section title="What this place offers">
      <ul className="grid gap-4 sm:grid-cols-2">
        {listing.amenities.slice(0, 10).map((amenity) => (
          <li key={amenity.key} className="flex items-center gap-4">
            <AmenityIcon iconKey={amenity.icon_key} /> {amenity.name}
          </li>
        ))}
      </ul>
      {listing.amenities.length > 10 && (
        <Button variant="secondary" size="lg" className="mt-8" onClick={() => setOpen(true)}>
          Show all {listing.amenities.length} amenities
        </Button>
      )}
      <Modal open={open} onClose={() => setOpen(false)} title="What this place offers" className="md:!max-w-[640px]">
        <div className="space-y-8 p-6">
          {groups.map(([group, items]) => (
            <div key={group}>
              <h3 className="mb-3 text-lg font-semibold">{GROUP_TITLES[group] ?? group}</h3>
              <ul className="divide-y divide-line-soft">
                {items?.map((amenity) => (
                  <li key={amenity.key} className="flex items-center gap-4 py-4">
                    <AmenityIcon iconKey={amenity.icon_key} /> {amenity.name}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </Modal>
    </Section>
  );
}

function Description({ text }: { text: string }) {
  const [open, setOpen] = useState(false);
  const long = text.length > 320;
  return (
    <section className="border-t border-line-soft py-8">
      <p className={`whitespace-pre-line leading-relaxed ${long && !open ? "line-clamp-4" : ""}`}>{text}</p>
      {long && (
        <button onClick={() => setOpen((v) => !v)} className="mt-3 font-semibold underline">
          {open ? "Show less" : "Show more"}
        </button>
      )}
    </section>
  );
}

function ListingBody({ listing, booked }: { listing: ListingDetail; booked: BookedRange[] }) {
  const params = useSearchParams();
  const initial = parseSearch(params);
  const [trip, setTrip] = useState<Trip>({
    checkIn: initial.checkIn,
    checkOut: initial.checkOut,
    guests: { adults: initial.adults || 1, children: initial.children, infants: initial.infants, pets: initial.pets },
  });
  const [datesOpen, setDatesOpen] = useState(false);
  const nights = trip.checkIn && trip.checkOut ? nightsBetween(trip.checkIn, trip.checkOut) : 0;
  const months = typeof window !== "undefined" && window.innerWidth < 768 ? 1 : 2;

  const card = (compact?: boolean) => (
    <BookingCard listing={listing} trip={trip} onTripChange={setTrip} onPickDates={() => setDatesOpen(true)} compact={compact} />
  );

  return (
    <main className="mx-auto max-w-[1120px] px-4 pb-28 pt-6 md:px-6 lg:pb-6">
      <TitleRow listing={listing} />
      <div className="mt-6">
        <PhotoGrid photos={listing.all_photos} title={listing.title} />
      </div>

      <div className="mt-8 grid gap-12 lg:grid-cols-[1fr_380px]">
        <div>
          <header className="pb-6">
            <h2 className="text-[22px] font-semibold">{placeHeading(listing)}, {listing.state}</h2>
            <p className="mt-1 text-muted">{roomSummary(listing)} · Up to {listing.max_guests} guests</p>
            {listing.rating_avg !== null ? (
              <a href="#reviews" className="mt-2 flex items-center gap-1 text-sm font-medium">
                <Star size={14} className="fill-ink" /> {listing.rating_avg.toFixed(2)} · <span className="underline">{listing.review_count} reviews</span>
              </a>
            ) : (
              <p className="mt-2 text-sm font-medium">★ New</p>
            )}
          </header>

          <div className="flex items-center gap-4 border-t border-line-soft py-6">
            <Avatar firstName={listing.host.first_name} lastName={listing.host.last_initial} url={listing.host.avatar_url} size={48} />
            <div>
              <p className="font-semibold">Hosted by {listing.host.first_name}</p>
              <p className="text-sm text-muted">
                {listing.host.is_superhost ? "Superhost · " : ""}Joined in {new Date(listing.host.joined_at).getFullYear()}
              </p>
            </div>
          </div>

          <ul className="space-y-5 border-t border-line-soft py-6">
            {listing.is_guest_favourite && (
              <li className="flex gap-4">
                <Award strokeWidth={1.5} />
                <span>
                  <strong className="block">Guest favourite</strong>
                  <span className="text-muted">One of the most loved homes on Airbnb, according to guests</span>
                </span>
              </li>
            )}
            <li className="flex gap-4">
              <CalendarCheck strokeWidth={1.5} />
              <span>
                <strong className="block">Check in from {formatTime(listing.check_in_time)}</strong>
                <span className="text-muted">Check out by {formatTime(listing.check_out_time)}</span>
              </span>
            </li>
          </ul>

          <Description text={listing.description} />
          <Amenities listing={listing} />

          <Section title={nights ? `${nights} night${nights === 1 ? "" : "s"} in ${listing.city}` : `Select check-in date`} id="calendar">
            <p className="-mt-3 mb-4 text-muted">
              {trip.checkIn && trip.checkOut ? formatRange(trip.checkIn, trip.checkOut) : "Add your travel dates for exact pricing"}
            </p>
            <div className="overflow-x-auto">
              <DateRangePanel
                checkIn={trip.checkIn}
                checkOut={trip.checkOut}
                booked={booked}
                months={months}
                onChange={(checkIn, checkOut) => setTrip((t) => ({ ...t, checkIn, checkOut }))}
              />
            </div>
            {(trip.checkIn || trip.checkOut) && (
              <button onClick={() => setTrip((t) => ({ ...t, checkIn: undefined, checkOut: undefined }))} className="mt-2 font-semibold underline">
                Clear dates
              </button>
            )}
          </Section>
        </div>

        <div className="hidden lg:block">{card()}</div>
      </div>

      <ReviewsSection listing={listing} />

      <Section title="Where you'll be">
        <p className="mb-4 font-medium">
          {listing.city}, {listing.state}, {listing.country}
        </p>
        <div className="h-[380px] overflow-hidden rounded-card bg-surface">
          <LocationMap latitude={listing.latitude} longitude={listing.longitude} />
        </div>
        <p className="mt-3 text-sm text-muted">The exact address is shared after you book.</p>
      </Section>

      <Section title="Meet your host">
        <div className="flex max-w-[560px] gap-6 rounded-[24px] bg-surface p-8 shadow-card">
          <div className="text-center">
            <Avatar firstName={listing.host.first_name} lastName={listing.host.last_initial} url={listing.host.avatar_url} size={96} />
            <p className="mt-3 text-xl font-semibold">{listing.host.first_name}</p>
            <p className="text-sm text-muted">{listing.host.is_superhost ? "Superhost" : "Host"}</p>
          </div>
          <p className="text-sm leading-relaxed">{listing.host.bio ?? `${listing.host.first_name} hosts in ${listing.city}.`}</p>
        </div>
      </Section>

      <Section title="Things to know">
        <div className="grid gap-8 md:grid-cols-3">
          <div>
            <h3 className="mb-2 font-semibold">House rules</h3>
            <p className="text-sm">Check-in after {formatTime(listing.check_in_time)}</p>
            <p className="text-sm">Checkout before {formatTime(listing.check_out_time)}</p>
            <p className="text-sm">{listing.max_guests} guests maximum</p>
            <p className="text-sm">{listing.pets_allowed ? "Pets allowed" : "No pets"}</p>
            {listing.house_rules && <p className="mt-2 whitespace-pre-line text-sm">{listing.house_rules}</p>}
          </div>
          <div>
            <h3 className="mb-2 font-semibold">Safety &amp; property</h3>
            {listing.amenities.filter((a) => a.group === "safety").map((a) => (
              <p key={a.key} className="text-sm">{a.name}</p>
            ))}
            {listing.amenities.every((a) => a.group !== "safety") && <p className="text-sm text-muted">No safety devices listed</p>}
          </div>
          <div>
            <h3 className="mb-2 font-semibold">Cancellation policy</h3>
            <p className="text-sm">Free cancellation until check-in. After that the booking can no longer be cancelled.</p>
            <p className="mt-2 text-sm text-muted">
              Stays of {listing.min_nights}–{listing.max_nights} nights.
            </p>
          </div>
        </div>
      </Section>

      <div className="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-white px-4 py-3 lg:hidden">{card(true)}</div>

      {datesOpen && (
        <Modal open onClose={() => setDatesOpen(false)} title="Select dates" className="md:!max-w-[780px]">
          <div className="flex justify-center overflow-x-auto p-6">
            <DateRangePanel
              checkIn={trip.checkIn}
              checkOut={trip.checkOut}
              booked={booked}
              months={months}
              onChange={(checkIn, checkOut) => setTrip((t) => ({ ...t, checkIn, checkOut }))}
            />
          </div>
          <footer className="sticky bottom-0 flex items-center justify-between border-t border-line-soft bg-white px-6 py-4">
            <button
              onClick={() => setTrip((t) => ({ ...t, checkIn: undefined, checkOut: undefined }))}
              className="font-semibold underline"
            >
              Clear dates
            </button>
            <Button variant="dark" size="lg" onClick={() => setDatesOpen(false)}>
              Save
            </Button>
          </footer>
        </Modal>
      )}
    </main>
  );
}

/** /rooms/{id}: everything a guest needs to decide, with the reservation card beside it. */
export function ListingPage({ id }: { id: string }) {
  const [loaded, setLoaded] = useState<Loaded | null>(null);

  useEffect(() => {
    let current = true;
    Promise.all([listingsApi.detail(id), listingsApi.availability(id)])
      .then(([listing, booked]) => current && setLoaded({ id, state: "ready", listing, booked }))
      .catch(() => current && setLoaded({ id, state: "missing" }));
    return () => {
      current = false;
    };
  }, [id]);

  if (!loaded || loaded.id !== id) {
    return (
      <main className="mx-auto max-w-[1120px] space-y-4 px-4 py-8 md:px-6">
        <Skeleton className="h-8 w-2/3" />
        <Skeleton className="aspect-[2/1] max-h-[420px] w-full rounded-card" />
      </main>
    );
  }
  if (loaded.state === "missing") {
    return (
      <main className="mx-auto flex max-w-[560px] flex-col items-center gap-4 px-6 py-24 text-center">
        <h1 className="text-[28px] font-bold">That place isn&apos;t available</h1>
        <p className="text-muted">It may have been removed. Browse other stays instead.</p>
        <Link href="/homes">
          <Button size="lg">Keep exploring</Button>
        </Link>
      </main>
    );
  }
  return <ListingBody key={loaded.id} listing={loaded.listing} booked={loaded.booked} />;
}
