"use client";

import { useEffect, useState } from "react";

import { ExperienceCard } from "@/components/listing/CatalogCards";
import { ScrollRow } from "@/components/ui/ScrollRow";
import { Skeleton } from "@/components/ui/Skeleton";
import { catalogApi } from "@/lib/api/catalog";
import { searchPath } from "@/lib/routes";
import type { ExperienceCard as Experience, ExperienceCategory } from "@/types/api";

export const CATEGORY_TITLES: Record<ExperienceCategory, string> = {
  food: "Food and drink experiences",
  heritage: "Heritage and history walks",
  adventure: "Adventure and outdoors",
  wellness: "Wellness and yoga",
  nature: "Nature and countryside",
  arts: "Arts and crafts",
};

const CARD_WIDTH = "w-[calc((100%-16px)/2)] shrink-0 snap-start md:w-[calc((100%-60px)/4)] xl:w-[calc((100%-100px)/6)]";

function Row({ title, href, items }: { title: string; href: string; items: Experience[] }) {
  return (
    <ScrollRow title={title} href={href}>
      {items.map((experience) => (
        <div key={experience.id} className={CARD_WIDTH}>
          <ExperienceCard experience={experience} />
        </div>
      ))}
    </ScrollRow>
  );
}

/** The Experiences tab: "Happening today in…" first, then rows by kind of experience. */
export function ExperiencesHome() {
  const [items, setItems] = useState<Experience[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    catalogApi
      .experiences({ page_size: 50 })
      .then((page) => !cancelled && setItems(page.items))
      .catch(() => !cancelled && setItems([]));
    return () => {
      cancelled = true;
    };
  }, []);

  if (items === null) {
    return (
      <main className="mx-auto max-w-[1760px] space-y-4 px-4 py-8 md:px-6 xl:px-20">
        <Skeleton className="h-7 w-72" />
        <div className="flex gap-5 overflow-hidden">
          {Array.from({ length: 6 }, (_, i) => (
            <Skeleton key={i} className="aspect-square w-[calc((100%-100px)/6)] min-w-[180px] shrink-0 rounded-[14px]" />
          ))}
        </div>
      </main>
    );
  }

  // The city with the most experiences stands in for "your location".
  const counts = new Map<string, number>();
  for (const e of items) counts.set(e.city, (counts.get(e.city) ?? 0) + 1);
  const city = [...counts].sort((a, b) => b[1] - a[1])[0]?.[0];
  const today = items.filter((e) => e.city === city).sort((a, b) => a.start_time.localeCompare(b.start_time));
  const categories = (Object.keys(CATEGORY_TITLES) as ExperienceCategory[])
    .map((category) => ({ category, rows: items.filter((e) => e.category === category) }))
    .filter((group) => group.rows.length >= 3);

  return (
    <main className="mx-auto max-w-[1760px] px-4 pb-4 pt-2 md:px-6 xl:px-20">
      {items.length === 0 && <p className="py-20 text-center text-muted">No experiences are available right now.</p>}
      {today.length > 0 && <Row title={`Happening today in ${city}`} href={searchPath("experiences", city)} items={today} />}
      {items.length > 0 && (
        <Row title="Popular experiences across India" href={searchPath("experiences")} items={[...items].sort((a, b) => (b.rating_avg ?? 0) - (a.rating_avg ?? 0)).slice(0, 12)} />
      )}
      {categories.map(({ category, rows }) => (
        <Row key={category} title={CATEGORY_TITLES[category]} href={searchPath("experiences", null, { category })} items={rows.slice(0, 12)} />
      ))}
    </main>
  );
}
