"use client";

import { Heart } from "lucide-react";
import type { MouseEvent } from "react";

import { useWishlist } from "@/store/wishlist";

/** Airbnb's save icon: a white outline over a translucent dark heart, red once saved. */
export function HeartButton({ listingId, className = "" }: { listingId: number; className?: string }) {
  const saved = useWishlist((s) => s.savedIds.has(listingId));
  const toggle = useWishlist((s) => s.toggle);

  const onClick = (event: MouseEvent) => {
    event.preventDefault(); // the card around it is a link
    event.stopPropagation();
    void toggle(listingId);
  };

  return (
    <button
      onClick={onClick}
      aria-label={saved ? "Remove from wishlist" : "Save to wishlist"}
      aria-pressed={saved}
      className={`grid size-8 place-items-center transition active:scale-90 ${className}`}
    >
      <Heart
        size={24}
        strokeWidth={2}
        className={saved ? "fill-rausch stroke-rausch" : "fill-black/50 stroke-white"}
      />
    </button>
  );
}
