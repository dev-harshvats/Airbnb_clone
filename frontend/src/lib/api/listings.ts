import { api } from "@/lib/api/client";
import type { Destination, ListingCard, Page } from "@/types/api";

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
  destinations: () => api<Destination[]>("/destinations"),
};
