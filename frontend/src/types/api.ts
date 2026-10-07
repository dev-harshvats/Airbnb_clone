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
