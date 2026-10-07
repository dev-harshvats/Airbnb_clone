import { redirect } from "next/navigation";

import { searchPath, slugToPlace } from "@/lib/routes";

/** SEO-style address /{city}/stays forwards to that city's search results. */
export default async function CityStaysPage({ params }: { params: Promise<{ city: string }> }) {
  redirect(searchPath("homes", slugToPlace((await params).city)));
}
