"use client";

import { ListFilter, Map as MapIcon, Tag } from "lucide-react";
import dynamic from "next/dynamic";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { ListingCard } from "@/components/listing/ListingCard";
import { FiltersModal } from "@/components/search/FiltersModal";
import { Skeleton } from "@/components/ui/Skeleton";
import { useInfiniteList } from "@/hooks/useInfiniteList";
import { listingsApi } from "@/lib/api/listings";
import { nightsBetween } from "@/lib/format";
import { activeFilterCount, parseSearch, toListingQuery, toSearchParams, type SearchState } from "@/lib/searchState";

// Leaflet touches `window`, so the map only ever renders in the browser.
const MapView = dynamic(() => import("@/components/listing/MapView"), {
  ssr: false,
  loading: () => <Skeleton className="size-full" />,
});

const PAGE_SIZE = 24;

const SORTS: [value: NonNullable<SearchState["sort"]>, label: string][] = [
  ["recommended", "Recommended"],
  ["price_asc", "Price: low to high"],
  ["price_desc", "Price: high to low"],
  ["rating", "Top rated"],
  ["newest", "Newest"],
];

const withoutFilters = (state: SearchState): SearchState => ({
  ...parseSearch(new URLSearchParams()),
  checkIn: state.checkIn,
  checkOut: state.checkOut,
  adults: state.adults,
  children: state.children,
  infants: state.infants,
  pets: state.pets,
  category: state.category,
});

/** Search results: a filterable list of stays beside a map of the same stays, all driven by the URL. */
export function SearchResults({ place = null }: { place?: string | null }) {
  const params = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();
  const state = parseSearch(params);
  const location = place ?? params.get("location");

  const [filtersOpen, setFiltersOpen] = useState(false);
  const [showMap, setShowMap] = useState(true);
  const [phoneMap, setPhoneMap] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [hoverId, setHoverId] = useState<number | null>(null);

  const { setSentinel, ...list } = useInfiniteList(`${place ?? ""}|${params.toString()}`, (page) =>
    listingsApi.search({ ...toListingQuery(state, location), page, page_size: PAGE_SIZE }),
  );

  // Change the search by rewriting the URL; the list reloads because its key changes.
  const update = (next: SearchState) => {
    const query = toSearchParams(next);
    if (!place && location) query.set("location", location);
    router.push(query.size ? `${pathname}?${query}` : pathname);
    setSelectedId(null);
  };

  const nights = state.checkIn && state.checkOut ? nightsBetween(state.checkIn, state.checkOut) : undefined;
  const filterCount = activeFilterCount(state);
  const noun = list.total === 1 ? "home" : "homes";

  return (
    <main className="mx-auto max-w-[1760px] px-4 py-6 md:px-6 xl:px-10">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-sm font-semibold">
          {list.firstLoad ? <Skeleton className="h-5 w-40" /> : `${list.total.toLocaleString("en-IN")} ${noun}${location ? ` in ${location}` : ""}`}
        </h1>
        <div className="flex items-center gap-3">
          <p className="hidden items-center gap-2 text-sm xl:flex">
            <Tag size={18} className="fill-rausch stroke-rausch" /> Prices include all fees
          </p>
          <select
            aria-label="Sort by"
            value={state.sort ?? "recommended"}
            onChange={(event) =>
              update({ ...state, sort: event.target.value === "recommended" ? undefined : (event.target.value as SearchState["sort"]) })
            }
            className="h-10 rounded-control border border-line bg-white px-3 text-sm font-medium hover:border-ink"
          >
            {SORTS.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => setFiltersOpen(true)}
            className="flex h-10 items-center gap-2 rounded-control border border-line px-4 text-sm font-medium hover:border-ink"
          >
            <ListFilter size={16} /> Filters
            {filterCount > 0 && <span className="grid size-5 place-items-center rounded-full bg-ink text-xs text-white">{filterCount}</span>}
          </button>
          <button
            type="button"
            onClick={() => setShowMap((v) => !v)}
            className="hidden h-10 items-center gap-2 rounded-control border border-line px-4 text-sm font-medium hover:border-ink lg:flex"
          >
            <MapIcon size={16} /> {showMap ? "Hide map" : "Show map"}
          </button>
        </div>
      </div>

      <div className={showMap ? "lg:grid lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:gap-6" : ""}>
        <div>
          {list.failed && <p className="py-16 text-center text-muted">We couldn&apos;t load stays right now. Please try again.</p>}
          {!list.firstLoad && !list.failed && list.total === 0 && (
            <div className="py-16 text-center">
              <h2 className="text-xl font-semibold">No exact matches</h2>
              <p className="mt-1 text-muted">Try changing your search or removing some filters.</p>
              {filterCount > 0 && (
                <button type="button" onClick={() => update(withoutFilters(state))} className="mt-4 font-semibold underline">
                  Remove all filters
                </button>
              )}
            </div>
          )}

          <div
            className={`grid grid-cols-1 gap-x-6 gap-y-10 sm:grid-cols-2 ${showMap ? "xl:grid-cols-3" : "lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5"}`}
          >
            {list.items.map((listing) => (
              <div key={listing.id} onMouseEnter={() => setHoverId(listing.id)} onMouseLeave={() => setHoverId(null)}>
                <ListingCard listing={listing} variant="grid" checkIn={state.checkIn} checkOut={state.checkOut} nights={nights} />
              </div>
            ))}
            {list.loading &&
              Array.from({ length: list.firstLoad ? 10 : 4 }, (_, i) => (
                <div key={`s${i}`} className="space-y-3">
                  <Skeleton className="aspect-square w-full rounded-[14px]" />
                  <Skeleton className="h-4 w-2/3" />
                  <Skeleton className="h-4 w-1/2" />
                </div>
              ))}
          </div>
          <div ref={setSentinel} className="h-8" />
        </div>

        {/* On phones the map is a full-screen overlay opened from the floating button; on desktop it sticks beside the list. */}
        <div
          className={`${phoneMap ? "fixed inset-0 z-40" : "hidden"} ${showMap ? "lg:sticky lg:top-24 lg:z-0 lg:block lg:h-[calc(100vh-7rem)] lg:overflow-hidden lg:rounded-[16px]" : "lg:hidden"}`}
        >
          <MapView items={list.items} selectedId={selectedId} hoverId={hoverId} onSelect={setSelectedId} nights={nights} />
        </div>
      </div>

      <button
        type="button"
        onClick={() => setPhoneMap((v) => !v)}
        className="fixed bottom-24 left-1/2 z-50 flex -translate-x-1/2 items-center gap-2 rounded-full bg-ink px-5 py-3 text-sm font-semibold text-white shadow-modal lg:hidden"
      >
        {phoneMap ? (
          <>
            <ListFilter size={16} /> Show list
          </>
        ) : (
          <>
            <MapIcon size={16} /> Map
          </>
        )}
      </button>

      {filtersOpen && (
        <FiltersModal
          place={location}
          state={state}
          onClose={() => setFiltersOpen(false)}
          onApply={(next) => {
            setFiltersOpen(false);
            update(next);
          }}
        />
      )}
    </main>
  );
}
