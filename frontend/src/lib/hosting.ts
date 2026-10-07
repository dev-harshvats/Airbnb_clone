import type { ListingDetail } from "@/types/api";

/** The steps of the create-listing wizard, in order (the last one publishes). */
export const WIZARD_STEPS = [
  "about",
  "property-type",
  "place-type",
  "location",
  "floor-plan",
  "amenities",
  "photos",
  "title",
  "description",
  "category",
  "price",
  "rules",
  "review",
] as const;
export type StepKey = (typeof WIZARD_STEPS)[number];

export const MIN_PHOTOS = 5;
export const MIN_PRICE = 500;
export const MAX_TITLE = 50;
export const MAX_DESCRIPTION = 500;

/** What a host fills in. Money is whole rupees; coordinates start at the chosen city. */
export type ListingDraft = {
  propertyType: string;
  placeType: "entire" | "private_room" | "shared_room";
  addressLine: string;
  city: string;
  state: string;
  postalCode: string;
  latitude: number;
  longitude: number;
  maxGuests: number;
  bedrooms: number;
  beds: number;
  bathrooms: number;
  amenityIds: number[];
  categoryId?: number;
  title: string;
  description: string;
  pricePerNight?: number;
  cleaningFee: number;
  minNights: number;
  maxNights: number;
  houseRules: string;
  petsAllowed: boolean;
};

export const emptyDraft = (): ListingDraft => ({
  propertyType: "",
  placeType: "entire",
  addressLine: "",
  city: "",
  state: "",
  postalCode: "",
  latitude: 20.5937,
  longitude: 78.9629,
  maxGuests: 4,
  bedrooms: 1,
  beds: 1,
  bathrooms: 1,
  amenityIds: [],
  title: "",
  description: "",
  cleaningFee: 0,
  minNights: 1,
  maxNights: 30,
  houseRules: "",
  petsAllowed: false,
});

/** Why a step can't be left yet (null when it is fine). `photoCount` comes from the server. */
export function validateStep(step: StepKey, draft: ListingDraft, photoCount: number): string | null {
  switch (step) {
    case "property-type":
      return draft.propertyType ? null : "Choose what kind of place this is.";
    case "location":
      if (!draft.city || !draft.addressLine.trim()) return "Choose a city and enter the street address.";
      return draft.postalCode.trim().length >= 3 ? null : "Enter the postal code.";
    case "floor-plan":
      return draft.maxGuests >= 1 ? null : "A place needs room for at least one guest.";
    case "photos":
      return photoCount >= MIN_PHOTOS ? null : `Add at least ${MIN_PHOTOS} photos (you have ${photoCount}).`;
    case "title":
      if (!draft.title.trim()) return "Give your place a title.";
      return draft.title.length <= MAX_TITLE ? null : `Titles can be at most ${MAX_TITLE} characters.`;
    case "description":
      if (!draft.description.trim()) return "Describe your place.";
      return draft.description.length <= MAX_DESCRIPTION ? null : `Descriptions can be at most ${MAX_DESCRIPTION} characters.`;
    case "category":
      return draft.categoryId ? null : "Pick the category that describes your place best.";
    case "price":
      return (draft.pricePerNight ?? 0) >= MIN_PRICE ? null : `Set a nightly price of at least ₹${MIN_PRICE}.`;
    case "rules":
      if (draft.minNights < 1) return "The minimum stay is at least one night.";
      return draft.maxNights >= draft.minNights ? null : "The maximum stay can't be shorter than the minimum.";
    default:
      return null;
  }
}

/** The first step (in wizard order) that still stops the listing from being published. */
export function firstInvalidStep(draft: ListingDraft, photoCount: number): StepKey | null {
  return WIZARD_STEPS.find((step) => validateStep(step, draft, photoCount) !== null) ?? null;
}

/** The body for POST /hosting/listings (and PATCH, which accepts the same fields). */
/** `fallbackCategoryId` stands in until the host reaches the category step (the API needs one). */
export function toPayload(draft: ListingDraft, fallbackCategoryId?: number) {
  return {
    category_id: draft.categoryId ?? fallbackCategoryId,
    title: draft.title.trim() || "Untitled listing",
    description: draft.description.trim(),
    property_type: draft.propertyType || "house",
    place_type: draft.placeType,
    address_line: draft.addressLine.trim() || "Address to be added",
    city: draft.city || "Goa",
    state: draft.state || "Goa",
    postal_code: draft.postalCode.trim() || "000000",
    latitude: draft.latitude,
    longitude: draft.longitude,
    price_per_night: draft.pricePerNight ?? MIN_PRICE,
    cleaning_fee: draft.cleaningFee,
    min_nights: draft.minNights,
    max_nights: draft.maxNights,
    max_guests: draft.maxGuests,
    bedrooms: draft.bedrooms,
    beds: draft.beds,
    bathrooms: draft.bathrooms,
    pets_allowed: draft.petsAllowed,
    house_rules: draft.houseRules.trim(),
    amenity_ids: draft.amenityIds,
  };
}

/** Rebuild a draft from a saved listing, for the editor and for resuming a wizard. */
export function draftFromListing(listing: ListingDetail): ListingDraft {
  return {
    propertyType: listing.property_type,
    placeType: listing.place_type,
    addressLine: listing.address_line ?? "",
    city: listing.city,
    state: listing.state,
    postalCode: listing.postal_code ?? "",
    latitude: listing.latitude,
    longitude: listing.longitude,
    maxGuests: listing.max_guests,
    bedrooms: listing.bedrooms,
    beds: listing.beds,
    bathrooms: listing.bathrooms,
    amenityIds: listing.amenities.map((a) => a.id),
    categoryId: listing.category.id,
    title: listing.title,
    description: listing.description,
    pricePerNight: listing.price_per_night,
    cleaningFee: listing.cleaning_fee,
    minNights: listing.min_nights,
    maxNights: listing.max_nights,
    houseRules: listing.house_rules,
    petsAllowed: listing.pets_allowed,
  };
}
