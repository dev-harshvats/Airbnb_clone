"use client";

import {
  Building2, Castle, DoorOpen, Home, Hotel, Landmark, Ship, Tent, Tractor, TreeDeciduous, TreePine, Warehouse, type LucideIcon,
} from "lucide-react";
import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

import { AmenityIcon } from "@/components/listing/AmenityIcon";
import { PhotoUploader } from "@/components/host/PhotoUploader";
import { Skeleton } from "@/components/ui/Skeleton";
import { Stepper } from "@/components/ui/Stepper";
import { listingsApi } from "@/lib/api/listings";
import { CITIES } from "@/lib/cities";
import { formatINR } from "@/lib/format";
import { MAX_DESCRIPTION, MAX_TITLE, MIN_PRICE, type ListingDraft, type StepKey } from "@/lib/hosting";
import type { Amenity, Category, PhotoItem } from "@/types/api";

const PinPicker = dynamic(() => import("@/components/host/PinPicker"), { ssr: false, loading: () => <Skeleton className="size-full" /> });

const PROPERTY_TYPES: [key: string, label: string, Icon: LucideIcon][] = [
  ["house", "House", Home], ["flat", "Flat", Building2], ["guest_house", "Guest house", DoorOpen], ["hotel", "Hotel", Hotel],
  ["villa", "Villa", Castle], ["cottage", "Cottage", Warehouse], ["houseboat", "Houseboat", Ship], ["cabin", "Cabin", TreePine],
  ["farm_stay", "Farm stay", Tractor], ["treehouse", "Treehouse", TreeDeciduous], ["heritage_home", "Heritage home", Landmark], ["tent", "Tent", Tent],
];

const PLACE_TYPES: [key: ListingDraft["placeType"], title: string, hint: string][] = [
  ["entire", "An entire place", "Guests have the whole place to themselves."],
  ["private_room", "A room", "Guests have their own room in a home, plus access to shared spaces."],
  ["shared_room", "A shared room", "Guests sleep in a room or common area that may be shared with you or others."],
];

const GROUPS: Record<string, string> = { essentials: "Essentials", features: "Standout features", location: "Location", safety: "Safety items" };

/** Matches the server's fee, to give hosts a rough idea of the guest price. Real prices come from quotes. */
const SERVICE_FEE_RATE = 0.14;

export type StepContext = {
  categories: Category[];
  /** Photos only exist once the draft has been saved to the server. */
  listingId: number | null;
  photos: PhotoItem[];
  onPhotosChange: (photos: PhotoItem[]) => void;
};

type Props = {
  step: StepKey;
  draft: ListingDraft;
  patch: (changes: Partial<ListingDraft>) => void;
  ctx: StepContext;
};

const inputClass = "w-full rounded-control border border-muted px-3 py-3 text-base focus:border-ink focus:outline-none focus:ring-1 focus:ring-ink";

function Row({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b border-line-soft py-5">
      <div>
        <p className="text-lg">{title}</p>
        {hint && <p className="text-sm text-muted">{hint}</p>}
      </div>
      {children}
    </div>
  );
}

function Tile({ selected, onClick, children, className = "" }: { selected: boolean; onClick: () => void; children: React.ReactNode; className?: string }) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onClick}
      className={`rounded-[12px] border p-5 text-left transition ${selected ? "border-2 border-ink bg-surface" : "border-line hover:border-ink"} ${className}`}
    >
      {children}
    </button>
  );
}

