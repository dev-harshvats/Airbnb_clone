"use client";

import { Heart } from "lucide-react";
import { useState, type MouseEvent } from "react";

import { useWishlist } from "@/store/wishlist";

/** Airbnb's save icon: a white outline over a translucent dark heart, red once saved. */
export function HeartButton({ listingId, className = "" }: { listingId: number; className?: string }) {
  const saved = useWishlist((s) => s.savedIds.has(listingId));
  const toggle = useWishlist((s) => s.toggle);
  // Plays the pop only when the guest taps to save, not for hearts that are already red on page load.
  const [popping, setPopping] = useState(false);

  const onClick = (event: MouseEvent) => {
    event.preventDefault(); // the card around it is a link
    event.stopPropagation();
    if (!saved) setPopping(true);
    void toggle(listingId);
  };

  return (
    <button
      onClick={onClick}
      aria-label={saved ? "Remove from wishlist" : "Save to wishlist"}
      aria-pressed={saved}
      className={`grid size-8 place-items-center transition-transform duration-200 ease-airbnb hover:scale-110 active:scale-90 ${className}`}
    >
      <Heart
        size={24}
        strokeWidth={2}
        onAnimationEnd={() => setPopping(false)}
        className={`transition-colors duration-200 ${popping && saved ? "animate-heart" : ""} ${saved ? "fill-rausch stroke-rausch" : "fill-black/50 stroke-white"}`}
      />
    </button>
  );
}
