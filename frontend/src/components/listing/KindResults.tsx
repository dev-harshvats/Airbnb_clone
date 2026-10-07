import { Suspense } from "react";

import { CategoryBar } from "@/components/layout/CategoryBar";
import { ExperienceResults, ServiceResults } from "@/components/listing/CatalogResults";
import { SearchResults } from "@/components/listing/SearchResults";
import type { Kind } from "@/lib/routes";

/** Picks the results list for a tab (homes, experiences or services). useSearchParams needs Suspense. */
export function KindResults({ kind, place }: { kind: Kind; place: string | null }) {
  return (
    <Suspense fallback={<div className="h-[85px] border-b border-line-soft" />}>
      {kind === "homes" && (
        <>
          <CategoryBar place={place} />
          <SearchResults place={place} />
        </>
      )}
      {kind === "experiences" && <ExperienceResults place={place} />}
      {kind === "services" && <ServiceResults place={place} />}
    </Suspense>
  );
}
