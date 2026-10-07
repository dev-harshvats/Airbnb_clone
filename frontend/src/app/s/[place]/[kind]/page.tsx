import { notFound } from "next/navigation";

import { KindResults } from "@/components/listing/KindResults";
import { isKind, slugToPlace } from "@/lib/routes";

/** /s/Goa/homes, /s/Jaipur--India/experiences, /s/Goa/services: results for one place. */
export default async function PlaceResultsPage({ params }: { params: Promise<{ place: string; kind: string }> }) {
  const { place, kind } = await params;
  if (!isKind(kind)) notFound();
  return <KindResults kind={kind} place={slugToPlace(place)} />;
}
