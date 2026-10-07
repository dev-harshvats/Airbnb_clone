"use client";

import { Tag } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { ListingCard } from "@/components/listing/ListingCard";
import { Skeleton } from "@/components/ui/Skeleton";
import { listingsApi, type ListingQuery } from "@/lib/api/listings";
import { nightsBetween } from "@/lib/format";
import type { ListingCard as Listing } from "@/types/api";

const PAGE_SIZE = 24;

/** Turn the URL's query string into the filters the API understands. */
function toQuery(params: URLSearchParams, place: string | null): ListingQuery {
  const number = (key: string) => (params.get(key) ? Number(params.get(key)) : undefined);
  return {
    location: place ?? params.get("location") ?? undefined,
    check_in: params.get("check_in") ?? undefined,
    check_out: params.get("check_out") ?? undefined,
    adults: number("adults"),
    children: number("children"),
    category: params.get("category") ?? undefined,
    min_price: number("min_price"),
    max_price: number("max_price"),
    amenities: params.getAll("amenities"),
    property_types: params.getAll("property_types"),
    sort: (params.get("sort") as ListingQuery["sort"]) ?? undefined,
  };
}

/** The search results: a count, then a grid of cards that keeps loading as you scroll. */
export function SearchResults({ place = null }: { place?: string | null }) {
  const params = useSearchParams();
  const queryKey = `${place ?? ""}|${params.toString()}`;
  const [state, setState] = useState<{ key: string; items: Listing[]; total: number; page: number; loading: boolean; failed: boolean }>({
    key: "",
    items: [],
    total: 0,
    page: 0,
    loading: true,
    failed: false,
  });
  const sentinel = useRef<HTMLDivElement>(null);

  const fetchPage = (page: number, reset: boolean, isCurrent: () => boolean = () => true) =>
    listingsApi
      .search({ ...toQuery(params, place), page, page_size: PAGE_SIZE })
      .then((result) => {
        if (!isCurrent()) return;
        setState((s) => ({
          key: queryKey,
          items: reset ? result.items : [...s.items, ...result.items],
          total: result.total,
          page,
          loading: false,
          failed: false,
        }));
      })
      .catch(() => {
        if (isCurrent()) setState((s) => ({ ...s, loading: false, failed: true }));
      });

  // First page for this search. The flag drops a slow response that arrives after the search changed.
  useEffect(() => {
    let current = true;
    void fetchPage(1, true, () => current);
    return () => {
      current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reload only when the URL changes
  }, [queryKey]);

  // Results belonging to an older URL are treated as "still loading" rather than shown.
  const stale = state.key !== queryKey;
  const items = stale ? [] : state.items;
  const hasMore = !stale && items.length < state.total;
  useEffect(() => {
    const el = sentinel.current;
    if (!el || !hasMore || state.loading) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setState((s) => ({ ...s, loading: true }));
          void fetchPage(state.page + 1, false);
        }
      },
      { rootMargin: "400px" },
    );
    observer.observe(el);
    return () => observer.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- re-arm after each page
  }, [hasMore, state.loading, state.page, queryKey]);

  const checkIn = params.get("check_in") ?? undefined;
  const checkOut = params.get("check_out") ?? undefined;
  const nights = checkIn && checkOut ? nightsBetween(checkIn, checkOut) : undefined;
  const location = place ?? params.get("location");
  const firstLoad = stale || (state.loading && items.length === 0);

  return (
    <main className="mx-auto max-w-[1760px] px-4 py-6 md:px-6 xl:px-20">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-sm font-semibold">
          {firstLoad ? <Skeleton className="h-5 w-40" /> : `${state.total} ${state.total === 1 ? "home" : "homes"}${location ? ` in ${location}` : ""}`}
        </h1>
        <p className="flex items-center gap-2 text-sm">
          <Tag size={18} className="fill-rausch stroke-rausch" /> Prices include all fees
        </p>
      </div>

      {state.failed && items.length === 0 && (
        <p className="py-16 text-center text-muted">We couldn&apos;t load stays right now. Please try again.</p>
      )}
      {!firstLoad && !state.failed && state.total === 0 && (
        <div className="py-16 text-center">
          <h2 className="text-xl font-semibold">No exact matches</h2>
          <p className="mt-1 text-muted">Try changing your search or removing some filters.</p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
        {items.map((listing) => (
          <ListingCard key={listing.id} listing={listing} variant="grid" checkIn={checkIn} checkOut={checkOut} nights={nights} />
        ))}
        {(state.loading || stale) &&
          Array.from({ length: firstLoad ? 10 : 4 }, (_, i) => (
            <div key={`s${i}`} className="space-y-3">
              <Skeleton className="aspect-square w-full rounded-[14px]" />
              <Skeleton className="h-4 w-2/3" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          ))}
      </div>
      <div ref={sentinel} className="h-8" />
    </main>
  );
}
