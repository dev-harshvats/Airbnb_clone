"use client";

import { Check } from "lucide-react";
import { useEffect, useState } from "react";

import { PriceRange } from "@/components/search/PriceRange";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { listingsApi } from "@/lib/api/listings";
import { activeFilterCount, toListingQuery, type SearchState } from "@/lib/searchState";
import type { Amenity, PriceHistogram } from "@/types/api";

export const PROPERTY_TYPES: [key: string, label: string][] = [
  ["house", "House"], ["flat", "Flat"], ["guest_house", "Guest house"], ["hotel", "Hotel"],
  ["villa", "Villa"], ["cottage", "Cottage"], ["houseboat", "Houseboat"], ["cabin", "Cabin"],
  ["farm_stay", "Farm stay"], ["treehouse", "Treehouse"], ["heritage_home", "Heritage home"], ["tent", "Tent"],
];

const PLACE_TYPES: [key: string | undefined, label: string][] = [
  [undefined, "Any type"],
  ["private_room", "Room"],
  ["entire", "Entire home"],
];

const AMENITIES_SHOWN = 8;

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="border-b border-line-soft py-8 first:pt-2">
      <h3 className="mb-5 text-[22px] font-semibold">{title}</h3>
      {children}
    </section>
  );
}

const pill = (selected: boolean) =>
  `rounded-full border px-5 py-2 text-sm transition ${selected ? "border-ink bg-ink text-white" : "border-line hover:border-ink"}`;

function CountRow({ label, value, onChange }: { label: string; value?: number; onChange: (value?: number) => void }) {
  return (
    <div className="mb-5 last:mb-0">
      <p className="mb-2 text-base">{label}</p>
      <div className="no-scrollbar flex gap-2 overflow-x-auto">
        {[undefined, 1, 2, 3, 4, 5, 6, 7, 8].map((n) => (
          <button key={n ?? "any"} type="button" aria-pressed={value === n} onClick={() => onChange(n)} className={`${pill(value === n)} min-w-14`}>
            {n === undefined ? "Any" : n === 8 ? "8+" : n}
          </button>
        ))}
      </div>
    </div>
  );
}

function Toggle({ title, hint, checked, onChange }: { title: string; hint: string; checked: boolean; onChange: (value: boolean) => void }) {
  return (
    <div className="flex items-center justify-between gap-6 py-3">
      <div>
        <p className="text-base">{title}</p>
        <p className="text-sm text-muted">{hint}</p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={title}
        onClick={() => onChange(!checked)}
        className={`relative h-8 w-12 shrink-0 rounded-full transition ${checked ? "bg-ink" : "bg-[#b0b0b0]"}`}
      >
        <span className={`absolute left-1 top-1 size-6 rounded-full bg-white transition-transform ${checked ? "translate-x-4" : ""}`} />
      </button>
    </div>
  );
}

type Props = {
  place: string | null;
  state: SearchState;
  onApply: (next: SearchState) => void;
  onClose: () => void;
};

/**
 * Airbnb's Filters dialog. Edits are a draft: nothing changes on the page until "Show N places",
 * and that number is looked up live as the draft changes. Mount it only while it is open, so the
 * draft starts from the current search each time.
 */
