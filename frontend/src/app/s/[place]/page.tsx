import { notFound } from "next/navigation";

import { KindResults } from "@/components/listing/KindResults";
import { isKind } from "@/lib/routes";

/**
 * /s/homes, /s/experiences, /s/services: results for "anywhere". The single segment is named
 * `place` only because Next.js requires one name for this position; here it holds the kind.
 */
export default async function AnywhereResultsPage({ params }: { params: Promise<{ place: string }> }) {
  const { place: kind } = await params;
  if (!isKind(kind)) notFound();
  return <KindResults kind={kind} place={null} />;
}
