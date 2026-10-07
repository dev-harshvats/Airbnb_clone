"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ServiceCard } from "@/components/listing/CatalogCards";
import { ServiceIcon } from "@/components/services/ServiceIcons";
import { ScrollRow } from "@/components/ui/ScrollRow";
import { Skeleton } from "@/components/ui/Skeleton";
import { catalogApi } from "@/lib/api/catalog";
import { searchPath } from "@/lib/routes";
import type { ServiceCard as Service, ServiceTypeSummary } from "@/types/api";

const CARD_WIDTH = "w-[calc((100%-16px)/2)] shrink-0 snap-start md:w-[calc((100%-60px)/4)] xl:w-[calc((100%-100px)/6)]";

type Group = { type: ServiceTypeSummary; items: Service[] };

/** The Services tab: a row of service-type tiles, then one carousel per type. */
export function ServicesHome() {
  const [groups, setGroups] = useState<Group[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    catalogApi
      .serviceTypes()
      .then((types) =>
        Promise.all(
          types.map(async (type) => ({
            type,
            items: (await catalogApi.services({ service_type: type.key, page_size: 12 })).items,
          })),
        ),
      )
      .then((loaded) => !cancelled && setGroups(loaded))
      .catch(() => !cancelled && setGroups([]));
    return () => {
      cancelled = true;
    };
  }, []);

  if (groups === null) {
    return (
      <main className="mx-auto max-w-[1760px] space-y-4 px-4 py-8 md:px-6 xl:px-20">
        <Skeleton className="h-7 w-64" />
        <div className="flex gap-4">
          {Array.from({ length: 5 }, (_, i) => (
            <Skeleton key={i} className="size-[126px] rounded-[20px]" />
          ))}
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-[1760px] px-4 pb-4 pt-6 md:px-6 xl:px-20">
      {groups.length === 0 && <p className="py-20 text-center text-muted">No services are available right now.</p>}
      {groups.length > 0 && (
        <section className="pb-4">
          <h2 className="mb-4 text-[22px] font-semibold">Services across India</h2>
          <div className="no-scrollbar flex gap-4 overflow-x-auto">
            {groups.map(({ type }) => (
              <Link key={type.key} href={searchPath("services", null, { service_type: type.key })} className="w-[126px] shrink-0">
                <div className="grid aspect-square place-items-center rounded-[20px] bg-surface transition hover:bg-[#ebebeb]">
                  <ServiceIcon type={type.key} className="size-16" />
                </div>
                <p className="mt-2 text-sm font-semibold">{type.label}</p>
              </Link>
            ))}
          </div>
        </section>
      )}
      {groups.map(({ type, items }) => (
        <ScrollRow key={type.key} title={type.label} href={searchPath("services", null, { service_type: type.key })}>
          {items.map((service) => (
            <div key={service.id} className={CARD_WIDTH}>
              <ServiceCard service={service} />
            </div>
          ))}
        </ScrollRow>
      ))}
    </main>
  );
}
