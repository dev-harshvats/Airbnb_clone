import { api } from "@/lib/api/client";
import type { BookedRange } from "@/lib/availability";
import type { Amenity, Destination, ListingCard, ListingDetail, Page, PriceHistogram, Quote, Review } from "@/types/api";

/** The filters GET /listings understands (all optional). */
export type ListingQuery = {
  location?: string;
  check_in?: string;
  check_out?: string;
  adults?: number;
  children?: number;
  pets?: number;
  min_price?: number;
  max_price?: number;
  place_type?: string;
  property_types?: string[];
  bedrooms?: number;
  beds?: number;
  bathrooms?: number;
  amenities?: string[];
  category?: string;
  superhost?: boolean;
  guest_favourite?: boolean;
  sort?: "recommended" | "price_asc" | "price_desc" | "rating" | "newest";
  page?: number;
  page_size?: number;
};

export const listingsApi = {
  search: (query: ListingQuery) => api<Page<ListingCard>>("/listings", { query }),
  priceHistogram: (query: ListingQuery) => api<PriceHistogram>("/listings/price-histogram", { query }),
  amenities: () => api<Amenity[]>("/amenities"),
  detail: (id: number | string) => api<ListingDetail>(`/listings/${id}`),
  availability: (id: number | string) => api<{ booked: BookedRange[] }>(`/listings/${id}/availability`).then((r) => r.booked),
  quote: (id: number | string, checkIn: string, checkOut: string) =>
    api<Quote>(`/listings/${id}/quote`, { method: "POST", body: { check_in: checkIn, check_out: checkOut } }),
  reviews: (id: number | string, page: number, pageSize = 6) =>
    api<Page<Review>>(`/listings/${id}/reviews`, { query: { page, page_size: pageSize } }),
  destinations: () => api<Destination[]>("/destinations"),
};
