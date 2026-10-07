import type { ListingQuery } from "@/lib/api/listings";

/** Everything a stays search can be narrowed by. The URL is the source of truth; this is its typed view. */
export type SearchState = {
  checkIn?: string;
  checkOut?: string;
  adults: number;
  children: number;
  infants: number;
  pets: number;
  minPrice?: number;
  maxPrice?: number;
  placeType?: string;
  propertyTypes: string[];
  bedrooms?: number;
  beds?: number;
  bathrooms?: number;
  amenities: string[];
  category?: string;
  superhost: boolean;
  guestFavourite: boolean;
  sort?: NonNullable<ListingQuery["sort"]>;
};

const positive = (value: string | null) => {
  const n = value ? Number(value) : NaN;
  return Number.isFinite(n) && n > 0 ? n : undefined;
};

export function parseSearch(params: URLSearchParams): SearchState {
  return {
    checkIn: params.get("check_in") || undefined,
    checkOut: params.get("check_out") || undefined,
    adults: positive(params.get("adults")) ?? 0,
    children: positive(params.get("children")) ?? 0,
    infants: positive(params.get("infants")) ?? 0,
    pets: positive(params.get("pets")) ?? 0,
    minPrice: positive(params.get("min_price")),
    maxPrice: positive(params.get("max_price")),
    placeType: params.get("place_type") || undefined,
    propertyTypes: params.getAll("property_types"),
    bedrooms: positive(params.get("bedrooms")),
    beds: positive(params.get("beds")),
    bathrooms: positive(params.get("bathrooms")),
    amenities: params.getAll("amenities"),
    category: params.get("category") || undefined,
    superhost: params.get("superhost") === "true",
    guestFavourite: params.get("guest_favourite") === "true",
    sort: (params.get("sort") as SearchState["sort"]) || undefined,
  };
}

/** The inverse of parseSearch: only what is actually set ends up in the URL. */
export function toSearchParams(state: SearchState): URLSearchParams {
  const params = new URLSearchParams();
  const set = (key: string, value: string | number | undefined) => value !== undefined && value !== "" && params.set(key, String(value));
  set("check_in", state.checkIn);
  set("check_out", state.checkOut);
  for (const key of ["adults", "children", "infants", "pets"] as const) set(key, state[key] || undefined);
  set("min_price", state.minPrice);
  set("max_price", state.maxPrice);
  set("place_type", state.placeType);
  state.propertyTypes.forEach((value) => params.append("property_types", value));
  set("bedrooms", state.bedrooms);
  set("beds", state.beds);
  set("bathrooms", state.bathrooms);
  state.amenities.forEach((value) => params.append("amenities", value));
  set("category", state.category);
  if (state.superhost) params.set("superhost", "true");
  if (state.guestFavourite) params.set("guest_favourite", "true");
  set("sort", state.sort);
  return params;
}

/** How many filters the Filters button should badge. Dates, guests and category belong to the search bar. */
export function activeFilterCount(state: SearchState): number {
  return (
    (state.minPrice !== undefined || state.maxPrice !== undefined ? 1 : 0) +
    (state.placeType ? 1 : 0) +
    state.propertyTypes.length +
    [state.bedrooms, state.beds, state.bathrooms].filter((n) => n !== undefined).length +
    state.amenities.length +
    (state.superhost ? 1 : 0) +
    (state.guestFavourite ? 1 : 0)
  );
}

export function toListingQuery(state: SearchState, place: string | null): ListingQuery {
  return {
    location: place ?? undefined,
    check_in: state.checkIn,
    check_out: state.checkOut,
    adults: state.adults || undefined,
    children: state.children || undefined,
    pets: state.pets || undefined,
    min_price: state.minPrice,
    max_price: state.maxPrice,
    place_type: state.placeType,
    property_types: state.propertyTypes,
    bedrooms: state.bedrooms,
    beds: state.beds,
    bathrooms: state.bathrooms,
    amenities: state.amenities,
    category: state.category,
    superhost: state.superhost || undefined,
    guest_favourite: state.guestFavourite || undefined,
    sort: state.sort,
  };
}

export function withoutPaging(params: URLSearchParams): URLSearchParams {
  const copy = new URLSearchParams(params);
  copy.delete("page");
  return copy;
}