export function FiltersModal({ place, state, onApply, onClose }: Props) {
  const [draft, setDraft] = useState(state);
  const [histogram, setHistogram] = useState<PriceHistogram | null>(null);
  const [amenities, setAmenities] = useState<Amenity[]>([]);
  const [count, setCount] = useState<number | null>(null);
  const [allAmenities, setAllAmenities] = useState(false);

  const patch = (changes: Partial<SearchState>) => setDraft((d) => ({ ...d, ...changes }));
  const toggleIn = (list: string[], value: string) => (list.includes(value) ? list.filter((v) => v !== value) : [...list, value]);

  useEffect(() => {
    listingsApi.amenities().then(setAmenities).catch(() => setAmenities([]));
    // The histogram ignores the price filter on the server, so one fetch (for the search without price) is enough.
    listingsApi
      .priceHistogram(toListingQuery(state, place))
      .then(setHistogram)
      .catch(() => setHistogram(null));
    // eslint-disable-next-line react-hooks/exhaustive-deps -- loaded once, when the dialog opens
  }, []);

  // Live "Show N places": a debounced count for whatever the draft currently says.
  useEffect(() => {
    let current = true;
    const timer = setTimeout(() => {
      listingsApi
        .search({ ...toListingQuery(draft, place), page: 1, page_size: 1 })
        .then((result) => current && setCount(result.total))
        .catch(() => current && setCount(null));
    }, 250);
    return () => {
      current = false;
      clearTimeout(timer);
    };
  }, [draft, place]);

  const cleared: Partial<SearchState> = {
    minPrice: undefined, maxPrice: undefined, placeType: undefined, propertyTypes: [], bedrooms: undefined,
    beds: undefined, bathrooms: undefined, amenities: [], superhost: false, guestFavourite: false,
  };
  const shownAmenities = allAmenities ? amenities : amenities.slice(0, AMENITIES_SHOWN);

  return (
    <Modal open onClose={onClose} title="Filters" className="md:!max-w-[780px]">
      <div className="px-6 pb-4 md:px-8">
        <Section title="Type of place">
          <div className="inline-flex rounded-full border border-line p-1">
            {PLACE_TYPES.map(([key, label]) => (
              <button
                key={label}
                type="button"
                aria-pressed={draft.placeType === key}
                onClick={() => patch({ placeType: key })}
                className={`rounded-full px-6 py-2.5 text-sm font-medium transition ${draft.placeType === key ? "bg-ink text-white" : "hover:bg-surface"}`}
              >
                {label}
              </button>
            ))}
          </div>
        </Section>

        <Section title="Price range">
          <p className="-mt-3 mb-4 text-sm text-muted">Nightly prices before fees and taxes</p>
          <PriceRange histogram={histogram} min={draft.minPrice} max={draft.maxPrice} onChange={(minPrice, maxPrice) => patch({ minPrice, maxPrice })} />
        </Section>

        <Section title="Rooms and beds">
          <CountRow label="Bedrooms" value={draft.bedrooms} onChange={(bedrooms) => patch({ bedrooms })} />
          <CountRow label="Beds" value={draft.beds} onChange={(beds) => patch({ beds })} />
          <CountRow label="Bathrooms" value={draft.bathrooms} onChange={(bathrooms) => patch({ bathrooms })} />
        </Section>

        <Section title="Property type">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {PROPERTY_TYPES.map(([key, label]) => {
              const selected = draft.propertyTypes.includes(key);
              return (
                <button
                  key={key}
                  type="button"
                  aria-pressed={selected}
                  onClick={() => patch({ propertyTypes: toggleIn(draft.propertyTypes, key) })}
                  className={`rounded-[12px] border px-4 py-4 text-left text-sm font-medium transition ${selected ? "border-2 border-ink bg-surface" : "border-line hover:border-ink"}`}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </Section>

        <Section title="Amenities">
          <ul className="grid grid-cols-1 gap-x-8 gap-y-4 sm:grid-cols-2">
            {shownAmenities.map((amenity) => {
              const checked = draft.amenities.includes(amenity.key);
              return (
                <li key={amenity.key}>
                  <label className="flex cursor-pointer items-center gap-3 text-base">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => patch({ amenities: toggleIn(draft.amenities, amenity.key) })}
                      className="peer sr-only"
                    />
                    <span className="grid size-6 shrink-0 place-items-center rounded-[6px] border border-[#b0b0b0] peer-checked:border-ink peer-checked:bg-ink peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-ink">
                      {checked && <Check size={16} className="text-white" strokeWidth={3} />}
                    </span>
                    {amenity.name}
                  </label>
                </li>
              );
            })}
          </ul>
          {amenities.length > AMENITIES_SHOWN && (
            <button type="button" onClick={() => setAllAmenities((v) => !v)} className="mt-5 text-base font-semibold underline">
              {allAmenities ? "Show less" : `Show all ${amenities.length}`}
            </button>
          )}
        </Section>

        <Section title="Top-tier stays">
          <Toggle title="Superhost" hint="Stay with highly rated, experienced hosts" checked={draft.superhost} onChange={(superhost) => patch({ superhost })} />
          <Toggle title="Guest favourite" hint="The most loved homes on Airbnb" checked={draft.guestFavourite} onChange={(guestFavourite) => patch({ guestFavourite })} />
        </Section>
      </div>

      <footer className="sticky bottom-0 flex items-center justify-between border-t border-line-soft bg-white px-6 py-4 md:px-8">
        <button
          type="button"
          onClick={() => patch(cleared)}
          disabled={activeFilterCount(draft) === 0}
          className="text-base font-semibold underline disabled:cursor-not-allowed disabled:no-underline disabled:opacity-40"
        >
          Clear all
        </button>
        <Button variant="dark" size="lg" disabled={count === 0} onClick={() => onApply(draft)}>
          {count === null ? "Show places" : count === 0 ? "No places" : `Show ${count.toLocaleString("en-IN")} place${count === 1 ? "" : "s"}`}
        </Button>
      </footer>
    </Modal>
  );
}