function Amenities({ draft, patch }: Pick<Props, "draft" | "patch">) {
  const [amenities, setAmenities] = useState<Amenity[]>([]);
  useEffect(() => {
    listingsApi.amenities().then(setAmenities).catch(() => setAmenities([]));
  }, []);
  const toggle = (id: number) => patch({ amenityIds: draft.amenityIds.includes(id) ? draft.amenityIds.filter((a) => a !== id) : [...draft.amenityIds, id] });
  const groups = Object.entries(Object.groupBy(amenities, (a) => a.group));
  if (amenities.length === 0) return <Skeleton className="h-48 w-full" />;
  return (
    <div className="space-y-8">
      {groups.map(([group, items]) => (
        <div key={group}>
          <h3 className="mb-3 text-lg font-semibold">{GROUPS[group] ?? group}</h3>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {items?.map((amenity) => (
              <Tile key={amenity.id} selected={draft.amenityIds.includes(amenity.id)} onClick={() => toggle(amenity.id)} className="flex flex-col gap-3">
                <AmenityIcon iconKey={amenity.icon_key} size={28} />
                <span className="text-sm font-medium">{amenity.name}</span>
              </Tile>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

/** One screen of the listing form. The create wizard and the listing editor both render these. */
export function StepBody({ step, draft, patch, ctx }: Props) {
  switch (step) {
    case "about":
      return (
        <div className="space-y-6">
          {[
            ["1", "Tell us about your place", "Share some basic info, like where it is and how many guests can stay."],
            ["2", "Make it stand out", "Add 5 or more photos plus a title and description. We'll help you out."],
            ["3", "Finish up and publish", "Choose a starting price, set your rules, and publish your listing."],
          ].map(([n, title, text]) => (
            <div key={n} className="flex gap-6 border-b border-line-soft pb-6">
              <span className="text-2xl font-semibold">{n}</span>
              <div>
                <h3 className="text-2xl font-semibold">{title}</h3>
                <p className="mt-1 text-muted">{text}</p>
              </div>
            </div>
          ))}
        </div>
      );

    case "property-type":
      return (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {PROPERTY_TYPES.map(([key, label, Icon]) => (
            <Tile key={key} selected={draft.propertyType === key} onClick={() => patch({ propertyType: key })} className="flex flex-col gap-4">
              <Icon size={30} strokeWidth={1.5} />
              <span className="font-medium">{label}</span>
            </Tile>
          ))}
        </div>
      );

    case "place-type":
      return (
        <div className="space-y-3">
          {PLACE_TYPES.map(([key, title, hint]) => (
            <Tile key={key} selected={draft.placeType === key} onClick={() => patch({ placeType: key })} className="block w-full">
              <p className="text-lg font-semibold">{title}</p>
              <p className="text-sm text-muted">{hint}</p>
            </Tile>
          ))}
        </div>
      );

    case "location": {
      const chosen = CITIES.some((c) => c.city === draft.city);
      return (
        <div className="space-y-4">
          <label className="block">
            <span className="mb-1 block text-sm font-medium">City</span>
            <select
              value={draft.city}
              onChange={(event) => {
                const city = CITIES.find((c) => c.city === event.target.value);
                if (city) patch({ city: city.city, state: city.state, latitude: city.latitude, longitude: city.longitude, postalCode: draft.postalCode || city.postalCode });
              }}
              className={inputClass}
            >
              <option value="">Choose a city</option>
              {CITIES.map((c) => (
                <option key={c.city} value={c.city}>{c.city}, {c.state}</option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="mb-1 block text-sm font-medium">Street address</span>
            <input value={draft.addressLine} onChange={(event) => patch({ addressLine: event.target.value })} maxLength={200} className={inputClass} placeholder="House no., street, area" />
          </label>
          <label className="block">
            <span className="mb-1 block text-sm font-medium">Postal code</span>
            <input value={draft.postalCode} onChange={(event) => patch({ postalCode: event.target.value })} maxLength={12} inputMode="numeric" className={inputClass} />
          </label>
          <div>
            <p className="mb-2 text-sm font-medium">Drag the pin to your exact location</p>
            <div className="h-[320px] overflow-hidden rounded-card bg-surface">
              <PinPicker latitude={draft.latitude} longitude={draft.longitude} zoom={chosen ? 14 : 5} onChange={(latitude, longitude) => patch({ latitude, longitude })} />
            </div>
            <p className="mt-2 text-xs text-muted">Guests only see the area until they book.</p>
          </div>
        </div>
      );
    }

    case "floor-plan":
      return (
        <div>
          <Row title="Guests"><Stepper label="guests" value={draft.maxGuests} min={1} max={16} onChange={(maxGuests) => patch({ maxGuests })} /></Row>
          <Row title="Bedrooms"><Stepper label="bedrooms" value={draft.bedrooms} min={0} max={50} onChange={(bedrooms) => patch({ bedrooms })} /></Row>
          <Row title="Beds"><Stepper label="beds" value={draft.beds} min={0} max={50} onChange={(beds) => patch({ beds })} /></Row>
          <Row title="Bathrooms" hint="Half baths count as 0.5">
            <Stepper label="bathrooms" value={draft.bathrooms} min={0} max={50} step={0.5} onChange={(bathrooms) => patch({ bathrooms })} />
          </Row>
        </div>
      );

    case "amenities":
      return <Amenities draft={draft} patch={patch} />;

    case "photos":
      return ctx.listingId ? (
        <PhotoUploader listingId={ctx.listingId} photos={ctx.photos} onChange={ctx.onPhotosChange} />
      ) : (
        <Skeleton className="h-48 w-full" />
      );

    case "title":
      return (
        <div>
          <textarea
            aria-label="Title"
            value={draft.title}
            onChange={(event) => patch({ title: event.target.value })}
            rows={3}
            className={`${inputClass} text-2xl font-semibold`}
            placeholder="Sunny villa a short walk from the beach"
          />
          <p className={`mt-2 text-sm ${draft.title.length > MAX_TITLE ? "text-[#c13515]" : "text-muted"}`}>{draft.title.length}/{MAX_TITLE}</p>
        </div>
      );

    case "description":
      return (
        <div>
          <textarea
            aria-label="Description"
            value={draft.description}
            onChange={(event) => patch({ description: event.target.value })}
            rows={8}
            className={inputClass}
            placeholder="You'll fall in love with this place…"
          />
          <p className={`mt-2 text-sm ${draft.description.length > MAX_DESCRIPTION ? "text-[#c13515]" : "text-muted"}`}>{draft.description.length}/{MAX_DESCRIPTION}</p>
        </div>
      );

    case "category":
      return ctx.categories.length === 0 ? (
        <Skeleton className="h-48 w-full" />
      ) : (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {ctx.categories.map((category) => (
            <Tile key={category.id} selected={draft.categoryId === category.id} onClick={() => patch({ categoryId: category.id })}>
              <span className="font-medium">{category.label}</span>
            </Tile>
          ))}
        </div>
      );

    case "price": {
      const price = draft.pricePerNight ?? 0;
      return (
        <div className="text-center">
          <div className="flex items-center justify-center gap-2 text-[64px] font-bold leading-none">
            <span>₹</span>
            <input
              aria-label="Price per night in rupees"
              inputMode="numeric"
              value={draft.pricePerNight ?? ""}
              placeholder="0"
              onChange={(event) => patch({ pricePerNight: Number(event.target.value.replace(/\D/g, "")) || undefined })}
              className="w-[5ch] min-w-0 bg-transparent text-center outline-none"
              style={{ width: `${Math.max(2, String(draft.pricePerNight ?? "").length || 1)}ch` }}
            />
          </div>
          <p className="mt-3 text-muted">per night, before fees and taxes · minimum {formatINR(MIN_PRICE)}</p>
          {price >= MIN_PRICE && (
            <p className="mx-auto mt-8 max-w-sm rounded-[12px] border border-line p-4 text-sm">
              Guest price before taxes: about <strong>{formatINR(Math.round(price * (1 + SERVICE_FEE_RATE)))}</strong> per night, including the Airbnb service fee.
            </p>
          )}
        </div>
      );
    }

    case "rules":
      return (
        <div className="space-y-5">
          <label className="block">
            <span className="mb-1 block text-sm font-medium">Cleaning fee (₹, charged once per stay)</span>
            <input inputMode="numeric" value={draft.cleaningFee || ""} placeholder="0" onChange={(event) => patch({ cleaningFee: Number(event.target.value.replace(/\D/g, "")) || 0 })} className={inputClass} />
          </label>
          <div>
            <Row title="Minimum nights"><Stepper label="minimum nights" value={draft.minNights} min={1} max={30} onChange={(minNights) => patch({ minNights, maxNights: Math.max(draft.maxNights, minNights) })} /></Row>
            <Row title="Maximum nights"><Stepper label="maximum nights" value={draft.maxNights} min={draft.minNights} max={365} onChange={(maxNights) => patch({ maxNights })} /></Row>
            <Row title="Pets allowed">
              <button type="button" role="switch" aria-checked={draft.petsAllowed} aria-label="Pets allowed" onClick={() => patch({ petsAllowed: !draft.petsAllowed })} className={`relative h-8 w-12 rounded-full transition ${draft.petsAllowed ? "bg-ink" : "bg-[#b0b0b0]"}`}>
                <span className={`absolute left-1 top-1 size-6 rounded-full bg-canvas transition-transform ${draft.petsAllowed ? "translate-x-4" : ""}`} />
              </button>
            </Row>
          </div>
          <label className="block">
            <span className="mb-1 block text-sm font-medium">House rules</span>
            <textarea value={draft.houseRules} onChange={(event) => patch({ houseRules: event.target.value })} rows={4} maxLength={2000} className={inputClass} placeholder="No parties. Quiet hours after 10 pm." />
          </label>
        </div>
      );

    default:
      return null; // "review" is rendered by the wizard itself
  }
}

export const STEP_TITLES: Record<StepKey, { title: string; hint?: string }> = {
  about: { title: "It's easy to get started on Airbnb" },
  "property-type": { title: "Which of these best describes your place?" },
  "place-type": { title: "What type of place will guests have?" },
  location: { title: "Where's your place located?", hint: "Your address is only shared with guests after they've made a reservation." },
  "floor-plan": { title: "Share some basics about your place", hint: "You'll add more details later, like bed types." },
  amenities: { title: "Tell guests what your place has to offer", hint: "You can add more amenities after you publish." },
  photos: { title: "Add some photos of your place", hint: "You'll need at least 5 photos to get started. You can add more or make changes later." },
  title: { title: "Now, let's give your place a title", hint: "Short titles work best. Have fun with it. You can always change it later." },
  description: { title: "Create your description", hint: "Share what makes your place special." },
  category: { title: "Which category fits your place best?", hint: "Guests browse stays by category." },
  price: { title: "Now, set your price", hint: "You can change it any time." },
  rules: { title: "Set your stay rules", hint: "Cleaning fee, how long guests can stay, and your house rules." },
  review: { title: "Review your listing", hint: "Here's what we'll show to guests. Make sure everything looks good." },
};
