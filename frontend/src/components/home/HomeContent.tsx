"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ListingCard } from "@/components/listing/ListingCard";
import { Skeleton } from "@/components/ui/Skeleton";
import { ScrollRow } from "@/components/ui/ScrollRow";
import { listingsApi, type ListingQuery } from "@/lib/api/listings";
import { searchPath } from "@/lib/routes";
import type { Destination, ListingCard as Listing } from "@/types/api";

const TAGLINES: Record<string, string> = {
  Anjuna: "Beach cafes and sunsets",
  Palolem: "A quiet crescent bay",
  Mumbai: "The city by the sea",
  Manali: "Snowy mountain escape",
  Shimla: "Colonial hill charm",
  Leh: "High-altitude wonder",
  Rishikesh: "Yoga by the Ganga",
  Varanasi: "Ghats and evening aarti",
  Darjeeling: "Tea gardens and peaks",
  Jaipur: "The Pink City",
  Udaipur: "The city of lakes",
  Jaisalmer: "A golden desert fort",
  Alleppey: "Backwater houseboats",
  Kochi: "Fort Kochi charm",
  Munnar: "Misty tea hills",
  Coorg: "Coffee-estate calm",
  Bengaluru: "Garden city buzz",
  Ooty: "A Nilgiri hill station",
  Pondicherry: "The French Quarter",
  Gokarna: "Laid-back beaches",
};

type Row = { key: string; title: string; subtitle?: string; href: string; items: Listing[]; dates?: { in: string; out: string } };

const iso = (d: Date) => d.toISOString().slice(0, 10);

/** The coming Friday to Sunday (or today's weekend if it is already one). */
function nextWeekend() {
  const start = new Date();
  start.setUTCHours(0, 0, 0, 0);
  start.setUTCDate(start.getUTCDate() + ((5 - start.getUTCDay() + 7) % 7));
  const end = new Date(start);
  end.setUTCDate(end.getUTCDate() + 2);
  return { in: iso(start), out: iso(end) };
}

const searchHref = (q: ListingQuery) =>
  searchPath("homes", q.location, {
    check_in: q.check_in,
    check_out: q.check_out,
    guest_favourite: q.guest_favourite ? "true" : undefined,
    sort: q.sort,
  });

async function loadRows(destinations: Destination[]): Promise<Row[]> {
  const byState = new Map<string, number>();
  for (const d of destinations) byState.set(d.state, (byState.get(d.state) ?? 0) + d.listing_count);
  const states = [...byState].sort((a, b) => b[1] - a[1]).map(([state]) => state);

  // "Guest favourite" row: the state that has the most of them.
  const favourites = await listingsApi.search({ guest_favourite: true, page_size: 50 });
  const favouriteStates = new Map<string, number>();
  for (const l of favourites.items) favouriteStates.set(l.state, (favouriteStates.get(l.state) ?? 0) + 1);
  const favouriteState = [...favouriteStates].sort((a, b) => b[1] - a[1])[0]?.[0];

  const others = states.filter((s) => s !== favouriteState);
  const weekend = nextWeekend();
  const specs: { key: string; title: string; subtitle?: string; query: ListingQuery; dates?: Row["dates"] }[] = [];
  if (favouriteState) {
    specs.push({
      key: "favourites",
      title: `Guest favourite homes in ${favouriteState}`,
      subtitle: "Guests often rate these homes highly",
      query: { location: favouriteState, guest_favourite: true },
    });
  }
  if (others[0]) specs.push({ key: "popular", title: `Popular homes in ${others[0]}`, query: { location: others[0] } });
  if (others[1]) {
    specs.push({
      key: "weekend",
      title: `Available in ${others[1]} this weekend`,
      query: { location: others[1], check_in: weekend.in, check_out: weekend.out },
      dates: weekend,
    });
  }
  if (others[2]) specs.push({ key: "more", title: `Stay in ${others[2]}`, query: { location: others[2], sort: "rating" } });

  const rows = await Promise.all(
    specs.map(async (spec) => ({
      key: spec.key,
      title: spec.title,
      subtitle: spec.subtitle,
      href: searchHref(spec.query),
      dates: spec.dates,
      items: (await listingsApi.search({ ...spec.query, page_size: 12 })).items,
    })),
  );
  return rows.filter((row) => row.items.length > 0);
}

function DestinationTile({ destination }: { destination: Destination }) {
  return (
    <Link
      href={searchPath("homes", destination.city)}
      className="block w-[132px] shrink-0 snap-start sm:w-[148px]"
    >
      <div className="aspect-square overflow-hidden rounded-[14px] bg-surface">
        {destination.cover_url && (
          // eslint-disable-next-line @next/next/no-img-element -- already resized WebP renditions
          <img src={destination.cover_url} alt="" loading="lazy" className="size-full object-cover" />
        )}
      </div>
      <p className="mt-2 text-sm font-semibold">{destination.city}</p>
      <p className="text-xs leading-snug text-muted">{TAGLINES[destination.city] ?? `${destination.listing_count} stays`}</p>
    </Link>
  );
}

function RowSkeleton() {
  return (
    <div className="py-6">
      <Skeleton className="mb-4 h-6 w-72" />
      <div className="flex gap-5 overflow-hidden">
        {Array.from({ length: 6 }, (_, i) => (
          <div key={i} className="w-[calc((100%-100px)/6)] min-w-[200px] shrink-0 space-y-2">
            <Skeleton className="aspect-square w-full rounded-[14px]" />
            <Skeleton className="h-4 w-2/3" />
            <Skeleton className="h-4 w-1/2" />
          </div>
        ))}
      </div>
    </div>
  );
}

/** The home page body: destination tiles, then carousels of stays, as on airbnb.co.in. */
export function HomeContent() {
  const [destinations, setDestinations] = useState<Destination[] | null>(null);
  const [rows, setRows] = useState<Row[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    listingsApi
      .destinations()
      .then(async (list) => {
        if (cancelled) return;
        setDestinations(list);
        const loaded = await loadRows(list);
        if (!cancelled) setRows(loaded);
      })
      .catch(() => {
        if (!cancelled) {
          setDestinations([]);
          setRows([]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="mx-auto max-w-[1760px] px-4 pb-4 pt-2 md:px-6 xl:px-20">
      {destinations === null ? (
        <RowSkeleton />
      ) : (
        destinations.length > 0 && (
          <ScrollRow title="Destinations for you">
            {destinations.map((d) => (
              <DestinationTile key={`${d.city}-${d.state}`} destination={d} />
            ))}
          </ScrollRow>
        )
      )}

      {rows === null ? (
        <>
          <RowSkeleton />
          <RowSkeleton />
        </>
      ) : (
        rows.map((row) => (
          <ScrollRow key={row.key} title={row.title} subtitle={row.subtitle} href={row.href}>
            {row.items.map((listing) => (
              <div key={listing.id} className="w-[calc((100%-16px)/2)] shrink-0 snap-start md:w-[calc((100%-60px)/4)] xl:w-[calc((100%-100px)/6)]">
                <ListingCard
                  listing={listing}
                  nights={row.dates ? 2 : undefined}
                  checkIn={row.dates?.in}
                  checkOut={row.dates?.out}
                />
              </div>
            ))}
          </ScrollRow>
        ))
      )}
    </main>
  );
}
