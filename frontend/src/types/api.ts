/** Response shapes of the backend API (mirrors backend/app/schemas). */

export type ApiErrorBody = { detail: string; code: string };

export type User = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  avatar_url: string | null;
  is_host: boolean;
  is_superhost: boolean;
  created_at: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: "bearer";
  expires_in: number; // seconds until the access token expires
  user: User;
};

export type Category = {
  id: number;
  slug: string;
  label: string;
  icon_key: string;
};

export type Amenity = { id: number; key: string; name: string; icon_key: string; group: string };

/** Listing counts per equal-width price band between min_price and max_price. */
export type PriceHistogram = { min_price: number; max_price: number; buckets: number[] };

export type PhotoRef = { url: string; card_url: string };

export type ListingCard = {
  id: number;
  title: string;
  city: string;
  state: string;
  property_type: string;
  place_type: "entire" | "private_room" | "shared_room";
  price_per_night: number;
  cleaning_fee: number;
  max_guests: number;
  bedrooms: number;
  beds: number;
  bathrooms: number;
  rating_avg: number | null;
  review_count: number;
  is_guest_favourite: boolean;
  host_is_superhost: boolean;
  photos: PhotoRef[];
  latitude: number;
  longitude: number;
  /** Total for the searched dates, fees and taxes included (only when dates were searched). */
  total_for_dates: number | null;
};

export type Page<T> = { items: T[]; page: number; page_size: number; total: number };

export type Destination = {
  city: string;
  state: string;
  listing_count: number;
  cover_url: string | null;
};

export type ExperienceCategory = "food" | "heritage" | "adventure" | "wellness" | "nature" | "arts";
export type ServiceType = "photography" | "chefs" | "training" | "makeup" | "hair" | "massage";

export type ExperienceCard = {
  id: number;
  title: string;
  category: ExperienceCategory;
  city: string;
  state: string;
  start_time: string; // HH:MM
  duration_minutes: number;
  price_per_guest: number;
  rating_avg: number | null;
  review_count: number;
  photos: PhotoRef[];
};

export type HostProfile = {
  id: number;
  first_name: string;
  last_initial: string;
  avatar_url: string | null;
  bio: string | null;
  is_superhost: boolean;
  joined_at: string;
};

export type PhotoItem = PhotoRef & { id: number; caption: string | null; position: number };

export type ExperienceDetail = ExperienceCard & {
  description: string;
  max_guests: number;
  latitude: number;
  longitude: number;
  all_photos: PhotoItem[];
  host: HostProfile;
};

export type ServiceCard = {
  id: number;
  title: string;
  service_type: ServiceType;
  city: string;
  state: string;
  price_from: number;
  price_unit: string;
  is_popular: boolean;
  rating_avg: number | null;
  review_count: number;
  photos: PhotoRef[];
};

export type ServiceDetail = ServiceCard & { description: string; all_photos: PhotoItem[]; host: HostProfile };

export type ServiceTypeSummary = { key: ServiceType; label: string; count: number };

export type RatingBreakdown = {
  cleanliness: number | null;
  accuracy: number | null;
  check_in: number | null;
  communication: number | null;
  location: number | null;
  value: number | null;
};

export type ListingDetail = ListingCard & {
  status: "draft" | "active" | "inactive";
  description: string;
  country: string;
  category: Category;
  amenities: Amenity[];
  all_photos: PhotoItem[];
  host: HostProfile;
  house_rules: string;
  min_nights: number;
  max_nights: number;
  pets_allowed: boolean;
  check_in_time: string;
  check_out_time: string;
  rating_breakdown: RatingBreakdown;
  rating_distribution: Record<string, number>;
  /** Only returned to the listing's own host. */
  address_line: string | null;
  postal_code: string | null;
};

export type Review = {
  id: number;
  author_first_name: string;
  author_last_initial: string;
  author_avatar_url: string | null;
  rating: number;
  cleanliness: number;
  accuracy: number;
  check_in: number;
  communication: number;
  location: number;
  value: number;
  comment: string;
  created_at: string;
};

export type Quote = {
  nightly_rate: number;
  nights: number;
  subtotal: number;
  cleaning_fee: number;
  service_fee: number;
  taxes: number;
  total: number;
};

export type PaymentMethod = "card" | "upi";

export type Booking = Quote & {
  code: string;
  status: "confirmed" | "cancelled";
  listing: { id: number; title: string; city: string; state: string; photo_url: string | null; host_first_name: string };
  check_in: string;
  check_out: string;
  adults: number;
  children: number;
  infants: number;
  pets: number;
  payment_method: PaymentMethod;
  created_at: string;
  cancelled_at: string | null;
  can_cancel: boolean;
  can_review: boolean;
  has_review: boolean;
};

export type TripScope = "upcoming" | "past" | "cancelled";

export type HostListing = {
  id: number;
  title: string;
  status: "draft" | "active" | "inactive";
  city: string;
  state: string;
  price_per_night: number;
  photo_url: string | null;
  rating_avg: number | null;
  review_count: number;
  upcoming_reservations: number;
};

export type Reservation = {
  code: string;
  status: "confirmed" | "cancelled";
  listing_id: number;
  listing_title: string;
  guest_first_name: string;
  guest_last_initial: string;
  guest_avatar_url: string | null;
  check_in: string;
  check_out: string;
  nights: number;
  guests: number;
  total: number;
  payout: number;
};

export type HostStats = {
  active_listings: number;
  upcoming_reservations: number;
  earnings_this_month: number;
  earnings_total: number;
};
