import { formatINR } from "@/lib/format";
import type { ListingCard } from "@/types/api";

const PROPERTY_LABELS: Record<string, string> = {
  house: "Home",
  flat: "Flat",
  guest_house: "Guest house",
  hotel: "Hotel",
  villa: "Villa",
  cottage: "Cottage",
  houseboat: "Houseboat",
  cabin: "Cabin",
  farm_stay: "Farm stay",
  treehouse: "Treehouse",
  heritage_home: "Heritage home",
  tent: "Tent",
};

/** "Flat in Anjuna": what Airbnb shows above a listing's own title. */
export function placeHeading(listing: Pick<ListingCard, "property_type" | "place_type" | "city">): string {
  const base = PROPERTY_LABELS[listing.property_type] ?? "Home";
  const kind = listing.place_type === "private_room" ? `Room in ${base.toLowerCase()}` : base;
  return `${kind} in ${listing.city}`;
}

export const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;

/** "₹10,446 for 2 nights" when dates were searched, else "₹4,500 night". */
export function priceCaption(listing: Pick<ListingCard, "price_per_night" | "total_for_dates">, nights?: number) {
  if (listing.total_for_dates !== null && nights) {
    return { amount: formatINR(listing.total_for_dates), suffix: `for ${plural(nights, "night")}` };
  }
  return { amount: formatINR(listing.price_per_night), suffix: "night" };
}

/** "3 bedrooms · 3 beds · 2 bathrooms" */
export function roomSummary(l: Pick<ListingCard, "bedrooms" | "beds" | "bathrooms">): string {
  const bedrooms = l.bedrooms === 0 ? "Studio" : plural(l.bedrooms, "bedroom");
  return [bedrooms, plural(l.beds, "bed"), plural(l.bathrooms, "bathroom")].join(" · ");
}
