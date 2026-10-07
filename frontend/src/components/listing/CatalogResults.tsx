"use client";

import { Tag } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { CATEGORY_TITLES } from "@/components/home/ExperiencesHome";
import { ExperienceCard, ServiceCard } from "@/components/listing/CatalogCards";
import { Skeleton } from "@/components/ui/Skeleton";
import { useInfiniteList } from "@/hooks/useInfiniteList";
import { catalogApi } from "@/lib/api/catalog";
import { searchPath } from "@/lib/routes";
import type { ExperienceCategory, ServiceType } from "@/types/api";

const PAGE_SIZE = 24;
const GRID = "grid grid-cols-1 gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5";

const SERVICE_LABELS: Record<ServiceType, string> = {
  photography: "Photography",
  chefs: "Chefs",
  training: "Training",
  makeup: "Make-up",
  hair: "Hair",
  massage: "Massage",
};

function Chip({ href, active, children }: { href: string; active: boolean; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className={`shrink-0 rounded-full border px-4 py-2 text-sm font-medium transition ${active ? "border-ink bg-ink text-white" : "border-line hover:border-ink"}`}
    >
      {children}
    </Link>
  );
}

function Header({ count, noun, place, loading }: { count: number; noun: string; place: string | null; loading: boolean }) {
  return (
    <div className="mb-6 flex items-center justify-between">
      <h1 className="text-sm font-semibold">
        {loading ? <Skeleton className="h-5 w-48" /> : `${count} ${noun}${count === 1 ? "" : "s"}${place ? ` in ${place}` : ""}`}
      </h1>
      <p className="flex items-center gap-2 text-sm">
        <Tag size={18} className="fill-rausch stroke-rausch" /> Prices include all fees
      </p>
    </div>
  );
}

function Skeletons({ count }: { count: number }) {
  return Array.from({ length: count }, (_, i) => (
    <div key={i} className="space-y-3">
      <Skeleton className="aspect-square w-full rounded-[14px]" />
      <Skeleton className="h-4 w-2/3" />
      <Skeleton className="h-4 w-1/2" />
    </div>
  ));
}

function Empty({ failed }: { failed: boolean }) {
  return failed ? (
    <p className="py-16 text-center text-muted">We couldn&apos;t load results right now. Please try again.</p>
  ) : (
    <div className="py-16 text-center">
      <h2 className="text-xl font-semibold">No exact matches</h2>
      <p className="mt-1 text-muted">Try changing your search or choosing another place.</p>
    </div>
  );
}

/** /s/{place}/experiences: a grid of experiences with category chips. */
export function ExperienceResults({ place }: { place: string | null }) {
  const category = (useSearchParams().get("category") as ExperienceCategory | null) ?? undefined;
  const { setSentinel, ...list } = useInfiniteList(`${place}|${category}`, (page) =>
    catalogApi.experiences({ location: place ?? undefined, category, page, page_size: PAGE_SIZE }),
  );

  return (
    <main className="mx-auto max-w-[1760px] px-4 py-6 md:px-6 xl:px-20">
      <div className="no-scrollbar mb-6 flex gap-2 overflow-x-auto">
        <Chip href={searchPath("experiences", place)} active={!category}>All</Chip>
        {(Object.keys(CATEGORY_TITLES) as ExperienceCategory[]).map((key) => (
          <Chip key={key} href={searchPath("experiences", place, { category: key })} active={category === key}>
            {CATEGORY_TITLES[key].split(" ")[0]}
          </Chip>
        ))}
      </div>
      <Header count={list.total} noun="experience" place={place} loading={list.firstLoad} />
      {!list.firstLoad && list.items.length === 0 && <Empty failed={list.failed} />}
      <div className={GRID}>
        {list.items.map((experience) => (
          <ExperienceCard key={experience.id} experience={experience} />
        ))}
        {list.loading && <Skeletons count={list.firstLoad ? 10 : 4} />}
      </div>
      <div ref={setSentinel} className="h-8" />
    </main>
  );
}

/** /s/{place}/services: a grid of services with service-type chips. */
export function ServiceResults({ place }: { place: string | null }) {
  const type = (useSearchParams().get("service_type") as ServiceType | null) ?? undefined;
  const { setSentinel, ...list } = useInfiniteList(`${place}|${type}`, (page) =>
    catalogApi.services({ location: place ?? undefined, service_type: type, page, page_size: PAGE_SIZE }),
  );

  return (
    <main className="mx-auto max-w-[1760px] px-4 py-6 md:px-6 xl:px-20">
      <div className="no-scrollbar mb-6 flex gap-2 overflow-x-auto">
        <Chip href={searchPath("services", place)} active={!type}>All</Chip>
        {(Object.keys(SERVICE_LABELS) as ServiceType[]).map((key) => (
          <Chip key={key} href={searchPath("services", place, { service_type: key })} active={type === key}>
            {SERVICE_LABELS[key]}
          </Chip>
        ))}
      </div>
      <Header count={list.total} noun="service" place={place} loading={list.firstLoad} />
      {!list.firstLoad && list.items.length === 0 && <Empty failed={list.failed} />}
      <div className={GRID}>
        {list.items.map((service) => (
          <ServiceCard key={service.id} service={service} />
        ))}
        {list.loading && <Skeletons count={list.firstLoad ? 10 : 4} />}
      </div>
      <div ref={setSentinel} className="h-8" />
    </main>
  );
}
