"use client";

import { ChevronLeft, ChevronRight, Star } from "lucide-react";
import Link from "next/link";
import { useState, type MouseEvent } from "react";

import { HeartButton } from "@/components/listing/HeartButton";
import { formatRange } from "@/lib/format";
import { placeHeading, priceCaption, roomSummary } from "@/lib/listing";
import type { ListingCard as Listing } from "@/types/api";

type ListingCardProps = {
  listing: Listing;
  /** "row" is the compact card used in home carousels; "grid" is the richer search-result card. */
  variant?: "row" | "grid";
  /** Searched dates: shown on the card, and used to price it as "₹X for N nights". */
  checkIn?: string;
  checkOut?: string;
  nights?: number;
};

function Rating({ listing, withCount }: { listing: Listing; withCount?: boolean }) {
  if (listing.rating_avg === null) return <span className="flex items-center gap-1">★ New</span>;
  return (
    <span className="flex shrink-0 items-center gap-1">
      <Star size={12} className="fill-ink" />
      {listing.rating_avg.toFixed(withCount ? 2 : 1)}
      {withCount && <span className="text-muted">({listing.review_count})</span>}
    </span>
  );
}

function PhotoArea({ listing, carousel }: { listing: Listing; carousel: boolean }) {
  const [index, setIndex] = useState(0);
  const photos = listing.photos;
  const go = (step: number) => (event: MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    setIndex((i) => (i + step + photos.length) % photos.length);
  };

  return (
    <div className="group relative aspect-square overflow-hidden rounded-[14px] bg-surface">
      {photos.length > 0 && (
        // eslint-disable-next-line @next/next/no-img-element -- already resized WebP renditions
        <img
          src={photos[carousel ? index : 0].card_url}
          alt={listing.title}
          loading="lazy"
          className="size-full object-cover transition-transform duration-300"
        />
      )}
      {listing.is_guest_favourite && (
        <span className="absolute left-3 top-3 rounded-full bg-white px-2.5 py-1 text-[13px] font-semibold shadow-pill">
          Guest favourite
        </span>
      )}
      <HeartButton listingId={listing.id} className="absolute right-3 top-3" />

      {carousel && photos.length > 1 && (
        <>
          <button
            onClick={go(-1)}
            aria-label="Previous photo"
            className="absolute left-2 top-1/2 hidden size-8 -translate-y-1/2 place-items-center rounded-full bg-white/90 shadow-pill transition hover:scale-105 hover:bg-white group-hover:grid"
          >
            <ChevronLeft size={16} />
          </button>
          <button
            onClick={go(1)}
            aria-label="Next photo"
            className="absolute right-2 top-1/2 hidden size-8 -translate-y-1/2 place-items-center rounded-full bg-white/90 shadow-pill transition hover:scale-105 hover:bg-white group-hover:grid"
          >
            <ChevronRight size={16} />
          </button>
          <div className="absolute inset-x-0 bottom-3 flex justify-center gap-1">
            {photos.map((photo, i) => (
              <span
                key={photo.url}
                className={`size-1.5 rounded-full ${i === index ? "bg-white" : "bg-white/60"}`}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

/** A listing as Airbnb shows it: photo with badge and heart, then a few lines of caption. */
export function ListingCard({ listing, variant = "row", checkIn, checkOut, nights }: ListingCardProps) {
  const price = priceCaption(listing, nights);
  const href = `/rooms/${listing.id}${checkIn && checkOut ? `?check_in=${checkIn}&check_out=${checkOut}` : ""}`;

  return (
    <Link href={href} className="block">
      <PhotoArea listing={listing} carousel={variant === "grid"} />
      {variant === "grid" ? (
        <div className="mt-3 text-[15px] leading-snug">
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-semibold">{placeHeading(listing)}</h3>
            <Rating listing={listing} withCount />
          </div>
          <p className="truncate text-muted">{listing.title}</p>
          <p className="text-muted">{roomSummary(listing)}</p>
          {checkIn && checkOut && <p className="text-muted">{formatRange(checkIn, checkOut)}</p>}
          <p className="mt-1">
            <span className="font-semibold underline">{price.amount}</span> {price.suffix}
          </p>
        </div>
      ) : (
        <div className="mt-2.5 text-sm leading-snug">
          <h3 className="truncate font-semibold">{placeHeading(listing)}</h3>
          <p className="flex items-center gap-1 text-muted">
            <span>
              {price.amount} {price.suffix}
            </span>
            <span aria-hidden>·</span>
            <Rating listing={listing} />
          </p>
        </div>
      )}
    </Link>
  );
}
